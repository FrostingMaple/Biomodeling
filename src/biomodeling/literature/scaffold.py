"""Create deterministic extraction scaffolds from prepared source evidence."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .extraction import EXTRACTION_SCHEMA_VERSION
from .lexicon import match_models, match_parameters, match_relations

_VARIABLE_CUES = re.compile(
    r"\b("
    r"concentration|coefficient|ratio|abundance|temperature|dose|volume|"
    r"velocity|affinity|probability|sensitivity|specificity|precision|"
    r"phosphorylation|dephosphorylation|flux|yield|capacity|threshold|amplitude|frequency|"
    r"diameter|length|mass|biomarker|steady[- ]state|half[- ]life|"
    r"dissociation constant|association constant|transition rate|inhibition|activation|mutation|genotype|"
    r"rate constant|rate|growth rate|decay rate|production rate|clearance|release rate|"
    r"degradation|synthesis|transport|diffusion|permeability|conductance|"
    r"equilibrium constant|binding constant|hill coefficient|michaelis|"
    r"half[- ]saturation|carrying capacity|lag time|doubling time|"
    r"initial condition|boundary condition|parameter|kinetic parameter|"
    r"initial value|timescale|time[- ]scale|volume|surface area|"
    r"population size|cell number|copy number|expression level|"
    r"fold change|relative expression|optical density|biomass|"
    r"substrate|product|inhibitor|activator|repressor|enzyme|"
    r"state occupancy|occupancy|pseudotime|free energy|sampling time|"
    r"association rate|dissociation rate|binding rate|turnover number"
    r")\w*",
    re.IGNORECASE,
)
_GENERIC_CANDIDATES = {
    "activity",
    "activation",
    "adjusted",
    "assumes",
    "condition",
    "constant",
    "count",
    "error",
    "fraction",
    "input",
    "kinetic",
    "level",
    "model",
    "number",
    "output",
    "parameter",
    "percentage",
    "population",
    "rate",
    "response",
    "state",
    "time",
    "weight",
    "measurement",
    "value",
    "data",
    "method",
    "rationalize",
    "transitioning",
}
_LATEX_FRAGMENTS = {
    "aligned", "array", "ast", "begin", "bf", "cdot", "delta", "elements",
    "end", "epsilon", "frac", "infty", "int", "langle", "ldots", "left",
    "limits", "log", "mathrm", "partial", "psi", "rangle", "right", "rm",
    "sqrt", "sum", "text", "usepackage", "usepacka", "usepackag",
}
_UNIT_WORDS = {
    "au", "a.u.", "day", "days", "fold", "g", "h", "hour", "hours", "kg",
    "l", "m", "mg", "min", "ml", "mm", "ms", "mM", "nM", "pM", "s", "second",
    "seconds", "uM", "µM", "percent", "percentage",
}
_STOP_CANDIDATES = {
    "all", "and", "are", "as", "at", "be", "by", "can", "composed", "defined",
    "denote", "denotes", "each", "for", "from", "function", "given", "happ",
    "here", "in", "is", "it", "letting", "linearly", "may", "of", "on", "or",
    "other", "over", "rows", "run", "runs", "starting", "step", "step0",
    "takes", "the", "these", "this", "to", "using", "was", "we", "were",
    "where", "with", "yielding",
}
_NOT_REPORTED = "Not reported"
_EQUATION_PATTERN = re.compile(
    r"(?P<left>[A-Za-z][A-Za-z0-9_^{}\[\]()\-]{0,30})\s*=\s*"
    r"(?P<right>[^.;\n]{1,160})",
)
_MATH_TOKEN_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])([A-Za-z](?:[A-Za-z0-9_^{}\[\]()+\-]*)?|[A-Za-z]_\{[^}]+\})(?![A-Za-z0-9_])"
)
_EQUATION_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "of", "on", "or", "the", "to", "was", "were", "where", "with",
}
_EXPRESSION_STOPWORDS = {"all", "each", "for", "given", "over", "runs", "the"}

# Author-facing parameter names and symbols, ordered before generic phrase rules.
_INDEXED_SYMBOL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])([A-Za-z][A-Za-z]{0,5}(?:_?\{?\d+\}?))(?!\d)"
)


_PARAMETER_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bk[\s_-]*on\b", "k_on"),
    (r"\bk[\s_-]*off\b", "k_off"),
    (r"\bk[\s_-]*cat\b", "kcat"),
    (r"\bK\s*[_ -]?m\b", "Km"),
    (r"\bV\s*[_ -]?max\b", "Vmax"),
    (r"\bIC\s*50\b", "IC50"),
    (r"\bEC\s*50\b", "EC50"),
    (r"\bK\s*[_ -]?d\b", "Kd"),
    (r"\bAUROC\b", "AUROC"),
    (r"\bAUPRC\b", "AUPRC"),
)


def scaffold_from_source(
    source_path: Path,
    *,
    extractor: str = "bio_variable_extractor scaffold",
    max_variables: int = 0,
) -> dict[str, Any]:
    source = json.loads(source_path.read_text(encoding="utf-8"))
    chunks = [chunk for chunk in source.get("chunks", []) if isinstance(chunk, dict)]
    metadata = source.get("metadata", {}) if isinstance(source.get("metadata"), dict) else {}
    abstract = next((chunk for chunk in chunks if chunk.get("section") == "abstract"), None)
    question_chunk = abstract or (chunks[0] if chunks else None)

    question = _question_from_metadata(metadata, question_chunk)
    study_profile = _study_profile(chunks)
    equation_relationships = _equation_relationships(chunks)
    variables, candidate_stats = _candidate_variables(
        chunks,
        max_variables=max_variables,
        equation_relationships=equation_relationships,
    )
    lexicon_relationships = _lexicon_relationships(chunks, variables)
    relationships = _relationships(variables, equation_relationships, lexicon_relationships)
    unresolved = _unresolved(variables, relationships)

    return {
        "schema_version": EXTRACTION_SCHEMA_VERSION,
        "document": {
            "title": metadata.get("title") or source_path.stem,
            "authors": ", ".join(metadata.get("authors", []))
            if isinstance(metadata.get("authors"), list)
            else str(metadata.get("authors", _NOT_REPORTED)),
            "year": metadata.get("year") or _NOT_REPORTED,
            "source_path": source.get("source_path", str(source_path)),
            "source_name": source.get("source_name", source_path.name),
            "language": metadata.get("language", "en") or "en",
            "doi": metadata.get("doi") or None,
            "pmcid": metadata.get("pmcid") or None,
        },
        "research_question": {
            "question": question,
            "scope": _scope_from_source(chunks),
            "confidence": "low",
            "evidence": [_evidence(question_chunk, question)] if question_chunk else [],
        },
        "study_profile": study_profile,
        "variables": variables,
        "relationships": relationships,
        "unresolved": unresolved,
        "extraction_metadata": {
            "extracted_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "extractor": extractor,
            "coverage": (
                f"Prepared text only: {source.get('section_count', 0)} section(s) and "
                f"{source.get('chunk_count', 0)} evidence block(s)."
            ),
            "method": "Deterministic scaffold from prepared text; every field requires semantic review.",
            "review_status": "scaffold",
            "reviewer": "",
            "reviewed_at": "",
            "discovered_candidate_count": candidate_stats["discovered"],
            "retained_candidate_count": candidate_stats["retained"],
            "truncated_candidate_count": candidate_stats["truncated"],
            "warnings": [
                "Scaffold output is not a completed semantic review.",
                (f'{candidate_stats["truncated"]} candidate(s) were dropped by --max-variables; rerun with 0 for no truncation.' if candidate_stats["truncated"] else "No candidates were dropped by truncation."),
                "Variable candidates are evidence-derived and may include false positives or omit implicit variables.",
                "Relationship records are extracted only from textual equalities or assigned vocabulary; no associations are invented.",
            ],
        },
    }


def _question_from_metadata(metadata: dict[str, Any], chunk: dict[str, Any] | None) -> str:
    if chunk:
        text = str(chunk.get("text", "")).strip()
        if text:
            return _first_sentence(text)
    title = str(metadata.get("title") or "").strip()
    if title:
        return title
    return _NOT_REPORTED


def _scope_from_source(chunks: list[dict[str, Any]]) -> str:
    sections = []
    for chunk in chunks:
        section = str(chunk.get("section", ""))
        if section and section not in sections:
            sections.append(section)
    return "Sections supplied: " + ", ".join(sections[:12]) if sections else _NOT_REPORTED


def _study_profile(chunks: list[dict[str, Any]]) -> dict[str, str]:
    all_text = " ".join(str(chunk.get("text", "")) for chunk in chunks)
    organisms = []
    for pattern in (
        r"\b(?:E\.?\s*coli|Escherichia coli)\b",
        r"\b(?:Homo sapiens|human|human hepatocytes)\b",
        r"\b(?:Saccharomyces cerevisiae|yeast)\b",
        r"\b(?:Arabidopsis thaliana|Arabidopsis)\b",
        r"\b(?:Zea mays|maize)\b",
        r"\b(?:Mus musculus|mouse|mice)\b",
        r"\b(?:HEK293|HeLa|K-12)\b",
    ):
        match = re.search(pattern, all_text, re.IGNORECASE)
        if match:
            organisms.append(match.group(0))
    return {
        "organism_or_system": ", ".join(dict.fromkeys(organisms)) or _NOT_REPORTED,
        "study_design": _first_matching_sentence(all_text, r"\b(experiment|simulation|model|dataset|review)\w*\b"),
        "model_type": _first_matching_sentence(all_text, r"\b(kinetic model|mass action model|markov|boolean|mathematical model|ordinary differential)\b"),
        "sample_scale": _first_matching_sentence(all_text, r"\b(samples?|datasets?|replicates?|cells?|simulations?|parameter sets?)\b"),
        "time_scale": _first_matching_sentence(all_text, r"\b(seconds?|minutes?|hours?|days?|time course|time-scale|steady[- ]state)\b"),
    }


def _candidate_variables(
    chunks: list[dict[str, Any]],
    *,
    max_variables: int,
    equation_relationships: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Collect evidence-backed candidates and report truncation explicitly."""
    merged: dict[str, dict[str, Any]] = {}

    def add(raw: str, chunk: dict[str, Any], quote: str, priority: int) -> None:
        raw = _normalise_raw(raw)
        if not raw or not _valid_candidate(raw):
            return
        key = raw.lower()
        previous = merged.get(key)
        if previous is not None:
            # Prefer the shortest author term and the richest evidence quote.
            if len(raw) < len(str(previous["raw_name"])):
                previous["raw_name"] = raw
            if len(quote) > len(str(previous.get("quote", ""))):
                previous["quote"] = quote
            previous["priority"] = min(int(previous.get("priority", 99)), priority)
            return
        merged[key] = {
            "raw_name": raw,
            "chunk": chunk,
            "quote": quote,
            "priority": priority,
        }

    # 0. Community lexicon parameters, matched on their canonical symbols and aliases.
    for chunk in chunks:
        text = str(chunk.get("text", ""))
        for entry in match_parameters(text, limit=60):
            # Record the concrete author-facing spelling found in this chunk, not only the first symbol.
            candidates = list(entry.get("symbols", [])) + list(entry.get("aliases", []))
            for candidate in candidates:
                candidate = str(candidate).strip()
                if len(candidate) < 2:
                    continue
                flexible = re.escape(candidate).replace(r'\_', r'[_\s-]?').replace(r'\ ', r'[_\s-]?')
                match = re.search(r'(?<![A-Za-z0-9])' + flexible + r'(?![A-Za-z0-9])', text, re.IGNORECASE)
                if match:
                    add(candidate, chunk, _sentence_containing(text, match.start()), -1)

    # 1. Explicit parameter symbols and common quantitative names.
    for chunk in chunks:
        text = str(chunk.get("text", ""))
        for match in _INDEXED_SYMBOL_PATTERN.finditer(text):
            raw = match.group(1).replace("{", "").replace("}", "")
            if not raw or raw.lower() in _GENERIC_CANDIDATES:
                continue
            add(raw, chunk, _sentence_containing(text, match.start()), 1)
        for pattern, symbol in _PARAMETER_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                add(symbol, chunk, _sentence_containing(text, match.start()), 1)
        for raw, quote in _definitional_candidates(text):
            add(raw, chunk, quote, 2)

    # 2. Equation symbols, retaining the author's symbol spelling.
    for symbol, evidence in _equation_symbol_evidence(chunks, equation_relationships or []):
        add(symbol, evidence["chunk"], evidence["quote"], 3)

    # 3. Quantitative phrases, but only nouns/phrases in variable contexts.
    for chunk in chunks:
        text = str(chunk.get("text", ""))
        for match in _VARIABLE_CUES.finditer(text):
            raw = match.group(0).strip()
            add(raw, chunk, _sentence_containing(text, match.start()), 4)

    ordered = sorted(
        merged.values(),
        key=lambda item: (int(item["priority"]), -len(item["quote"]), str(item["raw_name"]).lower()),
    )
    discovered_count = len(ordered)
    truncated_count = 0
    if max_variables > 0 and discovered_count > max_variables:
        truncated_count = discovered_count - max_variables
        # Protect quantitative parameter candidates from displacement by prose fragments.
        protected = [item for item in ordered if _is_protected_parameter(str(item.get("raw_name", "")))]
        unprotected = [item for item in ordered if item not in protected]
        reserved = protected[:max_variables]
        remaining = max_variables - len(reserved)
        ordered = reserved + (unprotected[:remaining] if remaining > 0 else [])

    variables: list[dict[str, Any]] = []
    used_symbols: set[str] = set()
    for index, item in enumerate(ordered, start=1):
        raw = str(item["raw_name"])
        chunk = item["chunk"]
        quote = str(item["quote"])
        canonical = _canonical_name(raw)
        symbol = _author_symbol(raw) or _unique_symbol(_symbol(canonical, index), used_symbols)
        used_symbols.add(symbol)
        variables.append(
            {
                "variable_id": f"V{index:03d}",
                "raw_name": raw,
                "canonical_name": canonical,
                "symbol": symbol,
                "aliases": [],
                "role": _role_for(raw, quote),
                "kind": _kind_for(raw),
                "definition": _definition(quote, canonical),
                "unit": _unit_near(quote),
                "value_or_range": _value_near(quote),
                "relationship": _relationship_note(raw, equation_relationships or []),
                "evidence": [_evidence(chunk, quote)],
                "confidence": "low",
                "notes": "Evidence-derived candidate; requires semantic review.",
            }
        )
    return variables, {
        "discovered": discovered_count,
        "retained": len(variables),
        "truncated": truncated_count,
    }


