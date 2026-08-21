---
name: paper-writing
description: "论文写作：基于全部上游产物与目标会议模板搭骨架，模仿参考论文结构与节奏润色，引用须来自知识库或联网验证(R2)，未确认标[CITATION NEEDED]，定稿需人工门禁(R6)。"
description_zh: "论文写作（骨架+模仿润色+真实引用）"
description_en: "Paper writing (skeleton + mimic polish + real citations)"
version: 1.0.0
tags: [research, writing, manuscript, latex, citation]
display_name: "论文写作"
visibility: public
---

# 论文写作（paper-writing）

你把"把证据写成可投稿的稿子"模块化。本阶段是**作者**，所有数字来自真实产物，所有引用可核验；质量把关（quality-gate）才会只读评审（R3）。

## 输入

- 上游全部产物：`lit-review/`、`idea-validation/`、`experiment-design/`、`code-execution/`、`data-analysis/`。
- 目标会议/期刊 LaTeX 模板（用户提供路径，或联网取官方模板）。无模板则用 Markdown 等价结构。

## 工作流程

1. **搭骨架**：按目标模板章节（Abstract / Intro / Related / Method / Exp / Conclusion），先填占位与来源标注（每段注明数据来自哪个上游产物）。
2. **填内容**：
   - Intro：从 `gap-analysis.md` 引出动机，从 `idea-validation/report.md` 引出贡献（3 条 bullet，不夸大）。
   - Related：从 `references/papers/*.md` 归纳，不堆砌。
   - Method：从 `plan.md` 提炼，公式用真实符号，不写未实现的模块。
   - Exp：从 `stats-report.md` + `figures/*.png` 搬数据，**数字必须来自 data-analysis 产物**（R0/R2 不编造指标）；图直接引用 `fig01` 等编号，不要重画。
3. **模仿润色**：读 `$RESEARCH_PIPELINE_ROOT/references/papers/` 中 2–3 篇同会议代表作，模仿其段落节奏、衔接、强度（不抄句子、不改事实）。
4. **引用（R2 铁律）**：
   - 每句引用优先从 `$RESEARCH_PIPELINE_ROOT/references/library.bib` 取真实条目。
   - 凡无法确认的一律写 `[CITATION NEEDED]`，**禁止写死作者/年份/卷期/页码**。
   - 文末 bibliography 仅含库内条目；新增文献先入库（R9）再引用。
5. **自检清单**：数字可追溯？引用可核验（无裸造）？范围未超 plan（R8）？图表编号连续？

## 硬规则

- **R0**：所有数字来自真实产物，禁止编造或"合理估计"。
- **R2**：引用真实，`[CITATION NEEDED]` 兜底；二次违规按 R0 处理。
- **R3**：本阶段是作者；质量把关只读不改，本阶段不自我评审定稿。
- **R6**：定稿需人工确认才放行（human_approved 置 true 后进 quality-gate）。
- **R8/R9**：范围锁定、知识库优先。

## 输出

- `outputs/paper-writing/manuscript/main.tex`（或 `.md`）+ 配套（如 `.bib`、figures 软链）
- `outputs/paper-writing/HANDOFF.md`（human_approved=false 待定稿确认）

## 完成判定

manuscript 落盘 + 自检清单过 + HANDOFF（human_approved=false）+ 无未上报偏差 → 交人工门禁（R6 定稿）。确认后置 `human_approved: true`，下游 `quality-gate` 启动只读评审。
