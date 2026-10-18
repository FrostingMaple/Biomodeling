import json
import os

from security_utils import redact_secrets
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


def _env_int(name, default, minimum=0):
    """Read an integer environment setting with a safe fallback."""
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        print(f"[agent] invalid {name}={raw!r}; using {default}")
        return default
    if value < minimum:
        print(f"[agent] {name}={value} is below minimum {minimum}; using {minimum}")
        return minimum
    return value


def _usage_total_tokens(response):
    """Best-effort extraction of total token usage from an SDK response."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return 0
    if isinstance(usage, dict):
        value = usage.get("total_tokens")
    else:
        value = getattr(usage, "total_tokens", None)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _emit_event(on_event, event, **payload):
    """Notify the caller without allowing persistence errors to stop the agent."""
    if on_event is None:
        return
    try:
        safe_payload = {
            key: redact_secrets(value) if isinstance(value, str) else value
            for key, value in payload.items()
        }
        on_event(event, **safe_payload)
    except Exception as exc:
        print(f"[agent] event callback failed ({event}): {exc}")


def run_agent(
    client,
    model,
    messages,
    tools,
    functions,
    verbose=True,
    on_event=None,
):
    """Run the LLM tool-calling loop until the model returns a final answer.

    `on_event` is an optional callback receiving (event_name, **payload). It is
    used to persist partial sessions after API/tool events. Retries and network
    timeouts are configured on the OpenAI client in main.py.
    """
    max_rounds = _env_int("BIOMODEL_MAX_TOOL_ROUNDS", 40, minimum=1)
    max_total_tokens = _env_int("BIOMODEL_MAX_TOTAL_TOKENS", 200000, minimum=0)
    total_tokens = 0

    for round_number in range(1, max_rounds + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
        except Exception as exc:
            _emit_event(
                on_event,
                "api_error",
                round=round_number,
                error=f"{type(exc).__name__}: {exc}",
            )
            raise

        usage_tokens = _usage_total_tokens(response)
        total_tokens += usage_tokens
        _emit_event(
            on_event,
            "api_response",
            round=round_number,
            usage_tokens=usage_tokens,
            total_tokens=total_tokens,
        )

        if max_total_tokens > 0 and total_tokens > max_total_tokens:
            error = (
                f"agent token budget exceeded: {total_tokens} > "
                f"{max_total_tokens} (set BIOMODEL_MAX_TOTAL_TOKENS=0 to disable)"
            )
            _emit_event(on_event, "agent_error", error=error)
            raise RuntimeError(error)

        message = response.choices[0].message

        if verbose:
            print("\n--- LLM Raw Output ---")
            print(_bounded(message))
            print("---------------------------\n")

        if not message.tool_calls:
            final_message = _message_to_dict(message)
            final_message.pop("name", None)
            final_message.pop("tool_calls", None)
            messages.append(final_message)
            _emit_event(
                on_event,
                "assistant_message",
                content=message.content,
                total_tokens=total_tokens,
            )
            return message.content

        # Normalise the SDK message for persistent, JSON-serialisable history.
        message_dict = _message_to_dict(message)
        if message_dict.get("name") is None:
            message_dict.pop("name", None)
        messages.append(message_dict)

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            raw_args = tool_call.function.arguments or ""

            args, args_ok = _repair_arguments(raw_args)
            if not args_ok:
                print(f"[LLM调用参数格式错误] {name}")
                error_text = (
                    "ERROR: the arguments for this tool call were not valid "
                    "JSON and could not be repaired. Please retry the call "
                    "with arguments that are a single, complete, valid JSON "
                    f"object. Raw arguments received:\n{raw_args}"
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": error_text,
                })
                _emit_event(on_event, "tool_error", round=round_number, tool=name, error=error_text)
                continue

            print(f"[LLM决定调用] {name}({args})")

            if name not in functions:
                print(f"[未知工具] {name}")
                error_text = (
                    f"ERROR: unknown tool '{name}'. "
                    f"Available tools: {sorted(functions)}."
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": error_text,
                })
                _emit_event(on_event, "tool_error", round=round_number, tool=name, error=error_text)
                continue

            try:
                result = functions[name](**args)
            except Exception as exc:
                print(f"[Python工具报错] {name}: {exc}")
                error_text = f"TOOL ERROR: {redact_secrets(str(exc))}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": error_text,
                })
                _emit_event(on_event, "tool_error", round=round_number, tool=name, error=str(exc))
                continue

            print("[Python工具返回]")
            print(_bounded(result))
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result),
            })
            _emit_event(
                on_event,
                "tool_result",
                round=round_number,
                tool=name,
                total_tokens=total_tokens,
            )

    error = f"agent exceeded {max_rounds} tool-calling rounds without finishing."
    _emit_event(on_event, "agent_error", error=error)
    raise RuntimeError(error)
