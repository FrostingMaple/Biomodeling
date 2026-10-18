# biomodel-agent

AI **生物系统数学建模 Agent**：能够从生物文献文本中

1. **自动复现** 文献中已有的数学模型（ODE / PDE）；
2. **自发构建（hypothesis-driven）** 新的数学模型。

是一个课程作业项目。整套系统由「LLM 驱动的智能体 + 可验证的数值求解引擎 +
结构化模型中间表示（Model IR）」组成。

> [!IMPORTANT]
> **本项目是团队合作项目。** 向 GitHub 上传、提交或合并代码时，必须使用本人的 GitHub 账号并以合作贡献者身份进行。请勿直接向主分支推送，也不要使用强制推送、覆盖提交等方式破坏团队其他成员的工作成果。

## 参与贡献

所有改动应先从最新主分支创建独立分支，再通过 Pull Request 申请合并。提交 PR 前请同步上游、运行测试，并在描述中说明改动范围、验证方式和潜在影响。主分支只接受经过审查的合并请求。

- 禁止直接向 `main` / `master` 推送；
- 禁止未经沟通覆盖、回退或删除他人的提交与文件；
- 禁止冒用他人身份或使用他人的 GitHub 凭据；
- 发现冲突时应先沟通，确认双方意图后再解决。

完整的身份配置、分支命名、提交、Pull Request、审查和冲突处理要求见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 1. 快速开始

首次运行推荐直接使用项目自带的一键入口。它会检查项目内 `.venv`：若环境不存在，则自动创建 **Python 3.12 专属环境**并安装全部依赖；优先使用 `uv`，没有 `uv` 时回退到 `py -3.12` + `pip`。

> **Python 版本说明**：推荐 Python 3.12（默认一键脚本会使用它）。Python 3.14 也已验证可通过，但需要使用放宽后的绘图依赖（`matplotlib>=3.11`）；可执行 `.\bootstrap.ps1 -PythonVersion 3.14 -Recreate` 创建 3.14 环境，或直接执行 `.\run.ps1 -PythonVersion 3.14 --demo`（已有 3.12 `.venv` 时需加 `-Recreate`）。

```powershell
.\run.ps1 --demo
```

> 如果 PowerShell 禁止执行本地脚本，可使用：
> `powershell -ExecutionPolicy Bypass -File .\run.ps1 --demo`

也可以只初始化环境、不立即运行：

```powershell
.\bootstrap.ps1
```

只想检查环境是否齐全、不安装任何依赖：

```powershell
.\bootstrap.ps1 -CheckOnly
```

若目录中已有一个版本不符或损坏的 `.venv`，脚本会停止并提示，而不会静默删除环境。确认要重建时执行：

```powershell
.\bootstrap.ps1 -Recreate
```

### 1.1 无 API 演示（推荐先跑这个）

不依赖任何大模型接口，自动用**内置的 Lotka-Volterra 模型**跑通"复现 → 模拟 →
报告"完整流程，快速验证数值引擎是否工作：

```powershell
.\run.ps1 --demo
```

产物生成在 `output/` 下：

| 产物 | 说明 |
|---|---|
| `runs/models/model_ir_lotka_volterra_...__reproduce.json` | 提取的模型 IR |
| `runs/simulation/simulation_lotka_volterra_...__reproduce.json` | 数值解 |
| `runs/simulation/simulation_lotka_volterra_...__reproduce.png` | 轨迹图 |
| `runs/reports/report_lotka_volterra_reproduce.md` | 复现报告 |

### 1.2 LLM 交互模式

需要设置环境变量并联网：

```bash
# Windows PowerShell
$env:USTC_LLM_API_KEY='sk-xxxx'
$env:BIOMODEL_MODEL='deepseek-flash'   # 可选，默认就是这个

.\run.ps1 --data data\test.pdf
```

不给 `--data` 则进入对话模式，直接描述你想要复现/构建的模型或给文件路径。

> 说明：默认使用中国科学技术大学大模型公共服务平台（OpenAI 兼容接口），
> 默认模型为 `deepseek-flash`，默认端点为 `https://api.llm.ustc.edu.cn/v1`。
> `BIOMODEL_MODEL` 和 `BIOMODEL_BASE_URL` 可用于覆盖默认模型与端点。

