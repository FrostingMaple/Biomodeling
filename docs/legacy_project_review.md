# Biomodeling 项目完善建议

> 审查对象：`C:\Users\我的电脑\Documents\ChatGPT\Biomodeling-main\Biomodeling-main`  
> 文档用途：记录当前项目最需要修改和完善的事项，作为后续迭代任务清单。  
> 审查性质：只读分析，不包含代码修改。

---

## 1. 总体评价

该项目是一个 LLM 驱动的生物系统数学建模 Agent 原型，核心流程为：

`文献读取 -> Model IR 提取/构建 -> ODE/PDE 数值求解 -> JSON/PNG 输出 -> Markdown 报告`

主要优点：

- 主流程完整，包含 CLI、LLM Agent、Model IR、工具层、数值求解和报告生成。
- 使用 SymPy 解析方程，未发现直接 `exec/eval` 用户方程，安全性方向正确。
- 支持 ODE，并声称支持一维反应扩散 PDE。
- 支持文本和 PDF 文献读取。
- 支持无 API 的 Lotka-Volterra demo。
- 支持会话保存、恢复和历史列表。
- 已有 Repressilator 复现报告和扩展分析，报告质量总体较好。

主要问题：

- README、代码配置和 lockfile 不一致，干净环境下可能无法按文档运行。
- 缺少自动化测试和 CI，数值引擎与 Agent 工具链缺少回归保障。
- PDE 支持较弱，边界条件实现不完整，也缺少实际 PDE 产物验证。
- Model IR 缺少运行时业务校验。
- 报告和实验结果缺少统一的可复现元数据。
- Agent 调用缺少重试、超时、成本控制和评估集。

综合定位：

- 作为课程作业原型：约 7–7.5/10。
- 作为公开可复用工具：约 4.5–5/10。
- 综合：约 6/10。

---

## 2. P0：必须优先修复

### P0-1 统一 README 与代码中的 API 配置

涉及文件：

- `README.md`
- `main.py`

当前不一致：

- README 写使用 `USTC_LLM_API_KEY`，代码实际读取 `DEEPSEEK_API_KEY`。
- README 写 USTC 端点 `https://api.llm.ustc.edu.cn/v1`，代码实际使用 `https://api.deepseek.com/v1`。
- README 写默认模型为 `deepseek-v4-flash-ascend`，代码实际默认 `deepseek-flash`。

建议修改：

1. 明确项目最终使用的服务商和端点。
2. 若保留 DeepSeek：
   - README 改为 `DEEPSEEK_API_KEY`；
   - base URL 改为 `https://api.deepseek.com/v1`；
   - 默认模型改为 `deepseek-flash`，或把默认模型提取到配置项。
3. 若保留 USTC：
   - `main.py` 改为读取 `USTC_LLM_API_KEY`；
   - base URL 改为 `https://api.llm.ustc.edu.cn/v1`；
   - 默认模型与 README 保持一致。
4. 增加 `.env.example` 或配置说明文件。

验收标准：

- 用户仅按 README 设置环境变量即可进入交互模式。
- README、代码、示例命令中的 API key、端点和模型名完全一致。

---

### P0-2 修复 `uv.lock` 与 `pyproject.toml` 不一致

涉及文件：

- `pyproject.toml`
- `uv.lock`

当前问题：

- `pyproject.toml` 声明了 `numpy`、`scipy`、`matplotlib`、`sympy`、`pymupdf`。
- `uv.lock` 中项目自身依赖元数据只记录了 `openai`。
- 使用 lockfile 重建环境时可能缺失核心依赖。

建议修改：

1. 重新生成 lockfile：

   ```powershell
   cd C:\Users\我的电脑\Documents\ChatGPT\Biomodeling-main\Biomodeling-main
   uv lock
   uv sync
   ```

2. 检查 `uv.lock` 中是否包含全部运行依赖。
3. 增加 smoke test，验证核心包可导入。

验收标准：

- 删除本地虚拟环境后，执行 `uv sync` 可完整安装所有依赖。
- `uv run python main.py --demo` 成功运行。
- `uv.lock` 与 `pyproject.toml` 一致。

---

### P0-3 修复安装说明与实际环境不一致

涉及文件：

- `README.md`

当前问题：

- README 声称项目自带 `.venv`。
- 实际项目目录下没有 `.venv`。
- README 中大量命令依赖 `.venv\Scripts\python.exe`，按文档直接运行会失败。

建议修改：

1. 将 README 中命令统一改为 `uv run`：

   ```powershell
   uv sync
   uv run python main.py --demo
   uv run python main.py --data data\test.pdf
   ```

