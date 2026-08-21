#!/usr/bin/env python3
"""Build the research-pipeline GitHub Pages site (English only, polished UI).

Self-contained: no third-party dependencies. Reads from the repo root and writes
``site/index.html``.  Use ``--check`` to validate skill structure without writing.

Run locally:  python .github/build_site.py [--check]
"""
import os
import re
import sys
import html
import glob
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

REPO_URL = "https://github.com/starsman-lab/scientific-research-pipeline"
RAW = f"{REPO_URL}/blob/main"

# English-only copy for the interface.
SITE_TITLE = "Research Pipeline Harness"
SITE_SUBTITLE = (
    "Seven stage-gated agent skills for reproducible, auditable research. "
    "Human-in-the-loop, no fabrication, fully provenance-tracked."
)
SECTIONS = {
    "pipeline": "The Pipeline",
    "skills": "Skills",
    "rules": "Hard Rules",
    "docs": "Documentation",
    "footer": "A portable agent-skills harness for WorkBuddy, Claude Code and Codex.",
}

# Stage number -> English label.
STAGE_NAMES = {
    "1": "Literature Review",
    "2": "Idea Validation",
    "3": "Experiment Design",
    "4": "Code Execution",
    "5": "Data Analysis",
    "6": "Paper Writing",
    "7": "Quality Gate",
}

# Rule id -> English title (mirrors Rule.md R0-R10).
RULE_TITLES = {
    "R0": "Academic Integrity (top priority)",
    "R1": "Provenance Logging",
    "R2": "Citation Authenticity",
    "R3": "Read-Only Review",
    "R4": "Stage Gate",
    "R5": "No-Output-No-Seat (anti-theater)",
    "R6": "Human-in-the-Loop",
    "R7": "Real Execution",
    "R8": "Scope Lock",
    "R9": "KB-First",
    "R10": "Speak-Up (deviation reporting)",
}


# --------------------------------------------------------------------------- #
# Parsers
# --------------------------------------------------------------------------- #
def parse_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            val = (
                [v.strip().strip('"').strip("'") for v in inner.split(",") if v.strip()]
                if inner
                else []
            )
        else:
            val = val.strip().strip('"').strip("'")
        fm[key] = val
    return fm


def parse_stages(path):
    stages = []
    if not os.path.exists(path):
        return stages
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(
                r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*`(.+?)`\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|",
                line,
            )
            if m and m.group(1).isdigit():
                gate = m.group(5)
                stages.append(
                    {
                        "num": m.group(1),
                        "name_zh": m.group(2).strip(),
                        "skill": m.group(3).strip(),
                        "status": m.group(4).strip(),
                        "gate": ("✅" in gate or "是" in gate),
                    }
                )
    return stages


def parse_rules(path):
    rules = []
    if not os.path.exists(path):
        return rules
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"^##\s+(R\d)\s+(.+)$", line)
            if m:
                rid = m.group(1)
                rules.append({"id": rid, "title": RULE_TITLES.get(rid, m.group(2).strip())})
    return rules


def collect_skills():
    skills = []
    for sk in sorted(glob.glob(os.path.join(REPO, "skills", "*", "SKILL.md"))):
        fm = parse_frontmatter(open(sk, encoding="utf-8").read())
        if "name" not in fm:
            continue
        rel = os.path.relpath(sk, REPO).replace("\\", "/")
        desc = fm.get("description_en") or fm.get("description", "")
        skills.append(
            {
                "name": fm.get("name"),
                "desc": desc,
                "version": fm.get("version", ""),
                "tags": fm.get("tags", []),
                "path": rel,
                "url": f"{RAW}/{rel}",
            }
        )
    return skills


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def check():
    skills = collect_skills()
    stages = parse_stages(os.path.join(REPO, "docs", "STAGE-CONTRACTS.md"))
    rules = parse_rules(os.path.join(REPO, "Rule.md"))
    errors = []

    names = [s["name"] for s in skills]
    for s in skills:
        if not s["desc"]:
            errors.append(f"skill {s['name']}: missing 'description'/'description_en'")
    if len(names) != len(set(names)):
        errors.append(f"duplicate skill names: {names}")

    for f in ("Rule.md", "docs/STAGE-CONTRACTS.md", "README.md"):
        if not os.path.exists(os.path.join(REPO, f)):
            errors.append(f"missing base file: {f}")

    if errors:
        for e in errors:
            print("  ERR", e, file=sys.stderr)
        sys.exit(1)
    print(f"check OK: {len(skills)} skills, {len(stages)} stages, {len(rules)} rules")
    return skills, stages, rules


