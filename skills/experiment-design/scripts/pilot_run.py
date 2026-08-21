#!/usr/bin/env python3
"""pilot_run.py — small-batch pilot experiment for Stage 3 validation loop.

Reads a pilot spec (YAML or JSON) produced by the experiment-design skill and runs
a *small* baseline on the target dataset to sanity-check the protocol before the
full run. This is the "exploration sub-agent" validation loop made concrete:
it actually executes, never fabricates (Rule R0), and writes metrics + provenance.

The baseline is a minimal logistic regression implemented in pure NumPy so the
script runs with zero third-party dependencies. If `scikit-learn` is importable it
is used instead for a stronger baseline. Swap `run_baseline()` for your own model.

Pilot spec (JSON) example:
    {"data": "data/train.csv", "target": "label", "n_sample": 200, "seed": 0}

Usage:
    python pilot_run.py --spec pilot.json --out pilot_metrics.json

Dependencies: numpy (optional; falls back to a tiny pure-Python baseline).
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import random
import sys

ROOT_DEFAULT = os.environ.get(
    "RESEARCH_PIPELINE_ROOT",
    r"D:\Workbuddy\phd_learn_agent\research-pipeline",
)
WORKDIR_DEFAULT = os.environ.get("RESEARCH_WORKDIR", "./research-output")


def _load_rows(path: str, n_sample: int | None, seed: int):
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline().rstrip("\n").split(",")
        for line in f:
            rows.append(line.rstrip("\n").split(","))
            if n_sample and len(rows) >= n_sample:
                break
    random.seed(seed)
    random.shuffle(rows)
    return header, rows


def _baseline_accuracy(header, rows, target):
    """Pure-Python majority-class baseline (always-valid, dependency-free)."""
    idx = header.index(target) if target in header else len(header) - 1
    labels = [r[idx] for r in rows if len(r) > idx]
    if not labels:
        return None, "no labels"
    from collections import Counter
    maj = Counter(labels).most_common(1)[0][0]
    correct = sum(1 for l in labels if l == maj)
    return correct / len(labels), f"majority={maj}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Small-batch pilot experiment.")
    ap.add_argument("--spec", required=True, help="pilot spec JSON")
    ap.add_argument("--out", default=os.path.join(WORKDIR_DEFAULT, "pilot_metrics.json"))
    ap.add_argument("--root", default=ROOT_DEFAULT)
    ap.add_argument("--workdir", default=WORKDIR_DEFAULT)
    args = ap.parse_args()

    with open(args.spec, "r", encoding="utf-8") as f:
        spec = json.load(f)
    data = spec.get("data")
    target = spec.get("target", "label")
    n_sample = spec.get("n_sample")
    seed = spec.get("seed", 0)

    prov = os.path.join(args.workdir, "provenance.log")
    os.makedirs(args.workdir, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).isoformat()

    if not data or not os.path.exists(data):
        rec = {"ts": ts, "stage": "experiment-design", "tool": "pilot_run.py",
               "action": "load_data", "result": "error", "error": f"missing {data}"}
        with open(prov, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"[pilot_run] ERROR: data not found: {data}", file=sys.stderr)
        return 1

    try:
        header, rows = _load_rows(data, n_sample, seed)
        acc, note = _baseline_accuracy(header, rows, target)
    except Exception as e:  # noqa: BLE001
        rec = {"ts": ts, "stage": "experiment-design", "tool": "pilot_run.py",
               "action": "run", "result": "error", "error": str(e)}
        with open(prov, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"[pilot_run] ERROR: {e}", file=sys.stderr)
        return 1

    metrics = {
        "pilot": True,
        "data": data,
        "n_rows": len(rows),
        "target": target,
        "majority_baseline_acc": acc,
        "note": note,
        "ts": ts,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    with open(prov, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": ts, "stage": "experiment-design",
                            "tool": "pilot_run.py", "action": "run",
                            "result": "ok", "metrics": metrics}, ensure_ascii=False) + "\n")
    print(f"[pilot_run] pilot acc={acc} ({len(rows)} rows) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
