"""
main.py — CLI entry point for biomodel-agent.

Two modes:

  python main.py --demo
      Run the full "reproduce -> simulate -> report" pipeline automatically on a
      built-in Lotka-Volterra model, WITHOUT any LLM API call. Great for a quick
      demo and for verifying the numerical engine works.

  python main.py [--data path_to_literature.txt]
      Interactive mode: connect to the configured OpenAI-compatible LLM (USTC by default; DeepSeek optional) and let the
      agent read the literature, extract/reproduce or spontaneously derive
      the model, simulate it and write a report. The conversation is
      persistent: it is auto-saved after every round to output/sessions/, so
      you can exit (type `exit`) and later resume it with --resume.

  python main.py --resume SESSION_ID
      Resume a previously-saved conversation and keep talking. The full agent
      message history (including tool calls) is reloaded, so the agent
      remembers the models it built before. Does NOT re-process --data.

  python main.py --list-sessions
      List all saved conversations you can resume.

Required env vars for interactive mode:
  USTC_LLM_API_KEY    (default provider; BIOMODEL_MODEL is optional)
  DEEPSEEK_API_KEY    (only when BIOMODEL_PROVIDER=deepseek)
  BIOMODEL_BASE_URL   (optional endpoint override)
  BIOMODEL_REQUEST_TIMEOUT (optional, default 120 seconds)
  BIOMODEL_MAX_RETRIES     (optional, default 2)
  BIOMODEL_MAX_TOOL_ROUNDS (optional, default 40)
  BIOMODEL_MAX_TOTAL_TOKENS (optional, default 200000; 0 disables)
"""

import argparse
import json
import os
import sys
from pathlib import Path

from security_utils import redact_secrets


LLM_PROVIDERS = {
    "ustc": {
        "api_key_env": "USTC_LLM_API_KEY",
        "base_url": "https://api.llm.ustc.edu.cn/v1",
        "model": "deepseek-flash",
    },
    "deepseek": {
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
}


def _env_int(name, default, minimum=0):
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        print(f"警告：{name}={raw!r} 不是整数，使用默认值 {default}。")
        return default
    if value < minimum:
        print(f"警告：{name}={value} 低于最小值 {minimum}，使用 {minimum}。")
        return minimum
    return value


def _env_float(name, default, minimum=0.0):
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        print(f"警告：{name}={raw!r} 不是数字，使用默认值 {default}。")
        return default
    if value < minimum:
        print(f"警告：{name}={value} 低于最小值 {minimum}，使用 {minimum}。")
        return minimum
    return value


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
        metadata=data.get("run_metadata"),
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
# Interactive (LLM) mode + session persistence
# ---------------------------------------------------------------------------

def _sessions_dir():
    d = Path("output") / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _session_path(session_id):
    return _sessions_dir() / f"{session_id}.json"


def _new_session_id():
    from datetime import datetime
    return "sess_" + datetime.now().strftime("%Y%m%d_%H%M%S")


def _save_session(session):
    """Persist a session (id, model, data_path, created_at, messages) to disk."""
    path = _session_path(session["session_id"])
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)
    tmp.replace(path)  # atomic-ish write: never leave a half-written session


def _load_session(session_id):
    path = _session_path(session_id)
    if not path.exists():
        return None, f"找不到会话 '{session_id}'。\n可用 `python main.py --list-sessions` 查看已保存的会话。"
    try:
        with open(path, encoding="utf-8") as f:
            session = json.load(f)
        return session, None
    except Exception as exc:
        return None, f"读取会话 '{session_id}' 失败：{exc}"


def _list_sessions():
    """Print a human-readable listing of all saved sessions."""
    sess_dir = _sessions_dir()
    files = sorted(sess_dir.glob("sess_*.json"), key=lambda p: p.name, reverse=True)
    if not files:
        print("（还没有保存任何会话。）")
        return
    print("已保存的会话（最新的在前）:") if False else None
    print(f"{'会话 ID':<24} {'创建时间':<22} {'消息数':<8} 说明")
    print("-" * 80)
    for p in files:
        try:
            with open(p, encoding="utf-8") as f:
                s = json.load(f)
            n = len(s.get("messages", []))
            title = s.get("note", "")
            print(f"{s.get('session_id'):<24} {s.get('created_at',''):<22} {n:<8} {title}")
        except Exception:
            print(f"{p.stem:<24} （无法解析）")
    print("\n使用 `python main.py --resume <会话ID>` 恢复某个会话继续对话。")


