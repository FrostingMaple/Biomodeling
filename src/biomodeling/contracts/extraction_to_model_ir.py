"""Convert Bio Variable Extractor output into biomodel-agent Model IR.

The unified extraction format keeps project A's evidence-rich payload and may
optionally include a complete B-native ``model_ir`` object.  When ``model_ir``
is absent, this module performs a conservative structural mapping and marks the
result as a draft instead of inventing equations or numeric values.
"""

from __future__ import annotations

import copy
import hashlib
import re
from pathlib import Path
from typing import Any, Iterable

from ..modeling.model_ir import validate_model_ir


class ExtractionConversionError(ValueError):
    """Raised when a strict conversion cannot produce a runnable Model IR."""


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _safe_identifier(value: Any, fallback: str) -> str:
    text = _text(value, fallback)
    text = re.sub(r"[^A-Za-z0-9_]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    if not text:
        text = fallback
    if not text[0].isalpha():
        text = f"v_{text}"
    return text


def _unique_name(candidate: str, used: set[str]) -> str:
    base = candidate
    index = 2
    while candidate in used:
        candidate = f"{base}_{index}"
        index += 1
    used.add(candidate)
    return candidate


def _parse_single_number(value: Any) -> float | None:
    """Return a number only when the text contains exactly one numeric value."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or re.search(r"\b(not reported|unknown|n/?a)\b", text, re.I):
        return None
    numbers = re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", text)
    if len(numbers) != 1:
        return None
    try:
        return float(numbers[0])
    except ValueError:
        return None


def _normalize_model_type(payload: dict[str, Any], explicit: Any = None) -> str:
    raw = _text(explicit or _as_dict(payload.get("study_profile")).get("model_type"))
    lowered = raw.lower()
    if re.search(r"\bpde\b|partial differential|reaction[- ]diffusion|spatiotemporal", lowered):
        return "PDE"
    if re.search(r"\bode\b|ordinary differential|differential equation|dynamic model", lowered):
        return "ODE"
    if re.search(r"stochastic|random|markov|master equation", lowered):
        return "stochastic"
    return "unknown"


def _source_text(payload: dict[str, Any]) -> str:
    document = _as_dict(payload.get("document"))
    title = _text(document.get("title"), "Untitled biological model")
    doi = _text(document.get("doi"))
    source_name = _text(document.get("source_name") or document.get("source_path"))
    parts = [title]
    if doi:
        parts.append(f"DOI: {doi}")
    elif source_name:
        parts.append(source_name)
    return " | ".join(parts)


def _confidence(payload: dict[str, Any], explicit: Any = None) -> str:
    value = _text(explicit).lower()
    if value in {"high", "medium", "low"}:
        return value
    values = [
        _text(item.get("confidence")).lower()
        for item in _as_list(payload.get("variables"))
        if isinstance(item, dict)
    ]
    if values and all(item == "high" for item in values):
        return "high"
    if any(item == "low" for item in values):
        return "low"
    return "medium"


def _evidence_index(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    question = _as_dict(payload.get("research_question"))
    for evidence in _as_list(question.get("evidence")):
        if isinstance(evidence, dict):
            records.append({"owner_kind": "research_question", "owner_id": None, **evidence})
    for variable in _as_list(payload.get("variables")):
        if not isinstance(variable, dict):
            continue
        owner_id = _text(variable.get("variable_id"))
        for evidence in _as_list(variable.get("evidence")):
            if isinstance(evidence, dict):
                records.append({"owner_kind": "variable", "owner_id": owner_id, **evidence})
    for relationship in _as_list(payload.get("relationships")):
        if not isinstance(relationship, dict):
            continue
        owner_id = _text(relationship.get("relationship_id"))
        for evidence in _as_list(relationship.get("evidence")):
            if isinstance(evidence, dict):
                records.append({"owner_kind": "relationship", "owner_id": owner_id, **evidence})
    for item in _as_list(payload.get("unresolved")):
        if isinstance(item, dict):
            for evidence in _as_list(item.get("evidence")):
                if isinstance(evidence, dict):
                    records.append({"owner_kind": "unresolved", "owner_id": None, **evidence})
    return records


def _parse_time_domain(payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    profile = _as_dict(payload.get("study_profile"))
    text = _text(profile.get("time_scale"))
    patterns = [
        r"(?:from|between)?\s*([-+]?\d+(?:\.\d+)?)\s*(?:to|until|through|[-–])\s*([-+]?\d+(?:\.\d+)?)",
        r"([-+]?\d+(?:\.\d+)?)\s*(?:to|until|through|[-–])\s*([-+]?\d+(?:\.\d+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            start, end = float(match.group(1)), float(match.group(2))
            if end > start:
                return {"t_start": start, "t_end": end, "source": text}, True
    return {"t_start": 0.0, "t_end": 1.0, "source": "adapter-default"}, False


def _state_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    variables = [item for item in _as_list(payload.get("variables")) if isinstance(item, dict)]
    target_ids: list[str] = []
    for relationship in _as_list(payload.get("relationships")):
        if not isinstance(relationship, dict) or relationship.get("type") != "equation":
            continue
        target_ids.extend(_text(value) for value in _as_list(relationship.get("to")))
    target_set = {item for item in target_ids if item}
    if target_set:
        selected = [
            item for item in variables
            if _text(item.get("variable_id")) in target_set
            and _text(item.get("role")) not in {"parameter"}
        ]
        if selected:
            return selected
    for roles in ({"dependent", "derived", "latent"}, {"independent", "controlled", "covariate", "categorical", "other"}):
        selected = [item for item in variables if _text(item.get("role")) in roles]
        if selected:
            return selected
    return [item for item in variables if _text(item.get("role")) != "parameter"]


def _parameter_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item for item in _as_list(payload.get("variables"))
        if isinstance(item, dict) and _text(item.get("role")) in {"parameter", "constant"}
    ]


def _map_variables(
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, str], list[dict[str, Any]], dict[str, str], list[str]]:
    warnings: list[str] = []
    used: set[str] = set()
    variables: list[dict[str, Any]] = []
    variable_names: dict[str, str] = {}
    for item in _state_candidates(payload):
        variable_id = _text(item.get("variable_id"))
        name = _unique_name(
            _safe_identifier(item.get("symbol") or item.get("canonical_name") or item.get("raw_name"), "state"),
            used,
        )
        if variable_id:
            variable_names[variable_id] = name
        variables.append({
            "name": name,
            "description": _text(item.get("definition") or item.get("canonical_name") or item.get("raw_name"), name),
            "unit": _text(item.get("unit"), "unknown"),
            "role": _text(item.get("role")),
            "variable_id": variable_id or None,
            "canonical_name": _text(item.get("canonical_name")) or None,
            "confidence": _text(item.get("confidence")) or None,
            "evidence_refs": [
                _text(ev.get("block_id"))
                for ev in _as_list(item.get("evidence"))
                if isinstance(ev, dict) and _text(ev.get("block_id"))
            ],
        })
    parameters: list[dict[str, Any]] = []
    parameter_names: dict[str, str] = {}
    for item in _parameter_candidates(payload):
        variable_id = _text(item.get("variable_id"))
        name = _unique_name(
            _safe_identifier(item.get("symbol") or item.get("canonical_name") or item.get("raw_name"), "parameter"),
            used,
        )
        if variable_id:
            parameter_names[variable_id] = name
        value = _parse_single_number(item.get("value_or_range"))
        if value is None:
            warnings.append(f"Parameter {variable_id or name} has no single numeric value.")
        parameters.append({
            "name": name,
            "description": _text(item.get("definition") or item.get("canonical_name") or item.get("raw_name"), name),
            "value_known": value is not None,
            "value": value,
            "unit": _text(item.get("unit"), "unknown"),
            "variable_id": variable_id or None,
            "canonical_name": _text(item.get("canonical_name")) or None,
            "evidence_refs": [
                _text(ev.get("block_id"))
                for ev in _as_list(item.get("evidence"))
                if isinstance(ev, dict) and _text(ev.get("block_id"))
            ],
        })
    if not variables:
        warnings.append("No state-variable candidates were found in the extraction.")
    return variables, variable_names, parameters, parameter_names, warnings


def _derive_equations(
    payload: dict[str, Any], variable_names: dict[str, str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    equations: list[dict[str, Any]] = []
    algebraic: list[dict[str, Any]] = []
    warnings: list[str] = []
    derivative_pattern = re.compile(
        r"(?:d\s*[\^2\s]*\s*(?:\[\s*)?([A-Za-z_]\w*)(?:\s*\])?\s*/\s*d\s*[tx]\s*\^?\s*2?)|(?:d2\s*([A-Za-z_]\w*)\s*/\s*dx2)",
        re.I,
    )
    for relationship in _as_list(payload.get("relationships")):
        if not isinstance(relationship, dict) or relationship.get("type") != "equation":
            continue
        relationship_id = _text(relationship.get("relationship_id"))
        expression = _text(relationship.get("expression"))
        if not expression:
            continue
        left, right = (expression.split("=", 1) + [""])[:2] if "=" in expression else ("", expression)
        match = derivative_pattern.search(left)
        target_id = ""
        if match:
            derivative_name = match.group(1) or match.group(2) or ""
            for candidate_id, variable_name in variable_names.items():
                if derivative_name == variable_name:
                    target_id = candidate_id
                    break
        if not target_id:
            targets = [_text(value) for value in _as_list(relationship.get("to")) if _text(value)]
            if len(targets) == 1 and targets[0] in variable_names:
                target_id = targets[0]
        dynamic = bool(match)
        if target_id and dynamic:
            equations.append({
                "variable": variable_names[target_id],
                "expression": right.strip() if left else expression,
                "relationship_id": relationship_id or None,
            })
            warnings.append(
                f"Relationship {relationship_id or '(unnamed)'} was mapped as a differential equation; verify the derivative target."
            )
        else:
            algebraic.append({
                "relationship_id": relationship_id or None,
                "type": relationship.get("type"),
                "from": _as_list(relationship.get("from")),
                "to": _as_list(relationship.get("to")),
                "expression": expression,
                "reason": "No explicit derivative notation; retained as an algebraic relationship.",
            })
    return equations, algebraic, warnings


def _initial_conditions(
    payload: dict[str, Any], variables: list[dict[str, Any]], warnings: list[str]
) -> list[dict[str, Any]]:
    source = {
        _text(item.get("variable_id")): item
        for item in _as_list(payload.get("variables"))
        if isinstance(item, dict) and _text(item.get("variable_id"))
    }
    result: list[dict[str, Any]] = []
    for variable in variables:
        item = source.get(_text(variable.get("variable_id")), {})
        value = _parse_single_number(item.get("value_or_range"))
        if value is None:
            warnings.append(f"Initial condition for {variable['name']} is not a single numeric value.")
        result.append({
            "variable": variable["name"],
            "value_known": value is not None,
            **({"value": value} if value is not None else {}),
            "source_text": _text(item.get("value_or_range")) or None,
        })
    return result


def _missing_information(payload: dict[str, Any], warnings: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for item in _as_list(payload.get("unresolved")):
        if isinstance(item, dict):
            issue = _text(item.get("issue"))
            action = _text(item.get("recommended_action"))
            if issue:
                missing.append(f"{issue} Recommended action: {action}" if action else issue)
    for warning in warnings:
        if warning not in missing:
            missing.append(warning)
    return missing


def _merge_seed(payload: dict[str, Any], auto: dict[str, Any]) -> dict[str, Any]:
    seed = _as_dict(payload.get("model_ir_seed"))
    if not seed:
        return auto
    merged = copy.deepcopy(auto)
    for key, value in seed.items():
        merged[key] = copy.deepcopy(value)
    return merged


def _direct_model_ir(payload: dict[str, Any]) -> dict[str, Any] | None:
    direct = payload.get("model_ir")
    return copy.deepcopy(direct) if isinstance(direct, dict) and direct else None


def extraction_to_model_ir(
    payload: dict[str, Any],
    *,
    extraction_path: str | Path | None = None,
    mode: str | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    """Return a B-compatible Model IR with provenance and conversion metadata."""
    if not isinstance(payload, dict):
        raise ExtractionConversionError("Extraction payload must be a JSON object.")

    direct = _direct_model_ir(payload)
    if direct is not None:
        model = direct
        warnings: list[str] = []
        algebraic: list[dict[str, Any]] = []
        if mode:
            model.setdefault("origin", {})["mode"] = mode
    else:
        variables, variable_names, parameters, _parameter_names, warnings = _map_variables(payload)
        equations, algebraic, equation_warnings = _derive_equations(payload, variable_names)
        warnings.extend(equation_warnings)
        initial_conditions = _initial_conditions(payload, variables, warnings)
        domain, domain_known = _parse_time_domain(payload)
        if not domain_known:
            warnings.append("Time domain was not explicit; adapter used a draft placeholder [0, 1].")
        model = {
            "model_name": _text(_as_dict(payload.get("document")).get("title"), "Converted biological model"),
            "model_type": _normalize_model_type(payload),
            "description": _text(
                _as_dict(payload.get("research_question")).get("question")
                or _as_dict(payload.get("study_profile")).get("model_type"),
                "Model converted from an evidence-grounded variable extraction.",
            ),
            "variables": variables,
            "parameters": parameters,
            "equations": equations,
            "domain": domain,
            "initial_conditions": initial_conditions,
            "boundary_conditions": [],
            "origin": {
                "mode": mode or "reproduce",
                "source_text": _source_text(payload),
                "confidence": _confidence(payload),
                "assumptions": [],
            },
            "missing_information": [],
        }
        model = _merge_seed(payload, model)
        model.setdefault("origin", {})
        if mode:
            model["origin"]["mode"] = mode

    if mode and _as_dict(model.get("origin")).get("mode") != mode:
        model["origin"]["mode"] = mode

    model.setdefault("boundary_conditions", [])
    model.setdefault("missing_information", [])
    model.setdefault("origin", {})
    model.setdefault("origin", {})["source_extraction"] = str(extraction_path) if extraction_path else None
    if extraction_path:
        path = Path(extraction_path)
        if path.is_file():
            model["origin"]["source_extraction_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()

    evidence = _evidence_index(payload)
    if evidence:
        model["evidence"] = evidence

    missing = _missing_information(payload, warnings)
    existing_missing = [
        _text(item) for item in _as_list(model.get("missing_information")) if _text(item)
    ]
    for item in existing_missing:
        if item not in missing:
            missing.append(item)
    required_missing = []
    if not _as_list(model.get("equations")):
        required_missing.append("No runnable differential equations were supplied.")
    elif len(_as_list(model.get("equations"))) < len(_as_list(model.get("variables"))):
        required_missing.append("Equations do not cover every Model IR state variable.")
    if any(not bool(item.get("value_known")) for item in _as_list(model.get("parameters")) if isinstance(item, dict)):
        required_missing.append("At least one parameter lacks a numeric value.")
    if any(not bool(item.get("value_known")) for item in _as_list(model.get("initial_conditions")) if isinstance(item, dict)):
        required_missing.append("At least one initial condition lacks a numeric value.")
    for item in required_missing:
        if item not in missing:
            missing.append(item)
    model["missing_information"] = missing

    validation = validate_model_ir(model, for_simulation=True)
    model_ready = bool(validation["valid"] and not required_missing)
    conversion = {
        "source_schema": "bio_variable_extractor/extraction.schema.json",
        "target_schema": "biomodeling.modeling.model_ir",
        "source_extraction": str(extraction_path) if extraction_path else None,
        "model_ready": model_ready,
        "warnings": list(dict.fromkeys(warnings)),
        "algebraic_relationships": algebraic,
        "validation_for_simulation": validation,
    }
    if model_ready:
        conversion["validation_for_simulation"] = {"valid": True, "errors": [], "warnings": validation["warnings"]}
    model["conversion"] = conversion

    if strict and not model_ready:
        details = "; ".join(validation["errors"] + conversion["warnings"])
        raise ExtractionConversionError(f"Extraction is not simulation-ready. {details}")
    return model


def load_and_convert(
    extraction_path: str | Path,
    *,
    mode: str | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    import json

    path = Path(extraction_path)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return extraction_to_model_ir(payload, extraction_path=path, mode=mode, strict=strict)
