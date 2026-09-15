import json
import re
import sys

# Make ALL console printing encoding-safe: never crash on characters (e.g. a
# '®' in a PDF) that the local console codec (cp936/GBK on Windows) cannot
# encode. Non-encodable chars are replaced instead of raising.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass
try:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

# Cap how much of a single tool result we print to the console in verbose mode.
# Huge outputs (full literature text, big simulation JSON) would otherwise
# flood/garble the terminal and make the run feel very slow.
PRINT_MAX_CHARS = 2000


def _bounded(text, limit=PRINT_MAX_CHARS):
    """Return a printable, length-capped, encoding-safe string for the console."""
    s = str(text)
    s = s.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    if len(s) > limit:
        return s[:limit] + f"\n...[truncated {len(s) - limit} more chars]"
    return s


def _message_to_dict(message):
    """Convert an OpenAI SDK ChatCompletionMessage (or a plain dict) into a
    plain, JSON-serialisable dict suitable for saving to disk and re-sending
    to the API. Handles optional tool_calls (also SDK objects) and `name`.
    """
    if isinstance(message, dict):
        return dict(message)
    tc = getattr(message, "tool_calls", None) or []
    tool_calls = []
    for tc_obj in tc:
        if isinstance(tc_obj, dict):
            tool_calls.append(dict(tc_obj))
            continue
        fn = getattr(tc_obj, "function", None)
        tool_calls.append({
            "id": getattr(tc_obj, "id", None),
            "type": getattr(tc_obj, "type", "function"),
            "function": {
                "name": getattr(fn, "name", None),
                "arguments": getattr(fn, "arguments", "{}"),
            },
        })
    return {
        "role": getattr(message, "role", "assistant"),
        "content": getattr(message, "content", None),
        "name": getattr(message, "name", None),
        "tool_calls": tool_calls,
    }


def _repair_arguments(arg_str):
    """Best-effort repair of a model-produced tool `arguments` string into a
    dict. Returns (parsed_dict, ok_flag). Returns (None, False) if it cannot
    recover.

    Models -- especially cheap/fast ones like deepseek-flash -- sometimes emit
    malformed JSON for the big nested arguments of tools like save_model_ir /
    simulate_model (a full Model IR). We try progressively:
      1. strip markdown code fences;
      2. plain json.loads (already sanitised);
      3. cut trailing garbage (e.g. a truncation cut mid-object);
      4. stack-based bracket balancing to close what is obviously unclosed;
      5. strip a possible trailing comma.
    """
    s = arg_str.strip()

    # Drop surrounding markdown fences like ```json ... ```
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE).strip()
    s = re.sub(r"\s*```\s*$", "", s).strip()

    def try_load(txt):
        try:
            obj = json.loads(txt)
            return obj if isinstance(obj, dict) else None
        except (json.JSONDecodeError, TypeError, ValueError):
            return None

    obj = try_load(s)
    if obj is not None:
        return obj, True

    # Remove trailing commas before any closing brace/bracket (a very common
    # model slip), e.g. `{"a": 1,}` or nested `{"a": {"b": [1,2,],}}`. Loop
    # until stable to handle nesting.
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r",\s*([}\]])", r"\1", s)
    if s != arg_str.strip():
        obj = try_load(s)
        if obj is not None:
            return obj, True

    # Attempt bracket balancing: find the outermost matching JSON object.
    openers = 0
    end_index = -1
    in_str = False
    esc = False
    for i, ch in enumerate(s):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            openers += 1
        elif ch == "}":
            openers -= 1
            if openers == 0:
                end_index = i
                break
    if end_index != -1:
        obj = try_load(s[: end_index + 1])
        if obj is not None:
            return obj, True

    # Close unclosed brackets by appending the right number of closers.
    stack = []
    in_str = False
    esc = False
    for ch in s:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack:
                stack.pop()
    closers = "".join("}" if o == "{" else "]" for o in reversed(stack))
    if closers:
        obj = try_load(s + closers)
        if obj is not None:
            return obj, True

    return None, False


def run_agent(
    client,
    model,
    messages,
    tools,
    functions,
    verbose=True,
):
    """Run the LLM tool-calling loop until the model returns a final answer.

    `verbose=True` (default) prints a step-by-step trace: each tool the model
    decides to call and what the Python tool returned. Pass `verbose=False` for
    a quiet run (the full raw model message is only printed in verbose mode,
    since printing it can flood the console with large tool results).
    """
    max_rounds = 40  # hard safety cap on tool-calling rounds

    for _ in range(max_rounds):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        message = response.choices[0].message

        if verbose:
            print("\n--- DeepSeek Raw Output ---")
            print(_bounded(message))
            print("---------------------------\n")

        if not message.tool_calls:
            return message.content

        # Normalise the SDK ChatCompletionMessage object into a plain,
        # JSON-serialisable dict so that the whole `messages` list can be
        # saved/restored to disk for session persistence (and still be re-sent
        # to the API, which accepts this classic shape).
        messages.append(_message_to_dict(message))

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            raw_args = tool_call.function.arguments or ""

            # Robustly parse the tool arguments. If the model produced
            # malformed JSON, feed the error back to the model as a tool
            # result so it can correct itself instead of crashing the loop.
            args, args_ok = _repair_arguments(raw_args)
            if not args_ok:
                print(f"[DeepSeek调用参数格式错误] {name}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": (
                        "ERROR: the arguments for this tool call were not valid "
                        "JSON and could not be repaired. Please retry the call "
                        "with arguments that are a single, complete, valid JSON "
                        f"object. Raw arguments received:\n{raw_args}"
                    ),
                })
                continue

            print(f"[DeepSeek决定调用] {name}({args})")

            if name not in functions:
                print(f"[未知工具] {name}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": f"ERROR: unknown tool '{name}'. Available tools: {sorted(functions)}.",
                })
                continue

            try:
                result = functions[name](**args)
            except Exception as exc:  # surface tool errors back to the model
                print(f"[Python工具报错] {name}: {exc}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": f"TOOL ERROR: {exc}",
                })
                continue

            print("[Python工具返回]")
            print(_bounded(result))

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result),
            })

    raise RuntimeError(
        f"agent exceeded {max_rounds} tool-calling rounds without finishing."
    )
