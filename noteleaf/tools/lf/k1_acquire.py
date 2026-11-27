#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lf/k1_acquire.py: Noteleaf K1 素材获取多源发现层。

多源对应"获取素材"能力，素材评估归 K2、偏好排序归 K3，本模块只负责"弄到手"：
  1. PAPERS   论文清单：按主题从种子表出候选论文（标准知识点锚）+ 扫描本地副本；
             加 --ragflow 额外走 RAGFlow 检索发现层，把种子表外的高相关论文也落工单
  2. VENDOR   厂商数字卡：抓官方页，抽离价格/配额类数字成一页"数字卡"（拿不到则落工单）
  3. TEXTBOOK 教材获取：下载/复制教材到本地 <教材>，失败落工单
  4. ZHIHU    知乎发现层：按主题调用知乎搜索 API，标题/作者/URL/热度/千字摘要落工单；
             只作工程实践线索，全文回原文页面核验（网页直抓被 zse-ck 反爬挡住）

所有获取动作都追加进 framework/k1/tickets.jsonl（name 冲突不覆盖），
工单是协商产物：机器只能"取"，取值/采用由作者与 K2 定。

CLI:
  python3 tools/lf/k1_acquire.py PAPERS <主题词...> [--ragflow [--limit N] [--min-sim X]] [--tickets ...]
  python3 tools/lf/k1_acquire.py PREP <讲ID> <主题词...> [--ragflow [--limit N]] [--tickets ...] [--out 素材包.json]
  python3 tools/lf/k1_acquire.py VENDOR <name> <url> [--tickets ...]
  python3 tools/lf/k1_acquire.py TEXTBOOK <name> <url|本地路径> [--tickets ...]
  python3 tools/lf/k1_acquire.py SUMMARY [--tickets ...]
  python3 tools/lf/k1_acquire.py --selfcheck

设计考量：
  - 种子表是"标准知识点锚"：论文的关键价值是 background 里被当作常识的标准点 + 年度演进的能力信号。
  - 发现层（RAGFlow）补"种子表外的新论文"：对每个主题发中/英两种查询，
    按文档去重、从 chunk 正文提取标题，相似度过阈值、标题可读才入工单（source="ragflow"）；
    文档名可能只是 DOI 编号，正文首段才是标题来源。
  - 断网不撒谎：网络失败就落工单(queued)，作者看见的是"待取"而非"已取"。
  - 本地探测：references/ 下同名 PDF 即视为已具备，避免重复抓取。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = PROJECT_ROOT / "CloudComputing" / "framework"
K1_DIR = FRAMEWORK / "k1"
DEFAULT_SEEDS = K1_DIR / "paper_seeds.json"
DEFAULT_TICKETS = K1_DIR / "tickets.jsonl"
REFERENCES = PROJECT_ROOT / "CloudComputing" / "references"
DOWNLOADS = K1_DIR / "downloads"
VENDOR_CARDS = K1_DIR / "vendor_cards"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36")
TIMEOUT = 12

# 三态分级（CRAG 思路）：high=种子锚/高相似，ambiguous=发现层低相似待核，gap=无可用素材。
# 只作证据可信度标签，不改 status（have/queued/scored 仍由 K2FROM_TICKETS 消费）。
HIGH_SIM = 0.7
GRADE_HIGH = "high"
GRADE_AMBIGUOUS = "ambiguous"


def grade_of(r: dict) -> str:
    """工单证据可信度：种子锚为 high；发现层按 sim 分级；其余默认 high。"""
    if r.get("grade") in (GRADE_HIGH, GRADE_AMBIGUOUS):
        return r["grade"]
    if r.get("source") == "ragflow":
        return GRADE_HIGH if (r.get("sim") or 0) >= HIGH_SIM else GRADE_AMBIGUOUS
    return GRADE_HIGH


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


