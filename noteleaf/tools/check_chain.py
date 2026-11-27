#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_chain: 讲义/教材质检编排器（Noteleaf M1）

把散落在 skill 与 tools 里的校验脚本收口为一条可复现的 gate 链：
自动识别目标资产类型（LaTeX 章节 / 单文件 HTML / PPTX），按序跑对应门禁，
汇总为统一 JSON 台账（含 md5、时间戳、每门命中、真/假阳性留白），提供 human 与 json 两种输出。

用法:
  tools/check_chain.py <path> [--kind auto|tex|html|pptx] [--json] [--out FILE] [--allow-vendor]
示例:
  tools/check_chain.py manuscript-v10                          # LaTeX 全书
  tools/check_chain.py manuscript-v10/chapter05_xxx.tex        # 单章
  tools/check_chain.py DaaC/part1.html                         # HTML 讲义（自动探测）
  tools/check_chain.py CloudComputing/xx.pptx --kind pptx      # PPTX 包
  tools/check_chain.py manuscript-v10 --json --out /tmp/ledger.json

设计要点（Noteleaf）:
  - 门禁是状态机: 每门输出 ok/fail，全链终止码 = 有无 FAIL。
  - 台账 JSON 单源: 每次跑写一行 run 记录，future 汇总"拦错曲线"用。
  - 只定位不做判断: 机检命中留 human_verify 占位，判定交人（五动作审稿）。
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------- 常数 ----------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHECK_REDLINES = Path.home() / ".workbuddy/skills/textbook-writing/scripts/check_redlines.py"
CHECK_HTML = Path.home() / ".workbuddy/skills/book-production/scripts/check_html_delivery.py"
VERIFY_DECK = Path.home() / ".workbuddy/skills/lecture-ppt/scripts/verify_deck.py"
CHECK_CHAPTER = SCRIPT_DIR / "check_chapter.sh"
LEDGER_DIR = PROJECT_ROOT / ".workbuddy" / "ledger"

# 机器可判的"红线失败"正则（来自 check_redlines 的核心项，作为独立 gate 的兜底）
PROSE_DASH = re.compile(r"[—–]")
NUM_RANGE = re.compile(r"\d--\d")
TILDE_CMD = re.compile(r"\\textasciitilde")
VENDOR_RE = re.compile(r"阿里|腾讯|华为|昇腾|洛神|神龙|盘古|XGW|AVS|TGW|CLB")
OUTLINK = re.compile(r'(src|href)="https?://|url\(https?://')


