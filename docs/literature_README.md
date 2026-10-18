# Bio Variable Extractor

`bio_variable_extractor` is a self-contained workspace kit for an agent working with English biological literature. It turns a paper into an evidence-grounded Markdown cross-reference table of research-question variables and parameters.

Supported inputs:

- local `.txt`, `.md`, `.rst`, `.xml`, `.jats`, `.docx`, and text-layer `.pdf` files;
- PDF input runs the app-bundled Python runtime with `pdfplumber` in an isolated subprocess, so layout-aware page text, page numbers and ruled tables work without installing anything;
- DOI identifiers, resolved through Crossref plus open-access full text from Europe PMC, NCBI PMC BioC, or the PubMed abstract when full text is unavailable.

The kit follows an **agent-driven** design: the agent performs semantic extraction, while the included Python package handles source preparation, JSON validation, final-review gating, and deterministic Markdown rendering. No API key is required. A scaffold is explicitly a draft; only an extraction that passes `validate --final` can be represented as a completed deliverable.

## What it extracts

- the paper's research question or the most defensible reconstruction;
- organism/system, design, model type, sample, and time scale;
- independent, dependent, controlled, covariate, parameter, derived, categorical, and latent variables;
- author terms, canonical English names, symbols, aliases, definitions, units, ranges, and relationships;
- source block and page evidence for every variable;
- confidence, ambiguities, symbol collisions, and unresolved items.

## Directory layout

```text
bio_variable_extractor/
├─ AGENTS.md
├─ README.md
├─ prompts/
│  └─ extraction_prompt.md
├─ src/
│  └─ bio_variable_extractor/
│     ├─ __init__.py
│     ├─ __main__.py
│     ├─ cli.py
│     ├─ extraction.py
│     ├─ io_utils.py
│     ├─ validation.py
│     └─ rendering.py
├─ templates/
│  ├─ extraction.schema.json
│  └─ variable_crosswalk.template.md
├─ examples/
│  ├─ sample_paper.md
│  ├─ sample_source.json
│  ├─ sample_chunks_prepared.jsonl
│  ├─ sample_extraction.json
│  └─ sample_variable_crosswalk.md
└─ tests/
   └─ test_pipeline.py
```

## Requirements

The core pipeline uses only the Python standard library and has been structured for Python 3.10+.

PDF input works with no installation when the Codex app runtime is present. If that runtime is missing, install a reader in the active interpreter:

```bash
py -m pip install pdfplumber pypdf
```

DOCX input requires no extra package: paragraphs, headings, footnote/endnote text and table rows are read directly from the OOXML archive. Tables and formulas that are embedded as images still require manual review.

PDF input reads page-by-page, preserves page numbers on every evidence block, recognises additional modelling headings (`Model`, `Parameters`, `Initial conditions`, and similar), and keeps ruled tables as `table | row | cells`. Scanned PDFs without a text layer are rejected with an OCR message instead of producing empty text. Unruled tables may still appear as collapsed text and need manual verification.

JATS XML and DOI resolution use only the Python standard library and require no extra package. DOI resolution works offline for the pipeline itself, but needs network access for Crossref, Europe PMC, PMC BioC, or PubMed.

## Quick start

From this directory:

```bash
py -m src.bio_variable_extractor prepare examples/sample_paper.md --out work/source.json --chunks-out work/chunks.jsonl
py -m src.bio_variable_extractor prepare-doi 10.1371/journal.pcbi.1007486 --out work/doi_source.json --chunks-out work/doi_chunks.jsonl
py -m src.bio_variable_extractor prepare C:\papers\model.docx --out work/docx_source.json
py -m src.bio_variable_extractor prepare C:\papers\model.pdf --out work/pdf_source.json --chunks-out work/pdf_chunks.jsonl
py -m src.bio_variable_extractor convert C:\papers\model.pdf --out-dir work\export --image-mode page,embedded --ocr auto
py -m src.bio_variable_extractor convert 10.1371/journal.pcbi.1007486 --out-dir work\doi_export --ocr auto
py -m src.bio_variable_extractor validate examples/sample_extraction.json --source examples/sample_source.json
py -m src.bio_variable_extractor validate examples/sample_extraction.json --source examples/sample_source.json --final
py -m src.bio_variable_extractor render examples/sample_extraction.json --source examples/sample_source.json --out work/variable_crosswalk.md --final
```

`examples/sample_source.json` is generated from `examples/sample_paper.md` and lets you run validation and rendering immediately without a preparation step. The `work/` directory is created automatically.

`prepare` also accepts a DOI directly, so `prepare-doi` is a convenience alias that never mistakes a DOI for a file path.

For a directory of PMC JATS XML files:

```bash
py -m src.bio_variable_extractor prepare-dir .\work\pmc_fulltext --out-dir .\work\batch --pattern "*.xml"
```

This writes one `*.source.json` and one `*.chunks.jsonl` per source plus a `prepare_manifest.json`.

To create a review-required extraction scaffold from a prepared source:

```bash
py -m src.bio_variable_extractor scaffold .\work\batch\prepared\PMC0000000.source.json --out .\work\batch\PMC0000000.extraction.json
```

