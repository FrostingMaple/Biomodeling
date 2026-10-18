"""Integration tests for the unified extraction -> Model IR -> simulation path."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from biomodeling.contracts.extraction_to_model_ir import load_and_convert  # noqa: E402
from biomodeling.modeling.model_ir import validate_model_ir  # noqa: E402
from biomodeling.modeling.simulate import simulate_model  # noqa: E402


class ContractIntegrationTests(unittest.TestCase):
    def test_model_ready_extraction_converts_and_simulates(self):
        extraction = ROOT / "examples" / "model_ready_extraction.json"
        model = load_and_convert(extraction, strict=True)
        self.assertTrue(model["conversion"]["model_ready"])
        validation = validate_model_ir(model, for_simulation=True)
        self.assertTrue(validation["valid"], msg=validation["errors"])
        with tempfile.TemporaryDirectory() as temp_dir:
            result = simulate_model(model, output_dir=temp_dir, tag="contract")
            self.assertEqual(result["status"], "ok")
            self.assertTrue(Path(result["results_file"]).exists())
            self.assertTrue(Path(result["plot_file"]).exists())

    def test_literature_sample_converts_to_explicit_draft(self):
        extraction = ROOT / "examples" / "literature" / "sample_extraction.json"
        model = load_and_convert(extraction)
        self.assertFalse(model["conversion"]["model_ready"])
        self.assertEqual(model["equations"], [])
        self.assertTrue(any("single numeric value" in item for item in model["conversion"]["warnings"]))
        self.assertTrue(model["missing_information"])

    def test_evidence_is_preserved_in_model_ir(self):
        extraction = ROOT / "examples" / "model_ready_extraction.json"
        model = load_and_convert(extraction)
        self.assertTrue(model["evidence"])
        self.assertEqual(model["evidence"][0]["owner_kind"], "research_question")
        self.assertTrue(any(item["owner_kind"] == "variable" for item in model["evidence"]))

    def test_conversion_is_json_serializable(self):
        extraction = ROOT / "examples" / "model_ready_extraction.json"
        model = load_and_convert(extraction)
        encoded = json.dumps(model, ensure_ascii=False)
        self.assertIn("model_ready", encoded)


if __name__ == "__main__":
    unittest.main()
