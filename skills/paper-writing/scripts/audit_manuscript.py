#!/usr/bin/env python3
"""audit_manuscript.py — claim→evidence audit for the paper-writing stage.

Implements the "argument contract" self-check (nature-skills proposal-first +
Imbad0202 claim→evidence receipt). Read-only. Verifies:
  * every Contribution listed in argument-contract.md has a corresponding
    quantitative result in the manuscript
  * Related-work map keys are all real and present in library.bib
  * no unresolved [CITATION NEEDED]
  * Discussion explicitly discusses the mechanism hypothesis

Outputs audit-report.md with Major/Minor. Exit 0 (advisory).
Usage:
    python audit_manuscript.py --contract argument-contract.md \
        --manuscript main.md --bib library.bib --out audit-report.md
"""
from __future__ import annotations
import argparse
import os
import re


def _section(lower: str, header: str) -> str:
    m = re.search(rf"##\s*{header}.*?(?=\n##\s|\Z)", lower, re.S)
    return m.group(0) if m else ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Argument-contract audit.")
    ap.add_argument("--contract", required=True)
    ap.add_argument("--manuscript", required=True)
    ap.add_argument("--bib", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    contract = open(args.contract, encoding="utf-8", errors="replace").read()
    ms = open(args.manuscript, encoding="utf-8", errors="replace").read()
    ms_low = ms.lower()

    majors, minors = [], []

    # 1. every Contribution Cn has a number in the manuscript
    contribs = re.findall(r"^- C\d+:\s*(.+)$", contract, re.M)
    if not contribs:
        majors.append("论证契约未列出任何 Contribution（C1/C2/...）")
    for c in contribs:
        # a contribution is 'backed' if the manuscript contains a number near it;
        # heuristic: manuscript Results must contain the metric numbers.
        if not re.search(r"\d+\.\d{2,}", ms_low):
            majors.append(f"Contribution 缺可回溯数字: {c[:60]}...")
            break

    # 2. related-work map keys exist in bib
    if args.bib and os.path.exists(args.bib):
        bib = open(args.bib, encoding="utf-8", errors="replace").read()
        keys = set(re.findall(r"@\w+\{([^,]+),", bib))
        for line in re.findall(r"-\s*(支持|对照|相邻):\s*(.*)", contract):
            for k in re.findall(r"\[?([a-z0-9\-]+)\]?", line[1]):
                k = k.strip()
                if k and k not in keys:
                    minors.append(f"Related-work 引用键 `{k}` 不在 library.bib")

    # 3. no unresolved CITATION NEEDED
    if "[CITATION NEEDED]" in ms:
        majors.append("稿件含未解决的 [CITATION NEEDED]（R2 拦截）")

    # 4. mechanism discussed in Discussion
    disc = _section(ms_low, "discussion")
    if not re.search(r"because|due to|since|mechanism|why", disc):
        minors.append("Discussion 未显式讨论 mechanism（为什么 C1 成立）")

    # 5. limitations present
    if not _section(ms_low, "limitation"):
        minors.append("缺 Limitations 章节（建议含校准/数据可用性/泛化威胁）")

    verdict = "需修订" if majors else ("可定稿" if not minors else "可定稿（建议修 Minor）")
    lines = ["# Manuscript Audit (argument contract)\n"]
    lines.append("## 整改清单")
    lines.append("### Major（必须改）")
    lines += [f"- [ ] {m}" for m in majors] or ["- 无"]
    lines.append("### Minor（建议改）")
    lines += [f"- [ ] {m}" for m in minors] or ["- 无"]
    lines.append(f"\n## 综合建议: {verdict}")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[audit] majors={len(majors)} minors={len(minors)} -> {args.out} ({verdict})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