# --------------------------------------------------------------------------- #
# Render
# --------------------------------------------------------------------------- #
def render(skills, stages, rules):
    def esc(s):
        return html.escape(str(s))

    stage_cards = []
    for st in stages:
        label = STAGE_NAMES.get(st["num"], st["skill"])
        gate_badge = (
            '<span class="gate">human gate</span>' if st["gate"] else ""
        )
        stage_cards.append(
            f'<div class="stage{" gate-stage" if st["gate"] else ""}">'
            f'<div class="stage-num">{esc(st["num"])}</div>'
            f'<div class="stage-body"><div class="stage-name">{esc(label)}'
            f' <code>{esc(st["skill"])}</code></div>{gate_badge}</div>'
            f"</div>"
        )
    pipeline_html = '<div class="pipeline">' + "".join(stage_cards) + "</div>"

    skill_cards = []
    for s in skills:
        chips = "".join(
            f'<span class="chip">{esc(t)}</span>' for t in (s["tags"] or [])
        )
        skill_cards.append(
            f'<a class="card" href="{esc(s["url"])}" target="_blank" rel="noopener">'
            f'<div class="card-top"><code class="card-name">{esc(s["name"])}</code>'
            f'<span class="ver">v{esc(s["version"])}</span></div>'
            f'<p class="card-desc">{esc(s["desc"])}</p>'
            f'<div class="chips">{chips}</div>'
            f'<span class="card-link">View SKILL.md →</span>'
            f"</a>"
        )
    skills_html = '<div class="grid">' + "".join(skill_cards) + "</div>"

    rule_cards = []
    for r in rules:
        rule_cards.append(
            f'<div class="rule"><span class="rid">{esc(r["id"])}</span>'
            f'<span class="rtitle">{esc(r["title"])}</span></div>'
        )
    rules_html = '<div class="rules">' + "".join(rule_cards) + "</div>"

    docs_html = "".join(
        f'<a class="doc" href="{esc(f"{RAW}/{p}")}" target="_blank" rel="noopener">'
        f'<code>{esc(p)}</code><span>→</span></a>'
        for p in ("Rule.md", "docs/STAGE-CONTRACTS.md", "CONTRIBUTING.md", "README.md")
    )

    year = datetime.date.today().year

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(SITE_TITLE)} · Skills</title>
<meta name="description" content="{esc(SITE_SUBTITLE)}">
<style>
  :root {{
    --bg:#0b1020; --panel:#121a30; --panel2:#16203c; --fg:#e8edf7; --muted:#9aa7c2;
    --line:#243150; --brand:#6ea8fe; --brand2:#a78bfa; --accent:#34d399; --warn:#fbbf24;
    --radius:16px; --shadow:0 10px 30px rgba(0,0,0,.35);
  }}
  @media (prefers-color-scheme: light) {{
    :root {{ --bg:#f6f8fc; --panel:#ffffff; --panel2:#f1f4fa; --fg:#15203a;
      --muted:#5b6479; --line:#e2e8f2; --brand:#2563eb; --brand2:#7c3aed;
      --accent:#059669; --warn:#b45309; --shadow:0 10px 30px rgba(20,40,90,.10); }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,
    "Helvetica Neue","PingFang SC",sans-serif; color:var(--fg); background:var(--bg);
    line-height:1.65; -webkit-font-smoothing:antialiased; }}
  a {{ color:inherit; text-decoration:none; }}
  .wrap {{ max-width:1040px; margin:0 auto; padding:0 22px; }}
  header {{ position:relative; overflow:hidden; padding:72px 0 56px;
    background:radial-gradient(1200px 500px at 15% -20%, rgba(110,168,254,.25), transparent 60%),
              radial-gradient(1000px 500px at 100% 0%, rgba(167,139,250,.22), transparent 55%);
    border-bottom:1px solid var(--line); }}
  .badges {{ display:flex; gap:8px; flex-wrap:wrap; margin:18px 0 14px; }}
  .badge {{ font-size:12.5px; padding:5px 11px; border-radius:999px;
    background:var(--panel2); border:1px solid var(--line); color:var(--muted); }}
  .badge b {{ color:var(--brand); font-weight:600; }}
  h1 {{ margin:0; font-size:38px; letter-spacing:-.02em;
    background:linear-gradient(90deg,var(--brand),var(--brand2));
    -webkit-background-clip:text; background-clip:text; color:transparent; }}
  header p {{ margin:14px 0 0; max-width:680px; color:var(--muted); font-size:16px; }}
  .gh {{ display:inline-flex; align-items:center; gap:8px; margin-top:22px;
    padding:10px 16px; border-radius:10px; font-weight:600; font-size:14.5px;
    background:linear-gradient(90deg,var(--brand),var(--brand2)); color:#fff;
    box-shadow:var(--shadow); }}
  section {{ padding:46px 0; border-bottom:1px solid var(--line); }}
  h2 {{ font-size:22px; margin:0 0 22px; display:flex; align-items:center; gap:10px; }}
  h2::before {{ content:""; width:6px; height:22px; border-radius:3px;
    background:linear-gradient(var(--brand),var(--brand2)); display:inline-block; }}
  /* pipeline */
  .pipeline {{ display:flex; flex-wrap:wrap; gap:14px; align-items:stretch; }}
  .stage {{ flex:1 1 200px; display:flex; gap:12px; align-items:center;
    background:var(--panel); border:1px solid var(--line); border-radius:var(--radius);
    padding:16px; transition:.2s; }}
  .stage:hover {{ transform:translateY(-3px); border-color:var(--brand); box-shadow:var(--shadow); }}
  .stage.gate-stage {{ border-color:rgba(251,191,36,.45);
    background:linear-gradient(180deg, rgba(251,191,36,.07), transparent); }}
  .stage-num {{ font-weight:800; font-size:20px; color:var(--brand);
    min-width:30px; text-align:center; }}
  .stage-name {{ font-weight:600; font-size:15px; }}
  .stage-name code {{ display:block; font-size:12px; color:var(--muted); margin-top:2px; }}
  .gate {{ display:inline-block; margin-top:6px; font-size:11px; padding:2px 8px;
    border-radius:999px; background:rgba(251,191,36,.16); color:var(--warn);
    border:1px solid rgba(251,191,36,.4); }}
  /* skill grid */
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:16px; }}
  .card {{ display:flex; flex-direction:column; gap:10px; background:var(--panel);
    border:1px solid var(--line); border-radius:var(--radius); padding:18px;
    transition:.2s; }}
  .card:hover {{ transform:translateY(-4px); border-color:var(--brand);
    box-shadow:var(--shadow); }}
  .card-top {{ display:flex; justify-content:space-between; align-items:center; }}
  .card-name {{ font-size:15px; font-weight:700; color:var(--brand); }}
  .ver {{ font-size:11.5px; color:var(--muted); border:1px solid var(--line);
    padding:2px 8px; border-radius:999px; }}
  .card-desc {{ margin:0; font-size:13.5px; color:var(--muted); flex:1; }}
  .chips {{ display:flex; flex-wrap:wrap; gap:6px; }}
  .chip {{ font-size:11px; color:var(--brand2); background:var(--panel2);
    border:1px solid var(--line); padding:2px 8px; border-radius:999px; }}
  .card-link {{ font-size:12.5px; color:var(--brand); font-weight:600; }}
  /* rules */
  .rules {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:12px; }}
  .rule {{ display:flex; align-items:center; gap:12px; background:var(--panel);
    border:1px solid var(--line); border-radius:12px; padding:12px 14px; }}
  .rid {{ font-weight:800; color:var(--accent); font-size:14px;
    min-width:34px; text-align:center; }}
  .rtitle {{ font-size:13.5px; }}
  /* docs */
  .docs {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:12px; }}
  .doc {{ display:flex; justify-content:space-between; align-items:center;
    background:var(--panel); border:1px solid var(--line); border-radius:12px;
    padding:14px 16px; transition:.2s; }}
  .doc:hover {{ border-color:var(--brand); transform:translateY(-2px); }}
  .doc code {{ color:var(--brand); font-size:14px; }}
  .doc span {{ color:var(--muted); }}
  footer {{ padding:30px 0 50px; color:var(--muted); font-size:13px; text-align:center; }}
  footer a {{ color:var(--brand); }}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <h1>{esc(SITE_TITLE)}</h1>
    <p>{esc(SITE_SUBTITLE)}</p>
    <div class="badges">
      <span class="badge"><b>{len(stages)}</b> stages</span>
      <span class="badge"><b>{len(skills)}</b> skills</span>
      <span class="badge"><b>3</b> human gates</span>
      <span class="badge">semi-automatic</span>
      <span class="badge">MIT</span>
    </div>
    <a class="gh" href="{esc(REPO_URL)}" target="_blank" rel="noopener">★ View on GitHub</a>
  </div>
</header>

<main class="wrap">
  <section>
    <h2>{esc(SECTIONS["pipeline"])}</h2>
    {pipeline_html}
  </section>

  <section>
    <h2>{esc(SECTIONS["skills"])}</h2>
    {skills_html}
  </section>

  <section>
    <h2>{esc(SECTIONS["rules"])}</h2>
    {rules_html}
  </section>

  <section>
    <h2>{esc(SECTIONS["docs"])}</h2>
    <div class="docs">{docs_html}</div>
  </section>
</main>

<footer class="wrap">
  {esc(SECTIONS["footer"])} · © {year} <a href="{esc(REPO_URL)}">starsman-lab</a>
</footer>
</body>
</html>"""


# --------------------------------------------------------------------------- #
def main():
    if "--check" in sys.argv:
        check()
        return
    skills, stages, rules = check()
    out = os.path.join(REPO, "site", "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(render(skills, stages, rules))
    print(f"wrote {out} ({len(skills)} skills)")


if __name__ == "__main__":
    main()
