#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lf/asset_score.py: Noteleaf K2 素材评估。

对单条素材按评估卡评分（源头层级30 / 机制完整度25 / 可核对20 / 时效15 / 许可10），
输出评分 + 层标签 + 挂偏好维度，追加到 framework/asset_ledger.jsonl。

CLI:
  python3 tools/lf/asset_score.py SCORE "<name>" --layer L4 --src paper \
      --mechanism high --cite yes --recency 2026 --license cc \
      [--lecture 02_弹性计算] [--prefs_linked 机制] [--out asset_ledger.jsonl]
  python3 tools/lf/asset_score.py SCORE_FILE <file> --topics 词1 词2 \
      --layer L4 --src paper --cite yes --recency 2026 --license cc \
      [--out asset_ledger.jsonl]
  python3 tools/lf/asset_score.py LIST --out asset_ledger.jsonl
  python3 tools/lf/asset_score.py SUMMARY --out asset_ledger.jsonl

设计考量：
  - 计分透明：five 维度各自 0..1 评分，总分 = Σ(score_i × weight_i)，可复核。
  - 命中不等于取舍：评估只评分+打标，是否采用由偏好矩阵（K3）决定。
  - 条目不可变：追加式写 jsonl，同 name 冲突报错不覆盖（保护台账）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))  # 直跑时让 lf.* 可解析
DEFAULT_OUT = PROJECT_ROOT / "CloudComputing" / "framework" / "asset_ledger.jsonl"
DEFAULT_TICKETS = PROJECT_ROOT / "CloudComputing" / "framework" / "k1" / "tickets.jsonl"

WEIGHTS = {"源头层级": 0.30, "机制完整度": 0.25, "可核对": 0.20, "时效": 0.15, "许可": 0.10}

# 源头层级：论文=1.0 厂商官方/名校课程/顶级教材=0.85 一般书籍=0.6 二手=0.3
SRC_MAP = {
    "paper": 1.0, "vendor": 0.85, "course": 0.85, "book_top": 0.9,
    "book": 0.65, "blog": 0.35, "video": 0.3,
}
# 机制完整度：high=给做法(步骤/状态机/数字)，mid=给名词+一句机制，low=只给名词
MECH_MAP = {"high": 1.0, "mid": 0.6, "low": 0.3}
CITE_MAP = {"yes": 1.0, "partial": 0.6, "no": 0.2}
LIC_MAP = {"cc": 1.0, "own": 1.0, "authorized": 1.0, "unknown": 0.3, "commercial": 0.35}


def score_asset(name: str, layer: str, src: str, mechanism: str, cite: str,
                recency: int, license_s: str, user: bool = False) -> dict:
    now_y = date.today().year
    # 时效: 当年1.0，每差一年 -0.12，下限 0.2
    age = max(0, now_y - int(recency))
    rec = max(0.2, 1.0 - age * 0.12)
    scores = {
        "源头层级": SRC_MAP.get(src, 0.5),
        "机制完整度": MECH_MAP.get(mechanism, 0.5),
        "可核对": CITE_MAP.get(cite, 0.4),
        "时效": rec,
        "许可": LIC_MAP.get(license_s, 0.3),
    }
    total = round(sum(scores[k] * WEIGHTS[k] for k in WEIGHTS), 3)
    return {
        "name": name,
        "layer": layer,
        "src": src,
        "mechanism": mechanism,
        "cite": cite,
        "recency": recency,
        "license": license_s,
        "user": user,
        "scores": scores,
        "total": total,
        "ts": date.today().isoformat(),
    }


def score_file(path: Path, topics: list[str], layer: str, src: str,
               cite: str, recency: int, license_s: str,
               mode: str = "fast") -> dict:
    """读文件 → 用解析证据自动判机制完整度 → 走 K2 五维评分。

    机制判据改成有正文支撑的硬信号：结构块（标题/表）+ 主题覆盖率。
    不再靠 snippet 猜。cite 默认强制 no：机器读了正文也没资格判出处可信，
    要人工显式 --cite yes 才承认（此时 cite_basis 留痕是谁拍的板）。
    """
    from lf.doc_read import read_doc
    rd = read_doc(path, topics, mode=mode)
    h = rd["headings"] + rd["tables"]
    if h >= 5 and rd["coverage"] >= 0.5:
        mech = "high"
    elif h >= 2 or rd["coverage"] > 0:
        mech = "mid"
    else:
        mech = "low"
    entry = score_asset(rd["name"], layer, src, mech, cite, recency, license_s)
    entry["read"] = {k: rd[k] for k in
                     ("md5", "chars", "headings", "tables", "table_rows",
                      "formulas", "source", "topics", "covered_topics",
                      "coverage", "hits", "engine", "path")}
    entry["mechanism_basis"] = f"解析证据: {h} 结构块, 覆盖 {rd['covered_topics']}/{rd['topics']}"
    entry["cite_basis"] = ("人工显式声明" if cite == "yes" else
                           "机器保守置否，待人工核对出处")
    return entry