def _definitional_candidates(text: str) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    pattern = re.compile(
        r"\b(?:the\s+|a\s+|an\s+)?(?P<name>[A-Za-z][A-Za-z0-9\- ]{2,60}?)\s+"
        r"(?:is|are|was|were|denotes|represents|refers to|means)\s+"
        r"(?:defined|calculated|measured|estimated|modeled|modelled|given|set)"
    )
    for match in pattern.finditer(text):
        name = re.sub(r"\s+", " ", match.group("name")).strip(" ,;:.")
        if name and len(name.split()) <= 6:
            candidates.append((name, _sentence_containing(text, match.start())))
    return candidates


def _normalise_raw(raw: str) -> str:
    raw = re.sub(r"\s+", " ", raw).strip(" ,;:.")
    raw = raw.strip("()[]")
    return raw


def _valid_candidate(raw: str) -> bool:
    lowered = raw.lower()
    if len(raw) < 2 or not re.search(r"[A-Za-z]", raw):
        return False
    if lowered in _UNIT_WORDS or lowered in _STOP_CANDIDATES or lowered in _GENERIC_CANDIDATES:
        return False
    if lowered.rstrip("s") in _GENERIC_CANDIDATES:
        return False
    if lowered in _LATEX_FRAGMENTS or any(lowered.startswith(prefix) for prefix in ("begin{", "end{", "rm{", "bf{", "array", "usep")):
        return False
    if lowered in {"any", "assumption", "being", "binding", "bound", "calculate", "computed", "distribution", "effective", "equation", "exchange", "exp", "fit", "give", "implies", "intermediate", "master", "numerically", "points", "probabilities", "reference", "represent", "set", "single", "solve", "specific", "strand", "taking", "target", "that", "various", "concentrat"}:
        return False
    if "{{" in raw or "}}" in raw or raw.count("{") != raw.count("}"):
        return False
    if raw.startswith(("begin{", "end{", "rm{", "bf{")):
        return False
    if re.search(r"(?:}_{|}\^|\^\{|\\[A-Za-z]+)", raw):
        return False
    if re.search(r"[\]\[()]", raw) and not re.search(r"\b(?:concentration|rate|flux|level|activity|occupancy|probability)\b", raw, re.I):
        return False
    if raw.startswith(("the ", "once ", "when ", "where ", "which ", "that ", "these ", "this ")):
        return False
    if lowered in {"any", "assumption", "being", "binding", "calculate", "computed", "distribution", "effective", "equation", "exchange", "exp", "fit", "give", "implies", "intermediate", "master", "numerically", "points", "probabilities", "reference", "represent", "set", "single", "solve", "specific", "strand", "taking", "target", "that", "usep", "usepa", "usepacka", "various"}:
        return False
    if raw.endswith((")", "]", "}")):
        return False
    if re.search(r"(?:ized|izing|ised|ising|with)$", lowered):
        return False
    if lowered.endswith("s") and lowered[:-1] in _GENERIC_CANDIDATES:
        return False
    if len(raw.split()) > 6:
        return False
    if re.fullmatch(r"[A-Za-z]", raw):
        return False
    return True

