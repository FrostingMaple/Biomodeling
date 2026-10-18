# biomodel-agent evaluation

本目录保存模型能力评估案例和结果。

## 目录

- `cases/cases.json`：固定评估案例；
- `run_eval.py`：离线/在线评估入口；
- `results/eval_results.json`：最近一次评估汇总（运行产物，不提交）。

## 离线回归评估

不调用 LLM，使用案例中的固定 Model IR 检查数值引擎、元数据和报告验证：

```powershell
.\.venv\Scripts\python.exe eval\run_eval.py --offline
```

也可以通过 `--case <case_id>` 只运行单个案例。

## 在线 Agent 评估

需要配置 USTC 或 DeepSeek API Key：

```powershell
.\.venv\Scripts\python.exe eval\run_eval.py --live
```

在线评估会让真实 Agent 读取案例文本、保存 Model IR、执行模拟并生成报告。
它不属于默认 CI，避免引入 API Key、网络波动和调用成本。

## 指标

- Model IR 校验通过；
- 模型类型匹配；
- 期望变量全部出现；
- `origin.mode` 匹配；
- 模拟成功；
- `run_metadata` 存在；
- 报告章节覆盖；
- 在线模式额外记录 Agent 最终输出和错误原因。

## 新增案例

在 `eval/cases/cases.json` 中增加包含以下字段的对象：

- `id`
- `name`
- `model_type`
- `paper_text`
- `expected`
- `ir`
- `report_sample`

新增案例后运行离线评估确认其可执行。
