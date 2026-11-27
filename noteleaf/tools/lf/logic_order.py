#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lf/logic_order.py: 逻辑顺序工具（2026-11-25）。

用户机制：材料自带逻辑 → 工具抽取 → 评价候选 → 提案给用户确认 → 确认后写契约 →
正文按契约组织材料，ORDER 检查回读核对。机器只抽取与打分，裁决交人。

三段命令：
  EXTRACT <inputs目录>          从素材抽章节骨架并映射到概念，输出每份材料的概念顺序
  PROPOSE <inputs目录> --section <节> [--current a,b,c]
                                汇总候选顺序，按 L1先修/L2共识/覆盖 打分，输出 top-k 提案
  CONFIRM <contract.json> --order a,b,c [--reason ...]
                                把用户选定顺序写进契约 order_anchors（version+1，changelog 记理由）

概念映射表：inputs/<part>/concept_map.json（可选，缺省用内置数据中心网络拓扑表）。
格式：{"概念名": {"pats": [英文章节标题正则...], "prereq": [先修概念...]}}
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

# ---------- 内置概念表：数据中心网络拓扑演进（part4 1.2 试点用） ----------
DEFAULT_CONCEPT_MAP = {
    "传统三层架构": {
        "pats": [r"current data center", r"existing", r"hierarch", r"three[- ]tier",
                 r"oversubscription", r"background", r"motivation"],
        "prereq": [],
    },
    "CLOS": {
        "pats": [r"clos"],
        "prereq": ["传统三层架构"],
    },
    "Fat-Tree": {
        "pats": [r"fat[- ]?tree"],
        "prereq": ["CLOS"],
    },
    "Leaf-Spine": {
        "pats": [r"leaf[- ]?spine", r"spine"],
        "prereq": ["CLOS"],
    },
    "Jupiter": {
        "pats": [r"jupiter", r"direct[- ]connect"],
        "prereq": ["CLOS"],
    },
    "路由/流量工程": {
        "pats": [r"routing", r"traffic.{0,10}engineering", r"flow schedul",
                 r"addressing", r"lookup", r"ecmp"],
        "prereq": [],
    },
    "评估": {
        "pats": [r"evaluation", r"experiment", r"results"],
        "prereq": [],
    },
}


def load_concept_map(inputs_dir: Path) -> dict:
    p = inputs_dir / "concept_map.json"
    if p.exists():
        raw = json.loads(p.read_text(encoding="utf-8"))
        return {k: v for k, v in raw.items() if not k.startswith("_")}
    return DEFAULT_CONCEPT_MAP


def load_manifest(inputs_dir: Path) -> list[dict]:
    p = inputs_dir / "manifest.json"
    if not p.exists():
        sys.exit(f"缺 manifest.json: {p}")
    return json.loads(p.read_text(encoding="utf-8")).get("materials", [])


def extract_headings(md_text: str) -> list[str]:
    """抽 Markdown 标题行（marker 输出 ## 开头），去掉编号与伪影。"""
    heads = []
    for line in md_text.splitlines():
        m = re.match(r"^#{1,4}\s+(.+)$", line.strip())
        if not m:
            continue
        t = m.group(1).strip()
        # 过滤伪影：纯数字/公式/代码行
        if re.match(r"^[\d.\s\-/]+$", t) or len(t) < 3:
            continue
        heads.append(t)
    return heads


def classify_all(title: str, cmap: dict) -> list[str]:
    """一个标题可能含多个概念（如 Clos Networks/Fat-Trees）：返回全部命中，
    按各自最早匹配位置排序，避免单概念丢失或泛词抢专词。"""
    hits = []
    for concept, spec in cmap.items():
        first = -1
        for p in spec.get("pats", []):
            m = re.search(p, title, re.I)
            if m and (first == -1 or m.start() < first):
                first = m.start()
        if first >= 0:
            hits.append((first, concept))
    return [c for _, c in sorted(hits)]


def order_from_headings(heads: list[str], cmap: dict) -> list[str]:
    """标题序列 → 概念顺序（去重保序，标题内多概念按位置）。"""
    order = []
    for h in heads:
        for c in classify_all(h, cmap):
            if c not in order:
                order.append(c)
    return order


