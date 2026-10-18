"""Layered PDF extraction with page maps and layout-aware fallbacks.

The extractor prefers a layout-aware backend (``pdfplumber`` when available),
falls back to ``pypdf`` for the plain text layer, and finally reports a clear
error when neither backend is installed. Scanned pages are reported instead of
silently producing empty or partial text.
"""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .extraction import SourceError, _normalize_newlines


@dataclass
class PdfExtraction:
    lines: list[str] = field(default_factory=list)
    pages: list[int | None] = field(default_factory=list)
    page_count: int = 0
    text_page_count: int = 0
    empty_pages: list[int] = field(default_factory=list)
    backend: str = ""
    has_tables: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def read_pdf(path: Path) -> PdfExtraction:
    """Extract PDF text using the best available backend."""
    errors: list[str] = []
    bundled = _read_with_bundled_runtime(path)
    if bundled is not None:
        if bundled.text_page_count:
            return bundled
        errors.append("bundled runtime found no extractable text")
    for backend in (_read_with_pdfplumber, _read_with_pypdf):
        try:
            extraction = backend(path)
        except _BackendUnavailable as exc:
            errors.append(str(exc))
            continue
        if extraction.text_page_count:
            return extraction
        # Upgrade a pypdf result only if a richer backend becomes available later.
        errors.append(
            f"{backend.__name__} found no extractable text on any of "
            f"{extraction.page_count} page(s)."
        )
    raise SourceError(_missing_text_message(path, errors))


class _BackendUnavailable(RuntimeError):
    """Raised when an optional PDF backend is not importable."""


