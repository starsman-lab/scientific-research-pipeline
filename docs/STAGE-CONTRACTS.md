# 阶段契约（Stage Contracts）

> 每个 Stage 是一个受约束的 Sub-Agent。本文档锁定每个 Stage 的**输入、输出、下游消费者、Handoff Envelope 字段**，以及人工门禁开关。
> 配套规则见根目录 `Rule.md`。任何 Stage 不满足契约即按 R4 / R5 退回。

---

## 流水线总览（7 阶段）

```
[1] 文献调研 ──auto──> [2] Idea 验证 ──auto──> [3] 实验设计 ──GATE──> [4] 代码执行 ──auto──>
[5] 数据分析 ──auto──> [6] 论文写作 ──GATE(定稿)──> [7] 质量把关 ──GATE──> 人类终审
```

| # | Stage | 技能名 | 状态 | 人工门禁(R6) |
|---|-------|--------|------|--------------|
| 1 | 文献调研 | `literature-review` | ✅ 已建 | 否（自动串联） |
| 2 | Idea 验证 | `idea-validation` | ✅ 已建 | 否（自动串联） |
| 3 | 实验设计 | `experiment-design` | ✅ 已建 | ✅ 是 |
| 4 | 代码执行 | `code-execution` | ✅ 已建 | 否 |
| 5 | 数据分析 | `data-analysis` | ✅ 已建 | 否 |
| 6 | 论文写作 | `paper-writing` | ✅ 已建 | ✅ 定稿时 |
| 7 | 质量把关 | `quality-gate` | ✅ 已建 | ✅ 是 |

---

## Handoff Envelope（交接信封，通用模板）

每个 Stage 完成时，在 `$RESEARCH_WORKDIR/<stage>/HANDOFF.md` 写入以下内容，下游 Stage 方可启动。

```markdown
# HANDOFF: <from_stage> -> <to_stage>
- timestamp: <ISO8601>
- human_approved: <true|false>
- artifacts:
  - <path/to/output1>
  - <path/to/output2>
- key_findings: |
    <3-5 条关键结论，机器可读要点>
- open_questions:
  - <未决项1>
  - <未决项2>
- blockers: <none | <阻塞描述>>
```

下游 Stage 启动前必须：①读取上游 HANDOFF.md ②校验 `blockers == none` 或已解决 ③读取 `artifacts` 指向的文件。

---

## [1] 文献调研 `literature-review`

- **输入**：研究方向描述（自由文本，含目标会议/期刊、时间窗、子领域关键词）。
- **子模式**：
  - `scan`（快速扫描）：近 2 年顶会顶刊相关论文，每篇输出标题 / 主要做法(一句话) / 数据集 / 核心指标。
  - `gap`（深度分析）：基于 scan 结果，输出结构化"未被解决的问题清单"。
- **输出**：
  - `outputs/lit-review/scan.md`（论文地图）
  - `outputs/lit-review/gap-analysis.md`（未解决问题清单，直接喂给 Idea 验证）
  - 每条论文同步入库 `references/papers/` + `references/library.bib`（R9）
- **下游消费者**：`idea-validation`（消费 gap-analysis.md）
- **门禁**：自动；产物须含 provenance（R1）。

## [2] Idea 验证 `idea-validation`

- **输入**：Idea 描述（自由文本）+ 上游 `gap-analysis.md`。
- **三问**：
  1. 近 3 年是否有人做过？（联网检索相关论文）
  2. 方法能否讲通故事？（扮演审稿人打分，1-5）
  3. 与现有方法差异是否显著？（对比分析）
- **输出**：`outputs/idea-validation/report.md`（三问结论 + 过滤建议：推进 / 修改后推进 / 放弃）
- **下游消费者**：`experiment-design`（仅当结论为"推进"时）
- **门禁**：自动；三问任一项为"严重风险"时显式上报（R10）。

## [3] 实验设计 `experiment-design`（已建）

- **输入**：`idea-validation/report.md`。
- **职责**：自动设计 baseline 对比、消融实验方案、评分标准；另一 Review Agent 审核并迭代；关键决策用小批量探索子 Agent 预实验验证。
- **输出**：`outputs/experiment-design/plan.md` + 预实验报告。
- **门禁**：✅ 人工确认（R6）。
- **下游消费者**：`code-execution`。

## [4] 代码执行 `code-execution`（已建）

- **输入**：`experiment-design/plan.md`。
- **职责**：真实环境跑代码（本地 Bash / 远程 GPU 任务文件 / 手动说明三路径，见 R7）。
- **输出**：`outputs/code-execution/results/*.json` + `provenance.log`。
- **门禁**：自动；严禁编造（R0/R1/R7）。
- **下游消费者**：`data-analysis`。

## [5] 数据分析 `data-analysis`（已建）

- **输入**：`code-execution/results/*.json`。
- **职责**：合并 DataFrame、算主指标/效应量、统计检验、生成 ≥9 张科研色系 300DPI 图。
- **输出**：`outputs/data-analysis/figures/` + `stats-report.md`。
- **门禁**：自动。
- **下游消费者**：`paper-writing`。

## [6] 论文写作 `paper-writing`（已建）

- **输入**：上述全部产物 + 目标会议 LaTeX 模板。
- **职责**：搭骨架、模仿参考论文结构与节奏润色；引用须来自知识库或联网验证（R2）。
- **输出**：`outputs/paper-writing/manuscript/`（LaTeX/MD）。
- **门禁**：✅ 定稿时人工确认（R6）。
- **下游消费者**：`quality-gate`。

## [7] 质量把关 `quality-gate`

- **输入**：`paper-writing/manuscript/` + 全部上游产物 + `provenance.log`。
- **职责**：6 维认识论审查（各 1-5 分）+ 编造/虚假引用检查；只读评审（R3）。
- **输出**：`outputs/quality-gate/review-report.md`（综合建议 + 逐维分数 + 整改清单）。
- **门禁**：✅ 人工确认结论（R6）。
- **下游消费者**：人类终审。

---

## 目录结构（约定）

```
$RESEARCH_WORKDIR/
├── provenance.log              # R1 溯源日志 (JSONL)
├── decisions/
│   └── OPEN-DECISIONS.md        # R8 未决项登记
├── lit-review/                 # Stage 1
├── idea-validation/            # Stage 2
├── experiment-design/          # Stage 3
├── code-execution/             # Stage 4
├── data-analysis/              # Stage 5
├── paper-writing/              # Stage 6
└── quality-gate/               # Stage 7
```
