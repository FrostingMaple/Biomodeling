"""
pdf_utils.py — extract plain text from academic PDF files.

Uses PyMuPDF (import pymupdf) for fast, layout-aware extraction. Academic
papers are frequently two-column; we reconstruct a readable reading order by
sorting text blocks by (line row, left-to-right) so that equations, headers
and body text come out in a sensible order that an LLM can parse.

If pymupdf is not installed this module degrades gracefully: callers can check
HAS_PYMPDF and fall back to a message.
"""

from pathlib import Path

try:
    import pymupdf  # PyMuPDF >= 1.24 preferred import
    if not hasattr(pymupdf, "open"):
        # very old releases exposed fitz.open
        import fitz as pymupdf
    HAS_PYMPDF = True
except Exception:  # pragma: no cover - optional dependency
    HAS_PYMPDF = False


def _page_text(page):
    """Extract page text in a proper reading order, handling two-column layouts.

    Text blocks are clustered into horizontal row-bands by their vertical
    position; within each band blocks are sorted left-to-right. This yields the
    correct "read the left column top-to-bottom, then the right column"
    ordering that naive y-sorting gets wrong.
    """
    blocks = [b for b in page.get_text("blocks") if b[6] == 0]
    if not blocks:
        return ""

    # ---- cluster blocks into row-bands by vertical position ----
    blocks.sort(key=lambda b: (b[1], b[0]))
    bands = []  # list of [y_start, y_end, [blocks]]
    for x0, y0, x1, y1, text, *_ in blocks:
        t = text.strip()
        if not t:
            continue
        # try to fit into an existing band whose vertical span overlaps y0
        placed = False
        for band in bands:
            if y0 <= band[1] and y1 >= band[0]:
                band[1] = max(band[1], y1)
                band[1] = max(band[1], y0)
                band[2].append((x0, t))
                placed = True
                break
        if not placed:
            bands.append([y0, y1, [(x0, t)]])

    lines = []
    for y_start, y_end, items in bands:
        items.sort(key=lambda it: it[0])  # left-to-right within the band
        lines.append("  ".join(t for _, t in items))
    return "\n".join(lines)


def extract_pdf_text(path: str | Path, max_chars: int | None = None) -> str:
    """Return the text of a PDF file as a single string.

    Pages are concatenated with a clear page separator so the agent knows where
    page breaks occur. If `max_chars` is given, output is truncated to that
    many characters (useful for very long papers).
    """
    if not HAS_PYMPDF:
        return (
            "ERROR: pymupdf is not installed in this environment, so .pdf "
            "files cannot be parsed. Install it with "
            '`uv pip install --python .venv/Scripts/python.exe pymupdf` '
            "or convert the PDF to a UTF-8 .txt file first."
        )
    path = Path(path)
    if not path.exists():
        return f"ERROR: file not found: {path}"

    parts = []
    try:
        doc = pymupdf.open(path)
    except Exception as exc:  # pragma: no cover
        return f"ERROR: failed to open PDF {path}: {exc}"
    try:
        for i, page in enumerate(doc):
            page_text = _page_text(page).strip()
            if page_text:
                header = f"\n----- PAGE {i + 1} -----\n"
                parts.append(header + page_text)
    finally:
        doc.close()

    full = "\n".join(parts)
    if max_chars and len(full) > max_chars:
        return (
            f"[PDF text is {len(full)} chars; showing first {max_chars} chars]\n"
            + full[:max_chars]
        )
    return full
