# CONTRIBUTING — 科研流水线技能规范

本仓库把"文献调研 → Idea 验证 → 实验设计 → 代码执行 → 数据分析 → 论文写作 → 质量把关"落地为一组**受约束的 Agent Skills Harness**。任何 Agent（WorkBuddy / Claude Code / Codex）加载 `skills/` 即可按固定流程跑科研，人在关键节点把关。

本文件说明"一个技能怎么写、怎么加、怎么验收"，确保多 Agent 不共享上下文时仍能各自产出合格产物。

---

## 1. 目录与寻址约定

| 路径 | 作用 |
|------|------|
| `skills/<skill-name>/SKILL.md` | 一个 Stage / 技能。目录名全局唯一 |
| `Rule.md` | 硬规则宪法（R0–R10），所有技能必须引用 |
| `docs/STAGE-CONTRACTS.md` | 7 阶段输入/输出/交接契约 + Handoff 模板 |
| `references/` | 知识库脚手架（论文卡模板、bibtex 库） |
| `OVERVIEW.md` / `README.md` / `README.en.md` | 仓库文档，状态需同步 |

- **共享根变量**：`RESEARCH_PIPELINE_ROOT`，默认仓库根。所有技能据此找 `Rule.md` / `docs/` / `references/`，部署到用户级技能目录后也能定位。
- **产物落盘变量**：`RESEARCH_WORKDIR`，默认 `./research-output/`。运行产物**不在仓库内**（见 `.gitignore` 的 `research-output/`）。

---

## 2. SKILL.md Frontmatter（必填字段）

```yaml
---
name: <skill-name>            # 小写连字符，必须与目录名完全一致（CI 校验）
description: "一句话英文描述，含动作动词，供 Agent 发现/触发"   # 必填
description_zh: "中文描述"     # 推荐
description_en: "English description"  # 推荐
version: 1.0.0                # 语义化版本
tags: [research, ...]         # 小写数组
display_name: "中文展示名"
visibility: public
---
```

字段约束：
- `name` == 目录名，否则 `validate.yml` 失败。
- `description` 必填、简洁、以动词开头（如"文献调研：拆成两步…"），这是 Agent 匹配触发的关键。
- `version` 语义化；只有破坏性接口改动（HANDOFF 字段 / 路径变更）才升主版本。

---

## 3. SKILL.md 正文结构（推荐）

按以下小节组织，便于下游 Stage 与主编排器解析：

1. **角色定位**：你是…，明确"不做什么"（如 quality-gate 只读不改稿）。
2. **输入**：必读文件路径 + 启动前校验（上游 HANDOFF、是否 `human_approved == true`、provenance 是否齐全）。
3. **职责与步骤**：编号动作，关键决策点写清。
4. **输出**：具体文件名（落 `$RESEARCH_WORKDIR/<stage>/`）。
5. **规则呼应**：显式引用 `Rule.md` 的 R 编号（见下表）。
6. **Handoff Envelope**：完成时写 `$RESEARCH_WORKDIR/<stage>/HANDOFF.md`，下游据此启动。

---

## 4. 跨阶段硬约束（R0–R10）

| 编号 | 规则 | 含义 |
|------|------|------|
| R0 | 学术诚信总纲 | 严禁编造数据 / 结论（最高优先级） |
| R1 | 溯源日志 | 每次外部检索写 `provenance.log`（JSONL），失败标 `null` 不补造 |
| R2 | 引用真实性 | 引用须真实，未确认标 `[CITATION NEEDED]` |
| R3 | 只读评审 | quality-gate 只读不改稿 |
| R4 | 阶段门禁 | 产物过门禁才进下一环 |
| R5 | 反剧场 | 无产物不出位（no-output-no-seat） |
| R6 | 人在回路 | 三处人工门禁：实验设计 / 论文定稿 / 质量把关 |
| R7 | 真实执行 | 代码须真实环境跑，禁止臆测 |
| R8 | 范围锁定 | 不擅自扩范围，未决项登记 `decisions/OPEN-DECISIONS.md` |
| R9 | 知识库优先 | 写作/检索优先取已入库 `references/` |
| R10 | 偏差上报 | 风险 / 阻塞显式回报，不静默跳过 |

