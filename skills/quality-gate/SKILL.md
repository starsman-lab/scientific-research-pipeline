---
name: quality-gate
description: "论文质量把关：从六个维度做认识论审查(证据相关性/可证伪性/范围校准/论证连贯性/探索完整性/方法学严谨性)，每维1-5分，并做编造数据与虚假引用检查。只读评审，不改稿，输出整改清单与综合建议。需人工确认结论。"
description_zh: "质量把关（6维认识论审查 + 诚信检查）"
description_en: "Quality gate (6-dimension epistemological review)"
version: 1.0.0
tags: [research, review, quality, integrity-check]
display_name: "质量把关"
visibility: public
---

# 质量把关（quality-gate）

你是流水线的**最后一道防线**。不是语法校对，而是认识论层面的审查：这篇论文的证据链是否成立、是否讲过了头、数据是否真实、引用是否伪造。

## 输入

- `outputs/paper-writing/manuscript/`（待审稿件，LaTeX/MD）
- 全部上游产物（idea-validation / experiment-design / code-execution / data-analysis 的成果）
- `provenance.log`（溯源日志，R1）

## 六维认识论审查（每维 1–5 分）

| 维度 | 审查要点 | 低分信号 |
|------|----------|----------|
| 证据相关性 | 实验是否真的支撑论断 | 拿 A 实验证明 B 结论 |
| 可证伪性 | 核心主张是否可被证伪 | "模型更好因为更智能"类空话 |
| 范围校准 | 结论是否超出证据范围 | 小鼠结论推到人；小样本推全局 |
| 论证连贯性 | 动机→方法→结果→结论是否自洽 | 中间跳步、前后矛盾 |
| 探索完整性 | 是否报告了失败/负结果/局限 | 只报正向、掩去消融失败 |
| 方法学严谨性 | 统计/对照/消融是否规范 | 无显著性检验、无基线对比 |

每维给分 + 一句理由 + 若 <3 给出整改点。

## 诚信检查（最高优先级，对应 R0/R2）

1. **编造数据检查**：抽取稿件中的关键数字/图表，回溯 `provenance.log` 与 `code-execution/results/*.json`，确认每个数字都有真实执行来源。任何无法回溯的数字 → 标 `FABRICATED_DATA` 风险。
2. **虚假/弱引用检查**（参考 nature-ref-verifier + K-Dense-AI line-pinned）：
   - 存在性：每处 `\cite{key}` 必须在 `library.bib` 中。
   - 完整性：bib 条目不得带 `NEED-METADATA` 或缺失 author/title/year/venue，否则标 `INCOMPLETE_REF`。
   - 相关性：条目标题/摘要与本研究主题明显无关 → 标 `WEAK_CITATION`（自动只能提示，最终由人判）。
   - 出现 `[CITATION NEEDED]` 未解决、或作者/年份/卷期对不上 → 标 `FABRICATED_CITATION` 风险。
3. **统计一致性检查**（参考 nature-statistics）：稿件中的 AUC/ACC/F1、p 值、效应量须与 `data-analysis/stats-report.md` 一致；不一致 → 标 `STATS_MISMATCH`。
4. 任一风险命中 → 综合建议直接为 `不通过`，并列出具体位置。

## 只读评审（R3，铁律）

- **你只写 review report，绝不修改原稿文件。**
- 所有意见写入 `outputs/quality-gate/review-report.md`，由作者（人或下游）决定是否采纳。

## 输出

```markdown
# Quality Review Report: <稿件标题>
## 六维评分
- 证据相关性: <n>/5 — <理由/整改点>
- 可证伪性: <n>/5
- 范围校准: <n>/5
- 论证连贯性: <n>/5
- 探索完整性: <n>/5
- 方法学严谨性: <n>/5
## 综合分: <均值>/5
## 诚信检查
- 编造数据: 无风险 | <命中位置>
- 虚假引用: 无风险 | <命中位置>
## 综合建议: 通过 | 小修后通过 | 不通过
## 整改清单
- [ ] <具体可执行的修改项>
## 人工确认: 待研究者确认结论
```

## 必须做的（硬规则）

- **只读（R3）**：不改稿，只产出 report。
- **真实核查（R0/R2）**：诚信检查必须基于 provenance 与 library，不凭感觉。
- **偏差上报（R10）**：发现任何诚信风险必须显式标红，不得"沉默通过"。
- **人工门禁（R6）**：结论必须等研究者确认（标 `human_approved`）后才算放行。

## 完成判定

`review-report.md` 落盘 + 六维齐全 + 诚信检查完成 + HANDOFF.md 写完（含 `human_approved` 占位）→ 交还研究者做终审。

---

## 可执行脚本（scripts/）

- `scripts/gate_check.py`：把「六维评分卡 + 诚信检查」部分自动化（**只读**，R3）。校验 6 维分值格式（1–5 + 门禁阈值）、回溯 `provenance.log` 找 null/error（编造数据信号）、扫描工作区 `\cite{key}` 核对 `library.bib`（虚假/弱引用信号）、比对稿件与 `stats-report.md` 的数字（统计一致性）；输出 `gate-check.json` + `gate-check.md`。仅标准库依赖。
  ```bash
  python skills/quality-gate/scripts/gate_check.py --review outputs/quality-gate/review-report.md --workdir outputs/ --bib references/library.bib --stats outputs/5-data-analysis/stats-report.md
  ```
- 脚本只做可量化的机械核查与门禁初筛；六维的「理由/整改点」仍由 Agent 填写。最终 `human_approved` 仍须研究者确认（R6）。
