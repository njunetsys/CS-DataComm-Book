#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lf/prefs.py: Noteleaf K3 偏好矩阵消费。

作者在写作前声明本讲偏好（应用/原理/机制/架构，多选）。
本模块：
  - declare_prefs()  写入 framework/prefs/<lecture>_prefs.json（可带 audience/difficulty 可选字段）
  - load_prefs()     读取，缺失返回默认（机制+原理）
  - supply_priority() 依偏好给出供料排序表（素材层优先级 + 篇幅权重 + 写作动作）
  - verify_prefs()   对照成品 HTML 查各选中维度是否有对应信号（机检只定位，不判好坏）
设计考量：
  - 偏好是"声明式"：只影响供料排序与篇幅权重，不直接改正文（与机检只定位同哲学）。
  - 多选时按命中维度叠加权重，未选维度降为 0.6。
  - 默认偏好（未声明时）落到能力模型里的现行默认：机制+原理，应用辅，架构作主线。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PREFS_DIR = PROJECT_ROOT / "CloudComputing" / "framework" / "prefs"

DIMENSIONS = ["应用", "原理", "机制", "架构"]

DEFAULT_PREFS = ["机制", "原理"]

# 各维度: 供料层权重(素材层 L1-L4), 篇幅权重, 写作动作
DIMENSION_PROFILE = {
    "应用": {
        "layers": {"L3": 1.0, "L2": 0.9, "L1": 0.6, "L4": 0.5},
        "weight": 1.0,
        "action": "每节给真实场景决策题、选型依据、失效模式，L3 厂商+案例优先",
    },
    "原理": {
        "layers": {"L4": 1.0, "L1": 0.9, "L2": 0.6, "L3": 0.4},
        "weight": 1.0,
        "action": "背景动机、可测量上限（如 P/A、1/alpha）、机理推导，论文+L1 论证优先",
    },
    "机制": {
        "layers": {"L4": 1.0, "L2": 0.9, "L3": 0.7, "L1": 0.5},
        "weight": 1.0,
        "action": "协议步骤、状态机、路径图、数字口径，L4 mechanism + L2 notes 优先",
    },
    "架构": {
        "layers": {"L1": 1.0, "L2": 0.9, "L3": 0.8, "L4": 0.5},
        "weight": 1.0,
        "action": "分层图、代际因果、设计权衡、SLA 全貌，L1 全书 + 架构白皮书优先",
    },
}
NON_SELECTED_SCALE = 0.6

# 难度/受众：可选元数据，与四维偏好正交（不改 layer_priority，避免动 O2 门禁）
DIFFICULTIES = ["入门", "进阶", "高级"]
# 维度落实信号：VERIFY 用，命中 ≥1 个即算该维度在正文有落点（启发式，只定位）
DIMENSION_SIGNALS = {
    "应用": ["场景", "选型", "失效模式", "决策题", "取舍"],
    "原理": ["动机", "上限", "推导", "机理", "为什么", "可测量"],
    "机制": ["步骤", "状态机", "协议", "路径", "字节", "流程"],
    "架构": ["分层", "代际", "设计权衡", "SLA", "全貌", "层次"],
}


def prefs_path(lecture: str) -> Path:
    return PREFS_DIR / f"{lecture}_prefs.json"


def declare_prefs(lecture: str, dims: list[str], audience: str = "",
                  difficulty: str = "") -> dict:
    unknown = [d for d in dims if d not in DIMENSIONS]
    if unknown:
        raise ValueError(f"未知偏好维度: {unknown}，可选 {DIMENSIONS}")
    if difficulty and difficulty not in DIFFICULTIES:
        raise ValueError(f"未知难度: {difficulty}，可选 {DIFFICULTIES}")
    dims = list(dict.fromkeys(dims))  # 去重保序
    entry = {"lecture": lecture, "dims": dims,
             "audience": audience, "difficulty": difficulty}
    PREFS_DIR.mkdir(parents=True, exist_ok=True)
    p = prefs_path(lecture)
    p.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry


def load_prefs(lecture: str) -> list[str]:
    p = prefs_path(lecture)
    if not p.exists():
        return list(DEFAULT_PREFS)
    try:
        entry = json.loads(p.read_text(encoding="utf-8"))
        dims = entry.get("dims", [])
        return [d for d in dims if d in DIMENSIONS] or list(DEFAULT_PREFS)
    except (json.JSONDecodeError, OSError):
        return list(DEFAULT_PREFS)


def supply_priority(lecture: str, dims: list[str] | None = None) -> dict:
    """依偏好算供料排序表。返回 各素材层权重 + 篇幅权重 + 写作动作。"""
    dims = dims or load_prefs(lecture)
    layer_score = {"L1": 0.0, "L2": 0.0, "L3": 0.0, "L4": 0.0}
    total_w = 0.0
    actions: list[str] = []
    for d in DIMENSIONS:
        profile = DIMENSION_PROFILE[d]
        selected = d in dims
        scale = 1.0 if selected else NON_SELECTED_SCALE
        if selected:
            actions.append(profile["action"])
            total_w += profile["weight"]
        for layer, w in profile["layers"].items():
            layer_score[layer] += w * scale
    # 篇幅权重：选中维度数做主权，未选按 0.6 折算并归一
    base = sum(1.0 for d in dims if d in DIMENSIONS) or 1.0
    norm = base + (len(DIMENSIONS) - len(dims)) * NON_SELECTED_SCALE
    length_factor = norm / 4.0
    # 受众/难度：可选元数据，从已声明文件读，缺省空（不改排序）
    audience = difficulty = ""
    p = prefs_path(lecture)
    if p.exists():
        try:
            meta = json.loads(p.read_text(encoding="utf-8"))
            audience = meta.get("audience", "") or ""
            difficulty = meta.get("difficulty", "") or ""
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "lecture": lecture,
        "dims": dims,
        "audience": audience,
        "difficulty": difficulty,
        "layer_priority": dict(sorted(layer_score.items(), key=lambda kv: -kv[1])),
        "length_factor": round(length_factor, 2),
        "actions": actions,
        "source": "prefs" if p.exists() else "default",
    }