def sort_supply(rows: list[dict], layer_priority: dict[str, float]) -> list[dict]:
    """供料排序：user 条目置顶，其余按 层优先级×评估分 降序。

    原 K4 的独立排序逻辑并入此处：唯一数据源是台账，user 只是一个布尔标记，
    不再需要第二本 MANIFEST。
    """
    user, ranked = [], []
    for r in rows:
        base = {"name": r["name"], "layer": r["layer"], "score": r["total"],
                "user": bool(r.get("user")),
                "tag": f"台账 {r.get('src', '?')}"}
        if base["user"]:
            base["pri"] = 99.0
            base["tag"] = "用户自供"
            user.append(base)
        else:
            base["pri"] = round(layer_priority.get(r["layer"], 0.0) * r["total"], 3)
            ranked.append(base)
    user.sort(key=lambda x: -x["score"])   # 同为置顶时按分排
    ranked.sort(key=lambda x: -x["pri"])
    return user + ranked


def append(entry: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    existing = load(out)
    if any(e["name"] == entry["name"] for e in existing):
        raise ValueError(f"素材已存在，不覆盖: {entry['name']}")
    with open(out, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load(out: Path) -> list[dict]:
    if not out.exists():
        return []
    rows = []
    for line in out.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def summary(out: Path) -> str:
    rows = load(out)
    if not rows:
        return "台账为空"
    L = [f"素材评估台账 · {len(rows)} 条"]
    by_layer: dict[str, list] = {}
    for r in rows:
        by_layer.setdefault(r["layer"], []).append(r)
    for layer in sorted(by_layer):
        items = by_layer[layer]
        avg = sum(i["total"] for i in items) / len(items)
        L.append(f"\n[{layer}] 平均分 {avg:.3f} · {len(items)} 条")
        for i in sorted(items, key=lambda x: -x["total"]):
            L.append(f"  {i['total']:.3f}  {i['name']}")
    return "\n".join(L)


# ---------- 工单 → 台账打通（K1→K2）----------
# 层映射：论文→L4、厂商数字卡→L3、教材→L1、其他→L2
_TICKET_LAYER = {"paper": "L4", "vendor_card": "L3", "textbook": "L1"}


def layer_for_ticket(t: dict) -> str:
    return _TICKET_LAYER.get(t.get("kind", ""), "L2")


def mechanism_heuristic(snip: str) -> str:
    """从 snippet 启发式判机制完整度：有数字/步骤/状态机→high，有实质描述→mid，否则 low。"""
    if not snip:
        return "low"
    if re.search(r"\d|步骤|状态机|路径|字节|ms|流程|协议|算法", snip):
        return "high"
    if len(snip) >= 40:
        return "mid"
    return "low"


def tickets_to_ledger(tickets: Path, out: Path, dry_run: bool = False) -> dict:
    """把 K1 工单里未入台账的素材按 K2 卡自动粗打分入台账。

    mechanism 用 snippet 启发式，cite 一律标 no（出处待人工核对，得 0.2），
    回写工单 status=scored 表示已打分。打分是粗筛，最终取值由作者与偏好决定。
    """
    def _load(p: Path) -> list[dict]:
        if not p.exists():
            return []
        rows = []
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return rows

    tk = _load(tickets)
    existing = load(out)
    existing_names = {e["name"] for e in existing}
    now_y = date.today().year
    added, skipped = [], []
    for t in tk:
        name = t.get("name", "")
        if not name or name in existing_names:
            skipped.append(name)
            continue
        entry = score_asset(
            name, layer_for_ticket(t), "paper",
            mechanism_heuristic(t.get("capability_signal") or ""),
            "no", t.get("year") or now_y, t.get("license") or "unknown",
        )
        entry["src"] = t.get("kind", "paper")
        entry["source"] = t.get("source", "seed")       # seed / ragflow / vendor
        entry["urn"] = t.get("urn", "")
        if t.get("sim"):
            entry["sim"] = round(t["sim"], 3)
        if not t.get("local"):
            entry["status"] = "queued"                  # 待取素材也打分排队，进供料会靠后
        if dry_run:
            added.append(entry)
        else:
            try:
                append(entry, out)
                added.append(entry)
            except ValueError:
                skipped.append(name)

    # 回写工单 status=scored（非 dry_run）
    if not dry_run:
        fresh = _load(tickets)
        written = False
        with open(tickets, "w", encoding="utf-8") as f:
            for r in fresh:
                if r.get("name") in {e["name"] for e in added} and r.get("status") == "queued":
                    r["status"] = "scored"
                    written = True
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {"added": len(added), "skipped": len(skipped), "dry_run": dry_run,
            "entries": added}


def main() -> int:
    ap = argparse.ArgumentParser(description="Noteleaf K2 素材评估")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_score = sub.add_parser("SCORE", help="给单条素材打分并入台账")
    p_score.add_argument("name")
    p_score.add_argument("--layer", choices=["L1", "L2", "L3", "L4"], required=True)
    p_score.add_argument("--src", choices=list(SRC_MAP), required=True)
    p_score.add_argument("--mechanism", choices=list(MECH_MAP), required=True)
    p_score.add_argument("--cite", choices=list(CITE_MAP), required=True)
    p_score.add_argument("--recency", type=int, required=True, help="年份")
    p_score.add_argument("--license", choices=list(LIC_MAP), default="unknown")
    p_score.add_argument("--user", action="store_true",
                         help="标为用户自供（供料置顶），原 K4 的 user 标记")
    p_score.add_argument("--out", default=str(DEFAULT_OUT))
    p_list = sub.add_parser("LIST", help="列出台账")
    p_list.add_argument("--out", default=str(DEFAULT_OUT))
    p_sum = sub.add_parser("SUMMARY", help="汇总")
    p_sum.add_argument("--out", default=str(DEFAULT_OUT))
    p_ft = sub.add_parser("FROM_TICKETS", help="从 K1 工单把未入台账素材自动打分入台账")
    p_ft.add_argument("--tickets", default=str(DEFAULT_TICKETS))
    p_ft.add_argument("--out", default=str(DEFAULT_OUT))
    p_ft.add_argument("--dry-run", action="store_true", help="只算不改（不写台账不回写工单）")
    p_sf = sub.add_parser("SCORE_FILE", help="读文件，用解析证据打分入台账")
    p_sf.add_argument("file")
    p_sf.add_argument("--topics", nargs="*", default=[])
    p_sf.add_argument("--layer", choices=["L1", "L2", "L3", "L4"], default="L4")
    p_sf.add_argument("--src", choices=list(SRC_MAP), default="paper")
    p_sf.add_argument("--cite", choices=list(CITE_MAP), default="no",
                      help="默认 no；只有人工核对过出处才显式给 yes")
    p_sf.add_argument("--recency", type=int, default=date.today().year)
    p_sf.add_argument("--license", choices=list(LIC_MAP), default="unknown")
    p_sf.add_argument("--mode", default="fast", choices=["fast", "balanced", "no_ocr"])
    p_sf.add_argument("--user", action="store_true",
                      help="标为用户自供（供料置顶），原 K4 的 user 标记")
    p_sf.add_argument("--out", default=str(DEFAULT_OUT))
    p_sf.add_argument("--dry-run", action="store_true", help="只算不入账")
    args = ap.parse_args()

    out = Path(args.out).expanduser()
    if args.cmd == "SCORE":
        entry = score_asset(args.name, args.layer, args.src, args.mechanism,
                            args.cite, args.recency, args.license, user=args.user)
        append(entry, out)
        print(json.dumps(entry, ensure_ascii=False, indent=2))
    elif args.cmd == "LIST":
        for e in load(out):
            print(json.dumps(e, ensure_ascii=False))
    elif args.cmd == "SUMMARY":
        print(summary(out))
    elif args.cmd == "FROM_TICKETS":
        r = tickets_to_ledger(Path(args.tickets).expanduser(), out, dry_run=args.dry_run)
        print(f"（{'dry-run 预览' if r['dry_run'] else '已执行'}）新增 {r['added']} 条，"
              f"跳过 {r['skipped']} 条")
        for e in r["entries"]:
            print(f"  {e['total']:.3f}  {e.get('layer','?')}  [{e.get('source')}]  {e['name']}")
        if r["dry_run"]:
            print("…dry-run 未写台账、未回写工单")
    elif args.cmd == "SCORE_FILE":
        entry = score_file(Path(args.file).expanduser(), args.topics, args.layer,
                           args.src, args.cite, args.recency, args.license, args.mode)
        if args.user:
            entry["user"] = True
        if not args.dry_run:
            append(entry, out)
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        if args.dry_run:
            print("…dry-run 未入账", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
