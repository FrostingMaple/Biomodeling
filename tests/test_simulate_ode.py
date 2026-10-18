"""ODE 求解引擎的最小回归测试。"""

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulate import simulate_model  # noqa: E402


def lotka_volterra_ir():
    return {
        "model_name": "test lotka volterra",
        "model_type": "ODE",
        "description": "test model",
        "variables": [
            {"name": "X", "description": "prey", "unit": "unknown"},
            {"name": "Y", "description": "predator", "unit": "unknown"},
        ],
        "parameters": [
            {"name": "a", "description": "growth", "value_known": True, "value": 1.0, "unit": "unknown"},
            {"name": "b", "description": "interaction", "value_known": True, "value": 0.1, "unit": "unknown"},
            {"name": "c", "description": "conversion", "value_known": True, "value": 0.075, "unit": "unknown"},
            {"name": "d", "description": "death", "value_known": True, "value": 1.5, "unit": "unknown"},
        ],
        "equations": [
            {"variable": "X", "expression": "a*X - b*X*Y"},
            {"variable": "Y", "expression": "c*X*Y - d*Y"},
        ],
        "domain": {"t_start": 0, "t_end": 10},
        "initial_conditions": [
            {"variable": "X", "value_known": True, "value": 10},
            {"variable": "Y", "value_known": True, "value": 5},
        ],
        "boundary_conditions": [],
        "origin": {"mode": "reproduce", "source_text": "test", "confidence": "high", "assumptions": []},
        "missing_information": [],
    }


class SimulateOdeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = ROOT / "tests" / "_tmp_output_ode"
        self.tmp.mkdir(parents=True, exist_ok=True)
        for item in self.tmp.iterdir():
            if item.is_file():
                item.unlink()

    def tearDown(self):
        for item in self.tmp.iterdir():
            if item.is_file():
                item.unlink()

    def test_lotka_volterra_runs(self):
        result = simulate_model(lotka_volterra_ir(), output_dir=str(self.tmp), tag="unit")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["model_type"], "ODE")
        results_file = Path(result["results_file"])
        self.assertTrue(results_file.exists())
        payload = json.loads(results_file.read_text(encoding="utf-8"))
        self.assertIn("X", payload)
        self.assertIn("Y", payload)
        self.assertGreater(len(payload["t"]), 0)
        self.assertIn("summary", result)
        self.assertIn("final_state", result["summary"])

    def test_missing_parameter_value_raises(self):
        model = copy.deepcopy(lotka_volterra_ir())
        model["parameters"][0]["value_known"] = False
        model["parameters"][0].pop("value", None)
        with self.assertRaises(ValueError) as ctx:
            simulate_model(model, output_dir=str(self.tmp), tag="missing_param")
        self.assertIn("parameters without numeric values", str(ctx.exception))

    def test_missing_initial_condition_raises(self):
        model = copy.deepcopy(lotka_volterra_ir())
        model["initial_conditions"][0]["value_known"] = False
        model["initial_conditions"][0].pop("value", None)
        with self.assertRaises(ValueError) as ctx:
            simulate_model(model, output_dir=str(self.tmp), tag="missing_ic")
        self.assertIn("missing initial conditions", str(ctx.exception))

    def test_missing_equation_raises(self):
        model = copy.deepcopy(lotka_volterra_ir())
        model["equations"] = model["equations"][:1]
        with self.assertRaises(ValueError) as ctx:
            simulate_model(model, output_dir=str(self.tmp), tag="missing_eq")
        self.assertIn("Equations missing for variables", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
