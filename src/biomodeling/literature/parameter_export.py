"""Export extracted parameters and variables to standalone Markdown files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

DEFAULT_OUTPUT_DIR = Path.cwd() / "runs"

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


def safe_filename(value: str, fallback: str = "parameters") -> str:
    """Convert a title or identifier into a filesystem-safe Markdown filename."""
    text = re.sub(r"[\\/:*?\"<>|\r\n\t]+", "_", str(value or "")).strip(" ._")
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"_+", "_", text)
    if not text:
        text = fallback
    return text[:120] + ("" if text.lower().endswith(".md") else ".md")


def render_parameters_markdown(
    payload: dict[str, Any],
    *,
    include_other_roles: bool = True,
    include_relationships: bool = True,
    include_unresolved: bool = True,
    title_suffix: str = "",
) -> str:
    """Render one extraction payload as a focused parameter Markdown document."""
    document = payload.get("document", {}) if isinstance(payload.get("document"), dict) else {}
    question = payload.get("research_question", {}) if isinstance(payload.get("research_question"), dict) else {}
    profile = payload.get("study_profile", {}) if isinstance(payload.get("study_profile"), dict) else {}
    variables = [item for item in payload.get("variables", []) if isinstance(item, dict)]
    relationships = [item for item in payload.get("relationships", []) if isinstance(item, dict)]
    unresolved = [item for item in payload.get("unresolved", []) if isinstance(item, dict)]
    metadata = payload.get("extraction_metadata", {}) if isinstance(payload.get("extraction_metadata"), dict) else {}

    if include_other_roles:
        selected = variables
    else:
        selected = [item for item in variables if str(item.get("role")) in {"parameter", "controlled", "covariate", "constant"}]

    lines: list[str] = []
    title = str(document.get("title") or document.get("source_name") or "Extracted Parameters")
    lines.append(f"# Extracted Parameters and Variables — {_inline(title)}{title_suffix}")
    lines.append("")
    lines.append(f"- Source: {_inline(document.get('source_name', 'Not reported'))}")
    lines.append(f"- DOI: {_inline(document.get('doi') or 'Not reported')}")
    lines.append(f"- Year: {_inline(document.get('year', 'Not reported'))}")
    lines.append(f"- Language: {_inline(document.get('language', 'Not reported'))}")
    lines.append(f"- Review status: {_inline(metadata.get('review_status', 'Not reported'))}")
    lines.append(f"- Reviewer: {_inline(metadata.get('reviewer') or 'Not reported')}")
    lines.append(f"- Total variables: {len(variables)}")
    lines.append(f"- Total parameters: {sum(1 for item in variables if str(item.get('role')) == 'parameter')}")
    lines.append(f"- Exported records: {len(selected)}")
    lines.append("")

    if question.get("question"):
        lines.append("## Research Question")
        lines.append("")
        lines.append(_inline(question.get("question")))
        lines.append("")

    if profile:
        lines.append("## Study Profile")
        lines.append("")
        lines.append("| Dimension | Description |")
        lines.append("| --- | --- |")
        for field, key in (
            ("Organism or system", "organism_or_system"),
            ("Study design", "study_design"),
            ("Model type", "model_type"),
            ("Sample scale", "sample_scale"),
            ("Time scale", "time_scale"),
        ):
            lines.append(f"| {_cell(field)} | {_cell(profile.get(key, 'Not reported'))} |")
        lines.append("")

    lines.append("## Parameter Summary")
    lines.append("")
    lines.append("| Variable ID | Author term | Canonical name | Symbol | Author symbol | Derivative | Role | Type | Unit | Value or range | Confidence |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for item in selected:
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(item.get("variable_id", "")),
                    _cell(item.get("raw_name", "")),
                    _cell(item.get("canonical_name", "")),
                    _cell(item.get("symbol", "")),
                    _cell(item.get("author_symbol", "")),
                    _cell(item.get("derivative", "") or "—"),
                    _cell(ROLE_LABELS.get(str(item.get("role")), item.get("role", ""))),
                    _cell(KIND_LABELS.get(str(item.get("kind")), item.get("kind", ""))),
                    _cell(item.get("unit", "")),
                    _cell(item.get("value_or_range", "")),
                    _cell(item.get("confidence", "")),
                ]
            )
            + " |"
        )
    if not selected:
        lines.append("| — | No parameter records matched the export filter. | — | — | — | — | — | — | — |")
    lines.append("")

    lines.append("## Detailed Parameter Records")
    lines.append("")
    for item in selected:
        identifier = _inline(item.get("variable_id", ""))
        lines.append(f"### {identifier} — {_inline(item.get('canonical_name') or item.get('raw_name') or '')}")
        lines.append("")
        lines.append(f"- **Author term:** {_inline(item.get('raw_name', 'Not reported'))}")
        lines.append(f"- **Aliases:** {_inline(', '.join(str(a) for a in item.get('aliases', [])) or 'None reported')}")
        lines.append(f"- **Symbol:** {_inline(item.get('symbol', 'Not reported'))}")
        lines.append(f"- **Author symbol:** {_inline(item.get('author_symbol', 'Not reported'))}")
        lines.append(f"- **Symbol rationale:** {_inline(item.get('symbol_notes', 'Not reported'))}")
        if item.get("derivative"):
            lines.append(f"- **Time derivative:** `{_inline(item.get('derivative'))}`")
        lines.append(f"- **Role:** {_inline(ROLE_LABELS.get(str(item.get('role')), item.get('role', 'Not reported')))}")
        lines.append(f"- **Type:** {_inline(KIND_LABELS.get(str(item.get('kind')), item.get('kind', 'Not reported')))}")
        lines.append(f"- **Definition:** {_inline(item.get('definition', 'Not reported'))}")
        lines.append(f"- **Unit:** {_inline(item.get('unit', 'Not reported'))}")
        lines.append(f"- **Value or range:** {_inline(item.get('value_or_range', 'Not reported'))}")
        lines.append(f"- **Relationship:** {_inline(item.get('relationship', 'Not reported'))}")
        lines.append(f"- **Confidence:** {_inline(item.get('confidence', 'Not reported'))}")
        lines.append(f"- **Notes:** {_inline(item.get('notes', 'Not reported'))}")
        evidence = item.get("evidence", [])
        if isinstance(evidence, list) and evidence:
            lines.append("- **Evidence:**")
            for reference in evidence:
                if not isinstance(reference, dict):
                    continue
                block_id = _inline(reference.get("block_id", ""))
                section = _inline(reference.get("section", ""))
                page = reference.get("page")
                location = ", ".join(str(part) for part in (section, f"p. {page}" if page is not None else "") if part)
                lines.append(f"  - `{block_id}`{f' ({location})' if location else ''}: “{_inline(reference.get('quote', ''))}”")
        else:
            lines.append("- **Evidence:** None recorded.")
        lines.append("")

    if include_relationships and relationships:
        lines.append("## Relationships")
        lines.append("")
        lines.append("| ID | Type | From | To | Expression | Evidence |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for relation in relationships:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _cell(relation.get("relationship_id", "")),
                        _cell(relation.get("type", "")),
                        _cell(", ".join(str(x) for x in relation.get("from", []))),
                        _cell(", ".join(str(x) for x in relation.get("to", []))),
                        _cell(relation.get("expression", "")),
                        _cell(_evidence_summary(relation.get("evidence", []))),
                    ]
                )
                + " |"
            )
        lines.append("")

    if include_unresolved and unresolved:
        lines.append("## Unresolved or Ambiguous Items")
        lines.append("")
        lines.append("| Issue | Related variables | Recommended action |")
        lines.append("| --- | --- | --- |")
        for item in unresolved:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _cell(item.get("issue", "")),
                        _cell(", ".join(str(x) for x in item.get("related_variables", []))),
                        _cell(item.get("recommended_action", "")),
                    ]
                )
                + " |"
            )
        lines.append("")

    lines.append("## Export Metadata")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Extractor | {_cell(metadata.get('extractor', 'Not reported'))} |")
    lines.append(f"| Extracted at | {_cell(metadata.get('extracted_at', 'Not reported'))} |")
    lines.append(f"| Reviewed at | {_cell(metadata.get('reviewed_at', 'Not reported'))} |")
    lines.append(f"| Coverage | {_cell(metadata.get('coverage', 'Not reported'))} |")
    lines.append(f"| Warnings | {_cell('; '.join(str(w) for w in metadata.get('warnings', [])) or 'None')} |")
    lines.append("")
    return "\n".join(lines)


def export_parameters_markdown(
    payload: dict[str, Any],
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    *,
    filename: str | None = None,
    include_other_roles: bool = True,
    include_relationships: bool = True,
    include_unresolved: bool = True,
) -> Path:
    """Write one payload to a Markdown file and return the written path."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    document = payload.get("document", {}) if isinstance(payload.get("document"), dict) else {}
    default_name = Path(str(document.get("source_name") or "parameters")).stem
    target = directory / (filename if filename else safe_filename(document.get("title") or default_name, fallback=default_name))
    text = render_parameters_markdown(
        payload,
        include_other_roles=include_other_roles,
        include_relationships=include_relationships,
        include_unresolved=include_unresolved,
    )
    target.write_text(text, encoding="utf-8")
    return target


def export_parameters_batch(
    inputs: Iterable[Path],
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    *,
    include_other_roles: bool = True,
    include_relationships: bool = True,
    include_unresolved: bool = True,
) -> list[Path]:
    """Export many extraction JSON files to Markdown and return written paths."""
    written: list[Path] = []
    for path in inputs:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        written.append(
            export_parameters_markdown(
                payload,
                output_dir,
                include_other_roles=include_other_roles,
                include_relationships=include_relationships,
                include_unresolved=include_unresolved,
            )
        )
    return written


def _evidence_summary(evidence: Any) -> str:
    if not isinstance(evidence, list):
        return ""
    parts = []
    for item in evidence:
        if isinstance(item, dict) and item.get("block_id"):
            page = item.get("page")
            parts.append(f"{item['block_id']} (p. {page})" if page is not None else str(item["block_id"]))
    return "; ".join(parts)


def _cell(value: Any) -> str:
    if value is None:
        return "Not reported"
    text = str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")
    return text.strip() or "Not reported"


def _inline(value: Any) -> str:
    if value is None:
        return "Not reported"
    return str(value).replace("\n", " ").strip() or "Not reported"

