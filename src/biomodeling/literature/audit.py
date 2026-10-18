"""Deterministic self-audit for variable extraction scaffolds.

The audit is intentionally evidence-bound: it inspects only the extraction
payload and the prepared source blocks.  It does not claim that a candidate is
semantically correct merely because it passed a keyword rule.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pathlib import Path
from .io_utils import load_json

_NOT_REPORTED = {"not reported", "unknown", "n/a", "na", "none", ""}

# Units and purely grammatical words must never be variable candidates.
UNIT_WORDS = {
    "au", "a.u.", "day", "days", "fold", "g", "h", "hour", "hours", "kg",
    "l", "m", "mg", "min", "ml", "mm", "ms", "mM", "nM", "pM", "s", "second",
    "seconds", "uM", "µM", "percent", "percentage",
}
STOP_WORDS = {
    "a", "all", "an", "and", "are", "as", "at", "be", "by", "can", "composed",
    "corresponding", "defined", "denote", "denotes", "each", "for", "from",
    "function", "given", "happ", "here", "in", "is", "it", "letting", "linearly",
    "matrix", "may", "method", "model", "of", "on", "or", "other", "over",
    "rows", "run", "runs", "starting", "step", "step0", "takes", "the", "these",
    "this", "to", "using", "was", "we", "were", "where", "with", "yielding",
}
# Phrases that indicate the candidate is a sentence fragment rather than a name.
FRAGMENT_PREFIXES = (
    "and ", "as ", "at ", "by ", "for ", "from ", "how ", "in ", "of ", "on ",
    "the ", "these ", "this ", "to ", "using ", "we ", "when ", "where ", "which ",
)
PARAMETER_HINTS = (
    "rate constant", "rate constants", "association rate", "dissociation rate",
    "binding rate", "transition rate", "release rate", "clearance rate",
    "half-life", "half life", "km", "kcat", "vmax", "ic50", "ic90", "ec50",
    "kd", "ka", "kon", "koff", "k_on", "k_off", "hill coefficient",
    "michaelis", "affinity", "equilibrium constant", "diffusion coefficient",
    "permeability", "conductance", "free energy", "activation energy",
    "temperature", "threshold", "sensitivity", "specificity", "auroc", "auprc",
)
VARIABLE_HINTS = (
    "abundance", "activity", "biomarker", "cell number", "concentration",
    "copy number", "dose", "expression", "flux", "fraction", "genotype",
    "level", "mutation", "occupancy", "phosphorylation", "population",
    "probability", "ratio", "state", "time", "volume",
)


@dataclass
class AuditFinding:
    severity: str
    code: str
    message: str
    variable_ids: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "variable_ids": self.variable_ids,
        }


@dataclass
class AuditReport:
    findings: list[AuditFinding] = field(default_factory=list)
    checked_variables: int = 0

    @property
    def error_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "warning")

    @property
    def ok(self) -> bool:
        return self.error_count == 0

    def add(self, severity: str, code: str, message: str, ids: list[str] | None = None) -> None:
        self.findings.append(AuditFinding(severity, code, message, ids or []))

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "checked_variables": self.checked_variables,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "findings": [finding.as_dict() for finding in self.findings],
        }


def audit_extraction(
    payload: dict[str, Any],
    *,
    source_path: str | None = None,
    block_text: dict[str, str] | None = None,
    max_findings: int = 200,
) -> AuditReport:
    """Audit one extraction payload for obvious semantic and evidence defects."""
    report = AuditReport()
    variables = [item for item in payload.get("variables", []) if isinstance(item, dict)]
    report.checked_variables = len(variables)

    if not variables:
        report.add("error", "no_variables", "No variable records were produced.")
        return report

    if source_path and block_text is None:
        source = load_json(Path(source_path))
        block_text = {
            str(chunk.get("block_id")): str(chunk.get("text", ""))
            for chunk in source.get("chunks", [])
            if isinstance(chunk, dict) and chunk.get("block_id")
        }
    block_text = block_text or {}

    seen_symbols: dict[str, str] = {}
    seen_names: dict[str, str] = {}

    for index, variable in enumerate(variables):
        variable_id = str(variable.get("variable_id") or f"variables[{index}]")
        raw_name = str(variable.get("raw_name") or "").strip()
        canonical = str(variable.get("canonical_name") or "").strip()
        symbol = str(variable.get("symbol") or "").strip()
        lowered = _normalize_phrase(raw_name or canonical)

        if _is_unit_or_stopword(lowered):
            report.add(
                "error",
                "non_variable_candidate",
                f"{variable_id} ('{raw_name}') is a unit, stopword, or grammatical fragment, not a variable.",
                [variable_id],
            )

        if _looks_like_fragment(raw_name):
            report.add(
                "warning",
                "sentence_fragment",
                f"{variable_id} ('{raw_name}') looks like a sentence fragment and needs semantic review.",
                [variable_id],
            )

        evidence = variable.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            report.add("error", "missing_evidence", f"{variable_id} has no evidence reference.", [variable_id])
        else:
            for ref_index, reference in enumerate(evidence):
                if not isinstance(reference, dict):
                    report.add("error", "invalid_evidence", f"{variable_id} evidence has an invalid entry.", [variable_id])
                    continue
                block_id = str(reference.get("block_id") or "")
                quote = str(reference.get("quote") or "").strip()
                if not block_id or not quote:
                    report.add("error", "empty_evidence", f"{variable_id} evidence is missing a block_id or quote.", [variable_id])
                elif block_text and block_id in block_text:
                    if not _quote_matches(quote, block_text[block_id]):
                        report.add(
                            "error",
                            "evidence_not_in_source",
                            f"{variable_id} evidence quote is not found in source block {block_id}.",
                            [variable_id],
                        )

        if not raw_name or not re.search(r"[A-Za-z]", raw_name):
            report.add("error", "invalid_name", f"{variable_id} has no usable raw name.", [variable_id])

        if symbol:
            if symbol in seen_symbols and seen_symbols[symbol] != variable_id:
                report.add(
                    "warning",
                    "symbol_collision",
                    f"Symbol '{symbol}' is reused by {seen_symbols[symbol]} and {variable_id}.",
                    [seen_symbols[symbol], variable_id],
                )
            else:
                seen_symbols[symbol] = variable_id
        name_key = _normalize_phrase(canonical)
        if name_key:
            if name_key in seen_names and seen_names[name_key] != variable_id:
                report.add(
                    "warning",
                    "duplicate_name",
                    f"Canonical name '{canonical}' appears in {seen_names[name_key]} and {variable_id}.",
                    [seen_names[name_key], variable_id],
                )
            else:
                seen_names[name_key] = variable_id

        if _normalize_phrase(str(variable.get("unit", ""))) in _NOT_REPORTED:
            report.add(
                "info",
                "unit_not_reported",
                f"{variable_id} ('{raw_name}') has no reported unit; verify against the source.",
                [variable_id],
            )

        if str(variable.get("confidence") or "low") == "low":
            report.add(
                "info",
                "low_confidence",
                f"{variable_id} ('{raw_name}') is still low confidence.",
                [variable_id],
            )

        if len(report.findings) >= max_findings:
            report.add("warning", "finding_limit", "Audit stopped after reaching the finding limit.")
            break

    return report


def format_audit(report: AuditReport) -> str:
    if not report.findings:
        return f"Self-audit passed after checking {report.checked_variables} variable(s)."
    lines = [
        f"Self-audit checked {report.checked_variables} variable(s): "
        f"{report.error_count} error(s), {report.warning_count} warning(s)."
    ]
    for finding in report.findings:
        ids = f" [{', '.join(finding.variable_ids)}]" if finding.variable_ids else ""
        lines.append(f"  - {finding.severity.upper()} {finding.code}{ids}: {finding.message}")
    return "\n".join(lines)


def _normalize_phrase(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _is_unit_or_stopword(value: str) -> bool:
    if value in UNIT_WORDS or value in STOP_WORDS:
        return True
    if value.endswith(")"):
        return True
    if value.isdigit():
        return True
    return False


def _looks_like_fragment(name: str) -> bool:
    lowered = name.strip().lower()
    if lowered.startswith(FRAGMENT_PREFIXES):
        return True
    if len(name.split()) > 6:
        return True
    if name.endswith((",", ";", ":")):
        return True
    return False


def _quote_matches(quote: str, block_text: str) -> bool:
    def normalize(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip().lower()
    normalized_quote = normalize(quote)
    normalized_block = normalize(block_text)
    if not normalized_quote:
        return False
    return normalized_quote in normalized_block