def _read_with_bundled_runtime(path: Path) -> PdfExtraction | None:
    """Run PDF extraction in the app-bundled Python runtime when available."""
    import json
    import os
    import subprocess

    candidates = []
    app_root = os.environ.get("CODEX_RUNTIME_ROOT")
    if app_root:
        candidates.append(Path(app_root) / "dependencies" / "python" / "python.exe")
    candidates.extend(
        [
            Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "python" / "python.exe",
            pathlib_path("~/AppData/Local/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"),
        ]
    )
    worker = Path(__file__).with_name("pdf_extract_worker.py")
    if not worker.is_file():
        return None
    for python in candidates:
        if python is None or not python.is_file():
            continue
        try:
            completed = subprocess.run(
                [str(python), str(worker), str(path)],
                capture_output=True,
                check=False,
                timeout=300,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if completed.returncode != 0 or not completed.stdout:
            continue
        try:
            payload = json.loads(completed.stdout.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue
        return PdfExtraction(
            lines=[str(item) for item in payload.get("lines", [])],
            pages=list(payload.get("pages", [])),
            page_count=int(payload.get("page_count", 0)),
            text_page_count=int(payload.get("text_page_count", 0)),
            empty_pages=[int(item) for item in payload.get("empty_pages", [])],
            backend="pdfplumber-bundled",
            has_tables=bool(payload.get("has_tables", False)),
        )
    return None


def pathlib_path(value: str) -> Path:
    return Path(value).expanduser()


def _read_with_pdfplumber(path: Path) -> PdfExtraction:
    try:
        pdfplumber = importlib.import_module("pdfplumber")
    except ImportError as exc:
        raise _BackendUnavailable("pdfplumber is not installed") from exc

    extraction = PdfExtraction(backend="pdfplumber")
    try:
        with pdfplumber.open(str(path)) as pdf:
            extraction.page_count = len(pdf.pages)
            for page_number, page in enumerate(pdf.pages, start=1):
                lines: list[str] = []
                tables = _pdfplumber_tables(page)
                if tables:
                    extraction.has_tables = True
                    lines.extend(tables)

                body = page.extract_text(x_tolerance=1.5, y_tolerance=3, layout=False) or ""
                body_lines = _split_pdf_lines(body)
                table_cells = {
                    cell.strip().lower()
                    for line in tables
                    for cell in line.replace("TABLE_ROW:", "").split("|")
                    if cell.strip()
                }
                for line in body_lines:
                    if _body_line_already_in_tables(line, tables, table_cells):
                        continue
                    if line not in lines:
                        lines.append(line)

                if lines:
                    extraction.text_page_count += 1
                else:
                    extraction.empty_pages.append(page_number)
                _append_page(extraction, lines, page_number)

    except Exception as exc:  # noqa: BLE001 - backend-specific failures
        raise SourceError(f"Could not read PDF '{path}' with pdfplumber: {exc}") from exc
    return extraction


def _body_line_already_in_tables(
    line: str,
    tables: list[str],
    table_cells: set[str],
) -> bool:
    """Return True when a flat text line duplicates a recovered table row."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.lower() in table_cells:
        return True
    # A line made entirely of words that already appear in table cells plus
    # punctuation is a duplicate of the table content.
    tokens = [token for token in stripped.split() if token not in {"|"}]
    if not tokens:
        return False
    meaningful = [token for token in tokens if len(token.strip(".,;:()")) > 1]
    if not meaningful:
        return False
    hits = sum(1 for token in meaningful if token.lower() in table_cells)
    if hits == len(meaningful):
        return True
    # pdfplumber can split a single table row across many short words; compare
    # the concatenated form as well.
    compact = re.sub(r"\W+", "", stripped).lower()
    for table in tables:
        flat = re.sub(r"\W+", "", table.replace("TABLE_ROW:", "")).lower()
        if compact and compact in flat:
            return True
    return False


def _pdfplumber_tables(page: Any) -> list[str]:
    """Recover bordered tables, then fall back to coordinate-based row grouping."""
    lines: list[str] = []
    seen: set[str] = set()
    try:
        tables = page.extract_tables() or []
    except Exception:  # noqa: BLE001 - table recovery is best effort
        tables = []
    for table in tables:
        for row in table:
            cells = [re.sub(r"\s+", " ", str(cell)).strip() for cell in row if cell is not None]
            cells = [cell for cell in cells if cell]
            if cells:
                line = "TABLE_ROW: " + " | ".join(cells)
                if line not in seen:
                    seen.add(line)
                    lines.append(line)

    for line in _coordinate_table_lines(page):
        if line not in seen:
            seen.add(line)
            lines.append(line)
    return lines


def _read_with_pypdf(path: Path) -> PdfExtraction:
    try:
        pypdf = importlib.import_module("pypdf")
    except ImportError as exc:
        raise _BackendUnavailable("pypdf is not installed") from exc

    extraction = PdfExtraction(backend="pypdf")
    try:
        reader = pypdf.PdfReader(str(path))
        extraction.page_count = len(reader.pages)
        for page_number, page in enumerate(reader.pages, start=1):
            text = ""
            try:
                text = page.extract_text() or ""
            except Exception:  # noqa: BLE001 - keep going through remaining pages
                text = ""
            lines = _split_pdf_lines(text)
            if lines:
                extraction.text_page_count += 1
            else:
                extraction.empty_pages.append(page_number)
            _append_page(extraction, lines, page_number)
    except Exception as exc:  # noqa: BLE001 - backend-specific failures
        raise SourceError(f"Could not read PDF '{path}' with pypdf: {exc}") from exc
    return extraction


def _split_pdf_lines(text: str) -> list[str]:
    normalized = _normalize_newlines(text)
    lines: list[str] = []
    for raw in normalized.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw).strip()
        if line:
            lines.append(line)
    return lines


def _append_page(extraction: PdfExtraction, lines: list[str], page_number: int) -> None:
    if extraction.lines:
        extraction.lines.append("")
        extraction.pages.append(None)
    extraction.lines.extend(lines)
    extraction.pages.extend([page_number] * len(lines))


def _missing_text_message(path: Path, errors: list[str]) -> str:
    detail = " ".join(errors).strip()
    if "not installed" in detail and "found no extractable text" not in detail:
        return (
            "PDF input requires either 'pdfplumber' or 'pypdf'. "
            "Install one with: py -m pip install pdfplumber pypdf"
        )
    return (
        f"The PDF '{path}' contains no extractable text on any page. "
        "It is likely a scanned document; run OCR before prepare. "
        f"Backend details: {detail}"
    )
