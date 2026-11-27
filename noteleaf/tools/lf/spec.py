#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lf/: Noteleaf Framework 核心包。

单一真源 spec 读取 + 校验：
  - load_spec()       读 framework/spec/spec_vX.json，做结构校验
  - pipeline_order()  返回按 pipeline 顺序的阶段 id
  - spec_report()     给 human 读的 spec 摘要
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SPEC_DIR = PROJECT_ROOT / "CloudComputing" / "framework" / "spec"
SPEC_PATH = SPEC_DIR / "spec_v0.1.0.json"

REQUIRED_STAGE_FIELDS = ["id", "name", "abilities", "inputs", "outputs", "gate", "desc"]


def load_spec(path: Path | None = None) -> dict:
    p = path or SPEC_PATH
    if not p.exists():
        raise FileNotFoundError(f"spec 不存在: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    # 校验
    assert data.get("name"), "spec 缺 name"
    stages = data.get("pipeline", [])
    ids = [s["id"] for s in stages]
    assert len(ids) == len(set(ids)), f"阶段 id 重复: {ids}"
    for s in stages:
        for f in REQUIRED_STAGE_FIELDS:
            assert f in s, f"阶段 {s.get('id')} 缺字段 {f}"
    return data


def pipeline_order(spec: dict | None = None) -> list[str]:
    spec = spec or load_spec()
    return [s["id"] for s in spec["pipeline"]]


def spec_report(path: Path | None = None) -> str:
    spec = load_spec(path)
    L = [f"{spec.get('name')} spec v{spec.get('version')}"]
    L.append(f"spec 文件: {path or SPEC_PATH}")
    L.append(f"共享真源: {spec.get('shared_spec')}")
    L.append("")
    for s in spec["pipeline"]:
        L.append(f"[{s['id']:<8}] {s['name']}")
        L.append(f"    能力: {', '.join(s['abilities'])}")
        L.append(f"    输入: {', '.join(s['inputs'])}")
        L.append(f"    输出: {', '.join(s['outputs'])}")
        L.append(f"    门禁: {s['gate']}")
    return "\n".join(L)


if __name__ == "__main__":
    # 自检：能读、能过结构校验、顺序正确
    spec = load_spec()
    order = pipeline_order(spec)
    expect = ["ASSET", "ANCHOR", "WRITE", "GATE", "REVIEW", "DELIVER"]
    if order != expect:
        print(f"FAIL 顺序不符: {order}", file=sys.stderr)
        sys.exit(1)
    print(spec_report())
    print("\n自检 OK: spec 读取与结构校验通过")
    sys.exit(0)
