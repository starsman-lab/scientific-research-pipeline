# research-pipeline — A Research Pipeline Harness

> Break the loop "literature review → idea validation → experiment design → code execution → data analysis → paper writing → peer review → quality gate" into 8 constrained stages.
> Each stage is a sub-agent; its artifact must pass a gate before the next stage starts. It reuses the MVP expert-team idea of "phase gates + clear division of labor + no-theater", but for research instead of engineering.
>
> Design references: K-Dense-AI/scientific-agent-skills, PKU-YuanGroup/OpenAI4S, Imbad0202/academic-research-skills, Yuan1z0825/nature-skills.

📦 GitHub: https://github.com/starsman-lab/scientific-research-pipeline · 中文版: [README.md](README.md)

## Core Ideas

- **AI is co-pilot, not pilot**: automate repetitive work; the researcher makes the key judgments (human-in-the-loop).
- **No fabrication (R0)**: every result comes from real execution; failures are marked `null`, never backfilled.
- **Auditable provenance (R1)**: every external call is logged to a provenance ledger.
- **Real citations (R2)**: mark anything unverified as `[CITATION NEEDED]`.
- **Semi-automatic (R6)**: routine stages chain automatically; only experiment design, paper finalization, and the quality-gate conclusion need the researcher's explicit confirmation.

## Status (v1.3.0)

| Stage | Skill | Status | Gate |
|-------|-------|--------|------|
| 1 Literature review | `literature-review` | ✅ ready | auto |
| 2 Idea validation | `idea-validation` | ✅ ready | auto |
| 3 Experiment design | `experiment-design` | ✅ ready | human confirm (R6) |
| 4 Code execution | `code-execution` | ✅ ready | auto |
| 5 Data analysis | `data-analysis` | ✅ ready | auto |
| 6 Paper writing | `paper-writing` | ✅ ready | human confirm on finalize (R6) |
| 7 Peer review | `peer-review` | ✅ ready | auto (revision loop on Major) |
| 8 Quality gate | `quality-gate` | ✅ ready | human confirm (R6) |

> **v1.3.0 enhancements (inspired by 4 open-source research-agent repos)**
> - **Argument contract / proposal-first**: before drafting, `paper-writing` writes `argument-contract.md` (thesis + ≤3 contributions each pinned to evidence + mechanism hypothesis + threats to validity), then drafts (nature-skills).
> - **review → revise loop**: new `peer-review` stage simulates 2–3 reviewers producing Major/Minor; a Major triggers a fallback to `paper-writing` for revision (academic-research-skills).
> - **Citation strictness**: literature fetch scores relevance (only high/medium enter the library); quality gate adds a ref-verifier (flags `INCOMPLETE_REF`) + stats consistency (manuscript vs stats-report), directly catching "present-but-irrelevant / incomplete" citations (nature-ref-verifier / nature-statistics).
> - **line-pinned / candidate hypothesis**: citations bind to concrete sources; idea validation writes a falsifiable `candidate` hypothesis first (K-Dense-AI).
> - **Ledger-first provenance**: every execution appends to the provenance ledger (OpenAI4S).

Foundation files: `Rule.md` (hard rules R0–R10), `docs/STAGE-CONTRACTS.md` (stage contracts), `references/` (knowledge-base scaffold).

> **Semi-automatic (R6)**: routine stages chain automatically; only the experiment-design plan, the paper finalization, and the quality-gate conclusion require the researcher's own confirmation to proceed.

## Install

### A. WorkBuddy (usable in this environment immediately)

The skill directory follows the WorkBuddy convention (`skills/<name>/SKILL.md`). Two ways to load:

- **User-level (all workspaces)**: copy each sub-directory under `skills/` to `~/.workbuddy/skills/<name>/`.
- **Project-level (this workspace only)**: copy to `<workspace>/.workbuddy/skills/<name>/`.

One-shot deploy (PowerShell / Git Bash):

```bash
# user-level
cp -r skills/* "$HOME/.workbuddy/skills/"
```

After deploy, say "run research pipeline / literature review / idea validation / experiment design / code execution / data analysis / paper writing / peer review / quality gate" in this session to trigger.

### B. Claude Code / Codex (portable)

This repo's `skills/` follows the Agent Skills standard (`SKILL.md` + frontmatter `name`/`description`). Copy the whole `skills/` into the target agent's skills directory, or load it as a plugin.

## Usage

Entry point: trigger the `research-pipeline` skill; the main agent chains stages per `docs/STAGE-CONTRACTS.md` and passes a Handoff Envelope between them. You can also trigger a single stage (e.g. only literature review).

The shared rule root is set by env var `RESEARCH_PIPELINE_ROOT` (default repo root); every stage reads `Rule.md` / `docs` / `references` from it. The minimal working directory is set by `RESEARCH_WORKDIR` (default `./research-output/`); all artifacts land there.

## License

MIT (for the skill definition text). Respect each third-party skill's own license when reusing.
