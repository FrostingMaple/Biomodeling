"""Source ingestion and deterministic chunking."""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

CHUNK_SCHEMA_VERSION = "1.0"
EXTRACTION_SCHEMA_VERSION = "1.0"

_SENTENCE_END = re.compile(r"(?<=[.!?])(?:[)\]\"']*)\s+(?=[A-Z0-9(\[]|\Z)")
_MARKDOWN_HEADING = re.compile(r"^\s*#{1,6}\s+(?P<title>.+?)\s*$")
_NAMED_HEADING = re.compile(
    r"^\s*(?:(?P<number>(?:\d+(?:\.\d+)*)|(?:[IVXLC]+))[.)]?\s+)?"
    r"(?P<title>abstract|introduction|background|related work|materials and methods|"
    r"methods|methodology|study design|experimental design|model|mathematical model|"
    r"model description|model formulation|model equations?|governing equations?|"
    r"kinetic model|kinetics|parameter(?:s| values?| estimation| table)?|"
    r"variable(?:s| definitions?| table)?|state variables?|"
    r"initial conditions?|boundary conditions?|assumptions?|equations?|"
    r"simulation(?:s| setup| details)?|experimental data|data|"
    r"results|findings|discussion|conclusions?|limitations?|references|"
    r"supplementary(?: information)?|appendix)\s*:?\s*$",
    re.IGNORECASE,
)
_PDF_UNAMBIGUOUS_SINGLE_HEADINGS = {
    "abstract",
    "assumptions",
    "equations",
    "kinetics",
    "methods",
    "model",
    "results",
    "discussion",
    "conclusions",
    "references",
    "appendix",
}
_PDF_SECTION_HEADINGS = {
    "abstract",
    "assumptions",
    "boundary conditions",
    "data",
    "equations",
    "experimental data",
    "governing equations",
    "initial conditions",
    "kinetic model",
    "kinetics",
    "mathematical model",
    "model",
    "model description",
    "model equations",
    "model formulation",
    "parameter estimation",
    "parameter table",
    "parameter values",
    "parameters",
    "simulation details",
    "simulation setup",
    "simulations",
    "state variables",
    "variable definitions",
    "variable table",
    "variables",
}
_JATS_TITLE_TAGS = {"article-title", "title"}
_XML_ID_ATTR = "{http://www.w3.org/XML/1998/namespace}id"
_XML_VAL_ATTR = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
_JATS_TEXT_BLOCK_TAGS = {
    "abstract",
    "table-wrap",
    "p",
    "caption",
    "license-p",
    "disp-quote",
    "speech",
    "statement",
    "note",
    "fn",
}


class SourceError(RuntimeError):
    """Raised when a source cannot be read into evidence-bearing text."""


class DownloadError(SourceError):
    """Raised when a DOI cannot be resolved into readable source text."""


@dataclass(frozen=True)
class Section:
    section: str
    order: int
    text: str
    line_start: int = 0
    line_end: int = 0


@dataclass(frozen=True)
class Token:
    text: str
    page: int | None


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\ufeff", "")


def _clean_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in _normalize_newlines(text).split("\n"):
        line = raw_line.rstrip()
        if line.strip():
            lines.append(line)
    return lines


@dataclass(frozen=True)
class SourceDocument:
    text: str
    pages: list[int | None]
    metadata: dict[str, object]


def read_source(path: Path) -> tuple[str, list[int | None]]:
    """Return text and a per-line page map (``None`` for page-less formats)."""
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".markdown", ".rst"}:
        return path.read_text(encoding="utf-8", errors="replace"), []
    if suffix in {".xml", ".jats"}:
        document = read_source_document(path)
        return document.text, document.pages
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix == ".docx":
        return _read_docx(path)
    raise SourceError(
        f"Unsupported source type '{suffix or '(none)'}'. "
        "Use .txt, .md, .rst, .xml, .jats, .pdf, or .docx."
    )


def read_source_document(path: Path) -> SourceDocument:
    """Read a source and return text, page map, and available metadata."""
    suffix = path.suffix.lower()
    if suffix in {".xml", ".jats"}:
        return _read_jats(path)
    if suffix == ".docx":
        return _read_docx_document(path)
    text, pages = read_source(path)
    return SourceDocument(text=text, pages=pages, metadata={})


