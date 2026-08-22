---
name: literature-review
description: "科研文献调研：拆成两步——scan(快速扫描近2年顶会顶刊，每篇输出标题/做法/数据集/指标) 与 gap(深度分析，输出结构化未解决问题清单)。结果同步入库知识库，并写provenance溯源日志。"
description_zh: "文献调研（快速扫描 + 深度 gap 分析）"
description_en: "Literature review (scan + gap analysis)"
version: 1.0.0
tags: [research, literature, survey, gap-analysis]
display_name: "文献调研"
visibility: public
---

# 文献调研（literature-review）

你把繁琐的"人肉搜文献"模块化。给定研究方向，分两步产出**领域地图**与**未解决问题清单**，直接喂给 Idea 验证。

## 输入

- 研究方向描述（自由文本）：含目标会议/期刊、时间窗（默认近 2 年）、子领域关键词、是否限定数据集/任务类型。
- 可选：续跑时读取上游 HANDOFF。

## 子模式

调用本技能时指定 `mode`：
- `scan`：快速扫描，画粗地图。
- `gap`：深度分析，基于已有 scan 结果找 gap（需先有 `outputs/lit-review/scan.md`）。
- 不指定则**先 scan 后 gap** 连跑。

---

## 模式一：scan（快速扫描）

1. 用 WebSearch / WebFetch 在学术来源检索，优先：arXiv、Semantic Scholar、OpenAlex、Google Scholar、PubMed（按领域选）。建议查询组合：
   - `"<关键词>" venue:<会议名> 2024|2025`
   - `"<关键词>" benchmark dataset <名称>`
   - 用 `allowed_domains` 限定 arxiv.org / semanticscholar.org / openreview.net 等。
2. 每篇论文提取并输出为一行表项：

   | 标题 | 主要做法(一句话) | 数据集 | 核心指标 | 相关性 | 来源 |
   |------|----------------|--------|----------|--------|------|

   目标：20–60 篇覆盖领域的摘要信息，约 20 分钟出粗地图。
3. **相关性评分（强制，参考 nature-citation 的严格他引审计）**：对每条论文，对照本研究
   问题计算 relevance ∈ {高, 中, 低}（高=直接支撑/对照本研究；中=方法/数据相邻；低=仅主题词命中）。
   **只有 高/中 才入库并允许被引用**；低相关论文仅作「检索覆盖」记录，不得进入 related-work，
   避免自动抓取但无关的文献污染引用（peer-review 会二次标 `WEAK_CITATION`）。
4. **每条必须带真实来源 URL / arXiv ID**（R2），不得编造标题或指标。
5. 同步入库：把每篇写成 `$RESEARCH_PIPELINE_ROOT/references/papers/<year>-<firstauthor>-<short>.md`（用 `$RESEARCH_PIPELINE_ROOT/references/templates/paper-card.md`），并追加 bibtex 到 `$RESEARCH_PIPELINE_ROOT/references/library.bib`（R9）。入库条目须补全 author/title/year/venue，**禁止 `NEED-METADATA` 占位**（quality-gate 会标 `INCOMPLETE_REF`）。

## 模式二：gap（深度分析）

基于 `scan.md`，做结构化 gap 分析：

1. 横向对比 scan 中的做法，找出**共性假设 / 未覆盖场景 / 方法空白**。
2. **Related-work 三元归纳**：从入库（高/中相关）论文中归纳三类，供 paper-writing 直接消费：
   - **支持（supporting）**：与本主张同向或提供方法基础。
   - **对照（contrasting）**：得出不同结论 / 用不同方法，是审稿人最爱问的。
   - **相邻（adjacent）**：同领域但不同任务，用于划定边界。
   每类下列出 2–5 篇真实条目（带 cite key），并写明「本稿用它支撑/对照哪句话」。
3. 输出 `outputs/lit-review/gap-analysis.md`，结构：

   ```markdown
   # Gap Analysis: <方向>
   ## 1. 已被充分研究的子方向
   - ...
   ## 2. 未被解决 / 研究不足的问题（未解决问题清单）
   - [GAP-1] <问题描述> | 为什么重要 | 现有方法为何没解决 | 可能切入点
   - [GAP-2] ...
   ## 3. 方法层面的空白
   - ...
   ## 4. 数据集 / 评测空白
   - ...
   ```

3. 这份清单是 Idea 验证的直接输入——每条 GAP 都应可被转化为一个可验证的 idea。

---

## 必须做的（硬规则）

- **provenance（R1）**：每次搜索/抓取向 `$RESEARCH_WORKDIR/provenance.log` 追加一行（时间戳 + 真实 query + 结果数 + 来源域名）。失败标 `null`。
- **引用真实（R2）**：所有论文须来自真实检索，禁止编造；指标须标注出处（论文章节/表格）。
- **知识库优先（R9）**：先查 `$RESEARCH_PIPELINE_ROOT/references/` 是否已有相关卡，避免重复检索；新论文入库后才可引用。
- **偏差上报（R10）**：若某方向近 2 年文献极少（可能太新或太冷），显式写出"检索覆盖可能不全"。

## 输出

- `outputs/lit-review/scan.md`（论文地图）
- `outputs/lit-review/gap-analysis.md`（未解决问题清单）
- `$RESEARCH_PIPELINE_ROOT/references/papers/*.md` + `$RESEARCH_PIPELINE_ROOT/references/library.bib`（入库）
- `outputs/lit-review/HANDOFF.md`（交接信封，指向上面两个产物）

## 完成判定

scan 与 gap 均有落盘文件 + provenance 有记录 + HANDOFF.md 写完 → 自动进下一 Stage（idea-validation）。

---

## 可执行脚本（scripts/）

本技能配套真实工具，提示词驱动、脚本落地（参考 K-Dense-AI/scientific-agent-skills 的 `skill/scripts/` 模式）：

- `scripts/fetch_papers.py`：调 arXiv API 批量抓取近 N 年论文，按「查询词与标题/摘要的词重叠」
  计算 relevance 分（高/中/低），仅高/中才写入卡与 `library.bib`，每次调用写 provenance（R1）。
  强制补全 author/title/year，**默认不带 `NEED-METADATA` 占位**（若 API 缺字段则标 `低相关` 不入库）。
  **仅标准库依赖**。
  ```bash
  python skills/literature-review/scripts/fetch_papers.py --query "logistic regression vs gradient boosting tabular medical" --max 20 --year-from 2022
  ```
- `scan` 模式的初筛优先用该脚本批量拉卡；`gap` 仍由 Agent 基于 scan 做结构化分析与 related-work 三元归纳。脚本拉回的卡是 `gap` 与引用的真实来源（R2/R9）。