技能正文须显式引用相关 R 编号，不能只口头承诺。

---

## 5. 新增一个 Stage

1. 在 `docs/STAGE-CONTRACTS.md` 增加该 Stage 行（状态先标 `📋 规划中`，含输入/输出/下游/门禁）。
2. 写 `skills/<name>/SKILL.md`（frontmatter + 第 3 节结构 + R 呼应）。
3. 在 `OVERVIEW.md` 交付表与状态表各加一行。
4. 在 `README.md` 与 `README.en.md` 进度表各加一行。
5. 本地跑一次 `.github/build_site.py` 确认能生成站点（顺便验证 frontmatter 可解析）。
6. 提 PR：CI（`validate.yml` + `pages.yml`）通过 + 人工 review 后合并。

---

## 6. 本地校验与站点预览

```bash
# 校验 frontmatter / 文件结构是否正常（与 CI validate.yml 同源逻辑）
python .github/build_site.py --check

# 生成本地预览站点到 site/，浏览器打开 site/index.html
python .github/build_site.py
```

> 说明：`validate.yml` 在 GitHub Actions 运行；本地无 act 时可直接跑 `.github/build_site.py --check` 复用同源校验，避免提交后才发现 frontmatter 错误。

---

## 7. 版本与发布

- `version` 随 SKILL.md 实质修改递增；破坏性接口（Handoff 字段 / 路径）升主版本，并在 PR 说明影响面。
- 仓库遵循语义化版本 + 半自动门禁；涉及 `Rule.md` R0–R10 的修改必须经人工确认，因其影响全部 Stage。
- 合并到 `main` 后，`pages.yml` 会自动把技能清单渲染为 GitHub Pages 站点。

提交前请确认：frontmatter 合法、`name` 与目录一致、地基文件（`Rule.md` / `docs/STAGE-CONTRACTS.md` / `README.md`）引用无误。

---

## 8. 配套 scripts/ 可执行脚本规范

本仓库与"纯提示词技能库"的关键区别在于：**每个 Stage skill 在 `skills/<name>/scripts/` 下挂真实可执行 Python，SKILL.md 末尾用「可执行脚本（scripts/）」段调用**。Agent 读提示词决策，脚本落地真实计算（参照 K-Dense-AI/scientific-agent-skills 的 `skill/scripts/` 模式）。

原则：
- **零依赖优先**：检索 / 解析 / 校验 / 路由类（fetch、novelty、citation、gate、pilot、run）只用标准库，任何环境可跑。
- **科学栈显式声明**：仅 `data-analysis/analyze.py` 依赖 `pandas numpy scipy matplotlib statsmodels`，SKILL.md 调用段须写清安装命令。
- **脚本是工具，提示词是调用说明**：执行逻辑写在 `scripts/`，不在 SKILL.md 正文堆代码。
- **脚本同样守规则**：写 `provenance.log`（R1），失败标 `null` 不伪造（R0），只读不改稿（R3）。

现有脚本：

| skill | 脚本 | 作用 | 依赖 |
|-------|------|------|------|
| literature-review | `scripts/fetch_papers.py` | arXiv 批量抓取 → 写论文卡 + bib | 标准库 |
| idea-validation | `scripts/check_novelty.py` | 近3年检索 + 文本重叠度筛查 | 标准库 |
| experiment-design | `scripts/pilot_run.py` | 小批量预实验 baseline 验证 | 标准库（可选 sklearn） |
| code-execution | `scripts/run_experiment.py` | 三路径真实执行 router | 标准库 |
| data-analysis | `scripts/analyze.py` | 合并+检验+Holm 校正+≥9图 | pandas/numpy/scipy/matplotlib/statsmodels |
| paper-writing | `scripts/check_citations.py` | `[CITATION NEEDED]` + bib 真实性校验 | 标准库 |
| quality-gate | `scripts/gate_check.py` | 6维评分卡 + 诚信门禁初筛 | 标准库 |

新增 Stage 时，若该阶段含可机械化执行的逻辑（检索、统计、校验、绘图、路由），应同步写 `scripts/` 并挂接到 SKILL.md。