def _author_symbol(raw: str) -> str | None:
    compact = raw.strip()
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_^{}\[\]()+\-/]*", compact):
        if len(compact) <= 12 and (
            any(char.isdigit() for char in compact)
            or "_" in compact
            or compact.isupper()
            or compact in {"k", "t", "x", "y", "z", "r", "v", "V", "K", "N", "C", "P", "S", "T"}
        ):
            return compact
    for pattern, symbol in _PARAMETER_PATTERNS:
        if re.fullmatch(pattern, compact, re.IGNORECASE):
            return symbol
    return None


def _equation_relationships(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    relationships: list[dict[str, Any]] = []
    seen: set[str] = set()
    for chunk in chunks:
        text = str(chunk.get("text", ""))
        for match in _EQUATION_PATTERN.finditer(text):
            expression = match.group(0).strip()
            left = match.group("left").strip()
            right = match.group("right").strip()
            if not _valid_equation(left, right) or expression in seen:
                continue
            seen.add(expression)
            relationships.append(
                {
                    "relationship_id": f"R{len(relationships) + 1:03d}",
                    "type": "equation",
                    "from": _symbols_in(left),
                    "to": _symbols_in(right),
                    "expression": expression,
                    "evidence": [_evidence(chunk, _sentence_containing(text, match.start()))],
                    "notes": "Extracted verbatim from a textual equality; symbols require confirmation.",
                }
            )
    return relationships


def _valid_equation(left: str, right: str) -> bool:
    if not left or not right:
        return False
    if len(left) > 80 or len(right) > 160:
        return False
    if len(_symbols_in(left)) + len(_symbols_in(right)) < 2:
        return False
    if not _MATH_TOKEN_PATTERN.search(left) or not _MATH_TOKEN_PATTERN.search(right):
        return False
    right_tokens = _symbols_in(right)
    if not any(len(token) > 1 or token.islower() for token in right_tokens):
        return False
    return True


def _symbols_in(expression: str) -> list[str]:
    symbols: list[str] = []
    for match in _MATH_TOKEN_PATTERN.finditer(expression):
        symbol = match.group(1)
        while symbol.endswith(")"):
            symbol = symbol[:-1]
        if not symbol:
            continue
        if symbol.lower() in _EQUATION_STOPWORDS or symbol.lower() in _EXPRESSION_STOPWORDS:
            continue
        if (
            len(symbol) > 2
            and symbol.isalpha()
            and not any(character in expression for character in ("_", "^", "{", "+", "/"))
        ):
            continue
        if symbol in symbols:
            continue
        symbols.append(symbol)
    return symbols


def _equation_symbol_evidence(
    chunks: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> list[tuple[str, dict[str, Any]]]:
    evidence: list[tuple[str, dict[str, Any]]] = []
    for relationship in relationships:
        for reference in relationship.get("evidence", []):
            if not isinstance(reference, dict):
                continue
            block_id = str(reference.get("block_id", ""))
            chunk = next(
                (candidate for candidate in chunks if str(candidate.get("block_id")) == block_id),
                None,
            )
            if chunk is None:
                continue
            quote = str(reference.get("quote", "")) or _NOT_REPORTED
            for symbol in list(relationship.get("from", [])) + list(relationship.get("to", [])):
                if (
                    isinstance(symbol, str)
                    and symbol
                    and symbol.lower() not in _EQUATION_STOPWORDS
                    and symbol.lower() not in _EXPRESSION_STOPWORDS
                ):
                    evidence.append((symbol, {"chunk": chunk, "quote": quote}))
    return evidence


def _relationship_note(raw: str, relationships: list[dict[str, Any]]) -> str:
    for relationship in relationships:
        symbols = set(relationship.get("from", [])) | set(relationship.get("to", []))
        if raw in symbols:
            return str(relationship.get("expression", _NOT_REPORTED))
    return _NOT_REPORTED


def _canonical_name(raw: str) -> str:
    words = re.sub(r"[_-]+", " ", raw).split()
    return " ".join(word if word.isupper() else word.capitalize() for word in words)


def _symbol(name: str, index: int) -> str:
    words = re.findall(r"[A-Za-z]+", name)
    if not words:
        return f"x{index}"
    if len(words) == 1:
        return words[0][:3].lower()
    return "".join(word[0] for word in words[:4]).lower() + str(index)


def _unique_symbol(candidate: str, used: set[str]) -> str:
    if candidate not in used:
        return candidate
    base = re.sub(r"\d+$", "", candidate) or "x"
    suffix = 2
    while f"{base}{suffix}" in used:
        suffix += 1
    return f"{base}{suffix}"


def _role_for(raw: str, quote: str) -> str:
    lowered = raw.lower()
    context = quote.lower()
    if any(word in lowered for word in ("condition", "mutation", "genotype", "treatment", "dose", "temperature")):
        return "independent"
    if any(word in context for word in ("response", "output", "activation", "expressed", "estimated", "level", "activity")):
        return "dependent"
    if any(word in lowered for word in ("constant", "coefficient", "parameter", "rate", "affinity", "threshold", "km", "kcat", "vmax", "ic50")):
        return "parameter"
    if any(word in lowered for word in ("ratio", "fraction", "percentage", "derived")):
        return "derived"
    return "other"


def _kind_for(raw: str) -> str:
    lowered = raw.lower()
    if any(word in lowered for word in ("number", "count", "population")):
        return "count"
    if any(word in lowered for word in ("rate", "flux", "velocity", "frequency")):
        return "rate"
    if any(word in lowered for word in ("condition", "state", "genotype", "mutation")):
        return "categorical"
    return "continuous"


def _definition(quote: str, canonical: str) -> str:
    sentence = quote.strip() or _NOT_REPORTED
    return f"Evidence-supported candidate for {canonical}: {sentence}"


def _unit_near(quote: str) -> str:
    match = re.search(
        r"\b(?:mM|uM|µM|nM|pM|M|mg|g|kg|mL|L|s|ms|min|h|hour|hours|day|days|%|percent|fold|AU|a\.u\.)\b",
        quote,
        re.IGNORECASE,
    )
    return match.group(0) if match else _NOT_REPORTED


def _value_near(quote: str) -> str:
    match = re.search(
        r"(?:=|of|at|between|from)\s*(-?\d+(?:\.\d+)?(?:\s*(?:to|–|-)\s*-?\d+(?:\.\d+)?)?)",
        quote,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else _NOT_REPORTED


def _lexicon_relationships(
    chunks: list[dict[str, Any]],
    variables: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Discover evidence-bound directional relations using the relation lexicon."""
    variable_terms: list[tuple[str, str]] = []
    for variable in variables:
        vid = str(variable.get("variable_id") or "")
        for term in [variable.get("raw_name"), variable.get("canonical_name")]:
            term = str(term or "").strip()
            if len(term) >= 2:
                variable_terms.append((term, vid))
    discovered: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for chunk in chunks:
        text = str(chunk.get("text", ""))
        for entry in match_relations(text, limit=12):
            for alias in list(entry.get("aliases", []))[:6]:
                alias = str(alias).strip()
                if len(alias) < 3:
                    continue
                match = re.search(r"(?<![A-Za-z0-9])" + re.escape(alias).replace(r"\ ", r"\s+") + r"(?![A-Za-z0-9])", text, re.IGNORECASE)
                if not match:
                    continue
                sentence = _sentence_containing(text, match.start())
                # Require at least one extracted variable to appear in the same sentence.
                positioned: list[tuple[int, str]] = []
                for term, vid in variable_terms:
                    found = re.search(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])", sentence, re.IGNORECASE)
                    if found:
                        positioned.append((found.start(), vid))
                if len(positioned) < 2:
                    continue
                positioned.sort(key=lambda item: item[0])
                # Bind distinct variables nearest the relation word; reject self-loops.
                relation_pos = match.start() - (len(text) - len(sentence))
                positioned.sort(key=lambda item: abs(item[0] - relation_pos))
                ordered = list(dict.fromkeys(vid for _, vid in positioned))
                if len(ordered) < 2:
                    continue
                linked = ordered[:3]
                key = (str(entry.get("id")), chunk.get("block_id", ""), sentence[:80])
                if key in seen:
                    continue
                seen.add(key)
                source_ids = linked[: max(1, len(linked) // 2)]
                target_ids = [vid for vid in linked if vid not in source_ids] or linked[1:2]
                if not source_ids or not target_ids or set(source_ids) == set(target_ids):
                    continue
                discovered.append(
                    {
                        "relationship_id": f"RX{len(discovered) + 1:03d}",
                        "type": "directional",
                        "from": source_ids,
                        "to": target_ids,
                        "expression": alias,
                        "evidence": [_evidence(chunk, sentence)],
                        "notes": f"Relation lexicon candidate: {entry.get('canonical_name')}. Requires semantic confirmation; not a proven causal claim.",
                    }
                )
                break
    return discovered


def _relationships(
    variables: list[dict[str, Any]],
    equation_relationships: list[dict[str, Any]],
    lexicon_relationships: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    symbol_to_variable = {
        str(variable.get("symbol")): str(variable.get("variable_id"))
        for variable in variables
        if variable.get("symbol") and variable.get("variable_id")
    }
    relationships: list[dict[str, Any]] = []
    for equation in equation_relationships:
        from_ids = [
            symbol_to_variable[symbol]
            for symbol in equation.get("from", [])
            if symbol in symbol_to_variable
        ]
        to_ids = [
            symbol_to_variable[symbol]
            for symbol in equation.get("to", [])
            if symbol in symbol_to_variable
        ]
        if not from_ids and not to_ids:
            continue
        relationships.append(
            {
                "relationship_id": f"R{len(relationships) + 1:03d}",
                "type": "equation",
                "from": from_ids,
                "to": to_ids,
                "expression": equation.get("expression", _NOT_REPORTED),
                "evidence": equation.get("evidence", []),
                "notes": str(equation.get("notes", "Requires semantic confirmation.")),
            }
        )
    for relation in lexicon_relationships or []:
        relation["relationship_id"] = f"R{len(relationships) + 1:03d}"
        relationships.append(relation)
    return relationships


def _unresolved(
    variables: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not variables:
        return []
    items = [
        {
            "issue": "Evidence-derived variables require semantic review against the source.",
            "related_variables": [variable["variable_id"] for variable in variables],
            "evidence": [],
            "recommended_action": "Run semantic-review, then inspect self-audit findings.",
        }
    ]
    unlinked = [
        str(variable.get("variable_id"))
        for variable in variables
        if str(variable.get("relationship", _NOT_REPORTED)) == _NOT_REPORTED
    ]
    if unlinked:
        items.append(
            {
                "issue": "No explicit equation or assignment was found for these variables.",
                "related_variables": unlinked,
                "evidence": [],
                "recommended_action": "Check tables, figures, equations and supplementary material before modeling.",
            }
        )
    if not relationships:
        items.append(
            {
                "issue": "No textual equation was detected in the supplied text.",
                "related_variables": [],
                "evidence": [],
                "recommended_action": "Supply equations as plain text or JATS math markup; PDF math may need a layout-aware parser.",
            }
        )
    return items


def _evidence(chunk: dict[str, Any] | None, quote: str) -> dict[str, Any]:
    if not chunk:
        return {"block_id": "B0001", "quote": quote or _NOT_REPORTED, "page": None, "section": ""}
    return {
        "block_id": str(chunk.get("block_id", "B0001")),
        "quote": quote.strip() or _NOT_REPORTED,
        "page": chunk.get("page"),
        "section": chunk.get("section", ""),
    }


def _first_sentence(text: str) -> str:
    match = re.match(r"(.+?[.!?])(?:\s|$)", text.strip())
    return (match.group(1) if match else text.strip())[:500]


def _sentence_containing(text: str, offset: int) -> str:
    """Return a contiguous source quote containing the match position."""
    text = str(text)
    radius = 320
    start = max(0, offset - radius)
    end = min(len(text), offset + radius)
    sentence_start = text.rfind(".", 0, offset) + 1
    sentence_end = text.find(".", offset)
    sentence_end = len(text) if sentence_end < 0 else sentence_end + 1
    if sentence_end - sentence_start <= 1400:
        start, end = sentence_start, sentence_end
    return text[start:end].strip()[:1400]


def _first_matching_sentence(text: str, pattern: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return _NOT_REPORTED
    return _sentence_containing(text, match.start())[:500]

_PROTECTED_PARAMETER_PATTERN = re.compile(
    r"^(?:k[_ ]?(?:on|off|cat|f|r)|koff|kon|Km|K_M|K_m|KM|Knm|Vmax|V_max|IC50|IC_50|EC50|EC_50|"
    r"Kd|K_D|Ki|K_i|kcat[_/]?Km|half[- ]life|half[- ]saturation|t_half|t1/2|clearance|release rate|"
    r"growth rate|diffusion coefficient|temperature|threshold|AUROC|AUPRC|flux|reaction flux|"
    r"dissociation rate|association rate|dissociation constant|association constant|enzyme concentration|"
    r"metabolite concentration|substrate concentration|initial condition|initial value)$",
    re.IGNORECASE,
)


def _is_protected_parameter(raw: str) -> bool:
    return bool(_PROTECTED_PARAMETER_PATTERN.match(raw.strip()))
