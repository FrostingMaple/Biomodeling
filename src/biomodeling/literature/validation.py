"""Validation for the extraction JSON contract."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from dataclasses import dataclass, field
from typing import Any, Iterable

from .extraction import EXTRACTION_SCHEMA_VERSION

ROLE_VALUES = {
    "independent",
    "dependent",
    "controlled",
    "covariate",
    "parameter",
    "derived",
    "categorical",
    "latent",
    "other",
}
KIND_VALUES = {
    "continuous",
    "discrete",
    "binary",
    "categorical",
    "ordinal",
    "count",
    "rate",
    "constant",
    "unknown",
}
CONFIDENCE_VALUES = {"high", "medium", "low"}
RELATIONSHIP_TYPES = {
    "equation",
    "directional",
    "definition",
    "grouping",
    "association",
    "other",
}

_SYMBOL_ALLOWED = re.compile(r"^[A-Za-z][A-Za-z0-9_^{}\[\]()+\-/]*$")
_NOT_REPORTED = {"not reported", "unknown", "n/a", "na", "none", ""}
REVIEW_STATUS_VALUES = {"scaffold", "needs_review", "reviewed"}
FINAL_REVIEW_STATUS = "reviewed"


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def validate_extraction(
    payload: dict[str, Any],
    *,
    known_block_ids: set[str] | None = None,
    known_sections: set[str] | None = None,
    block_text: dict[str, str] | None = None,
    final: bool = False,
) -> ValidationReport:
    report = ValidationReport()
    _require_mapping(payload, "root", report)
    _require_keys(
        payload,
        [
            "schema_version",
            "document",
            "research_question",
            "study_profile",
            "variables",
            "relationships",
            "unresolved",
            "extraction_metadata",
        ],
        "root",
        report,
    )
    if report.errors:
        return report

    if payload.get("schema_version") != EXTRACTION_SCHEMA_VERSION:
        report.error(
            f"root.schema_version must be '{EXTRACTION_SCHEMA_VERSION}', "
            f"found {payload.get('schema_version')!r}."
        )

    _validate_document(payload["document"], report)
    _validate_research_question(payload["research_question"], report)
    _validate_study_profile(payload["study_profile"], report)
    variable_ids = _validate_variables(payload["variables"], report)
    _validate_relationships(payload["relationships"], variable_ids, report)
    _validate_unresolved(payload["unresolved"], variable_ids, report)
    _validate_metadata(payload["extraction_metadata"], report)
    _validate_evidence_references(payload, known_block_ids, known_sections, block_text, report)
    _validate_symbol_uniqueness(payload["variables"], report)
    if final:
        _validate_final_quality(payload, report)
    return report


def _require_mapping(value: Any, path: str, report: ValidationReport) -> None:
    if not isinstance(value, dict):
        report.error(f"{path} must be an object.")


def _require_list(value: Any, path: str, report: ValidationReport) -> None:
    if not isinstance(value, list):
        report.error(f"{path} must be an array.")


def _require_nonempty_string(value: Any, path: str, report: ValidationReport) -> None:
    if not isinstance(value, str) or not value.strip():
        report.error(f"{path} must be a non-empty string.")


def _require_keys(
    value: Any,
    keys: Iterable[str],
    path: str,
    report: ValidationReport,
) -> None:
    if not isinstance(value, dict):
        return
    for key in keys:
        if key not in value:
            report.error(f"{path}.{key} is required.")


def _validate_document(value: Any, report: ValidationReport) -> None:
    _require_mapping(value, "document", report)
    if not isinstance(value, dict):
        return
    _require_keys(value, ["title", "source_path", "source_name", "language"], "document", report)
    for key in ("title", "source_path", "source_name", "language"):
        _require_nonempty_string(value.get(key), f"document.{key}", report)
    if value.get("language") and value["language"].lower() not in {"en", "english"}:
        report.warning("document.language is not English; extraction rules are optimized for English text.")


def _validate_research_question(value: Any, report: ValidationReport) -> None:
    _require_mapping(value, "research_question", report)
    if not isinstance(value, dict):
        return
    _require_keys(value, ["question", "scope", "evidence"], "research_question", report)
    _require_nonempty_string(value.get("question"), "research_question.question", report)
    _require_nonempty_string(value.get("scope"), "research_question.scope", report)
    _validate_evidence(value.get("evidence"), "research_question.evidence", report, minimum=1)
    confidence = value.get("confidence")
    if confidence is not None and confidence not in CONFIDENCE_VALUES:
        report.error("research_question.confidence must be high, medium, or low.")


def _validate_study_profile(value: Any, report: ValidationReport) -> None:
    _require_mapping(value, "study_profile", report)
    if not isinstance(value, dict):
        return
    for key in ("organism_or_system", "study_design", "model_type", "sample_scale", "time_scale"):
        if key not in value:
            report.warning(f"study_profile.{key} is missing; use 'Not reported' when appropriate.")
        elif not isinstance(value[key], str):
            report.error(f"study_profile.{key} must be a string.")


def _validate_variables(value: Any, report: ValidationReport) -> set[str]:
    _require_list(value, "variables", report)
    ids: set[str] = set()
    if not isinstance(value, list):
        return ids
    if not value:
        report.error("variables must contain at least one record.")
    for index, variable in enumerate(value):
        path = f"variables[{index}]"
        _require_mapping(variable, path, report)
        if not isinstance(variable, dict):
            continue
        required = [
            "variable_id",
            "raw_name",
            "canonical_name",
            "symbol",
            "aliases",
            "role",
            "kind",
            "definition",
            "unit",
            "value_or_range",
            "relationship",
            "evidence",
            "confidence",
            "notes",
        ]
        _require_keys(variable, required, path, report)
        if report.errors and any(key not in variable for key in required):
            continue

        variable_id = variable.get("variable_id")
        if not isinstance(variable_id, str) or not re.fullmatch(r"V\d{3,}", variable_id):
            report.error(f"{path}.variable_id must match V000 (for example V001).")
        elif variable_id in ids:
            report.error(f"{path}.variable_id '{variable_id}' is duplicated.")
        else:
            ids.add(variable_id)

        for key in (
            "raw_name",
            "canonical_name",
            "symbol",
            "definition",
            "unit",
            "value_or_range",
            "relationship",
            "notes",
        ):
            _require_nonempty_string(variable.get(key), f"{path}.{key}", report)

        symbol = variable.get("symbol")
        if isinstance(symbol, str) and not _SYMBOL_ALLOWED.fullmatch(symbol.strip()):
            report.error(
                f"{path}.symbol {symbol!r} is not a compact notation; "
                "use letters, digits, _, ^, [], (), +, -, or /."
            )

        aliases = variable.get("aliases")
        if not isinstance(aliases, list) or not all(isinstance(item, str) and item.strip() for item in aliases):
            report.error(f"{path}.aliases must be an array of non-empty strings.")

        role = variable.get("role")
        if role not in ROLE_VALUES:
            report.error(f"{path}.role must be one of: {', '.join(sorted(ROLE_VALUES))}.")
        kind = variable.get("kind")
        if kind not in KIND_VALUES:
            report.error(f"{path}.kind must be one of: {', '.join(sorted(KIND_VALUES))}.")
        confidence = variable.get("confidence")
        if confidence not in CONFIDENCE_VALUES:
            report.error(f"{path}.confidence must be high, medium, or low.")

        _validate_evidence(variable.get("evidence"), f"{path}.evidence", report, minimum=1)

        unit = variable.get("unit")
        if isinstance(unit, str) and unit.strip().lower() in _NOT_REPORTED:
            report.warning(f"{path}.unit is not reported; confirm that the source does not provide one.")
        if confidence == "low":
            notes = variable.get("notes")
            if isinstance(notes, str) and notes.strip().lower() in {"", "none", "n/a", "na"}:
                report.warning(f"{path} has low confidence but no explanation in notes.")
    return ids


def _validate_relationships(value: Any, variable_ids: set[str], report: ValidationReport) -> None:
    _require_list(value, "relationships", report)
    if not isinstance(value, list):
        return
    for index, relationship in enumerate(value):
        path = f"relationships[{index}]"
        _require_mapping(relationship, path, report)
        if not isinstance(relationship, dict):
            continue
        _require_keys(relationship, ["relationship_id", "type", "from", "to", "expression", "evidence", "notes"], path, report)
        required = ["relationship_id", "type", "from", "to", "expression", "evidence", "notes"]
        if report.errors and any(key not in relationship for key in required):
            continue
        relationship_id = relationship.get("relationship_id")
        if not isinstance(relationship_id, str) or not re.fullmatch(r"R\d{3,}", relationship_id):
            report.error(f"{path}.relationship_id must match R000 (for example R001).")
        if relationship.get("type") not in RELATIONSHIP_TYPES:
            report.error(
                f"{path}.type must be one of: {', '.join(sorted(RELATIONSHIP_TYPES))}."
            )
        for key in ("from", "to"):
            targets = relationship.get(key)
            if not isinstance(targets, list) or not all(isinstance(item, str) for item in targets):
                report.error(f"{path}.{key} must be an array of variable IDs.")
                continue
            for target in targets:
                if target not in variable_ids:
                    report.error(f"{path}.{key} references unknown variable '{target}'.")
        for key in ("expression", "notes"):
            _require_nonempty_string(relationship.get(key), f"{path}.{key}", report)
        _validate_evidence(relationship.get("evidence"), f"{path}.evidence", report, minimum=1)


def _validate_unresolved(value: Any, variable_ids: set[str], report: ValidationReport) -> None:
    _require_list(value, "unresolved", report)
    if not isinstance(value, list):
        return
    for index, item in enumerate(value):
        path = f"unresolved[{index}]"
        _require_mapping(item, path, report)
        if not isinstance(item, dict):
            continue
        _require_keys(item, ["issue", "related_variables", "evidence", "recommended_action"], path, report)
        for key in ("issue", "recommended_action"):
            _require_nonempty_string(item.get(key), f"{path}.{key}", report)
        related = item.get("related_variables")
        if not isinstance(related, list) or not all(isinstance(variable, str) for variable in related):
            report.error(f"{path}.related_variables must be an array of variable IDs.")
        else:
            for variable in related:
                if variable not in variable_ids:
                    report.error(f"{path}.related_variables references unknown variable '{variable}'.")
        _validate_evidence(item.get("evidence"), f"{path}.evidence", report, minimum=0)


def _validate_metadata(value: Any, report: ValidationReport) -> None:
    _require_mapping(value, "extraction_metadata", report)
    if not isinstance(value, dict):
        return
    required = ["extracted_at", "extractor", "coverage", "method", "warnings"]
    _require_keys(value, required, "extraction_metadata", report)
    for key in ("extracted_at", "extractor", "coverage", "method"):
        _require_nonempty_string(value.get(key), f"extraction_metadata.{key}", report)
    warnings = value.get("warnings")
    if not isinstance(warnings, list) or not all(isinstance(item, str) for item in warnings):
        report.error("extraction_metadata.warnings must be an array of strings.")
    review_status = value.get("review_status")
    if review_status is not None and review_status not in REVIEW_STATUS_VALUES:
        report.error(
            "extraction_metadata.review_status must be scaffold, needs_review, or reviewed."
        )


def _validate_final_quality(payload: dict[str, Any], report: ValidationReport) -> None:
    """Reject drafts when an extraction is presented as a final deliverable."""
    metadata = payload.get("extraction_metadata", {})
    if not isinstance(metadata, dict):
        return

    extractor = str(metadata.get("extractor", ""))
    if "scaffold" in extractor.lower():
        report.error(
            "final validation rejected scaffold extractor; complete the Agent semantic review first."
        )

    review_status = str(metadata.get("review_status", "")).strip().lower()
    if review_status != FINAL_REVIEW_STATUS:
        report.error(
            "final validation requires extraction_metadata.review_status='reviewed'."
        )
    for key in ("reviewer", "reviewed_at"):
        _require_nonempty_string(
            metadata.get(key), f"extraction_metadata.{key}", report
        )

    warnings = metadata.get("warnings", [])
    if isinstance(warnings, list):
        draft_markers = (
            "not a completed semantic review",
            "keyword-derived",
            "false positives",
            "omit implicit variables",
            "requires agent review",
            "requires semantic confirmation",
        )
        for warning in warnings:
            lowered = str(warning).lower()
            if any(marker in lowered for marker in draft_markers):
                report.error(
                    "final validation rejected metadata warning that describes a draft: "
                    f"{warning}"
                )

    semantic = metadata.get("semantic_review", {})
    if not isinstance(semantic, dict) or not semantic:
        report.warning("extraction_metadata.semantic_review is absent; use semantic-review to record evidence-bound review history.")
    else:
        for key in ("reviewer", "reviewed_at", "changed_variable_count"):
            if key not in semantic:
                report.warning(f"extraction_metadata.semantic_review.{key} is absent from this reviewed extraction.")
        if semantic.get("reviewer") != metadata.get("reviewer"):
            report.warning("semantic_review.reviewer differs from extraction_metadata.reviewer.")

    variables = payload.get("variables", [])
    if not isinstance(variables, list):
        return
    for index, variable in enumerate(variables):
        if not isinstance(variable, dict):
            continue
        path = f"variables[{index}]"
        if variable.get("confidence") == "low":
            report.error(
                f"final validation rejected {path}: low-confidence candidates must be "
                "confirmed, reclassified, or removed."
            )
        notes = str(variable.get("notes", "")).lower()
        if "automatically proposed" in notes or "requires semantic confirmation" in notes:
            report.error(
                f"final validation rejected {path}: notes still describe an unconfirmed scaffold candidate."
            )


def _validate_evidence(
    value: Any,
    path: str,
    report: ValidationReport,
    *,
    minimum: int,
) -> None:
    if not isinstance(value, list):
        report.error(f"{path} must be an array.")
        return
    if len(value) < minimum:
        report.error(f"{path} must contain at least {minimum} evidence reference(s).")
    for index, evidence in enumerate(value):
        item_path = f"{path}[{index}]"
        _require_mapping(evidence, item_path, report)
        if not isinstance(evidence, dict):
            continue
        _require_keys(evidence, ["block_id", "quote"], item_path, report)
        _require_nonempty_string(evidence.get("block_id"), f"{item_path}.block_id", report)
        _require_nonempty_string(evidence.get("quote"), f"{item_path}.quote", report)
        if "page" in evidence and evidence["page"] is not None and not isinstance(evidence["page"], int):
            report.error(f"{item_path}.page must be an integer or null.")
        if "section" in evidence and not isinstance(evidence["section"], str):
            report.error(f"{item_path}.section must be a string when present.")


def _validate_evidence_references(
    payload: dict[str, Any],
    known_block_ids: set[str] | None,
    known_sections: set[str] | None,
    block_text: dict[str, str] | None,
    report: ValidationReport,
) -> None:
    if known_block_ids is None and block_text is None:
        return
    for path, evidence in _walk_evidence(payload):
        block_id = evidence.get("block_id")
        if known_block_ids is not None and isinstance(block_id, str) and block_id not in known_block_ids:
            report.error(f"{path}.block_id '{block_id}' is not present in the prepared source.")
        quote = evidence.get("quote")
        if block_text is not None and isinstance(block_id, str) and isinstance(quote, str):
            source_text = block_text.get(block_id)
            if source_text is not None and not _quote_matches(quote, source_text):
                report.error(
                    f"{path}.quote was not found in block {block_id}. "
                    "Copy an exact contiguous quote from the prepared chunk."
                )
        section = evidence.get("section")
        if known_sections and isinstance(section, str) and section and section not in known_sections:
            report.warning(f"{path}.section '{section}' is not a detected source section.")


def _quote_matches(quote: str, block_text: str) -> bool:
    def normalize(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip().lower()

    normalized_quote = normalize(quote)
    normalized_block = normalize(block_text)
    if not normalized_quote:
        return False
    if normalized_quote in normalized_block:
        return True
    # Allow minor PDF extraction artifacts such as hyphenation or ligature loss,
    # but require high similarity to the best matching block region.
    if len(normalized_quote) < 24:
        return False
    window = max(len(normalized_quote) + 40, int(len(normalized_quote) * 1.35))
    best = 0.0
    if len(normalized_block) <= window:
        best = SequenceMatcher(None, normalized_quote, normalized_block).ratio()
    else:
        step = max(1, len(normalized_quote) // 4)
        for start in range(0, max(1, len(normalized_block) - len(normalized_quote) + 1), step):
            segment = normalized_block[start : start + window]
            best = max(best, SequenceMatcher(None, normalized_quote, segment).ratio())
            if best >= 0.92:
                break
    return best >= 0.86


def _walk_evidence(payload: Any, path: str = "root") -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(payload, dict):
        if "block_id" in payload and "quote" in payload:
            yield path, payload
            return
        for key, value in payload.items():
            yield from _walk_evidence(value, f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            yield from _walk_evidence(value, f"{path}[{index}]")


def _validate_symbol_uniqueness(value: Any, report: ValidationReport) -> None:
    if not isinstance(value, list):
        return
    seen: dict[str, tuple[str, str]] = {}
    for index, variable in enumerate(value):
        if not isinstance(variable, dict):
            continue
        symbol = variable.get("symbol")
        meaning = variable.get("canonical_name")
        if not isinstance(symbol, str) or not isinstance(meaning, str):
            continue
        normalized = symbol.strip()
        if normalized in seen:
            previous_id, previous_meaning = seen[normalized]
            report.warning(
                f"Symbol '{normalized}' is reused by {previous_id} ({previous_meaning}) "
                f"and variables[{index}] ({meaning}); add explicit disambiguation."
            )
        else:
            seen[normalized] = (str(variable.get("variable_id", f"variables[{index}]")), meaning)


def format_report(report: ValidationReport, *, final: bool = False) -> str:
    prefix = "Final validation" if final else "Validation"
    lines: list[str] = []
    if report.ok and not report.warnings:
        return f"{prefix} passed with no errors or warnings."
    if report.errors:
        lines.append(f"Errors ({len(report.errors)}):")
        lines.extend(f"  - {message}" for message in report.errors)
    if report.warnings:
        lines.append(f"Warnings ({len(report.warnings)}):")
        lines.extend(f"  - {message}" for message in report.warnings)
    if report.ok:
        lines.insert(0, f"{prefix} passed with warnings.")
    else:
        lines.insert(0, f"{prefix} failed.")
    return "\n".join(lines)

