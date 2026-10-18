"""运行元数据与结果追溯测试。"""

import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulate import simulate_model  # noqa: E402
from tools import save_report  # noqa: E402


def minimal_ir():
    return {
        "model_name": "metadata test",
        "model_type": "ODE",
        "description": "metadata test model",
        "variables": [{"name": "X", "description": "state", "unit": "unknown"}],
        "parameters": [{"name": "r", "description": "rate", "value_known": True, "value": 1.0, "unit": "unknown"}],
        "equations": [{"variable": "X", "expression": "r*X"}],
        "domain": {"t_start": 0, "t_end": 1},
        "initial_conditions": [{"variable": "X", "value_known": True, "value": 1.0}],
        "boundary_conditions": [],
        "origin": {"mode": "reproduce", "source_text": "test", "confidence": "high", "assumptions": []},
        "missing_information": [],
    }


class MetadataTests(unittest.TestCase):
    def test_simulation_json_contains_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = simulate_model(minimal_ir(), output_dir=tmp, tag="metadata")
            payload = json.loads(Path(result["results_file"]).read_text(encoding="utf-8"))
            metadata = payload["run_metadata"]
            self.assertRegex(metadata["run_id"], r"^[0-9a-f]{12}$")
            self.assertEqual(metadata["tag"], "metadata")
            self.assertIn("model_ir_sha256", metadata)
            self.assertEqual(len(metadata["model_ir_sha256"]), 64)
            self.assertIn("python_version", metadata)
            self.assertIn("package_versions", metadata)
            self.assertIn("numpy", metadata["package_versions"])
            self.assertEqual(result["run_metadata"]["run_id"], metadata["run_id"])

    def test_model_hash_is_stable_and_changes_with_model(self):
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            first = simulate_model(minimal_ir(), output_dir=tmp1, tag="a")
            second = simulate_model(minimal_ir(), output_dir=tmp2, tag="b")
            self.assertEqual(
                first["run_metadata"]["model_ir_sha256"],
                second["run_metadata"]["model_ir_sha256"],
            )
            changed = minimal_ir()
            changed["description"] = "different model"
            third = simulate_model(changed, output_dir=tmp1, tag="c")
            self.assertNotEqual(
                first["run_metadata"]["model_ir_sha256"],
                third["run_metadata"]["model_ir_sha256"],
            )

    def test_report_can_embed_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                result = simulate_model(minimal_ir(), output_dir="simout", tag="report")
                message = save_report(
                    "Metadata report",
                    "body",
                    filename="metadata_report",
                    metadata=result["run_metadata"],
                )
                self.assertIn("Report saved to", message)
                report = Path(message.splitlines()[0].split("Report saved to ", 1)[1])
                text = report.read_text(encoding="utf-8")
                self.assertIn("## Run metadata", text)
                self.assertIn(result["run_metadata"]["run_id"], text)
            finally:
                os.chdir(old_cwd)

    def test_report_without_metadata_remains_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                message = save_report("Plain report", "body", filename="plain_report")
                report = Path(message.splitlines()[0].split("Report saved to ", 1)[1])
                text = report.read_text(encoding="utf-8")
                self.assertNotIn("## Run metadata", text)
                self.assertIn("body", text)
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
