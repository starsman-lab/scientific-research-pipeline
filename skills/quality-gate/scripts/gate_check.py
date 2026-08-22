#!/usr/bin/env python3
"""gate_check.py — Stage 7/8 quality-gate automation (partial).

Partially automates the 6-dimension epistemology review (Rule R3: read-only on the
manuscript — this script never edits the draft):
  * validates the review scorecard format (each dimension 1-5 + gate threshold)
  * flags FABRICATED DATA by scanning provenance.log for null/error results
  * flags FAKE / WEAK CITATIONS by checking every \\cite key against library.bib
    and flagging incomplete entries (NEED-METADATA / missing fields)
  * flags STATS MISMATCH by comparing manuscript numbers to data-analysis/stats-report.md
Outputs gate-check.json + gate-check.md. Final human sign-off stays with the user
(Rule R6).

Usage:
    python gate_check.py --review review-report.md --workdir <dir> --bib <lib.bib> \
        --stats <stats-report.md>

Dependencies: Python standard library only.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys

ROOT_DEFAULT = os.environ.get(
    "RESEARCH_PIPELINE_ROOT",
    r"D:\Workbuddy\phd_learn_agent\research-pipeline",
)

DIMS = ["evidence_relevance", "falsifiability", "scope_calibration",
        "coherence", "exploration_completeness", "methodology_rigor"]
GATE_THRESHOLD = 3  # any dimension below this fails the gate


def _scorecard(review_path: str) -> dict:
    scores = {}
    if os.path.exists(review_path):
        txt = open(review_path, "r", encoding="utf-8", errors="replace").read()
        for d in DIMS:
            m = re.search(rf"{d}\D*?([1-5])", txt)
            if m:
                scores[d] = int(m.group(1))
    return scores


def _prov_nulls(workdir: str) -> list:
    log = os.path.join(workdir, "provenance.log")
    bad = []
    if os.path.exists(log):
        for line in open(log, "r", encoding="utf-8", errors="replace"):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("result") == "error" or rec.get("error"):
                bad.append(rec.get("tool") or rec.get("stage") or "?")
    return bad


def _bib_entries(bib_path: str) -> dict:
    """{key: {'complete': bool, 'need_metadata': bool, 'title': str}}."""
    out = {}
    if not os.path.exists(bib_path):
        return out
    txt = open(bib_path, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"@\w+\{([^,]+),\n(.*?)\n\}", txt, re.S):
        key = m.group(1).strip()
        body = m.group(2)
        need = "NEED-METADATA" in body
        fields = set(re.findall(r"^\s*(\w+)\s*=", body, re.M))
        complete = (not need) and {"title", "author", "year"}.issubset(fields)
        title_m = re.search(r"title\s*=\s*\{([^}]+)\}", body)
        out[key] = {"complete": complete, "need_metadata": need,
                    "title": title_m.group(1) if title_m else ""}
    return out


def _stats_consistency(workdir: str, stats_path: str) -> list:
    """Compare AUC/ACC/F1 baseline/proposed means in stats-report vs manuscript.

    Conservative: only flags a manuscript float that deviates from BOTH the
    baseline and proposed value of its metric by > 0.03 (rounding-tolerant).
    Returns a list of human-readable mismatch strings.
    """
    if not stats_path or not os.path.exists(stats_path):
        return []
    stats = open(stats_path, encoding="utf-8", errors="replace").read()
    targets = {}
    for met in ["auc", "acc", "f1"]:
        m = re.search(rf"{met}:\s*baseline=([0-9]+\.[0-9]+)\s+proposed=([0-9]+\.[0-9]+)", stats)
        if m:
            targets[met] = (float(m.group(1)), float(m.group(2)))

    # gather manuscript text (exclude review/gate reports to avoid self-comparison)
    mtext = []
    for root, _, files in os.walk(workdir):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            low = fn.lower()
            if "review" in low or "gate" in low or "handoff" in low:
                continue
            mtext.append(open(os.path.join(root, fn), encoding="utf-8", errors="replace").read())
    blob = "\n".join(mtext).lower()

    issues = []
    # manuscript states scores as "<METRIC> mean = 0.XXX" (Abstract/Results);
    # match that explicit form only (allow a line break), so p-values /
    # mean_diff are ignored.
    ms_vals = {}
    for met in targets:
        m = re.search(rf"{met}\s+mean\s*=\s*\n?\s*(0\.[0-9]+)", blob)
        if m:
            ms_vals[met] = float(m.group(1))
    for met, (b, p) in targets.items():
        if met not in ms_vals:
            continue
        val = ms_vals[met]
        if abs(val - b) > 0.03 and abs(val - p) > 0.03:
            issues.append(f"{met} manuscript mean {val} deviates >0.03 from both baseline {b} and proposed {p}")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="Quality-gate automation.")
    ap.add_argument("--review", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--bib", default=os.path.join(ROOT_DEFAULT, "references", "library.bib"))
    ap.add_argument("--stats", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = args.out or os.path.join(args.workdir, "gate-check.md")

    scores = _scorecard(args.review)
    nulls = _prov_nulls(args.workdir)
    entries = _bib_entries(args.bib)

    # citation scan across the workdir
    incomplete_refs = []
    fake_cites = []
    for root, _, files in os.walk(args.workdir):
        for fn in files:
            if fn.endswith(".md"):
                txt = open(os.path.join(root, fn), encoding="utf-8", errors="replace").read()
                for k in re.findall(r"\\cite\{([^}]+)\}", txt):
                    for kk in k.split(","):
                        kk = kk.strip()
                        if kk and kk not in entries:
                            fake_cites.append(kk)
                        elif kk and not entries.get(kk, {}).get("complete"):
                            incomplete_refs.append(kk)

    stats_issues = _stats_consistency(args.workdir, args.stats)

    below = [d for d, s in scores.items() if s < GATE_THRESHOLD]
    passed = (not below) and (not nulls) and (not fake_cites) and (not incomplete_refs) and (not stats_issues)
    summary = {
        "scores": scores, "dims_below_threshold": below,
        "fabricated_data_signals": nulls,
        "fake_citations": sorted(set(fake_cites)),
        "incomplete_refs": sorted(set(incomplete_refs)),
        "stats_mismatches": stats_issues,
        "passed": passed,
    }
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("# Quality Gate Check (automated)\n\n")
        f.write("## 6-dimension scorecard\n\n")
        for d in DIMS:
            f.write(f"- {d}: {scores.get(d, 'n/a')}\n")
        f.write(f"\nDimensions below threshold ({GATE_THRESHOLD}): {below or 'none'}\n")
        f.write(f"\nFabricated-data signals (provenance null/error): {nulls or 'none'}\n")
        f.write(f"\nFake citations (not in library.bib): {sorted(set(fake_cites)) or 'none'}\n")
        f.write(f"\nIncomplete refs (NEED-METADATA/missing fields): {sorted(set(incomplete_refs)) or 'none'}\n")
        f.write(f"\nStats mismatches (vs stats-report): {stats_issues or 'none'}\n")
        f.write(f"\n**verdict**: {'PASS — ready for human sign-off' if passed else 'FAIL — resolve before R6 sign-off'}\n")
    with open(out.replace(".md", ".json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"[gate_check] dims_below={below} nulls={len(nulls)} fake_cites={len(set(fake_cites))} "
          f"incomplete={len(set(incomplete_refs))} stats={len(stats_issues)} -> {out} "
          f"({'PASS' if passed else 'FAIL'})")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
