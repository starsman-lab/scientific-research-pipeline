#!/usr/bin/env python3
"""fetch_papers.py — literature scan fetcher for the research pipeline.

Pulls recent papers from arXiv (and optionally Semantic Scholar) and writes:
  * one Markdown card per paper -> $RESEARCH_PIPELINE_ROOT/references/papers/<year>-<slug>.md
  * one bibtex entry per paper    -> $RESEARCH_PIPELINE_ROOT/references/library.bib

Every external call is appended to provenance.log (Rule R1). On network failure
the paper is SKIPPED and the failure is recorded as null — never fabricated
(Rule R0). The script uses only the Python standard library.

Usage:
    python fetch_papers.py --query "multimodal medical foundation model" --max 20 --year-from 2024

Exit code 0 even when some fetches fail (failures are logged, not fatal).
"""
from __future__ import annotations
import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

NS = {"a": "http://www.w3.org/2005/Atom"}
ROOT_DEFAULT = os.environ.get(
    "RESEARCH_PIPELINE_ROOT",
    r"D:\Workbuddy\phd_learn_agent\research-pipeline",
)
WORKDIR_DEFAULT = os.environ.get("RESEARCH_WORKDIR", "./research-output")


def _http_get(url: str, timeout: int = 25) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": "research-pipeline/1.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return f"__ERROR__::{e}"


def _slug(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:60] or "untitled"


def _relevance(query: str, title: str, summary: str) -> str:
    """Token-overlap relevance: 高/中/低 vs the research query."""
    q_tokens = set(re.findall(r"[a-z0-9]{4,}", query.lower()))
    doc = (title + " " + summary).lower()
    doc_tokens = set(re.findall(r"[a-z0-9]{4,}", doc))
    if not q_tokens:
        return "中"
    overlap = len(q_tokens & doc_tokens) / max(1, len(q_tokens))
    if overlap >= 0.5:
        return "高"
    if overlap >= 0.25:
        return "中"
    return "低"


def _arxiv_search(query: str, max_n: int, year_from: int, keep_low: bool = False):
    url = (
        "http://export.arxiv.org/api/query?search_query=all:"
        + urllib.parse.quote(query)
        + f"&start=0&max_results={max_n}&sortBy=submittedDate&sortOrder=descending"
    )
    raw = _http_get(url)
    if raw is None or raw.startswith("__ERROR__"):
        return [], raw
    out = []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        return [], f"__ERROR__::{e}"
    for entry in root.findall("a:entry", NS):
        title = " ".join(entry.findtext("a:title", "", NS).split())
        summary = " ".join(entry.findtext("a:summary", "", NS).split())
        published = entry.findtext("a:published", "", NS)[:4]
        if published and int(published) < year_from:
            continue
        rel = _relevance(query, title, summary)
        if rel == "低" and not keep_low:
            continue  # 低相关不入库，避免污染引用（R2 相关性）
        aid_url = entry.findtext("a:id", "", NS)
        aid = aid_url.rsplit("/", 1)[-1]
        authors = [a.findtext("a:name", "", NS) for a in entry.findall("a:author", NS)]
        cats = [c.get("term") for c in entry.findall("a:category", NS)]
        out.append({
            "source": "arxiv",
            "id": aid,
            "title": title,
            "abstract": summary,
            "authors": authors,
            "year": published,
            "url": aid_url,
            "categories": cats,
            "relevance": rel,
        })
    return out, None


def _card_md(p: dict) -> str:
    authors = ", ".join(p["authors"][:8]) + (" et al." if len(p["authors"]) > 8 else "")
    return (
        f"# {p['title']}\n\n"
        f"- **Source**: {p['source']} `{p['id']}`\n"
        f"- **Year**: {p['year']}\n"
        f"- **Relevance**: {p.get('relevance', '中')}\n"
        f"- **Authors**: {authors}\n"
        f"- **URL**: {p['url']}\n"
        f"- **Categories**: {', '.join(p['categories'])}\n\n"
        f"## Abstract\n\n{p['abstract']}\n\n"
        f"## Anchors\n\n"
        f"- url: {p['url']}\n"
        f"- arxiv: {p['id']}\n\n"
        f"## Notes (fill after reading)\n\n"
        f"- method: \n- dataset: \n- metric: \n- gap: \n"
        f"- related_work_role: <支持/对照/相邻>\n"
    )


def _bib_entry(p: dict) -> str:
    key = f"{p['source']}{p['year']}{_slug(p['title'])[:12]}"
    authors = " and ".join(p["authors"][:3])
    # arxiv 提供 title/author/year；不带 NEED-METADATA 占位（quality-gate 会查完整性）
    return (
        f"@article{{{key},\n"
        f"  title = {{{p['title']}}},\n"
        f"  author = {{{authors}}},\n"
        f"  year = {{{p['year']}}},\n"
        f"  url = {{{p['url']}}},\n"
        f"  eprint = {{{p['id']}}},\n"
        f"  relevance = {{{p.get('relevance', '中')}}}\n"
        f"}}\n\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch papers for literature scan.")
    ap.add_argument("--query", required=True)
    ap.add_argument("--max", type=int, default=20)
    ap.add_argument("--year-from", type=int, default=2024)
    ap.add_argument("--root", default=ROOT_DEFAULT)
    ap.add_argument("--workdir", default=WORKDIR_DEFAULT)
    args = ap.parse_args()

    papers_dir = os.path.join(args.root, "references", "papers")
    lib_bib = os.path.join(args.root, "references", "library.bib")
    os.makedirs(papers_dir, exist_ok=True)
    prov_log = os.path.join(args.workdir, "provenance.log")
    os.makedirs(args.workdir, exist_ok=True)

    papers, err = _arxiv_search(args.query, args.max, args.year_from)
    ts = dt.datetime.now(dt.timezone.utc).isoformat()

    call = {
        "ts": ts,
        "stage": "literature-review",
        "tool": "fetch_papers.py",
        "query": args.query,
        "source": "arxiv",
        "result": "error" if err else f"{len(papers)} papers",
        "error": err,
    }
    with open(prov_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(call, ensure_ascii=False) + "\n")
    if err:
        print(f"[fetch_papers] arxiv failed: {err}", file=sys.stderr)
        return 0

    written = 0
    for p in papers:
        fn = f"{p['year']}-{_slug(p['title'])}.md"
        with open(os.path.join(papers_dir, fn), "w", encoding="utf-8") as f:
            f.write(_card_md(p))
        with open(lib_bib, "a", encoding="utf-8") as f:
            f.write(_bib_entry(p))
        written += 1
        print(f"  wrote {fn}")

    # scan report
    report = os.path.join(args.workdir, "scan.md")
    with open(report, "w", encoding="utf-8") as f:
        f.write(f"# Literature Scan — {args.query}\n\n")
        f.write(f"- query: {args.query}\n- year_from: {args.year_from}\n"
                f"- fetched (高/中相关): {written}\n- skipped (低相关, 不入库): {args.max - len(papers)}\n\n")
        f.write("| # | 标题 | 年 | 相关性 | 来源 |\n|---|------|----|--------|------|\n")
        for i, p in enumerate(papers, 1):
            f.write(f"| {i} | {p['title']} | {p['year']} | {p.get('relevance','中')} | {p['url']} |\n")
    print(f"[fetch_papers] done: {written} papers (高/中相关) -> {papers_dir}; "
          f"skipped {args.max - len(papers)} 低相关; report -> {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
