"""Normalize extracted symbols into conventional mathematical notation.

The goal is readability: a reader should be able to recognize volume, concentration,
reaction rate, population size, and time derivatives without knowing the author's
private abbreviations.  Author symbols are always preserved in ``author_symbol``.
"""

from __future__ import annotations

import re
from typing import Any

# Well-established international conventions are preserved verbatim.
CONVENTIONAL_SYMBOLS = {
    "Km", "Vmax", "kcat", "k_on", "k_off", "Kd", "Ki", "IC50", "EC50",
    "T", "D", "R0", "S", "I", "R", "E", "N", "t", "x", "y", "z",
}

# Keyword -> (canonical letter, default subscript, notes)
_QUANTITY_RULES: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (("volume",), "V", "", "volume"),
    (("concentration", "level", "abundance", "biomarker"), "c", "", "concentration or abundance"),
    (("reaction rate", "reaction flux", "flux", "rate of reaction", "velocity"), "r", "", "reaction rate or flux"),
    (("rate constant", "rate coefficient", "kinetic constant"), "k", "", "rate constant"),
    (("growth rate",), "k", "growth", "growth rate constant"),
    (("degradation rate", "decay rate", "turnover"), "k", "deg", "degradation or decay rate constant"),
    (("clearance rate", "clearance", "elimination"), "k", "clear", "clearance rate constant"),
    (("release rate",), "k", "release", "release rate constant"),
    (("production rate", "synthesis rate"), "k", "syn", "production or synthesis rate constant"),
    (("transcription rate",), "k", "tx", "transcription rate constant"),
    (("translation rate",), "k", "tl", "translation rate constant"),
    (("association rate",), "k", "on", "association rate constant"),
    (("dissociation rate",), "k", "off", "dissociation rate constant"),
    (("transition rate",), "k", "transition", "state transition rate constant"),
    (("half-life", "half life"), "t", "half", "half-life"),
    (("time constant",), "tau", "", "time constant"),
    (("sampling time", "time scale", "timescale"), "t", "sample", "time or sampling scale"),
    (("temperature",), "T", "", "temperature"),
    (("diffusion coefficient", "diffusivity"), "D", "", "diffusion coefficient"),
    (("conductance",), "g", "", "ionic conductance"),
    (("capacitance",), "C", "m", "membrane capacitance"),
    (("membrane potential",), "V", "m", "membrane potential"),
    (("reversal potential", "equilibrium potential"), "E", "", "reversal potential"),
    (("free energy", "gibbs"), "G", "", "free energy"),
    (("activation energy",), "E", "a", "activation energy"),
    (("equilibrium constant",), "K", "eq", "equilibrium constant"),
    (("inhibition constant",), "Ki", "", "inhibition constant"),
    (("threshold",), "theta", "", "threshold"),
    (("hill coefficient", "cooperativity"), "n", "H", "Hill coefficient"),
    (("probability", "occupancy", "fraction"), "p", "", "probability or fraction"),
    (("population size", "population", "cell number", "copy number"), "N", "", "population or count"),
    (("dose",), "d", "", "dose"),
    (("inhibitor",), "I", "", "inhibitor"),
    (("enzyme",), "E", "enz", "enzyme"),
    (("substrate",), "c", "S", "substrate concentration"),
    (("product",), "c", "P", "product concentration"),
    (("specificity",), "s", "spec", "specificity"),
    (("sensitivity",), "s", "sens", "sensitivity"),
    (("precision",), "p", "prec", "precision"),
    (("mass action ratio", "reaction quotient"), "Q", "", "mass action ratio"),
    (("flux control coefficient",), "C", "J", "flux control coefficient"),
    (("concentration control coefficient",), "C", "S", "concentration control coefficient"),
    (("response coefficient",), "R", "resp", "response coefficient"),
    (("elasticity",), "epsilon", "", "kinetic elasticity"),
)

# Preferred subscripts for frequently co-occurring named quantities.
_NAMED_SUBSCRIPTS = {
    "gfap": "GFAP",
    "uch-l1": "UCH_L1",
    "uch l1": "UCH_L1",
    "nf-l": "NF_L",
    "nf l": "NF_L",
    "tau": "tau",
    "erk": "ERK",
    "akt": "Akt",
    "egfr": "EGFR",
    "insulin": "insulin",
    "glucagon": "glucagon",
    "glucose": "glucose",
    "sodium": "Na",
    "na+": "Na",
    "messenger rna": "mRNA",
    "mrna": "mRNA",
    "protein": "prot",
    "enzyme": "enz",
    "substrate": "S",
    "product": "P",
    "biomarker": "bio",
    "receptor": "R",
    "ligand": "L",
    "dimer": "dimer",
    "dna": "DNA",
    "atp": "ATP",
    "adp": "ADP",
}

_DERIVATIVE_STATE_LETTERS = {
    "population": "N",
    "population size": "N",
    "cell number": "N",
    "copy number": "N",
    "concentration": "c",
    "biomarker": "c",
    "membrane potential": "V",
    "volume": "V",
    "mass": "m",
    "state probability": "p",
}

