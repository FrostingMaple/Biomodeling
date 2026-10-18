"""一维 PDE 边界条件回归测试。"""

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from biomodeling.modeling.simulate import simulate_model  # noqa: E402


def pde_ir(initial_expr="0.5 + 0.5*cos(pi*x)", boundaries=None, spatial=None):
    return {
        "model_name": "pde boundary test",
        "model_type": "PDE",
        "description": "pure diffusion boundary test",
        "variables": [
            {"name": "u", "description": "state", "unit": "unknown"},
        ],
        "parameters": [
            {"name": "D", "description": "diffusion coefficient", "value_known": True, "value": 0.1, "unit": "unknown"},
        ],
        "equations": [
            {"variable": "u", "expression": "D*d2u/dx2"},
        ],
        "domain": {
            "t_start": 0,
            "t_end": 0.1,
            "spatial": spatial or [{"x_start": 0, "x_end": 1, "n_points": 31}],
        },
        "initial_conditions": [
            {"variable": "u", "value_known": True, "expr": initial_expr},
        ],
        "boundary_conditions": boundaries or [],
        "origin": {
            "mode": "self_derived",
            "source_text": "test",
            "confidence": "low",
            "assumptions": [],
        },
        "missing_information": [],
    }


def boundary(var, side, kind, value):
    return {"variable": var, "boundary": side, "type": kind, "value": value}


class PdeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_zero_dirichlet_boundaries_remain_zero(self):
        model = pde_ir(
            initial_expr="1 - (x - 0.5)**2",
            boundaries=[
                boundary("u", "left", "dirichlet", 0.0),
                boundary("u", "right", "dirichlet", 0.0),
            ],
        )
        result = simulate_model(model, output_dir=self.tmp.name, tag="dirichlet_zero")
        data = result["summary"]
        self.assertEqual(result["status"], "ok")
        self.assertIn("final_profile", data)

    def test_nonzero_dirichlet_is_enforced(self):
        model = pde_ir(
            initial_expr="0",
            boundaries=[
                boundary("u", "left", "dirichlet", 1.0),
                boundary("u", "right", "dirichlet", 2.0),
            ],
        )
        output_dir = ROOT / "tests" / "_tmp_pde"
        result = simulate_model(model, output_dir=str(output_dir), tag="dirichlet_nonzero")
        path = Path(result["results_file"])
        import json
        payload = json.loads(path.read_text(encoding="utf-8"))
        values = np.asarray(payload["u"])
        self.assertAlmostEqual(float(values[0, 0]), 1.0, places=6)
        self.assertAlmostEqual(float(values[0, -1]), 2.0, places=6)
        self.assertAlmostEqual(float(values[-1, 0]), 1.0, places=5)
        self.assertAlmostEqual(float(values[-1, -1]), 2.0, places=5)

    def test_zero_neumann_conserves_mass(self):
        model = pde_ir(
            initial_expr="0.5 + 0.5*cos(pi*x)",
            boundaries=[
                boundary("u", "left", "neumann", 0.0),
                boundary("u", "right", "neumann", 0.0),
            ],
        )
        output_dir = ROOT / "tests" / "_tmp_pde"
        result = simulate_model(model, output_dir=str(output_dir), tag="neumann_zero")
        import json
        payload = json.loads(Path(result["results_file"]).read_text(encoding="utf-8"))
        values = np.asarray(payload["u"])
        mass_start = float(values[0].sum())
        mass_end = float(values[-1].sum())
        self.assertAlmostEqual(mass_end, mass_start, delta=max(1e-3, abs(mass_start) * 1e-3))

    def test_nonzero_neumann_adds_mass(self):
        model = pde_ir(
            initial_expr="0",
            boundaries=[
                boundary("u", "left", "neumann", -0.1),
                boundary("u", "right", "neumann", 0.0),
            ],
        )
        result = simulate_model(model, output_dir=self.tmp.name, tag="neumann_flux")
        self.assertEqual(result["status"], "ok")
        self.assertGreater(result["summary"]["final_profile"]["u"]["max"], 1e-6)

    def test_multiple_spatial_intervals_are_rejected(self):
        model = pde_ir(
            spatial=[
                {"x_start": 0, "x_end": 0.5, "n_points": 21},
                {"x_start": 0.5, "x_end": 1.0, "n_points": 21},
            ],
        )
        with self.assertRaises(ValueError) as ctx:
            simulate_model(model, output_dir=self.tmp.name, tag="multi_interval")
        self.assertIn("exactly one spatial interval", str(ctx.exception))

    def test_missing_spatial_domain_is_rejected(self):
        model = pde_ir()
        model["domain"].pop("spatial")
        with self.assertRaises(ValueError) as ctx:
            simulate_model(model, output_dir=self.tmp.name, tag="missing_spatial")
        self.assertIn("domain.spatial", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()



