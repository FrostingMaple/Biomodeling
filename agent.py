import json


def run_agent(
    client,
    model,
    messages,
    tools,
    functions
):

    while True:

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        message = response.choices[0].message

        print("\n--- DeepSeek Raw Output ---")
        print(message)
        print("---------------------------\n")

        if not message.tool_calls:
            return message.content

        messages.append(message)

        for tool_call in message.tool_calls:

            name = tool_call.function.name

            args = json.loads(
                tool_call.function.arguments
            )

            print(
                f"[DeepSeek决定调用] "
                f"{name}({args})"
            )

            result = functions[name](**args)

            print("[Python工具返回]")
            print(result)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result),
            })