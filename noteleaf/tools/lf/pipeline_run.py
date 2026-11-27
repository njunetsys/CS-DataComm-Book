#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lf/pipeline_run.py: Noteleaf 端到端编排·验证主链六段。

对一讲依次走 ASSET → ANCHOR → WRITE → GATE → REVIEW → DELIVER，
每段报告「产出物 + 状态」，汇总成一个 e2e 记录追加进 .workbuddy/ledger/。
机器只负责『有/没有、过/不过、以及跑出了什么』，判断好坏仍归作者（六段里 GATE 可机判，
REVIEW/DELIVER 的观感与发布决策由作者拍板，这里只标 ready/pending）。

CLI:
  python3 tools/lf/pipeline_run.py --lecture 02_弹性计算 \
      [--html <framework 内的生成稿 .html>] [--json] [--no-ledger] \
      [--require-review] [--require-rubric]
退出码：0=PASS（各段产出物齐备） 1=FAIL（某段缺阻塞项）

优化记录（2026-11-25）：
  - 同一份 HTML 只在 run() 开头读一次，GATE/REVIEW/DELIVER 复用 bytes/text/md5。
  - check_chain 改为进程内 inspect(text=, digest=) 入口，判据与 CLI 完全一致。
  - --json 默认只打印摘要；完整结果落 framework/review/<讲ID>_pipeline_full.json。

各段的『产出物契约』（与 spec_v0.1.0.json 对齐):
  ASSET   -> 素材台账(资产台账jsonl) + 供料排序 + M2 显式画像读回
  ANCHOR  -> framework/anchors/ANCHOR_RULES.html（通用写作规则）
  WRITE   -> 生成稿 html + O2 前置门禁（prefs/写作规则缺项即拦，再验文件在）
  GATE    -> check_chain 门禁（红线/自包含/外链/图序…），FAIL=0 才算过
  REVIEW  -> G2 原子 rubric 自动跑（待回源清单）+ G3 三态审稿；闭环结论回写 M2
  DELIVER -> 自包含单 HTML + md5 快照（对外零依赖）
  M2 画像 -> ASSET 段读回显式画像；已闭环审稿结论在 REVIEW 段去重回写
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = PROJECT_ROOT / "CloudComputing" / "framework"
ANCHORS_DIR = FRAMEWORK / "anchors"
ASSET_LEDGER = FRAMEWORK / "asset_ledger.jsonl"
LEDGER = PROJECT_ROOT / ".workbuddy" / "ledger" / "ledger.jsonl"
CHECK_CHAIN = PROJECT_ROOT / "tools" / "check_chain.py"

sys.path.insert(0, str(PROJECT_ROOT / "tools"))
import check_chain  # noqa: E402  （进程内复用门禁，避免重复读 HTML）


