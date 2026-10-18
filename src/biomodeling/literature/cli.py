"""Command-line interface for prepare, validate, and render."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .doi import looks_like_doi, resolve_doi
from .export import convert_source
from .extraction import read_and_chunk
from .io_utils import load_json, write_json, write_jsonl, write_text
from .batch import normalize_scaffold_for_review, prepare_directory
from .scaffold import scaffold_from_source
from .rendering import render_markdown
from .audit import audit_extraction, format_audit
from .semantic_review import semantic_review
from .lexicon import entries, lexicon_summary, load_lexicon, match_models, match_parameters, match_relations
from .parameter_export import DEFAULT_OUTPUT_DIR, export_parameters_markdown
from .validation import format_report, validate_extraction


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bio-variable-extractor",
        description="Prepare, validate, and render biological variable extractions.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser(
        "prepare",
        help="Read a paper and write a source inventory plus citable chunks.",
    )
    prepare.add_argument(
        "source",
        help="DOI identifier or input file (.txt, .md, .rst, .xml, .jats, .pdf, or .docx).",
    )
    prepare.add_argument("--out", type=Path, required=True, help="Output source inventory JSON.")
    prepare.add_argument("--chunks-out", type=Path, help="Optional JSONL output for chunks.")
    prepare.add_argument("--target-words", type=int, default=170, help="Target words per chunk.")
    prepare.add_argument("--max-words", type=int, default=260, help="Maximum words per chunk.")
    prepare.add_argument("--quiet", action="store_true", help="Suppress the summary line.")

    prepare_doi = subparsers.add_parser(
        "prepare-doi",
        help="Resolve a DOI to metadata plus open-access full text (or abstract) and prepare it.",
    )
    prepare_doi.add_argument("doi", help="DOI identifier, DOI URL, or doi: prefixed value.")
    prepare_doi.add_argument("--out", type=Path, required=True, help="Output source inventory JSON.")
    prepare_doi.add_argument("--chunks-out", type=Path, help="Optional JSONL output for chunks.")
    prepare_doi.add_argument("--target-words", type=int, default=170, help="Target words per chunk.")
    prepare_doi.add_argument("--max-words", type=int, default=260, help="Maximum words per chunk.")
    prepare_doi.add_argument("--timeout", type=int, default=45, help="Per-request timeout in seconds.")
    prepare_doi.add_argument("--quiet", action="store_true", help="Suppress the summary line.")

    convert = subparsers.add_parser(
        "convert",
        help="Convert a local paper or DOI into Markdown with locally saved assets.",
    )
    convert.add_argument(
        "source",
        help="DOI identifier or input file (.txt, .md, .rst, .xml, .jats, .pdf, or .docx).",
    )
    convert.add_argument("--out-dir", type=Path, required=True, help="Output directory.")
    convert.add_argument(
        "--extract-images",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Extract or render images into the output assets directory.",
    )
    convert.add_argument(
        "--image-mode",
        default="page,embedded",
        help="Comma-separated image modes for PDF input: page, embedded.",
    )
    convert.add_argument(
        "--ocr",
        choices=["auto", "always", "never"],
        default="auto",
        help="OCR policy for saved images. auto uses a local backend when present.",
    )
    convert.add_argument("--ocr-lang", default="eng", help="OCR language code, for example eng or chi_sim.")
    convert.add_argument(
        "--ocr-backend",
        default="auto",
        help="Preferred OCR backend: auto, tesseract, pytesseract, easyocr, paddleocr, or rapidocr.",
    )
    convert.add_argument("--timeout", type=int, default=45, help="Per-request DOI timeout in seconds.")
    convert.add_argument("--quiet", action="store_true", help="Suppress the summary line.")

    prepare_dir = subparsers.add_parser(
        "prepare-dir",
        help="Prepare every matching source in a directory.",
    )
    prepare_dir.add_argument("input_dir", type=Path, help="Directory containing source files.")
    prepare_dir.add_argument("--out-dir", type=Path, required=True, help="Output directory.")
    prepare_dir.add_argument("--pattern", default="*.xml", help="Glob pattern for source files.")
    prepare_dir.add_argument("--target-words", type=int, default=170, help="Target words per chunk.")
    prepare_dir.add_argument("--max-words", type=int, default=260, help="Maximum words per chunk.")

    validate = subparsers.add_parser(
        "validate",
        help="Validate an extraction JSON against the contract and optional source inventory.",
    )
    validate.add_argument("extraction", type=Path, help="Extraction JSON to validate.")
    validate.add_argument("--source", type=Path, help="Prepared source inventory JSON.")
    validate.add_argument("--json", action="store_true", help="Emit machine-readable results.")
    validate.add_argument(
        "--final",
        action="store_true",
        help="Require a completed semantic review and reject scaffold or low-confidence drafts.",
    )

    render = subparsers.add_parser(
        "render",
        help="Render an extraction JSON as a Markdown cross-reference table.",
    )
    render.add_argument("extraction", type=Path, help="Validated extraction JSON.")
    render.add_argument("--out", type=Path, required=True, help="Markdown output path.")
    render_mode = render.add_mutually_exclusive_group()
    render_mode.add_argument("--allow-invalid", action="store_true", help="Render despite validation errors.")
    render_mode.add_argument(
        "--final",
        action="store_true",
        help="Run the final quality gate and mark the Markdown as a final reviewed extraction.",
    )
    render.add_argument("--source", type=Path, help="Prepared source inventory JSON.")

    scaffold = subparsers.add_parser(
        "scaffold",
        help="Create a deterministic extraction JSON scaffold from a prepared source.",
    )
    scaffold.add_argument("source", type=Path, help="Prepared source inventory JSON.")
    scaffold.add_argument("--out", type=Path, required=True, help="Output extraction JSON.")
    scaffold.add_argument("--extractor", default="bio_variable_extractor scaffold", help="Extractor label.")
    scaffold.add_argument("--max-variables", type=int, default=0, help="Maximum candidate variables; 0 means no truncation (default, lossless).")

    normalize = subparsers.add_parser(
        "normalize-review",
        help="Prepare a readable review queue from a scaffold without marking it reviewed.",
    )
    normalize.add_argument("extraction", type=Path, help="Scaffold extraction JSON.")
    normalize.add_argument("--out", type=Path, required=True, help="Output review-queue JSON.")
    normalize.add_argument(
        "--reviewer",
        default="pending expert semantic review",
        help="Reviewer label recorded in the draft metadata.",
    )

    self_review = subparsers.add_parser(
        "self-review",
        help="Run an evidence-bound self-audit on an extraction JSON.",
    )
    self_review.add_argument("extraction", type=Path, help="Extraction JSON to audit.")
    self_review.add_argument("--source", type=Path, help="Prepared source inventory JSON.")
    self_review.add_argument("--json", action="store_true", help="Emit machine-readable audit results.")
    self_review.add_argument("--out", type=Path, help="Optional JSON path for the audit report.")

    semantic = subparsers.add_parser(
        "semantic-review",
        help="Apply evidence-bound semantic normalisation and return a reviewed copy.",
    )
    semantic.add_argument("extraction", type=Path, help="Scaffold or draft extraction JSON.")
    semantic.add_argument("--out", type=Path, required=True, help="Output reviewed extraction JSON.")
    semantic.add_argument("--source", type=Path, help="Prepared source inventory JSON.")
    semantic.add_argument(
        "--reviewer",
        default="deterministic semantic reviewer",
        help="Reviewer label recorded in extraction metadata.",
    )
    semantic.add_argument(
        "--keep-needs-review",
        action="store_true",
        help="Keep review_status as needs_review even when the deterministic pass is clean.",
    )
    semantic.add_argument("--json", action="store_true", help="Emit machine-readable review summary.")
    semantic.add_argument("--audit-out", type=Path, help="Optional JSON path for the post-review audit.")

    lex = subparsers.add_parser(
        "lexicon",
        help="Inspect the biological modelling lexicons.",
    )
    lex.add_argument("name", nargs="?", choices=["parameters", "relations", "expressions", "models"], help="Lexicon to inspect.")
    lex.add_argument("--id", dest="entry_id", help="Return one entry by ID.")
    lex.add_argument("--search", help="Search entries and aliases for text.")
    lex.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")

    export_params = subparsers.add_parser(
        "export-parameters",
        help="Export extracted parameters and variables to a Markdown file.",
    )
    export_params.add_argument("extractions", nargs="+", type=Path, help="One or more extraction or reviewed JSON files.")
    export_params.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory. Default: {DEFAULT_OUTPUT_DIR}",
    )
    export_params.add_argument("--filename", help="Explicit output filename when exporting a single JSON.")
    export_params.add_argument(
        "--parameters-only",
        action="store_true",
        help="Export only parameter/controlled/covariate records instead of all variables.",
    )
    export_params.add_argument("--no-relationships", action="store_true", help="Omit the relationships section.")
    export_params.add_argument("--no-unresolved", action="store_true", help="Omit the unresolved-items section.")
    export_params.add_argument("--json", action="store_true", help="Emit machine-readable export summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            return _command_prepare(args)
        if args.command == "prepare-doi":
            return _command_prepare_doi(args)
        if args.command == "convert":
            return _command_convert(args)
        if args.command == "prepare-dir":
            return _command_prepare_dir(args)
        if args.command == "validate":
            return _command_validate(args)
        if args.command == "render":
            return _command_render(args)
        if args.command == "scaffold":
            return _command_scaffold(args)
        if args.command == "normalize-review":
            return _command_normalize_review(args)
        if args.command == "self-review":
            return _command_self_review(args)
        if args.command == "semantic-review":
            return _command_semantic_review(args)
        if args.command == "lexicon":
            return _command_lexicon(args)
        if args.command == "export-parameters":
            return _command_export_parameters(args)
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    parser.error(f"Unknown command: {args.command}")
    return 2


def _command_prepare(args: argparse.Namespace) -> int:
    source_input = str(args.source)
    if looks_like_doi(source_input) and not Path(source_input).is_file():
        return _prepare_doi_source(
            source_input,
            out=args.out,
            chunks_out=args.chunks_out,
            target_words=args.target_words,
            max_words=args.max_words,
            timeout=45,
            quiet=args.quiet,
        )

    source_path = Path(source_input)
    if not source_path.is_file():
        raise ValueError(
            f"Source file not found: {source_path}. "
            "Pass an existing file or a DOI such as 10.1038/s41586-020-2649-2."
        )
    source, chunks = read_and_chunk(
        source_path,
        target_words=args.target_words,
        max_words=args.max_words,
    )
    write_json(args.out, source)
    if args.chunks_out:
        write_jsonl(args.chunks_out, chunks)
    if not args.quiet:
        print(
            f"Prepared {source['chunk_count']} chunk(s) from "
            f"{source['word_count']} words in {source['section_count']} section(s)."
        )
        print(f"Inventory: {args.out}")
        if args.chunks_out:
            print(f"Chunks: {args.chunks_out}")
    return 0


def _command_prepare_doi(args: argparse.Namespace) -> int:
    return _prepare_doi_source(
        args.doi,
        out=args.out,
        chunks_out=args.chunks_out,
        target_words=args.target_words,
        max_words=args.max_words,
        timeout=args.timeout,
        quiet=args.quiet,
    )


def _prepare_doi_source(
    doi: str,
    *,
    out: Path,
    chunks_out: Path | None,
    target_words: int,
    max_words: int,
    timeout: int,
    quiet: bool,
) -> int:
    source, chunks, document = resolve_doi(
        doi,
        target_words=target_words,
        max_words=max_words,
        timeout=timeout,
    )
    write_json(out, source)
    if chunks_out:
        write_jsonl(chunks_out, chunks)
    if not quiet:
        access = source.get("metadata", {}).get("access", "unknown")
        print(
            f"Prepared {source['chunk_count']} chunk(s) from "
            f"{source['word_count']} words ({access})."
        )
        if source.get("metadata", {}).get("warning"):
            print(f"Warning: {source['metadata']['warning']}")
        print(f"Inventory: {out}")
        if chunks_out:
            print(f"Chunks: {chunks_out}")
    if not document.text.strip():
        raise ValueError(f"DOI {doi} produced no extractable text.")
    return 0


def _command_prepare_dir(args: argparse.Namespace) -> int:
    if not args.input_dir.is_dir():
        raise ValueError(f"Input directory not found: {args.input_dir}")
    manifest = prepare_directory(
        args.input_dir,
        args.out_dir,
        pattern=args.pattern,
        target_words=args.target_words,
        max_words=args.max_words,
    )
    print(
        f"Prepared {manifest['prepared_count']} of {manifest['file_count']} source(s); "
        f"{manifest['failed_count']} failed."
    )
    print(f"Manifest: {args.out_dir / 'prepare_manifest.json'}")
    return 0 if manifest["failed_count"] == 0 else 1


def _command_validate(args: argparse.Namespace) -> int:
    payload = load_json(args.extraction)
    known_block_ids, known_sections, block_text = _load_source_context(args.source)

    report = validate_extraction(
        payload,
        known_block_ids=known_block_ids,
        known_sections=known_sections,
        block_text=block_text,
        final=args.final,
    )
    if args.json:
        print(
            json.dumps(
                {
                    "ok": report.ok,
                    "mode": "final" if args.final else "draft",
                    "errors": report.errors,
                    "warnings": report.warnings,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(format_report(report, final=args.final))
    return 0 if report.ok else 1


def _command_render(args: argparse.Namespace) -> int:
    payload = load_json(args.extraction)
    known_block_ids, known_sections, block_text = _load_source_context(args.source)
    report = validate_extraction(
        payload,
        known_block_ids=known_block_ids,
        known_sections=known_sections,
        block_text=block_text,
        final=args.final,
    )
    if not report.ok and not args.allow_invalid:
        print(format_report(report, final=args.final), file=sys.stderr)
        if args.final:
            print("Final rendering cannot bypass validation errors.", file=sys.stderr)
        else:
            print("Refusing to render invalid extraction. Use --allow-invalid to override.", file=sys.stderr)
        return 1
    markdown = render_markdown(payload, final=args.final)
    write_text(args.out, markdown)
    print(f"Rendered Markdown: {args.out}")
    return 0


def _load_source_context(
    source_path: Path | None,
) -> tuple[set[str] | None, set[str] | None, dict[str, str] | None]:
    if source_path is None:
        return None, None, None
    source = load_json(source_path)
    chunks = source.get("chunks", [])
    if not isinstance(chunks, list):
        raise ValueError(f"Invalid prepared source: 'chunks' must be an array in {source_path}.")
    known_block_ids = {
        str(chunk.get("block_id"))
        for chunk in chunks
        if isinstance(chunk, dict) and chunk.get("block_id")
    }
    known_sections = {
        str(section.get("section"))
        for section in source.get("sections", [])
        if isinstance(section, dict) and section.get("section")
    }
    block_text = {
        str(chunk.get("block_id")): str(chunk.get("text", ""))
        for chunk in chunks
        if isinstance(chunk, dict) and chunk.get("block_id")
    }
    return known_block_ids, known_sections, block_text


def _command_convert(args: argparse.Namespace) -> int:
    ocr_mode = args.ocr
    if ocr_mode == "always":
        from .ocr import detect_backend

        if detect_backend(args.ocr_backend) is None:
            raise ValueError(
                "OCR was requested with --ocr always but no local OCR backend is available. "
                "Install tesseract, pytesseract, easyocr, paddleocr, or rapidocr."
            )
    result = convert_source(
        args.source,
        args.out_dir,
        extract_images=args.extract_images,
        ocr_mode=ocr_mode,
        ocr_lang=args.ocr_lang,
        ocr_backend=args.ocr_backend,
        image_mode=args.image_mode,
        timeout=args.timeout,
    )
    if not args.quiet:
        print("Markdown: " + str(args.out_dir / "document.md"))
        print("Assets: " + str(len(result.assets)))
        print("Manifest: " + str(args.out_dir / "image_manifest.json"))
        for warning in result.warnings:
            print("Warning: " + warning)
    return 0


def _command_normalize_review(args: argparse.Namespace) -> int:
    if not args.extraction.is_file():
        raise ValueError(f"Extraction file not found: {args.extraction}")
    payload = load_json(args.extraction)
    normalized = normalize_scaffold_for_review(payload, reviewer=args.reviewer)
    write_json(args.out, normalized)
    print(f"Review queue: {args.out}")
    print(f"Variables requiring semantic confirmation: {len(normalized.get('variables', []))}")
    print("Status: needs_review (not a final extraction)")
    return 0


def _command_scaffold(args: argparse.Namespace) -> int:
    if not args.source.is_file():
        raise ValueError(f"Prepared source file not found: {args.source}")
    payload = scaffold_from_source(
        args.source,
        extractor=args.extractor,
        max_variables=args.max_variables,
    )
    write_json(args.out, payload)
    print(f"Scaffold: {args.out}")
    print(f"Candidate variables: {len(payload['variables'])}")
    return 0



def _command_self_review(args: argparse.Namespace) -> int:
    if not args.extraction.is_file():
        raise ValueError(f"Extraction file not found: {args.extraction}")
    payload = load_json(args.extraction)
    report = audit_extraction(
        payload,
        source_path=str(args.source) if args.source else None,
    )
    rendered = report.as_dict()
    if args.out:
        write_json(args.out, rendered)
    if args.json:
        print(json.dumps(rendered, ensure_ascii=False, indent=2))
    else:
        print(format_audit(report))
        if args.out:
            print(f"Audit report: {args.out}")
    return 0 if report.ok else 1


def _command_semantic_review(args: argparse.Namespace) -> int:
    if not args.extraction.is_file():
        raise ValueError(f"Extraction file not found: {args.extraction}")
    payload = load_json(args.extraction)
    reviewed, report = semantic_review(
        payload,
        source_path=str(args.source) if args.source else None,
        reviewer=args.reviewer,
        mark_reviewed=not args.keep_needs_review,
    )
    write_json(args.out, reviewed)
    if args.audit_out:
        write_json(args.audit_out, report.as_dict())
    summary = {
        "output": str(args.out),
        "review_status": reviewed.get("extraction_metadata", {}).get("review_status"),
        "variable_count": len(reviewed.get("variables", [])),
        "audit_ok": report.ok,
        "audit_errors": report.error_count,
        "audit_warnings": report.warning_count,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"Semantic review: {args.out}")
        print(f"Variables: {summary['variable_count']}")
        print(f"Status: {summary['review_status']}")
        print(f"Audit: {'passed' if report.ok else 'failed'} ({report.error_count} error(s), {report.warning_count} warning(s))")
        if args.audit_out:
            print(f"Audit report: {args.audit_out}")
    return 0 if report.ok else 1


def _command_lexicon(args: argparse.Namespace) -> int:
    if not args.name:
        summary = lexicon_summary()
        if args.json:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            for name, stats in summary.items():
                print(f"{name}: {stats['entry_count']} entries, {stats['source_count']} sources")
        return 0

    payload = load_lexicon(args.name)
    if args.entry_id:
        wanted = str(args.entry_id).strip().lower()
        found = [entry for entry in payload.get('entries', []) if str(entry.get('id', '')).lower() == wanted]
        if not found:
            raise ValueError(f"Entry '{args.entry_id}' not found in {args.name} lexicon.")
        result: object = found[0]
    elif args.search:
        needle = str(args.search).lower()
        result = []
        for entry in payload.get('entries', []):
            blob = json.dumps(entry, ensure_ascii=False).lower()
            if needle in blob:
                result.append(entry)
    else:
        result = payload

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        items = result if isinstance(result, list) else [result]
        if not items:
            print('No matching entries.')
            return 0
        for entry in items:
            if not isinstance(entry, dict):
                continue
            print(f"{entry.get('id','')}: {entry.get('canonical_name','')}")
            if entry.get('definition'):
                print(f"  {entry['definition']}")
            if entry.get('expression'):
                print(f"  expression: {entry['expression']}")
            if entry.get('description'):
                print(f"  {entry['description']}")
        print(f"Matched entries: {len(items)}")
    return 0




def _command_export_parameters(args: argparse.Namespace) -> int:
    if args.filename and len(args.extractions) > 1:
        raise ValueError("--filename can only be used when exporting a single extraction file.")
    written: list[str] = []
    for extraction in args.extractions:
        if not extraction.is_file():
            raise ValueError(f"Extraction file not found: {extraction}")
        payload = load_json(extraction)
        target = export_parameters_markdown(
            payload,
            args.out_dir,
            filename=args.filename,
            include_other_roles=not args.parameters_only,
            include_relationships=not args.no_relationships,
            include_unresolved=not args.no_unresolved,
        )
        written.append(str(target))
    summary = {
        "out_dir": str(args.out_dir),
        "exported_count": len(written),
        "files": written,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for path in written:
            print(f"Exported: {path}")
        print(f"Total exported: {len(written)}")
    return 0
