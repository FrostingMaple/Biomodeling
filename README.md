# Biomodeling 整合版

本目录将两个原有项目整合为一个统一工程，同时保留原项目目录不变：

- A：`bio_variable_extractor`，负责文献准备、证据化变量/参数提取、校验和变量交叉表。
- B：`biomodel-agent`，负责 Model IR、ODE/PDE 数值求解、LLM Agent 和建模报告。

## 项目来源与分支定位

- B（`biomodel-agent`）的来源仓库为 [FrostingMaple/Biomodeling](https://github.com/FrostingMaple/Biomodeling)。
- 统合后的本项目记为 B 的整合分支：`integration/parameter-extraction`。
- 该分支在 B 的建模能力基础上，整合 A 的文献参数提取、变量交叉表与统一建模链路。
- 该分支不替代 B 的上游仓库，也不得覆盖或改写 B 的既有历史；接入 Git 时应使用上述正式分支名，不直接在主分支开发。

统一后的主链路为：

```text
文献 / DOI
  -> A: source.json + chunks.jsonl
  -> A: extraction.json（证据化变量与关系）
  -> 统一契约: extraction -> Model IR
  -> B: Model IR 校验
  -> B: ODE/PDE 仿真 JSON + PNG
  -> Markdown 联合报告
```

## 目录结构

```text
Biomodeling-合并尝试/
├─ pyproject.toml
├─ run.ps1
├─ bootstrap.ps1
├─ src/
│  └─ biomodeling/
│     ├─ literature/          # 项目 A
│     │  ├─ cli.py
│     │  ├─ extraction.py
│     │  ├─ validation.py
│     │  ├─ doi.py
│     │  ├─ rendering.py
│     │  ├─ lexicons/
│     │  ├─ prompts/
│     │  └─ templates/
│     ├─ modeling/            # 项目 B 的模型与求解层
│     │  ├─ model_ir.py
│     │  ├─ simulate.py
│     │  └─ pdf_utils.py
│     ├─ agent/               # 项目 B 的 Agent 层
│     │  ├─ agent.py
│     │  ├─ main.py
│     │  ├─ prompts.py
│     │  └─ tools.py
│     ├─ contracts/           # 两项目统一契约
│     │  ├─ extraction.schema.json
│     │  ├─ model_ir.schema.json
│     │  └─ extraction_to_model_ir.py
│     └─ cli.py
├─ examples/
│  ├─ literature/             # A 的原始样例
│  ├─ modeling_test.pdf       # B 的原始样例文献
│  └─ model_ready_extraction.json
├─ tests/
├─ docs/
└─ runs/                      # 统一运行产物
```

> [!IMPORTANT]
> **测试文献不提交到 Git。** `examples/modeling_test.pdf`、`examples/literature/sample_paper.md` 和 `examples/literature/sample_pdf.pdf` 仅用于本地验证，已在 `.gitignore` 中排除。克隆仓库后如需运行依赖这些文件的测试，请从团队共享位置获取并放回原路径；禁止使用 `git add -f` 强制提交。

## 环境与快速开始

推荐 Python 3.12：

```powershell
.\bootstrap.ps1
.\run.ps1 --help
```

如果不希望安装项目，也可以直接设置 `PYTHONPATH`：

```powershell
$env:PYTHONPATH = "src"
py -m biomodeling --help
```

如果本机已有可用环境，也可以直接运行测试：

```powershell
$env:PYTHONPATH = "src"
py -m unittest discover -s tests -v
```

## 统一命令

### 1. 文献准备（A）

```powershell
.\run.ps1 literature prepare examples\literature\sample_paper.md `
  --out runs\demo\source.json `
  --chunks-out runs\demo\chunks.jsonl
```

也可以处理 DOI：

```powershell
.\run.ps1 literature prepare 10.1371/journal.pcbi.1007486 `
  --out runs\demo\doi_source.json `
  --chunks-out runs\demo\doi_chunks.jsonl
```

### 2. 校验与渲染 A 的结果

```powershell
.\run.ps1 literature validate runs\demo\extraction.json --source runs\demo\source.json
.\run.ps1 literature render runs\demo\extraction.json `
  --source runs\demo\source.json `
  --out runs\demo\variable_crosswalk.md `
  --final
```

### 3. A 输出转换为 B 输入

```powershell
.\run.ps1 to-model-ir runs\demo\extraction.json `
  --out runs\demo\model_ir.json `
  --mode reproduce
```

严格模式：

```powershell
.\run.ps1 to-model-ir runs\demo\extraction.json `
  --out runs\demo\model_ir.json `
  --strict
```

`--strict` 仅在模型具备以下条件时成功：

- 有可求解的 ODE/PDE 方程；
- 所有状态变量都有方程；
- 参数有单一数值；
- 初值有单一数值；
- 时间域可确定。

否则会明确失败，不会伪造缺失数据。

### 4. 校验与仿真 Model IR

```powershell
.\run.ps1 validate-model runs\demo\model_ir.json --simulation
.\run.ps1 simulate runs\demo\model_ir.json --output-dir runs\demo\simulation
```

### 5. 无 API 演示与 LLM Agent

```powershell
.\run.ps1 demo
.\run.ps1 agent --data examples\modeling_test.pdf
```

LLM Agent 需要设置对应环境变量，详见 `.env.example` 和 `docs/modeling_README.md`。

## A 输出与 B 输入的统一方式

统一格式仍是 A 的 evidence extraction JSON，但新增两个可选顶层字段：

```json
{
  "model_ir": {},
  "model_ir_seed": {}
}
```

- `model_ir`：完整的 B Model IR。存在时直接作为转换目标，适合“模型已经明确”的情况。
- `model_ir_seed`：只覆盖部分 Model IR 字段，适合 Agent 已知方程、时间域或初值，但仍有部分信息缺失的情况。

如果两者都不存在，适配器会保守地自动映射：

| A 字段 | B 字段 | 行为 |
|---|---|---|
| `document` / `study_profile` | `model_name` / `model_type` | 生成名称并归一化模型类型 |
| `variables[role=dependent]` | `variables` | 映射为状态变量候选 |
| `variables[role=parameter]` | `parameters` | 尝试解析单一数值 |
| `value_or_range` | `initial_conditions` | 仅单一数值可作为初值 |
| `relationships[type=equation]` | `equations` | 只有带明确导数符号的关系才自动映射 |
| `unresolved` | `missing_information` | 汇总未解决问题 |
| `evidence` | `evidence` | 保留 `block_id`、页码、章节和原文引用 |

适配器还会写入：

```json
{
  "conversion": {
    "model_ready": false,
    "warnings": [],
    "algebraic_relationships": [],
    "validation_for_simulation": {}
  }
}
```

`model_ready=false` 表示该 Model IR 可以继续由 Agent 或人工补全，但不能直接仿真。

## 端到端验证样例

`examples/model_ready_extraction.json` 同时包含：

- A 格式的变量、参数、关系、证据和 review metadata；
- 一个完整的 B 格式 `model_ir`。

可直接验证：

```powershell
.\run.ps1 to-model-ir examples\model_ready_extraction.json `
  --out runs\integration_demo\model_ir.json `
  --strict

.\run.ps1 validate-model runs\integration_demo\model_ir.json --simulation
.\run.ps1 simulate runs\integration_demo\model_ir.json `
  --output-dir runs\integration_demo\simulation `
  --tag integration
```

预期产物：

```text
runs/integration_demo/
├─ model_ir.json
└─ simulation/
   ├─ simulation_unified_lotka_volterra_demonstration__integration.json
   └─ simulation_unified_lotka_volterra_demonstration__integration.png
```

## Agent 新增工具

B 的 Agent 工具面新增：

- `prepare_literature(source, out_dir)`：调用 A 的文献准备层，支持本地文件和 DOI。
- `convert_extraction_to_model_ir(extraction_path, output_path, strict)`：调用统一契约层。

原有工具仍然保留：

- `read_text`
- `save_model_ir`
- `simulate_model`
- `save_report`

## 测试

```powershell
$env:PYTHONPATH = "src"
py -m unittest discover -s tests -v
```

当前测试共 80 项，包括：

- A 的 46 项原有文献处理测试；
- B 的 Model IR、ODE 求解和工具测试；
- 新增的 extraction → Model IR → simulation 集成测试；
- B 的无 API 端到端 smoke test。

## 重要限制

1. **A 的变量提取不自动等于 B 的微分方程模型。** 适配器不会把普通代数关系伪造成 ODE。
2. 自动转换只在能确定数值时填写参数和初值；范围、多个候选值和缺失值都会进入 `missing_information`。
3. 时间域未知时使用 `[0, 1]` 作为草稿占位，并标记 `model_ready=false`；不得将该占位当作科学结论。
4. 原 A、B 项目目录未修改；本目录是独立整合尝试。
5. A 的部分 PDF 能力依赖 `pdfplumber`/`pypdf`，可通过 `pip install -e ".[pdf]"` 安装。
6. LLM 模式需要联网和 API Key；无 API 的 `demo` 与数值仿真不需要 LLM。

