#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lf/intent_ga.py: 意图契约 + G-A 概念四要素原型（2026-11-25）。

哲学：不评「这节浅不浅」，只回答可核对问题「声明的要素有没有落点、落在哪」。
- 基准是意图契约，不是模型印象。契约校验不过 → 整份不判，直接报无效。
- 双层判据：信号词（候选）+ 同窗实质锚（数字/术语/因果/对比）。
  只有信号没有实质锚 = HOLLOW（空壳词），不许升 PASS。
- 元数据块从检查输入剥离：契约写进正文骗不过检查。
- 只 WARN 不 BLOCK：教学结构检查永不成为过关门槛，防「合规稿」KPI 游戏。

CLI:
  python3 tools/lf/intent_ga.py CHECK <contract.json> <section.html> [--json]
  python3 tools/lf/intent_ga.py DIFF  <old.json> <new.json>
  python3 tools/lf/intent_ga.py --selfcheck
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
VOCAB_DIR = ROOT / "CloudComputing" / "framework" / "vocab"

KIND_ELEMENTS = {
    "mechanism": ["what", "why", "how", "cost"],
    "transition": ["what"],
    "example": ["what", "how"],
    "summary": ["what", "why"],
}
ELEMENT_CN = {"what": "是什么", "why": "为什么", "how": "怎么做", "cost": "代价权衡"}
ORDERS = {"intuition_first", "phenomenon_first", "top_down"}

# 第一层：候选信号。只说明「这里像是在讲这个要素」，不说明讲透了。
SIGNALS = {
    "what": ["是什么", "定义为", "指的是", "称为", "由.{0,20}提出", "三个角色", "职责", "核心是", "就是"],
    "why": ["为什么", "原因", "因为", "由于", "目的", "为了", "不足", "局限", "难以", "导致", "所以", "需要"],
    "how": ["步骤", "收到", "监测", "写入", "读取", "超过阈值", "据此", "按概率", "增大", "减小", "发送", "调整", "通过"],
    "cost": ["局限", "代价", "权衡", "缺点", "参数多", "调参", "精度粗", "相比", "然而", "但", "困难", "无法", "只有",
             "好处", "收益", "优势", "好处是", " benefit", "换来", "提升", "降低", "避免", "因此能", "得以"],
}
# 第二层：实质锚。信号窗内必须至少命中一个，否则判 HOLLOW。
SUBSTANCE = [
    r"\d+(?:\.\d+)?\s*(?:%|bit|个|台|年|ms|MB)",  # 可核对数字
    r"[A-Za-z][A-Za-z0-9+\-]{2,}",                  # 具体术语/缩写
    r"α|β|P99|ECN|PFC|CNP|INT|RDMA|RoCE",
    r"因为|导致|所以|目的是|原因是|由于",          # 因果
    r"相比|而|不同|反而|代价是",                   # 对比
    r"队列|速率|缓存|带宽|延迟|拥塞|反馈",         # 机制对象
]
SUBSTANCE_RE = [re.compile(x) for x in SUBSTANCE]
WINDOW = 60  # 前后各 60 字算同窗

# 元数据块：契约声明不得当正文证据
META_BLOCKS = [
    re.compile(r"<!--\s*CONTRACT\b.*?-->", re.S | re.I),
    re.compile(r"<script[^>]+type=[\"']application/json[\"'][^>]*>.*?</script>", re.S | re.I),
    re.compile(r"【契约】.*?【/契约】", re.S),
]


def strip_meta(text: str) -> tuple[str, int]:
    """返回 (剥离后的正文, 剥离块数)。契约块里的字不算证据。"""
    n = 0
    for pat in META_BLOCKS:
        text, k = pat.subn(" ", text)
        n += k
    return text, n


