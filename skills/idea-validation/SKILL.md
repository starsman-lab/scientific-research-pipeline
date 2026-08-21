---
name: idea-validation
description: "Idea 验证：在真正动手前，用三问过滤方向——(1)近3年是否有人做过 (2)方法能否讲通故事(扮演审稿人打分) (3)与现有方法差异是否显著。输出结构化报告与推进/修改/放弃建议，帮研究者省去重复造轮子的时间。"
description_zh: "Idea 验证（三问过滤）"
description_en: "Idea validation (3-question filter)"
version: 1.0.0
tags: [research, idea, validation, reviewer-simulation]
display_name: "Idea 验证"
visibility: public
---

# Idea 验证（idea-validation）

你在研究者真正投入实验前，先替他把 idea "挑战一遍"。目的不是替他想 idea，而是**过滤掉"看上去好但其实做过了/讲不通"的方向**，并让他在写 Introduction 前就把逻辑想深一层。

## 输入

- Idea 描述（自由文本）：方法核心、要解决什么问题、预期贡献。
- 上游 `outputs/lit-review/gap-analysis.md`（来自 literature-review，提供领域空白上下文）。
- 可选：研究者已有的初步实验迹象。

## 三问（必须逐条作答）

### Q1：近 3 年是否有人做过？
- 用 WebSearch / WebFetch 检索近 3 年相关论文（arXiv、Semantic Scholar、OpenAlex、会议官网）。
- 列出最相关的 3–5 篇"撞车"论文，逐篇说明：它做了什么、与本研究的交集、差异点。
- 结论：`未做过` / `部分重叠` / `高度相似(高风险)`。

### Q2：方法能否讲通故事？（扮演审稿人打分）
- 切换到审稿人视角，对 idea 的**动机—方法—贡献**链条打分（1–5）：
  - 动机是否真实（问题确实未被解决？）
  - 方法是否对症（方法真的能解决问题？）
  - 贡献是否清晰（相比 SOTA 增量是什么？）
- 输出一段"审稿人叙事"：如果录取，故事怎么讲；如果被拒，最可能的拒稿理由是什么。
- 结论：`故事成立(4-5)` / `需补强(2-3)` / `讲不通(1)`。

### Q3：与现有方法差异是否显著？
- 对比分析：列出本研究 vs 最近 2–3 个最强基线，在**假设 / 数据 / 机制 / 评测**四个维度上的差异。
- 判断差异是否足以构成"新贡献"而非"换皮"：给出 `显著` / `边际` / `几乎无差异`。

## 输出

写 `outputs/idea-validation/report.md`：

```markdown
# Idea Validation Report: <idea 一句话>
## Q1 是否做过: <结论>
- 撞车论文: <列表+交集说明>
## Q2 故事评分: <均分>/5
- 审稿人叙事: <一段话>
- 最可能拒稿理由: <或"无明显短板">
## Q3 差异显著性: <结论>
- 四维对比: <表>
## 综合建议: 推进 | 修改后推进 | 放弃
- 理由: ...
- 若"修改后推进": 需补强的点: <列表>
## 上游 gap 对应关系: <本 idea 对应 gap-analysis 的哪条 GAP>
```

## 必须做的（硬规则）

- **真实检索（R1/R2）**：Q1 的每篇"撞车"论文须来自真实检索，带来源；不得凭记忆编造"有人做过/没人做过"。
- **不替用户决策（R6 精神）**：综合建议是"建议"，最终推进与否由研究者定；若三问均高风险，显式标注 `建议放弃` 但说明这是过滤建议而非命令。
- **偏差上报（R10）**：若检索覆盖可能不全（新方向文献少），写明"结论可靠性受限"。

## 完成判定

`report.md` 落盘 + 三问齐全 + HANDOFF.md 写完 → 自动进下一 Stage。
仅当综合建议为 `推进` 或 `修改后推进` 时，下游 experiment-design 才可消费本报告。

---

## 可执行脚本（scripts/）

- `scripts/check_novelty.py`：近 3 年 arXiv 检索 + 文本重叠度启发式（difflib 风格 token 重叠），输出 novelty 报告。这是**启发式筛查**，不替人决策（R6 精神）；最终 go/no-go 仍由研究者定。仅标准库依赖。
  ```bash
  python skills/idea-validation/scripts/check_novelty.py --idea "knowledge-constrained multimodal heart-failure risk model" --max 15
  ```
- Q1「近 3 年是否做过」优先用该脚本做量化初筛，Agent 再对 top 重叠论文做语义判断与三问叙事。