STATE_ROLES = {"dependent", "derived", "covariate"}
PARAMETER_ROLES = {"parameter", "controlled"}


def normalize_symbol(variable: dict[str, Any]) -> dict[str, str]:
    """Return normalised symbol fields for one variable record."""
    author_symbol = str(variable.get("symbol") or "").strip()
    canonical = str(variable.get("canonical_name") or variable.get("raw_name") or "").strip()
    raw = str(variable.get("raw_name") or "").strip()
    role = str(variable.get("role") or "other")
    kind = str(variable.get("kind") or "continuous")
    lowered = f"{raw} {canonical}".lower()

    # Keep well-established conventions unchanged.
    if author_symbol in CONVENTIONAL_SYMBOLS and not _needs_subscript(lowered):
        return {
            "symbol": author_symbol,
            "author_symbol": author_symbol,
            "symbol_notes": "Author symbol matches an established international convention; retained unchanged.",
        }

    letter, subscript, reason = _match_quantity(lowered)
    if letter is None:
        letter, subscript, reason = _fallback_letter(lowered, role, kind)

    subscript = subscript or _named_subscript(lowered)
    symbol = _compose(letter, subscript)

    notes = _symbol_notes(author_symbol, symbol, reason, role, lowered)
    return {"symbol": symbol, "author_symbol": author_symbol or "Not reported", "symbol_notes": notes}


def derivative_expression(variable: dict[str, Any], symbol: str | None = None) -> str | None:
    """Return a time-derivative expression for state-like variables, else None."""
    role = str(variable.get("role") or "")
    if role not in STATE_ROLES:
        return None
    canonical = str(variable.get("canonical_name") or variable.get("raw_name") or "").lower()
    for phrase, letter in _DERIVATIVE_STATE_LETTERS.items():
        if phrase in canonical:
            subscript = _named_subscript(canonical)
            return f"d{_compose(letter, subscript)}/dt"
    # Fall back to the normalised symbol, using the named subscript when available.
    state = str(symbol or variable.get("symbol") or "").strip()
    if not state:
        letter, subscript, _ = _match_quantity(canonical)
        subscript = subscript or _named_subscript(canonical)
        state = _compose(letter or "x", subscript)
    state = re.sub(r"[^A-Za-z0-9_]", "", state) or "X"
    return f"d{state}/dt"


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Apply symbol normalisation in place-safe fashion and return a summary."""
    variables = [item for item in payload.get("variables", []) if isinstance(item, dict)]
    used: set[str] = set()
    changed = 0
    for variable in variables:
        original = str(variable.get("symbol") or "")
        result = normalize_symbol(variable)
        symbol = result["symbol"]
        if symbol in used:
            suffix = 2
            while f"{symbol}_{suffix}" in used:
                suffix += 1
            symbol = f"{symbol}_{suffix}"
            result["symbol_notes"] = result["symbol_notes"] + " Disambiguated with numeric suffix because the same symbol appears more than once."
        used.add(symbol)
        variable["symbol"] = symbol
        variable["author_symbol"] = result["author_symbol"]
        variable["symbol_notes"] = result["symbol_notes"]
        derivative = derivative_expression(variable, symbol)
        if derivative:
            variable["derivative"] = derivative
        if symbol != original:
            changed += 1
    return {"normalized_variables": len(variables), "changed_symbols": changed}


def _needs_subscript(lowered: str) -> bool:
    return any(token in lowered for token in ("specific", "total", "maximal", "maximum", "initial"))


def _match_quantity(lowered: str) -> tuple[str | None, str, str]:
    for keywords, letter, subscript, reason in _QUANTITY_RULES:
        if any(keyword in lowered for keyword in keywords):
            return letter, subscript, reason
    return None, "", ""


def _named_subscript(lowered: str) -> str:
    for name, subscript in _NAMED_SUBSCRIPTS.items():
        if name in lowered:
            return subscript
    return ""


def _fallback_letter(lowered: str, role: str, kind: str) -> tuple[str, str, str]:
    if role in PARAMETER_ROLES:
        return "k", "", "unspecified model parameter represented as a rate-like constant"
    if kind == "rate":
        return "r", "", "unspecified rate quantity"
    if kind == "count":
        return "N", "", "unspecified count or population quantity"
    words = re.findall(r"[a-z]+", lowered)
    for word in words:
        if word not in {"the", "and", "for", "with", "value", "level", "ratio"}:
            return word[0], "", "first meaningful letter of the author term"
    return "x", "", "generic variable placeholder"


def _compose(letter: str, subscript: str) -> str:
    if not subscript:
        return letter
    subscript = re.sub(r"[^A-Za-z0-9_]+", "_", subscript).strip("_")
    return f"{letter}_{subscript}" if subscript else letter


def _symbol_notes(author_symbol: str, symbol: str, reason: str, role: str, lowered: str) -> str:
    if author_symbol and author_symbol != symbol:
        return f"Author symbol '{author_symbol}' normalised to '{symbol}' ({reason})."
    if author_symbol:
        return f"Author symbol '{author_symbol}' retained; interpreted as {reason}."
    return f"Symbol '{symbol}' assigned from the author term ({reason})."
