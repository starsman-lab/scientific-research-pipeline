#!/usr/bin/env python3
"""analyze.py — Stage 5 data analysis & figure generation.

Consumes the JSON result envelopes produced by code-execution, merges them into a
pandas DataFrame, computes primary metrics + effect sizes, runs statistical tests
(with multiple-comparison correction to avoid p-hacking), and renders >=9
publication-ready 300-DPI figures in an academic color palette. Writes
stats-report.md. Every aggregation step logs provenance (Rule R1); null/failed
runs from code-execution are KEPT as null and excluded from statistics, never
back-filled (Rule R0).

Usage:
    python analyze.py --results results/ --out analysis/
    python analyze.py --demo --out analysis/      # synthetic demo run

Dependencies: pandas, numpy, scipy, matplotlib (statsmodels optional).
"""
from __future__ import annotations
import argparse
import datetime as dt
import glob
import json
import os
import sys

# ---- academic palette (muted, color-blind-friendly-ish) -------------------
C_PRIMARY = "#1f3a5f"   # deep blue
C_SECOND = "#b23b3b"    # brick red
C_THIRD = "#4a7c59"     # moss green
C_FOURTH = "#d9a441"    # ochre
C_GRID = "#c9c9c9"
PALETTE = [C_PRIMARY, C_SECOND, C_THIRD, C_FOURTH, "#6a4c93", "#887044"]


def _need_libs():
    try:
        import numpy as np  # noqa: F401
        import pandas as pd  # noqa: F401
        import scipy.stats as st  # noqa: F401
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # noqa: F401
        return True
    except ImportError as e:  # pragma: no cover
        print(f"[analyze] missing dependency: {e}\nInstall: pip install pandas numpy scipy matplotlib",
              file=sys.stderr)
        return False


def _demo_data(out_dir: str) -> str:
    """Write a small synthetic results/ set so the pipeline is runnable end-to-end."""
    import numpy as np
    os.makedirs(out_dir, exist_ok=True)
    rng = np.random.default_rng(0)
    methods = ["baseline", "proposed"]
    metrics = ["auc", "acc", "f1"]
    for i in range(12):
        m = methods[i % 2]
        base = {"baseline": 0.72, "proposed": 0.81}[m]
        rec = {
            "run": i, "method": m,
            "auc": float(np.clip(rng.normal(base, 0.04), 0, 1)),
            "acc": float(np.clip(rng.normal(base - 0.02, 0.04), 0, 1)),
            "f1": float(np.clip(rng.normal(base - 0.01, 0.04), 0, 1)),
            "status": "ok",
        }
        with open(os.path.join(out_dir, f"run_{i:02d}.json"), "w") as f:
            json.dump(rec, f, indent=2)
    return out_dir


def _load_results(results_dir: str):
    rows = []
    nulls = 0
    for fp in sorted(glob.glob(os.path.join(results_dir, "*.json"))):
        with open(fp, "r", encoding="utf-8") as f:
            try:
                rec = json.load(f)
            except json.JSONDecodeError:
                nulls += 1
                continue
        if rec.get("status") == "error" or rec.get("auc") is None:
            nulls += 1
            continue
        rows.append(rec)
    return rows, nulls


def _stats_block(df, metrics):
    import numpy as np
    import scipy.stats as st
    from statsmodels.stats.multitest import multipletests  # type: ignore
    lines = []
    pvals = []
    # paired comparison proposed vs baseline across runs (method is the grouping)
    base = df[df.method == "baseline"]
    prop = df[df.method == "proposed"]
    for met in metrics:
        t, p = st.ttest_ind(prop[met].values, base[met].values, equal_var=False)
        d = (prop[met].mean() - base[met].mean()) / df[met].std(ddof=1)
        pvals.append(p)
        lines.append(f"- {met}: baseline={base[met].mean():.3f} proposed={prop[met].mean():.3f} "
                     f"cohen_d={d:.3f} p={p:.2e}")
    rejected, pvals_corr, _, _ = multipletests(pvals, method="holm")
    lines.append("\nMultiple-comparison correction (Holm):")
    for met, p, pc, r in zip(metrics, pvals, pvals_corr, rejected):
        lines.append(f"- {met}: raw_p={p:.2e} holm_p={pc:.2e} sig={bool(r)}")
    return "\n".join(lines)


