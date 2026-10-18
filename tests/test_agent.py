"""Agent 工具循环可靠性测试（不访问网络）。"""

import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from biomodeling.agent.agent import run_agent  # noqa: E402


class FakeClient:
    def __init__(self, responses):
        self._responses = iter(responses)
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create),
        )

    def _create(self, **kwargs):
        return next(self._responses)


def make_response(message, total_tokens=None):
    usage = SimpleNamespace(total_tokens=total_tokens) if total_tokens is not None else None
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message)],
        usage=usage,
    )


def make_message(content=None, tool_calls=None):
    return SimpleNamespace(
        role="assistant",
        content=content,
        tool_calls=tool_calls or [],
    )


def make_tool_call(name, arguments, call_id="call-1"):
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(name=name, arguments=arguments),
    )


class AgentReliabilityTests(unittest.TestCase):
    def test_direct_final_response(self):
        client = FakeClient([make_response(make_message(content="done"))])
        messages = [{"role": "user", "content": "hello"}]
        answer = run_agent(client, "fake", messages, [], [], verbose=False)
        self.assertEqual(answer, "done")
        self.assertEqual(messages[-1]["role"], "assistant")
        self.assertEqual(messages[-1]["content"], "done")

    def test_tool_call_then_final(self):
        tool = make_tool_call("echo", '{"value": "x"}')
        client = FakeClient([
            make_response(make_message(tool_calls=[tool])),
            make_response(make_message(content="finished")),
        ])
        messages = [{"role": "user", "content": "run"}]
        answer = run_agent(client, "fake", messages, [], {"echo": lambda value: f"echo:{value}"}, verbose=False)
        self.assertEqual(answer, "finished")
        self.assertTrue(any(m.get("role") == "tool" for m in messages))

    def test_malformed_tool_json_is_reported(self):
        tool = make_tool_call("echo", '{bad json')
        events = []
        client = FakeClient([
            make_response(make_message(tool_calls=[tool])),
            make_response(make_message(content="recovered")),
        ])
        answer = run_agent(
            client,
            "fake",
            [{"role": "user", "content": "run"}],
            [],
            {"echo": lambda value: value},
            verbose=False,
            on_event=lambda event, **data: events.append((event, data)),
        )
        self.assertEqual(answer, "recovered")
        self.assertTrue(any(event == "tool_error" for event, _ in events))

    def test_tool_error_is_reported(self):
        tool = make_tool_call("explode", '{}')
        events = []

        def explode():
            raise RuntimeError("boom")

        client = FakeClient([
            make_response(make_message(tool_calls=[tool])),
            make_response(make_message(content="handled")),
        ])
        answer = run_agent(
            client,
            "fake",
            [{"role": "user", "content": "run"}],
            [],
            {"explode": explode},
            verbose=False,
            on_event=lambda event, **data: events.append((event, data)),
        )
        self.assertEqual(answer, "handled")
        self.assertTrue(any(event == "tool_error" for event, _ in events))

    def test_max_tool_rounds(self):
        tool = make_tool_call("echo", '{}')
        client = FakeClient([make_response(make_message(tool_calls=[tool]))])
        with patch.dict(os.environ, {"BIOMODEL_MAX_TOOL_ROUNDS": "1"}, clear=False):
            with self.assertRaises(RuntimeError) as ctx:
                run_agent(client, "fake", [{"role": "user", "content": "run"}], [], {"echo": lambda: "ok"})
        self.assertIn("exceeded 1 tool-calling rounds", str(ctx.exception))

    def test_token_budget(self):
        client = FakeClient([make_response(make_message(content="too late"), total_tokens=6)])
        with patch.dict(os.environ, {"BIOMODEL_MAX_TOTAL_TOKENS": "5"}, clear=False):
            with self.assertRaises(RuntimeError) as ctx:
                run_agent(client, "fake", [{"role": "user", "content": "run"}], [], {})
        self.assertIn("token budget exceeded", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()



