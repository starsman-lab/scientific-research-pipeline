# 科研流水线 Harness — 落地概览（v1.2.0）

> 把"文献调研 → Idea 验证 → 实验设计 → 代码执行 → 数据分析 → 论文写作 → 质量把关"落地为受约束的 Agent Skills Harness。
> 参照：K-Dense-AI/scientific-agent-skills、PKU-YuanGroup/OpenAI4S、Imbad0202/academic-research-skills、Yuan1z0825/nature-skills。

## 本次交付

| 文件 | 作用 |
|------|------|
| `Rule.md` | 硬规则宪法（R0–R10）：严禁编造 / 溯源日志 / 引用真实 / 只读评审 / 阶段门禁 / 人在回路 / 真实执行 / 范围锁定 / 知识库优先 / 偏差上报 |
| `docs/STAGE-CONTRACTS.md` | 7 阶段输入/输出/交接契约 + Handoff Envelope 模板 + 目录结构 |
| `references/` | 知识库脚手架：论文 Markdown 卡模板、bibtex 库、入库流程 |
| `skills/research-pipeline/` | 主编排器：串联 7 阶段、卡门禁、半自动调度 |
| `skills/literature-review/` | 文献调研：scan（快速扫描）+ gap（深度未解决问题清单） |
| `skills/idea-validation/` | Idea 验证：三问过滤（是否做过 / 故事 / 差异显著性） |
| `skills/quality-gate/` | 质量把关：6 维认识论审查 + 编造/虚假引用检查（只读） |
| `skills/experiment-design/` | 实验设计：baseline/消融/评分 + 独立 Review 循环 + 小批量预实验验证 |
| `skills/code-execution/` | 代码执行：真实执行三路径（本地 Bash / 远程 GPU 任务文件 / 手动说明） |
| `skills/data-analysis/` | 数据分析：合并 JSON + 统计检验 + 效应量 + ≥9 张 300DPI 科研图 |
| `skills/paper-writing/` | 论文写作：骨架 + 模仿润色 + 引用校验（[CITATION NEEDED]） |

已部署到 `~/.workbuddy/skills/`，本会话可直接触发。

## 怎么用

- **WorkBuddy（已就绪）**：直接说"运行科研流水线 / 文献调研 / Idea 验证 / 质量把关"。
- **共享根变量**：`RESEARCH_PIPELINE_ROOT`（默认 `D:\Workbuddy\phd_learn_agent\research-pipeline`），各技能据此找 Rule.md / docs / references。
- **便携式**：`research-pipeline/` 整仓可推 GitHub；`skills/` 符合 Agent Skills 标准，Claude Code / Codex 直接加载。
- **半自动门禁**（R6）：常规阶段自动串联；实验设计、论文定稿、质量把关三处必须你确认才放行。

## 各阶段当前状态（v1.2.0）

- ✅ 全部 7 阶段可用：1 文献调研、2 Idea 验证、3 实验设计、4 代码执行、5 数据分析、6 论文写作、7 质量把关
- v1.2.0 新增：**每阶段 skill 均配 `scripts/` 真实可执行 Python**（fetch_papers / check_novelty / pilot_run / run_experiment / analyze / check_citations / gate_check），提示词驱动脚本落地，不再是纯 markdown 提示词库
- 半自动门禁（R6）：3 实验设计、6 论文定稿、7 质量把关结论 三处需人工确认

## 下一步（持续迭代）

- 用真实课题跑通一轮，把各 Stage 的实际 prompt 调优笔记回填 `references/` 或 `decisions/`。
- 可加：Stage 间 `make`-式编排脚本、产物 diff 校验、跨 Stage 一致性 lint。

建议每跑通一篇论文后，回填对应 Stage 的实际 prompt 调优笔记到 `references/` 或 `decisions/`，持续迭代。