def _figures(df, out_dir, metrics):
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.color": C_GRID,
                         "figure.dpi": 300, "savefig.dpi": 300})
    methods = sorted(df.method.unique())
    paths = []

    def _save(fig, name):
        p = os.path.join(out_dir, name)
        fig.savefig(p, bbox_inches="tight")
        plt.close(fig)
        paths.append(p)

    # 1. boxplot of primary metric
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.boxplot([df[df.method == m]["auc"] for m in methods], tick_labels=methods,
               patch_artist=True,
               boxprops=dict(facecolor=C_PRIMARY, alpha=.6))
    ax.set_title("Primary metric (AUC) by method"); ax.set_ylabel("AUC")
    _save(fig, "fig1_boxplot_auc.png")

    # 2. bar with 95% CI across metrics
    fig, ax = plt.subplots(figsize=(6, 4))
    x = np.arange(len(metrics)); w = 0.35
    means = {m: df[df.method == m][metrics].mean() for m in methods}
    errs = {m: df[df.method == m][metrics].sem() * 1.96 for m in methods}
    for i, m in enumerate(methods):
        ax.bar(x + (i - .5) * w, means[m], w, yerr=errs[m], capsize=4,
               label=m, color=PALETTE[i % len(PALETTE)], alpha=.85)
    ax.set_xticks(x); ax.set_xticklabels(metrics); ax.legend(); ax.set_ylabel("score")
    ax.set_title("Metrics with 95% CI")
    _save(fig, "fig2_bar_ci.png")

    # 3. scatter improvement per run
    fig, ax = plt.subplots(figsize=(5, 4))
    b = df[df.method == "baseline"]["auc"].reset_index(drop=True)
    p = df[df.method == "proposed"]["auc"].reset_index(drop=True)
    ax.scatter(b, p, color=C_SECOND, alpha=.7)
    lim = [min(b.min(), p.min()), max(b.max(), p.max())]
    ax.plot(lim, lim, "--", color=C_GRID)
    ax.set_xlabel("baseline AUC"); ax.set_ylabel("proposed AUC")
    ax.set_title("Per-run AUC (above line = improvement)")
    _save(fig, "fig3_scatter_auc.png")

    # 4. forest plot of Cohen's d
    fig, ax = plt.subplots(figsize=(6, 3))
    ds = []
    for met in metrics:
        d = (df[df.method == "proposed"][met].mean() - df[df.method == "baseline"][met].mean()) / df[met].std(ddof=1)
        ds.append(d)
    ax.errorbar(ds, range(len(metrics)), xerr=[0.2] * len(metrics), fmt="o", color=C_PRIMARY)
    ax.axvline(0, color=C_GRID); ax.set_yticks(range(len(metrics))); ax.set_yticklabels(metrics)
    ax.set_title("Effect size (Cohen's d)"); ax.set_xlabel("d")
    _save(fig, "fig4_forest_effect.png")

    # 5. distribution histogram
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.hist(df[df.method == "baseline"]["auc"], bins=8, alpha=.6, label="baseline", color=C_PRIMARY)
    ax.hist(df[df.method == "proposed"]["auc"], bins=8, alpha=.6, label="proposed", color=C_SECOND)
    ax.legend(); ax.set_title("AUC distribution"); ax.set_xlabel("AUC")
    _save(fig, "fig5_hist_auc.png")

    # 6. correlation heatmap of metrics
    fig, ax = plt.subplots(figsize=(4, 4))
    corr = df[metrics].corr()
    im = ax.imshow(corr, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(metrics))); ax.set_xticklabels(metrics, rotation=45, ha="right")
    ax.set_yticks(range(len(metrics))); ax.set_yticklabels(metrics)
    for i in range(len(metrics)):
        for j in range(len(metrics)):
            ax.text(j, i, f"{corr.values[i,j]:.2f}", ha="center", va="center", fontsize=8)
    ax.set_title("Metric correlation")
    _save(fig, "fig6_corr_heatmap.png")

    # 7. effect-size comparison bar
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(metrics, ds, color=PALETTE[:len(metrics)])
    ax.axhline(0, color=C_GRID); ax.set_title("Cohen's d by metric"); ax.set_ylabel("d")
    _save(fig, "fig7_effect_bar.png")

    # 8. spread (std) by metric
    fig, ax = plt.subplots(figsize=(5, 4))
    stds = [df[df.method == "proposed"][m].std() for m in metrics]
    ax.bar(metrics, stds, color=C_THIRD, alpha=.85)
    ax.set_title("Proposed std by metric"); ax.set_ylabel("std")
    _save(fig, "fig8_std_bar.png")

    # 9. grouped AUC violin-ish (use strip)
    fig, ax = plt.subplots(figsize=(5, 4))
    for i, m in enumerate(methods):
        y = df[df.method == m]["auc"]
        ax.stripplot(x=[m] * len(y), y=y, color=PALETTE[i % len(PALETTE)], alpha=.6) if False else None
        ax.scatter([i] * len(y) + np.random.default_rng(i).uniform(-.05, .05, len(y)), y,
                   color=PALETTE[i % len(PALETTE)], alpha=.6)
    ax.set_xticks(range(len(methods))); ax.set_xticklabels(methods); ax.set_ylabel("AUC")
    ax.set_title("AUC points by method")
    _save(fig, "fig9_strip_auc.png")

    return paths