def md5_of(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list, cwd=None, timeout=600) -> tuple[int, str]:
    """跑子进程，返回 (returncode, 合并输出)。"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except FileNotFoundError as e:
        return 127, f"命令不存在: {e}"
    except subprocess.TimeoutExpired:
        return 124, "超时"


def probe_kind(p: Path, hint: str) -> str:
    """自动探测目标资产类型。"""
    if hint != "auto":
        return hint
    if p.is_dir():
        return "tex"
    name = p.name.lower()
    if name.endswith(".pptx"):
        return "pptx"
    if name.endswith(".html") or name.endswith(".htm"):
        return "html"
    if name.endswith(".tex"):
        return "tex"
    ext = p.suffix.lower()
    if ext in (".pdf", ".md", ".txt", ""):
        return "tex"  # 目录/教材源默认走 tex 红线
    return "html"


# ---------- gate 实现 ----------
# 每个 gate: (name, desc) -> (ok: bool, detail: str, hits: int)

def gate_tex_compile(chap: str) -> dict:
    """LaTeX 单章编译：页数/错误/未定义/缺图/Overfull（复用 check_chapter.sh）。"""
    rc, out = run(["bash", str(CHECK_CHAPTER), chap])
    lines = out.splitlines()
    first = lines[0] if lines else "无输出"
    warn_lines = [l.strip() for l in lines if "WARN" in l or "!" in l]
    ok = rc == 0 and not warn_lines
    return {"name": "tex_compile", "ok": ok, "detail": first,
            "hits": len(warn_lines),
            "evidence": warn_lines[:5]}


def gate_tex_all() -> dict:
    """LaTeX 全书：编译 + 红线 + 引用。"""
    rc, out = run(["bash", str(CHECK_CHAPTER), "all"], timeout=900)
    warn_lines = [l.strip() for l in out.splitlines() if "WARN" in l]
    ok = rc == 0 and not warn_lines
    return {"name": "tex_compile_all", "ok": ok, "detail": f"{len(warn_lines)} 章 WARN",
            "hits": len(warn_lines), "evidence": warn_lines[:10]}


def run_py(script: Path, args: list, timeout=900) -> tuple[int, str]:
    return run([sys.executable, str(script)] + args, timeout=timeout)


def gate_redlines(target: str) -> dict:
    """红线体检：破折号/厂商名/todo/浮动体孤儿/跨章可证伪/图引用体例。"""
    rc, out = run_py(CHECK_REDLINES, [target], timeout=900)
    # 提取 A/B/C/D 计数
    m = re.search(r"A=(\d+)\s+B=(\d+)\s+C=(\d+)\s+D=(\d+)", out)
    if m:
        a, b, c, d = (int(x) for x in m.groups())
        detail = f"红线A={a} 厂商B={b} 孤儿C={c} 图引用D={d}"
        fail_n = a + b + c + d
    else:
        fail_n = out.count("FAIL")
        detail = out.strip().splitlines()[-1] if out.strip() else "未知输出"
    ev = [l.strip() for l in out.splitlines() if "命中" in l or "WARN" in l or "FAIL" in l][:8]
    return {"name": "redlines", "ok": fail_n == 0, "detail": detail,
            "hits": fail_n, "evidence": ev}


def gate_html(path: Path, allow_vendor: bool = False) -> dict:
    """单文件 HTML 交付体检（外链/base64/标签/锚点/破折号/厂商名）。"""
    cmd = [sys.executable, str(CHECK_HTML), str(path)]
    if allow_vendor:
        cmd.append("--allow-vendor")
    rc, out = run(cmd, timeout=300)
    fails = [l for l in out.splitlines() if "[FAIL]" in l]
    warns = [l for l in out.splitlines() if "[WARN]" in l]
    m = re.search(r"PASS=(\d+) WARN=(\d+) FAIL=(\d+)", out)
    detail = m.group(0) if m else out.strip().splitlines()[-2:]
    return {"name": "html_delivery", "ok": not fails,
            "detail": f"PASS={m.group(1)} WARN={m.group(2)} FAIL={m.group(3)}" if m else out.strip()[-200:],
            "hits": len(fails), "evidence": fails[:8] + warns[:2]}


def gate_deck(path: Path) -> dict:
    """PPTX 包校验：zip 完整性/XML/顺序/rels/孤儿/媒体。"""
    rc, out = run([sys.executable, str(VERIFY_DECK), "--pptx", str(path)], timeout=600)
    fails = [l for l in out.splitlines() if "FAIL" in l or "✗" in l]
    m = re.search(r"FAIL=(\d+)", out)
    fail_n = int(m.group(1)) if m else len(fails)
    ok = fail_n == 0
    tail = out.strip().splitlines()[-2:] if out.strip() else ""
    return {"name": "deck_package", "ok": ok, "detail": " | ".join(tail),
            "hits": fail_n, "evidence": fails[:10]}


def gate_manifest(path: Path, text: str | None = None, digest: str | None = None) -> dict:
    """打包/自包含清单：md5、文件大小、图数、内联图(非 data: 即 FAIL)、外链数、布局留人工。

    390px 无溢出需真实渲染，这里不做（留人工/agent 通读），仅在 detail 注明。
    text/digest 可由上游一次读入后传入，避免同一份 HTML 在六段链里反复读。
    """
    text = path.read_text(encoding="utf-8", errors="ignore") if text is None else text
    imgs = re.findall(r"<img\b[^>]*>", text)
    external_img = [m for m in imgs if 'src="data:' not in m and "src='data:" not in m]
    ns = {"http://www.w3.org/2000/svg", "http://www.w3.org/1999/xhtml",
          "http://www.w3.org/XML/1998/namespace"}
    outbound = sorted({u for u in re.findall(r"https?://[^\s\"'<>]+", text) if u not in ns})
    inline_bytes = sum(len(m) for m in re.findall(r'src="data:[^"]{0,40}base64,', text))
    detail = (f"md5={digest or md5_of(str(path))}  {path.stat().st_size}B  图={len(imgs)} "
              f"外链图={len(external_img)}  外链={len(outbound)}  layout390px=留人工/agent")
    ok = len(external_img) == 0 and len(outbound) == 0
    return {"name": "bundle_manifest", "ok": ok, "detail": detail,
            "hits": len(external_img) + len(outbound),
            "evidence": [m[:80] for m in external_img[:3]] + outbound[:3]}


def gate_prose_fast(text: str, allow_vendor: bool) -> dict:
    """快速兜底：对散文本做破折号/数字范围/外链/厂商名扫描（任何资产通用）。"""
    n_dash = len(PROSE_DASH.findall(text))
    n_range = len(NUM_RANGE.findall(text))
    n_tilde = len(TILDE_CMD.findall(text))
    n_vendor = 0 if allow_vendor else len(VENDOR_RE.findall(text))
    n_link = len(OUTLINK.findall(text))
    total = n_dash + n_range + n_tilde + n_vendor + n_link
    detail = f"破折号={n_dash} 数字双连={n_range} asciitilde={n_tilde} 厂商={n_vendor} 外链={n_link}"
    return {"name": "prose_fast", "ok": total == 0, "detail": detail,
            "hits": total, "evidence": []}


# ---------- 台账 ----------
def ledger_path() -> Path:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    return LEDGER_DIR / "ledger.jsonl"


def append_ledger(entry: dict):
    p = ledger_path()
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def summary_runs() -> dict:
    """汇总历史台账：按 kind 计数，门通过率分母只算真有 gates 的记录。

    旧口径把 e2e/preflight 行也算进 runs，会让门通过率分母虚高；这里保留
    runs_total 看全量追加量，runs 只记有 gates 的 run，并单独给 stages 六段统计。
    """
    p = ledger_path()
    if not p.exists():
        return {"runs": 0, "runs_total": 0, "by_kind": {}, "gates": {},
                "stages": {}, "total_hits": 0}
    runs = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                runs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    gate_rows = [r for r in runs if isinstance(r.get("gates"), list)]
    by_kind: dict[str, int] = {}
    gates: dict[str, dict] = {}
    stages: dict[str, dict] = {}
    for r in runs:
        kind = str(r.get("kind", "unknown"))
        by_kind[kind] = by_kind.get(kind, 0) + 1
        for g in r.get("gates", []) or []:
            d = gates.setdefault(g["name"], {"ok": 0, "total": 0, "hits": 0})
            d["total"] += 1
            if g.get("ok"):
                d["ok"] += 1
            d["hits"] += g.get("hits", 0)
        for sid, v in (r.get("stages") or {}).items():
            if not isinstance(v, dict):
                continue
            d = stages.setdefault(sid, {"ok": 0, "total": 0})
            d["total"] += 1
            if v.get("ok"):
                d["ok"] += 1
    return {"runs": len(gate_rows), "runs_total": len(runs), "by_kind": by_kind,
            "gates": gates, "stages": stages,
            "total_hits": sum(g.get("hits", 0) for r in gate_rows
                              for g in r.get("gates", []))}


# ---------- 主流程 ----------
def human_report(entry: dict, summary: dict) -> str:
    L = []
    L.append(f"### check_chain · {entry['ts']}")
    L.append(f"target: {entry['target']}   kind: {entry['kind']}   md5: {entry['md5']}")
    L.append("")
    worst = "PASS"
    for g in entry["gates"]:
        mark = "PASS" if g["ok"] else "FAIL"
        if g["ok"] is False:
            worst = "FAIL"
        L.append(f"[{mark}] {g['name']:<18} {g['detail']}")
        for e in g.get("evidence", [])[:4]:
            L.append(f"        {e}")
    L.append("")
    L.append(f"判定: {worst}    机检命中(待人工回源核验): {sum(g.get('hits',0) for g in entry['gates'])}")
    if summary.get("runs", 0) > 0:
        L.append(f"台账累计: {summary['runs']} gate run / 全量 {summary.get('runs_total', summary['runs'])} 行 "
                 f"/ {summary['total_hits']} 命中")
    return "\n".join(L)


def inspect(target: str | Path, kind: str = "auto", allow_vendor: bool = False,
            text: str | None = None, digest: str | None = None,
            append: bool = True) -> tuple[dict, dict]:
    """跑一次门禁并返回 (台账条目, 汇总)。

    text/digest 由上游一次读入后传入时，manifest 与 prose_fast 不再重复读文件；
    CLI 不传这两个参数时行为与原先完全一致。
    """
    p = Path(target).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(p)
    kind = probe_kind(p, kind)

    gates: list[dict] = []
    text_for_fast = text if text is not None else ""
    if kind == "tex":
        pkg = gate_tex_all() if p.is_dir() else gate_tex_compile_from_path(p)
        gates.append(pkg)
        gates.append(gate_redlines(str(PROJECT_ROOT / "manuscript-v10" if p.is_dir() else p)))
        if text is None:
            files = sorted(PROJECT_ROOT.glob("manuscript-v10/*.tex")) if p.is_dir() else [p]
            for f in files:
                if f.is_file():
                    try:
                        text_for_fast += f.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        pass
    elif kind == "html":
        gates.append(gate_html(p, allow_vendor))
        gates.append(gate_manifest(p, text=text, digest=digest))
        if text is None:
            try:
                text_for_fast = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass
    elif kind == "pptx":
        gates.append(gate_deck(p))

    if text_for_fast.strip():
        gates.append(gate_prose_fast(text_for_fast, allow_vendor))

    has_fail = any(g["ok"] is False for g in gates)
    entry = {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "target": str(p),
        "kind": kind,
        "md5": (digest or md5_of(str(p))) if p.is_file() else "",
        "verdict": "FAIL" if has_fail else "PASS",
        "gates": gates,
        "allow_vendor": bool(allow_vendor),
    }
    if append:
        append_ledger(entry)
    return entry, summary_runs()


def main() -> int:
    ap = argparse.ArgumentParser(description="Noteleaf M1 质检编排器 check_chain")
    ap.add_argument("target", nargs="?", help="目标路径（--list 时可省略）")
    ap.add_argument("--kind", choices=["auto", "tex", "html", "pptx"], default="auto")
    ap.add_argument("--json", action="store_true", help="输出 JSON 台账到 stdout")
    ap.add_argument("--out", default="", help="台账 JSON 输出路径")
    ap.add_argument("--allow-vendor", action="store_true", help="DaaC 讲义允许云厂商名")
    ap.add_argument("--list", action="store_true", help="列出历史台账汇总")
    args = ap.parse_args()

    if args.list:
        s = summary_runs()
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return 0

    if not args.target:
        ap.error("需要提供 target 路径（或使用 --list）")

    p = Path(args.target).expanduser().resolve()
    if not p.exists():
        print(f"FAIL: 路径不存在 {p}", file=sys.stderr)
        return 2
    entry, summary = inspect(p, kind=args.kind, allow_vendor=args.allow_vendor)

    if args.json or args.out:
        out = json.dumps(entry, ensure_ascii=False, indent=2)
        if args.out:
            Path(args.out).write_text(out, encoding="utf-8")
            print(f"台账已写: {args.out}")
        else:
            print(out)
    else:
        print(human_report(entry, summary))

    return 1 if entry["verdict"] == "FAIL" else 0


def gate_tex_compile_from_path(p: Path) -> dict:
    """从单章文件路径提取补零章号，走编译 gate。"""
    m = re.search(r"chapter(\d\d)_", p.name)
    if not m:
        return {"name": "tex_compile", "ok": None, "detail": "无法识别章号", "hits": 0, "evidence": []}
    chap = m.group(1)
    return gate_tex_compile(chap)


if __name__ == "__main__":
    sys.exit(main())