2. 或明确要求用户先创建虚拟环境：

   ```powershell
   uv venv
   uv sync
   ```

3. 删除“项目自带 `.venv`”这类与实际仓库状态不符的描述。

验收标准：

- README 中的命令从干净 checkout 开始能够执行。
- 不再引用不存在的 `.venv`。

---

### P0-4 增加最小可运行验证

涉及文件建议：

- 新增 `tests/test_smoke.py`
- 新增 `tests/test_simulate_ode.py`

建议修改：

1. 增加无 API smoke test，验证：
   - `main.py --demo` 可运行；
   - `output/` 能生成 IR、模拟 JSON、PNG 和报告；
   - 核心依赖导入正常。

2. 增加 ODE 测试：
   - Lotka-Volterra 能成功求解；
   - 缺失参数时返回错误；
   - 缺失初值时返回错误；
   - 方程变量与 `variables` 不一致时返回错误。

验收标准：

- 运行 `uv run pytest` 可通过。
- 修改数值引擎后能通过基础回归测试。

---

## 3. P1：应尽快完善

### P1-1 增加 Model IR 运行时业务校验

涉及文件：

- `model_ir.py`
- `tools.py`
- `simulate.py`

当前问题：

- Model IR 主要只是给 LLM 的 JSON Schema。
- `save_model_ir` 不独立校验 IR。
- 非法模型可能在保存成功后才在模拟阶段失败。

建议修改：

1. 增加函数 `validate_model_ir(model) -> list[str] | None`。
2. 校验内容：
   - `model_type` 是否为 ODE/PDE/stochastic/unknown；
   - variables 是否为空；
   - variables 是否重复；
   - equations 的 variable 是否都存在；
   - 每个变量是否有对应方程；
   - parameters 是否重复；
   - `value_known=True` 时是否有数值；
   - initial_conditions 是否覆盖所有变量；
   - PDE 是否有 spatial 域；
   - PDE 所需边界条件是否足够；
   - `origin.mode` 和 `origin.confidence` 是否合法。
3. `save_model_ir` 调用校验，非法时明确报错或返回结构化错误。
4. `simulate_model` 继续保留错误返回给 Agent 的机制。

验收标准：

- 明确错误在保存阶段被捕获。
- Agent 能收到可读错误并自行修正 IR。

---

### P1-2 修正 PDE 边界条件实现

涉及文件：

- `simulate.py`
- `model_ir.py`

当前问题：

- PDE 只使用第一个空间区间，多区间会被忽略。
- Dirichlet 边界仅将边界导数置零。
- Neumann 边界基本是 `pass`，没有使用 `bc["value"]`。
- 非零边界值、通量边界条件不可靠。

建议修改：

1. 明确当前只支持一维单区间 PDE，并在 schema 和 README 中写明。
2. 正确实现 Dirichlet：
   - 固定边界节点值；
   - 或通过 ghost node 正确处理边界。
3. 正确实现 Neumann：
   - 使用 `bc["value"]`；
   - 支持零通量和非零梯度。
4. 对不支持的边界条件显式报错，不要静默忽略。
5. 增加 Fisher-KPP PDE 测试：
   - 与理论波速 `2*sqrt(D*r)` 对照；
   - 验证边界条件对结果的影响。

验收标准：

- 至少一个 PDE 示例能从 IR 跑通并生成 JSON/PNG。
- 非零 Dirichlet/Neumann 行为有测试覆盖。
- 不支持的 PDE 配置会明确报错。

---

### P1-3 增加 Agent 调用可靠性

涉及文件：

- `agent.py`
- `main.py`

当前问题：

- 无重试和退避。
- 无请求超时配置。
- 无 Token/成本限制。
- 无工具调用成功率统计。
- 出错时主要依赖打印和模型自行修正。

建议修改：

1. OpenAI client 增加超时。
2. API 调用增加有限重试和指数退避。
3. 增加最大 Token 或最大成本保护。
4. 增加每轮工具调用日志。
5. 将关键错误写入会话文件，便于恢复和诊断。
6. 对模型只输出解释、不调用工具的情况增加提示或重试策略。

验收标准：

- 网络偶发失败不会直接中断整个会话。
- 长时间运行有成本和安全边界。
- 会话文件中能看到关键工具调用和错误记录。

---

### P1-4 增加结果可复现元数据

涉及文件：

- `tools.py`
- `simulate.py`
- `main.py`

当前问题：

- 报告和模拟结果缺少代码版本、依赖版本、模型名、输入文件哈希、运行时间和环境信息。
- 不同时间生成的同名文件可能难以区分来源。

建议修改：

