# biomodel-agent

AI **生物系统数学建模 Agent**：能够从生物文献文本中

1. **自动复现** 文献中已有的数学模型（ODE / PDE）；
2. **自发构建（hypothesis-driven）** 新的数学模型。

是一个课程作业项目。整套系统由「LLM 驱动的智能体 + 可验证的数值求解引擎 +
结构化模型中间表示（Model IR）」组成。

---

## 1. 快速开始

依赖由项目自带（`uv` 管理的 `.venv`）。需要 Python ≥ 3.12。

### 1.1 无 API 演示（推荐先跑这个）

不依赖任何大模型接口，自动复现 `data/test_model.txt` 里的
Lotka-Volterra 模型，做数值模拟并生成报告：

```bash
.venv\Scripts\python.exe main.py --demo
```

产物生成在 `output/` 下：

| 产物 | 说明 |
|---|---|
| `output/model_ir_lotka_volterra_...__reproduce.json` | 提取的模型 IR |
| `output/simulation_lotka_volterra_...__reproduce.json` | 数值解 |
| `output/simulation_lotka_volterra_...__reproduce.png` | 轨迹图 |
| `output/reports/report_lotka_volterra_reproduce.md` | 复现报告 |

### 1.2 LLM 交互模式

需要设置环境变量并联网：

```bash
# Windows PowerShell
$env:USTC_LLM_API_KEY='sk-xxxx'
$env:BIOMODEL_MODEL='deepseek-v4-flash-ascend'   # 可选，默认就是这个

.venv\Scripts\python.exe main.py --data data\self_derived_chemostat.txt
```

不给 `--data` 则进入对话模式，直接描述你想要复现/构建的模型或给文件路径。

> 说明：`BIOMODEL_MODEL` 可以换成任意 OpenAI 兼容的模型名；接口地址在
> `main.py` 中默认为 USTC 端点 `https://api.llm.ustc.edu.cn/v1`。

### 支持 PDF 文献 📄

`--data` 直接支持 `.pdf`（自动解析为文本，可处理**两栏学术排版**），也支持
`.txt` / `.md` / `.tex`：

```bash
$env:USTC_LLM_API_KEY='sk-xxx'
.venv\Scripts\python.exe main.py --data "data\我的论文.pdf"
```

> PDF 解析需要 `pymupdf`（已列入 `pyproject.toml`）。如果环境里没装，先执行：
> `uv pip install --python .venv/Scripts/python.exe pymupdf`
> 然后照常运行即可。

---

## 2. 系统架构

```
                    ┌──────────────────────────────────────────────┐
                    │               用户 / 研究者                    │
                    └───────────────┬──────────────────────────────┘
                                    │ 自然语言 / 文献文件路径
                                    ▼
  ┌───────────────────────────────────────────────────────────────┐
  │                        main.py (CLI 入口)                       │
  │   --demo  无 API 演示   |  交互模式 + --data 指定文献             │
  └───────────────┬───────────────────────────────────────────────┘
                  ▼
  ┌───────────────────────────────────────────────────────────────┐
  │                        agent.py (LLM 循环)                     │
  │   调用 DeepSeek，解析其 tool_calls，驱动下面 4 个工具            │
  └───────────────┬───────────────────────────────────────────────┘
                  ▼
  ┌───────────────────────────────────────────────────────────────┐
  │ tools.py  ──  agent 的工具面（LLM 可调用）                      │
  │   read_text     读取文献正文（支持 .txt 与 .pdf 自动解析）               │
  │   save_model_ir 保存模型中间表示 (Model IR)                     │
  │   simulate_model 数值求解 ODE/PDE 并出图                       │
  │   save_report    写 Markdown 建模报告                           │
  └───────┬──────────────────────────────┬────────────────────────┘
          │                              │
          ▼                              ▼
  ┌────────────────┐           ┌──────────────────────────────┐
  │ model_ir.py    │           │ simulate.py (数值引擎)        │
  │ Model IR 契约   │           │  ODE: scipy.solve_ivp(RK45)  │
  │ (ODE/PDE schema)│           │  PDE: 有限差分 + 方法线 (BDF) │
  └────────────────┘           │  sympy 安全解析方程表达式      │
                              └──────────────────────────────┘
```

### 各模块职责

