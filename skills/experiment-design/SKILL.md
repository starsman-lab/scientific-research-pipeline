---
name: experiment-design
description: "实验设计：读取Idea验证结论，自动产出baseline对比方案、消融实验设计、评分标准；经独立Review Agent审核迭代；关键决策用探索子Agent做小批量预实验验证循环。需人工门禁(R6)。"
description_zh: "实验设计（baseline/消融/评分 + Review + 小批量预实验）"
description_en: "Experiment design (baseline/ablation/scoring + review + small-batch pre-experiment)"
version: 1.0.0
tags: [research, experiment, design, ablation, baseline, review]
display_name: "实验设计"
visibility: public
---

# 实验设计（experiment-design）

你把"怎么证明这个 idea 真的有效"模块化。读入 Idea 验证结论，产出**可执行的实验方案**，并经过独立 Review 与小规模预实验验证后，才交人工确认（R6）。本阶段不跑正式训练，只把"要跑什么、怎么算赢、怎么防作弊"讲清楚并做小批量验证。

## 输入

- 必读：`outputs/idea-validation/report.md`（三问结论与过滤建议）。
  - 若结论不是 `推进` 或 `修改后推进` → **立即停止**，按 R10 写入偏差并回报，不进入设计。
- 参考（R9 优先取已入库）：`outputs/lit-review/gap-analysis.md`、`$RESEARCH_PIPELINE_ROOT/references/papers/*.md`、`$RESEARCH_PIPELINE_ROOT/references/library.bib`。

## 工作流程

### Step 1 解析 Idea 与验收假设
1. 从 report.md 抽取：核心贡献点、声称优势、目标任务、目标数据集、方法关键组件。
2. 写出**可证伪的验收假设**（对应 R0 精神——结论必须可被数据推翻）：
   - H1：本方法在主指标上显著优于最强 baseline（p<0.05，效应量 ≥ 约定阈值）。
   - H2：移除组件 X 后性能显著下降，证明 X 必要。
3. 写入 `outputs/experiment-design/README.md`（设计总则：假设、风险、范围）。

### Step 2 设计 baseline 对比（R8 范围锁定）
1. 列出 3–5 个**公平** baseline：
   - 任务标准 SOTA（真实公开代码，URL 须真实，R2）。
   - 与你方法"共享最多组件、只差核心改动"的消融式 baseline（最能说明贡献）。
   - 朴素启发式 / 随机 / 常量（下界）。
2. 每个 baseline 注明：来源（论文卡或库）、实现方式（复用已有代码 / 自行实现）、公开代码 URL、许可。
3. 公平性约束表：相同数据划分、相同预处理、相同评测协议、相同随机种子范围、相同计算预算上限。

### Step 3 设计消融实验
1. 拆出方法可独立移除的组件（≥3 个），每个对应一个消融问题。
2. 消融表：组件 | 移除后预期 | 验证什么 | 风险等级。
3. 注明协议：单独消融（一次去一个）还是累积消融（逐级去掉），并解释为何选该协议。

### Step 4 定义评分标准
1. 主指标 + ≥2 个辅助指标：写明公式、方向（高/低好）、为何选它、是否可被操纵（防 gaming）。
2. 统计协议：交叉验证折数 / 重复次数、显著性检验方法（配对 t / Wilcoxon / bootstrap CI）、效应量（Cohen's d 或相对提升%）、多重比较校正方式。
3. 计算预算：参数量、FLOPs、显存、训练时长（用于 Step 6 与 R7 真实执行规划）。

### Step 5 独立 Review Agent 审核迭代（关键）
1. 把 plan 草稿交给**独立 Review Agent**（不共享本上下文）。固定 prompt：
   > 你是资深方法审稿人，评审以下实验方案能否支撑其声称贡献。重点挑刺：①baseline 是否公平（有无偷换评测协议）②消融是否覆盖关键组件③指标是否可被操纵④统计协议是否够力（样本量/重复数）⑤是否有数据泄漏/偷看测试集风险⑥预算是否现实。输出格式：`通过` 或 `打回` + 编号缺陷清单（每条含具体修改建议）。
