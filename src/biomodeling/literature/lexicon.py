"""Load and query the biological modelling lexicons."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

LEXICON_DIR = Path(__file__).resolve().parent / 'lexicons'
LEXICON_TYPES = ('parameters', 'relations', 'expressions', 'models')


@lru_cache(maxsize=None)
def load_lexicon(name: str) -> dict[str, Any]:
    if name not in LEXICON_TYPES:
        raise ValueError(f"Unknown lexicon '{name}'. Expected one of: {', '.join(LEXICON_TYPES)}")
    path = LEXICON_DIR / f'{name}.json'
    if not path.is_file():
        raise FileNotFoundError(f'Lexicon file not found: {path}')
    return json.loads(path.read_text(encoding='utf-8'))


def load_all_lexicons() -> dict[str, dict[str, Any]]:
    return {name: load_lexicon(name) for name in LEXICON_TYPES}


def entries(name: str) -> list[dict[str, Any]]:
    return [entry for entry in load_lexicon(name).get('entries', []) if isinstance(entry, dict)]


def entry_by_id(name: str, entry_id: str) -> dict[str, Any] | None:
    wanted = entry_id.strip().lower()
    for entry in entries(name):
        if str(entry.get('id', '')).lower() == wanted:
            return entry
    return None


def match_parameters(text: str, *, limit: int = 50) -> list[dict[str, Any]]:
    """Match parameter names and symbols, tolerating underscore and spacing variants."""
    matches: list[dict[str, Any]] = []
    seen: set[str] = set()
    payload = load_lexicon('parameters')
    variants: dict[str, list[str]] = payload.get('symbol_variants', {}) if isinstance(payload.get('symbol_variants'), dict) else {}
    for entry in entries('parameters'):
        terms = list(entry.get('symbols', [])) + list(entry.get('aliases', [])) + [str(entry.get('canonical_name', ''))]
        for symbol in entry.get('symbols', []):
            terms.extend(variants.get(str(symbol), []))
        for term in terms:
            term = str(term).strip()
            if len(term) < 2:
                continue
            # Ignore underscore/space differences: k_on == kon, half-life == half life.
            flexible = re.escape(term).replace(r'\_', r'[_\s-]?').replace(r'\ ', r'[_\s-]?')
            pattern = r'(?<![A-Za-z0-9])' + flexible + r'(?![A-Za-z0-9])'
            if re.search(pattern, text, re.IGNORECASE):
                if str(entry['id']) not in seen:
                    seen.add(str(entry['id']))
                    matches.append(entry)
                break
        if len(matches) >= limit:
            break
    return matches


def match_relations(text: str, *, limit: int = 50) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries('relations'):
        terms = list(entry.get('aliases', [])) + [str(entry.get('canonical_name', ''))]
        for term in terms:
            term = str(term).strip()
            if len(term) < 3:
                continue
            if re.search(r'(?<![A-Za-z0-9])' + re.escape(term).replace(r'\ ', r'\s+') + r'(?![A-Za-z0-9])', text, re.IGNORECASE):
                if str(entry['id']) not in seen:
                    seen.add(str(entry['id']))
                    matches.append(entry)
                break
        if len(matches) >= limit:
            break
    return matches


def match_models(text: str, *, limit: int = 50) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries('models'):
        terms = list(entry.get('aliases', [])) + [str(entry.get('canonical_name', ''))]
        for term in terms:
            term = str(term).strip()
            if len(term) < 4:
                continue
            if re.search(r'(?<![A-Za-z0-9])' + re.escape(term).replace(r'\ ', r'\s+') + r'(?![A-Za-z0-9])', text, re.IGNORECASE):
                if str(entry['id']) not in seen:
                    seen.add(str(entry['id']))
                    matches.append(entry)
                break
        if len(matches) >= limit:
            break
    return matches


def lexicon_summary() -> dict[str, Any]:
    return {
        name: {
            'entry_count': len(entries(name)),
            'source_count': len(load_lexicon(name).get('sources', [])),
        }
        for name in LEXICON_TYPES
    }