| 文件 | 职责 |
|---|---|
| `prompts.py` | 系统提示词：定义「复现」与「自发构建」两种工作模式的完整流程与守则 |
| `model_ir.py` | **Model IR 契约**。统一描述 ODE/PDE 模型（变量、参数、方程、时间/空间域、初值/边值、来源、假设、缺失信息）。LLM 产出 IR，数值引擎消费 IR。 |
| `simulate.py` | **数值引擎**。把 Model IR 翻译成可求解的系统：ODE 用 `solve_ivp`；PDE 用中心差分 + method-of-lines（`D*d2u/dx2` 自动识别为扩散项）。用 `sympy` 把方程文本安全解析成数值函数，**不使用 `exec`**。 |
| `pdf_utils.py` | **PDF → 文本**。用 `pymupdf` 解析 `.pdf`，按行带聚簇正确处理两栏学术排版。`read_text` 遇到 `.pdf` 时自动调用它。 |
| `tools.py` | agent 可调用的 4 个工具及其 OpenAI function-calling schema（`read_text` 支持 .txt/.pdf）。 |
| `agent.py` | LLM 工具调用循环（`run_agent`）。 |
| `main.py` | CLI 入口：`--demo` 与交互模式。 |

### Model IR 结构（核心契约）

一份 Model IR 是一份包含以下字段的 JSON：

```jsonc
{
  "model_name": "...",
  "model_type": "ODE | PDE | ...",
  "description": "生物机制的自然语言描述",
  "variables":   [{ "name", "description", "unit" }],
  "parameters":  [{ "name", "value_known", "value", "unit" }],
  "equations":   [{ "variable", "expression" }],      // 如 "a*X - b*X*Y"
  "domain":      { "t_start", "t_end", "spatial": [{ "x_start", "x_end", "n_points" }] },
  "initial_conditions": [{ "variable", "value_known", "value" | "expr" }],
  "boundary_conditions": [{ "variable", "boundary", "type", "value" }],
  "origin": { "mode": "reproduce|self_derived", "source_text", "confidence", "assumptions" },
  "missing_information": ["..."]
}
```

- 对 **复现**：`origin.mode = "reproduce"`，只使用原文明确信息，缺失值一律
  `value_known: false` 并登记 `missing_information`。
- 对 **自发构建**：`origin.mode = "self_derived"`，在 `assumptions` 中显式列出
  建模假设（评分关键），并用 `simulate_model` 验证假设下的定性行为。

---

## 3. 如何实现「复现文献模型」

以 `data/fisher_kpp_pde.txt`（Fisher-KPP 反应扩散方程）为例，agent 的流程：

1. `read_text` 读取文献 → 识别出这是 PDE（`du/dt = D·uxx + r·u(1-u)`）。
2. `save_model_ir(tag="reproduce")` 保存 IR：变量 `u`、参数 `D=0.2, r=1.0`、
   空间域 `[0,40]`、初值高斯峰、Neumann 边值。
3. `simulate_model(tag="reproduce")` → `solve_ivp` 求解 → 得到传播波。
4. 报告中对比：传播波前速度 ≈ `2√(D·r) ≈ 0.894`，与理论一致 → **复现成功**。

`sympy` 会把 IR 里的文本方程解析为数值函数，因此 agent 输出什么样的方程文本
`simulate.py` 都能安全求值，只要符号与 `variables` 一致。

---

## 4. 如何实现「自发构建模型」

以 `data/self_derived_chemostat.txt`（恒化器两种菌竞争，**只描述机制，没有方程**）
为例：

1. `read_text` 提取机制：两种菌 + 单一限制营养物 `S`；Monod 饱和生长；稀释速率 `D`。
2. 显式写出假设并据此推导方程：

   ```
   dA/dt = μA(S)·A - D·A        dS/dt = D·(S_in - S) - ... ·consumption
   dB/dt = μB(S)·B - D·B
   μi(S) = μmax_i · S / (Ki + S)     (Monod)
   ```

3. `save_model_ir(tag="self_derived")`，`assumptions` 记录：Monod 生长、完全混合、
   恒定稀释、无死亡（忽略维持代谢）……
4. `simulate_model` 用合理参数验证：不同 `μ/K` 组合下 → 共存稳态 或 单一菌占优，
   对照文献“哪种参数域共存”的结论。
