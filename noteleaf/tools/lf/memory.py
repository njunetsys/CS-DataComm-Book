#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lf/memory.py: Noteleaf M2 跨会话记忆。

参考 LectūraAgents 的三层记忆架构，但对象换成讲义作者/使用者：
  短期层：单次会话内存，不落盘（本模块只提供 recall 返回结构，不持久化临时状态）
  长期层：framework/memory/profile.json，存显式声明的使用者画像与交付体例
  动态层：framework/memory/decisions.jsonl，append-only 存已闭环的审稿结论与拍板

边界：只记「显式声明」和「已经 resolved 的结论」，不从未声明行为里推断个人信息。
机器只负责读回和去重，不把记忆当成质量判定。

CLI:
  python3 tools/lf/memory.py PROFILE --lecture <讲ID> [--import-prefs] [--json]
  python3 tools/lf/memory.py DECIDE --lecture <讲ID> --key <K> --value <V> [--why W] [--source S]
  python3 tools/lf/memory.py RECALL [--lecture <讲ID>] [--limit N] [--json]
  python3 tools/lf/memory.py LINK_REVIEW <review.json> [--lecture <讲ID>]
  python3 tools/lf/memory.py --selfcheck
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from lf.prefs import prefs_path  # noqa: E402

MEMORY_DIR = PROJECT_ROOT / "CloudComputing" / "framework" / "memory"
PROFILE_PATH = MEMORY_DIR / "profile.json"
DECISIONS_PATH = MEMORY_DIR / "decisions.jsonl"

SCHEMA = "lf.memory.profile/v1"

# 项目级交付体例：来自用户明确要求，不靠隐式学习
DEFAULT_GLOBAL = {
    "delivery": {
        "format": "单文件自包含 HTML",
        "layout": "窄卡片优先，不用宽表格",
        "tone": "先说人话，再给术语",
        "source": "2026-11-25 用户明确要求 / 项目交付体例",
    },
    "machine_role": {
        "rule": "机检只定位，好坏归人",
        "source": "Noteleaf 设计原则",
    },
}
# 画像只收显式字段；audience/difficulty 来自 K3 声明，dims 来自偏好矩阵
PROFILE_FIELDS = ("dims", "audience", "difficulty")


def _today() -> str:
    return datetime.date.today().isoformat()


def _now() -> str:
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def _digest(obj) -> str:
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def load_profile() -> dict:
    """读长期画像；缺文件返回带项目默认值的骨架，不自动推断个人偏好。"""
    base = {"schema": SCHEMA, "updated": "", "global": DEFAULT_GLOBAL, "lectures": {}}
    if not PROFILE_PATH.exists():
        return base
    try:
        data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return base
    if not isinstance(data, dict):
        return base
    data.setdefault("schema", SCHEMA)
    data.setdefault("updated", "")
    glob = data.setdefault("global", {})
    for k, v in DEFAULT_GLOBAL.items():
        glob.setdefault(k, v)
    data.setdefault("lectures", {})
    return data


def save_profile(data: dict) -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    data["updated"] = _now()
    PROFILE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")


def sync_from_prefs(lecture: str) -> dict:
    """把 K3 已声明的偏好快照进 M2 长期层；只写显式字段，变了才落盘。"""
    data = load_profile()
    p = prefs_path(lecture)
    if not p.exists():
        return {"changed": False, "source": "default", "profile": data,
                "note": "未声明偏好，保留默认；不写入臆测画像"}
    try:
        entry = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"changed": False, "source": "broken", "profile": data,
                "note": "偏好文件损坏，M2 不写入"}
    snap = {k: entry.get(k, "") for k in PROFILE_FIELDS}
    snap["source"] = str(p)
    snap["updated"] = _today()
    old = data["lectures"].get(lecture, {})
    if all(old.get(k) == snap[k] for k in PROFILE_FIELDS):
        return {"changed": False, "source": "prefs", "profile": data,
                "note": "画像无变化，未重复写入"}
    data["lectures"][lecture] = snap
    save_profile(data)
    return {"changed": True, "source": "prefs", "profile": data,
            "note": "K3 显式画像已快照进 M2"}


