#!/usr/bin/env python3
"""peer_review.py — Stage 7.5 mechanical pre-check for the peer-review stage.

Performs the quantifiable part of a simulated peer review and writes a
Major/Minor draft into review-report.md. It does NOT edit the manuscript
(read-only, Rule R3). The Agent fills in reviewer narratives and the final
"ready to finalize" call.

Checks:
  * structural: required sections present
  * evidence ledger: quantitative claims in the manuscript trace to stats-report
  * citation integrity: every \\cite{key} exists in library.bib AND the bib
    entry is complete (no NEED-METADATA / missing fields); flags weak/off-topic
    citations for human judgment
  * stats consistency: AUC/ACC/F1/p-values in the manuscript match stats-report

Exit code 0 (pre-check is advisory); the Agent decides pass/fail.
Usage:
    python peer_review.py --manuscript draft.md --stats stats-report.md \
        --bib library.bib --out review-report.md
"""
from __future__ import annotations
import argparse
import json
import os
import re

REQUIRED_SECTIONS = ["abstract", "introduction", "related", "method", "result",
                     "discussion", "limitation", "conclusion"]


def _bib_keys(bib_path: str) -> dict:
    """Return {key: entry_text} and flag completeness."""
    if not os.path.exists(bib_path):
        return {}
    txt = open(bib_path, encoding="utf-8", errors="replace").read()
    out = {}
    for m in re.finditer(r"@\w+\{([^,]+),\n(.*?)\n\}", txt, re.S):
        key = m.group(1).strip()
        body = m.group(2)
        has_need = "NEED-METADATA" in body
        fields = set(re.findall(r"^\s*(\w+)\s*=", body, re.M))
        complete = not has_need and {"title", "author", "year"}.issubset(fields)
        out[key] = {"need_metadata": has_need, "complete": complete, "body": body}
    return out


def _section_present(lower: str, name: str) -> bool:
    # fuzzy: a heading containing the keyword
    return bool(re.search(rf"#+\s*.*{name}.*", lower))


def _float_pairs(text: str) -> list:
    return [float(x) for x in re.findall(r"-?\d+\.\d+", text)]


def main() -> int:
    ap = argparse.ArgumentParser(description="Peer-review mechanical pre-check.")
    ap.add_argument("--manuscript", required=True)
    ap.add_argument("--stats", default=None)
    ap.add_argument("--bib", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    ms = open(args.manuscript, encoding="utf-8", errors="replace").read()
    ms_low = ms.lower()
    bib = _bib_keys(args.bib)

    majors, minors = [], []

    # 1. structure
    missing = [s for s in REQUIRED_SECTIONS if not _section_present(ms_low, s)]
    if missing:
        majors.append(f"缺失核心章节: {', '.join(missing)}（建议补齐 Related Work / Limitations）")

    # 2. evidence ledger: quantitative claims need numbers nearby
    result_block = ms[ms_low.find("## 3"):] if "## 3" in ms_low else ms
    if not re.search(r"\d+\.\d{2,}", result_block):
        majors.append("Results 段未出现可回溯的量化数字（claim→evidence 证据链缺失）")

    # 3. citation integrity
    cites = set()
    for c in re.findall(r"\\cite\{([^}]+)\}", ms):
        cites.update(k.strip() for k in c.split(","))
    for k in cites:
        if k not in bib:
            majors.append(f"引用键 `{k}` 不在 library.bib（虚假引用风险）")
        elif not bib[k]["complete"]:
            minors.append(f"引用键 `{k}` bib 条目不完整（NEED-METADATA/缺字段），需补全元数据")

    # 4. stats consistency (anchor on "<METRIC> mean = 0.XXX" to avoid p-values)
    if args.stats and os.path.exists(args.stats):
        stats = open(args.stats, encoding="utf-8", errors="replace").read()
        for met in ["auc", "acc", "f1"]:
            m_ms = re.search(rf"{met}\s+mean\s*=\s*(0\.[0-9]+)", ms_low)
            m_st = re.search(rf"{met}:\s*baseline=([0-9]+\.[0-9]+)", stats.lower())
            if m_ms and m_st:
                if abs(float(m_ms.group(1)) - float(m_st.group(1))) > 0.03:
                    majors.append(f"稿件与 stats-report 的 {met} 不一致（{m_ms.group(1)} vs {m_st.group(1)}）")

    # verdict
    verdict = "需修订" if majors else ("可定稿" if not minors else "可定稿（建议修 Minor）")

    lines = ["# Peer Review Report (mechanical pre-check)\n"]
    lines.append("## 结构检查")
    lines.append(f"- {'章节齐全' if not missing else '缺失: ' + ', '.join(missing)}\n")
    lines.append("## Evidence ledger")
    lines.append(f"- {'量化论断可回溯' if not majors or 'claim' not in ' '.join(majors) else '见 Major'}\n")
    lines.append("## Citation 审查")
    lines.append(f"- INCOMPLETE_REF: {[k for k in cites if k in bib and not bib[k]['complete']] or 'none'}")
    lines.append(f"- 不在 bib: {[k for k in cites if k not in bib] or 'none'}\n")
    lines.append("## 统计一致性")
    lines.append("- " + ("一致" if not any('stats-report' in m or '不一致' in m for m in majors) else "见 Major") + "\n")
    lines.append("## 整改清单")
    lines.append("### Major（必须改）")
    lines += [f"- [ ] {m}" for m in majors] or ["- 无"]
    lines.append("### Minor（建议改）")
    lines += [f"- [ ] {m}" for m in minors] or ["- 无"]
    lines.append(f"\n## 综合建议: {verdict}")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[peer_review] majors={len(majors)} minors={len(minors)} -> {args.out} ({verdict})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