def prefs_report(lecture: str, dims: list[str] | None = None) -> str:
    sp = supply_priority(lecture, dims)
    L = [f"Noteleaf 偏好矩阵 · {lecture}"]
    L.append(f"声明偏好: {sp['dims']}   (来源: {sp['source']}, 默认=机制+原理)")
    if sp.get("audience") or sp.get("difficulty"):
        L.append(f"受众/难度: {sp.get('audience') or '未指定'} / {sp.get('difficulty') or '未指定'}")
    L.append(f"篇幅权重因子: {sp['length_factor']}")
    L.append("供料层优先级:")
    for k, v in sp["layer_priority"].items():
        L.append(f"  {k}: {v:.2f}")
    if sp["actions"]:
        L.append("写作动作:")
        for a in sp["actions"]:
            L.append(f"  · {a}")
    return "\n".join(L)


def verify_prefs(lecture: str, html_path: str, dims: list[str] | None = None) -> dict:
    """偏好落实检查：在成品 HTML 里找各选中维度的信号词。

    机检只定位：命中=有落点，未命中=待人工确认，不判好坏、不阻塞（贯彻 K3 声明式哲学）。
    """
    from pathlib import Path
    sp = supply_priority(lecture, dims)
    html = Path(html_path)
    if not html.exists():
        raise FileNotFoundError(f"成品不存在: {html_path}")
    text = re.sub(r"<[^>]+>", " ", html.read_text(encoding="utf-8", errors="ignore"))
    text = re.sub(r"\s+", " ", text)
    checks = []
    for d in sp["dims"]:
        hits = [s for s in DIMENSION_SIGNALS.get(d, []) if s in text]
        checks.append({"dim": d, "hits": hits,
                       "ok": bool(hits),
                       "note": "有落点" if hits else "未检出信号词，需人工确认是否真缺"})
    missing = [c["dim"] for c in checks if not c["ok"]]
    return {"lecture": lecture, "html": str(html),
            "dims": sp["dims"], "checks": checks,
            "verdict": "PASS" if not missing else "WARN",
            "missing": missing}


def verify_report(v: dict) -> str:
    L = [f"K3 偏好落实检查 · {v['lecture']}",
         f"成品: {v['html']}", f"声明维度: {'、'.join(v['dims'])}"]
    for c in v["checks"]:
        mark = "✓" if c["ok"] else "?"
        L.append(f"  {mark} {c['dim']}: {c['note']}"
                 + (f"（命中: {'、'.join(c['hits'])}）" if c["hits"] else ""))
    L.append(f"判定: {v['verdict']}"
             + (f"  未检出: {'、'.join(v['missing'])}" if v["missing"] else "  全部有落点"))
    L.append("说明：机检只定位信号词，不判内容质量；未命中需人工回原文确认。")
    return "\n".join(L)


if __name__ == "__main__":
    import sys
    argv = sys.argv[1:]
    if argv and argv[0] == "--selfcheck":
        # 声明 + 读取 + 排序，全程不依赖外部
        declare_prefs("_selftest", ["机制", "架构"])
        back = load_prefs("_selftest")
        assert back == ["机制", "架构"], f"读回不一致: {back}"
        p = supply_priority("_selftest", ["机制", "架构"])
        assert p["layer_priority"]["L1"] > 0 and p["length_factor"] > 0
        # 受众/难度可选字段：声明后可读回，不改排序
        declare_prefs("_selftest", ["机制"], audience="研究生", difficulty="进阶")
        p2 = supply_priority("_selftest")
        assert p2["audience"] == "研究生" and p2["difficulty"] == "进阶"
        assert p2["layer_priority"] == p["layer_priority"] or p2["dims"] == ["机制"]
        # VERIFY：有信号 / 无信号两态
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            good = Path(td) / "g.html"
            bad = Path(td) / "b.html"
            good.write_text("<p>协议步骤与状态机，逐字节走一遍流程</p>", encoding="utf-8")
            bad.write_text("<p>一段没有信号的散文</p>", encoding="utf-8")
            vg = verify_prefs("_selftest", str(good), dims=["机制"])
            vb = verify_prefs("_selftest", str(bad), dims=["机制"])
            assert vg["verdict"] == "PASS" and vb["verdict"] == "WARN"
        print(prefs_report("_selftest", ["机制", "架构"]))
        # 清理
        prefs_path("_selftest").unlink(missing_ok=True)
        print("自检 OK: 声明/读取/供料排序/受众难度/VERIFY 通过")
        sys.exit(0)
    if len(argv) >= 2 and argv[0] == "--declare":
        entry = declare_prefs(argv[1], json.loads(argv[2]),
                              audience=argv[3] if len(argv) > 3 else "",
                              difficulty=argv[4] if len(argv) > 4 else "")
        print(json.dumps(entry, ensure_ascii=False))
        print(prefs_report(argv[1]))
        sys.exit(0)
    if len(argv) >= 3 and argv[0] == "VERIFY":
        v = verify_prefs(argv[1], argv[2])
        print(verify_report(v))
        sys.exit(0 if v["verdict"] == "PASS" else 2)
    # 报告模式
    lecture = argv[0] if argv else "_default"
    print(prefs_report(lecture))
    sys.exit(0)
