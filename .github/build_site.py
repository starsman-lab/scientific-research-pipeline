#!/usr/bin/env python3
"""Build a static GitHub Pages site listing all research-pipeline skills.

Self-contained: no third-party dependencies. Run in CI and locally:
    python .github/build_site.py            # generate ./site/index.html
    python .github/build_site.py --check     # validate skills, no output

Reads:
    skills/*/SKILL.md          (frontmatter)
    Rule.md                    (R0-R10 headings)
    docs/STAGE-CONTRACTS.md    (7-stage status table)
"""
import os
import re
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
REPO_URL = "https://github.com/starsman-lab/scientific-research-pipeline"


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
            val = [v.strip().strip('"').strip("'") for v in inner.split(",") if v.strip()] if inner else []
        else:
            val = val.strip().strip('"').strip("'")
        fm[key] = val
    return fm


def parse_stages(path):
    stages = []
    if not os.path.exists(path):
        return stages
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*`(.+?)`\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", line)
        if m and m.group(1).isdigit():
            stages.append({
                "num": m.group(1),
                "name": m.group(2).strip(),
                "skill": m.group(3).strip(),
                "status": m.group(4).strip(),
                "gate": m.group(5).strip(),
            })
    return stages


def parse_rules(path):
    rules = []
    if not os.path.exists(path):
        return rules
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^##\s+(R\d)\s+(.+)$", line)
        if m:
            rules.append({"id": m.group(1), "title": m.group(2).strip()})
    return rules


def collect_skills():
    skills = []
    for sk in sorted(glob.glob(os.path.join(REPO, "skills", "*", "SKILL.md"))):
        fm = parse_frontmatter(open(sk, encoding="utf-8").read())
        if "name" not in fm:
            continue
        rel = os.path.relpath(sk, REPO).replace("\\", "/")
        skills.append({
            "name": fm.get("name"),
            "display": fm.get("display_name", fm.get("name")),
            "desc": fm.get("description", ""),
            "desc_zh": fm.get("description_zh", ""),
            "desc_en": fm.get("description_en", ""),
            "version": fm.get("version", ""),
            "tags": fm.get("tags", []) if isinstance(fm.get("tags"), list) else [],
            "path": rel,
            "url": f"{REPO_URL}/blob/main/{rel}",
        })
    return skills


def esc(s):
    return (s if isinstance(s, str) else str(s))


