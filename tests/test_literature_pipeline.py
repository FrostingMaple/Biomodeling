"""Standard-library tests for the extraction pipeline."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "literature"
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from biomodeling.literature.doi import looks_like_doi, normalize_doi, resolve_doi
from biomodeling.literature.export import convert_source, markdown_from_text
from biomodeling.literature.ocr import OcrResult, OcrUnavailable, detect_backend, ocr_image
from biomodeling.literature.audit import audit_extraction
from biomodeling.literature.lexicon import entries, lexicon_summary, load_all_lexicons, match_parameters
from biomodeling.literature.parameter_export import export_parameters_markdown, render_parameters_markdown, safe_filename
from biomodeling.literature.symbol_normalization import derivative_expression, normalize_payload, normalize_symbol
from biomodeling.literature.semantic_review import semantic_review
from biomodeling.literature.extraction import (
    build_sections,
    chunk_sections,
    read_and_chunk,
    read_source_document,
)
from biomodeling.literature.batch import normalize_scaffold_for_review
from biomodeling.literature.scaffold import _candidate_variables, _equation_relationships, scaffold_from_source
from biomodeling.literature.io_utils import load_json
from biomodeling.literature.rendering import render_markdown
from biomodeling.literature.validation import validate_extraction


class ExtractionTests(unittest.TestCase):
    def test_build_sections_detects_headings(self) -> None:
        text = "# Abstract\n\nSome abstract text.\n\n# Methods\n\nSome methods text."
        sections = build_sections(text)
        self.assertEqual([section.section for section in sections], ["abstract", "methods"])

    def test_chunks_do_not_cross_sections(self) -> None:
        text = "# Abstract\n\n" + "word " * 300 + "\n\n# Results\n\n" + "result " * 300
        sections = build_sections(text)
        chunks = chunk_sections(sections, target_words=50, max_words=80)
        self.assertGreater(len(chunks), 2)
        block_ids = [chunk["block_id"] for chunk in chunks]
        self.assertEqual(len(block_ids), len(set(block_ids)))
        self.assertEqual(chunks[0]["section"], "abstract")
        self.assertEqual(chunks[-1]["section"], "results")

    def test_read_and_chunk_markdown(self) -> None:
        paper = EXAMPLES / "sample_paper.md"
        if not paper.is_file():
            self.skipTest("sample_paper.md fixture is not present")
        source, chunks = read_and_chunk(paper)
        self.assertGreater(source["word_count"], 100)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk["block_id"].startswith("B") for chunk in chunks))

    def test_read_docx_paragraphs_headings_and_tables(self) -> None:
        document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Abstract</w:t></w:r></w:p>
    <w:p><w:r><w:t>Growth rate is modeled as a function of substrate concentration.</w:t></w:r></w:p>
    <w:tbl>
      <w:tr><w:tc><w:p><w:r><w:t>Parameter</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Value</w:t></w:r></w:p></w:tc></w:tr>
      <w:tr><w:tc><w:p><w:r><w:t>mu_max</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>0.61 per hour</w:t></w:r></w:p></w:tc></w:tr>
    </w:tbl>
  </w:body>
</w:document>
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "paper.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", document_xml)
            document = read_source_document(path)
        self.assertIn("# Abstract", document.text)
        self.assertIn("Growth rate is modeled", document.text)
        self.assertIn("mu_max | 0.61 per hour", document.text)
        self.assertEqual(document.metadata.get("format"), "docx")


class PdfTests(unittest.TestCase):
    def test_pdf_reading_reports_pages_sections_and_equations(self) -> None:
        from biomodeling.literature.pdf import read_pdf

        pdf_path = EXAMPLES / "sample_pdf.pdf"
        if not pdf_path.is_file():
            self.skipTest("sample_pdf.pdf fixture is not present")
        extraction = read_pdf(pdf_path)
        self.assertGreaterEqual(extraction.page_count, 2)
        self.assertGreater(extraction.text_page_count, 0)
        self.assertTrue(extraction.backend)
        self.assertEqual(extraction.backend, "pdfplumber-bundled")
        self.assertTrue(any(page == 1 for page in extraction.pages if page is not None))
        self.assertTrue(any(page == 2 for page in extraction.pages if page is not None))

        source, chunks = read_and_chunk(pdf_path)
        sections = {str(chunk.get("section")) for chunk in chunks}
        self.assertIn("abstract", sections)
        self.assertIn("parameters", sections)
        self.assertGreater(len(_equation_relationships(chunks)), 0)

    def test_missing_pdf_backend_reports_actionable_error(self) -> None:
        from biomodeling.literature import pdf as pdf_module

        with mock.patch.object(pdf_module, "_read_with_bundled_runtime", return_value=None), \
             mock.patch.object(pdf_module, "_read_with_pdfplumber", side_effect=pdf_module._BackendUnavailable("pdfplumber is not installed")), \
             mock.patch.object(pdf_module, "_read_with_pypdf", side_effect=pdf_module._BackendUnavailable("pypdf is not installed")):
            with self.assertRaises(Exception) as context:
                pdf_module.read_pdf(Path("missing.pdf"))
        self.assertIn("pdfplumber", str(context.exception))
        self.assertIn("pypdf", str(context.exception))


class MarkdownExportTests(unittest.TestCase):
    def test_markdown_from_text_renders_tables_and_headings(self) -> None:
        text = "# Abstract\n\nSome text.\n\nTABLE_ROW: mu_max | 0.61 | per hour\n"
        markdown = markdown_from_text(text)
        self.assertIn("# Abstract", markdown)
        self.assertIn("| mu_max | 0.61 | per hour |", markdown)
        self.assertIn("Some text.", markdown)

    def test_convert_pdf_writes_markdown_and_page_images(self) -> None:
        pdf_path = EXAMPLES / "sample_pdf.pdf"
        if not pdf_path.is_file():
            self.skipTest("sample_pdf.pdf fixture is not present")
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "export"
            result = convert_source(
                pdf_path,
                out_dir,
                extract_images=True,
                ocr_mode="never",
                image_mode="page",
            )
            document = out_dir / "document.md"
            manifest = out_dir / "image_manifest.json"
            self.assertTrue(document.is_file())
            self.assertTrue(manifest.is_file())
            self.assertIn("Extracted Assets", document.read_text(encoding="utf-8"))
            page_assets = [asset for asset in result.assets if asset.kind == "page"]
            self.assertGreaterEqual(len(page_assets), 2)
            for asset in page_assets:
                self.assertTrue(asset.path.is_file())
                self.assertGreater(asset.path.stat().st_size, 0)

    def test_convert_docx_extracts_media_and_tables(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            docx_path = temp / "paper.docx"
            _write_sample_docx(docx_path)
            out_dir = temp / "export"
            result = convert_source(docx_path, out_dir, extract_images=True, ocr_mode="never")
            document = (out_dir / "document.md").read_text(encoding="utf-8")
            self.assertIn("mu_max | 0.61 per hour", document)
            embedded = [asset for asset in result.assets if asset.kind == "embedded"]
            self.assertEqual(len(embedded), 1)
            self.assertTrue(embedded[0].path.is_file())

    def test_figure_captions_render_into_markdown(self) -> None:
        from biomodeling.literature.export import reference_jats_images_from_text

        jats = """<article><body><fig id="f1"><caption><p>Model overview</p></caption>
        <graphic xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="figure1.jpg"/></fig></body></article>"""
        with tempfile.TemporaryDirectory() as temp_dir:
            assets_dir = Path(temp_dir) / "assets"
            assets_dir.mkdir()
            warnings: list[str] = []
            assets = reference_jats_images_from_text(
                jats, assets_dir, warnings, source_label="paper.xml"
            )
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0].kind, "remote_reference")
        self.assertIn("Model overview", assets[0].caption)
        self.assertTrue(warnings)

    def test_ocr_warning_when_no_backend_available(self) -> None:
        with mock.patch("biomodeling.literature.export.detect_backend", return_value=None):
            assets = []
            from biomodeling.literature.export import Asset, _run_ocr

            with tempfile.TemporaryDirectory() as temp_dir:
                image = Path(temp_dir) / "page.png"
                image.write_bytes(b"png")
                assets.append(Asset(asset_id="page-001", path=image, source="x", kind="page", page=1))
                warnings: list[str] = []
                _run_ocr(assets, lang="eng", backend="auto", warnings=warnings)
                self.assertTrue(any("No local OCR backend" in warning for warning in warnings))
                self.assertEqual(assets[0].ocr_text, "")

    def test_ocr_uses_mocked_backend(self) -> None:
        with mock.patch("biomodeling.literature.export.detect_backend", return_value="tesseract"), \
             mock.patch(
                 "biomodeling.literature.export.ocr_image",
                 return_value=OcrResult(text="mu_max = 0.61 per hour", backend="tesseract"),
             ):
            from biomodeling.literature.export import Asset, _run_ocr

            with tempfile.TemporaryDirectory() as temp_dir:
                image = Path(temp_dir) / "page.png"
                image.write_bytes(b"png")
                assets = [Asset(asset_id="page-001", path=image, source="x", kind="page", page=1)]
                warnings: list[str] = []
                _run_ocr(assets, lang="eng", backend="auto", warnings=warnings)
        self.assertEqual(assets[0].ocr_backend, "tesseract")
        self.assertIn("mu_max", assets[0].ocr_text)


class OcrTests(unittest.TestCase):
    def test_detect_backend_returns_none_when_nothing_available(self) -> None:
        with mock.patch("biomodeling.literature.ocr.shutil.which", return_value=None), \
             mock.patch("biomodeling.literature.ocr.importlib.util.find_spec", return_value=None):
            self.assertIsNone(detect_backend("auto"))

    def test_ocr_image_raises_without_backend(self) -> None:
        with mock.patch("biomodeling.literature.ocr.detect_backend", return_value=None):
            with self.assertRaises(OcrUnavailable):
                ocr_image(Path("missing.png"))


class EquationTests(unittest.TestCase):
    def test_equation_extraction_and_variable_linkage(self) -> None:
        chunks = [
            {
                "block_id": "B0001",
                "section": "model",
                "page": None,
                "text": "The specific growth rate is given by mu = mu_max * S / (K_s + S) for all runs.",
            }
        ]
        relationships = _equation_relationships(chunks)
        self.assertEqual(len(relationships), 1)
        self.assertEqual(relationships[0]["type"], "equation")
        self.assertIn("mu", relationships[0]["from"])
        self.assertTrue(any("mu_max" in item for item in relationships[0]["to"]))

        variables, _stats = _candidate_variables(
            chunks,
            max_variables=10,
            equation_relationships=relationships,
        )
        names = {variable["raw_name"].lower() for variable in variables}
        self.assertIn("mu", names)
        self.assertIn("mu_max", names)


class DoiTests(unittest.TestCase):
    def test_looks_like_and_normalize_doi(self) -> None:
        self.assertTrue(looks_like_doi("10.1038/s41586-020-2649-2"))
        self.assertTrue(looks_like_doi("https://doi.org/10.1038/s41586-020-2649-2"))
        self.assertFalse(looks_like_doi("./paper.pdf"))
        self.assertEqual(
            normalize_doi("https://doi.org/10.1038/s41586-020-2649-2"),
            "10.1038/s41586-020-2649-2",
        )

    def test_resolve_doi_uses_abstract_when_full_text_unavailable(self) -> None:
        crossref = {
            "message": {
                "title": ["A minimal model"],
                "author": [{"given": "Ada", "family": "Lovelace"}],
                "issued": {"date-parts": [[2020, 1, 1]]},
                "abstract": "<p>We model growth rate as a function of substrate.</p>",
                "container-title": ["Journal of Models"],
                "URL": "https://doi.org/10.1234/example",
            }
        }
        with mock.patch("biomodeling.literature.doi._fetch_crossref", return_value=crossref["message"]),              mock.patch("biomodeling.literature.doi._fetch_full_text", return_value=None):
            source, chunks, document = resolve_doi("10.1234/example")
        self.assertEqual(source["metadata"]["access"], "abstract_only")
        self.assertEqual(source["metadata"]["doi"], "10.1234/example")
        self.assertIn("substrate", document.text)
        self.assertGreater(len(chunks), 0)


class ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = load_json(EXAMPLES / "sample_extraction.json")
        self.source = load_json(EXAMPLES / "sample_source.json")
        self.block_ids = {
            chunk["block_id"]
            for chunk in self.source["chunks"]
            if isinstance(chunk, dict) and chunk.get("block_id")
        }

    def test_sample_extraction_is_valid(self) -> None:
        report = validate_extraction(self.payload, known_block_ids=self.block_ids)
        self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_sample_extraction_passes_final_gate(self) -> None:
        report = validate_extraction(
            self.payload,
            known_block_ids=self.block_ids,
            final=True,
        )
        self.assertTrue(report.ok, msg="\n".join(report.errors))

    def test_final_gate_rejects_scaffold(self) -> None:
        payload = json.loads(json.dumps(self.payload))
        payload["extraction_metadata"]["extractor"] = "bio_variable_extractor scaffold"
        payload["extraction_metadata"]["review_status"] = "scaffold"
        payload["extraction_metadata"]["reviewer"] = ""
        payload["extraction_metadata"]["reviewed_at"] = ""
        payload["variables"][0]["confidence"] = "low"
        payload["variables"][0]["notes"] = "Automatically proposed candidate; requires semantic confirmation."
        report = validate_extraction(payload, final=True)
        self.assertFalse(report.ok)
        self.assertTrue(any("scaffold extractor" in error for error in report.errors))
        self.assertTrue(any("review_status='reviewed'" in error for error in report.errors))
        self.assertTrue(any("low-confidence" in error for error in report.errors))

    def test_scaffold_is_explicitly_marked_as_draft(self) -> None:
        scaffold = scaffold_from_source(EXAMPLES / "sample_source.json", max_variables=5)
        self.assertEqual(scaffold["extraction_metadata"]["review_status"], "scaffold")
        self.assertEqual(scaffold["extraction_metadata"]["reviewer"], "")
        report = validate_extraction(scaffold, final=True)
        self.assertFalse(report.ok)
        self.assertTrue(any("scaffold" in error.lower() for error in report.errors))

    def test_review_normalization_remains_non_final(self) -> None:
        scaffold = scaffold_from_source(EXAMPLES / "sample_source.json", max_variables=5)
        review = normalize_scaffold_for_review(scaffold)
        self.assertEqual(review["extraction_metadata"]["review_status"], "needs_review")
        self.assertTrue(all("Pending semantic review" in item["notes"] for item in review["variables"]))
        report = validate_extraction(review, final=True)
        self.assertFalse(report.ok)

    def test_unknown_block_is_rejected(self) -> None:
        payload = json.loads(json.dumps(self.payload))
        payload["variables"][0]["evidence"][0]["block_id"] = "B9999"
        report = validate_extraction(payload, known_block_ids=self.block_ids)
        self.assertFalse(report.ok)
        self.assertTrue(any("B9999" in error for error in report.errors))

    def test_unknown_relationship_target_is_rejected(self) -> None:
        payload = json.loads(json.dumps(self.payload))
        payload["relationships"][0]["to"] = ["V999"]
        report = validate_extraction(payload)
        self.assertFalse(report.ok)



class AccuracyAndReviewTests(unittest.TestCase):
    def test_scaffold_keeps_parameter_symbols_and_drops_units(self) -> None:
        from biomodeling.literature.scaffold import scaffold_from_source
        import tempfile, json

        source = {
            "source_path": "test.xml",
            "source_name": "test.xml",
            "section_count": 1,
            "chunk_count": 1,
            "metadata": {"title": "Kinetic test", "language": "en"},
            "chunks": [
                {
                    "block_id": "B0001",
                    "section": "methods",
                    "text": "The association rate constant k_on was 1.5 per s. Km was 2 mM. We measured GFP concentration at 5 mM.",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "source.json"
            source_path.write_text(json.dumps(source), encoding="utf-8")
            payload = scaffold_from_source(source_path, max_variables=50)
        names = {item["raw_name"] for item in payload["variables"]}
        self.assertIn("k_on", names)
        self.assertIn("Km", names)
        self.assertNotIn("mM", names)
        self.assertNotIn("we", names)

    def test_self_audit_flags_units_and_stopwords(self) -> None:
        payload = {
            "variables": [
                {
                    "variable_id": "V001",
                    "raw_name": "mM",
                    "canonical_name": "mM",
                    "symbol": "mM",
                    "aliases": [],
                    "role": "other",
                    "kind": "continuous",
                    "definition": "unit",
                    "unit": "Not reported",
                    "value_or_range": "Not reported",
                    "relationship": "Not reported",
                    "evidence": [{"block_id": "B0001", "quote": "5 mM", "page": None, "section": ""}],
                    "confidence": "low",
                    "notes": "candidate",
                }
            ]
        }
        report = audit_extraction(payload)
        codes = {finding.code for finding in report.findings}
        self.assertIn("non_variable_candidate", codes)

    def test_semantic_review_normalises_and_removes_fragments(self) -> None:
        payload = {
            "schema_version": "1.0",
            "document": {"title": "T", "source_path": "s", "source_name": "s", "language": "en"},
            "research_question": {"question": "Q", "scope": "S", "evidence": [{"block_id": "B0001", "quote": "Q"}]},
            "study_profile": {},
            "variables": [
                {
                    "variable_id": "V001",
                    "raw_name": "k_on",
                    "canonical_name": "Kon",
                    "symbol": "kon",
                    "aliases": [],
                    "role": "other",
                    "kind": "continuous",
                    "definition": "candidate",
                    "unit": "Not reported",
                    "value_or_range": "Not reported",
                    "relationship": "Not reported",
                    "evidence": [{"block_id": "B0001", "quote": "k_on was 1.5 per s", "page": None, "section": ""}],
                    "confidence": "low",
                    "notes": "candidate",
                },
                {
                    "variable_id": "V002",
                    "raw_name": "begin{array}",
                    "canonical_name": "Begin",
                    "symbol": "beg",
                    "aliases": [],
                    "role": "other",
                    "kind": "continuous",
                    "definition": "fragment",
                    "unit": "Not reported",
                    "value_or_range": "Not reported",
                    "relationship": "Not reported",
                    "evidence": [{"block_id": "B0001", "quote": "begin{array}", "page": None, "section": ""}],
                    "confidence": "low",
                    "notes": "candidate",
                },
            ],
            "relationships": [],
            "unresolved": [],
            "extraction_metadata": {"extracted_at": "x", "extractor": "scaffold", "coverage": "x", "method": "x", "warnings": []},
        }
        reviewed, report = semantic_review(payload, mark_reviewed=True)
        self.assertEqual(len(reviewed["variables"]), 1)
        self.assertEqual(reviewed["variables"][0]["symbol"], "k_on")
        self.assertEqual(reviewed["variables"][0]["role"], "parameter")
        self.assertTrue(report.ok)

class LexiconTests(unittest.TestCase):
    def test_all_lexicons_load_and_have_unique_ids(self) -> None:
        lexicons = load_all_lexicons()
        self.assertEqual(set(lexicons), {"parameters", "relations", "expressions", "models"})
        for name, payload in lexicons.items():
            ids = [entry["id"] for entry in payload["entries"]]
            self.assertEqual(len(ids), len(set(ids)), msg=f"duplicate IDs in {name}")
            self.assertTrue(payload["sources"], msg=f"missing sources in {name}")

    def test_lexicon_cross_references_resolve(self) -> None:
        lexicons = load_all_lexicons()
        parameter_ids = {entry["id"] for entry in lexicons["parameters"]["entries"]}
        expression_ids = {entry["id"] for entry in lexicons["expressions"]["entries"]}
        relation_ids = {entry["id"] for entry in lexicons["relations"]["entries"]}
        for expression in lexicons["expressions"]["entries"]:
            for parameter_id in expression["parameters"]:
                self.assertIn(parameter_id, parameter_ids)
        for model in lexicons["models"]["entries"]:
            for parameter_id in model["parameters"]:
                self.assertIn(parameter_id, parameter_ids)
            for expression_id in model["expressions"]:
                self.assertIn(expression_id, expression_ids)
            for relation_id in model["relations"]:
                self.assertIn(relation_id, relation_ids)

    def test_parameter_matching_finds_canonical_symbols(self) -> None:
        matches = match_parameters("The fitted Km was 2 mM and kcat was 5 per s.")
        ids = {entry["id"] for entry in matches}
        self.assertIn("PARAM_KM", ids)
        self.assertIn("PARAM_KCAT", ids)

    def test_lexicon_summary_counts(self) -> None:
        summary = lexicon_summary()
        self.assertGreaterEqual(summary["parameters"]["entry_count"], 30)
        self.assertGreaterEqual(summary["models"]["entry_count"], 20)


class LosslessAndProtectionTests(unittest.TestCase):
    def test_default_max_variables_is_lossless(self) -> None:
        import inspect
        from biomodeling.literature.scaffold import scaffold_from_source
        signature = inspect.signature(scaffold_from_source)
        self.assertEqual(signature.parameters["max_variables"].default, 0)

    def test_truncation_is_reported_explicitly(self) -> None:
        import json, tempfile
        from biomodeling.literature.scaffold import scaffold_from_source

        source = {
            "source_path": "s",
            "source_name": "s",
            "section_count": 1,
            "chunk_count": 1,
            "metadata": {"title": "T", "language": "en"},
            "chunks": [{"block_id": "B0001", "section": "methods", "text": " ".join(
                f"rate constant k{i} was {i} per s." for i in range(30)
            )}],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "source.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            payload = scaffold_from_source(path, max_variables=5)
        metadata = payload["extraction_metadata"]
        self.assertEqual(metadata["retained_candidate_count"], 5)
        self.assertGreater(metadata["truncated_candidate_count"], 0)
        self.assertTrue(any("dropped by --max-variables" in w for w in metadata["warnings"]))

    def test_protected_parameters_survive_small_cap(self) -> None:
        import json, tempfile
        from biomodeling.literature.scaffold import scaffold_from_source

        text = " ".join(["filler words here"] * 40) + " Km was 2 mM. k_off was 1 per s. kcat was 5 per s."
        source = {
            "source_path": "s", "source_name": "s", "section_count": 1, "chunk_count": 1,
            "metadata": {"title": "T", "language": "en"},
            "chunks": [{"block_id": "B0001", "section": "methods", "text": text}],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "source.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            payload = scaffold_from_source(path, max_variables=5)
        names = {v["raw_name"].lower() for v in payload["variables"]}
        self.assertTrue({"km", "k_off", "kcat"} & names, msg=f"protected parameters missing: {names}")




class ParameterExportTests(unittest.TestCase):
    def _payload(self):
        return {
            "document": {"title": "Test Model", "source_name": "test.xml", "language": "en", "doi": "10.0/test", "year": 2026},
            "research_question": {"question": "Q", "scope": "S", "evidence": [{"block_id": "B0001", "quote": "Q"}]},
            "study_profile": {"organism_or_system": "human"},
            "variables": [
                {
                    "variable_id": "V001", "raw_name": "Km", "canonical_name": "Michaelis constant",
                    "symbol": "Km", "aliases": [], "role": "parameter", "kind": "continuous",
                    "definition": "half saturation", "unit": "mM", "value_or_range": "2",
                    "relationship": "Not reported", "confidence": "high", "notes": "n",
                    "evidence": [{"block_id": "B0001", "quote": "Km was 2 mM", "page": None, "section": "methods"}],
                },
                {
                    "variable_id": "V002", "raw_name": "response", "canonical_name": "response",
                    "symbol": "r", "aliases": [], "role": "dependent", "kind": "continuous",
                    "definition": "outcome", "unit": "Not reported", "value_or_range": "Not reported",
                    "relationship": "Not reported", "confidence": "medium", "notes": "n",
                    "evidence": [{"block_id": "B0001", "quote": "response increased", "page": None, "section": ""}],
                },
            ],
            "relationships": [{"relationship_id": "R001", "type": "directional", "from": ["V001"], "to": ["V002"], "expression": "Km affects response", "evidence": [{"block_id": "B0001", "quote": "Km affects response"}], "notes": "n"}],
            "unresolved": [],
            "extraction_metadata": {"extracted_at": "x", "extractor": "test", "coverage": "c", "method": "m", "warnings": [], "review_status": "reviewed", "reviewer": "r", "reviewed_at": "y"},
        }

    def test_render_contains_parameter_table_and_evidence(self) -> None:
        text = render_parameters_markdown(self._payload())
        self.assertIn("## Parameter Summary", text)
        self.assertIn("Michaelis constant", text)
        self.assertIn("Km was 2 mM", text)
        self.assertIn("## Relationships", text)

    def test_export_writes_markdown_file(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            path = export_parameters_markdown(self._payload(), temp_dir, filename="out.md")
            self.assertTrue(path.is_file())
            self.assertIn("Michaelis constant", path.read_text(encoding="utf-8"))
            self.assertEqual(path.name, "out.md")

    def test_parameters_only_filter(self) -> None:
        text = render_parameters_markdown(self._payload(), include_other_roles=False)
        summary = text.split("## Parameter Summary")[1].split("## Detailed")[0]
        self.assertIn("Km", summary)
        self.assertNotIn("| V002 |", summary)

    def test_safe_filename_sanitizes(self) -> None:
        self.assertEqual(safe_filename("a/b:c*d?.md"), "a_b_c_d_.md")
        self.assertTrue(safe_filename("").endswith(".md"))




class SymbolNormalizationTests(unittest.TestCase):
    def test_volume_concentration_and_rate_use_common_letters(self) -> None:
        volume = normalize_symbol({"raw_name": "volume", "canonical_name": "volume", "symbol": "vol", "role": "parameter", "kind": "continuous"})
        concentration = normalize_symbol({"raw_name": "substrate concentration", "canonical_name": "substrate concentration", "symbol": "sub", "role": "independent", "kind": "continuous"})
        rate = normalize_symbol({"raw_name": "reaction flux", "canonical_name": "reaction rate", "symbol": "flux", "role": "derived", "kind": "rate"})
        self.assertEqual(volume["symbol"], "V")
        self.assertEqual(concentration["symbol"], "c_S")
        self.assertEqual(rate["symbol"], "r")

    def test_author_symbol_is_preserved(self) -> None:
        result = normalize_symbol({"raw_name": "clearance rate", "canonical_name": "clearance rate", "symbol": "cl", "role": "parameter", "kind": "rate"})
        self.assertEqual(result["symbol"], "k_clear")
        self.assertEqual(result["author_symbol"], "cl")
        self.assertIn("cl", result["symbol_notes"])

    def test_derivative_expression_for_state_variables(self) -> None:
        variable = {"raw_name": "GFAP level", "canonical_name": "GFAP level", "role": "dependent", "kind": "continuous"}
        symbol = normalize_symbol(variable)["symbol"]
        self.assertEqual(derivative_expression(variable, symbol), "dc_GFAP/dt")
        self.assertIsNone(derivative_expression({"raw_name": "Km", "canonical_name": "Km", "role": "parameter"}, "Km"))

    def test_payload_symbols_are_unique(self) -> None:
        payload = {"variables": [
            {"raw_name": "concentration", "canonical_name": "concentration", "symbol": "c1", "role": "independent", "kind": "continuous"},
            {"raw_name": "concentration", "canonical_name": "concentration", "symbol": "c2", "role": "independent", "kind": "continuous"},
        ]}
        summary = normalize_payload(payload)
        symbols = [v["symbol"] for v in payload["variables"]]
        self.assertEqual(len(symbols), len(set(symbols)))
        self.assertEqual(summary["normalized_variables"], 2)


class RenderingTests(unittest.TestCase):
    def test_render_contains_core_sections(self) -> None:
        payload = load_json(EXAMPLES / "sample_extraction.json")
        markdown = render_markdown(payload)
        for heading in (
            "# Variable and Parameter Cross-Reference",
            "## Research Question",
            "## Full Cross-Reference Table",
            "## Relationships",
            "## Unresolved or Ambiguous Items",
        ):
            self.assertIn(heading, markdown)
        self.assertIn("mu_max", markdown)
        self.assertIn("|", markdown)
        self.assertIn("DRAFT / NOT FINAL", markdown)

    def test_final_render_has_reviewed_marker(self) -> None:
        payload = load_json(EXAMPLES / "sample_extraction.json")
        markdown = render_markdown(payload, final=True)
        self.assertIn("Final reviewed extraction", markdown)
        self.assertNotIn("DRAFT / NOT FINAL", markdown)


class CliIntegrationTests(unittest.TestCase):
    def test_prepare_validate_render_roundtrip(self) -> None:
        from biomodeling.literature.cli import main

        paper = EXAMPLES / "sample_paper.md"
        if not paper.is_file():
            self.skipTest("sample_paper.md fixture is not present")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            source_json = temp / "source.json"
            chunks_jsonl = temp / "chunks.jsonl"
            markdown = temp / "crosswalk.md"

            self.assertEqual(
                main(
                    [
                        "prepare",
                        str(paper),
                        "--out",
                        str(source_json),
                        "--chunks-out",
                        str(chunks_jsonl),
                        "--quiet",
                    ]
                ),
                0,
            )
            self.assertTrue(source_json.is_file())
            self.assertTrue(chunks_jsonl.is_file())
            self.assertEqual(
                main(["validate", str(EXAMPLES / "sample_extraction.json"), "--source", str(source_json)]),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "validate",
                        str(EXAMPLES / "sample_extraction.json"),
                        "--source",
                        str(source_json),
                        "--final",
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "render",
                        str(EXAMPLES / "sample_extraction.json"),
                        "--source",
                        str(source_json),
                        "--out",
                        str(markdown),
                        "--final",
                    ]
                ),
                0,
            )
            rendered = markdown.read_text(encoding="utf-8")
            self.assertIn("Variable and Parameter Cross-Reference", rendered)
            self.assertIn("Final reviewed extraction", rendered)

    def test_final_render_rejects_allow_invalid_combination(self) -> None:
        from biomodeling.literature.cli import build_parser

        with self.assertRaises(SystemExit):
            build_parser().parse_args(
                [
                    "render",
                    "input.json",
                    "--out",
                    "out.md",
                    "--final",
                    "--allow-invalid",
                ]
            )


def _write_sample_docx(path: Path) -> None:
    import base64

    png_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="
    )

    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Abstract</w:t></w:r></w:p>
    <w:p><w:r><w:t>We model the growth rate as a function of substrate concentration.</w:t></w:r></w:p>
    <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Parameters</w:t></w:r></w:p>
    <w:tbl>
      <w:tr><w:tc><w:p><w:r><w:t>mu_max</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>0.61 per hour</w:t></w:r></w:p></w:tc></w:tr>
    </w:tbl>
  </w:body>
</w:document>
"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/media/image1.png", png_bytes)


if __name__ == "__main__":
    unittest.main()








