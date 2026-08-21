---
name: code-execution
description: "代码真实执行：读取实验设计plan，三路径真实跑代码（本地Bash / 远程GPU任务文件 / 手动说明），严禁编造结果，全程provenance溯源，产物以JSON落盘供下游分析。"
description_zh: "代码执行（本地/远程/手动三路径，真实执行）"
description_en: "Code execution (local/remote/manual, real execution only)"
version: 1.0.0
tags: [research, code, execution, reproducibility, gpu]
display_name: "代码执行"
visibility: public
---

# 代码执行（code-execution）

你把"跑实验"模块化。核心铁律：**结果必须来自真实执行，禁止模型臆测（R0/R7）**。本阶段只负责把 plan 变成真实数字，不做统计分析与作图（交给 data-analysis）。

## 输入

- 必读：`outputs/experiment-design/plan.md`（含 config、baseline、消融、评分标准、预算）。
- 启动前校验上游 HANDOFF：`human_approved == true`（R4 门禁），否则拒绝启动。
- 可选：`outputs/experiment-design/pre-exp/`（已验证可跑通的小批量配置，直接复用为正式配置基底）。

## 三路径（按算力与可用性选择，R7）

### 路径① 本地 Bash 跑 Python（优先）
- 适用：数据清洗、小模型、CPU 可跑的消融、统计计算、小批量复跑。
- 用受管 Python 建隔离 venv，依赖装入隔离 env（不污染用户环境）：
  - 建：`python -m venv <env>`；装：`venv/bin/pip install <pkg>`；跑：`venv/bin/python script.py`。
- 跑出的指标统一写为 JSON：
  `outputs/code-execution/results/<exp_name>.json`
  结构：`{"exp": "<名>", "metric": "<指标>", "value": <数>, "std": <数>, "n": <int>, "seed": <int>, "runtime_s": <数>, "env": "<venv/commit>"}`
- 每个实验一个 JSON；同实验多次重复可合并为一个文件内的列表。

### 路径② 远程 GPU 任务文件
- 适用：训练 / 大模型 / 需 GPU（本地沙箱无 GPU 时）。
- 生成**自包含任务文件**交远程服务器（如 Seetacloud）：
  - `outputs/code-execution/tasks/<exp_name>/train.py`（或脚本）
  - `outputs/code-execution/tasks/<exp_name>/run.sh`（含激活、安装、启动、日志落盘）
  - `outputs/code-execution/tasks/<exp_name>/requirements.txt`
  - `outputs/code-execution/tasks/<exp_name>/config.yaml`（数据路径占位、超参、种子）
  - 任务文件须自包含：含数据路径占位、训练日志落盘、结果写 JSON。
- 给出提交说明（connect / 提交 / 回捞产物），产物回捞后放入 `results/`。
- 写明远程实例可能释放的风险，关键产物及时本地冷备（复制回 `results/`）。

### 路径③ 手动执行说明（兜底）
- 当环境确实无法自动跑（缺数据权限 / 缺 GPU / 需人工点击）：
  生成 `outputs/code-execution/MANUAL.md`：逐步命令 + 预期产物 + 回传位置 + 验收判据。
- 明确标注"此实验需人工执行，未执行则对应 results 为空"，**不得伪造**（R0）。
- 留给人工跑完回传 JSON 后，本阶段补录 provenance 并放行下游。

## 执行纪律

- 每条结果 JSON 须可追溯到：命令 / 脚本路径 / commit / 数据版本。
- **provenance（R1）**：每次执行向 `$RESEARCH_WORKDIR/provenance.log` 追加一行（命令或脚本、退出码、产物路径、耗时秒）；失败 / 超时标 `"status":"null"`，不补造成功。
- **真实环境（R7）**：禁止"我推断结果是 X"；任何数字须来自真实运行输出。
- **偏差上报（R10）**：NaN / 报错 / 指标异常 / 与预实验方向严重背离，显式写入 results 与 HANDOFF `open_questions`。
- **范围锁定（R8）**：只跑 plan 列出的实验，不擅自加实验；新增走变更流程。

## 输出

- `outputs/code-execution/results/*.json`（真实指标，路径①/②产物）
- `outputs/code-execution/tasks/`（路径②任务文件）
- `outputs/code-execution/MANUAL.md`（路径③，按需）
- `outputs/code-execution/HANDOFF.md`（交接信封，列全部 results 路径）

## 完成判定

plan 中列出的每个实验都有对应 `results/*.json`（真实）或 `MANUAL.md` 说明 + provenance 完整无 null 造假 → 自动进 `data-analysis`。若仅 MANUAL 未回传，HANDOFF 标注 `blockers: 待人工回传` 并暂停（不伪造下游输入）。

---

## 可执行脚本（scripts/）

- `scripts/run_experiment.py`：实现「三路径真实执行」的 router（对应 R7）。
  ```bash
  # 路径① 本地 venv 跑（优先）
  python skills/code-execution/scripts/run_experiment.py --path local \
    --script train.py --config cfg.yaml --out outputs/code-execution/results/run1.json
  # 路径② 远程 GPU 任务包（自包含 train.py + run.sh + config）
  python skills/code-execution/scripts/run_experiment.py --path remote \
    --script train.py --config cfg.yaml --out outputs/code-execution/tasks/run1/
  # 路径③ 手动执行说明
  python skills/code-execution/scripts/run_experiment.py --path manual \
    --script train.py --config cfg.yaml --out outputs/code-execution/MANUAL.md
  ```
- 脚本只做路由与 provenance 记录（R1）：local 非 0 退出码则结果标 `null` 不伪造；remote 仅打包不执行；manual 仅产出说明文档。仅标准库依赖。