def read_text_and_chunk(
    text: str,
    *,
    source_path: str,
    source_name: str,
    metadata: dict[str, object] | None = None,
    source_bytes: bytes | None = None,
    pages: Sequence[int | None] | None = None,
    target_words: int = 170,
    max_words: int = 260,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Build a prepared source from already-extracted text."""
    return _prepare_from_text(
        text,
        source_path=source_path,
        source_name=source_name,
        metadata=metadata,
        source_bytes=source_bytes,
        pages=pages,
        target_words=target_words,
        max_words=max_words,
    )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _node_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    if any(_local_name(node.tag) in {"math", "tex-math"} for node in element.iter()):
        return " ".join(_mathml_text(element).split())
    return " ".join("".join(element.itertext()).split())


def _mathml_text(element: ET.Element) -> str:
    """Render MathML into readable linear notation such as k_on and K_m."""
    pieces: list[str] = []
    for node in element.iter():
        tag = _local_name(node.tag)
        if tag in {"math", "semantics", "mrow", "tex-math", "alternatives", "mml"}:
            continue
        if tag == "mi":
            pieces.append(str(node.text or "").strip())
        elif tag == "mn":
            pieces.append(str(node.text or "").strip())
        elif tag == "mo":
            operator = str(node.text or "").strip()
            if operator in {"=", "+", "-", "/", "*", "(", ")"}:
                pieces.append(f" {operator} ")
        elif tag == "msub":
            children = list(node)
            base = _mathml_text(children[0]) if children else ""
            sub = _mathml_text(children[1]) if len(children) > 1 else ""
            if base and sub:
                pieces.append(f"{base}_{sub}")
            else:
                pieces.append(base or sub)
        elif tag == "msup":
            children = list(node)
            base = _mathml_text(children[0]) if children else ""
            sup = _mathml_text(children[1]) if len(children) > 1 else ""
            if base and sup:
                pieces.append(f"{base}^{sup}")
            else:
                pieces.append(base or sup)
        elif tag == "msubsup":
            children = list(node)
            base = _mathml_text(children[0]) if children else ""
            sub = _mathml_text(children[1]) if len(children) > 1 else ""
            sup = _mathml_text(children[2]) if len(children) > 2 else ""
            if base and sub:
                pieces.append(f"{base}_{sub}")
            elif base:
                pieces.append(base)
            if sup:
                pieces.append(f"^{sup}")
        elif tag == "mfrac":
            children = list(node)
            numerator = _mathml_text(children[0]) if children else ""
            denominator = _mathml_text(children[1]) if len(children) > 1 else ""
            if numerator and denominator:
                pieces.append(f"({numerator})/({denominator})")
            else:
                pieces.append(numerator or denominator)
        elif tag in {"mover", "munder", "munderover"}:
            children = list(node)
            base = _mathml_text(children[0]) if children else ""
            script = _mathml_text(children[1]) if len(children) > 1 else ""
            upper = _mathml_text(children[2]) if len(children) > 2 else ""
            if base:
                pieces.append(base)
            if tag == "mover" and script:
                pieces.append(f"^{script}")
            elif script:
                pieces.append(f"_{script}")
            if upper:
                pieces.append(f"^{upper}")
        elif tag in {"msqrt", "mroot"}:
            children = list(node)
            pieces.append("sqrt(" + " ".join(_mathml_text(child) for child in children) + ")")
    return "".join(pieces).strip()


def _first_descendant(root: ET.Element, tag_name: str) -> ET.Element | None:
    return next((element for element in root.iter() if _local_name(element.tag) == tag_name), None)


def _read_jats(path: Path) -> SourceDocument:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        raise SourceError(f"Could not parse JATS XML '{path}': {exc}") from exc

    metadata = _jats_metadata(root)
    body = _first_descendant(root, "body")
    if body is None:
        raise SourceError(f"JATS XML '{path}' does not contain a body element.")

    lines: list[str] = []
    first = True
    abstract = _first_descendant(root, "abstract")
    if abstract is not None:
        lines.append("# abstract")
        lines.append("")
        lines.extend(_jats_text_blocks(abstract))
        first = False
    for section in _jats_body_sections(body):
        if not first:
            lines.append("")
        first = False
        lines.append(f"# {section['title']}")
        lines.append("")
        lines.extend(section["paragraphs"])
    text = "\n".join(lines).strip()
    if not text:
        raise SourceError(f"JATS XML '{path}' contains no extractable body text.")
    page_map = [None] * len(text.split("\n"))
    metadata["format"] = "jats_xml"
    return SourceDocument(text=text, pages=page_map, metadata=metadata)


def _jats_metadata(root: ET.Element) -> dict[str, object]:
    article_title = _node_text(_first_descendant(root, "article-title"))
    authors: list[str] = []
    for contrib in root.iter():
        if _local_name(contrib.tag) != "contrib":
            continue
        if contrib.attrib.get("contrib-type", "author") not in {"author", ""}:
            continue
        name = next((child for child in contrib if _local_name(child.tag) == "name"), None)
        if name is None:
            continue
        surname = _node_text(next((child for child in name if _local_name(child.tag) == "surname"), None))
        given = _node_text(next((child for child in name if _local_name(child.tag) == "given-names"), None))
        full_name = " ".join(part for part in (given, surname) if part).strip()
        if full_name:
            authors.append(full_name)

    year = ""
    for element in root.iter():
        if _local_name(element.tag) == "year" and _node_text(element):
            year = _node_text(element)
            break
    doi = ""
    for element in root.iter():
        if _local_name(element.tag) == "article-id" and element.attrib.get("pub-id-type") == "doi":
            doi = _node_text(element)
            break
    pmcid = ""
    for element in root.iter():
        if _local_name(element.tag) == "article-id" and element.attrib.get("pub-id-type") == "pmcid":
            pmcid = _node_text(element)
            break
    return {
        "title": article_title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "pmcid": pmcid,
        "language": root.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", "en"),
    }


def _jats_body_sections(body: ET.Element) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    direct_sections = [child for child in body if _local_name(child.tag) == "sec"]
    if direct_sections:
        for section in direct_sections:
            sections.extend(_walk_jats_section(section, fallback_title="Body"))
    else:
        sections.append({"title": "Body", "paragraphs": _jats_paragraphs(body)})
    return [section for section in sections if section["paragraphs"]]


def _walk_jats_section(section: ET.Element, fallback_title: str) -> list[dict[str, object]]:
    title_element = next((child for child in section if _local_name(child.tag) == "title"), None)
    title = _node_text(title_element) or fallback_title
    paragraphs = _jats_direct_paragraphs(section)
    records: list[dict[str, object]] = []
    if paragraphs:
        records.append({"title": title, "paragraphs": paragraphs})
    for child in section:
        if _local_name(child.tag) != "sec":
            continue
        records.extend(_walk_jats_section(child, fallback_title=title))
    return records


def _jats_direct_paragraphs(container: ET.Element) -> list[str]:
    """Collect paragraph-like nodes directly owned by a section, excluding nested sections."""
    paragraphs: list[str] = []

    def collect(element: ET.Element, *, is_root: bool) -> None:
        tag = _local_name(element.tag)
        if tag == "sec" and not is_root:
            return
        if tag in _JATS_TEXT_BLOCK_TAGS:
            text = _node_text(element)
            if text and text not in paragraphs:
                paragraphs.append(text)
            return
        for child in element:
            collect(child, is_root=False)

    for child in container:
        if _local_name(child.tag) == "sec":
            continue
        collect(child, is_root=False)
    for table in container.iter():
        if _local_name(table.tag) != "table-wrap" or table is container:
            continue
        text = _node_text(table)
        if text and text not in paragraphs:
            paragraphs.append(text)
    return paragraphs


def _jats_paragraphs(container: ET.Element) -> list[str]:
    paragraphs: list[str] = []
    for element in container.iter():
        if _local_name(element.tag) not in _JATS_TEXT_BLOCK_TAGS:
            continue
        text = _node_text(element)
        if not text:
            continue
        # A parent abstract/fn may include child paragraphs and would otherwise duplicate them.
        if any(text == existing or text in existing for existing in paragraphs):
            continue
        paragraph_lines = _paragraph_lines(text)
        paragraphs.extend(paragraph_lines)
    return paragraphs


def _jats_text_blocks(container: ET.Element) -> list[str]:
    blocks: list[str] = []
    for element in container.iter():
        if _local_name(element.tag) == "table-wrap" and element is not container:
            text = _node_text(element)
            if text and text not in blocks:
                blocks.append(text)
            continue
        if _local_name(element.tag) not in _JATS_TEXT_BLOCK_TAGS:
            continue
        text = _node_text(element)
        if text and text not in blocks:
            blocks.append(text)
    return blocks


def _paragraph_lines(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    # Preserve long text as one paragraph; the chunker handles sentence-sized blocks.
    return [cleaned]


def _read_pdf(path: Path) -> tuple[str, list[int | None]]:
    _register_pdf_dependency_paths()
    from .pdf import read_pdf

    extraction = read_pdf(path)
    return extraction.text, extraction.pages


def _register_pdf_dependency_paths() -> None:
    """Make bundled PDF backends importable without installing anything."""
    import sys

    candidate = (
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "python"
        / "Lib"
        / "site-packages"
    )
    if candidate.is_dir():
        entry = str(candidate)
        if entry not in sys.path:
            sys.path.insert(0, entry)


def _read_docx(path: Path) -> tuple[str, list[int | None]]:
    document = _read_docx_document(path)
    return document.text, document.pages


def _read_docx_document(path: Path) -> SourceDocument:
    """Read DOCX paragraphs and tables without requiring an external package."""
    try:
        with zipfile.ZipFile(path) as archive:
            documents = [name for name in archive.namelist() if name.startswith("word/") and name.endswith(".xml")]
            if "word/document.xml" not in archive.namelist():
                raise SourceError(f"DOCX '{path}' does not contain word/document.xml.")
            root = ET.fromstring(archive.read("word/document.xml"))
            lines = _docx_block_lines(root)
            lines.extend(_docx_footnote_lines(archive, documents))
    except zipfile.BadZipFile as exc:
        raise SourceError(f"Could not open DOCX '{path}': {exc}") from exc
    except ET.ParseError as exc:
        raise SourceError(f"Could not parse DOCX '{path}': {exc}") from exc

    if not lines:
        raise SourceError(f"DOCX '{path}' contains no extractable paragraphs or tables.")
    return SourceDocument(text="\n".join(lines), pages=[], metadata={"format": "docx"})


def _docx_block_lines(root: ET.Element) -> list[str]:
    """Walk document.xml in reading order, emitting headings, paragraphs and table rows."""
    paragraphs: dict[str, ET.Element] = {}
    tables: dict[str, ET.Element] = {}
    body = next(
        (element for element in root.iter() if _local_name(element.tag) == "body"),
        None,
    )
    for element in root.iter():
        tag = _local_name(element.tag)
        if tag == "p":
            paragraphs[element.attrib.get(_XML_ID_ATTR, str(id(element)))] = element
        elif tag == "tbl":
            tables[element.attrib.get(_XML_ID_ATTR, str(id(element)))] = element
    blocks: list[tuple[int, str]] = []
    order = 0
    for child in body if body is not None else root:
        tag = _local_name(child.tag)
        if tag == "p":
            text = _node_text(child)
            if text:
                blocks.append((order, _docx_paragraph_line(child, text)))
                order += 1
        elif tag == "tbl":
            for line in _docx_table_lines(child):
                blocks.append((order, line))
                order += 1
    return [line for _, line in blocks]


def _docx_paragraph_line(element: ET.Element, text: str) -> str:
    style = next(
        (
            node.attrib.get(_XML_VAL_ATTR, "")
            for node in element.iter()
            if _local_name(node.tag) == "pStyle"
        ),
        "",
    )
    if "heading" in style.lower() or "title" in style.lower():
        return f"# {text}"
    return text


def _docx_table_lines(table: ET.Element) -> list[str]:
    lines: list[str] = []
    for row in (child for child in table if _local_name(child.tag) == "tr"):
        cells = [_node_text(cell) for cell in row if _local_name(cell.tag) == "tc"]
        cells = [cell for cell in cells if cell]
        if cells:
            lines.append(" | ".join(cells))
    return lines


def _docx_footnote_lines(archive: zipfile.ZipFile, names: list[str]) -> list[str]:
    lines: list[str] = []
    for name in sorted(names):
        if not (name.startswith("word/footnotes") or name.startswith("word/endnotes")):
            continue
        try:
            root = ET.fromstring(archive.read(name))
        except ET.ParseError:
            continue
        for paragraph in (node for node in root.iter() if _local_name(node.tag) == "p"):
            text = _node_text(paragraph)
            if text:
                lines.append(text)
    return lines


def build_sections(text: str, pages: Sequence[int | None] | None = None) -> list[Section]:
    """Split source text into ordered sections while preserving page metadata."""
    page_map = list(pages or [])
    normalized = _normalize_newlines(text)
    raw_lines = normalized.split("\n")
    if not page_map:
        page_map = [None] * len(raw_lines)
    elif len(page_map) < len(raw_lines):
        page_map.extend([page_map[-1] if page_map else None] * (len(raw_lines) - len(page_map)))

    sections: list[Section] = []
    current_name = "front_matter"
    current_order = 0
    buffer: list[tuple[int, str]] = []

    def flush() -> None:
        nonlocal buffer
        content = "\n".join(_strip_table_marker(line) for _, line in buffer if line.strip()).strip()
        if content:
            line_start = buffer[0][0]
            line_end = buffer[-1][0] + 1
            sections.append(
                Section(current_name, current_order, content, line_start, line_end)
            )
        buffer = []

    for index, raw_line in enumerate(raw_lines):
        line = raw_line.rstrip()
        if not line.strip():
            if buffer:
                buffer.append((index, ""))
            continue

        heading = _MARKDOWN_HEADING.match(line.strip()) or _NAMED_HEADING.match(line.strip())
        if heading is None and _is_pdf_section_heading(line):
            heading = re.match(r"^\s*(?P<title>.+?)\s*$", line.strip())
        if heading:
            flush()
            current_name = _normalize_heading(heading.group("title"))
            current_order += 1
            continue

        buffer.append((index, line))

    flush()
    if not sections:
        cleaned = normalized.strip()
        if cleaned:
            sections.append(Section("front_matter", 0, cleaned, 0, len(raw_lines)))
    return _merge_tiny_sections(sections)


def _strip_table_marker(line: str) -> str:
    marker = "TABLE_ROW:"
    stripped = line.lstrip()
    if stripped.startswith(marker):
        return stripped[len(marker) :].strip()
    return line


def _normalize_heading(value: str) -> str:
    key = re.sub(r"\s+", " ", value.strip().lower())
    aliases = {
        "materials and methods": "methods",
        "methodology": "methods",
        "mathematical model": "model",
        "study design": "methods",
        "experimental design": "methods",
        "findings": "results",
        "conclusion": "conclusions",
        "limitation": "limitations",
        "supplementary information": "supplementary",
    }
    return aliases.get(key, key.replace(" ", "_"))


def _is_pdf_section_heading(line: str) -> bool:
    """Detect short standalone headings that survived PDF text extraction."""
    if line.strip().startswith("TABLE_ROW:"):
        return False
    candidate = line.strip().strip(":")
    if not candidate or len(candidate) > 60:
        return False
    if len(candidate.split()) > 8:
        return False
    if candidate.endswith((".", ";", ",")):
        return False
    if re.search(r"\d", candidate):
        # Numbered headings such as "2.1 Kinetic model" are allowed; data rows are not.
        stripped = re.sub(r"^\d+(?:\.\d+)*[.)]?\s+", "", candidate).lower()
        if stripped not in _PDF_SECTION_HEADINGS:
            return False
        return True
    normalized = re.sub(r"[^a-z ]", "", candidate.lower()).strip()
    if normalized not in _PDF_SECTION_HEADINGS:
        return False
    if len(normalized.split()) > 1:
        return True
    # Single ambiguous words ("parameter", "variable", "data") are often table
    # cells after PDF extraction; require an unambiguous single-word heading.
    return normalized in _PDF_UNAMBIGUOUS_SINGLE_HEADINGS


def _merge_tiny_sections(sections: list[Section]) -> list[Section]:
    """Attach empty headings to the preceding section without merging real text."""
    merged: list[Section] = []
    for section in sections:
        if not section.text.strip():
            continue
        if merged and len(section.text.split()) < 3:
            previous = merged[-1]
            merged[-1] = Section(
                previous.section,
                previous.order,
                f"{previous.text}\n{section.text}",
                previous.line_start,
                section.line_end,
            )
            continue
        merged.append(section)
    return merged


def chunk_sections(
    sections: Sequence[Section],
    *,
    target_words: int = 170,
    max_words: int = 260,
    pages: Sequence[int | None] | None = None,
) -> list[dict[str, object]]:
    """Create stable evidence blocks that do not cross section boundaries."""
    if target_words <= 0 or max_words < target_words:
        raise ValueError("Require 0 < target_words <= max_words")

    chunks: list[dict[str, object]] = []
    sequence = 0
    page_map = list(pages or [])
    for section in sections:
        for piece in _split_section(section.text, target_words, max_words):
            piece_page = _page_for_piece(
                piece,
                section.text,
                section.line_start,
                section.line_end,
                page_map,
            )
            sequence += 1
            chunks.append(
                {
                    "block_id": f"B{sequence:04d}",
                    "section": section.section,
                    "section_order": section.order,
                    "page": piece_page,
                    "text": _piece_text(piece),
                    "word_count": len(_piece_text(piece).split()),
                    "sha256": hashlib.sha256(_piece_text(piece).encode("utf-8")).hexdigest(),
                }
            )
    return chunks


def _sentence_pieces(text: str) -> list[str]:
    text = re.sub(r"[ \t]+", " ", text).strip()
    if not text:
        return []
    pieces = [part.strip() for part in _SENTENCE_END.split(text) if part.strip()]
    return pieces or [text]


def _split_section(text: str, target_words: int, max_words: int) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    pieces: list[str] = []
    for paragraph in paragraphs:
        current: list[str] = []
        current_words = 0
        for sentence in _sentence_pieces(paragraph):
            sentence_words = len(sentence.split())
            if current and current_words + sentence_words > max_words:
                pieces.append(" ".join(current))
                current = []
                current_words = 0
            if sentence_words > max_words:
                if current:
                    pieces.append(" ".join(current))
                    current = []
                    current_words = 0
                pieces.extend(_hard_split(sentence, target_words, max_words))
                continue
            current.append(sentence)
            current_words += sentence_words
            if current_words >= target_words:
                pieces.append(" ".join(current))
                current = []
                current_words = 0
        if current:
            pieces.append(" ".join(current))
    return pieces


def _hard_split(text: str, target_words: int, max_words: int) -> list[str]:
    words = text.split()
    pieces: list[str] = []
    for start in range(0, len(words), target_words):
        pieces.append(" ".join(words[start : start + target_words]))
    return pieces


def _piece_text(piece: str) -> str:
    return piece.strip()


def _page_for_piece(
    piece: str,
    section_text: str,
    line_start: int,
    line_end: int,
    pages: Sequence[int | None],
) -> int | None:
    if not pages:
        return None
    local_ratio = 0.0
    if section_text and piece:
        local_offset = section_text.find(piece)
        if local_offset > 0:
            local_ratio = local_offset / len(section_text)
    absolute = line_start + round((line_end - line_start - 1) * local_ratio)
    absolute = max(0, min(absolute, min(line_end, len(pages)) - 1))
    if line_start <= absolute < len(pages):
        return pages[absolute]
    for index in range(max(0, line_start), min(line_end, len(pages))):
        if pages[index] is not None:
            return pages[index]
    return None


def iter_chunks_as_records(chunks: Iterable[dict[str, object]]) -> Iterator[str]:
    import json

    for chunk in chunks:
        yield json.dumps(chunk, ensure_ascii=False, sort_keys=True)


def page_for_offset(text: str, offset: int, pages: Sequence[int | None]) -> int | None:
    """Map a character offset to a page number when a page map is available."""
    if not pages:
        return None
    bounded = max(0, min(offset, len(text.splitlines()) - 1))
    if bounded < len(pages):
        return pages[bounded]
    return pages[-1]


def read_and_chunk(path: Path, target_words: int = 170, max_words: int = 260) -> tuple[dict[str, object], list[dict[str, object]]]:
    document = read_source_document(path)
    return _prepare_from_text(
        document.text,
        source_path=str(path.resolve()),
        source_name=path.name,
        metadata=document.metadata,
        source_bytes=path.read_bytes(),
        pages=document.pages,
        target_words=target_words,
        max_words=max_words,
    )


def _prepare_from_text(
    text: str,
    *,
    source_path: str,
    source_name: str,
    metadata: dict[str, object] | None = None,
    source_bytes: bytes | None = None,
    pages: Sequence[int | None] | None = None,
    target_words: int = 170,
    max_words: int = 260,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    page_map = list(pages or [])
    sections = build_sections(text, page_map)
    chunks = chunk_sections(
        sections,
        target_words=target_words,
        max_words=max_words,
        pages=page_map,
    )
    payload = source_bytes if source_bytes is not None else text.encode("utf-8")
    source = {
        "schema_version": CHUNK_SCHEMA_VERSION,
        "source_path": source_path,
        "source_name": source_name,
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "character_count": len(text),
        "word_count": len(text.split()),
        "section_count": len(sections),
        "chunk_count": len(chunks),
        "metadata": metadata or {},
        "sections": [
            {
                "section": section.section,
                "order": section.order,
                "word_count": len(section.text.split()),
            }
            for section in sections
        ],
        "chunks": chunks,
    }
    return source, chunks
