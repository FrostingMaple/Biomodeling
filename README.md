# BioModel Agent 运行版

本目录仅分发运行程序、安装/启动脚本、运行依赖和这份使用说明。不包含测试代码、测试报告、评测脚本、演示程序、演示项目、预期答案或历史计算结果。

## 下载

推荐下载仓库的 `codex/runtime-only-20261030` 分支：

[下载纯运行版 ZIP](https://github.com/FrostingMaple/Biomodeling/archive/refs/heads/codex/runtime-only-20261030.zip)

解压后进入包含本说明和 `setup.sh` 的目录。该分支根目录就是运行程序；主分支另有同学原先的整合工程和测试文件。主分支的 `biomodel-agent-standalone/` 目录与本运行版相同。

## 环境与安装

需要 **64 位 Python 3.12、Linux 或 WSL2**，无需 GPU。Windows 用户请在 WSL2 终端操作；完整工作流依赖 Unix 文件锁，不能直接在 PowerShell 中运行。建议将程序放在 WSL 的 Linux 文件系统中。

Ubuntu / WSL 如果缺少环境，请先安装系统提供的 `python3.12` 和 `python3.12-venv`。确认 `python3.12 --version` 后，在本目录运行：

```bash
bash setup.sh
bash start.sh
```

首次安装需要联网下载依赖。打开终端显示的地址（一般为 <http://127.0.0.1:8765>）；研究项目页为 <http://127.0.0.1:8765/projects>。终端保持运行，按 `Ctrl+C` 退出。以后只需 `bash start.sh`。

不使用脚本时，等效操作为：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python -m biomodel_agent workbench --store runs/workbench --port 8765
```

## 配置模型服务

默认不调用大模型，可以打开界面、导入资料并检查输入。让 Agent 规划研究前，需要在启动终端设置自己的 OpenAI 兼容服务：

```bash
export BIOMODEL_API_KEY='替换为自己的密钥'
export BIOMODEL_BASE_URL='https://YOUR_PROVIDER/v1'
export BIOMODEL_MODEL='YOUR_MODEL'
bash start.sh --allow-provider
```

服务应支持 `/chat/completions` 和工具调用。程序不自动读取 `.env`。在线操作会调用你的模型服务并使用相应额度，界面展示实际资料范围和冻结预算。密钥仅通过本机环境变量提供。

## 使用自己的资料

1. 在首页 `/` 导入 UTF-8 TXT / Markdown 或原生模型 JSON；单文件不超过 1 MB。没有预置文献或计算结果。
2. 打开 `/projects`，填写研究目标、选择已导入的资料或模型，核对规划、迭代和计算额度；启用服务后再推进研究。
3. 查看建模对象、证据、假设和实验方案。需要讨论时回答具体问题，再继续原项目。
4. 查看实验、实际检查和结论，通过界面导出报告或 ZIP 研究包。

支持有限 ODE、稳态 FBA、随机反应、1D 线性 PDE、布尔网络和格点个体模型；不是任意论文自动复现工具。计算成功不代表生物学结论已被证实。资料不足或类型不支持时，查看具体状态和缺口。

## 本机数据与常用命令

运行后数据保存在 `runs/workbench/`，退出后保留；升级前备份整个存储。下载内容中不预置 `runs/`。同一任务沿用原存储和恢复入口，不通过复制目录来假定此前请求未发生。

```bash
# 查看命令与依赖状态（不发送模型请求）
.venv/bin/python -m biomodel_agent --help
.venv/bin/python -m biomodel_agent workspace-doctor

# 更换端口
bash start.sh --port 8766

# 可选 PDF 布局提取和图像功能
.venv/bin/python -m pip install '.[pdf,figures]'
```

浏览器上传目前支持上述文本和 JSON；PDF 使用 `source-ingest` CLI。`workspace-init --output 新目录` 为外部 Agent 创建空白工作区，不预载合成资料或演示运行。

`src/biomodel_agent/workspace_assets/templates/` 内的 6 份 JSON 是程序运行时给 Agent 说明输入结构的模板。它们不包含测试结果或参考答案；其中示意数值不能作为用户任务的证据。ODE 模板的数值与选择保持未解决，执行前必须按实际资料填写。

`requirements.lock` / `requirements-pdf.lock` 供需要固定版本的环境使用，已排除测试依赖。普通安装按上面的 `setup.sh` 即可。安装失败时先确认 Python 版本、Linux / WSL2 和 pip 网络连接。

历史 `case-*` 命令依赖另行提供的案例库，本运行版不附带历史案例材料或参考结果；新任务请从自己的资料开始。