`scaffold` output is a candidate list for semantic review, not a finished expert extraction. It sets `extraction_metadata.review_status` to `scaffold`; `validate --final` rejects it.

To make a scaffold easier to review without pretending it is finished, normalize it into an explicit non-final review queue:

```bash
py -m src.bio_variable_extractor normalize-review .\work\batch\PMC0000000.extraction.json --out .\work\batch\PMC0000000.review.json
```

This replaces generated abbreviations with readable names and sets `review_status` to `needs_review`. It does not remove any candidate and it still cannot pass `validate --final` until every candidate is semantically confirmed.

The `prepare` command creates a stable source inventory. For DOI input it records the access route (`open_full_text` or `abstract_only`), DOI, PMCID, and any retrieval warning in `metadata`. The agent uses the JSONL chunks to identify variables. Equations written as plain-text equalities are also detected and turned into `equation` relationships. The `validate` command checks contract shape, evidence references, symbol collisions, and relationship targets. `validate --final` additionally requires `review_status: reviewed`, reviewer metadata, no scaffold-only warnings, no scaffold notes, and no unconfirmed low-confidence rows. `render --final` writes a Markdown table marked as a final reviewed extraction; ordinary rendering is explicitly marked `DRAFT / NOT FINAL`.

When the package is installed or placed on `PYTHONPATH`, the shorter module form also works:

```bash
py -m bio_variable_extractor prepare paper.txt --out work/source.json
```

## Workflow for an agent

1. Read `AGENTS.md` when the workspace is opened.
2. Run `prepare` on the paper.
3. Extract the research question and candidate variables using `prompts/extraction_prompt.md`.
4. Write JSON matching `templates/extraction.schema.json`.
5. Run draft `validate`; fix errors and review warnings.
6. Semantically verify every candidate against its evidence. Remove ordinary words that are not variables or parameters, correct names/symbols, and resolve or retain ambiguities deliberately.
7. Set `review_status` to `reviewed`, provide `reviewer` and `reviewed_at`, and remove scaffold-only notes and warnings.
8. Run `validate --final`; fix every remaining error.
9. Run `render --final`; verify the evidence columns and unresolved section.
10. Return the Markdown path and a concise coverage report. If final validation fails, return or label the result only as a draft.

## Markdown export

`convert` turns a local file or DOI into a self-contained folder:

```text
export/
  document.md
  image_manifest.json
  assets/
    page-001.png
    docx-image-001.png
```

- DOCX images come from `word/media`.
- Text-layer PDFs are rendered page by page to PNG, and embedded raster images are extracted when present.
- JATS and BioC sources record figure references and captions; image files are not downloaded automatically because publisher paths vary and may require access rights.
- Every asset is listed in `image_manifest.json` with its source, page, kind, caption, and OCR status.

OCR is optional and never installed automatically:

```bash
py -m src.bio_variable_extractor convert paper.pdf --out-dir export --ocr auto
py -m src.bio_variable_extractor convert paper.pdf --out-dir export --ocr always --ocr-lang eng
py -m src.bio_variable_extractor convert paper.pdf --out-dir export --ocr never
```

Supported local backends are `tesseract`, `pytesseract`, `easyocr`, `paddleocr`, and `rapidocr`. With `--ocr auto` the converter uses the first available backend and records a warning when none exists; with `--ocr always` it fails with an actionable message instead of silently skipping OCR.

## Output contract

The main JSON object has these top-level sections:

| Section | Purpose |
| --- | --- |
| `document` | Source identity and metadata |
| `research_question` | Question, scope, and evidence |
| `study_profile` | Organism, design, model, sample, time scale |
| `variables` | Normalized variable/parameter records |
| `relationships` | Evidence-backed equations or directional links |
| `unresolved` | Ambiguities, contradictions, and missing information |
| `extraction_metadata` | Coverage, method, warnings, timestamps, and review status (`scaffold`, `needs_review`, or `reviewed`) |

The rendered Markdown contains a summary, a role/type table, a full cross-reference table, relationships, symbol notes, unresolved items, and an explicit draft/final review marker.

## Markdown and asset limitations

- Scanned PDFs are out of scope; run OCR or a dedicated layout tool first.
- Unruled PDF tables may collapse into plain text rows.
- JATS and BioC figure files are recorded as references, not bundled, unless you download them yourself.
- OCR applies to raster images only. Vector figures and image-only equations keep their page PNG.

## Accuracy boundaries

This kit cannot prove that a variable list is exhaustive. Accuracy depends on the completeness of the supplied text and the agent's evidence discipline. Scanned PDFs without an OCR layer are detected and rejected; run OCR before `prepare` to use them. PDF figures, image-only formulas, unruled tables and multi-column layouts may still need a dedicated layout or OCR preprocessor.

DOI resolution depends on external services. When full text is behind a paywall, only the Crossref/PubMed abstract is prepared and `metadata.access` is `abstract_only`; the missing full text is reported rather than silently inferred. Relationship records are extracted only from literal textual equalities or assignment vocabulary, and every symbol still requires semantic confirmation. `validate --final` enforces that the semantic review step has actually been completed before a result is presented as final.

## Testing

```bash
py -m unittest discover -s tests -v
```

The tests use only the standard library plus the bundled PDF runtime when present; DOCX and DOI tests require no extra packages.
