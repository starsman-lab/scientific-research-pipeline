#!/usr/bin/env python3
"""gate_check.py — Stage 7 quality-gate automation (partial).

Partially automates the 6-dimension epistemology review (Rule R3: read-only on the
manuscript — this script never edits the draft):
  * validates the review scorecard format (each dimension 1-5 + gate threshold)
  * flags FABRICATED DATA by scanning provenance.log for null/error results
  * flags FAKE CITATIONS by checking every \\cite key against library.bib
Outputs gate-check.json + gate-check.md. Final human sign-off stays with the user
(Rule R6).

Usage:
    python gate_check.py --review review-report.md --workdir <dir> --bib <lib.bib>

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


def _bib_keys(bib_path: str) -> set:
    if not os.path.exists(bib_path):
        return set()
    return set(re.findall(r"@\w+\{([^,]+),", open(bib_path, encoding="utf-8", errors="replace").read()))


def main() -> int:
    ap = argparse.ArgumentParser(description="Quality-gate automation.")
    ap.add_argument("--review", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--bib", default=os.path.join(ROOT_DEFAULT, "references", "library.bib"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = args.out or os.path.join(args.workdir, "gate-check.md")

    scores = _scorecard(args.review)
    nulls = _prov_nulls(args.workdir)
    bib_keys = _bib_keys(args.bib)

    # fake citation scan: find any cite key not in bib within the review/manuscript dir
    fake_cites = []
    for root, _, files in os.walk(args.workdir):
        for fn in files:
            if fn.endswith(".md"):
                txt = open(os.path.join(root, fn), encoding="utf-8", errors="replace").read()
                for k in re.findall(r"\\cite\{([^}]+)\}", txt):
                    for kk in k.split(","):
                        kk = kk.strip()
                        if kk and kk not in bib_keys:
                            fake_cites.append(kk)

    below = [d for d, s in scores.items() if s < GATE_THRESHOLD]
    passed = (not below) and (not nulls) and (not fake_cites)
    summary = {
        "scores": scores, "dims_below_threshold": below,
        "fabricated_data_signals": nulls, "fake_citations": sorted(set(fake_cites)),
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
        f.write(f"\n**verdict**: {'PASS — ready for human sign-off' if passed else 'FAIL — resolve before R6 sign-off'}\n")
    with open(out.replace(".md", ".json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"[gate_check] dims_below={below} nulls={len(nulls)} fake_cites={len(set(fake_cites))} "
          f"-> {out} ({'PASS' if passed else 'FAIL'})")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