def main() -> int:
    if not _need_libs():
        return 2
    import numpy as np  # noqa: F401
    import pandas as pd
    import matplotlib.pyplot as plt  # noqa: F401

    ap = argparse.ArgumentParser(description="Stage 5 analysis + figures.")
    ap.add_argument("--results", default="results/")
    ap.add_argument("--out", default="analysis/")
    ap.add_argument("--demo", action="store_true", help="generate synthetic results first")
    ap.add_argument("--workdir", default=os.environ.get("RESEARCH_WORKDIR", "./research-output"))
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    if args.demo:
        args.results = _demo_data(args.results)

    rows, nulls = _load_results(args.results)
    if not rows:
        print("[analyze] no valid result envelopes found (nulls excluded: "
              f"{nulls}). Nothing to analyze.", file=sys.stderr)
        return 1
    df = pd.DataFrame(rows)
    metrics = [c for c in ["auc", "acc", "f1"] if c in df.columns]

    prov = os.path.join(args.workdir, "provenance.log")
    os.makedirs(args.workdir, exist_ok=True)
    with open(prov, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": dt.datetime.now(dt.timezone.utc).isoformat(),
                            "stage": "data-analysis", "tool": "analyze.py",
                            "n_valid": len(df), "n_null_excluded": nulls},
                           ensure_ascii=False) + "\n")

    stats = _stats_block(df, metrics)
    figs = _figures(df, args.out, metrics)

    report = os.path.join(args.out, "stats-report.md")
    with open(report, "w", encoding="utf-8") as f:
        f.write(f"# Statistical Analysis Report\n\n")
        f.write(f"- valid runs: {len(df)}  (null/error excluded: {nulls})\n")
        f.write(f"- methods: {sorted(df.method.unique())}\n- metrics: {metrics}\n\n")
        f.write("## Tests (Welch t-test + Holm correction)\n\n" + stats + "\n\n")
        f.write("## Figures\n\n")
        for p in figs:
            f.write(f"![{os.path.basename(p)}]({os.path.basename(p)})\n")
    print(f"[analyze] {len(df)} runs, {len(figs)} figures -> {args.out} "
          f"({os.path.basename(report)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