#### 可选：使用 DeepSeek 官方接口

```powershell
$env:BIOMODEL_PROVIDER='deepseek'
$env:DEEPSEEK_API_KEY='sk-xxxx'
# 可选；默认使用 deepseek-chat
$env:BIOMODEL_MODEL='deepseek-chat'

.\run.ps1 --data data\test.pdf
```

### 支持 PDF 文献 📄

`--data` 直接支持 `.pdf`（自动解析为文本，可处理**两栏学术排版**），也支持
`.txt` / `.md` / `.tex`：

```bash
$env:USTC_LLM_API_KEY='sk-xxx'
.\run.ps1 --data "data\我的论文.pdf"
```

> PDF 解析需要 `pymupdf`（已列入初始化脚本和 `pyproject.toml`）。首次初始化环境时会自动安装；如果怀疑依赖缺失，可先检查并补齐：
> `.\bootstrap.ps1 -CheckOnly`
> `.\bootstrap.ps1`
> 然后照常运行即可。

---

## 1.3 开发验证（运行测试）

项目自带基于标准库 `unittest` 的最小回归测试，不需要额外测试依赖，也不会调用任何 LLM API：

```powershell
.\bootstrap.ps1 -CheckOnly
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

测试覆盖：

- ODE 数值求解与结果落盘；
- 缺少参数、初值、方程时的错误路径；
- 工具层 JSON 修复与错误返回；
- 无 API 的 `--demo` 端到端 smoke test。

### Model IR 业务校验

`save_model_ir` 和 `simulate_model` 都会在进入文件写入或数值求解前调用
`validate_model_ir()`。校验失败时，错误会作为工具结果返回给 Agent，便于 Agent
自动修正，而不是等到求解阶段才失败。

校验内容包括变量/参数/方程引用关系、初值与空间域、PDE 网格、边界条件和
`origin` 字段。合法 IR 可正常保存；不完整但结构合法的 IR 允许保存，并在模拟时
给出明确的缺失信息。

### Agent 调用可靠性

交互模式支持以下可选环境变量：

| 变量 | 默认值 | 作用 |
|---|---:|---|
| `BIOMODEL_REQUEST_TIMEOUT` | `120` | 单次 LLM 请求超时秒数 |
| `BIOMODEL_MAX_RETRIES` | `2` | OpenAI SDK 网络重试次数 |
| `BIOMODEL_MAX_TOOL_ROUNDS` | `40` | 单轮 Agent 最大工具调用循环数 |
| `BIOMODEL_MAX_TOTAL_TOKENS` | `200000` | 单轮会话累计 Token 保护阈值；设为 `0` 可关闭 |

网络超时与瞬时错误由 OpenAI SDK 负责重试；工具调用、错误和 Token 统计会触发
会话持久化回调，Agent 异常时会保存当前会话并打印可读错误。

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
  │   调用 OpenAI 兼容 LLM（默认 USTC），驱动下面 4 个工具           │
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

当文献给出完整方程（如 Fisher-KPP 反应扩散 `du/dt = D·uxx + r·u(1-u)`）时，
agent 的流程：

1. `read_text` 读取文献 → 识别出这是 PDE 还是 ODE，抽出各变量、参数、方程。
2. `save_model_ir(tag="reproduce")` 保存 IR：变量 `u`、参数 `D, r`、空间域、
   初值、边值。
3. `simulate_model(tag="reproduce")` → `solve_ivp` 求解 → 得到传播波。
4. 报告中对比理论指标（如波速 ≈ `2√(D·r)`）→ **复现成功**。

`sympy` 会把 IR 里的文本方程解析为数值函数，因此 agent 输出什么样的方程文本
`simulate.py` 都能安全求值，只要符号与 `variables` 一致。

---

## 4. 如何实现「自发构建模型」

当文献**只描述机制、没有给出方程**时（例如 CRISPR–Cas9 论文描述"RNA 引导的
双链 DNA 切割"这类生化机制，`data/test.pdf` 即是这类），agent 的流程：

1. `read_text` 提取机制：识别生物实体与相互作用（底物、酶、产物、速率过程）。
2. 显式写出假设并据此推导方程（例如酶促切割可假设 Michaelis–Menten 动力学）：

   ```
   dE/dt = ...        dC/dt = k_on·E·S - (k_off + k_cat)·C
   dS/dt = -k_on·E·S + k_off·C        dP/dt = k_cat·C
   ```

3. `save_model_ir(tag="self_derived")`，把每一步抽象用 `assumptions` 记录。
4. `simulate_model` 用合理参数做数值验证，判断定性行为是否符合文献描述。
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

### PDE 当前能力与已知约束

当前求解器支持：

- **一维单空间区间**的反应扩散 PDE；
- **Dirichlet** 边界：边界节点固定为 `boundary_conditions.value`；
- **Neumann** 边界：`boundary_conditions.value` 表示边界处的 `du/dx`；
- 未声明边界条件时使用零通量近似；
- 多空间区间、二维或三维空间会明确报错，不会静默截断或忽略。

> Neumann 符号约定：边界值表示 `du/dx`。因此左边界负值通常表示向域内输入通量，
> 正值表示向外梯度；具体方向应结合模型定义解释。

### 未来 PDE 扩展路线

以下能力当前**尚未实现**，作为后续扩展目标：

- 二维/三维 PDE 与多维空间网格；
- 多空间区间、复杂几何与非均匀网格；
- 张量/各向异性扩散；
- Robin 边界、周期边界和时变边界条件；
- 适用于高维问题的隐式、有限体积或有限元求解器；
- 多维结果可视化与更完整的边界条件组合验证。

### 其他已知约束

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
├── bootstrap.ps1    # 首次初始化：创建 .venv 并安装全部依赖
├── run.ps1          # 一键入口：环境不存在时先初始化，再运行 main.py
├── pyproject.toml   # 依赖与元数据
├── data/            # 你放入的待建模文献（.pdf / .txt）
│   └── test.pdf     # 示例：CRISPR–Cas9 论文（自发构建用：只有机制、无方程）
└── output/          # agent 产出：IR、模拟 JSON/PNG、reports/（已 gitignore）
```