def load_jsonl(p: Path) -> list[dict]:
    if not Path(p).exists():
        return []
    out = []
    for line in Path(p).read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def md5_of(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def read_doc(html: Path) -> dict:
    """一次读入：后续各段共享 bytes/text/md5，避免同一份大 HTML 反复读。"""
    if not html.exists():
        return {"path": html, "bytes": b"", "text": "", "size": 0, "md5": ""}
    raw = html.read_bytes()
    return {"path": html, "bytes": raw,
            "text": raw.decode("utf-8", errors="ignore"),
            "size": len(raw), "md5": hashlib.md5(raw).hexdigest()}


def doc_stable(doc: dict) -> bool:
    """收尾核对：运行中若文件被别处改动，明确暴露，不拿旧快照假装通过。"""
    if not doc["path"].exists():
        return doc["size"] == 0
    return hashlib.md5(doc["path"].read_bytes()).hexdigest() == doc["md5"]


def scan_outbound(text: str) -> list[str]:
    """D1 粗判：抓真外链，含 XML 命名空间白名单、url()、srcset、href/src。

    XML 命名空间 URI 是标记不是依赖，白名单放行；出处型 <a href=https> 在交付物里
    仍算外链，需作者自行决定是否保留。
    """
    ns = {"http://www.w3.org/2000/svg", "http://www.w3.org/1999/xhtml",
          "http://www.w3.org/XML/1998/namespace"}
    urls = set(re.findall(r"https?://[^\s\"'<>()]+", text))
    urls |= set(re.findall(r"url\(\s*['\"]?(https?://[^'\") ]+)", text, re.I))
    for attr in ("href", "src"):
        urls |= set(re.findall(rf"{attr}\s*=\s*['\"](https?://[^'\"]+)", text, re.I))
    for blob in re.findall(r"srcset\s*=\s*['\"]([^'\"]+)", text, re.I):
        for part in blob.split(","):
            tokens = part.strip().split()
            if tokens and tokens[0].startswith("http"):
                urls.add(tokens[0])
    return sorted({u.rstrip(".,);") for u in urls if u not in ns})


def stage_asset(lecture: str) -> dict:
    rows = load_jsonl(ASSET_LEDGER)
    by_layer = {}
    for r in rows:
        by_layer.setdefault(r["layer"], []).append(r)
    from lf.asset_score import sort_supply
    from lf.prefs import supply_priority
    from lf import memory as lf_memory
    ranked = sort_supply(rows, supply_priority(lecture)["layer_priority"])
    prof = lf_memory.recall(lecture, limit=5)
    lp = prof["lecture_profile"]
    return {"rows": len(rows),
            "profile": {"dims": lp.get("dims", []),
                        "audience": lp.get("audience", ""),
                        "difficulty": lp.get("difficulty", ""),
                        "decisions": len(prof["decisions"])},
            "by_layer": {k: len(v) for k, v in sorted(by_layer.items())},
            "top_supply": [{"name": x["name"], "user": x["user"], "pri": x["pri"]}
                           for x in ranked[:5]],
            "ok": len(rows) > 0,
            "msg": f"素材台账 {len(rows)} 条（分 {len(by_layer)} 层），供料 top: "
                   f"{'、'.join(x['name'][:10] for x in ranked[:3]) or '空'}"}


def stage_anchor(lecture: str) -> dict:
    from lf.preflight import ANCHOR_RULES, inspect_anchor
    r = inspect_anchor(ANCHOR_RULES)
    return {"file": str(ANCHOR_RULES),
            "bytes": ANCHOR_RULES.stat().st_size if ANCHOR_RULES.exists() else 0,
            "ok": r["ok"], "msg": "; ".join(r["evidence"])}


def stage_write(html: Path, lecture: str, doc: dict) -> dict:
    """写作段：先跑 O2 前置门禁（prefs/写作规则），缺项即拦；再验生成稿在。"""
    from lf.preflight import run_preflight
    pf = run_preflight(lecture)
    if not html.exists():
        base = {"file": str(html), "bytes": 0, "ok": False, "msg": "生成稿缺失"}
    else:
        base = {"file": str(html), "bytes": doc["size"],
                "ok": doc["size"] > 0,
                "msg": f"生成稿 {doc['size']}B"}
    base["preflight"] = pf["verdict"]
    base["preflight_blocked"] = pf["blocked"]
    if pf["verdict"] == "FAIL" and base["ok"]:
        base["ok"] = False
        base["msg"] += f"；O2 前置门禁未过: {pf['blocked']}"
    return base


def stage_gate(html: Path, doc: dict) -> dict:
    """门禁：进程内跑 check_chain；只把『纯厂商命中』按讲义体例放行（命中数仍展示）。"""
    try:
        entry, _ = check_chain.inspect(html, kind="html", allow_vendor=False,
                                       text=doc["text"], digest=doc["md5"])
        gates = entry.get("gates", [])
        fails = [g["name"] for g in gates if g.get("ok") is False]
        # 讲义体例允许厂商名：仅当失败全为 prose_fast、且其 detail 中其余红线均为 0
        vendor_only = False
        vendor_n = 0
        if fails == ["prose_fast"]:
            det = next((g.get("detail", "") for g in gates if g["name"] == "prose_fast"), "")
            m = re.search(r"厂商=(\d+)", det)
            vendor_n = int(m.group(1)) if m else 0
            rest_ok = all((f"{k}=0" in det) for k in ("破折号", "数字双连", "asciitilde", "外链"))
            vendor_only = rest_ok and vendor_n > 0
        if vendor_only:
            return {"verdict": "PASS(讲义体例放行厂商)", "ok": True, "fails": [],
                    "msg": f"门禁其余全绿；厂商名命中 {vendor_n} 处（讲义体例允许，待作者复核）"}
        return {"verdict": entry.get("verdict"), "fails": fails, "ok": not fails,
                "msg": f"门禁 {entry.get('verdict')}，失败门: {fails or '无'}"}
    except Exception as e:
        return {"ok": False, "msg": f"门禁调用失败: {type(e).__name__}: {e}"}


def check_contracts(lecture: str, text: str) -> dict:
    """对 contracts/ 下属于本讲的契约逐份跑 CHECK(四要素)+ORDER(逻辑顺序)。
    全部 WARN 级：只定位不拦，结果进 full json 供作者回读。"""
    from lf.intent_ga import (check_ga, check_order, extract_section,
                              load_contract, strip_meta, validate_contract)
    cdir = FRAMEWORK / "contracts"
    out = []
    if not cdir.exists():
        return {"checked": 0, "results": [], "msg": "无 contracts 目录"}
    for cp in sorted(cdir.glob("*.contract.json")):
        if cp.name.startswith("_"):
            continue
        try:
            c = load_contract(cp)
        except (json.JSONDecodeError, OSError) as e:
            out.append({"contract": cp.name, "error": f"读取失败: {e}"})
            continue
        cid = str(c.get("contract_id", ""))
        prefix = cid.split("::")[0]
        if prefix != lecture and not lecture.startswith(prefix + "_"):
            continue
        errs = validate_contract(c)
        if errs:
            out.append({"contract": cp.name, "contract_id": cid,
                        "valid": False, "errors": errs})
            continue
        sid = c.get("section_id", "")
        body = extract_section(text, sid) if sid else text
        body, _ = strip_meta(body)
        ga = check_ga(body, c)
        od = check_order(body, c)
        out.append({"contract": cp.name, "contract_id": cid, "section_id": sid,
                    "valid": True,
                    "ga": {"hit": ga["hit"], "hollow": ga["hollow"], "miss": ga["miss"],
                           "miss_items": [i["label"] for i in ga["items"]
                                          if i["verdict"] == "MISS"]},
                    "order": {"verdict": od["verdict"],
                              "inversions": od.get("inversions", []),
                              "missing": od.get("missing", [])}})
    n = len(out)
    bad = [r["contract"] for r in out
           if r.get("valid") is False or r.get("order", {}).get("verdict") == "SUSPECT"]
    return {"checked": n, "results": out,
            "msg": f"契约 {n} 份" + (f"，疑点 {len(bad)}: {bad}" if bad else "，无逆序/缺失")}


def stage_review(lecture: str, html: Path, doc: dict, require_rubric: bool = False) -> dict:
    """REVIEW 段：G2 原子 rubric 自动跑 + G3 三态审稿 + M2 闭环回写。

    G2 不替人判对错：它只把「含数字但无出处」的原子断言导成待回源清单，
    审稿人拿清单逐条对照素材；R5/R7 这类启发式只记 WARN。
    review JSON 最小 schema:
      {"lecture": str, "reviewer": str, "changed_by": str, "ts": str,
       "issues": [{"id": int, "issue": str, "evidence": str, "source": str,
                   "resolved": bool, "note": str}]}
    """
    from lf.memory import link_review
    from lf.rubric_check import CtxParser, check

    review_dir = FRAMEWORK / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    rubric_path = review_dir / f"{lecture}_rubric.json"

    if not html.exists():
        rub = {"items": [], "unanchored": [], "no_alt_imgs": [], "fail_ids": [],
               "fail_count": 0, "warn_count": 0, "error": "生成稿缺失，G2 未跑"}
        rub_msg = "G2 未跑（生成稿缺失）"
    else:
        cp = CtxParser()
        cp.feed(doc["text"])
        rub = check(cp.events, cp.imgs)
        rub_msg = (f"G2 FAIL={rub['fail_count']} WARN={rub['warn_count']} "
                   f"待回源={len(rub['unanchored'])}")

    export = {
        "file": str(html), "lecture": lecture,
        "md5": doc["md5"],
        "items": rub.get("items", []),
        "pending_source_check": [{"sec": u["sec"], "hit": u["hit"]}
                                 for u in rub.get("unanchored", [])],
        "no_alt_imgs": rub.get("no_alt_imgs", []),
        "fail_ids": rub.get("fail_ids", []),
        "fail_count": rub.get("fail_count", 0),
        "warn_count": rub.get("warn_count", 0),
        "error": rub.get("error", ""),
        "note": "G2 原子评测：待回源清单供独立审稿逐条对照素材；机检只定位，不判好坏",
    }
    rubric_path.write_text(json.dumps(export, ensure_ascii=False, indent=2),
                           encoding="utf-8")

    p = review_dir / f"{lecture}_review.json"
    m2_link = None
    if not p.exists():
        base = {"archived": "", "ok": True, "status": "pending",
                "msg": "无审稿档案，待独立审稿"}
    else:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            base = {"archived": str(p), "ok": False, "status": "open",
                    "msg": f"审稿档案损坏: {e}"}
        else:
            reviewer = str(data.get("reviewer", ""))
            changed_by = str(data.get("changed_by", ""))
            issues = data.get("issues", [])
            if reviewer and changed_by and reviewer == changed_by:
                base = {"archived": str(p), "ok": False, "status": "open",
                        "reviewer": reviewer, "changed_by": changed_by,
                        "msg": "审稿人与改动者相同，违反独立性"}
            elif not isinstance(issues, list) or not issues:
                base = {"archived": str(p), "ok": False, "status": "open",
                        "msg": "审稿档案无 issues 清单（应含逐条 issue/evidence/resolved/note）"}
            else:
                missing = [i for i in issues if not all(
                    k in i for k in ("issue", "evidence", "resolved", "note"))]
                open_ones = [i.get("id") for i in issues if not i.get("resolved")]
                if missing:
                    base = {"archived": str(p), "ok": False, "status": "open",
                            "msg": f"{len(missing)} 条 issue 缺 evidence/resolved/note 字段，未闭环"}
                elif open_ones:
                    base = {"archived": str(p), "ok": True, "status": "open",
                            "open_ids": open_ones,
                            "msg": f"审稿意见 {len(issues)} 条，未解决 {len(open_ones)} 条: {open_ones}"}
                else:
                    base = {"archived": str(p), "ok": True, "status": "ready",
                            "reviewer": reviewer,
                            "msg": f"审稿意见 {len(issues)} 条全部闭环（reviewer={reviewer or '?'}）"}
                    m2_link = link_review(p, lecture)
                    if m2_link:
                        base["m2_digest"] = m2_link["digest"][:10]

    base["rubric"] = {
        "path": str(rubric_path),
        "ok": rub.get("fail_count", 0) == 0 and not rub.get("error"),
        "fail_ids": rub.get("fail_ids", []),
        "fail_count": rub.get("fail_count", 0),
        "warn_count": rub.get("warn_count", 0),
        "pending_source_check": len(rub.get("unanchored", [])),
        "no_alt_imgs": len(rub.get("no_alt_imgs", [])),
    }
    base["g2_ok"] = base["rubric"]["ok"]
    base["msg"] += f"；{rub_msg}，清单 {rubric_path.name}"
    if html.exists():
        base["contracts"] = check_contracts(lecture, doc["text"])
        base["msg"] += f"；契约 {base['contracts']['msg']}"
    if require_rubric and not base["g2_ok"]:
        base["g2_blocked"] = True
    return base


def stage_deliver(html: Path, doc: dict) -> dict:
    outbound = scan_outbound(doc["text"])
    return {"md5": doc["md5"], "outbound": outbound, "outbound_hits": len(outbound),
            "ok": len(outbound) == 0,
            "msg": f"md5={doc['md5'][:10]}… 真外链 {len(outbound)}（0=自包含粗判通过，细则见门禁）"}


def full_result_path(lecture: str) -> Path:
    p = FRAMEWORK / "review" / f"{lecture}_pipeline_full.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def summarize_result(result: dict) -> dict:
    """对话里只给摘要，完整证据落文件；判据字段原样保留。"""
    keep = ("ok", "msg", "status", "g2_blocked", "preflight", "preflight_blocked")
    stages = {}
    for sid, v in result.get("stages", {}).items():
        d = {k: v[k] for k in keep if k in v}
        if "rubric" in v:
            d["rubric"] = v["rubric"]
        if "outbound_hits" in v:
            d["outbound_hits"] = v["outbound_hits"]
        stages[sid] = d
    return {"ts": result.get("ts"), "target": result.get("target"),
            "html": result.get("html"), "verdict": result.get("verdict"),
            "order": result.get("order"), "fails": result.get("fails"),
            "context": result.get("context"), "memory": result.get("memory"),
            "stages": stages,
            "full_result": str(full_result_path(result.get("target", "unknown")))}


def run(lecture: str, html: Path, require_review: bool = False,
        require_rubric: bool = False) -> dict:
    # O3：顺序由 spec 单一真源决定，不再硬编码；未在 handlers 里的段标 FAIL 暴露漂移
    from lf import memory as lf_memory
    from lf.spec import load_spec, pipeline_order
    profile_sync = lf_memory.sync_from_prefs(lecture)  # M2：只收 K3 显式画像
    order = pipeline_order(load_spec())
    doc = read_doc(html)  # 唯一一次读入；下面各段只读内存
    handlers = {
        "ASSET": lambda: stage_asset(lecture),
        "ANCHOR": lambda: stage_anchor(lecture),
        "WRITE": lambda: stage_write(html, lecture, doc),
        "GATE": lambda: stage_gate(html, doc),
        "REVIEW": lambda: stage_review(lecture, html, doc, require_rubric),
        "DELIVER": lambda: stage_deliver(html, doc),
    }
    stages = {}
    for sid in order:
        h = handlers.get(sid)
        stages[sid] = h() if h else {"ok": False, "msg": f"spec 阶段 {sid} 无执行器"}
    stable = doc_stable(doc)
    # REVIEW pending/open 默认不算 FAIL（人为动作）；--require-review 时未闭环才算 FAIL
    # G2 默认也不拦；--require-rubric 时 R3 等真 FAIL 才整链 FAIL
    fails = [k for k, v in stages.items() if v["ok"] is False and k != "REVIEW"]
    if require_review and stages.get("REVIEW", {}).get("status") != "ready":
        fails.append("REVIEW")
    if require_rubric and stages.get("REVIEW", {}).get("g2_ok") is False:
        fails.append("G2")
    if not stable:
        fails.append("CONTEXT")
    verdict = "FAIL" if fails else "PASS"
    return {"ts": date.today().isoformat(), "target": lecture, "kind": "e2e",
            "html": str(html), "verdict": verdict, "order": order, "stages": stages,
            "context": {"md5": doc["md5"], "bytes": doc["size"], "stable": stable},
            "memory": {"profile_changed": profile_sync["changed"],
                       "profile_source": profile_sync["source"]},
            "fails": fails}


def append_ledger(entry: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Noteleaf 端到端编排·验证主链六段")
    ap.add_argument("--lecture", required=True)
    ap.add_argument("--html", default="", help="生成稿路径（默认从 framework 现有文件挑 02 弹性计算）")
    ap.add_argument("--json", action="store_true",
                    help="输出摘要 JSON；完整结果已写 framework/review/<讲ID>_pipeline_full.json")
    ap.add_argument("--full-json", action="store_true",
                    help="在 stdout 输出完整 JSON（默认只在文件里留完整版）")
    ap.add_argument("--no-ledger", action="store_true")
    ap.add_argument("--require-review", action="store_true",
                    help="审稿未闭环(open/pending)时整条 FAIL")
    ap.add_argument("--require-rubric", action="store_true",
                    help="G2 原子评测有真 FAIL 时整条 FAIL（默认只提示不拦）")
    args = ap.parse_args()

    html = Path(args.html).expanduser() if args.html else Path(__file__).resolve().parent.parent
    if not args.html:
        # 缺省：framework 下与讲座相关的「框架生成版」html
        cands = sorted(FRAMEWORK.glob("*.html"))
        hit = next((p for p in cands if p.name.startswith("第二部分") and "框架生成" in p.name), None)
        hit = hit or next((p for p in cands if "框架生成" in p.name), None)
        if not hit:
            print("未找到生成稿，请 --html 显式指定"); return 1
        html = hit

    result = run(args.lecture, html, require_review=args.require_review,
                 require_rubric=args.require_rubric)
    if not args.no_ledger:
        append_ledger(result)
    full_path = full_result_path(args.lecture)
    full_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.full_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.json:
        print(json.dumps(summarize_result(result), ensure_ascii=False, indent=2))
    else:
        print(f"Noteleaf 端到端 · {args.lecture}  →  {html.name}")
        order = result["order"]
        for k in order:
            v = result["stages"][k]
            if v.get("ok") and k == "REVIEW" and v.get("status") in ("pending", "open"):
                st = "*待人工*"
            else:
                st = "PASS" if v["ok"] else "FAIL"
            print(f"  [{st}] {k:<8} {v['msg']}")
        print(f"结论: {result['verdict']} （失败段: {result['fails'] or '无'}）")
        rv = result["stages"].get("REVIEW", {})
        if rv.get("rubric"):
            print(f"  G2: FAIL={rv['rubric']['fail_count']} WARN={rv['rubric']['warn_count']} "
                  f"待回源={rv['rubric']['pending_source_check']} → {rv['rubric']['path']}")
        print(f"完整记录: {full_path}")
    return 1 if result["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
