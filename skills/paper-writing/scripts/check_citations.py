#!/usr/bin/env python3
"""check_citations.py — Stage 6 citation integrity check.

Scans a draft (Markdown) for unresolved [CITATION NEEDED] markers and verifies that
every \\cite{key} reference actually exists in $RESEARCH_PIPELINE_ROOT/references/library.bib.
Enforces Rule R2 (real citations only). Outputs citation-check.md + a JSON summary.

Usage:
    python check_citations.py --draft draft.md --bib references/library.bib --out citation-check.md

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


def _bib_keys(bib_path: str) -> set[str]:
    if not os.path.exists(bib_path):
        return set()
    text = open(bib_path, "r", encoding="utf-8", errors="replace").read()
    return set(re.findall(r"@\w+\{([^,]+),", text))


def main() -> int:
    ap = argparse.ArgumentParser(description="Citation integrity check.")
    ap.add_argument("--draft", required=True)
    ap.add_argument("--bib", default=os.path.join(ROOT_DEFAULT, "references", "library.bib"))
    ap.add_argument("--out", default="citation-check.md")
    args = ap.parse_args()

    draft = open(args.draft, "r", encoding="utf-8", errors="replace").read()
    needed = re.findall(r"\[CITATION NEEDED\]", draft)
    cites = re.findall(r"\\cite\{([^}]+)\}", draft)
    # also catch pandoc/latex multi-key
    keys = set()
    for c in cites:
        keys.update(k.strip() for k in c.split(","))

    bib_keys = _bib_keys(args.bib)
    missing = sorted(k for k in keys if k not in bib_keys)

    passed = (len(needed) == 0) and (len(missing) == 0)
    summary = {
        "citation_needed_unresolved": len(needed),
        "cite_keys_total": len(keys),
        "missing_from_bib": missing,
        "passed": passed,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("# Citation Check\n\n")
        f.write(f"- [CITATION NEEDED] unresolved: {len(needed)}\n")
        f.write(f"- \\cite keys: {len(keys)}  | missing from library.bib: {len(missing)}\n")
        f.write(f"- **verdict**: {'PASS' if passed else 'FAIL — fix before gate'}\n\n")
        if missing:
            f.write("## Missing keys\n\n" + "\n".join(f"- `{k}`" for k in missing) + "\n")
    print(f"[check_citations] needed={len(needed)} missing={len(missing)} -> {args.out} "
          f"({'PASS' if passed else 'FAIL'})")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
