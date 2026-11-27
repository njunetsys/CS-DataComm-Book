#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lf/lecture_lint.py: 讲义机械痕迹体检（2026-11-25 用户拍板「机械项，不动文风」）。

只做确定性定位，不裁决、不改写。每类检查输出等级 + 行号 + 原文片段，
人工按 SKILL.md §6.1 决定怎么处理。文风层（句长均匀/套路比喻/作者态度）刻意不查。

检查项:
  L1 破折号      —— / – (en dash 数字范围) / 裸 --          FAIL
  L2 画外音      图注里的 OCR 已核验 / 据截图 / 已校对 …    FAIL
  L3 空锚文本    看详解 / 去围观 / 看热议 … 短锚文本链接    FAIL
  L4 段首套话    值得注意的是 / 不难发现 / 综上所述 …       WARN
  L5 空对举      不是 A，而是 B（可能承载实质，只定位）     WARN
  L6 图引用      每个 div.cap 的「图 N-M」正文有无引用      WARN
                 讲义图号是「图 N-M」不是教材「图 N.M」，rubric R4 的 d 口径需另修
  L7 图大小      像素宽 600–1000、PNG≤400KB/JPEG≤250KB     WARN
  L8 同页        .fig 容器有无 break-inside:avoid           WARN

CLI:
  python3 tools/lf/lecture_lint.py <file.html> [--json] [--out FILE]
  python3 tools/lf/lecture_lint.py --selfcheck
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ---------- 判据 ----------
DASH2 = re.compile(r"——")
ENDASH_RANGE = re.compile(r"\d\s*[–]\s*\d")
BARE_DD = re.compile(r"(?<![-=])--(?![-=>])")

VOICEOVER = re.compile(
    r"OCR\s*已核验|已核验|已校对|据截图|根据截图|截图所示|编者注|待补|待核")
SHORT_ANCHOR = re.compile(
    r"^(去围观|看热议|看演进|看详解|看分析|看架构|看对比|看解析|看实测|看展望|"
    r"看拆解|看推导|看配置|看规格|看技术|看进展|看设计原则|看实战|看通信原语|"
    r"看原始|看出处|看论文|看原文|点这里|戳这里|详见)$")
PLATITUDE = re.compile(r"值得注意的是|不难发现|综上所述|总而言之|众所周知|显而易见")
ANTITHESIS = re.compile(r"不是[^，。；]{1,30}[，,]\s*而是[^。；]{1,40}")

CLEAN_TAGS = re.compile(r"<[^>]+>")
BLOCK_RE = re.compile(r"<(style|script)\b[^>]*>.*?</\1\s*>", re.I | re.S)
B64_RE = re.compile(r"data:image/[^;\"')]+;base64,[A-Za-z0-9+/=]+", re.I)
CAP_RE = re.compile(r"<div\s+class=\"cap\"[^>]*>(.*?)</div>", re.I | re.S)
FIG_RE = re.compile(r"<div\s+class=\"fig\"[^>]*>.*?</div>\s*</div>|<div\s+class=\"fig\"[^>]*>.*?</div>", re.I | re.S)
IMG_RE = re.compile(r"<img\b[^>]*src=\"data:image/([^;]+);base64,([^\"]+)\"[^>]*>", re.I | re.S)
FIGNO_RE = re.compile(r"图\s*(\d+)[\-–](\d+)")

PIXEL_MIN, PIXEL_MAX = 600, 1000
KB_PNG, KB_JPEG = 400, 250


def visible_lines(html: str) -> list[tuple[int, str]]:
    """剥 style/script/base64 后，按原行号返回可见文本行。"""
    masked = BLOCK_RE.sub(lambda m: "\n" * m.group(0).count("\n"), html)
    masked = B64_RE.sub("[BASE64]", masked)
    # 标签换成空格而非空串，避免跨单元格的「—」被拼成「——」误报
    return [(i, CLEAN_TAGS.sub(" ", ln)) for i, ln in enumerate(masked.splitlines(), 1)]


def add(items: list, lid: str, level: str, line: int, text: str, note: str = ""):
    items.append({"id": lid, "level": level, "line": line,
                  "evidence": text.strip()[:120], "note": note})


def check_text(lines: list[tuple[int, str]]) -> list[dict]:
    items: list[dict] = []
    for ln, text in lines:
        if DASH2.search(text):
            add(items, "L1", "FAIL", ln, text, "双破折号：按语境改冒号/逗号/拆句")
        if ENDASH_RANGE.search(text):
            add(items, "L1", "FAIL", ln, text, "en dash 数字范围：改成「至」")
        if BARE_DD.search(text):
            add(items, "L1", "FAIL", ln, text, "裸双连字符：删除")
        if VOICEOVER.search(text):
            add(items, "L2", "FAIL", ln, text, "画外音：删过程性备注，图注只留说明+来源")
        if PLATITUDE.search(text):
            add(items, "L4", "WARN", ln, text, "段首套话：直接删或改直陈")
        if ANTITHESIS.search(text):
            add(items, "L5", "WARN", ln, text, "空对举：A/B 有实质则保留，套话才改")
    return items


