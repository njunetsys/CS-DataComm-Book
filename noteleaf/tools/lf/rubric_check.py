#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lf/rubric_check.py: PresentBench 式原子 rubric 评测器（引方法，不抄代码）。

对照 PresentBench 的设计（arXiv 2603.07244）：
- 二分判定 0/1 + 局部证据（原文片段），不做模糊打分
- 材料无关（结构/清晰/一致性）+ 材料依赖（完整/忠实/示例）
只对 HTML 讲义做「可机判」的结构与忠实度原子项；复杂主观项（视觉美观等）刻意
不在列，与 Noteleaf「机检只定位、好坏归人」同哲学。

校准记录（2026-11-23，实测后）：
- R1 空节：初版按 (depth, heading) 字典分组，段落会继承上一个标题的过期文本、
  depth=0，导致"分组误伤"。改为「按文档顺序维护标题栈」，段落归属最近的开合标题
  链，只对 h2 级成节统计，文档题( h1 )与前导段(首个 h2 之前)不算节。
- R2 标题：初版要求 h2>=3 且每标题 >8 字；实测"序章"2 字小节等被误报。
  校准为 h2>=2 且标题非空( >=2 字即可)。
- R4 图说明：初版"无 alt 即 FAIL"；实测 13 张无 alt 拖垮整页。校准为
  "正文零引用图才 FAIL，缺 alt 只降为 WARN"。
- R7 示例性：随 R1/R2 的分组修正同步重建（按 h2 成节统计）；与 R5 一样是
  显式信号启发式（'例如/案例'等词），实测整页无这些词也未必有错，降为 WARN。

用途：与 tools/check_chain.py 红线机检做「评测方式对比」——
红线机检抓格式红线（破折号/去公司化/外链），本工具抓结构/忠实度（空节/无来源断言/图无引用）。
CLI:
  python3 tools/lf/rubric_check.py <file.html> [--json] [--verbose]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# ---------- 轻量 HTML 解析：标题栈 + p 段落 + img ----------
H_LEVEL = {"h1": 1, "h2": 2, "h3": 3}


