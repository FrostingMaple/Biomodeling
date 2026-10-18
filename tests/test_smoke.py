"""端到端 smoke test：不调用 LLM，仅验证 demo 流程可用。"""

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class DemoSmokeTests(unittest.TestCase):
    def test_demo_runs_and_writes_artifacts(self):
        completed = subprocess.run(
            [sys.executable, "-m", "biomodeling.cli", "demo"],
            cwd=str(ROOT),
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
        self.assertEqual(completed.returncode, 0, msg=completed.stdout + completed.stderr)

        report = ROOT / "runs" / "reports" / "report_lotka_volterra_reproduce.md"
        sim_json = ROOT / "runs" / "simulation" / "simulation_lotka_volterra_predator_prey_model__reproduce.json"
        model_ir = ROOT / "runs" / "models" / "model_ir_lotka_volterra_predator_prey_model__reproduce.json"

        self.assertTrue(model_ir.exists(), "Model IR was not written")
        self.assertTrue(sim_json.exists(), "simulation JSON was not written")
        self.assertTrue(report.exists(), "report was not written")


if __name__ == "__main__":
    unittest.main()





