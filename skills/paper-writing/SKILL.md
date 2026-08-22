---
name: paper-writing
description: "论文写作：先建「论证契约」(proposal-first)再起草——thesis + 3条贡献(每条挂证据) + 机制假设 + 威胁效度；related-work 分支持/对照/相邻三类且用真实相关引用；结果按多面板证据架构陈述；统计自审(数字可回溯、效应量+CI)。引用须真实(R2)，未确认标[CITATION NEEDED]，定稿需人工门禁(R6)。"
description_zh: "论文写作（论证契约 + 贡献定位 + 机制 + 多面板证据）"
description_en: "Paper writing (argument contract + contribution framing + mechanism + multi-panel evidence)"
version: 1.1.0
tags: [research, writing, manuscript, citation, argument-contract]
display_name: "论文写作"
visibility: public
---

# 论文写作（paper-writing）

你把"把证据写成可投稿的稿子"模块化。本阶段是**作者**：先建论证契约，再起草；
所有数字来自真实产物，所有引用可核验；质量把关（quality-gate）与同行评审（peer-review）
才会只读审查（R3）。

> 思路来源：Yuan1z0825/nature-skills 的 proposal-first（先建证据/论证契约再起草、
> 重建论证而非泛泛生成）、K-Dense-AI 的 line-pinned citation（行级引用绑定）、
> Imbad0202 的 claim→evidence receipt（论断—证据收据）。

## 输入

- 上游全部产物：`lit-review/`、`idea-validation/`、`experiment-design/`、`code-execution/`、`data-analysis/`。
- 目标会议/期刊模板（用户提供路径，或联网取官方模板）。无模板则用 Markdown 等价结构。

## 工作流程

### 0. 论证契约（proposal-first，必须先做）

起草前先写 `outputs/paper-writing/argument-contract.md`，**不填完不写正文**：

```markdown
# Argument Contract
## Thesis（一句话核心主张）
- <可证伪的一句话>
## Contributions（≤3 条，每条挂证据）
- C1: <贡献> | 证据: <data-analysis 的哪张图/哪行数> | 强度: <强/中>
- C2: ...
## Mechanism hypothesis（为什么预期如此）
- <机制解释，可被数据支持或反驳>
## Related-work map（真实相关引用）
- 支持: [cite keys]
- 对照: [cite keys]
- 相邻: [cite keys]
## Threats to validity（提前列）
- <内部/外部效度威胁>
```

契约是后续自检的标尺：每一条 Contribution 必须在正文有对应数字，每一条 Related
必须指向真实相关文献。

### 1. 搭骨架（按目标模板章节）

Abstract / Intro(含 Related Work) / Method / Results / Discussion / Limitations / Conclusion。
每段注明数据来自哪个上游产物（line-pinned）。

### 2. 填内容

- **Intro + Related Work**：从 `gap-analysis.md` 引动机；从 `idea-validation/report.md` 引贡献。
  Related Work **分三类**（支持/对照/相邻）归纳，不堆砌；每条论断绑定具体 `\cite`，
  禁止用自动抓取但无关的文献充数（peer-review 会标 `WEAK_CITATION`）。
- **Method**：从 `plan.md` 提炼，公式用真实符号，不写未实现模块。
- **Results（多面板证据架构）**：从 `stats-report.md` + `figures/*.png` 搬数据，
  **数字必须来自 data-analysis 产物**（R0/R2 不编造）；每张图/表标编号与统计注记
  （n、检验、p、效应量、CI）。
- **Discussion**：先讲 **mechanism**（为什么 C1 成立），再讲边界与外部效度，最后落到
  真实研究问题（避免「demo 自嗨」）。
- **Limitations**：必须含校准/数据可用性/泛化等真实威胁（见 `argument-contract.md` 的 Threats）。

### 3. 模仿润色

读 `$RESEARCH_PIPELINE_ROOT/references/papers/` 中 2–3 篇同会议代表作，模仿段落节奏
（不抄句子、不改事实）。

### 4. 引用（R2 铁律）

- 每句引用优先从 `library.bib` 取**真实且相关**条目；凡无法确认相关性的一律
  写 `[CITATION NEEDED]`，**禁止写死作者/年份/卷期/页码**。
- 文末 bibliography 仅含库内条目；新增文献先入库（R9）再引用。

### 5. 自检清单（落盘前必跑 `audit_manuscript.py`）

- 数字可追溯（claim→evidence）？引用可核验（无裸造、无弱相关）？
- 范围未超 plan（R8）？图表编号连续？机制假设在 Discussion 被显式讨论？

## 硬规则

- **R0**：所有数字来自真实产物，禁止编造或"合理估计"。
- **R2**：引用真实且相关，`[CITATION NEEDED]` 兜底；二次违规按 R0 处理。
- **R3**：本阶段是作者；质量把关/同行评审只读不改，本阶段不自我评审定稿。
- **R6**：定稿需人工确认才放行（human_approved 置 true 后进 peer-review）。
- **R8/R9**：范围锁定、知识库优先。

## 输出

- `outputs/paper-writing/argument-contract.md`（论证契约）
- `outputs/paper-writing/manuscript/main.tex`（或 `.md`）+ 配套（`.bib`、figures 软链）
- `outputs/paper-writing/HANDOFF.md`（human_approved=false 待定稿确认）

## 完成判定

argument-contract 落盘 + manuscript 落盘 + `audit_manuscript.py` 无 Major + 自检清单过
+ HANDOFF（human_approved=false）+ 无未上报偏差 → 交人工门禁（R6 定稿）。确认后置
`human_approved: true`，下游 `peer-review` 启动只读评审；若有 Major 则回退本阶段 revise。

---

## 可执行脚本（scripts/）

- `scripts/check_citations.py`：扫描 `[CITATION NEEDED]` 并核对 `\cite{key}` 是否真实
  存在于 `library.bib`；输出 `citation-check.md` + JSON。仅标准库依赖。
  ```bash
  python skills/paper-writing/scripts/check_citations.py --draft outputs/paper-writing/manuscript/main.md --bib references/library.bib
  ```
- `scripts/audit_manuscript.py`：落地「论证契约自检」——核对每一条 Contribution 在
  正文有对应数字、Related Work 三类引用齐全、无 `[CITATION NEEDED]`、机制在 Discussion
  被讨论；输出 `audit-report.md`（Major/Minor）。仅标准库依赖。
  ```bash
  python skills/paper-writing/scripts/audit_manuscript.py --contract outputs/paper-writing/argument-contract.md --manuscript outputs/paper-writing/manuscript/main.md
  ```
- 定稿前必须跑这两个脚本：有 `[CITATION NEEDED]` 未解决、`\cite` 缺失、或 audit 命中
  Major → 拦截，不得进 peer-review。
