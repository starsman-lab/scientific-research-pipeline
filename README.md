# research-pipeline — 科研流水线 Harness

> 把"文献调研 → Idea 验证 → 实验设计 → 代码执行 → 数据分析 → 论文写作 → 质量把关"拆成 7 个受约束的 Stage，
> 每个 Stage 是一个 Sub-Agent，产物过门禁才能进下一环。对应 MVP 专家团"Phase 门禁 + 各司其职 + 反剧场"思路，
> 但用于科研而非工程。
>
> 设计参照：K-Dense-AI/scientific-agent-skills、PKU-YuanGroup/OpenAI4S、Imbad0202/academic-research-skills、Yuan1z0825/nature-skills。

## 核心理念

- **AI 是副驾驶，不是主驾驶**：自动化重复劳动，研究者做关键判断（人在回路）。
- **严禁编造**（R0）：一切结果来自真实执行；失败标 `null`，不补数。
- **溯源可审计**（R1）：每次外部调用记 provenance。
- **引用真实**（R2）：未确认标 `[CITATION NEEDED]`。
- **半自动**（R6）：常规阶段自动串联，仅实验设计 / 论文定稿 / 质量把关三处人工确认。

## 当前进度（v1.1.0）

| Stage | 技能 | 状态 | 门禁 |
|-------|------|------|------|
| 1 文献调研 | `literature-review` | ✅ 可用 | 自动 |
| 2 Idea 验证 | `idea-validation` | ✅ 可用 | 自动 |
| 3 实验设计 | `experiment-design` | ✅ 可用 | 人工确认（R6） |
| 4 代码执行 | `code-execution` | ✅ 可用 | 自动 |
| 5 数据分析 | `data-analysis` | ✅ 可用 | 自动 |
| 6 论文写作 | `paper-writing` | ✅ 可用 | 定稿人工确认（R6） |
| 7 质量把关 | `quality-gate` | ✅ 可用 | 人工确认（R6） |

地基文件：`Rule.md`（硬规则 R0–R10）、`docs/STAGE-CONTRACTS.md`（阶段契约）、`references/`（知识库脚手架）。

> **半自动（R6）**：常规阶段自动串联，仅实验设计方案、论文定稿、质量把关结论三处需研究者本人确认才放行。

## 安装

### A. WorkBuddy（本环境立即可用）

技能目录已按 WorkBuddy 规范组织（`skills/<name>/SKILL.md`）。两种加载方式：

- **用户级（跨所有工作区）**：将 `skills/` 下每个子目录复制到 `~/.workbuddy/skills/<name>/`。
- **项目级（仅本工作区）**：复制到 `<workspace>/.workbuddy/skills/<name>/`。

一键部署（PowerShell / Git Bash）：

```bash
# 用户级
cp -r skills/* "$HOME/.workbuddy/skills/"
```

部署后在本会话说"运行科研流水线 / 文献调研 / Idea 验证 / 实验设计 / 代码执行 / 数据分析 / 论文写作 / 质量把关"即可触发。

### B. Claude Code / Codex（可移植）

本仓库 `skills/` 符合 Agent Skills 标准（`SKILL.md` + frontmatter `name`/`description`）。直接复制整个 `skills/` 到对应 Agent 的 skills 目录，或整体作为 plugin 加载。

## 使用

主入口：触发 `research-pipeline` 技能，由主 Agent 按 `docs/STAGE-CONTRACTS.md` 串联各 Stage，传递 Handoff Envelope。
也可单独触发某个 Stage（如只做文献调研）。

共享规则根目录由环境变量 `RESEARCH_PIPELINE_ROOT` 指定（默认仓库根），所有 Stage 从中读取 `Rule.md` / `docs` / `references`。
最小工作目录由环境变量 `RESEARCH_WORKDIR` 指定（默认 `./research-output/`），所有产物落盘于此。

## 许可证

MIT（技能定义文本）。引用第三方技能时遵守各自许可证。
