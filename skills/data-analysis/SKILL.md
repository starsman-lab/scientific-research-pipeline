---
name: data-analysis
description: "数据分析：合并code-execution的JSON结果为DataFrame，计算主指标/效应量，做统计检验，生成≥9张科研色系300DPI图，产出stats-report.md。仅消费真实结果，禁止编造。"
description_zh: "数据分析（合并/检验/≥9张科研图）"
description_en: "Data analysis (merge / stats / >=9 scientific figures)"
version: 1.0.0
tags: [research, statistics, visualization, analysis, figures]
display_name: "数据分析"
visibility: public
---

# 数据分析（data-analysis）

你把"把真实数字变成可写进论文的证据"模块化。本阶段**只读 code-execution 的真实产物**，不做任何重跑；输出统计结论与成套科研图表，直接喂给论文写作。

## 输入

- 必读：`outputs/code-execution/results/*.json`（真实执行产物，R0/R7）。
- 参考：`outputs/experiment-design/plan.md` 中的评分标准（指标定义、统计协议、预算）。

## 工作流程

1. **合并**：读全部 `results/*.json` → 统一 pandas DataFrame（行=实验 × 重复，列=指标）。
   - 缺失实验显式标 `NaN` 并写入 `open_questions`（R10），**严禁补造**（R0）。
2. **主指标表**：每实验 `mean ± std`、n、相对 baseline 提升 %、95% CI（bootstrap 或正态近似）。
3. **效应量**：Cohen's d / 相对提升，附可解释文字（小/中/大效应）。
4. **统计检验**：按 plan 协议（配对 t / Wilcoxon / bootstrap）输出 p 值、是否显著；
   - **禁止 p-hacking**：多重比较须注明校正方式（Bonferroni / FDR），未校正不得宣称"多个指标均显著"。
5. **可视化（≥9 张，300 DPI，科研色系）**：
   - 用 matplotlib，`savefig(dpi=300)`；色系统一（建议 seaborn 调色板或自定义 hex，避免红绿冲突、灰度可读），字体 ≥8pt。
   - 落盘 `outputs/data-analysis/figures/fig01_<name>.png` … 至少覆盖：
     1. 主指标柱状图（误差棒 + 显著性标注）
     2. 主指标箱线/小提琴图（含散点）
     3. 消融对比图（组件移除后性能）
     4. 学习曲线（若有时序/epoch）
     5. 混淆矩阵（若分类）
     6. ROC / PR 曲线（若分类）
     7. 参数敏感性图（1–2 个关键超参）
     8. 误差分布直方图 / Q-Q 图
     9. 排名/雷达图（多指标综合对比）
     10.（可选）计算预算 vs 性能散点
   - 图清单写入 `stats-report.md`，方便论文引用 `fig01` 等编号。
6. **stats-report.md**：指标汇总表 + 检验结论 + 图清单 + 文字解读 + 局限与威胁效度（R10）。

## 硬规则

- **R0/R1**：只用真实 results，不补造；provenance 记录每次读入与作图脚本。
- **R2**：图中方法名须与库 / plan 一致，不杜撰方法全名。
- **R8**：只做 plan 约定的分析，不擅自加指标或新检验。
- **R10**：异常/矛盾显式上报。

## 输出

- `outputs/data-analysis/figures/*.png`（≥9 张，300 DPI，科研色系）
- `outputs/data-analysis/stats-report.md`（统计结论 + 图清单 + 解读）
- `outputs/data-analysis/HANDOFF.md`（交接信封，列 figures 与 report 路径）

## 完成判定

DataFrame 合并完成 + `stats-report.md` + ≥9 张图 + HANDOFF 写完 → 自动进 `paper-writing`（论文写作从 figures 与 report 搬数据，不重算）。

---

## 可执行脚本（scripts/）

- `scripts/analyze.py`：把第 1–5 步落成代码。合并 `results/*.json` → pandas DataFrame → 主指标/效应量 → **Welch t 检验 + Holm 多重比较校正**（防 p-hacking）→ **≥9 张 300 DPI 科研色系图** → `stats-report.md`。依赖 `pandas numpy scipy matplotlib statsmodels`（标准科研栈）。
  ```bash
  python skills/data-analysis/scripts/analyze.py --results outputs/code-execution/results/ --out outputs/data-analysis/
  # 无真实数据时可用 --demo 生成合成结果并跑通全流程，验证脚本本身
  python skills/data-analysis/scripts/analyze.py --demo --out outputs/data-analysis/
  ```
- 脚本复用本 SKILL 的图清单顺序（箱线/条形±CI/散点/森林图/直方图/相关热力图/效应量/方差/散点带），色系用 muted 学术 hex（深蓝/砖红/苔绿），`savefig(dpi=300)`。
