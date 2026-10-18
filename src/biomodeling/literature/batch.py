"""Batch preparation and extraction summary helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .extraction import read_and_chunk
from .io_utils import write_json, write_jsonl


def prepare_directory(
    input_dir: Path,
    output_dir: Path,
    *,
    pattern: str = "*.xml",
    target_words: int = 170,
    max_words: int = 260,
) -> dict[str, Any]:
    """Prepare every matching source in a directory and return a run manifest."""
    files = sorted(path for path in input_dir.glob(pattern) if path.is_file())
    prepared_dir = output_dir / "prepared"
    prepared_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, Any]] = []
    for path in files:
        stem = path.stem
        source_path = prepared_dir / f"{stem}.source.json"
        chunks_path = prepared_dir / f"{stem}.chunks.jsonl"
        try:
            source, chunks = read_and_chunk(
                path,
                target_words=target_words,
                max_words=max_words,
            )
            write_json(source_path, source)
            write_jsonl(chunks_path, chunks)
            metadata = source.get("metadata", {})
            entries.append(
                {
                    "source": str(path.resolve()),
                    "stem": stem,
                    "status": "prepared",
                    "word_count": source["word_count"],
                    "section_count": source["section_count"],
                    "chunk_count": source["chunk_count"],
                    "title": metadata.get("title", "") if isinstance(metadata, dict) else "",
                    "source_json": str(source_path.resolve()),
                    "chunks_jsonl": str(chunks_path.resolve()),
                }
            )
        except Exception as exc:
            entries.append(
                {
                    "source": str(path.resolve()),
                    "stem": stem,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    manifest = {
        "input_dir": str(input_dir.resolve()),
        "pattern": pattern,
        "file_count": len(files),
        "prepared_count": sum(1 for entry in entries if entry["status"] == "prepared"),
        "failed_count": sum(1 for entry in entries if entry["status"] == "failed"),
        "entries": entries,
    }
    write_json(output_dir / "prepare_manifest.json", manifest)
    return manifest


def extraction_stats(path: Path) -> dict[str, Any]:
    """Compute quality statistics for one extraction JSON file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    variables = payload.get("variables", [])
    roles: dict[str, int] = {}
    confidences: dict[str, int] = {}
    for variable in variables:
        if not isinstance(variable, dict):
            continue
        role = str(variable.get("role", "unknown"))
        confidence = str(variable.get("confidence", "unknown"))
        roles[role] = roles.get(role, 0) + 1
        confidences[confidence] = confidences.get(confidence, 0) + 1
    metadata = payload.get("extraction_metadata", {})
    return {
        "variable_count": len(variables),
        "relationship_count": len(payload.get("relationships", [])),
        "unresolved_count": len(payload.get("unresolved", [])),
        "roles": roles,
        "confidences": confidences,
        "review_status": metadata.get("review_status", "needs_review")
        if isinstance(metadata, dict)
        else "needs_review",
        "extractor": metadata.get("extractor", "unknown")
        if isinstance(metadata, dict)
        else "unknown",
    }


def normalize_scaffold_for_review(
    payload: dict[str, Any],
    *,
    reviewer: str = "pending expert semantic review",
) -> dict[str, Any]:
    """Turn a scaffold into an explicitly unreviewed, human-readable review queue.

    This function never promotes a scaffold to ``reviewed``. It only removes
    obvious symbol ambiguity so a reviewer can work from names rather than
    generated abbreviations, and records that semantic confirmation is still
    pending.
    """
    normalized = json.loads(json.dumps(payload))
    variables = normalized.get("variables", [])
    if not isinstance(variables, list):
        return normalized
    for index, variable in enumerate(variables, start=1):
        if not isinstance(variable, dict):
            continue
        canonical = str(variable.get("canonical_name") or variable.get("raw_name") or f"Variable {index}")
        variable["symbol"] = _symbol_from_canonical(canonical, index)
        variable["confidence"] = variable.get("confidence") or "low"
        notes = str(variable.get("notes", "")).strip()
        pending = "Pending semantic review: confirm whether this term is a quantity, parameter, state, or category in the paper."
        if "Pending semantic review" not in notes:
            variable["notes"] = f"{notes} {pending}".strip()
    metadata = normalized.get("extraction_metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        normalized["extraction_metadata"] = metadata
    metadata["review_status"] = "needs_review"
    metadata["reviewer"] = reviewer
    metadata["reviewed_at"] = ""
    warnings = metadata.get("warnings")
    if not isinstance(warnings, list):
        warnings = []
    warnings = [str(item) for item in warnings]
    marker = "Normalized review queue only; semantic confirmation has not been completed."
    if marker not in warnings:
        warnings.append(marker)
    metadata["warnings"] = warnings
    return normalized


def _symbol_from_canonical(canonical: str, index: int) -> str:
    words = [word for word in re.findall(r"[A-Za-z0-9]+", canonical) if word]
    if not words:
        return f"x{index}"
    if len(words) == 1:
        return words[0][:8]
    if len(words) == 2:
        return f"{words[0][:4]}_{words[1][:6]}".replace(" ", "_")
    return f"{words[0][:4]}_{words[1][:4]}_{index}"
