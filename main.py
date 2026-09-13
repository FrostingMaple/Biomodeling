"""
main.py — CLI entry point for biomodel-agent.

Two modes:

  python main.py --demo
      Run the full "reproduce -> simulate -> report" pipeline automatically on a
      built-in Lotka-Volterra model, WITHOUT any LLM API call. Great for a quick
      demo and for verifying the numerical engine works.

  python main.py [--data path_to_literature.txt]
      Interactive mode: connect to the configured LLM (DeepSeek via USTC
      endpoint) and let the agent read the literature, extract/reproduce or
      spontaneously derive the model, simulate it and write a report.

Required env var for interactive mode:
  USTC_LLM_API_KEY
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Demo mode: full local pipeline with no API call.
# ---------------------------------------------------------------------------

DEMO_IR = {
    "model_name": "Lotka-Volterra predator-prey model",
    "model_type": "ODE",
    "description": (
        "经典竞争-捕食模型：被捕食者 X 以 Logistic 之外的简单自然增长，"
        "与捕食者 Y 的交互项 -bXY；捕食者依赖捕食 -cXY 增长并以速率 d 死亡。"
    ),
    "variables": [
        {"name": "X", "description": "被捕食者（猎物）种群", "unit": "unknown"},
        {"name": "Y", "description": "捕食者种群", "unit": "unknown"},
    ],
    "parameters": [
        {"name": "a", "description": "猎物自然增长率", "value_known": True,
         "value": 1.0, "unit": "unknown"},
        {"name": "b", "description": "捕食导致猎物减少的速率", "value_known": True,
         "value": 0.1, "unit": "unknown"},
        {"name": "c", "description": "捕食转化效率", "value_known": True,
         "value": 0.075, "unit": "unknown"},
        {"name": "d", "description": "捕食者死亡速率", "value_known": True,
         "value": 1.5, "unit": "unknown"},
    ],
    "equations": [
        {"variable": "X", "expression": "a*X - b*X*Y"},
        {"variable": "Y", "expression": "c*X*Y - d*Y"},
    ],
    "domain": {"t_start": 0, "t_end": 40},
    "initial_conditions": [
        {"variable": "X", "value_known": True, "value": 10},
        {"variable": "Y", "value_known": True, "value": 5},
    ],
    "boundary_conditions": [],
    "origin": {
        "mode": "reproduce",
        "source_text": "built-in demo (classic Lotka-Volterra)",
        "confidence": "high",
        "assumptions": [
            "猎物在没有捕食者时按指数增长",
            "捕食者只能依靠捕食猎物增长，离开猎物时指数死亡",
            "相互作用项为质量作用形式的 -bXY / +cXY",
        ],
    },
    "missing_information": ["变量与参数的单位未在原文给出"],
}


def run_demo():
    print("=" * 64)
    print("biomodel-agent — 无 API 全流程演示")
    print("模式：复现文献已有模型 (reproduce) -> 模拟 -> 报告")
    print("=" * 64)

    from tools import save_model_ir, simulate_model, save_report

    # 1. demo model (built-in; no external data file needed)
    print("\n[1/4] 演示模型: 内置 Lotka-Volterra 捕食-被捕食模型")
    print("     dX/dt = aX - bXY,   dY/dt = cXY - dY   (a=1.0,b=0.1,c=0.075,d=1.5)")
    print("     初值 X(0)=10, Y(0)=5")

    # 2. save the extracted IR
    print("\n[2/4] 保存提取的 Model IR ...")
    ir_msg = save_model_ir(DEMO_IR, tag="reproduce")
    print("      ", ir_msg)

    # 3. simulate
    print("\n[3/4] 数值模拟 ...")
    sim_out = simulate_model(DEMO_IR, tag="reproduce")
    print("      ", sim_out.replace("\n", "\n       "))

    # 4. write report
    print("\n[4/4] 生成复现报告 ...")
    from simulate import _model_slug
    sim_json = Path("output") / f"simulation_{_model_slug(DEMO_IR)}__reproduce.json"
    with open(sim_json, encoding="utf-8") as f:
        data = json.load(f)
    rep = _demo_report(data)
    msg = save_report(
        title="Lotka-Volterra 模型复现报告",
        content=rep,
        filename="report_lotka_volterra_reproduce",
    )
    print("      ", msg)
    print("\n完成。图表与报告位于 output/ 目录。")
    return 0


def _demo_report(data):
    X = data["X"]
    Y = data["Y"]
    t = data["t"]
    Xmax = max(X)
    Ymax = max(Y)
    Xend = X[-1]
    Yend = Y[-1]
    tYmax = t[Y.index(max(Y))]
    return f"""## 模型方程

```
dX/dt = a X - b X Y
dY/dt = c X Y - d Y
```

a=1.0, b=0.1, c=0.075, d=1.5，初值 X(0)=10, Y(0)=5。

## 模拟结果（t ∈ [0, 40]）

- 猎物 X 峰值 {Xmax:.2f}（t≈{t[X.index(Xmax)]:.1f}）
- 捕食者 Y 峰值 {Ymax:.2f}（t≈{tYmax:.1f}）
- 末端状态 X≈{Xend:.2f}, Y≈{Yend:.2f}

轨迹呈现经典的**周期性振荡**（捕食-被捕食循环），符合 Lotka-Volterra
模型的定性行为。相空间轨迹为闭合环。

## 对比文献

结果与文献模型定义一致（振荡周期与振幅取决于参数），数值复现成功。
"""


# ---------------------------------------------------------------------------
# Interactive (LLM) mode
# ---------------------------------------------------------------------------

def run_interactive(data_path=None):
    api_key = os.getenv("USTC_LLM_API_KEY")
    if not api_key:
        print("缺少环境变量 USTC_LLM_API_KEY，无法连接 LLM。")
        print("提示：可用 `python main.py --demo` 运行无 API 演示。")
        return 1

    from openai import OpenAI
    from agent import run_agent
    from tools import TOOLS, FUNCTIONS
    from prompts import SYSTEM_PROMPT

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.llm.ustc.edu.cn/v1",
    )
    MODEL = os.getenv("BIOMODEL_MODEL", "deepseek-v4-flash-ascend")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if data_path:
        user_input = (
            f"请读取并处理这篇文献：{data_path}。"
            "（支持 .pdf 文件，会自动解析为文本）"
            "如果文献给出了完整数学模型，请按‘复现’模式提取并用 simulate_model "
            "复现并写报告；如果文献只描述了机制而没有完整方程，请按‘自发构建’模式"
            "提出假设驱动的 ODE/PDE 模型，模拟并写报告。"
        )
        print(f"文献路径: {data_path}")
    else:
        user_input = input("You: ")

    messages.append({"role": "user", "content": user_input})

    answer = run_agent(
        client=client,
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        functions=FUNCTIONS,
    )
    print("\nAgent:")
    print(answer)
    return 0


def main():
    parser = argparse.ArgumentParser(description="biomodel-agent")
    parser.add_argument("--demo", action="store_true",
                        help="运行无 API 的完整复现演示")
    parser.add_argument("--data", type=str, default=None,
                        help="文献文件路径，支持 .txt 与 .pdf（交互模式）")
    args = parser.parse_args()

    if args.demo:
        sys.exit(run_demo())
    sys.exit(run_interactive(args.data))


if __name__ == "__main__":
    main()
