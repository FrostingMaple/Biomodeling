"""Model IR 运行时校验测试。"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from biomodeling.modeling.model_ir import validate_model_ir  # noqa: E402


def minimal_ir():
    return {
        "model_name": "validator test",
        "model_type": "ODE",
        "description": "test model",
        "variables": [
            {"name": "X", "description": "state", "unit": "unknown"},
        ],
        "parameters": [
            {"name": "r", "description": "rate", "value_known": True, "value": 1.0, "unit": "unknown"},
        ],
        "equations": [
            {"variable": "X", "expression": "r*X"},
        ],
        "domain": {"t_start": 0, "t_end": 1},
        "initial_conditions": [
            {"variable": "X", "value_known": True, "value": 1.0},
        ],
        "boundary_conditions": [],
        "origin": {
            "mode": "self_derived",
            "source_text": "test",
            "confidence": "low",
            "assumptions": [],
        },
        "missing_information": [],
    }


class ModelIrValidationTests(unittest.TestCase):
    def test_valid_model_passes(self):
        report = validate_model_ir(minimal_ir(), for_simulation=True)
        self.assertTrue(report["valid"], report)

    def test_duplicate_variable_fails(self):
        model = minimal_ir()
        model["variables"].append({"name": "X", "description": "duplicate", "unit": "unknown"})
        report = validate_model_ir(model)
        self.assertFalse(report["valid"])
        self.assertTrue(any("duplicate variable" in e for e in report["errors"]))

    def test_equation_references_unknown_variable(self):
        model = minimal_ir()
        model["equations"][0]["variable"] = "Z"
        report = validate_model_ir(model)
        self.assertFalse(report["valid"])
        self.assertTrue(any("unknown variable" in e for e in report["errors"]))

    def test_missing_equation_fails(self):
        model = minimal_ir()
        model["variables"].append({"name": "Y", "description": "second state", "unit": "unknown"})
        model["initial_conditions"].append({"variable": "Y", "value_known": True, "value": 1.0})
        report = validate_model_ir(model)
        self.assertFalse(report["valid"])
        self.assertTrue(any("Equations missing" in e for e in report["errors"]))

    def test_missing_initial_condition_fails_for_simulation(self):
        model = minimal_ir()
        model["initial_conditions"][0]["value_known"] = False
        model["initial_conditions"][0].pop("value", None)
        report = validate_model_ir(model, for_simulation=True)
        self.assertFalse(report["valid"])
        self.assertTrue(any("missing initial conditions" in e for e in report["errors"]))

    def test_known_parameter_without_value_fails(self):
        model = minimal_ir()
        model["parameters"][0].pop("value", None)
        report = validate_model_ir(model, for_simulation=True)
        self.assertFalse(report["valid"])
        self.assertTrue(any("parameters without numeric values" in e for e in report["errors"]))

    def test_pde_requires_spatial_domain(self):
        model = minimal_ir()
        model["model_type"] = "PDE"
        report = validate_model_ir(model)
        self.assertFalse(report["valid"])
        self.assertTrue(any("domain.spatial" in e for e in report["errors"]))

    def test_invalid_origin_mode_fails(self):
        model = minimal_ir()
        model["origin"]["mode"] = "unknown"
        report = validate_model_ir(model)
        self.assertFalse(report["valid"])
        self.assertTrue(any("origin.mode" in e for e in report["errors"]))


if __name__ == "__main__":
    unittest.main()



