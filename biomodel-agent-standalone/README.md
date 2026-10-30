# BioModel Agent 可运行精简版

2026-10-30。本目录是独立的 BioModel Agent 科研原型，入口与仓库根目录的整合工程不同。**安装、启动命令均在本目录执行。**

保留运行源码、浏览器界面、必要工作区资源、少量模型示例及依赖配置；不包含测试代码、评测脚本、开发记录、历史运行结果或任何 API 密钥。首次安装需要联网下载 Python 依赖；安装后，下方布尔模型演示不需要联网或大模型服务。

## 1. 下载与环境

在 GitHub 点击 **Code → Download ZIP** 并解压，进入 `biomodel-agent-standalone`。也可：

```bash
git clone https://github.com/FrostingMaple/Biomodeling.git
cd Biomodeling/biomodel-agent-standalone
```

使用 **Python 3.12、Linux / WSL2**，无需 GPU。Windows 用户请在 WSL2 的终端运行以下命令；完整流程使用 Unix 文件锁，目前不支持直接在 Windows PowerShell 中运行。建议把本目录复制到 WSL 的 Linux 文件系统。

Ubuntu / WSL 若缺少 Python 或 venv，请先安装系统提供的 Python 3.12 和 `python3.12-venv`。确认 `python3.12 --version` 后继续。

## 2. 安装与启动

```bash
bash setup.sh
bash start.sh
```

打开启动日志中的本机地址，一般为 <http://127.0.0.1:8765>。推荐进入 **<http://127.0.0.1:8765/projects>** 研究项目页。终端保持运行，按 `Ctrl+C` 退出；下次直接 `bash start.sh`。

若不使用脚本，等效操作为：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python -m biomodel_agent workbench --store runs/workbench --port 8765
```

默认不调用大模型。可以打开界面、导入资料、检查配置；需要 Agent 自主规划研究时，按第 4 节启用自己的模型服务。首次建议先完成下一节的实际计算。

## 3. 不需要密钥的运行示例

```bash
.venv/bin/python demo.py
```

程序读取随包附带的两节点布尔网络，执行 8 步同步更新并进行数值检查，输出 `completion_eligible: true`、运行引用及输出目录。结果保存在本目录下 `runs/boolean-*/result.json` 与对应的不可变记录中。每次运行创建新的输出目录。

这是一个明确标注的合成演示，不是论文复现或实际生物结论。其他小型原生模型位于 `examples/model-types/`；FBA 输入在 `examples/fba-v1/`，ODE 的 SBML 模型和时间配置在 `examples/goodwin/`。

查看全部命令：

```bash
.venv/bin/python -m biomodel_agent --help
.venv/bin/python -m biomodel_agent model-types
```

## 4. 使用自己的模型服务

在启动工作台的同一终端中设置 OpenAI 兼容服务的地址、模型名称和密钥：

```bash
export BIOMODEL_API_KEY='替换为自己的密钥'
export BIOMODEL_BASE_URL='https://YOUR_PROVIDER/v1'
export BIOMODEL_MODEL='YOUR_MODEL'
bash start.sh --allow-provider
```

服务需要支持 `/chat/completions` 和工具调用。环境变量名称以这里为准；程序不自动读取 `.env` 文件。密钥仅留在本机，不上传到仓库。在线推进会调用你配置的模型服务并产生相应费用；界面会展示资料发送范围和额度。

## 5. 从资料到结果

1. 打开首页 `/`，导入 UTF-8 TXT / Markdown 材料或原生模型 JSON；浏览器单文件上限 1 MB。
2. 打开 `/projects`，描述研究目标，选择刚导入的资料或模型，检查规划、迭代和计算额度。启用模型服务后才可请求 Agent 规划。
3. 检查 Agent 给出的对象、尺度、证据、假设和实验方案；遇到讨论问题时填写回答，再继续当前项目。
4. 查看每轮实验、数值检查和研究结论，最后导出报告和 ZIP 研究包。

页面里的“计算完成”与“生物学结论得到证实”含义不同。资料不足、模型类型不支持或额度耗尽时，应检查具体状态。恢复旧任务须沿用同一 `runs/` 存储及相应命令，不要通过复制目录或重新运行来假定此前请求未发生。

随包 `examples/research-projects/application.json` 的规划/文献额度为 0，适合创建和查看项目；它不会自动开展在线研究。实际研究请在界面明确配置非零额度。

## 6. 数据、功能与常见问题

- **数据位置：** 工作台数据在 `runs/workbench/`，演示计算在 `runs/boolean-*/`；退出后仍保留。源码升级前建议备份整个 `runs/`。密钥通过环境变量配置。
- **端口被占用：** `bash start.sh --port 8766`，使用启动日志中的地址。
- **安装依赖失败：** 确认是 Linux / WSL2、64 位 Python 3.12，检查 pip 网络连接。首次安装需要 NumPy、SciPy、libSBML、RoadRunner、pypdf 和 httpx。
- **精确依赖版本：** `requirements.lock` 保留本地验证环境的版本，并已去掉测试依赖。需要固定版本时可先运行 `.venv/bin/python -m pip install -r requirements.lock`，再运行 `.venv/bin/python -m pip install --no-build-isolation --no-deps .`；普通安装用第 2 节即可。
- **可选功能：** `.venv/bin/python -m pip install '.[pdf,figures]'` 增加 PDF 布局提取和图像处理依赖；工作台浏览器上传目前只支持上述文本/JSON，PDF 使用 `source-ingest` CLI。
- **功能范围：** 有限 ODE、稳态 FBA、随机反应、1D 线性 PDE、布尔网络和格点个体模型。不是任意论文自动复现工具。图形界面是本机单用户工作台。
- **历史案例库：** 本精简版不分发 Goodwin 的历史案例闭包、参考答案和图片归档，`case-*` 历史案例命令不属于本版开箱功能；使用自带小型原生输入或自己的资料开始新任务。

## 目录

| 路径 | 用途 |
|---|---|
| `src/biomodel_agent/` | 运行代码、界面、必需工作区模板 |
| `examples/` | 小型原生输入与配置 |
| `setup.sh` / `start.sh` | 安装 / 启动工作台 |
| `demo.py` | 无密钥布尔模型使用示例 |
| `pyproject.toml` | 包与运行依赖配置 |
| `requirements*.lock` | 可选固定版本环境 |
| `runs/` | 在本机使用时生成，不随包上传 |