class CtxParser(HTMLParser):
    """按文档顺序维护标题栈，段落记录其归属标题链。

    HTML 小节通常不包裹 <section>，因此用「后出现即覆盖」的标题栈模拟：
    新标题出现时弹出层级 >= 它的更细标题（h3 被后继 h2 覆盖等）。
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.events: list[dict] = []          # {"t":"h"/"p","level","text"...}
        self.all_text: list[str] = []         # 所有可见块（含 li/td），供图引用核对
        self.imgs: list[dict] = []
        self._extra = None                    # 正在累积的 li/td 文本
        self._tmp = None                      # 正在累积的标题 {"level","text"}
        self._stack: list[dict] = []          # 已闭合标题链 [{level,text},...]
        self._para = None                     # 正在累积的段落 {"text","chain"}
        self._para_chain = None

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag in H_LEVEL:
            lv = H_LEVEL[tag]
            while self._stack and self._stack[-1]["level"] >= lv:
                self._stack.pop()
            self._tmp = {"level": lv, "text": ""}
        elif tag == "p":
            self._para = {"text": ""}
            self._para_chain = list(self._stack)
        elif tag in ("li", "td", "th"):
            self._extra = {"text": ""}
        elif tag == "img":
            self.imgs.append({"alt": (d.get("alt") or "").strip(),
                              "src": (d.get("src") or "")[:40]})

    def handle_startendtag(self, tag, attrs):
        if tag == "img":
            d = dict(attrs)
            self.imgs.append({"alt": (d.get("alt") or "").strip(),
                              "src": (d.get("src") or "")[:40]})

    def handle_data(self, data):
        if self._para is not None:
            self._para["text"] += data
        elif self._extra is not None:
            self._extra["text"] += data
        elif self._tmp is not None:
            self._tmp["text"] += data

    def handle_endtag(self, tag):
        if tag == "p" and self._para is not None:
            txt = self._para["text"].strip()
            if txt:
                self.events.append({"t": "p", "text": txt,
                                    "chain": self._para_chain or []})
            self._para = None
            self._para_chain = None
        elif tag in ("li", "td", "th") and self._extra is not None:
            txt = self._extra["text"].strip()
            if txt:
                self.all_text.append(txt)
                self.events.append({"t": "x", "text": txt})  # 非 p，不参与空节/断言统计
            self._extra = None
        elif tag in H_LEVEL and self._tmp is not None:
            txt = re.sub(r"\s+", " ", self._tmp["text"]).strip()
            if txt:
                self.events.append({"t": "h", "level": self._tmp["level"],
                                    "text": txt})
                self._stack.append({"level": self._tmp["level"], "text": txt})
            self._tmp = None


# ---------- 关联辅助 ----------
def h_label(chain: list[dict], level: int) -> str | None:
    """取标题链里最近的某级标题文本（level=2 取所在 h2 节）。"""
    for e in reversed(chain):
        if e["level"] == level:
            return e["text"]
    return None


# ---------- 原子项 ----------
NUM = re.compile(r"\d+(\.\d+)?\s*(ms|ns|µs|us|s\b|MB|GB|TB|KB|%|x|×|倍|核|vCPU|GiB)")
SRC_WORDS = re.compile(r"论文|官方|报告|来源|出自|参考文献|\[[0-9]+\]|\(.*20[0-9][0-9].*\)|据|来自|口径")
TERM_SIGNAL = re.compile(r"指|即|称为|定义为|是指|理解成|意思是")
EXAMPLE_SIGNAL = re.compile(r"例如|比如|如 |案例|举个|样例|示例")


WARN_IDS = {"R5", "R7"}          # 启发式提醒，不占用 FAIL 计数

def check(events, imgs):
    paras = [e for e in events if e["t"] == "p"]
    headings = [e for e in events if e["t"] == "h"]
    h2s = [h for h in headings if h["level"] == 2]
    h3s = [h for h in headings if h["level"] == 3]

    # 按 h2 节聚合（仅成节，前导段 depth 计为 None，不算空节）
    by_h2: dict[str, int] = {}
    ex_by_h2: dict[str, bool] = {}
    for p in paras:
        lbl = h_label(p["chain"], 2)
        if lbl is None:                      # 前导段，跳过成节统计
            continue
        by_h2[lbl] = by_h2.get(lbl, 0) + len(p["text"])
        if EXAMPLE_SIGNAL.search(p["text"]):
            ex_by_h2[lbl] = True

    # R1 空节：h2 节总长 < 120 字
    empty_h = [k for k, v in by_h2.items() if v < 120]

    # R3 无来源断言：含数字且无出处词且无软化词
    unanchored = []
    for p in paras:
        t = p["text"]
        if NUM.search(t) and not SRC_WORDS.search(t) \
           and not re.search(r"约|大约|量级|左右|近似|约略", t) and len(t) > 40:
            m = NUM.search(t)
            unanchored.append({"sec": (h_label(p["chain"], 2) or "")[:20],
                               "hit": t[max(0, m.start() - 30):m.end() + 30]})

    # R4 图有引用：正文零引用才是 FAIL；缺 alt 降 WARN
    fulltext = " ".join(p["text"] for p in paras)
    # 教材图号「图 3.1」、讲义图号「图 3-1」都要认；原口径只认「图3」会把讲义判失真。
    # 讲义引用常在 li/td 里，用 t=x 事件一并纳入（不参与 p 类判据）。
    full_all = " ".join(e["text"] for e in events if e["t"] in ("p", "x"))
    fig_ref = len(re.findall(r"图\s*[0-9０-９][.\-–][0-9０-９]", full_all))
    no_alt = [im for im in imgs if not im["alt"]]

    # R5 术语定义（宽松启发式，标提醒不判错）
    term_undef = sum(
        1 for p in paras
        if re.search(r"容器|虚拟机|无服务|弹性|调度", p["text"])
        and not TERM_SIGNAL.search(p["text"]))

    # R7 示例性：按 h2 节统计
    no_example = [k for k in by_h2 if k not in ex_by_h2]

    items = [
        {"id": "R1", "dim": "结构/完整",
         "pass": len(empty_h) == 0,
         "evidence": f"疑似过短 h2 节 {len(empty_h)} 个: {empty_h[:4]}"},
        {"id": "R2", "dim": "结构/清晰",
         "pass": len(h2s) >= 2 and all(len(h["text"]) >= 2 for h in h2s),
         "evidence": f"h2={len(h2s)}个，标题最短 {min((len(h['text']) for h in h2s), default=0)} 字"},
        {"id": "R3", "dim": "忠实度/无来源断言",
         "pass": len(unanchored) == 0,
         "evidence": f"含数字但无出处的断言 {len(unanchored)} 处，"
                     f"例: {unanchored[0]['hit'] if unanchored else '无'}"},
        {"id": "R4", "dim": "视觉/图有说明",
         "pass": fig_ref > 0,
         "evidence": f"图数={len(imgs)} 正文引用'图N'={fig_ref}处 "
                     f"无alt的img={len(no_alt)}{'（WARN：缺alt不判FAIL）' if no_alt else ''}"},
        {"id": "R5", "dim": "清晰/术语定义",
         "pass": term_undef < max(3, len(paras) // 5),
         "evidence": f"含核心术语但无定义句的段落 {term_undef} 段（宽松启发式，标提醒不判错）"},
        {"id": "R6", "dim": "完整/章节覆盖",
         "pass": len(h2s) >= 2,
         "evidence": f"章节数 h2={len(h2s)} h3={len(h3s)}（>=2 视作主干完整）"},
        {"id": "R7", "dim": "完整/示例性",
         "pass": len(no_example) == 0,
         "evidence": f"无任何示例信号的小节 {len(no_example)} 个: {no_example[:4]}"},
    ]
    return {"h2": len(h2s), "h3": len(h3s), "imgs": len(imgs),
            "paras": len(paras), "items": items,
            "unanchored": unanchored,                  # R3 无来源断言完整清单（供回源）
            "no_alt_imgs": no_alt,
            "fail_count": sum(1 for i in items
                              if not i["pass"] and i["id"] not in WARN_IDS),
            "warn_count": sum(1 for i in items
                              if not i["pass"] and i["id"] in WARN_IDS),
            "fail_ids": [i["id"] for i in items
                         if not i["pass"] and i["id"] not in WARN_IDS]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--export-json", default="",
                    help="把无来源断言清单(待回源)与无alt图导出到 JSON 文件，供审稿对照素材回源")
    a = ap.parse_args()
    for f in a.files:
        cp = CtxParser()
        cp.feed(open(f, encoding="utf-8").read())
        r = check(cp.events, cp.imgs)
        if a.json:
            print(json.dumps({"file": f, **r}, ensure_ascii=False, indent=2))
        else:
            print(f"rubric_check · {f.split('/')[-1]}")
            print(f"  结构: h2={r['h2']} h3={r['h3']} 图={r['imgs']} 段落={r['paras']}")
            for it in r["items"]:
                mark = "PASS" if it["pass"] else ("WARN" if it["id"] in WARN_IDS else "FAIL")
                print(f"  [{mark}] {it['id']} {it['dim']:<16s} {it['evidence'][:80]}")
            print(f"  结论: FAIL={r['fail_count']}(WARN={r['warn_count']}) 项: "
                  f"{r['fail_ids'] or '无'}")
            print()
        if a.export_json:
            out = {
                "file": str(f),
                "ts_export": __import__("datetime").date.today().isoformat(),
                "pending_source_check": [{"sec": u["sec"], "hit": u["hit"]}
                                         for u in r["unanchored"]],
                "no_alt_imgs": r["no_alt_imgs"],
                "note": "待回源清单：每条含数字断言的原文片段，供审稿逐条对照素材/论文/官网页码回源",
            }
            Path(a.export_json).write_text(
                json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"待回源清单已导出: {a.export_json} "
                  f"({len(out['pending_source_check'])} 条无来源断言)")
    sys.exit(0)


if __name__ == "__main__":
    main()
