#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lf/preflight.py: Noteleaf O2 前置门禁（写作前约束）。

写作 WRITE 之前必须同时满足两个硬前置，缺一即阻止进入写作：
  1. K3 偏好已声明  -> framework/prefs/<lecture>_prefs.json 存在且可解析出合法维度
  2. 认知锚已就位   -> framework/anchors/<lecture>.anchor.html 存在且非空
素材供料（ASSET 产物）是 WRITE 的输入之一，此处只做 WARN，不阻塞——
避免"作者手里已有一手素材但还没过机器"时误伤；硬阻塞只留给一定会翻车的两类缺项。

门禁哲学：机器只判"有没有"+给出补齐命令，判断"好不好"交给作者（与机检只定位同哲学）。

CLI:
  python3 tools/lf/preflight.py --lecture 02_弹性计算 [--json] [--no-ledger] [--missing-only]
退出码：0=PASS（可进入写作）  1=FAIL（有硬阻塞或缺项）  2=用法错
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = PROJECT_ROOT / "CloudComputing" / "framework"
PREFS_DIR = FRAMEWORK / "prefs"
ANCHORS_DIR = FRAMEWORK / "anchors"
ASSET_LEDGER = FRAMEWORK / "asset_ledger.jsonl"
LEDGER = PROJECT_ROOT / ".workbuddy" / "ledger" / "ledger.jsonl"

VALID_DIMS = ["应用", "原理", "机制", "架构"]


def _read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def check_prefs(lecture: str) -> dict:
    p = PREFS_DIR / f"{lecture}_prefs.json"
    if not p.exists():
        return {"ok": False, "hits": 1,
                "evidence": [f"偏好未声明: {p} 不存在"],
                "fix": f"python3 tools/lf/prefs.py --declare {lecture} '[\"机制\",\"原理\"]'"}
    try:
        dims = json.loads(p.read_text(encoding="utf-8")).get("dims", [])
    except (json.JSONDecodeError, OSError) as e:
        return {"ok": False, "hits": 1, "evidence": [f"偏好文件损坏: {e}"],
                "fix": f"修复或重写 {p}"}
    bad = [d for d in dims if d not in VALID_DIMS]
    if not dims or bad:
        return {"ok": False, "hits": 1, "evidence": [f"维度非法: {dims}，合法 {VALID_DIMS}"],
                "fix": f"python3 tools/lf/prefs.py --declare {lecture} '[\"机制\",\"原理\"]'"}
    return {"ok": True, "hits": 0, "evidence": [f"偏好已声明 {dims}"], "fix": ""}


# O1 通用写作规则检查：锚不再按讲存，是一份跨讲共用的写作规则。
# 查九节规则是否齐备（照 OpenMAIC 判结构合法），不查规则写得好不好。
ANCHOR_RULES = ANCHORS_DIR / "ANCHOR_RULES.html"
ANCHOR_PARTS = {
    "深度判据": r"深度判据|验收线",
    "知识态轨迹": r"知识态轨迹|进入时学生已有",
    "四板斧": r"四板斧|找支点|给来由",
    "可核对锚": r"可核对锚纪律|锚点纪律|字面检索确认",
    "图注规范": r"图注与实现规范|图前引入句",
    "五动作审稿": r"五动作审稿|改写者不得自审",
    "体例红线": r"体例红线|自包含单 HTML",
    "结构契约": r"结构契约|必填字段齐备",
    "写前握手": r"写前握手|先定结构再写正文",
}
ANCHOR_MIN_SECTION = 40  # h2 到下一 h2 之间的正文字数下限，低于此算空节（WARN）


