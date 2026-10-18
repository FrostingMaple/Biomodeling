# 整合设计

## 1. 目标

将两个原本独立运行的项目组合成一条流水线：

```text
证据化文献提取（A） -> 统一 Model IR（B） -> 数值仿真 -> 报告
```

原 A、B 项目目录均未修改。本工程保存的是独立整合副本。

## 2. 分层映射

| 原项目 | 原位置 | 整合后位置 | 职责 |
|---|---|---|---|
| A | `bio_variable_extractor/src/bio_variable_extractor` | `src/biomodeling/literature` | 文献读取、DOI、DOCX/JATS/PDF、证据块、变量与参数提取、校验、交叉表 |
| B | `Biomodeling-main/model_ir.py`、`simulate.py` | `src/biomodeling/modeling` | Model IR、ODE/PDE 求解、图形和数值摘要 |
| B | `Biomodeling-main/agent.py`、`tools.py`、`prompts.py`、`main.py` | `src/biomodeling/agent` | LLM 工具循环、Agent 工具面、交互入口 |
| 新增 | - | `src/biomodeling/contracts` | A 输出到 B 输入的转换与 JSON Schema |
| 新增 | - | `src/biomodeling/cli.py` | 统一命令行入口 |

## 3. 统一契约

A 的 extraction JSON 仍然是证据层主格式。它新增两个可选字段：

```json
{
  "model_ir": {},
  "model_ir_seed": {}
}
```

### `model_ir`

用于携带完整 B Model IR。适用于：

- 论文已经给出完整方程；
- Agent 已经完成模型构建；
- 需要保证 A 的证据与 B 的可求解模型一一对应。

转换时优先使用该字段。

### `model_ir_seed`

用于覆盖自动映射生成的部分字段。适用于：

- 只有方程、没有初值；
- 只有时间域或空间域；
- 希望把 Agent 已确认的字段固定下来，其余字段继续走自动映射。

## 4. 自动映射规则

`src/biomodeling/contracts/extraction_to_model_ir.py` 执行保守转换：

1. 文档标题、DOI、来源路径写入 `origin.source_text`。
2. `study_profile.model_type` 归一化为 `ODE`、`PDE`、`stochastic` 或 `unknown`。
3. 状态变量候选优先来自 equation relationship 的 `to` 目标，其次来自 dependent/derived 变量。
4. 参数候选来自 role 为 `parameter` 或 `constant` 的变量。
5. `value_or_range` 只有在恰好包含一个数值时才写入参数值或初值。
6. 只有带明确导数记号的 relationship 才转换为微分方程。
7. 代数关系保留在 `conversion.algebraic_relationships`，不会伪装成 ODE。
8. `unresolved`、转换警告和缺失数值合并到 `missing_information`。
9. A 的 `block_id`、页码、章节和引用写入 Model IR 的 `evidence` 字段。

## 5. 可运行性判定

适配器调用 B 的 `validate_model_ir(..., for_simulation=True)`，并设置：

```json
{
  "conversion": {
    "model_ready": true
  }
}
```

只有以下条件同时成立时才为 `true`：

- `model_type` 是 ODE 或 PDE；
- 状态变量非空；
- 每个状态变量都有方程；
- 每个参数都有单一数值；
- 每个状态变量都有可用初值；
- 时间域合法，PDE 还需要空间域和边界条件。

不满足时仍可输出草稿 Model IR，但 `model_ready=false`，且不得直接模拟。

## 6. 统一 CLI

```text
biomodeling literature ...   # A 的原有命令
biomodeling to-model-ir ...  # A -> B 转换
biomodeling validate-model   # B Model IR 校验
biomodeling simulate         # B 数值仿真
biomodeling demo             # B 无 API 演示
biomodeling agent ...        # B 的 LLM 交互模式
```

为兼容 A 的原命令，也可以省略 `literature` 前缀，例如：

```text
biomodeling prepare ...
biomodeling validate ...
biomodeling render ...
```

## 7. Agent 集成

B 的 Agent 新增两个工具：

- `prepare_literature(source, out_dir)`：调用 A 的文献准备层，生成 `source.json` 与 `chunks.jsonl`。
- `convert_extraction_to_model_ir(extraction_path, output_path, strict)`：调用统一契约层，返回 `model_ready`、警告与仿真校验结果。

Agent 的提示词已改为优先使用文献准备层，并保留原有 Model IR、仿真和报告工具。

## 8. 后续扩展点

1. 为 Model IR 增加正式的 `schema_version`。
2. 在 `model_ir_seed` 中加入更多 PDE 空间域模板。
3. 增加从文字方程到 SymPy 表达式的自动规范化。
4. 增加单位换算和量纲校验。
5. 为每次运行增加 `run_manifest.json`，记录输入哈希、依赖版本和模型名。
6. 将 A 的证据块直接渲染到 B 的最终报告中。