def check_anchors(html: str) -> list[dict]:
    items: list[dict] = []
    # 按原行号定位空锚文本
    for i, ln in enumerate(html.splitlines(), 1):
        for m in re.finditer(r"<a\b([^>]*)>(.*?)</a>", ln, re.I | re.S):
            label = CLEAN_TAGS.sub("", m.group(2)).strip()
            if SHORT_ANCHOR.match(label):
                href = re.search(r"href=\"([^\"]+)\"", m.group(1))
                add(items, "L3", "FAIL", i, ln,
                    f"空锚文本「{label}」→ {href.group(1)[:60] if href else '?'}；重要内容并入正文，否则删")
    return items


def check_figures(html: str) -> list[dict]:
    items: list[dict] = []
    masked = B64_RE.sub("[BASE64]", html)
    # 正文：剥掉所有 fig 容器与 style/script
    body = FIG_RE.sub(" ", masked)
    body = BLOCK_RE.sub(" ", body)
    body_text = CLEAN_TAGS.sub(" ", body)
    refs = set(FIGNO_RE.findall(body_text))
    caps = [(x.group(1), FIGNO_RE.search(CLEAN_TAGS.sub("", x.group(1))))
            for x in CAP_RE.finditer(masked)]
    for cap_html, no in caps:
        if not no:
            continue
        key = (no.group(1), no.group(2))
        if key not in refs:
            line = masked[:masked.find(cap_html)].count("\n") + 1 if cap_html in masked else 0
            add(items, "L6", "WARN", line, CLEAN_TAGS.sub("", cap_html).strip(),
                f"图 {key[0]}-{key[1]} 正文未见引用（若用「如图」需写清编号）")
    # 图大小
    if HAS_PIL:
        for i, m in enumerate(IMG_RE.finditer(html), 1):
            try:
                raw = base64.b64decode(m.group(2))
                im = Image.open(io.BytesIO(raw))
                w, h = im.size
                kb = len(raw) // 1024
                fmt = m.group(1).lower()
                cap = "jpg" if fmt in ("jpeg", "jpg") else fmt
                limit = KB_JPEG if cap in ("jpg", "jpeg") else KB_PNG
                line = html[:m.start()].count("\n") + 1
                reasons = []
                if w < PIXEL_MIN:
                    reasons.append(f"像素宽 {w}<{PIXEL_MIN}（过小，标注看不清）")
                if w > PIXEL_MAX:
                    reasons.append(f"像素宽 {w}>{PIXEL_MAX}（过大，等比缩放）")
                if kb > limit:
                    reasons.append(f"体积 {kb}KB>{limit}KB（压缩）")
                if reasons:
                    add(items, "L7", "WARN", line, f"图#{i} {w}×{h} {kb}KB", "；".join(reasons))
            except Exception as e:
                add(items, "L7", "WARN", 0, f"图#{i}", f"解码失败: {type(e).__name__}")
    else:
        add(items, "L7", "WARN", 0, "Pillow 未安装", "跳过像素/体积检查")
    # 同页 CSS
    if "break-inside" not in html or "avoid" not in html:
        add(items, "L8", "WARN", 0, ".fig 容器", "缺 break-inside:avoid，图/图注/引用可能跨页")
    return items


def check(html: str) -> dict:
    lines = visible_lines(html)
    items = check_text(lines) + check_anchors(html) + check_figures(html)
    fails = sum(i["level"] == "FAIL" for i in items)
    warns = sum(i["level"] == "WARN" for i in items)
    return {"items": items, "fail_count": fails, "warn_count": warns,
            "by_id": {lid: sum(i["id"] == lid for i in items)
                      for lid in ("L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8")},
            "policy": "机械项只定位不裁决；文风层不查"}


def selfcheck() -> int:
    html = ('<style>.fig{break-inside:avoid}</style>\n'
            '<p>值得注意的是，这不是 A，而是 B —— 一个测试——。</p>\n'
            '<p><a href="https://x">去围观</a></p>\n'
            '<div class="fig"><div class="cap">图 1-2 示意（OCR 已核验）</div></div>\n')
    r = check(html)
    assert r["by_id"]["L1"] >= 1, r
    assert r["by_id"]["L2"] == 1, r
    assert r["by_id"]["L3"] == 1, r
    assert r["by_id"]["L4"] == 1, r
    assert r["by_id"]["L5"] == 1, r
    assert r["by_id"]["L6"] == 1, r
    print("[OK] lecture_lint selfcheck: L1-L6 定位")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="讲义机械痕迹体检（只定位，不裁决）")
    ap.add_argument("file", nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default="")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck or not a.file:
        return selfcheck()
    p = Path(a.file).expanduser().resolve()
    if not p.exists():
        print(f"FAIL 文件不存在: {p}", file=sys.stderr)
        return 2
    r = check(p.read_text(encoding="utf-8", errors="ignore"))
    r["file"] = str(p)
    out = json.dumps(r, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(out, encoding="utf-8")
        print(f"台账已写: {a.out}")
    if a.json:
        print(out)
    else:
        print(f"lecture_lint · {p.name}")
        print(f"  合计 FAIL={r['fail_count']} WARN={r['warn_count']} {r['by_id']}")
        for it in r["items"]:
            print(f"  [{it['level']}] {it['id']} L{it['line']} {it['evidence'][:70]}")
            if it["note"]:
                print(f"          ↳ {it['note']}")
        print(f"  {r['policy']}")
    return 1 if r["fail_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