def append_decision(*, kind: str, key: str, value, lecture: str = "", why: str = "",
                    source: str = "", evidence: str = "", digest: str = "") -> dict:
    """向动态层追加一条决策；digest 非空时先查重，避免每次流水线重复写入。"""
    d = digest or _digest({"kind": kind, "key": key, "value": value,
                           "lecture": lecture, "source": source})
    if d:
        for e in load_decisions(limit=500):
            if e.get("digest") == d:
                return e
    entry = {"ts": _now(), "kind": kind, "lecture": lecture, "key": key,
             "value": value, "why": why, "source": source, "evidence": evidence,
             "digest": d}
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(DECISIONS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def load_decisions(limit: int = 0) -> list[dict]:
    if not DECISIONS_PATH.exists():
        return []
    rows = []
    for line in DECISIONS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    rows.reverse()  # 最近优先，便于 RECALL 直接取前 N 条
    return rows[:limit] if limit > 0 else rows


def recall_decisions(lecture: str = "", limit: int = 20) -> list[dict]:
    out = []
    for e in load_decisions():
        if lecture and e.get("lecture") not in ("", "_global", lecture):
            continue
        out.append(e)
        if len(out) >= limit:
            break
    return out


def recall(lecture: str = "", limit: int = 20) -> dict:
    """短期层读回视图：全局体例 + 本讲显式画像 + 最近决策。不落盘。"""
    data = load_profile()
    return {
        "schema": SCHEMA,
        "lecture": lecture,
        "global": data["global"],
        "lecture_profile": data["lectures"].get(lecture, {}) if lecture else {},
        "decisions": recall_decisions(lecture, limit),
        "privacy": "只存显式声明与已闭环结论，不推断个人信息",
    }


def link_review(review_path: Path | str, lecture: str = "") -> dict | None:
    """把 review JSON 里已 resolved 的结论回写 M2；按内容 digest 去重。"""
    p = Path(review_path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    issues = data.get("issues", []) if isinstance(data, dict) else []
    if not isinstance(issues, list):
        return None
    resolved = [i for i in issues if isinstance(i, dict) and i.get("resolved")]
    if not resolved:
        return None
    payload = [{"id": i.get("id"), "issue": i.get("issue", ""),
                "note": i.get("note", ""), "source": i.get("source", "")}
               for i in resolved]
    return append_decision(
        kind="review_resolved", key="审稿闭环回写",
        value=f"{len(resolved)} 条审稿意见已闭环",
        lecture=lecture or data.get("lecture", ""),
        why="；".join(str(i.get("issue", ""))[:40] for i in resolved[:3]),
        source=str(p), evidence=f"reviewer={data.get('reviewer', '?')}",
        digest=_digest({"kind": "review_resolved", "source": str(p), "payload": payload}))


def report(v: dict) -> str:
    L = [f"Noteleaf M2 跨会话记忆 · {v.get('lecture') or '_global'}"]
    g = v.get("global", {})
    dl = g.get("delivery", {})
    L.append(f"交付体例: {dl.get('format', '')} / {dl.get('layout', '')} / {dl.get('tone', '')}")
    lp = v.get("lecture_profile", {})
    if lp:
        L.append(f"本讲画像: 维度={lp.get('dims', [])} 受众={lp.get('audience') or '未指定'} "
                 f"难度={lp.get('difficulty') or '未指定'} (来源: {lp.get('source', '?')})")
    else:
        L.append("本讲画像: 未声明，沿用全局体例")
    L.append(f"最近决策 {len(v.get('decisions', []))} 条:")
    for e in v.get("decisions", [])[:10]:
        L.append(f"  [{e.get('kind')}] {e.get('key')}: {str(e.get('value'))[:80]}")
    L.append(v.get("privacy", ""))
    return "\n".join(L)


def selfcheck() -> int:
    global MEMORY_DIR, PROFILE_PATH, DECISIONS_PATH
    old = (MEMORY_DIR, PROFILE_PATH, DECISIONS_PATH)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        MEMORY_DIR = Path(td) / "memory"
        PROFILE_PATH = MEMORY_DIR / "profile.json"
        DECISIONS_PATH = MEMORY_DIR / "decisions.jsonl"
        s = sync_from_prefs("_selftest")
        assert s["changed"] is False and "不写入臆测画像" in s["note"]
        save_profile(load_profile())
        assert PROFILE_PATH.exists() and load_profile()["schema"] == SCHEMA
        a = append_decision(kind="decision", key="体例", value="窄卡片", lecture="_selftest")
        b = append_decision(kind="decision", key="体例", value="窄卡片", lecture="_selftest")
        assert a["digest"] == b["digest"] and len(load_decisions()) == 1
        rv = MEMORY_DIR / "review.json"
        rv.write_text(json.dumps({"lecture": "_selftest", "reviewer": "r1",
                                  "issues": [{"id": 1, "issue": "数字无出处",
                                              "resolved": True, "note": "已回源"}]},
                                 ensure_ascii=False), encoding="utf-8")
        assert link_review(rv, "_selftest") is not None
        assert len(load_decisions()) == 2
        assert len(recall("_selftest")["decisions"]) == 2
    MEMORY_DIR, PROFILE_PATH, DECISIONS_PATH = old
    print("自检 OK: 显式画像/去重决策/审稿回写/读回通过")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Noteleaf M2 跨会话记忆")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("PROFILE", aliases=["profile"])
    p.add_argument("--lecture", default="_global")
    p.add_argument("--import-prefs", action="store_true", help="把 K3 偏好快照进长期画像")
    p.add_argument("--json", action="store_true")

    d = sub.add_parser("DECIDE", aliases=["decide"])
    d.add_argument("--lecture", default="_global")
    d.add_argument("--key", required=True)
    d.add_argument("--value", required=True)
    d.add_argument("--why", default="")
    d.add_argument("--source", default="")

    r = sub.add_parser("RECALL", aliases=["recall"])
    r.add_argument("--lecture", default="")
    r.add_argument("--limit", type=int, default=20)
    r.add_argument("--json", action="store_true")

    lk = sub.add_parser("LINK_REVIEW", aliases=["link_review"])
    lk.add_argument("review")
    lk.add_argument("--lecture", default="")

    if "--selfcheck" in sys.argv:
        return selfcheck()
    a = ap.parse_args()
    if a.cmd in ("PROFILE", "profile"):
        if a.import_prefs:
            s = sync_from_prefs(a.lecture)
            if a.json:
                print(json.dumps(s, ensure_ascii=False, indent=2))
            else:
                print(s["note"])
                print(report(recall(a.lecture)))
        else:
            v = recall(a.lecture)
            print(json.dumps(v, ensure_ascii=False, indent=2) if a.json else report(v))
        return 0
    if a.cmd in ("DECIDE", "decide"):
        e = append_decision(kind="decision", key=a.key, value=a.value,
                            lecture=a.lecture, why=a.why, source=a.source)
        print(json.dumps(e, ensure_ascii=False))
        return 0
    if a.cmd in ("RECALL", "recall"):
        v = recall(a.lecture, a.limit)
        print(json.dumps(v, ensure_ascii=False, indent=2) if a.json else report(v))
        return 0
    if a.cmd in ("LINK_REVIEW", "link_review"):
        e = link_review(a.review, a.lecture)
        print(json.dumps(e, ensure_ascii=False) if e else "无已闭环意见可回写")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
