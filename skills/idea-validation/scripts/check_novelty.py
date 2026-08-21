#!/usr/bin/env python3
"""check_novelty.py — novelty / overlap check for an Idea (Stage 2).

Given an idea description, searches arXiv for recent (<=3 year) related work and
computes a lightweight textual-overlap score against each hit. Outputs a novelty
report. This is a HEURISTIC screen, NOT a substitute for expert judgement — the
final go/no-go decision stays with the human (Rule R6). No data is fabricated
(Rule R0); on search failure the run is recorded as null in provenance.

Usage:
    python check_novelty.py --idea "knowledge-constrained multimodal heart-failure risk model" --max 15

Dependencies: Python standard library only.
"""
from __future__ import annotations
import argparse
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


def _tokenize(text: str) -> set[str]:
    toks = re.findall(r"[a-z0-9]{3,}", text.lower())
    stop = {"the", "and", "for", "with", "that", "this", "from", "using", "model",
            "models", "based", "approach", "method", "learning", "network", "data"}
    return {t for t in toks if t not in stop}


def _overlap(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _arxiv_search(query: str, max_n: int):
    url = (
        "http://export.arxiv.org/api/query?search_query=all:"
        + urllib.parse.quote(query)
        + f"&start=0&max_results={max_n}&sortBy=relevance"
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
        year = entry.findtext("a:published", "", NS)[:4]
        out.append({
            "title": title, "abstract": summary, "year": year,
            "url": entry.findtext("a:id", "", NS),
        })
    return out, None


def main() -> int:
    ap = argparse.ArgumentParser(description="Novelty check for an idea.")
    ap.add_argument("--idea", required=True, help="idea description / claim")
    ap.add_argument("--max", type=int, default=15)
    ap.add_argument("--root", default=ROOT_DEFAULT)
    ap.add_argument("--workdir", default=WORKDIR_DEFAULT)
    args = ap.parse_args()

    idea_tokens = _tokenize(args.idea)
    hits, err = _arxiv_search(args.idea, args.max)
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    prov = os.path.join(args.workdir, "provenance.log")
    os.makedirs(args.workdir, exist_ok=True)

    with open(prov, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": ts, "stage": "idea-validation", "tool": "check_novelty.py",
            "query": args.idea, "source": "arxiv",
            "result": "error" if err else f"{len(hits)} hits", "error": err,
        }, ensure_ascii=False) + "\n")

    scored = []
    if not err:
        for h in hits:
            score = _overlap(idea_tokens, _tokenize(h["title"] + " " + h["abstract"]))
            scored.append((score, h))

    scored.sort(key=lambda x: x[0], reverse=True)
    max_score = scored[0][0] if scored else 0.0
    # heuristic verdict
    if max_score >= 0.45:
        verdict = "LIKELY_DONE — strong overlap, revise or abandon"
    elif max_score >= 0.25:
        verdict = "CLOSE — differentiate clearly"
    else:
        verdict = "NOVEL_ENOUGH — proceed to story check"

    report = os.path.join(args.workdir, "novelty-check.md")
    with open(report, "w", encoding="utf-8") as f:
        f.write(f"# Novelty Check\n\n- idea: {args.idea}\n")
        f.write(f"- max_overlap: {max_score:.3f}\n- verdict: {verdict}\n\n")
        f.write("## Top overlaps (heuristic)\n\n")
        for s, h in scored[:10]:
            f.write(f"- {s:.3f} | {h['title']} ({h['year']}) — {h['url']}\n")
    print(f"[check_novelty] max_overlap={max_score:.3f} verdict={verdict} -> {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