def append_ticket(entry: dict, tickets: Path) -> None:
    Path(tickets).parent.mkdir(parents=True, exist_ok=True)
    if any(r["name"] == entry["name"] and r["kind"] == entry["kind"]
           and r["urn"] == entry["urn"] for r in load_jsonl(tickets)):
        raise ValueError(f"工单已存在，不覆盖: [{entry['kind']}] {entry['name']}")
    with open(tickets, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------- PAPERS ----------------
def paper_tickets(topics: list[str], tickets: Path) -> list[dict]:
    seeds = json.loads(DEFAULT_SEEDS.read_text(encoding="utf-8"))["seeds"]
    wanted = [s for s in seeds
              if any(t in s["topic"] for t in topics) or
              any(s["id"] == t or t in s["id"] for t in topics)]
    made = []
    for s in wanted:
        token = re.sub(r"[^a-z0-9]+", "", s["id"].lower())
        local = find_local_pdf(s, token)
        entry = {
            "name": f"{s['title'][:40]} ({s['year']})", "kind": "paper",
            "urn": s["id"], "title": s["title"], "venue": s["venue"],
            "year": s["year"], "topic": s["topic"],
            "why_background": s["why_background"],
            "capability_signal": s["capability_signal"],
            "local": str(local) if local else "", "status": "have" if local else "queued",
            "ts": date.today().isoformat(),
        }
        try:
            append_ticket(entry, tickets)
        except ValueError:
            pass
        made.append(entry)
    return made


def find_local_pdf(seed: dict, token: str) -> Path | None:
    if not REFERENCES.exists():
        return None
    for f in REFERENCES.rglob("*"):
        if f.is_file() and f.suffix.lower() in (".pdf", ".pptx", ".txt", ".md"):
            name = re.sub(r"[^a-z0-9]+", "", Path(f).stem.lower())
            if token and token in name:
                return f
    return None


# ---------------- RAGFLOW 发现层 ----------------
RAGFLOW_CFG = K1_DIR / "ragflow.json"
# 整卷/批量改名/通讯类文件名无单篇价值，作为"论文发现"的直接候选跳过
NOISE_DOC = re.compile(
    r"(full_proceedings|paper_\d{3,}|unknown|Issue[\s+]*\d|_cn\b|白皮书|规范|"
    r"毕业论文|综述|HUAWEI|华为|RESEARCH)", re.I)
# 常见中文主题 → 英文追加查询（bge 对英文论文召回更好，主题词在此表内才有 en 查询）
EN_QUERY = {
    "虚拟化": "virtualization hypervisor virtual machine",
    "容器": "container isolation cgroup namespace",
    "调度": "cluster scheduling resource management",
    "无服务器": "serverless FaaS cold start function",
    "弹性计算": "elasticity autoscaling elastic compute",
    "集群管理": "cluster management Borg Kubernetes",
    "集群": "cluster management scheduler",
    "性能隔离": "performance isolation interference",
    "自动伸缩": "autoscaling scalability elasticity",
    "serverless": "serverless FaaS cold start",
    "弹性": "elasticity autoscaling",
}


def _load_ragflow_cfg() -> dict:
    if not RAGFLOW_CFG.exists():
        return {}
    try:
        return json.loads(RAGFLOW_CFG.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def ragflow_retrieve(cfg: dict, question: str, page_size: int = 30) -> list[dict]:
    body = json.dumps({
        "question": question, "dataset_ids": [cfg["kb"]],
        "page": 1, "page_size": page_size,
        "similarity_threshold": cfg.get("defaults", {}).get("similarity_threshold", 0.1),
    }).encode()
    req = urllib.request.Request(
        f"{cfg['endpoint']}/api/v1/retrieval", data=body,
        headers={"Authorization": "Bearer " + cfg["token"],
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        d = json.loads(r.read().decode())
    if d.get("code") != 0:
        raise RuntimeError(f"RAGFlow code={d.get('code')} {d.get('message')}")
    return d.get("data", {}).get("chunks", []) or []


def extract_title(name: str, content: str) -> str:
    """从文档名或 chunk 正文首段提取论文标题候选；不可读返回空串。"""
    base = re.sub(r"\.pdf$", "", name or "").strip()
    filename_title = ""
    if re.search(r"^[0-9.]+$", base):           # DOI/纯数字编号，名不采用
        filename_title = ""
    elif re.search(r"[A-Za-z]{4,}", base):
        filename_title = re.sub(r"[\s_]+", " ", base).strip()
    first_line = ""
    if content:
        raw = [ln for ln in (content.lstrip().splitlines() or [""]) if ln.strip()]
        # 标题常在第一行，偶在第二/三行；逐行找「非章节头、长度合适、含实词」者
        for ln in raw[:3]:
            cand_l = re.sub(r"^\s*\d+[\.\)]\s*", "", ln.strip())   # 去 "1." "1)"
            cand_l = re.sub(r"\s+", " ", cand_l).strip()
            if not (8 <= len(cand_l) <= 150):
                continue
            if re.search(r"^(introduction|abstract|background|related work|conclusion|"
                         r"overview|motivation|executive summary|contents|table of contents|"
                         r"references)$", cand_l, re.I):
                continue
            if re.search(r"[A-Za-z]{4,}", cand_l):
                first_line = cand_l
                break
    for sep in ("Abstract", "ABSTRACT", "摘要", "概要"):
        i = first_line.find(sep)
        if 8 < i:
            first_line = first_line[:i].strip()
            break
    content_title = (first_line
                     if 8 <= len(first_line) <= 150 and re.search(r"[A-Za-z]{4,}", first_line)
                     else "")
    # 章节头/占位首行不是论文标题 → 回退到文档名
    if content_title and re.search(
            r"^(introduction|abstract|background|related work|conclusion|overview|"
            r"motivation|executive summary|contents|table of contents|references)$",
            content_title, re.I):
        content_title = ""
    return re.sub(r"\s+", " ", content_title or filename_title).strip()


def _title_overlap(t1: str, t2: str) -> float:
    a = set(re.findall(r"[a-z0-9]{4,}", t1.lower()))
    b = set(re.findall(r"[a-z0-9]{4,}", t2.lower()))
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def ragflow_discover(topics: list[str], tickets: Path, limit: int = 8,
                     min_sim: float = 0.5) -> list[dict]:
    """按主题分组检索 RAGFlow，每主题配额取候选，与种子/既有工单去重后落票。

    实测教训（2026-11-23）：全局按相似度取 Top-N 会被 KB 里 AI 基建类文档
    （DeepSeek/大模型通信等）淹没，必须分组配额 + 标题与种子弱相关门禁。
    """
    cfg = _load_ragflow_cfg()
    if not cfg:
        print("RAGFlow 未配置（framework/k1/ragflow.json 缺失），跳过发现层")
        return []
    docs: dict[str, dict] = {}                  # 文档名 -> {sim, content(最佳chunk), topics}
    per_topic = max(2, limit // max(len(topics), 1))
    queries: list[tuple[str, str]] = []         # (主题, 查询串)
    for t in topics:
        queries.append((t, t))
        en = EN_QUERY.get(t)
        if en:
            queries.append((t, en))
    for topic, q in queries:
        try:
            for c in ragflow_retrieve(cfg, q):
                name = (c.get("document_keyword") or "").strip()
                if not name:
                    continue
                sim = c.get("similarity") or 0.0
                cur = docs.get(name)
                if cur is None or sim > cur["sim"]:
                    docs[name] = {"sim": sim, "content": c.get("content") or "",
                                  "topic": topic}
        except Exception as e:                  # 断网/接口抖动：本批跳过并留痕
            print(f"  检索失败 [{topic}:{q[:18]}]: {type(e).__name__}: {e}")
        import time; time.sleep(0.3)

    # 每主题只保留 sim 最高的 per_topic 个（防单一主题独占）
    per_topic_cands: dict[str, list[dict]] = {}
    for name, info in docs.items():
        if info["sim"] < min_sim or NOISE_DOC.search(name):
            continue
        title = extract_title(name, info["content"])
        if not title or re.search(r"(Language Model|MoE|大模型|检索增强|RAG\b)", title, re.I):
            continue
        cand = {"name": name, "sim": info["sim"], "title": title,
                "topic": info["topic"],
                "snippet": info["content"][:160].replace("\n", " ")}
        per_topic_cands.setdefault(info["topic"], []).append(cand)
    kept: dict[str, dict] = {}
    for k, lst in per_topic_cands.items():
        for cand in sorted(lst, key=lambda x: -x["sim"])[:per_topic]:
            key = cand["name"]
            if key not in kept or cand["sim"] > kept[key]["sim"]:
                kept[key] = cand

    existing = [r for r in load_jsonl(tickets) if r.get("kind") == "paper"]
    seed_titles = [r.get("title") or "" for r in existing]
    made = []
    for c in sorted(kept.values(), key=lambda x: -x["sim"])[:limit]:
        # 与既有工单（含种子）标题重叠 >= 0.45 视为已在池内，不重复入
        if any(_title_overlap(c["title"], t) >= 0.45 for t in seed_titles):
            continue
        entry = {
            "name": c["title"][:38] + " (.discovery)", "kind": "paper",
            "urn": re.sub(r"[^0-9a-z]+", "-", re.sub(r"\.pdf$", "", c["name"]).lower()).strip("-"),
            "title": c["title"], "venue": "", "year": 0,
            "topic": [c["topic"]],
            "why_background": (f"RAGFlow 发现层按主题「{c['topic']}」召回（sim={c['sim']:.3f}），"
                               f"来自文档 {c['name']}；种子表外新线索，待作者/代理核对标题与出处"),
            "capability_signal": c["snippet"],
            "local": "", "status": "queued", "source": "ragflow", "sim": round(c["sim"], 3),
            "grade": GRADE_HIGH if c["sim"] >= HIGH_SIM else GRADE_AMBIGUOUS,
            "ts": date.today().isoformat(),
        }
        try:
            append_ticket(entry, tickets)
            made.append(entry)
        except ValueError:
            pass
    return made


# ---------------- VENDOR ----------------
def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = r.read(600_000)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="ignore")


PRICE_RE = re.compile(r".{0,40}(元|¥|美元|US\$|/小时|/月|每小时|每月|/GB|GiB|核|vCPU).{0,40}")


def vendor_card(name: str, url: str, tickets: Path) -> dict:
    try:
        text = fetch_text(url)
        text = re.sub(r"\s+", " ", text)
        price_lines = [m.group(0).strip() for m in PRICE_RE.finditer(text)][:8]
        card = {"name": name, "kind": "vendor_card", "urn": url, "url": url,
                "status": "have", "fetched_at": date.today().isoformat(),
                "price_lines": price_lines, "raw_chars": len(text),
                "quote": f"官方页抓取 {len(price_lines)} 条价格/配额候选（需人工核对数字口径）",
                "ts": date.today().isoformat()}
        VENDOR_CARDS.mkdir(parents=True, exist_ok=True)
        Path(VENDOR_CARDS / f"{re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]+', '_', name)}_{date.today():%Y%m%d}.txt") \
            .write_text("".join(f"- {l}\n" for l in price_lines), encoding="utf-8")
    except Exception as e:  # 断网/反爬都落到工单
        card = {"name": name, "kind": "vendor_card", "urn": url, "url": url,
                "status": "queued", "why": f"抓取失败: {type(e).__name__}: {e}",
                "quote": "官方页不可达，转人工/代理获取后再评",
                "ts": date.today().isoformat()}
    try:
        append_ticket(card, tickets)
    except ValueError:
        pass
    return card


# ---------------- TEXTBOOK ----------------
def textbook(name: str, from_: str, tickets: Path) -> dict:
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    if from_.startswith(("http://", "https://")):
        fname = from_.split("/")[-1].split("?")[0] or f"{name}.pdf"
        dst = DOWNLOADS / fname
        try:
            req = urllib.request.Request(from_, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                data = r.read()
            dst.write_bytes(data)
            entry = {"name": name, "kind": "textbook", "urn": from_, "url": from_,
                     "status": "have", "local": str(dst), "bytes": len(data),
                     "ts": date.today().isoformat()}
        except Exception as e:
            entry = {"name": name, "kind": "textbook", "urn": from_, "url": from_,
                     "status": "queued", "why": f"下载失败: {type(e).__name__}: {e}",
                     "ts": date.today().isoformat()}
    else:
        src = Path(from_).expanduser()
        if not src.is_file():
            entry = {"name": name, "kind": "textbook", "urn": from_,
                     "status": "queued", "why": f"本地文件不存在: {from_}",
                     "ts": date.today().isoformat()}
        else:
            dst = DOWNLOADS / src.name
            import shutil
            shutil.copy2(src, dst)
            entry = {"name": name, "kind": "textbook", "urn": from_,
                     "status": "have", "local": str(dst), "bytes": src.stat().st_size,
                     "ts": date.today().isoformat()}
    try:
        append_ticket(entry, tickets)
    except ValueError:
        pass
    return entry


# ---------------- ZHIHU 发现层 ----------------
import subprocess as _subprocess
ZHIHU_SEARCH_BIN = Path.home() / ".workbuddy" / "bin" / "zhihu_search.sh"
# 知乎工单过滤：与前面 sun/q&A / 官方文档类噪声跳过
ZHIHU_NOISE = re.compile(
    r"(学习资料|书籍推荐|简历|面试|微信群|加群|公众号|PDF下载|电子书|"
    r"安装|配置教程|认证指南|大纲|真题|白皮书|我国|我国|怎么学好|如何学习|入门到放弃)", re.I)


def _zhihu_query(query: str, count: int = 10) -> list[dict]:
    """调用统一入口脚本查知乎搜索 API。脚本读 ~/.workbuddy/zhihu/access_secret，
    不在此处落密钥。返回 Items 列表；不可用返回空。"""
    if not ZHIHU_SEARCH_BIN.exists():
        print(f"  ZHIHU 未配置（缺 {ZHIHU_SEARCH_BIN}），跳过知乎发现层")
        return []
    try:
        p = _subprocess.run(
            [str(ZHIHU_SEARCH_BIN), json.dumps({"query": query, "count": count},
                                                ensure_ascii=False)],
            capture_output=True, text=True, timeout=40)
    except (OSError, _subprocess.TimeoutExpired) as e:
        print(f"  ZHIHU 调用失败: {type(e).__name__}: {e}")
        return []
    try:
        d = json.loads(p.stdout)
    except json.JSONDecodeError:
        print(f"  ZHIHU 返回非 JSON: {p.stdout[:120]}")
        return []
    if d.get("Code") != 0:
        print(f"  ZHIHU 返回 Code={d.get('Code')} {d.get('Message')}")
        return []
    return d.get("Data", {}).get("Items", []) or []


def _strip_utm(url: str) -> str:
    """去掉知乎出处的 UTM 溯源参数，保留可回溯链接。"""
    from urllib.parse import urlsplit, urlunsplit
    u = urlsplit(url)
    q = [kv for kv in (u.query.split("&") if u.query else []) if not kv.startswith("utm_")]
    return urlunsplit((u.scheme, u.netloc, u.path, "&".join(q), u.fragment))


def zhihu_discover(topics: list[str], tickets: Path, limit: int = 8,
                   count: int = 8) -> list[dict]:
    """按主题调知乎搜索，每主题配额取候选，与既有工单按 URL 去重后落票。

    只作工程实践线索（source="zhihu"，grade 语义是"线索待核验"）：
    知乎是工程解释/案例素材，不作为权威依据；全文以原 URL 回页面核验。
    """
    existing = load_jsonl(tickets)
    existing_urls = {r.get("urn") for r in existing}
    per_topic = max(2, limit // max(len(topics), 1))
    made: list[dict] = []
    for t in topics:
        got = 0
        for it in _zhihu_query(t, count):
            if got >= per_topic:
                break
            title = (it.get("Title") or "").strip()
            url = _strip_utm(it.get("Url") or "")
            if not title or not url:
                continue
            if ZHIHU_NOISE.search(title):
                continue
            if url in existing_urls:
                continue
            entry = {
                "name": title[:40], "kind": "zhihu",
                "urn": url, "url": url, "title": title,
                "topic": [t], "source": "zhihu",
                "author": it.get("AuthorName") or "",
                "votes": it.get("VoteUpCount") or 0,
                "comments": it.get("CommentCount") or 0,
                "authority": it.get("AuthorityLevel") or "",
                "snippet": (it.get("ContentText") or "")[:200].replace("\n", " "),
                "status": "queued",
                "grade": "ambiguous",
                "why_background": (f"知乎发现层按主题「{t}」召回，工程实践线索；"
                                   f"只作案例/解释素材，全文回原文核验"),
                "ts": date.today().isoformat(),
            }
            try:
                append_ticket(entry, tickets)
            except ValueError:
                continue
            made.append(entry)
            existing_urls.add(url)
            got += 1
    return made


# ---------------- PREP：一键素材包 + 缺口清单 ----------------
def prep(lecture: str, topics: list[str], tickets: Path,
         use_ragflow: bool = False, use_zhihu: bool = False, limit: int = 8) -> dict:
    """写新讲的素材准备入口（自动抓 + 缺口清单）：

    1. 种子表命中 → 逐条探测本地，能落 have 即算"已抓"；否则 queued 待取。
    2. --ragflow → 跑论文发现层，把种子表外新论文落工单（不自动下载，进缺口待你定）。
    3. --zhihu  → 跑知乎发现层，把工程实践线索落工单（只作案例/解释素材）。
    4. 三态分级：可用素材按 grade 分 high（种子锚/高相似）/ ambiguous（发现层低相似待核）；
       无可用素材的主题计为 gap。grade 是证据可信度，不改 status。
    5. 主题覆盖率：以用户给的主题词为分母，每个主题只要有 1 条可用素材即算覆盖。
    """
    made = paper_tickets(topics, tickets)
    found = ragflow_discover(topics, tickets, limit=limit) if use_ragflow else []
    zh = zhihu_discover(topics, tickets, limit=limit) if use_zhihu else []
    rows = load_jsonl(tickets)
    mine = [r for r in rows
            if r.get("kind") == "paper" and (not topics or
               any(t in (r.get("topic") or []) for t in topics))]
    have = [r for r in mine if r.get("status") in ("have", "scored")]
    queued = [r for r in mine if r.get("status") == "queued"]
    high = [r for r in have if grade_of(r) == GRADE_HIGH]
    amb = [r for r in have if grade_of(r) == GRADE_AMBIGUOUS]
    gap = [{"name": r["name"], "why": r.get("why", "待取/待人工核对出处（可走 TEXTBOOK 给 URL，或提供 PDF 走 SCORE_FILE 读文件评分）"),
            "source": r.get("source", "seed")} for r in queued]
    # 主题覆盖率：每个主题词只要有 1 条可用素材即算命中（种子/发现层均可）
    covered = [t for t in topics if any(t in (r.get("topic") or []) for r in have)]
    uncovered = [t for t in topics if t not in covered]
    coverage = {"topics": topics, "covered": covered, "uncovered": uncovered,
                "ratio": round(len(covered) / len(topics), 3) if topics else 0.0}
    report = [f"K1 素材包 · {lecture}（主题: {'、'.join(topics)}）",
              f"种子命中 {len(made)} 篇 · 论文发现层新增 {len(found)} 篇 · 知乎线索 {len(zh)} 条",
              f"三态: 高可信 {len(high)} · 待核 {len(amb)} · 缺口 {len(gap)}",
              f"主题覆盖: {len(covered)}/{len(topics)}（{coverage['ratio']:.0%}）"
              + (f"  待补主题: {'、'.join(uncovered)}" if uncovered else "  全覆盖"), ""]
    if high:
        report.append("高可信（种子锚/高相似，可直接用）:")
        for r in high:
            report.append(f"  ✓ {r['name']}  {r.get('local') or r.get('source','seed')}")
    if amb:
        report.append("待核（发现层低相似，需你确认标题与出处）:")
        for r in amb:
            report.append(f"  ? {r['name']}  sim={r.get('sim','-')}")
    if zh:
        report.append("知乎工程线索（只作案例/解释素材，全文回原文核验）:")
        for r in zh:
            report.append(f"  · {r['name']}  赞{r['votes']} {r.get('author','')}")
            report.append(f"      {r['urn']}")
    if gap:
        report.append("缺口清单（需要你提供素材或指导下载）:")
        for g in gap:
            report.append(f"  · [{g['source']}] {g['name']}")
            report.append(f"      {g['why']}")
    if not have and not gap:
        report.append("（无命中，考虑换主题词或提供文件走 SCORE_FILE）")
    report.append("")
    report.append("下一步：python3 tools/lf/asset_score.py FROM_TICKETS  "
                  "（把新入工单自动打分进台账，进入供料排序）")
    return {"lecture": lecture, "topics": topics,
            "have": [r["name"] for r in have],
            "high": [r["name"] for r in high], "ambiguous": [r["name"] for r in amb],
            "coverage": coverage, "gap": gap, "report": "\n".join(report)}


def summary(tickets: Path) -> str:
    rows = load_jsonl(tickets)
    if not rows:
        return "K1 工单为空（framework/k1/tickets.jsonl 尚无记录）"
    have = [r for r in rows if r.get("status") == "have"]
    queued = [r for r in rows if r.get("status") != "have"]
    L = [f"K1 素材获取工单 · {len(rows)} 条（已取 {len(have)} / 待取 {len(queued)}）"]
    if have:
        L.append("已取:")
        for r in have:
            L.append(f"  ✓ [{r['kind']}] {r['name']}  {r.get('local') or r.get('url','')}")
    if queued:
        L.append("待取(需人工/代理):")
        for r in queued:
            L.append(f"  · [{r['kind']}] {r['name']}  {r.get('why','')}")
    return "\n".join(L)


def selfcheck() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tickets = Path(td) / "t.jsonl"
        made = paper_tickets(["弹性计算"], tickets)
        assert made and all(r["status"] in ("have", "queued") for r in made), "PAPERS 失败"
        rows = load_jsonl(tickets)
        assert rows, "PAPERS 未产出"
        # 重复工单防写
        try:
            append_ticket(rows[0], tickets)
            raise SystemExit("本应拒绝重复工单")
        except ValueError:
            pass
        # 标题提取（离线可测）
        t = extract_title("3190508.3190517.pdf",
                          "Demystifying Serverless Costs: A Data-driven Analysis of AWS Lambda\nAbstract\nServerless…")
        assert t == "Demystifying Serverless Costs: A Data-driven Analysis of AWS Lambda", f"标题提取失败: {t}"
        t2 = extract_title("osdi16_full_proceedings.pdf", "1. Introduction\nLots of text")
        assert "Introduction" not in t2 and t2, f"首行去噪失败: {t2}"
        assert _title_overlap("Demystifying Serverless Costs", "Demystifying Serverless Costs and Prices") > 0.6
        # 三态分级：种子 high；发现层按 sim 分界；覆盖率按主题算
        assert grade_of({"source": "seed"}) == GRADE_HIGH
        assert grade_of({"source": "ragflow", "sim": 0.85}) == GRADE_HIGH
        assert grade_of({"source": "ragflow", "sim": 0.55}) == GRADE_AMBIGUOUS
        assert grade_of({"source": "ragflow", "sim": 0.55, "grade": "high"}) == GRADE_HIGH
        cov_tickets = Path(td) / "c.jsonl"
        cov_tickets.write_text(
            json.dumps({"name":"a","kind":"paper","topic":["虚拟化"],"status":"have"}, ensure_ascii=False)+"\n"+
            json.dumps({"name":"b","kind":"paper","topic":["调度"],"status":"queued"}, ensure_ascii=False)+"\n",
            encoding="utf-8")
        r = prep("自检讲", ["虚拟化", "调度"], cov_tickets)
        assert r["coverage"]["covered"] == ["虚拟化"] and r["coverage"]["uncovered"] == ["调度"]
        assert r["coverage"]["ratio"] == 0.5 and any(g["name"] == "b" for g in r["gap"])
        print(f"自检 OK: PAPERS 命中 {len(made)} 篇（样例 {made[0]['title'][:24]}…），防重复 OK，"
              f"标题提取/去噪/重叠判定 OK，三态分级/主题覆盖 OK")
        sys.exit(0)


def main() -> int:
    if "--selfcheck" in sys.argv:
        selfcheck()
    ap = argparse.ArgumentParser(description="Noteleaf K1 素材获取三件套")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--tickets", default=str(DEFAULT_TICKETS),
                        help="工单路径（默认 framework/k1/tickets.jsonl）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("PAPERS", parents=[common], help="按主题出论文清单并探测本地副本")
    p1.add_argument("topics", nargs="+")
    p1.add_argument("--ragflow", action="store_true",
                    help="额外走 RAGFlow 发现层（需 framework/k1/ragflow.json）")
    p1.add_argument("--limit", type=int, default=8, help="发现层单批最多新增工单（默认 8）")
    p1.add_argument("--min-sim", type=float, default=0.5, help="发现层相似度门槛（默认 0.5）")
    p2 = sub.add_parser("VENDOR", parents=[common], help="抓厂商官方数字卡")
    p2.add_argument("name")
    p2.add_argument("url")
    p3 = sub.add_parser("TEXTBOOK", parents=[common], help="获取教材（URL 下载或本地复制）")
    p3.add_argument("name")
    p3.add_argument("from_")
    p_z = sub.add_parser("ZHIHU", parents=[common], help="知乎工程线索发现层（按主题）")
    p_z.add_argument("topics", nargs="+")
    p_z.add_argument("--limit", type=int, default=8, help="单批最多新增知乎工单（默认 8）")
    p_s = sub.add_parser("SUMMARY", parents=[common], help="工单汇总")
    p_pr = sub.add_parser("PREP", parents=[common],
                          help="一键素材包+缺口清单（写新讲入口：种子表+可选发现层+缺口）")
    p_pr.add_argument("lecture", help="讲 ID，如 03_存储与数据")
    p_pr.add_argument("topics", nargs="+", help="主题词，如 存储 对象存储 文件系统")
    p_pr.add_argument("--ragflow", action="store_true", help="接 RAGFlow 论文发现层")
    p_pr.add_argument("--zhihu", action="store_true", help="接知乎工程线索发现层")
    p_pr.add_argument("--limit", type=int, default=8, help="发现层单批最多新增工单")
    p_pr.add_argument("--out", default="", help="把缺口 JSON 写到此路径（可选）")
    args = ap.parse_args()
    tickets = Path(args.tickets).expanduser()
    if args.cmd == "PAPERS":
        for e in paper_tickets(args.topics, tickets):
            print(f"[{e['status']}] {e['title']} ({e['venue']}, {e['year']})"
                  f"  ← {e['why_background']}")
        if args.ragflow:
            print(f"\n— RAGFlow 发现层（min_sim={args.min_sim}，最多 {args.limit} 条新增）—")
            found = ragflow_discover(args.topics, tickets, limit=args.limit,
                                     min_sim=args.min_sim)
            if not found:
                print("  无种子表外的新增发现（或均已入工单）")
            for e in found:
                print(f"[{e['status']}] {e['title']}  sim={e['sim']}  ← {e['why_background'][:60]}…")
    elif args.cmd == "VENDOR":
        c = vendor_card(args.name, args.url, tickets)
        print(json.dumps(c, ensure_ascii=False, indent=2))
    elif args.cmd == "TEXTBOOK":
        print(json.dumps(textbook(args.name, args.from_, tickets), ensure_ascii=False, indent=2))
    elif args.cmd == "ZHIHU":
        print(f"— 知乎工程线索发现层（按主题，最多 {args.limit} 条新增）—")
        zh = zhihu_discover(args.topics, tickets, limit=args.limit)
        if not zh:
            print("  无新增知乎线索（均已入工单，或知乎入口不可用）")
        for e in zh:
            print(f"[{e['status']}] {e['name']}  赞{e['votes']} {e.get('author','')}")
            print(f"      {e['urn']}")
            print(f"      {e['snippet'][:80]}…")
    elif args.cmd == "SUMMARY":
        print(summary(tickets))
    elif args.cmd == "PREP":
        r = prep(args.lecture, args.topics, tickets, use_ragflow=args.ragflow,
                 use_zhihu=args.zhihu, limit=args.limit)
        print(r["report"])
        if args.out:
            Path(args.out).expanduser().write_text(
                json.dumps({k: v for k, v in r.items() if k != "report"},
                           ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"缺口 JSON 已写: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