5. `save_report` 写完整派生报告。

> 自发构建的关键守则（已在 `prompts.py` 强制）：**每一项抽象都要落到
> `origin.assumptions`**，让模型“假设驱动”的属性可被审查。

---

## 5. 数值引擎要点（simulate.py）

- **ODE**：`scipy.integrate.solve_ivp`（RK45），支持任意维数、参数代入、初值。
- **PDE（一维反应扩散）**：方法线。把 `D*d2u/dx2`（写成 `D * d2u/dx2`、`D*u_xx`
  或 `D*uxx`）识别为扩散项，用中心差分 `(u_{k+1}-2u_k+u_{k-1})/dx²` 离散，
  得到半离散常微分系统后用 `solve_ivp`（BDF 刚性求解器）积分。
- **安全求值**：方程一律经 `sympy.sympify` 解析，绝不 `exec`，避免任意代码注入。
- **输出**：每跑一个模型在 `output/` 生成 `simulation_<slug>__<tag>.json`（数据）
  与 `.png`（轨迹/热图），同名模型不同 tag 不互相覆盖。

### 已知约束
- PDE 目前支持**一维**反应扩散类；多维空间、隐式求解器边界条件处理为后续扩展。
- 若参数/初值缺数值，引擎会明确报错，提示补齐，而非伪造数据。

---

## 6. 目录结构

```
biomodel_agent/
├── main.py          # CLI 入口（--demo / 交互，--data 支持 .txt/.pdf）
├── agent.py         # LLM 工具循环
├── prompts.py       # 系统提示词（两种工作模式 + 守则）
├── model_ir.py      # Model IR 契约（ODE/PDE schema）
├── simulate.py      # 数值引擎（ODE/PDE 求解 + 绘图）
├── pdf_utils.py     # PDF → 文本解析（pymupdf，两栏排版）          ▲ 新增
├── tools.py         # agent 工具面 + function-calling schema
├── pyproject.toml   # 依赖与元数据
├── data/            # 文献样本
│   ├── test_model.txt       # Lotka-Volterra（复现用，带方程）
│   ├── fisher_kpp_pde.txt   # Fisher-KPP（复现 PDE）
│   ├── self_derived_chemostat.txt  # 恒化器竞争（自发构建用，只有机制）
│   └── test_two_column.pdf  # 两栏 PDF 示例（验证 PDF 解析链路）
└── output/          # agent 产出：IR、模拟 JSON/PNG、reports/（已 gitignore）
```

---

## 7. 复现完整运行步骤

```bash
# 1) 确保依赖
uv pip install --python .venv/Scripts/python.exe \
    "numpy==2.2.6" "scipy==1.15.2" "matplotlib==3.9.4" "sympy" "openai" pymupdf

# 2) 无 API 演示
.venv\Scripts\python.exe main.py --demo

# 3) 用 LLM 处理一篇文献（复现 PDE，.txt）
$env:USTC_LLM_API_KEY='sk-xxx'
.venv\Scripts\python.exe main.py --data data\fisher_kpp_pde.txt

# 4) 用 LLM 从机制文本自发构建模型（.txt）
.venv\Scripts\python.exe main.py --data data\self_derived_chemostat.txt

# 5) 直接处理 PDF 文献（两栏排版也能解析）
.venv\Scripts\python.exe main.py --data "data\test_two_column.pdf"
```

---

## 8. 依赖说明

| 包 | 用途 | 注意 |
|---|---|---|
| `openai` | 调用 DeepSeek 兼容接口 | ≥3.8 |
| `numpy` | 数值数组 | 固定 **2.2.6**（2.5.3 在部分机器上有 DLL 兼容问题） |
| `scipy` | `solve_ivp` 求解器 | 匹配 numpy 的版本 |
| `matplotlib` | 出图 | 用 **<3.10**（新版本 `_backend_agg` 二进制与本机不兼容） |
| `sympy` | 方程符号解析/安全求值 | ≥1.14 |
| `pymupdf` | 解析 `.pdf` 文献为文本 | ≥1.24（`read_text` 遇到 PDF 时使用） |

> 由于本机部分预编译二进制扩展存在加载问题，版本做了**固定**而非随最新——
> 见 `pyproject.toml` 与上文“已知约束”。
