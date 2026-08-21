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

   | 标题 | 主要做法(一句话) | 数据集 | 核心指标 | 来源 |
   |------|----------------|--------|----------|------|

   目标：20–60 篇覆盖领域的摘要信息，约 20 分钟出粗地图。
3. **每条必须带真实来源 URL / arXiv ID**（R2），不得编造标题或指标。
4. 同步入库：把每篇写成 `$RESEARCH_PIPELINE_ROOT/references/papers/<year>-<firstauthor>-<short>.md`（用 `$RESEARCH_PIPELINE_ROOT/references/templates/paper-card.md`），并追加 bibtex 到 `$RESEARCH_PIPELINE_ROOT/references/library.bib`（R9）。

## 模式二：gap（深度分析）

基于 `scan.md`，做结构化 gap 分析：

1. 横向对比 scan 中的做法，找出**共性假设 / 未覆盖场景 / 方法空白**。
2. 输出 `outputs/lit-review/gap-analysis.md`，结构：

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