def inspect_anchor(p: Path) -> dict:
    """锚结构体检。返回 {ok,hits,evidence,warn,fix}。
    ok=False 只因缺必检部件或文件不可读；空节/id 重复为 WARN 不阻塞。"""
    import re
    if not p.exists():
        return {"ok": False, "hits": 1, "warn": False,
                "evidence": [f"认知锚未就位: {p} 不存在"],
                "fix": f"把认知锚 HTML 放入 {ANCHORS_DIR}，命名为 {p.name}"}
    raw = p.read_text(encoding="utf-8", errors="ignore")
    # 去 style/script 与标签，留正文供部件匹配
    text = re.sub(r"<(style|script)\b[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    evidence, missing = [], []
    for name, pat in ANCHOR_PARTS.items():
        if re.search(pat, text):
            evidence.append(f"{name}✓")
        else:
            missing.append(name)
    warns = []
    if missing:
        evidence.append(f"缺部件: {'、'.join(missing)}")

    # 软检：h2 id 重复
    ids = re.findall(r"<h2[^>]*\bid=[\"']([^\"']+)", raw, flags=re.I)
    dup = {x for x in ids if ids.count(x) > 1}
    if dup:
        warns.append(f"h2 id 重复: {'、'.join(sorted(dup))}")
    # 软检：空节（h2 分段正文过短）
    secs = re.split(r"<h2\b", raw, flags=re.I)[1:]
    short = []
    for i, sec in enumerate(secs, 1):
        body = re.sub(r"<[^>]+>", " ", sec)
        body = re.sub(r"\s+", "", body)
        if 0 < len(body) < ANCHOR_MIN_SECTION:
            short.append(f"第{i}段({len(body)}字)")
    if short:
        warns.append(f"空节: {'、'.join(short[:5])}")
    evidence += warns

    ok = not missing
    return {
        "ok": ok, "hits": len(missing) + len(warns),
        "warn": False,  # 部件缺失是硬阻塞，不进软提醒
        "evidence": evidence,
        "soft": warns,
        "fix": ("补齐锚部件: " + "、".join(missing)) if missing else "",
    }


def check_anchor(lecture: str) -> dict:
    """通用写作规则检查。lecture 仅为接口兼容，规则跨讲共用一份。"""
    r = inspect_anchor(ANCHOR_RULES)
    r["evidence"].insert(0, (f"写作规则 {ANCHOR_RULES.stat().st_size}B（跨讲共用）"
                             if ANCHOR_RULES.exists() else "写作规则未就位"))
    return r


def check_assets(lecture: str) -> dict:
    rows = _read_jsonl(ASSET_LEDGER)
    if not rows:
        return {"ok": True, "warn": True, "hits": 1,
                "evidence": ["素材台账为空：无供料排序，写作需自行说明素材来源"],
                "fix": "python3 tools/lf/asset_score.py SUMMARY"}
    names = [r["name"] for r in rows]
    return {"ok": True, "warn": False, "hits": 0,
            "evidence": [f"素材台账 {len(rows)} 条: {', '.join(names[:5])}{'…' if len(names)>5 else ''}"],
            "fix": ""}


def run_preflight(lecture: str, stage: str = "WRITE") -> dict:
    gates = [
        {"name": "prefs", **check_prefs(lecture)},
        {"name": "anchor", **check_anchor(lecture)},
        {"name": "assets", **check_assets(lecture)},
    ]
    hard_block = [g for g in gates if g["ok"] is False]
    warns = [g for g in gates if g.get("warn")]
    verdict = "PASS" if not hard_block else "FAIL"
    # 落账 schema 与 check_chain 对齐：gates[].hits=int 计数、evidence=命中明细
    return {
        "ts": date.today().isoformat(),
        "target": lecture,
        "kind": "preflight",
        "stage": stage,
        "verdict": verdict,
        "gates": [{"name": g["name"], "ok": g["ok"],
                   "hits": g["hits"], "evidence": g["evidence"],
                   "fix": g["fix"], "warn": g.get("warn", False)}
                  for g in gates],
        "blocked": [g["name"] for g in hard_block],
        "warnings": [g["name"] for g in warns],
    }


def append_ledger(entry: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Noteleaf O2 前置门禁")
    ap.add_argument("--lecture", required=True, help="讲 ID，如 02_弹性计算")
    ap.add_argument("--stage", default="WRITE")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-ledger", action="store_true")
    ap.add_argument("--missing-only", action="store_true",
                    help="只输出缺失项（便于脚本/agent 判断）")
    args = ap.parse_args()

    result = run_preflight(args.lecture, args.stage)
    if not args.no_ledger:
        append_ledger(result)

    if args.missing_only:
        for g in result["gates"]:
            if g["ok"] is False or g["warn"]:
                print(f"{'FAIL' if g['ok'] is False else 'WARN'} {g['name']}: {g['fix']}")
    elif args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"O2 前置门禁 · {args.lecture} ({args.stage})")
        for g in result["gates"]:
            status = "FAIL" if g["ok"] is False else ("WARN" if g["warn"] else "PASS")
            print(f"  [{status}] {g['name']}: {'; '.join(g['evidence'])}")
            if g["fix"]:
                print(f"         ↳ {g['fix']}")
        print(f"结论: {result['verdict']} （阻塞项: {result['blocked'] or '无'}"
              f" / 提醒: {result['warnings'] or '无'}）")

    return 1 if result["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