2. Review 结论写入 `outputs/experiment-design/review.md`：
   - `通过` → 进 Step 6。
   - `打回` → 按缺陷清单修改 plan.md，最多迭代 3 轮；3 轮仍不过 → 停止并上报（R10）。
3. **严禁本 Agent 自评自改**（呼应 R3 精神：设计者不兼评审）。

### Step 6 小批量预实验验证循环（高风险决策点）
对"方法能否跑通 / 核心组件是否有正向信号"这类高风险假设，用探索子 Agent 做小批量预实验，而非空想：
1. 生成**可执行验证产物**（非旁白，R5）：
   - `outputs/experiment-design/pre-exp/config.yaml`：小批量配置（数据子集 50–200 样本、1–2 折、少 epoch、小模型/小隐层）。
   - `outputs/experiment-design/pre-exp/run_prompt.md`：交给 code-execution 的任务说明模板（对应 R7 路径③）。
2. 派**探索子 Agent**（独立上下文）按 config 真实跑（本地 Bash 或远程 GPU 任务文件），返回：
   - 是否跑通（无报错、产物落盘）；
   - 相对最简 baseline 的方向是否正向；
   - 显存/时长是否可控（决定正式实验可行性）。
3. 读回结果自动分析：
   - 方向正向且可跑通 → 预实验通过，plan 标注 `已小批量验证`。
   - 方向负向或不可跑通 → 回 Step 2/3 调整方案，重做 Review；仍不行 → 上报（R10）。
4. 预实验全过程的每次执行写 provenance（R1）。

### Step 7 落盘最终 plan + Handoff
1. 汇总 `outputs/experiment-design/plan.md`：假设、baseline 表、消融表、评分标准、统计协议、预算、预实验结论、风险登记。
2. 写 `outputs/experiment-design/HANDOFF.md`（human_approved=false 待人工）。

## 硬规则

- **R0/R7**：预实验结果必须真实，禁止编造或"推断合理值"。
- **R1**：每次搜索/执行/Review 调用写 provenance.log（失败标 null）。
- **R2**：baseline 代码 URL、引用必须真实，禁编造。
- **R6**：最终 plan 需人工确认才放行（human_approved 置 true 后下游方可启动）。
- **R8**：严格按本 Spec 设计，不擅自加实验类型；新需求记 `decisions/OPEN-DECISIONS.md`。
- **R9**：对比方法优先从 `$RESEARCH_PIPELINE_ROOT/references/` 取。
- **R10**：任何不可行/矛盾显式上报，不沉默通过。

## 输出

- `outputs/experiment-design/plan.md`（最终方案）
- `outputs/experiment-design/review.md`（独立评审结论）
- `outputs/experiment-design/pre-exp/`（小批量预实验产物，含 config.yaml / run_prompt.md / 结果）
- `outputs/experiment-design/HANDOFF.md`（交接信封）

## 完成判定

plan.md + review.md 落盘 + HANDOFF 写完（human_approved=false）+ 无未上报偏差 → 交人工门禁（R6）。人工确认后置 `human_approved: true`，下游 `code-execution` 方可启动。

---

## 可执行脚本（scripts/）

- `scripts/pilot_run.py`：Step 6 小批量预实验验证循环的**真实执行器**。读 `pre-exp/config.json`（字段：`data` / `target` / `n_sample` / `seed`），本地小批量跑 baseline，返回 metrics JSON 验证「能否跑通 + 方向是否正向」。纯 NumPy 多数类基线，**零第三方依赖**即可跑；检测到 scikit-learn 时自动升级更强基线。
  ```bash
  python skills/experiment-design/scripts/pilot_run.py --spec outputs/experiment-design/pre-exp/config.json --out outputs/experiment-design/pre-exp/pilot_metrics.json
  ```
- 该脚本把 Step 6 的「探索子 Agent 预实验」落成可审计的真实产物；每次执行写 provenance（R1），失败标 null 不补造（R0）。
