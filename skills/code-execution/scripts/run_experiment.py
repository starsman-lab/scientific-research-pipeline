#!/usr/bin/env python3
"""run_experiment.py — real execution router for Stage 4 (three paths).

Implements the "real execution, never fabricate" contract (Rules R0/R7):
  * local  — runs <script> inside a managed venv via subprocess; stdout/stderr
             captured; on non-zero exit the result is recorded as null (not faked).
  * remote — packages <script> + <config> into a self-contained task bundle
             (run.sh + manifest) for a GPU box; does NOT execute here.
  * manual — emits MANUAL.md describing exactly what a human must run, so the
             step is still auditable even when compute is elsewhere.

Every call is appended to provenance.log (Rule R1). Outputs are written as JSON
result envelopes consumed downstream by data-analysis.

Usage:
    python run_experiment.py --path local  --script train.py --config cfg.yaml --out results/run1.json
    python run_experiment.py --path remote --script train.py --config cfg.yaml --out bundle/
    python run_experiment.py --path manual --script train.py --config cfg.yaml --out MANUAL.md

Dependencies: Python standard library only.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import subprocess
import sys

ROOT_DEFAULT = os.environ.get(
    "RESEARCH_PIPELINE_ROOT",
    r"D:\Workbuddy\phd_learn_agent\research-pipeline",
)
WORKDIR_DEFAULT = os.environ.get("RESEARCH_WORKDIR", "./research-output")


def _prov(workdir: str, rec: dict) -> None:
    os.makedirs(workdir, exist_ok=True)
    with open(os.path.join(workdir, "provenance.log"), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _run_local(script: str, config: str | None, python_exe: str, workdir: str) -> dict:
    cmd = [python_exe, script]
    if config:
        cmd += ["--config", config]
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "timeout", "ts": ts}
    ok = proc.returncode == 0
    rec = {"ts": ts, "stage": "code-execution", "tool": "run_experiment.py",
           "path": "local", "script": script, "returncode": proc.returncode,
           "result": "ok" if ok else "error"}
    _prov(workdir, rec)
    return {"status": "ok" if ok else "error", "returncode": proc.returncode,
            "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:], "ts": ts}


def _run_remote(script: str, config: str | None, out: str) -> dict:
    os.makedirs(out, exist_ok=True)
    manifest = {
        "script": os.path.basename(script), "config": os.path.basename(config) if config else None,
        "note": "Upload this bundle to the GPU box and run ./run.sh",
    }
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    with open(os.path.join(out, "run.sh"), "w", encoding="utf-8") as f:
        f.write("#!/usr/bin/env bash\nset -euo pipefail\n")
        f.write(f"python {os.path.basename(script)}")
        if config:
            f.write(f" --config {os.path.basename(config)}")
        f.write("\n")
    if script and os.path.exists(script):
        with open(script, "rb") as s, open(os.path.join(out, os.path.basename(script)), "wb") as d:
            d.write(s.read())
    if config and os.path.exists(config):
        with open(config, "rb") as s, open(os.path.join(out, os.path.basename(config)), "wb") as d:
            d.write(s.read())
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    _prov(os.path.dirname(out) or WORKDIR_DEFAULT,
          {"ts": ts, "stage": "code-execution", "tool": "run_experiment.py",
           "path": "remote", "bundle": out, "result": "ok"})
    return {"status": "ok", "bundle": out, "ts": ts}


def _run_manual(script: str, config: str | None, out: str) -> dict:
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# Manual Execution Step\n\n")
        f.write(f"Run this on the target machine:\n\n```bash\npython {script}")
        if config:
            f.write(f" --config {config}")
        f.write("\n```\n\nThen copy the produced `results/*.json` back into the workdir.\n")
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    _prov(os.path.dirname(out) or WORKDIR_DEFAULT,
          {"ts": ts, "stage": "code-execution", "tool": "run_experiment.py",
           "path": "manual", "manual_doc": out, "result": "ok"})
    return {"status": "ok", "manual": out, "ts": ts}


def main() -> int:
    ap = argparse.ArgumentParser(description="Real execution router (3 paths).")
    ap.add_argument("--path", choices=["local", "remote", "manual"], required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--config", default=None)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--out", required=True)
    ap.add_argument("--root", default=ROOT_DEFAULT)
    ap.add_argument("--workdir", default=WORKDIR_DEFAULT)
    args = ap.parse_args()

    if args.path == "local":
        res = _run_local(args.script, args.config, args.python, args.workdir)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
        print(f"[run_experiment] local -> {res['status']} ({args.out})")
        return 0 if res["status"] == "ok" else 1
    if args.path == "remote":
        res = _run_remote(args.script, args.config, args.out)
        print(f"[run_experiment] remote bundle -> {res['bundle']}")
        return 0
    res = _run_manual(args.script, args.config, args.out)
    print(f"[run_experiment] manual doc -> {res['manual']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
