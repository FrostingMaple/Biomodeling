# 联调测试记录

测试日期：2026-10-18  
目标目录：`C:\Users\我的电脑\Documents\ChatGPT\Biomodeling-合并尝试`  
测试解释器：项目 B 原有环境 `.venv\Scripts\python.exe`，Python 3.12.10

## 1. 完整测试集

执行：

```powershell
$env:PYTHONPATH = "src"
$Python = ".venv\Scripts\python.exe"
& $Python -m unittest discover -s tests -q
```


结果：

```text
Ran 80 tests in 9.197s
OK
```

覆盖范围：

- A 的 46 项文献处理测试；
- B 的 Model IR、ODE、PDE、Agent 工具和 smoke 测试；
- 新增的 A -> Model IR -> simulation 集成测试；
- 无 API 的 B 演示流程。

## 2. 模型就绪路径

命令：

```powershell
py -m biomodeling to-model-ir examples\model_ready_extraction.json `
  --out runs\integration_demo\model_ir.json `
  --mode reproduce `
  --strict
```

结果：

```text
model_ready: True
```

A 的最终质量门禁同时通过：`Final validation passed with no errors or warnings.`

B 校验：

```text
VALID
```

仿真结果：

- 模型：Unified Lotka-Volterra demonstration
- 时间域：[0, 20]
- 周期估计：约 5.4827
- 输出：仿真 JSON + PNG

## 3. 草稿路径

使用 A 的原始样例 `examples/literature/sample_extraction.json`：

```powershell
py -m biomodeling to-model-ir examples\literature\sample_extraction.json `
  --out runs\integration_demo\sample_draft_ir.json `
  --mode reproduce
```

结果：

```text
model_ready: False
```

原因：

- 原文样例描述 Monod 代数关系，没有完整 ODE 右端项；
- 若干参数只有范围或多个候选值；
- 时间域不明确；
- 适配器没有伪造方程、数值或时间域，而是写入 `missing_information` 与转换警告。

## 4. CLI smoke

已验证：

```powershell
.\run.ps1 literature prepare examples\literature\sample_paper.md `
  --out runs\cli_smoke\source.json `
  --chunks-out runs\cli_smoke\chunks.jsonl
```

结果：

```text
Prepared 6 chunk(s) from 380 words in 6 section(s).
```

同时验证 strict 转换：

```text
model_ready: True
```

## 5. 当前产物

```text
runs/
├─ cli_smoke/
│  ├─ source.json
│  ├─ chunks.jsonl
│  └─ model_ir.json
├─ integration_demo/
│  ├─ model_ir.json
│  ├─ sample_draft_ir.json
│  └─ simulation/
│     ├─ simulation_unified_lotka_volterra_demonstration__integration.json
│     └─ simulation_unified_lotka_volterra_demonstration__integration.png
├─ models/
├─ reports/
└─ simulation/
```

以上产物为测试生成，可在执行 `bootstrap.ps1` 后重新生成。


