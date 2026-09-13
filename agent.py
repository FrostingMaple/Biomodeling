import json


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
            print(message)
            print("---------------------------\n")

        if not message.tool_calls:
            return message.content

        messages.append(message)

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            print(f"[DeepSeek决定调用] {name}({args})")

            result = functions[name](**args)

            print("[Python工具返回]")
            print(result)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result),
            })

    raise RuntimeError(
        f"agent exceeded {max_rounds} tool-calling rounds without finishing."
    )
