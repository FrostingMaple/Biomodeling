"""Worker executed by the bundled Python runtime to extract PDF text.

This module is intentionally dependency-light and JSON-oriented so it can run
in a different Python installation than the main CLI process.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


def _split_lines(text: str) -> list[str]:
    return [re.sub(r"[ \t]+", " ", line).strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip()]


def _looks_like_table_row(line: str, table_cells: set[str]) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.lower() in table_cells:
        return True
    tokens = [token for token in stripped.split() if len(token.strip(".,;:()")) > 1]
    if not tokens:
        return False
    hits = sum(1 for token in tokens if token.lower() in table_cells)
    return hits == len(tokens)


def _coordinate_table_lines(page: Any) -> list[str]:
    try:
        words = page.extract_words(use_text_flow=False, keep_blank_chars=False) or []
    except Exception:  # noqa: BLE001
        return []
    if not words:
        return []

    rows: list[list[dict[str, Any]]] = []
    for word in sorted(words, key=lambda item: (float(item.get("top", 0)), float(item.get("x0", 0)))):
        top = float(word.get("top", 0))
        height = float(word.get("height", 0)) or 10.0
        placed = False
        for row in rows:
            row_top = float(row[0].get("top", 0))
            row_height = max(float(item.get("height", 0)) or 10.0 for item in row)
            if abs(top - row_top) <= max(2.0, min(height, row_height) * 0.5):
                row.append(word)
                placed = True
                break
        if not placed:
            rows.append([word])

    rows = [sorted(row, key=lambda item: float(item.get("x0", 0))) for row in rows]
    column_starts: dict[float, int] = {}
    table_rows: list[list[dict[str, Any]]] = []
    for row in rows:
        if len(row) < 3:
            continue
        gaps = [
            float(row[index + 1].get("x0", 0)) - float(row[index].get("x1", 0))
            for index in range(len(row) - 1)
        ]
        if not any(gap >= 18.0 for gap in gaps):
            continue
        # Prose rows have large, irregular inter-word gaps relative to word width.
        word_widths = [
            float(word.get("x1", 0)) - float(word.get("x0", 0))
            for word in row
            if float(word.get("x1", 0)) > float(word.get("x0", 0))
        ]
        if not word_widths:
            continue
        median_width = sorted(word_widths)[len(word_widths) // 2]
        large_gaps = [gap for gap in gaps if gap >= 18.0]
        if len(large_gaps) > 2 or (large_gaps and max(large_gaps) > median_width * 6.0):
            continue
        table_rows.append(row)
        for index, gap in enumerate(gaps):
            if gap < 18.0:
                continue
            start = round(float(row[index + 1].get("x0", 0)), 1)
            if not any(abs(start - existing) <= 10.0 for existing in column_starts):
                column_starts[start] = 1
        first = round(float(row[0].get("x0", 0)), 1)
        if not any(abs(first - existing) <= 10.0 for existing in column_starts):
            column_starts[first] = 1

    if len(column_starts) < 2 or len(column_starts) > 8:
        return []
    columns = sorted(column_starts)

    def column_index(word: dict[str, Any]) -> int:
        x0 = float(word.get("x0", 0))
        index = 0
        for position, column in enumerate(columns):
            if x0 >= column - 12.0:
                index = position
        return index

    lines: list[str] = []
    column_count = len(columns)
    for row in table_rows:
        if len(row) < 2:
            continue
        cells: dict[int, list[str]] = {}
        for word in row:
            cells.setdefault(column_index(word), []).append(str(word.get("text", "")))
        values = [" ".join(cells[index]) for index in sorted(cells)]
        values = [re.sub(r"\s+", " ", value).strip() for value in values if value.strip()]
        if len(values) < 2:
            continue
        # A genuine table row uses at least two distinct columns and has short
        # cell values. Long prose split by column detection is rejected.
        if len(values) < min(2, column_count) or len(values) < 2:
            continue
        if max(len(value.split()) for value in values) > 8:
            continue
        lines.append("TABLE_ROW: " + " | ".join(values))
    return lines


def extract(path: str) -> dict[str, Any]:
    import pdfplumber

    lines: list[str] = []
    pages: list[int | None] = []
    page_count = 0
    text_pages = 0
    empty_pages: list[int] = []
    has_tables = False

    with pdfplumber.open(path) as pdf:
        page_count = len(pdf.pages)
        for page_number, page in enumerate(pdf.pages, start=1):
            page_lines: list[str] = []
            table_lines: list[str] = []
            try:
                for table in page.extract_tables() or []:
                    for row in table:
                        cells = [re.sub(r"\s+", " ", str(cell)).strip() for cell in row if cell]
                        if cells:
                            table_lines.append("TABLE_ROW: " + " | ".join(cells))
            except Exception:  # noqa: BLE001
                table_lines = []
            if table_lines:
                has_tables = True
                page_lines.extend(table_lines)

            body = page.extract_text(x_tolerance=1.5, y_tolerance=3, layout=False) or ""
            table_cells = {
                cell.strip().lower()
                for line in table_lines
                for cell in line.replace("TABLE_ROW:", "").split("|")
                if cell.strip()
            }
            for line in _split_lines(body):
                if _looks_like_table_row(line, table_cells):
                    continue
                if line not in page_lines:
                    page_lines.append(line)

            if page_lines:
                text_pages += 1
            else:
                empty_pages.append(page_number)
            if lines:
                lines.append("")
                pages.append(None)
            lines.extend(page_lines)
            pages.extend([page_number] * len(page_lines))

    return {
        "lines": lines,
        "pages": pages,
        "page_count": page_count,
        "text_page_count": text_pages,
        "empty_pages": empty_pages,
        "has_tables": has_tables,
    }


def main() -> int:
    payload = extract(sys.argv[1])
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
