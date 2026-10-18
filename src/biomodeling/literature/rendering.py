"""Deterministic Markdown cross-reference rendering."""

from __future__ import annotations

from collections import Counter
from typing import Any

ROLE_LABELS = {
    "independent": "Independent variable",
    "dependent": "Dependent variable",
    "controlled": "Controlled variable",
    "covariate": "Covariate",
    "parameter": "Model parameter",
    "derived": "Derived quantity",
    "categorical": "Categorical variable",
    "latent": "Latent variable",
    "other": "Other analytical variable",
}

KIND_LABELS = {
    "continuous": "Continuous",
    "discrete": "Discrete",
    "binary": "Binary",
    "categorical": "Categorical",
    "ordinal": "Ordinal",
    "count": "Count",
    "rate": "Rate",
    "constant": "Constant",
    "unknown": "Unknown",
}


def render_markdown(payload: dict[str, Any], *, final: bool = False) -> str:
    document = payload.get("document", {})
    question = payload.get("research_question", {})
    profile = payload.get("study_profile", {})
    variables = [item for item in payload.get("variables", []) if isinstance(item, dict)]
    relationships = [item for item in payload.get("relationships", []) if isinstance(item, dict)]
    unresolved = [item for item in payload.get("unresolved", []) if isinstance(item, dict)]
    metadata = payload.get("extraction_metadata", {})

    lines: list[str] = []
    lines.append("# Variable and Parameter Cross-Reference")
    lines.append("")
    if final:
        lines.append("> Final reviewed extraction. This document passed the final quality gate.")
    else:
        lines.append(
            "> DRAFT / NOT FINAL. Semantic review and final validation are required before "
            "this document is treated as a completed extraction."
        )
    lines.append("")
    lines.append("## Document")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.extend(
        _table_row(field, value)
        for field, value in [
            ("Title", document.get("title", "Not reported")),
            ("Authors", document.get("authors", "Not reported")),
            ("Year", document.get("year", "Not reported")),
            ("Source", document.get("source_name", "Not reported")),
            ("Language", document.get("language", "Not reported")),
        ]
    )
    lines.append("")

    lines.append("## Research Question")
    lines.append("")
    lines.append(f"**Question:** {_inline(question.get('question', 'Not reported'))}")
    lines.append("")
    lines.append(f"**Scope:** {_inline(question.get('scope', 'Not reported'))}")
    lines.append("")
    lines.append(f"**Confidence:** {_inline(question.get('confidence', 'Not reported'))}")
    lines.append("")
    lines.append("**Evidence:**")
    lines.extend(_format_evidence(question.get("evidence", [])))
    lines.append("")

    lines.append("## Study Profile")
    lines.append("")
    lines.append("| Dimension | Description |")
    lines.append("| --- | --- |")
    for field, key in [
        ("Organism or system", "organism_or_system"),
        ("Study design", "study_design"),
        ("Model type", "model_type"),
        ("Sample scale", "sample_scale"),
        ("Time scale", "time_scale"),
    ]:
        lines.append(_table_row(field, profile.get(key, "Not reported")))
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total variables and parameters: **{len(variables)}**")
    role_counts = Counter(str(item.get("role", "other")) for item in variables)
    if role_counts:
        for role, count in sorted(role_counts.items()):
            lines.append(f"- {ROLE_LABELS.get(role, role)}: **{count}**")
    confidence_counts = Counter(str(item.get("confidence", "unknown")) for item in variables)
    if confidence_counts:
        summary = ", ".join(f"{key}: {value}" for key, value in sorted(confidence_counts.items()))
        lines.append(f"- Confidence: {summary}")
    lines.append("")

    lines.append("## Role and Type Overview")
    lines.append("")
    lines.append("| Symbol | Canonical name | Author term | Role | Type | Unit | Confidence |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for variable in variables:
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(variable.get("symbol", "")),
                    _cell(variable.get("canonical_name", "")),
                    _cell(variable.get("raw_name", "")),
                    _cell(ROLE_LABELS.get(str(variable.get("role")), variable.get("role", ""))),
                    _cell(KIND_LABELS.get(str(variable.get("kind")), variable.get("kind", ""))),
                    _cell(variable.get("unit", "")),
                    _cell(variable.get("confidence", "")),
                ]
            )
            + " |"
        )
    lines.append("")

    lines.append("## Full Cross-Reference Table")
    lines.append("")
    for variable in variables:
        variable_id = _inline(variable.get("variable_id", "Unidentified"))
        symbol = _inline(variable.get("symbol", "Not assigned"))
        if variable.get("derivative"):
            symbol = f"{symbol} / {_inline(variable.get('derivative'))}"
        canonical = _inline(variable.get("canonical_name", "Unnamed"))
        lines.append(f"### {variable_id} — {symbol}: {canonical}")
        lines.append("")
        lines.append("| Attribute | Value |")
        lines.append("| --- | --- |")
        rows = [
            ("Author term", variable.get("raw_name", "Not reported")),
            ("Author symbol", variable.get("author_symbol", "Not reported")),
            ("Symbol rationale", variable.get("symbol_notes", "Not reported")),
            ("Aliases", ", ".join(variable.get("aliases", [])) or "None reported"),
            ("Role", ROLE_LABELS.get(str(variable.get("role")), variable.get("role", "Not reported"))),
            ("Type", KIND_LABELS.get(str(variable.get("kind")), variable.get("kind", "Not reported"))),
            ("Definition", variable.get("definition", "Not reported")),
            ("Unit", variable.get("unit", "Not reported")),
            ("Value or range", variable.get("value_or_range", "Not reported")),
            ("Relationship", variable.get("relationship", "Not reported")),
            ("Confidence", variable.get("confidence", "Not reported")),
            ("Notes", variable.get("notes", "None")),
        ]
        lines.extend(_table_row(field, value) for field, value in rows)
        lines.append("")
        lines.append("**Evidence:**")
        lines.extend(_format_evidence(variable.get("evidence", [])))
        lines.append("")

    lines.append("## Relationships")
    lines.append("")
    if relationships:
        lines.append("| ID | Type | From | To | Expression or claim | Evidence |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for relationship in relationships:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _cell(relationship.get("relationship_id", "")),
                        _cell(relationship.get("type", "")),
                        _cell(", ".join(relationship.get("from", []))),
                        _cell(", ".join(relationship.get("to", []))),
                        _cell(relationship.get("expression", "")),
                        _cell(_evidence_summary(relationship.get("evidence", []))),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No evidence-backed relationships were extracted.")
    lines.append("")

    lines.append("## Symbol Notes")
    lines.append("")
    symbol_variables: dict[str, list[dict[str, Any]]] = {}
    for variable in variables:
        symbol_variables.setdefault(str(variable.get("symbol", "")), []).append(variable)
    collisions = {symbol: items for symbol, items in symbol_variables.items() if symbol and len(items) > 1}
    if collisions:
        lines.append("| Symbol | Variables | Disambiguation |")
        lines.append("| --- | --- | --- |")
        for symbol, items in sorted(collisions.items()):
            ids = ", ".join(str(item.get("variable_id", "")) for item in items)
            meanings = "; ".join(str(item.get("canonical_name", "")) for item in items)
            notes = " ".join(str(item.get("notes", "")) for item in items)
            lines.append(_table_row(symbol, f"{ids}: {meanings}", notes or "Not documented"))
    else:
        lines.append("No symbol collisions detected.")
    lines.append("")

    lines.append("## Unresolved or Ambiguous Items")
    lines.append("")
    if unresolved:
        lines.append("| Issue | Related variables | Evidence | Recommended action |")
        lines.append("| --- | --- | --- | --- |")
        for item in unresolved:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _cell(item.get("issue", "")),
                        _cell(", ".join(item.get("related_variables", []))),
                        _cell(_evidence_summary(item.get("evidence", []))),
                        _cell(item.get("recommended_action", "")),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No unresolved or ambiguous items were recorded.")
    lines.append("")

    semantic = metadata.get("semantic_review", {}) if isinstance(metadata, dict) else {}
    if isinstance(semantic, dict) and semantic:
        lines.append("## Semantic Review")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("| --- | --- |")
        lines.append(_table_row("Reviewer", semantic.get("reviewer", "Not reported")))
        lines.append(_table_row("Reviewed at", semantic.get("reviewed_at", "Not reported")))
        lines.append(_table_row("Changed variables", semantic.get("changed_variable_count", "Not reported")))
        lines.append("")
        changes = semantic.get("changes", [])
        if isinstance(changes, list) and changes:
            lines.append("| Variable | Changed fields |")
            lines.append("| --- | --- |")
            for change in changes:
                if isinstance(change, dict):
                    fields = change.get("changed_fields", [])
                    lines.append(_table_row(change.get("variable_id", ""), ", ".join(str(item) for item in fields) if isinstance(fields, list) else fields))
            lines.append("")

    lines.append("## Extraction Metadata")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.extend(
        _table_row(field, value)
        for field, value in [
            ("Extracted at", metadata.get("extracted_at", "Not reported")),
            ("Extractor", metadata.get("extractor", "Not reported")),
            ("Review status", metadata.get("review_status", "Not reviewed")),
            ("Reviewer", metadata.get("reviewer", "Not reported")),
            ("Reviewed at", metadata.get("reviewed_at", "Not reported")),
            ("Coverage", metadata.get("coverage", "Not reported")),
            ("Method", metadata.get("method", "Not reported")),
            ("Warnings", "; ".join(metadata.get("warnings", [])) or "None"),
        ]
    )
    lines.append("")
    return "\n".join(lines)


def _format_evidence(evidence: Any) -> list[str]:
    if not isinstance(evidence, list) or not evidence:
        return ["- None recorded."]
    lines: list[str] = []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        block_id = _inline(item.get("block_id", "Unknown block"))
        page = item.get("page")
        section = item.get("section")
        location = []
        if page is not None:
            location.append(f"p. {page}")
        if section:
            location.append(str(section))
        suffix = f" ({', '.join(location)})" if location else ""
        lines.append(f"- `{block_id}`{suffix}: “{_inline(item.get('quote', ''))}”")
    return lines or ["- None recorded."]


def _evidence_summary(evidence: Any) -> str:
    if not isinstance(evidence, list):
        return ""
    refs = []
    for item in evidence:
        if isinstance(item, dict):
            block_id = item.get("block_id")
            page = item.get("page")
            if block_id and page is not None:
                refs.append(f"{block_id} (p. {page})")
            elif block_id:
                refs.append(str(block_id))
    return "; ".join(refs)


def _table_row(field: Any, value: Any) -> str:
    return f"| {_cell(field)} | {_cell(value)} |"


def _cell(value: Any) -> str:
    if value is None:
        return "Not reported"
    text = str(value)
    text = text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")
    return text.strip() or "Not reported"


def _inline(value: Any) -> str:
    if value is None:
        return "Not reported"
    return str(value).replace("\n", " ").strip() or "Not reported"