def merge_orders(heading_order: list[str], intro_order: list[str],
                 w_head: float = 2.0, w_intro: float = 1.0) -> list[str]:
    """章节骨架(作者明示逻辑)为主、引言首次提及序为辅，按加权平均位置合并。
    只在一个信号里出现的概念按所在序列位置参与，不强行追加到尾部。"""
    concepts = list(heading_order)
    for c in intro_order:
        if c not in concepts:
            concepts.append(c)

    def pos(order: list[str], c: str) -> float:
        return order.index(c) / max(len(order) - 1, 1) if c in order else 1.0

    score = {}
    for c in concepts:
        s, w = 0.0, 0.0
        if c in heading_order:
            s += w_head * pos(heading_order, c); w += w_head
        if c in intro_order:
            s += w_intro * pos(intro_order, c); w += w_intro
        score[c] = s / w if w else 1.0
    return sorted(concepts, key=lambda c: score[c])


def intro_order(md_text: str, cmap: dict) -> list[str]:
    """引言段首次提及序：章节骨架漏掉的概念（如 Jupiter 正文里的 CLOS）
    通常在 INTRODUCTION 里按讲述顺序出现。只取引言，避免相关工作节串味。"""
    m = re.search(r"^#{1,4}\s+\d*\.?\s*INTRODUCTION\b", md_text, re.I | re.M)
    if not m:
        return []
    rest = md_text[m.end():]
    nxt = re.search(r"^#{1,4}\s+\d", rest, re.M)
    intro = rest[:nxt.start()] if nxt else rest
    pos = []
    for concept, spec in cmap.items():
        first = -1
        for p in spec.get("pats", []):
            mm = re.search(p, intro, re.I)
            if mm and (first == -1 or mm.start() < first):
                first = mm.start()
        if first >= 0:
            pos.append((first, concept))
    return [c for _, c in sorted(pos)]


def cmd_extract(inputs_dir: Path) -> dict:
    cmap = load_concept_map(inputs_dir)
    out = {}
    for mat in load_manifest(inputs_dir):
        md = inputs_dir / mat["md"]
        if not md.exists():
            out[mat["id"]] = {"error": f"md 不存在: {md}"}
            continue
        text = md.read_text(encoding="utf-8", errors="ignore")
        heads = extract_headings(text)
        ho = order_from_headings(heads, cmap)
        io_ = intro_order(text, cmap)
        merged = merge_orders(ho, io_)
        out[mat["id"]] = {
            "title": mat.get("title", ""),
            "headings": heads,
            "heading_order": ho,
            "intro_order": io_,
            "concept_order": merged,
        }
    return out


def _kendall_like(order: list[str], ref: list[str]) -> float:
    """候选顺序对参考顺序的一致率（只看两者共有的概念对）。"""
    common = [c for c in order if c in ref]
    pairs, agree = 0, 0
    for i in range(len(common)):
        for j in range(i + 1, len(common)):
            a, b = common[i], common[j]
            if a in ref and b in ref:
                pairs += 1
                if ref.index(a) < ref.index(b):
                    agree += 1
    return agree / pairs if pairs else 1.0