1. 每个模拟结果 JSON 增加：
   - `run_id`
   - `created_at`
   - `model_name`
   - `model_type`
   - `tag`
   - `source_ir_file`
   - `code_version`
   - `python_version`
   - `dependency_versions`
   - `input_file_hash`
2. 报告中增加“运行元数据”部分。
3. 文件名可使用时间戳或短 run id，避免覆盖和混淆。

验收标准：

- 任一报告可追溯到对应 IR、模拟文件和代码版本。
- 同名模型多次运行可以区分。

---

### P1-5 增加测试和 CI

涉及文件建议：

- `tests/test_model_ir.py`
- `tests/test_simulate_ode.py`
- `tests/test_simulate_pde.py`
- `tests/test_tools.py`
- `.github/workflows/ci.yml`

建议测试范围：

- Model IR 校验。
- ODE 求解稳定性。
- PDE 扩散与边界条件。
- PDF 提取。
- 工具 JSON 参数修复。
- 非法模型错误路径。
- `--demo` 端到端。

验收标准：

- 每次提交自动运行测试。
- 核心模块测试覆盖率有基本保障。

---

## 4. P2：中长期完善

### P2-1 正式打包

涉及文件：

- `pyproject.toml`

建议：

1. 明确 build backend。
2. 明确 package 和 module 发现规则。
3. 验证 `biomodel-agent` 命令入口安装后可用。
4. 增加版本号管理策略。

验收标准：

- 安装 wheel/sdist 后可执行 `biomodel-agent --demo`。

---

### P2-2 清理和治理输出目录

涉及文件：

- `output/`
- `.gitignore`

当前问题：

- `output/` 下已有大量历史 JSON、PNG 和报告。
- 演示产物可能混入仓库，影响可读性和体积。

建议：

1. 保留少量精选示例。
2. 将运行产物默认写入 `output/runs/<timestamp>/`。
3. 明确哪些示例产物应提交，哪些应忽略。
4. 增加清理命令或脚本。

验收标准：

- 仓库中只保留代表性示例。
- 新运行结果按 run 分目录保存。

---

### P2-3 增强报告自动验证

涉及文件：

- `tools.py`
- `simulate.py`
- `prompts.py`

建议：

1. 报告必须引用实际模拟文件名。
2. 报告中的数值应来自工具返回的结构化 summary。
3. 增加检查：
   - 是否包含方程；
   - 是否包含参数来源；
   - 是否包含假设；
   - 是否包含模拟结果；
   - 是否说明缺失信息。
4. 对报告中的关键数值与 simulation JSON 做一致性检查。

验收标准：

- 报告中的主要数值可自动追溯到模拟结果。
- 缺少必需章节时给出警告。

---

### P2-4 建立评估集

建议：

1. 准备若干标准文献或人工整理文本：
   - 已给完整 ODE 的论文；
   - 已给 PDE 的论文；
   - 只描述机制的论文；
   - 不适格文献。
2. 定义指标：
   - IR 提取正确率；
   - 方程结构正确率；
   - 参数识别正确率；
   - 模拟成功率；
   - 报告完整性。
3. 评估不同模型的工具调用稳定性。

验收标准：

- 每次修改 Prompt 或模型后都能跑固定评估集。
- 能量化系统能力变化，而不是只看单次演示。

---

### P2-5 安全与隐私

建议：

1. 明确文献加载是否会发送到第三方 API。
2. 支持本地模型或代理端点。
3. 增加 API key 不写入日志和会话文件的检查。
4. 对大型 PDF 和敏感文献增加提示。

验收标准：

- 用户明确知道哪些内容会离开本机。
- 日志和会话中不泄露 API key。

---

## 5. 建议实施顺序

1. 修 README、API 配置、`uv.lock` 和安装命令。
2. 加 smoke test，确保 `uv sync` 后 `main.py --demo` 稳定运行。
3. 加 Model IR 校验。
4. 修 PDE 边界条件并增加 PDE 示例。
5. 加测试和 CI。
6. 增加运行元数据与报告验证。
7. 清理输出目录并正式打包。
8. 建立模型评估集。

---

## 6. 验收清单

- [ ] README 与代码 API 配置一致。
- [ ] `uv.lock` 包含全部依赖。
- [ ] 干净环境可按 README 跑通 `--demo`。
- [ ] 有 `pytest` 测试和 CI。
- [ ] `save_model_ir` 会校验 IR。
- [ ] ODE 示例有回归测试。
- [ ] PDE 示例可运行，边界条件正确。
- [ ] 模拟结果有运行元数据。
- [ ] 报告数值可追溯到模拟结果。
- [ ] `biomodel-agent` 安装后可运行。
- [ ] 输出目录有清晰治理策略。
- [ ] 有固定评估集衡量 Agent 能力。
