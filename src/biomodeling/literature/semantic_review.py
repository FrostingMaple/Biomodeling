"""Evidence-bound semantic review for extraction candidates.

This module performs deterministic semantic normalisation that can be verified
from supplied source blocks.  It improves candidate names, roles, kinds, units,
symbols, and confidence, while retaining an explicit review trail.  It does not
replace domain-expert review for contested claims.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import AuditReport, audit_extraction
from .symbol_normalization import derivative_expression, normalize_symbol

_NOT_REPORTED = "Not reported"

PARAMETER_LEXICON: tuple[tuple[re.Pattern[str], str, str, str, str], ...] = (
    (re.compile(r"\bk[\s_-]*on\b|association rate constant", re.I), "association rate constant", "k_on", "parameter", "rate"),
    (re.compile(r"\bk[\s_-]*off\b|dissociation rate constant", re.I), "dissociation rate constant", "k_off", "parameter", "rate"),
    (re.compile(r"\bk[\s_-]*cat\b|turnover number", re.I), "catalytic turnover number", "kcat", "parameter", "rate"),
    (re.compile(r"\bK\s*[_ -]?m\b|michaelis[- ]menten constant|half[- ]saturation", re.I), "Michaelis constant", "Km", "parameter", "continuous"),
    (re.compile(r"\bV\s*[_ -]?max\b|maximum (?:reaction )?rate", re.I), "maximum reaction rate", "Vmax", "parameter", "rate"),
    (re.compile(r"\bIC\s*50\b", re.I), "half-maximal inhibitory concentration", "IC50", "parameter", "continuous"),
    (re.compile(r"\bEC\s*50\b", re.I), "half-maximal effective concentration", "EC50", "parameter", "continuous"),
    (re.compile(r"\bK\s*[_ -]?d\b|dissociation constant", re.I), "dissociation constant", "Kd", "parameter", "continuous"),
    (re.compile(r"half[- ]life", re.I), "half-life", "t_half", "parameter", "continuous"),
    (re.compile(r"clearance rate", re.I), "clearance rate", "k_clearance", "parameter", "rate"),
    (re.compile(r"release rate", re.I), "release rate", "k_release", "parameter", "rate"),
    (re.compile(r"transition rate", re.I), "transition rate", "k_transition", "parameter", "rate"),
    (re.compile(r"free[- ]energy", re.I), "free energy", "G_free", "parameter", "continuous"),
    (re.compile(r"\b(AUROC|AUPRC)\b", re.I), "area under the curve", "AUC_metric", "derived", "continuous"),
)

VARIABLE_LEXICON: tuple[tuple[re.Pattern[str], str, str, str, str], ...] = (
    (re.compile(r"\bGFAP\b", re.I), "glial fibrillary acidic protein level", "GFAP", "dependent", "continuous"),
    (re.compile(r"UCH[\s-]*L1", re.I), "ubiquitin C-terminal hydrolase L1 level", "UCH_L1", "dependent", "continuous"),
    (re.compile(r"\bNF[\s-]*L\b", re.I), "neurofilament light chain level", "NF_L", "dependent", "continuous"),
    (re.compile(r"\bERK\b", re.I), "extracellular signal-regulated kinase activity", "ERK", "dependent", "continuous"),
    (re.compile(r"\bAkt\b", re.I), "Akt kinase activity", "Akt", "dependent", "continuous"),
    (re.compile(r"\bEGFR\b|\bErbB1\b", re.I), "epidermal growth factor receptor level", "EGFR", "dependent", "continuous"),
    (re.compile(r"\bNa\+\b|\bsodium\b", re.I), "sodium concentration", "Na", "independent", "continuous"),
    (re.compile(r"\binsulin\b", re.I), "insulin concentration", "insulin", "independent", "continuous"),
    (re.compile(r"\bglucagon\b", re.I), "glucagon concentration", "glucagon", "independent", "continuous"),
    (re.compile(r"\bglucose\b", re.I), "glucose concentration", "glucose", "independent", "continuous"),
    (re.compile(r"\bpseudotime\b", re.I), "pseudotime", "pseudotime", "covariate", "continuous"),
    (re.compile(r"state occupancy", re.I), "state occupancy", "occupancy", "derived", "continuous"),
)

# Order matters: explicit physical parameters take precedence over generic nouns.
_ROLE_PARAMETER_TERMS = (
    "rate constant", "rate constants", "transition rate", "release rate", "clearance rate",
    "association rate", "dissociation rate", "binding rate", "production rate", "growth rate",
    "half-life", "half life", "initial condition", "initial value", "initial concentration",
    "sampling time", "time constant", "time-scale", "timescale", "diffusion coefficient",
    "conductance", "capacitance", "free energy", "thermodynamic", "equilibrium constant",
    "hill coefficient", "threshold", "affinity", "parameter", "elasticity", "control coefficient",
)

ROLE_BY_PHRASE = (
    (_ROLE_PARAMETER_TERMS, "parameter"),
    (("concentration", "dose", "treatment", "genotype", "mutation", "temperature", "substrate"), "independent"),
    (("activity", "level", "response", "expression", "biomarker", "flux", "occupancy", "output"), "dependent"),
    (("rate", "coefficient", "energy"), "parameter"),
    (("ratio", "fraction", "percentage", "derived", "mean", "median"), "derived"),
)

KIND_BY_PHRASE = (
    (("count", "number", "population", "copy number"), "count"),
    (("rate", "flux", "velocity", "frequency"), "rate"),
    (("state", "condition", "genotype", "mutation", "category", "label"), "categorical"),
    (("constant", "coefficient", "parameter", "threshold", "energy"), "continuous"),
)

_UNIT_PATTERN = re.compile(
    r"(?<![A-Za-z])(mM|uM|µM|nM|pM|M|mg|µg|ug|ng|kg|g|mL|µL|uL|L|s|ms|min|h|hours?|days?|%|percent|fold|AU|a\.u\.)"
)
_NUMBER_PATTERN = re.compile(r"(?<![A-Za-z0-9])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")

_MATH_CONTROL_TOKENS = {
    "ast", "cdot", "delta", "epsilon", "infty", "int", "langle", "left", "ldots",
    "log", "partial", "psi", "rangle", "right", "sigma", "sum",
}
_GRAMMAR_FRAGMENTS = {
    "after", "any", "assumption", "being", "binding", "bound", "calculate",
    "corresponding", "matrix", "computed",
    "concentrat", "distribution", "effective", "elements", "equation", "exchange", "exp",
    "fit", "fit-out", "first-order", "first-passage", "give", "implies", "intermediate",
    "limits", "master", "numerically", "out", "points", "probabilities", "reference",
    "represent", "set", "single", "solve", "specific", "strand", "taking", "target",
    "that", "usepa", "usepacka", "usepackag", "usepackage", "various",
}


def semantic_review(
    payload: dict[str, Any],
    *,
    source_path: str | None = None,
    reviewer: str = "deterministic semantic reviewer",
    mark_reviewed: bool = True,
) -> tuple[dict[str, Any], AuditReport]:
    """Return a semantically normalised copy plus the post-review audit report."""
    reviewed = _deep_copy(payload)
    variables = [item for item in reviewed.get("variables", []) if isinstance(item, dict)]
    chunks = _load_chunks(source_path) if source_path else {}
    seen_symbols: set[str] = set()
    changes: list[dict[str, Any]] = []
    retained: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []

    for index, variable in enumerate(variables, start=1):
        raw = str(variable.get("raw_name") or "")
        if _is_unusable_candidate(raw):
            removed.append({"variable_id": variable.get("variable_id"), "raw_name": raw})
            continue
        before = dict(variable)
        evidence_text = _evidence_text(variable, chunks)
        canonical = str(variable.get("canonical_name") or raw)

        lexeme = _match_lexicon(raw, canonical, evidence_text)
        if lexeme:
            canonical_name, symbol, role, kind = lexeme
            variable["canonical_name"] = canonical_name
            variable["symbol"] = symbol
            variable["role"] = role
            variable["kind"] = kind
            variable["aliases"] = _merge_aliases(variable.get("aliases"), raw if raw != canonical_name else "")
        else:
            variable["canonical_name"] = _clean_canonical(canonical or raw)
            variable["role"] = _refine_role(variable.get("role"), raw, evidence_text)
            variable["kind"] = _refine_kind(variable.get("kind"), raw)

        # Convert author-private abbreviations into conventional mathematical notation,
        # preserving the author symbol in ``author_symbol``.
        normalised = normalize_symbol(variable)
        variable["author_symbol"] = normalised["author_symbol"] if "author_symbol" not in variable else variable.get("author_symbol")
        variable["symbol_notes"] = normalised["symbol_notes"]
        variable["symbol"] = _unique_symbol(normalised["symbol"] or str(variable.get("symbol") or f"x{index}"), seen_symbols)
        seen_symbols.add(str(variable["symbol"]))
        derivative = derivative_expression(variable, str(variable["symbol"]))
        if derivative:
            variable["derivative"] = derivative
        variable["unit"] = _unit_from_text(evidence_text) or str(variable.get("unit") or _NOT_REPORTED)
        if str(variable["unit"]).lower() in {"not reported", "unknown", "none", ""}:
            variable["unit"] = _NOT_REPORTED
        variable["value_or_range"] = _value_from_text(evidence_text) or str(variable.get("value_or_range") or _NOT_REPORTED)
        variable["confidence"] = _confidence_for(variable, evidence_text)
        variable["evidence"] = _repair_evidence(variable, chunks, raw)
        variable["notes"] = _review_note(variable, before)
        retained.append(variable)

        if _changed(before, variable):
            changes.append({"variable_id": variable.get("variable_id"), "changed_fields": _changed_fields(before, variable)})

    merged_variables: list[dict[str, Any]] = []
    name_index: dict[str, dict[str, Any]] = {}
    for variable in retained:
        key = _merge_key(variable)
        existing = name_index.get(key)
        if existing is None:
            name_index[key] = variable
            merged_variables.append(variable)
            continue
        existing_aliases = _merge_aliases(existing.get("aliases"), str(variable.get("raw_name") or ""))
        existing["aliases"] = existing_aliases
        if len(str(variable.get("definition") or "")) > len(str(existing.get("definition") or "")):
            existing["definition"] = variable.get("definition")
        if str(variable.get("confidence")) == "high":
            existing["confidence"] = "high"
    # Renumber merged records, then remap every reference through the merged identities.
    representative: dict[str, str] = {}
    for variable in merged_variables:
        representative.setdefault(_merge_key(variable), str(variable.get("variable_id") or ""))
    id_map: dict[str, str] = {}
    for old in variables:
        old_id = str(old.get("variable_id") or "")
        id_map[old_id] = representative.get(_merge_key(old), old_id)
    for index, variable in enumerate(merged_variables, start=1):
        old_id = str(variable.get("variable_id") or "")
        new_id = f"V{index:03d}"
        variable["variable_id"] = new_id
        for original, target in list(id_map.items()):
            if target == old_id:
                id_map[original] = new_id
    reviewed["variables"] = merged_variables
    valid_ids = {str(item.get("variable_id")) for item in merged_variables}
    for item in reviewed.get("unresolved", []):
        if isinstance(item, dict):
            item["related_variables"] = [id_map.get(v, v) for v in item.get("related_variables", []) if id_map.get(v, v) in valid_ids]
    for relationship in reviewed.get("relationships", []):
        if isinstance(relationship, dict):
            relationship["from"] = [id_map.get(v, v) for v in relationship.get("from", []) if id_map.get(v, v) in valid_ids]
            relationship["to"] = [id_map.get(v, v) for v in relationship.get("to", []) if id_map.get(v, v) in valid_ids]
    metadata = reviewed.setdefault("extraction_metadata", {})
    metadata["review_status"] = "reviewed" if mark_reviewed else "needs_review"
    metadata["reviewer"] = reviewer
    metadata["reviewed_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    metadata["method"] = (
        "Evidence-derived scaffold plus deterministic semantic normalisation; "
        "final validation remains required."
    )
    warnings = [str(item) for item in metadata.get("warnings", [])]
    warnings = [item for item in warnings if "Scaffold output" not in item and "keyword-derived" not in item]
    warnings.append("Semantic review is deterministic and exhaustive only relative to the supplied text.")
    metadata["warnings"] = list(dict.fromkeys(warnings))
    metadata["semantic_review"] = {
        "reviewer": reviewer,
        "reviewed_at": metadata["reviewed_at"],
        "changed_variable_count": len(changes),
        "changes": changes,
        "removed_candidate_count": len(removed),
        "removed_candidates": removed,
    }

    audit = audit_extraction(reviewed, source_path=source_path)
    if audit.error_count:
        metadata["review_status"] = "needs_review"
    return reviewed, audit


def _deep_copy(value: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(value))


def _load_chunks(source_path: str | None) -> dict[str, str]:
    if not source_path:
        return {}
    from .io_utils import load_json
    source = load_json(Path(source_path))
    return {
        str(chunk.get("block_id")): str(chunk.get("text", ""))
        for chunk in source.get("chunks", [])
        if isinstance(chunk, dict) and chunk.get("block_id")
    }


def _evidence_text(variable: dict[str, Any], chunks: dict[str, str]) -> str:
    parts: list[str] = []
    for reference in variable.get("evidence", []):
        if not isinstance(reference, dict):
            continue
        parts.append(str(reference.get("quote") or ""))
        block_id = str(reference.get("block_id") or "")
        if block_id in chunks:
            parts.append(chunks[block_id])
    return " ".join(parts)[:4000]


def _match_lexicon(raw: str, canonical: str, evidence: str) -> tuple[str, str, str, str] | None:
    """Match a lexicon entry against the candidate term itself, not the whole block."""
    candidate_text = f"{raw} {canonical}".strip()
    for pattern, canonical_name, symbol, role, kind in PARAMETER_LEXICON:
        if pattern.search(candidate_text):
            return canonical_name, symbol, role, kind
    for pattern, canonical_name, symbol, role, kind in VARIABLE_LEXICON:
        if pattern.search(candidate_text):
            return canonical_name, symbol, role, kind
    if len(candidate_text) <= 24:
        for pattern, canonical_name, symbol, role, kind in VARIABLE_LEXICON:
            if pattern.search(evidence[:320]):
                return canonical_name, symbol, role, kind
    return None


def _clean_canonical(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip(" ,;:.")
    value = re.sub(r"^(the|a|an)\s+", "", value, flags=re.I)
    if len(value) > 80:
        value = value[:80].rstrip()
    return value or _NOT_REPORTED


def _refine_role(current: Any, raw: str, evidence: str) -> str:
    lowered = f"{raw} {evidence}".lower()
    for words, role in ROLE_BY_PHRASE:
        if any(word in lowered for word in words):
            return role
    current_text = str(current or "")
    if current_text in {"independent", "dependent", "controlled", "covariate", "parameter", "derived", "categorical", "latent", "other"}:
        return current_text
    return "other"


def _refine_kind(current: Any, raw: str) -> str:
    lowered = raw.lower()
    for words, kind in KIND_BY_PHRASE:
        if any(word in lowered for word in words):
            return kind
    current_text = str(current or "")
    if current_text in {"continuous", "discrete", "binary", "categorical", "ordinal", "count", "rate", "constant", "unknown"}:
        return current_text
    return "continuous"


def _unique_symbol(candidate: str, used: set[str]) -> str:
    candidate = re.sub(r"[^A-Za-z0-9_^{}\[\]()+\-/]", "", candidate) or "x"
    if candidate[0].isdigit():
        candidate = "x" + candidate
    if candidate not in used:
        return candidate
    base = re.sub(r"\d+$", "", candidate) or "x"
    suffix = 2
    while f"{base}_{suffix}" in used:
        suffix += 1
    return f"{base}_{suffix}"


def _unit_from_text(text: str) -> str | None:
    match = _UNIT_PATTERN.search(text)
    return match.group(1) if match else None


def _value_from_text(text: str) -> str | None:
    match = _NUMBER_PATTERN.search(text)
    return match.group(0) if match else None


def _confidence_for(variable: dict[str, Any], evidence: str) -> str:
    """Raise confidence only when the candidate itself is quantitatively anchored."""
    raw = str(variable.get("raw_name") or "").strip()
    if not raw or not evidence:
        return "low"
    position = evidence.lower().find(raw.lower())
    window = evidence[max(0, position - 80): position + len(raw) + 80] if position >= 0 else raw
    if _NUMBER_PATTERN.search(window) or _unit_from_text(window):
        return "high"
    if len(raw) >= 3 and not any(char.isdigit() for char in raw):
        return "medium"
    return "low"


def _review_note(variable: dict[str, Any], before: dict[str, Any]) -> str:
    notes = str(variable.get("notes") or "").strip()
    notes = notes.replace("Automatically proposed candidate; requires semantic confirmation.", "").strip()
    notes = notes.replace("Evidence-derived candidate; requires semantic review.", "").strip()
    changed = _changed_fields(before, variable)
    detail = f"Semantic review normalised: {', '.join(changed)}." if changed else "Semantic review retained this record."
    return f"{notes} {detail}".strip()


def _merge_aliases(value: Any, extra: str) -> list[str]:
    aliases = [str(item) for item in value] if isinstance(value, list) else []
    if extra and extra not in aliases:
        aliases.append(extra)
    return aliases


def _changed(before: dict[str, Any], after: dict[str, Any]) -> bool:
    return bool(_changed_fields(before, after))


def _changed_fields(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    fields = []
    for key in ("canonical_name", "symbol", "author_symbol", "symbol_notes", "derivative", "role", "kind", "unit", "value_or_range", "confidence", "notes", "evidence"):
        if before.get(key) != after.get(key):
            fields.append(key)
    return fields


def _is_unusable_candidate(raw: str) -> bool:
    lowered = raw.strip().lower()
    if not lowered:
        return True
    if lowered in _MATH_CONTROL_TOKENS or lowered in _GRAMMAR_FRAGMENTS:
        return True
    if lowered.startswith(("begin", "end", "rm{", "bf{", "textbf", "usepackage", "documentclass", "mathop", "frac", "sqrt", "usep")):
        return True
    if "{{" in raw or "}}" in raw or raw.count("{") != raw.count("}"):
        return True
    if raw.count("}") >= 3 or raw.count("{") >= 3:
        return True
    if re.search(r"(?:}_{|}\^|\^\{|\\[A-Za-z]+)", raw):
        return True
    if re.search(r"[\]\[()]", raw) and not re.search(r"\b(?:concentration|rate|flux|level|activity|occupancy|probability)\b", raw, re.I):
        return True
    if len(raw) > 32 and not _unit_from_text(raw):
        return True
    if re.fullmatch(r"[A-Za-z]{1,4}\d*[fs]?", raw) and lowered not in {"kcat", "km", "vmax", "ic50", "kd", "kon", "koff"}:
        return True
    return False

def _repair_evidence(variable: dict[str, Any], chunks: dict[str, str], raw: str) -> list[dict[str, Any]]:
    """Rebuild evidence as a contiguous quote that actually contains the candidate."""
    repaired: list[dict[str, Any]] = []
    for reference in variable.get("evidence", []):
        if not isinstance(reference, dict):
            continue
        block_id = str(reference.get("block_id") or "")
        source = chunks.get(block_id, "")
        quote = str(reference.get("quote") or "")
        if source:
            position = source.lower().find(raw.lower())
            if position >= 0:
                start = max(0, position - 240)
                end = min(len(source), position + len(raw) + 240)
                quote = source[start:end].strip()
        repaired.append(
            {
                "block_id": block_id,
                "quote": quote,
                "page": reference.get("page"),
                "section": reference.get("section", ""),
            }
        )
    return repaired


def _merge_key(variable: dict[str, Any]) -> str:
    value = str(variable.get("canonical_name") or variable.get("raw_name") or "").strip().lower()
    value = re.sub(r"\b(?:rate|rates|constant|constants|level|levels|value|values)\b", "", value)
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value or str(variable.get("raw_name") or "").strip().lower()


