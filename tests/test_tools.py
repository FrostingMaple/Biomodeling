"""工具层最小测试。"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from biomodeling.agent.agent import _repair_arguments  # noqa: E402
from biomodeling.agent.tools import simulate_model, save_model_ir  # noqa: E402


def minimal_ir():
    return {
        "model_name": "tool test",
        "model_type": "ODE",
        "description": "test",
        "variables": [{"name": "X", "description": "x", "unit": "unknown"}],
        "parameters": [{"name": "r", "description": "rate", "value_known": True, "value": 1.0, "unit": "unknown"}],
        "equations": [{"variable": "X", "expression": "r*X"}],
        "domain": {"t_start": 0, "t_end": 1},
        "initial_conditions": [{"variable": "X", "value_known": True, "value": 1.0}],
        "boundary_conditions": [],
        "origin": {"mode": "self_derived", "source_text": "test", "confidence": "low", "assumptions": []},
        "missing_information": [],
    }


class ToolsTests(unittest.TestCase):
    def test_repair_trailing_comma(self):
        obj, ok = _repair_arguments('{"a": 1, "b": [1, 2,],}')
        self.assertTrue(ok)
        self.assertEqual(obj, {"a": 1, "b": [1, 2]})

    def test_repair_unclosed_object(self):
        obj, ok = _repair_arguments('{"a": {"b": 2}')
        self.assertTrue(ok)
        self.assertEqual(obj, {"a": {"b": 2}})

    def test_save_model_ir_writes_file(self):
        message = save_model_ir(minimal_ir(), tag="unit_tools")
        self.assertIn("Model IR saved to", message)
        path = ROOT / "runs" / "models" / "model_ir_tool_test__unit_tools.json"
        self.assertTrue(path.exists())
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["model_name"], "tool test")
        path.unlink()

    def test_save_model_ir_rejects_invalid_model(self):
        model = minimal_ir()
        model["equations"][0]["variable"] = "Y"
        with self.assertRaises(ValueError) as ctx:
            save_model_ir(model, tag="invalid_unit")
        self.assertIn("Invalid Model IR", str(ctx.exception))

    def test_simulate_model_returns_error_json(self):
        model = minimal_ir()
        model["parameters"][0]["value_known"] = False
        model["parameters"][0].pop("value", None)
        raw = simulate_model(model, tag="unit_tools_error")
        payload = json.loads(raw)
        self.assertEqual(payload["status"], "error")
        self.assertIn("Cannot simulate", payload["error"])


if __name__ == "__main__":
    unittest.main()