def cmd_propose(inputs_dir: Path, section: str, current: list[str] | None) -> dict:
    cmap = load_concept_map(inputs_dir)
    ext = cmd_extract(inputs_dir)
    source_orders = {mid: v["concept_order"] for mid, v in ext.items()
                     if v.get("concept_order")}

    # 概念全集 = 各材料顺序的并集（保序）+ current 补充
    universe: list[str] = []
    for o in list(source_orders.values()) + ([current] if current else []):
        for c in o:
            if c not in universe:
                universe.append(c)

    def l1_score(order: list[str]) -> tuple[int, int]:
        """先修满足率：prereq 在 order 里出现时，必须排在依赖者之前。"""
        ok, tot = 0, 0
        for c in order:
            for pre in cmap.get(c, {}).get("prereq", []):
                if pre in order:
                    tot += 1
                    if order.index(pre) < order.index(c):
                        ok += 1
        return ok, tot

    def l2_score(order: list[str]) -> float:
        if not source_orders:
            return 0.0
        return sum(_kendall_like(order, ref) for ref in source_orders.values()) / len(source_orders)

    def coverage(order: list[str]) -> float:
        return len([c for c in universe if c in order]) / len(universe) if universe else 1.0

    def score(order: list[str]) -> dict:
        ok, tot = l1_score(order)
        return {"order": order,
                "L1先修": f"{ok}/{tot}",
                "L2材料共识": round(l2_score(order), 3),
                "覆盖": round(coverage(order), 3),
                "总分": round((ok / tot if tot else 1.0) * 0.4
                              + l2_score(order) * 0.4 + coverage(order) * 0.2, 3)}

    # 候选：每份材料顺序补全到全集 + current + 先修拓扑序
    cands: dict[str, list[str]] = {}
    for mid, o in source_orders.items():
        full = list(o) + [c for c in universe if c not in o]
        cands[f"{mid} 顺序补全"] = full
    if current:
        cands["当前讲义顺序"] = current
    # 先修拓扑序（Kahn，按 universe 出现序破平局）
    indeg = {c: 0 for c in universe}
    edges = []
    for c in universe:
        for pre in cmap.get(c, {}).get("prereq", []):
            if pre in indeg:
                indeg[c] += 1
                edges.append((pre, c))
    topo, ready = [], [c for c in universe if indeg[c] == 0]
    while ready:
        n = ready.pop(0)
        topo.append(n)
        for a, b in edges:
            if a == n:
                indeg[b] -= 1
                if indeg[b] == 0:
                    ready.append(b)
    if len(topo) == len(universe):
        cands["先修拓扑序"] = topo

    scored = sorted((score(o) for o in cands.values()),
                    key=lambda x: -x["总分"])
    # 去重（同 order 只留一个）
    seen, uniq = set(), []
    for s in scored:
        key = tuple(s["order"])
        if key not in seen:
            seen.add(key)
            uniq.append(s)
    return {"section": section, "universe": universe,
            "source_orders": source_orders,
            "candidates": uniq,
            "note": "机器只打分提案，选哪个由作者定；选定后用 CONFIRM 写进契约"}


def cmd_confirm(contract_path: Path, order: list[str], reason: str) -> dict:
    c = json.loads(contract_path.read_text(encoding="utf-8"))
    old = c.get("order_anchors")
    c["order_anchors"] = [{"anchor": a, "source_ref": "logic_order CONFIRM"} for a in order]
    c["version"] = int(c.get("version", 0)) + 1
    c.setdefault("changelog", []).append({
        "version": c["version"], "fields": ["order_anchors"],
        "reason": reason or f"逻辑顺序确认（旧值 {old}）"})
    contract_path.write_text(json.dumps(c, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    return {"contract": str(contract_path), "version": c["version"],
            "order_anchors": order}


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    ex = sub.add_parser("EXTRACT")
    ex.add_argument("inputs")
    pr = sub.add_parser("PROPOSE")
    pr.add_argument("inputs")
    pr.add_argument("--section", required=True)
    pr.add_argument("--current", default="", help="当前讲义顺序，逗号分隔")
    cf = sub.add_parser("CONFIRM")
    cf.add_argument("contract")
    cf.add_argument("--order", required=True, help="选定顺序，逗号分隔")
    cf.add_argument("--reason", default="")
    a = ap.parse_args()
    if a.cmd == "EXTRACT":
        print(json.dumps(cmd_extract(Path(a.inputs)), ensure_ascii=False, indent=2))
    elif a.cmd == "PROPOSE":
        cur = [x.strip() for x in a.current.split(",") if x.strip()] or None
        print(json.dumps(cmd_propose(Path(a.inputs), a.section, cur),
                         ensure_ascii=False, indent=2))
    elif a.cmd == "CONFIRM":
        order = [x.strip() for x in a.order.split(",") if x.strip()]
        print(json.dumps(cmd_confirm(Path(a.contract), order, a.reason),
                         ensure_ascii=False, indent=2))
    else:
        ap.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