---

## 7. 复现完整运行步骤

```powershell
# 1) 创建或检查项目专属环境，并安装全部依赖
.\bootstrap.ps1

# 2) 无 API 演示（内置 Lotka-Volterra，验证引擎）
.\run.ps1 --demo

# 3) 用 LLM 处理你的文献（支持 .txt / .pdf，自动解析）
$env:USTC_LLM_API_KEY='sk-xxx'
.\run.ps1 --data data\test.pdf

# 4) 换成任意你自己的文献
.\run.ps1 --data "data\你的文献.pdf"
```

> `bootstrap.ps1` 默认按 Python 3.12 安装兼容版本：`numpy==2.2.6`、
> `scipy==1.15.2`、`matplotlib==3.9.4`，并安装 `sympy`、`openai`、`pymupdf`。
> 这样可以避开 README 中记录的本机预编译二进制兼容问题。
>
> 使用 `-PythonVersion 3.14` 时，脚本会改用 Python 3.14 可安装的
> `numpy>=2.5.4`、`scipy>=1.18.1`、`matplotlib>=3.11` 组合。

---

## 8. 依赖说明

| 包 | 用途 | 注意 |
|---|---|---|
| `openai` | 调用 OpenAI 兼容接口（默认 USTC；可切 DeepSeek） | ≥3.8 |
| `numpy` | 数值数组 | Python 3.12 用 **2.2.6**；Python 3.14 用 **>=2.5.4** |
| `scipy` | `solve_ivp` 求解器 | Python 3.12 用 **1.15.2**；Python 3.14 用 **>=1.18.1** |
| `matplotlib` | 出图 | Python 3.12 用 **<3.10**；Python 3.14 用 **>=3.11** |
| `sympy` | 方程符号解析/安全求值 | ≥1.14 |
| `pymupdf` | 解析 `.pdf` 文献为文本 | ≥1.24（`read_text` 遇到 PDF 时使用） |

> 由于本机部分预编译二进制扩展存在加载问题，版本做了**固定**而非随最新——
> 见 `pyproject.toml` 与上文“已知约束”。

