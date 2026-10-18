"""安全与隐私相关测试。"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from security_utils import redact_secrets, safe_filename, safe_identifier  # noqa: E402
from tools import read_text, save_model_ir, save_report  # noqa: E402


def minimal_ir():
    return {
        "model_name": "security test",
        "model_type": "ODE",
        "description": "security test model",
        "variables": [{"name": "X", "description": "state", "unit": "unknown"}],
        "parameters": [{"name": "r", "description": "rate", "value_known": True, "value": 1.0, "unit": "unknown"}],
        "equations": [{"variable": "X", "expression": "r*X"}],
        "domain": {"t_start": 0, "t_end": 1},
        "initial_conditions": [{"variable": "X", "value_known": True, "value": 1.0}],
        "boundary_conditions": [],
        "origin": {"mode": "self_derived", "source_text": "test", "confidence": "low", "assumptions": []},
        "missing_information": [],
    }


class SecurityTests(unittest.TestCase):
    def test_external_read_is_rejected_by_default(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as handle:
            handle.write("external")
            path = Path(handle.name)
        try:
            result = read_text(str(path))
            self.assertIn("ERROR", result)
            self.assertIn("inside the project root", result)
        finally:
            path.unlink(missing_ok=True)

    def test_external_read_can_be_enabled_explicitly(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as handle:
            handle.write("external")
            path = Path(handle.name)
        try:
            with patch.dict(os.environ, {"BIOMODEL_ALLOW_EXTERNAL_READS": "1"}, clear=False):
                self.assertEqual(read_text(str(path)), "external")
        finally:
            path.unlink(missing_ok=True)

    def test_project_file_can_be_read(self):
        text = read_text("README.md")
        self.assertIn("biomodel-agent", text)

    def test_safe_identifier_rejects_traversal(self):
        for value in ("../x", "a/b", r"a\b", "..", "C:\\x"):
            with self.assertRaises(ValueError):
                safe_identifier(value)

    def test_safe_filename_rejects_traversal(self):
        for value in ("../x.md", "a/b.md", r"a\b.md", "..", "C:\\x.md"):
            with self.assertRaises(ValueError):
                safe_filename(value)

    def test_save_report_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                with self.assertRaises(ValueError):
                    save_report("title", "body", filename="../outside.md")
                self.assertFalse((Path(tmp) / "outside.md").exists())
            finally:
                os.chdir(old_cwd)

    def test_save_model_ir_rejects_unsafe_tag(self):
        with self.assertRaises(ValueError):
            save_model_ir(minimal_ir(), tag="../outside")

    def test_redact_secrets(self):
        secret = "sk-verysecret123456"
        self.assertEqual(redact_secrets(f"key={secret}"), "key=[REDACTED]")
        self.assertNotIn(secret, redact_secrets(f"error {secret}"))


if __name__ == "__main__":
    unittest.main()