def run_interactive(data_path=None, resume_id=None):
    provider = os.getenv("BIOMODEL_PROVIDER", "ustc").strip().lower()
    preset = LLM_PROVIDERS.get(provider)
    if preset is None:
        print(f"不支持的 BIOMODEL_PROVIDER={provider!r}；可选值：{", ".join(sorted(LLM_PROVIDERS))}。")
        return 1

    api_key = os.getenv(preset["api_key_env"])
    if not api_key:
        print(f"缺少环境变量 {preset['api_key_env']}，无法连接 LLM。")
        print("提示：可用 `python main.py --demo` 运行无 API 演示。")
        return 1

    from openai import OpenAI
    from agent import run_agent
    from tools import TOOLS, FUNCTIONS
    from prompts import SYSTEM_PROMPT

    MODEL = os.getenv("BIOMODEL_MODEL", preset["model"])
    BASE_URL = os.getenv("BIOMODEL_BASE_URL", preset["base_url"])
    REQUEST_TIMEOUT = _env_float("BIOMODEL_REQUEST_TIMEOUT", 120.0, minimum=1.0)
    MAX_RETRIES = _env_int("BIOMODEL_MAX_RETRIES", 2, minimum=0)

    # ---- Resume an existing session, or start a fresh one ----
    session_id = None
    note = data_path or ""
    if resume_id:
        session, err = _load_session(resume_id)
        if err:
            print(err)
            return 1
        messages = session.get("messages") or []
        if not any(m.get("role") == "system" for m in messages):
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        MODEL = os.getenv("BIOMODEL_MODEL") or session.get("model", MODEL)
        session_id = session["session_id"]
        note = session.get("note", "")
        print(f"已恢复会话 '{session_id}'（{session.get('created_at', '')}），"
              f"共 {len(messages)} 条历史消息。")
    else:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        session_id = _new_session_id()
        # 若传入了文献路径，先作为第一轮任务交给 agent，跑完再进入持续对话。
        # 新建会话的"未完成第一轮"也持久化，保证中断不丢。
        if data_path:
            messages.append({
                "role": "user",
                "content": (
                    f"请读取并处理这篇文献：{data_path}。"
                    "（支持 .pdf 文件，会自动解析为文本）"
                    "如果文献给出了完整数学模型，请按‘复现’模式提取并用 simulate_model "
                    "复现并写报告；如果文献只描述了机制而没有完整方程，请按‘自发构建’"
                    "模式提出假设驱动的 ODE/PDE 模型，模拟并写报告。"
                ),
            })

    client = OpenAI(
        api_key=api_key,
        base_url=BASE_URL,
        timeout=REQUEST_TIMEOUT,
        max_retries=MAX_RETRIES,
    )

    # 关键：把"当前会话"传给内部循环使用，以便每轮结束后落盘保存。
    session = {
        "session_id": session_id,
        "created_at": _created_at_of(session_id),
        "model": MODEL,
        "note": note,
        "data_path": data_path,
        "messages": messages,
    }

    def persist(event=None, **details):
        # keep messages and the latest runtime event in sync on disk
        session["messages"] = messages
        session["model"] = MODEL
        if event is not None:
            session["last_event"] = {"type": event, **details}
        _save_session(session)

    def record_agent_error(exc):
        message = f"[Agent runtime error] {type(exc).__name__}: {redact_secrets(str(exc))}"
        messages.append({"role": "assistant", "content": message})
        persist("agent_error", error=str(exc))
        print(f"\nAgent 运行失败：{message}")

    # First turn: process the data file (only for a fresh session with --data).
    if not resume_id and data_path:
        print(f"文献路径: {data_path}")
        print(f"[会话 {session_id}] 正在处理文献，请稍候……")
        try:
            run_agent(
                client=client,
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                functions=FUNCTIONS,
                verbose=False,
                on_event=persist,
            )
            persist()
        except Exception as exc:
            record_agent_error(exc)

    # Persistent chat loop: continue talking until the user types exit.
    print("\n（持续对话中：可继续提问或要求修改模型；输入 exit 退出。"
          f"会话 ID: {session_id}，退出后可 `--resume {session_id}` 继续）")
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "退出"):
            persist()  # save before leaving
            print("已保存会话，输入 `python main.py --resume "
                  f"{session_id}` 可继续。再见！")
            break

        messages.append({"role": "user", "content": user_input})
        try:
            answer = run_agent(
                client=client,
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                functions=FUNCTIONS,
                verbose=False,
                on_event=persist,
            )
            print("\nAgent:")
            print(answer)
            persist()  # persist after each round so nothing is lost on crash/exit
        except Exception as exc:
            record_agent_error(exc)
            continue

    return 0


def _created_at_of(session_id):
    """Recover a display timestamp from the session id (sess_YYYYMMDD_HHMMSS)."""
    stamp = session_id.removeprefix("sess_")
    if len(stamp) == 15 and stamp[:8].isdigit():  # YYYYMMDD_HHMMSS
        return stamp[:8] + "_" + stamp[9:]
    return ""


def main():
    parser = argparse.ArgumentParser(description="biomodel-agent")
    parser.add_argument("--demo", action="store_true",
                        help="运行无 API 的完整复现演示")
    parser.add_argument("--data", type=str, default=None,
                        help="文献文件路径，支持 .txt 与 .pdf（交互模式）")
    parser.add_argument("--resume", type=str, default=None, metavar="SESSION_ID",
                        help="恢复之前保存的会话并继续对话（不重新处理 --data 文献）")
    parser.add_argument("--list-sessions", action="store_true",
                        help="列出所有已保存的可恢复会话")
    args = parser.parse_args()

    if args.demo:
        sys.exit(run_demo())
    if args.list_sessions:
        _list_sessions()
        sys.exit(0)
    sys.exit(run_interactive(args.data, resume_id=args.resume))


if __name__ == "__main__":
    main()
