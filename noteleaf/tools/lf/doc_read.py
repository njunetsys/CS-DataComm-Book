#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lf/doc_read.py: Noteleaf 文档解析层（K2 的「读文件」能力）。

照 OpenMAIC 解析层做：按格式选解析器 → 保留结构 → 算内容指纹 → 统计可复核信号。
只读、不评分、不入账；产物交给 K2 的 SCORE/FROM_TICKETS 消费。

CLI:
  python3 tools/lf/doc_read.py READ <file> [--topics 主题词 ...] [--mode fast|balanced] [--out JSON]
  python3 tools/lf/doc_read.py selfcheck

设计契约：
  - 输入：文件路径 + 主题词列表（主题词来自 PREP 的同一批，保证分母一致）
  - 输出：{name, md5, chars, headings, tables, table_rows, formulas, hits:{词:次数},
           coverage, text_preview}；文本落 inputs/<name>/parsed.md 供后续引用
  - 相关性用「主题词在正文出现次数」这种可手算信号，不用黑箱 embedding
  - 结构统计（标题/表/公式）直接来自解析结果，不作估计
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INPUTS_DIR = PROJECT_ROOT / "CloudComputing" / "framework" / "inputs"
SUPPORTED = {".pdf", ".md", ".txt", ".docx", ".pptx", ".html"}


def md5_of(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def structure(text: str, blocks: dict | None = None) -> dict:
    """统计结构。优先用 marker 的 block_counts（版面模型真值），
    没有时退回 markdown 正则（可手算复核）。"""
    if blocks:
        return {
            "chars": len(text),
            "headings": blocks.get("SectionHeader", 0),
            "tables": blocks.get("Table", 0),
            "table_rows": len(re.findall(r"^\s*\|.*\|\s*$", text, re.M)),
            "formulas": len(re.findall(r"\$\$.+?\$\$", text, re.S)) +
                        len(re.findall(r"\\\(|\\\[", text)),
            "source": "marker:block_counts",
        }
    headings = re.findall(r"^#{1,6}\s+\S", text, re.M)
    table_rows = re.findall(r"^\s*\|.*\|\s*$", text, re.M)
    return {
        "chars": len(text),
        "headings": len(headings),
        "tables": 0,  # 纯文本无版面模型，不猜表数
        "table_rows": len(table_rows),
        "formulas": len(re.findall(r"\$\$.+?\$\$", text, re.S)) +
                    len(re.findall(r"\\\(|\\\[", text)),
        "source": "regex",
    }


def read_doc(path: Path, topics: list[str], mode: str = "fast",
             save_dir: Path | None = None) -> dict:
    p = Path(path).expanduser()
    if not p.is_file():
        raise FileNotFoundError(p)
    ext = p.suffix.lower()
    if ext not in SUPPORTED:
        raise ValueError(f"不支持的格式 {ext}，可选 {sorted(SUPPORTED)}")

    if ext in (".md", ".txt", ".html"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if ext == ".html":
            text = re.sub(r"<[^>]+>", " ", text)
        engine = "plain"
    else:
        # marker 只写临时目录，产物由本模块接管；不污染项目
        blocks: dict = {}
        with tempfile.TemporaryDirectory(prefix="lf_docread_") as td:
            out = subprocess.run(
                ["marker_single", str(p), "--output_dir", td,
                 "--output_format", "markdown", "--mode", mode],
                capture_output=True, text=True, timeout=600,
            )
            if out.returncode != 0:
                raise RuntimeError(f"marker 解析失败: {out.stderr[-400:]}")
            mds = list(Path(td).rglob("*.md"))
            if not mds:
                raise RuntimeError("marker 未产出 markdown")
            text = mds[0].read_text(encoding="utf-8", errors="ignore")
            metas = list(Path(td).rglob("*_meta.json"))
            if metas:
                meta = json.loads(metas[0].read_text(encoding="utf-8"))
                for page in meta.get("page_stats", []):
                    for kind, n in page.get("block_counts", []):
                        blocks[kind] = blocks.get(kind, 0) + int(n)
        engine = f"marker:{mode}"

    st = structure(text, blocks if ext not in (".md", ".txt", ".html") else None)
    low = text.lower()
    hits = {t: low.count(t.lower()) for t in topics if t}
    covered = sum(1 for v in hits.values() if v > 0)

    result = {
        "name": p.stem,
        "path": str(p),
        "format": ext.lstrip("."),
        "engine": engine,
        "md5": md5_of(p),
        **st,
        "hits": hits,
        "topics": len(topics),
        "covered_topics": covered,
        "coverage": round(covered / len(topics), 3) if topics else 0.0,
        "text_preview": text[:300].strip(),
    }
    if save_dir:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        (save_dir / "parsed.md").write_text(text, encoding="utf-8")
        (save_dir / "read.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        result["saved"] = str(save_dir / "parsed.md")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Noteleaf 文档解析层")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("READ", help="读一份文件，抽结构与主题命中")
    p.add_argument("file")
    p.add_argument("--topics", nargs="*", default=[])
    p.add_argument("--mode", default="fast", choices=["fast", "balanced", "no_ocr"])
    p.add_argument("--save", default="", help="落盘目录（默认不落）")
    p.add_argument("--out", default="", help="结果 JSON 路径")
    sub.add_parser("selfcheck", help="自检结构统计与命中算法")
    args = ap.parse_args()

    if args.cmd == "selfcheck":
        s = structure("# T\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n$$x$$\n")
        assert s["headings"] == 1 and s["table_rows"] == 3 and s["formulas"] == 1, s
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "a.md"
            f.write_text("# 标题\n\n调度 调度 集群\n", encoding="utf-8")
            r = read_doc(f, ["调度", "虚拟化"])
            assert r["hits"] == {"调度": 2, "虚拟化": 0} and r["coverage"] == 0.5, r
            assert len(r["md5"]) == 32 and r["engine"] == "plain"
        print("selfcheck OK: 结构统计 / 主题命中 / 覆盖率 / md5 通过")
        return 0

    out = read_doc(Path(args.file), args.topics, args.mode,
                   Path(args.save) if args.save else None)
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
