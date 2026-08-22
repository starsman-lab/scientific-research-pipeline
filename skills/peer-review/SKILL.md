---
name: peer-review
description: "同行评审（模拟）：把稿件交给 2–3 个独立审稿人视角做结构化批判，输出 Major/Minor 意见清单与内部一致性检查。它直接消费 paper-writing 稿件与上游产物，产出可执行的整改清单；revise 由下游 paper-writing 回退执行（review→revise 闭环）。只读评审，不改稿。"
description_zh: "同行评审（模拟 2–3 审稿人 + Major/Minor 清单）"
description_en: "Peer review (simulated 2–3 reviewers, Major/Minor list)"
version: 1.1.0
tags: [research, review, peer-review, critique, revise-loop]
display_name: "同行评审"
visibility: public
---

# 同行评审（peer-review）

你是流水线里的**审稿人团**。paper-writing 交来的稿子在这里被 2–3 个独立视角批判，
产出可执行的 Major / Minor 意见清单；之后回退到 paper-writing 做 revise，再回到本阶段，
形成 review → revise 闭环（参考 Imbad0202/academic-research-skills 的
research→write→review→revise→finalize 与 Yuan1z0825/nature-skills 的 nature-reviewer）。

## 输入

- `outputs/paper-writing/manuscript/`（待审稿件，LaTeX/MD）
- 全部上游产物（idea-validation / experiment-design / code-execution / data-analysis）
- `provenance.log`、`references/library.bib`

## 工作流程

1. **结构检查**：稿件是否具备 Abstract / Intro(含 Related Work) / Method / Results /
   Discussion / Limitations / Conclusion。缺核心章节 → Major。
2. **Evidence ledger 检查（claim→evidence）**：逐句核对稿件中的量化论断是否能在
   `stats-report.md` / `results/*.json` 找到对应数字；找不到且无标注 → Major（FABRICATED_DATA 风险）。
3. **Citation 相关性检查**：每处 `\cite{key}` 对照 `library.bib`——
   - 条目缺 author/title/year/venue 或带 `NEED-METADATA` → 标 `INCOMPLETE_REF`（Minor→Major 视是否支撑核心 claim）。
   - 标题/摘要与本研究主题明显无关 → 标 `WEAK_CITATION`，要求替换或删除。
4. **统计一致性**：稿件里的 AUC/ACC/F1、p 值、效应量须与 `stats-report.md` 一致；
   不一致 → Major。
5. **贡献与机制**：Discussion 是否讲清「为什么」（机制），而非只说「A 比 B 好」；
   贡献是否具体到可证伪；是否挂到真实研究问题（而非泛泛 demo）。
6. **模拟 2–3 个审稿人**，各自给一段叙事 + 总体倾向（Accept / Minor / Major），
   汇总去重为一份意见清单。

## 输出

写 `outputs/peer-review/review-report.md`：

```markdown
# Peer Review Report: <标题>
## 结构检查
- <章节齐全性 + 缺失项>
## Evidence ledger
- <claim→evidence 命中/缺失列表>
## Citation 审查
- INCOMPLETE_REF: <key 列表>
- WEAK_CITATION: <key 列表 + 建议替换方向>
## 统计一致性
- <一致 | 不一致位置>
## 审稿人视角（2–3）
- Reviewer A: <叙事 + 倾向>
- Reviewer B: ...
## 整改清单
### Major（必须改）
- [ ] <具体可执行的修改项>
### Minor（建议改）
- [ ] <...>
## 综合建议: 需修订 | 可定稿
```

## 硬规则

- **只读（R3）**：本阶段不改稿，只产出 report；revise 交回 paper-writing。
- **相关性也要查（补强 R2）**：引用存在 ≠ 引用合理；WEAK_CITATION 必须显式标出。
- **闭环**：综合建议为「需修订」时，编排器回退到 paper-writing 执行 revise，
  再回到本阶段复评，直到「可定稿」或人工介入（R6）。

## 完成判定

`review-report.md` 落盘 + Major/Minor 清单齐全 + HANDOFF.md 写完 → 交编排器。
若 Major 非空 → 编排器回退 paper-writing(revision)；若空 → 进 quality-gate。

---

## 可执行脚本（scripts/）

- `scripts/peer_review.py`：把结构检查 / Evidence ledger / Citation 完整性 / 统计一致性
  做成**机械预检**，输出 `review-report.md`（预填 Major/Minor 初稿），由 Agent 补写
  审稿人叙事与最终倾向。仅标准库依赖。
  ```bash
  python skills/peer-review/scripts/peer_review.py \
    --manuscript outputs/paper-writing/manuscript/main.md \
    --stats outputs/6-data-analysis/stats-report.md \
    --bib references/library.bib --out outputs/peer-review/review-report.md
  ```
- 脚本只做可量化预检；审稿人叙事与「为什么」判断仍由 Agent 完成。最终是否定稿由
  人工确认（R6）。