def render(skills, stages, rules):
    stage_cards = "\n".join(
        f'''      <div class="stage">
        <div class="stage-num">{esc(s['num'])}</div>
        <div class="stage-body">
          <div class="stage-name">{esc(s['name'])} <code>{esc(s['skill'])}</code></div>
          <div class="stage-meta"><span class="badge">{esc(s['status'])}</span> <span class="gate">门禁: {esc(s['gate'])}</span></div>
        </div>
      </div>''' for s in stages
    )

    skill_rows = "\n".join(
        f'''      <tr>
        <td><a href="{s['url']}"><code>{esc(s['name'])}</code></a></td>
        <td>{esc(s['display'])}</td>
        <td class="desc">{esc(s['desc'])}</td>
        <td>{" ".join(f'<span class="tag">{esc(t)}</span>' for t in s['tags'])}</td>
        <td><span class="ver">v{esc(s['version'])}</span></td>
      </tr>''' for s in skills
    )

    rule_items = "\n".join(
        f'      <li><b>{esc(r["id"])}</b> {esc(r["title"])}</li>' for r in rules
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>科研流水线 Harness · 技能清单</title>
<style>
  :root {{ --bg:#fff; --fg:#1a1a1e; --muted:#5b6470; --line:#e3e6ea; --brand:#1f6feb; --brand2:#0b3d91; --chip:#eef2f7; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue","PingFang SC","Microsoft YaHei",sans-serif; color:var(--fg); background:var(--bg); line-height:1.6; }}
  header {{ background:linear-gradient(135deg,var(--brand2),var(--brand)); color:#fff; padding:42px 20px; }}
  header .wrap {{ max-width:960px; margin:0 auto; }}
  header h1 {{ margin:0 0 8px; font-size:28px; }}
  header p {{ margin:0; opacity:.92; }}
  header a {{ color:#cfe3ff; }}
  main {{ max-width:960px; margin:0 auto; padding:28px 20px 60px; }}
  h2 {{ font-size:20px; margin:38px 0 14px; padding-bottom:6px; border-bottom:1px solid var(--line); }}
  .stages {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:12px; }}
  .stage {{ display:flex; gap:12px; border:1px solid var(--line); border-radius:10px; padding:12px 14px; }}
  .stage-num {{ flex:0 0 30px; height:30px; width:30px; border-radius:50%; background:var(--brand); color:#fff; font-weight:700; display:flex; align-items:center; justify-content:center; }}
  .stage-name code {{ background:var(--chip); padding:1px 6px; border-radius:5px; font-size:12px; }}
  .stage-meta {{ margin-top:4px; font-size:12.5px; color:var(--muted); }}
  .badge {{ background:#e7f6ec; color:#1a7f43; border-radius:5px; padding:1px 7px; }}
  .gate {{ color:var(--muted); }}
  table {{ width:100%; border-collapse:collapse; font-size:14px; }}
  th, td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--line); vertical-align:top; }}
  th {{ background:var(--chip); font-size:13px; }}
  td.desc {{ color:var(--muted); max-width:420px; }}
  code {{ font-family:"SFMono-Regular",Consolas,Menlo,monospace; }}
  .tag {{ display:inline-block; background:var(--chip); color:var(--muted); border-radius:5px; padding:1px 7px; margin:1px 3px 1px 0; font-size:11.5px; }}
  .ver {{ color:var(--brand); font-weight:600; font-size:12px; }}
  ul.rules {{ columns:2; column-gap:26px; padding-left:18px; font-size:13.5px; }}
  ul.rules li {{ margin-bottom:6px; break-inside:avoid; }}
  footer {{ max-width:960px; margin:0 auto; padding:18px 20px 50px; color:var(--muted); font-size:12.5px; border-top:1px solid var(--line); }}
  footer a {{ color:var(--brand); }}
</style>
</head>
<body>
<header><div class="wrap">
  <h1>科研流水线 Harness</h1>
  <p>7 阶段受约束的 Agent Skills：文献调研 → Idea 验证 → 实验设计 → 代码执行 → 数据分析 → 论文写作 → 质量把关。人在回路，严禁编造。</p>
  <p>仓库：<a href="{REPO_URL}">{REPO_URL}</a></p>
</div></header>
<main>
  <h2>流水线 7 阶段</h2>
  <div class="stages">
{stage_cards}
  </div>

  <h2>技能清单（{len(skills)} 个）</h2>
  <table>
    <thead><tr><th>技能</th><th>展示名</th><th>描述</th><th>标签</th><th>版本</th></tr></thead>
    <tbody>
{skill_rows}
    </tbody>
  </table>

  <h2>硬规则宪法（R0–R10）</h2>
  <ul class="rules">
{rule_items}
  </ul>

  <h2>相关文档</h2>
  <p>
    <a href="{REPO_URL}/blob/main/Rule.md">Rule.md</a> ·
    <a href="{REPO_URL}/blob/main/docs/STAGE-CONTRACTS.md">STAGE-CONTRACTS.md</a> ·
    <a href="{REPO_URL}/blob/main/CONTRIBUTING.md">CONTRIBUTING.md</a> ·
    <a href="{REPO_URL}/blob/main/README.md">README</a> ·
    <a href="{REPO_URL}/blob/main/README.en.md">README.en</a>
  </p>
</main>
<footer>
  本站点由 <code>.github/workflows/pages.yml</code> 自动生成自各技能 SKILL.md frontmatter，每次推送 main 自动更新。
</footer>
</body>
</html>
"""


def main():
    check_only = "--check" in sys.argv
    skills = collect_skills()
    stages = parse_stages(os.path.join(REPO, "docs", "STAGE-CONTRACTS.md"))
    rules = parse_rules(os.path.join(REPO, "Rule.md"))

    # validation (also used by CI gate)
    errors = []
    seen = set()
    for s in skills:
        if s["name"] in seen:
            errors.append(f"duplicate skill name: {s['name']}")
        seen.add(s["name"])
        dir_name = os.path.dirname(s["path"]).split("/")[-1]
        if s["name"] != dir_name:
            errors.append(f"name '{s['name']}' != dir '{dir_name}'")
        if not s["desc"]:
            errors.append(f"missing description: {s['name']}")

    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        if check_only:
            sys.exit(1)
    else:
        print(f"check OK: {len(skills)} skills, {len(stages)} stages, {len(rules)} rules")

    if check_only:
        sys.exit(0)

    out_dir = os.path.join(REPO, "site")
    os.makedirs(out_dir, exist_ok=True)
    html_path = os.path.join(out_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(render(skills, stages, rules))
    print(f"wrote {html_path} ({len(skills)} skills)")


if __name__ == "__main__":
    main()
