#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""doc_slice: 把单文件讲义切成带原行号的纯文本切片，供文件交接使用。

目的：子代理/审稿人只读自己那一章的切片，回传结论 JSON；主代理按行号抽验。
省的是「整本 HTML 反复搬进对话」的 token，不省「真读原文」这一步。

CLI:
  python3 tools/lf/doc_slice.py --html <讲义.html> --outdir <目录> [--prefix part4]
  python3 tools/lf/doc_slice.py --selfcheck

输出:
  <outdir>/manifest.json          源 md5、章范围、切片文件清单
  <outdir>/chapters/<prefix>_ch01.txt  每行形如 "L123: 正文..."
  <outdir>/full.txt               全部行号文本（兜底，不默认交给子代理）

判据不变：这里只做切片，不做任何质量判断。
"""
from __future__ import annotations

import argparse
import hashlib
import html as html_mod
import json
import re
import sys
from pathlib import Path

B64_RE = re.compile(r'data:image/[^;"\')]+;base64,[^"\')]+', re.I)
IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
BLOCK_RE = re.compile(r"<(style|script)\b[^>]*>.*?</\1\s*>", re.I | re.S)
CHAPTER_RE = re.compile(r'<h2\b[^>]*class=["\'][^"\']*\bchapter\b', re.I)
BREAK_RE = re.compile(r"</?(?:p|div|li|tr|h[1-6]|table|ul|ol|section)\b[^>]*>", re.I)
TAG_RE = re.compile(r"<[^>]+>")


def _blank_preserve(m: re.Match) -> str:
    return "\n" * m.group(0).count("\n")


def clean_line(line: str) -> str:
    """去标签、去 base64、保留纯文本；不裁行、不改行号。"""
    s = B64_RE.sub("[图]", line)
    s = IMG_RE.sub("[图]", s)
    s = BREAK_RE.sub("\n", s)
    s = TAG_RE.sub(" ", s)
    s = html_mod.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def chapter_title(line: str) -> str:
    m = re.search(r"<h2\b[^>]*>(.*?)</h2\s*>", line, re.I | re.S)
    return clean_line(m.group(1) if m else line)


def slice_doc(src: Path, outdir: Path, prefix: str = "lecture") -> dict:
    raw = src.read_bytes()
    text = raw.decode("utf-8", errors="ignore")
    digest = hashlib.md5(raw).hexdigest()
    masked = BLOCK_RE.sub(_blank_preserve, text)
    masked = B64_RE.sub("[图]", masked)
    lines = masked.splitlines()

    starts = [(i, chapter_title(line)) for i, line in enumerate(lines, 1)
              if CHAPTER_RE.search(line)]
    chunks: list[tuple[str, int, int, str]] = []
    if starts:
        if starts[0][0] > 1:
            chunks.append(("_front", 1, starts[0][0] - 1, "前言/目录"))
        for idx, (start, title) in enumerate(starts):
            end = starts[idx + 1][0] - 1 if idx + 1 < len(starts) else len(lines)
            chunks.append((f"ch{idx + 1:02d}", start, end, title or f"第 {idx + 1} 章"))
    else:
        chunks.append(("all", 1, len(lines), "全文"))

    out_chapters = outdir / "chapters"
    out_chapters.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", prefix) or "lecture"
    chapter_rows = []
    full_rows = []
    for sid, start, end, title in chunks:
        rows = [f"L{i}: {clean_line(lines[i - 1])}" for i in range(start, end + 1)]
        full_rows.extend(rows)
        rel = Path("chapters") / f"{safe}_{sid}.txt"
        (outdir / rel).write_text("\n".join(rows) + "\n", encoding="utf-8")
        chapter_rows.append({"id": sid, "title": title, "start": start, "end": end,
                             "file": str(rel), "chars": sum(len(r) for r in rows)})
    (outdir / "full.txt").write_text("\n".join(full_rows) + "\n", encoding="utf-8")

    manifest = {"source": str(src), "md5": digest, "bytes": len(raw),
                "total_lines": len(lines), "prefix": safe, "chapters": chapter_rows}
    (outdir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def selfcheck() -> int:
    import tempfile
    html_text = """<!DOCTYPE html><html><head><style>body{color:red}</style></head><body>
<h2 class="chapter">第 1 章 · 甲</h2><p>甲句一。</p>
<p>数据 <img src="data:image/png;base64,AAAA"></p>
<h2 class="chapter">第 2 章 · 乙</h2><p>乙句一。</p></body></html>"""
    with tempfile.TemporaryDirectory(prefix="lf_slice_") as td:
        src = Path(td) / "fixture.html"
        out = Path(td) / "slices"
        src.write_text(html_text, encoding="utf-8")
        m = slice_doc(src, out, "fixture")
        assert len(m["chapters"]) == 3, m  # front + 2 章
        assert m["chapters"][1]["title"] == "第 1 章 · 甲", m["chapters"][1]
        assert m["chapters"][2]["title"] == "第 2 章 · 乙", m["chapters"][2]
        ch1 = (out / "chapters" / "fixture_ch01.txt").read_text(encoding="utf-8")
        assert "L3:" in ch1, ch1
        assert "[图]" in (out / "full.txt").read_text(encoding="utf-8")
        assert "color:red" not in (out / "full.txt").read_text(encoding="utf-8")
        print("doc_slice selfcheck PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="把讲义切成带原行号的纯文本切片")
    ap.add_argument("--html", default="")
    ap.add_argument("--outdir", default="")
    ap.add_argument("--prefix", default="lecture")
    ap.add_argument("--selfcheck", action="store_true", help="跑内置夹具自检")
    a = ap.parse_args()
    if a.selfcheck:
        return selfcheck()
    if not a.html or not a.outdir:
        ap.error("需要 --html 与 --outdir（或 --selfcheck）")
    m = slice_doc(Path(a.html).expanduser(), Path(a.outdir).expanduser(), a.prefix)
    print(f"切片完成: {len(m['chapters'])} 块 / {m['total_lines']} 行 / md5={m['md5'][:10]}")
    for c in m["chapters"]:
        print(f"  {c['id']:<6} L{c['start']:>5}-L{c['end']:<5} {c['title'][:40]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