def load_contract(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def validate_contract(c: dict) -> list[str]:
    """契约纪律：无版本/无词表版本/节性质无理由变更/目标不可测 → 契约无效。"""
    errs = []
    kind = c.get("section_kind")
    if kind not in KIND_ELEMENTS:
        errs.append(f"section_kind 非法: {kind!r}，可选 {list(KIND_ELEMENTS)}")

    req = c.get("required_elements", [])
    if kind in KIND_ELEMENTS:
        derived = KIND_ELEMENTS[kind]
        missing = [e for e in derived if e not in req]
        if missing:
            errs.append(f"required_elements 减项 {missing}（{kind} 节派生 {derived}），"
                        "必须走 changelog 写理由才可减")
        unknown = [e for e in req if e not in ELEMENT_CN]
        if unknown:
            errs.append(f"未知要素 {unknown}")

    if c.get("order_contract") not in ORDERS:
        errs.append(f"order_contract 非法: {c.get('order_contract')!r}，可选 {sorted(ORDERS)}")

    objs = c.get("objectives", [])
    if not objs:
        errs.append("objectives 为空")
    for o in objs:
        if not re.match(r"读者能(解释|算出|区分|判断|说明|复述|比较|识别)", o):
            errs.append(f"教学目标不可测: {o!r}（须以「读者能+可观察动词」开头）")
        if re.search(r"掌握|了解|熟悉|理解", o):
            errs.append(f"教学目标含不可测动词: {o!r}")

    ref = c.get("known_terms_ref", "")
    m = re.fullmatch(r"([\w\-]+)@(\d+)", ref)
    if not m:
        errs.append(f"known_terms_ref 未锁版本: {ref!r}（须 name@version）")
    else:
        name, ver = m.group(1), int(m.group(2))
        vp = VOCAB_DIR / f"{name}.json"
        if not vp.exists():
            errs.append(f"词表不存在: {vp.name}")
        else:
            v = json.loads(vp.read_text(encoding="utf-8"))
            if v.get("version") != ver:
                errs.append(f"词表版本漂移: 契约引用 @{ver}，实际 v{v.get('version')}")

    if not isinstance(c.get("version"), int):
        errs.append("version 缺失或非整数")
    cl = c.get("changelog", [])
    if not any(x.get("version") == c.get("version") for x in cl):
        errs.append(f"changelog 无 version={c.get('version')} 对应记录")
    for x in cl:
        fields = x.get("fields", [])
        changed = set(fields) & {"section_kind", "required_elements"}
        if changed and not x.get("reason"):
            errs.append(f"changelog v{x.get('version')} 改了 {sorted(changed)} 但无 reason")

    return errs


def contract_diff(old: dict, new: dict) -> dict:
    """结构化字段 diff，不做整块文本对比；节性质变更高警示。"""
    keys = ["section_kind", "objectives", "known_terms_ref", "order_contract",
            "required_elements", "version", "anchors", "order_anchors"]
    changed = [k for k in keys if old.get(k) != new.get(k)]
    high = [k for k in changed if k in ("section_kind", "required_elements")]
    reason = next((x.get("reason", "") for x in new.get("changelog", [])
                   if x.get("version") == new.get("version")), "")
    return {"changed": changed, "high_risk": high,
            "reason": reason,
            "verdict": "OK" if not high or reason else "INVALID"}


def _sentences(text: str) -> list[tuple[int, str]]:
    """返回 (全文偏移, 句文本)。实质锚必须句内同窗，跨句会串味。"""
    return [(m.start(), m.group(0).strip())
            for m in re.finditer(r"[^。！？；\n]+", text) if m.group(0).strip()]


def check_ga(section_text: str, c: dict) -> dict:
    """对每要素出 是/否 + 命中位置。双层判据；契约块已由调用方剥离。"""
    req = c.get("required_elements", [])
    items = []
    for el in req:
        pats = [re.compile(p) for p in SIGNALS.get(el, [])]
        best = None
        hollow = []
        for si, (base, sent) in enumerate(_sentences(section_text)):
            for pat in pats:
                m = pat.search(sent)
                if not m:
                    continue
                s, e = max(0, m.start() - WINDOW), min(len(sent), m.end() + WINDOW)
                win = sent[s:e]
                subst = [mm.group(0) for mm in
                         (pat2.search(win) for pat2 in SUBSTANCE_RE) if mm]
                hit = {"element": el, "label": ELEMENT_CN.get(el, el),
                       "signal": m.group(0), "sentence_no": si + 1,
                       "pos": [base + m.start(), base + m.end()],
                       "evidence": sent[:90],
                       "substance": subst[:3]}
                if subst:
                    if best is None or len(subst) > len(best["substance"]):
                        best = hit
                else:
                    hollow.append(hit)
        if best:
            items.append({**best, "verdict": "HIT",
                          "note": "信号+实质锚同窗；供人工回读确认，不代表质量判定"})
        elif hollow:
            h = hollow[0]
            items.append({**h, "verdict": "HOLLOW",
                          "note": "只有信号词无实质锚（空壳），不许升 PASS；"
                                  f"另 {len(hollow)-1} 处同类"})
        else:
            items.append({"element": el, "label": ELEMENT_CN.get(el, el),
                          "verdict": "MISS", "signal": "", "substance": [],
                          "sentence_no": 0, "pos": [], "evidence": "",
                          "note": "未命中候选信号；缺要素可疑，交人工核对"})
    return {"contract_id": c.get("contract_id", ""), "items": items,
            "hit": sum(i["verdict"] == "HIT" for i in items),
            "hollow": sum(i["verdict"] == "HOLLOW" for i in items),
            "miss": sum(i["verdict"] == "MISS" for i in items),
            "policy": "教学结构检查永久 WARN 不 BLOCK；机器只定位，裁决归人"}


def _norm_anchors(raw: list) -> list[str]:
    """锚词双格式：字符串 或 {anchor/value} 对象，统一成字符串列表。"""
    out = []
    for a in raw or []:
        if isinstance(a, str):
            out.append(a)
        elif isinstance(a, dict):
            v = a.get("anchor") or a.get("value") or ""
            if v:
                out.append(v)
    return out


def check_order(section_text: str, c: dict) -> dict:
    """ORDER：核对契约声明的讲述顺序与正文首次出现位置。机器只定位。

    只读 order_anchors（logic_order CONFIRM 写入的逻辑顺序）；契约未声明
    order_anchors 时返回 SKIP，不回退 anchors（那是 G2 事实锚，不是顺序锚）。
    按声明顺序列出关键锚词；本函数返回每个锚的首次字符位置，
    并报「逆序对」（后面的锚先出现 = 顺序可疑）。判定交人。
    """
    anchors = _norm_anchors(c.get("order_anchors") or [])
    if not anchors:
        return {"verdict": "SKIP", "note": "契约未声明 order_anchors，无法核对顺序", "hits": []}
    clean = strip_meta(section_text)[0]
    clean = re.sub(r"<[^>]+>", " ", clean)
    hits = []
    for a in anchors:
        m = re.search(re.escape(a), clean)
        hits.append({"anchor": a, "pos": m.start() if m else -1,
                     "found": bool(m)})
    found = [h for h in hits if h["found"]]
    inversions = []
    for i in range(len(found)):
        for j in range(i + 1, len(found)):
            if found[j]["pos"] < found[i]["pos"]:
                inversions.append({"expected_before": found[i]["anchor"],
                                   "actually_before": found[j]["anchor"]})
    missing = [h["anchor"] for h in hits if not h["found"]]
    return {"verdict": "OK" if not inversions and not missing else "SUSPECT",
            "declared_order": anchors, "hits": hits, "inversions": inversions,
            "missing": missing,
            "note": "逆序/缺失只表示讲述顺序与契约不符，是否需重排由人裁决"}


def extract_section(html: str, section_id: str) -> str:
    """按 id 抽整节：子标题(h4…)属于本节，遇同级或更高级标题才结束。"""
    pat = re.compile(rf"<h([2-6])[^>]*id=[\"']{re.escape(section_id)}[\"'][^>]*>.*?</h\1>",
                     re.S | re.I)
    m = pat.search(html)
    if not m:
        return html
    level = int(m.group(1))
    start = m.end()
    nxt = re.search(rf"<h([2-{level}])\b", html[start:], re.I)
    return html[start:start + nxt.start()] if nxt else html[start:]


def selfcheck() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        v = {"vocab_id": "t", "version": 7, "terms": ["x"]}
        (VOCAB_DIR / "t.json").write_text(json.dumps(v), encoding="utf-8")
        try:
            base = {"contract_id": "t::s", "section_id": "s", "section_kind": "mechanism",
                    "objectives": ["读者能解释 X 为什么需要"],
                    "known_terms_ref": "t@7", "order_contract": "phenomenon_first",
                    "required_elements": ["what", "why", "how", "cost"],
                    "version": 1,
                    "changelog": [{"version": 1, "fields": ["init"], "reason": "首次"}]}
            assert validate_contract(base) == []
            bad = dict(base, objectives=["掌握 X"])
            assert any("不可测" in e for e in validate_contract(bad))
            bad = dict(base, known_terms_ref="t@6")
            assert any("漂移" in e for e in validate_contract(bad))
            bad = dict(base, required_elements=["what", "why"])
            assert any("减项" in e for e in validate_contract(bad))
            new = dict(base, version=2, section_kind="example",
                       changelog=[{"version": 2, "fields": ["section_kind"]}])
            assert contract_diff(base, new)["verdict"] == "INVALID"
            new["changelog"][0]["reason"] = "改为示例节"
            assert contract_diff(base, new)["verdict"] == "OK"

            text = ("DCQCN 由某厂商于 2015 年提出，核心是速率递减因子 α。"
                    "收到 CNP 时增大 α（更快降速），长时间没收到则减小 α，"
                    "能区分瞬时拥塞和持续拥塞。"
                    "局限是参数多、调参困难，反应式控制存在固有延迟。")
            r = check_ga(text, base)
            assert r["hit"] == 4 and r["miss"] == 0, r
            hollow = text + " 为什么？这是个好问题。为什么？"
            r2 = check_ga(hollow, base)
            assert r2["hollow"] == 0, r2  # 真节有实质锚，空壳不覆盖真命中
            only_hollow = ("某机制称为 X。为什么？这是个好问题。收到后调整参数。"
                           "代价是成本高。")
            r3 = check_ga(only_hollow, base)
            assert r3["hollow"] >= 1, r3
            stripped, n = strip_meta('<script type="application/json" id="c">'
                                     '{"why":"局限 代价 权衡 困难"}</script><p>正文</p>')
            assert n == 1 and "局限" not in stripped
            print("[OK] intent_ga selfcheck: 契约校验/字段diff/双层判据/元数据剥离")
            return 0
        finally:
            (VOCAB_DIR / "t.json").unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    ck = sub.add_parser("CHECK")
    ck.add_argument("contract")
    ck.add_argument("html")
    ck.add_argument("--section-id", default="")
    ck.add_argument("--json", action="store_true")
    df = sub.add_parser("DIFF")
    df.add_argument("old")
    df.add_argument("new")
    od = sub.add_parser("ORDER")
    od.add_argument("contract")
    od.add_argument("html")
    od.add_argument("--section-id", default="")
    od.add_argument("--json", action="store_true")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck or not a.cmd:
        return selfcheck()
    if a.cmd == "DIFF":
        print(json.dumps(contract_diff(load_contract(Path(a.old)),
                                       load_contract(Path(a.new))),
                         ensure_ascii=False, indent=2))
        return 0
    if a.cmd == "ORDER":
        c = load_contract(Path(a.contract))
        errs = validate_contract(c)
        if errs:
            print(json.dumps({"valid": False, "errors": errs}, ensure_ascii=False, indent=2))
            return 2
        raw = Path(a.html).read_text(encoding="utf-8", errors="ignore")
        sid = a.section_id or c.get("section_id", "")
        body = extract_section(raw, sid) if sid else raw
        r = check_order(body, c)
        r["contract"] = a.contract
        r["section_id"] = sid
        print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else
              f"ORDER · {c.get('contract_id','')} · 节={sid} · {r['verdict']}\n"
              + "\n".join(f"  {h['anchor']}: pos={h['pos']}" for h in r["hits"])
              + (f"\n  逆序: {r['inversions']}" if r["inversions"] else "")
              + (f"\n  缺失: {r['missing']}" if r["missing"] else ""))
        return 0
    c = load_contract(Path(a.contract))
    errs = validate_contract(c)
    if errs:
        out = {"contract": a.contract, "valid": False, "errors": errs}
        print(json.dumps(out, ensure_ascii=False, indent=2) if a.json else
              "契约无效：\n" + "\n".join("  - " + e for e in errs))
        return 2
    raw = Path(a.html).read_text(encoding="utf-8", errors="ignore")
    sid = a.section_id or c.get("section_id", "")
    body = extract_section(raw, sid) if sid else raw
    body, n_strip = strip_meta(body)
    r = check_ga(body, c)
    r["contract"] = a.contract
    r["section_id"] = sid
    r["meta_blocks_stripped"] = n_strip
    r["valid"] = True
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"意图契约 G-A · {c.get('contract_id','')} · 节={sid} · 剥离元数据块={n_strip}")
        for i in r["items"]:
            mark = {"HIT": "HIT ", "HOLLOW": "HOLLOW", "MISS": "MISS "}[i["verdict"]]
            loc = f"句{i['sentence_no']}" if i["sentence_no"] else "—"
            print(f"  [{mark}] {i['label']:<6s} {loc:<6s} 信号={i['signal'] or '—':<10s} "
                  f"实质={','.join(i['substance'][:2]) or '—'}")
            if i["verdict"] != "HIT":
                print(f"          ↳ {i['note']}")
        print(f"  合计: HIT={r['hit']} HOLLOW={r['hollow']} MISS={r['miss']} · {r['policy']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
