"""Convert prepared literature sources into Markdown with local assets."""

from __future__ import annotations

import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .doi import looks_like_doi, resolve_doi
from .extraction import SourceError, read_source_document
from .io_utils import write_json, write_text
from .ocr import OcrUnavailable, detect_backend, ocr_image

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"}
_OCR_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


@dataclass
class Asset:
    asset_id: str
    path: Path
    source: str
    kind: str
    page: int | None = None
    caption: str = ""
    ocr_text: str = ""
    ocr_backend: str = ""
    warning: str = ""


@dataclass
class ExportResult:
    markdown: str
    assets: list[Asset] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def convert_source(
    source: str | Path,
    out_dir: Path,
    *,
    extract_images: bool = True,
    ocr_mode: str = "auto",
    ocr_lang: str = "eng",
    ocr_backend: str = "auto",
    image_mode: str = "page,embedded",
    timeout: int = 45,
) -> ExportResult:
    """Convert a local file or DOI into Markdown plus local assets."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = out_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    assets: list[Asset] = []
    local_path: Path | None = None

    value = str(source)
    if looks_like_doi(value) and not Path(value).is_file():
        prepared, _chunks, document = resolve_doi(value, timeout=timeout)
        text = document.text
        metadata = dict(document.metadata)
        pages = document.pages
        source_name = str(prepared.get("source_name", value))
        suffix = ".xml"
        xml_reference = text if metadata.get("format") in {"jats_xml", "bioc_xml"} else ""
    else:
        local_path = Path(value)
        if not local_path.is_file():
            raise SourceError(f"Source file not found: {local_path}")
        document = read_source_document(local_path)
        text = document.text
        metadata = dict(document.metadata)
        pages = document.pages
        source_name = local_path.name
        suffix = local_path.suffix.lower()

    markdown_body = markdown_from_text(text)

    if extract_images:
        modes = {item.strip() for item in image_mode.split(",") if item.strip()}
        if local_path is not None and suffix == ".docx":
            assets.extend(_extract_docx_images(local_path, assets_dir, warnings))
        elif local_path is not None and suffix == ".pdf":
            if "page" in modes:
                assets.extend(_render_pdf_pages(local_path, assets_dir, warnings))
            if "embedded" in modes:
                assets.extend(_extract_pdf_images(local_path, assets_dir, warnings))
        elif local_path is not None and suffix in {".xml", ".jats"}:
            assets.extend(_reference_jats_images(local_path, assets_dir, warnings))
        elif xml_reference:
            assets.extend(
                reference_jats_images_from_text(
                    xml_reference,
                    assets_dir,
                    warnings,
                    source_label=source_name,
                )
            )

    if ocr_mode != "never" and assets:
        _run_ocr(assets, lang=ocr_lang, backend=ocr_backend, warnings=warnings)

    captions = metadata.get("figure_captions")
    if isinstance(captions, list) and captions:
        markdown_body += "\n\n## Figure Captions\n\n"
        for caption in captions:
            markdown_body += "- " + str(caption) + "\n"
        warnings.append(
            "Figure captions were captured from the source XML, but the corresponding image files were not downloaded."
        )

    if assets:
        markdown_body += "\n\n## Extracted Assets\n\n"
        for asset in assets:
            if asset.kind == "remote_reference" or not asset.path.exists():
                caption = asset.caption or asset.asset_id
                markdown_body += "- Figure reference (not downloaded): `" + asset.source + "`"
                if caption:
                    markdown_body += " - " + caption
                markdown_body += "\n"
                continue
            relative = asset.path.relative_to(out_dir).as_posix()
            title = asset.caption or asset.asset_id
            markdown_body += "![" + title + "](" + relative + ")\n\n"
            if asset.ocr_text:
                markdown_body += "**OCR text (" + asset.ocr_backend + "):**\n\n" + asset.ocr_text + "\n\n"

    manifest = {
        "source": source_name,
        "metadata": metadata,
        "warnings": warnings,
        "assets": [
            {
                "asset_id": asset.asset_id,
                "file": asset.path.relative_to(out_dir).as_posix() if asset.path.exists() else "",
                "source": asset.source,
                "kind": asset.kind,
                "page": asset.page,
                "caption": asset.caption,
                "ocr_backend": asset.ocr_backend,
                "ocr_characters": len(asset.ocr_text),
                "warning": asset.warning,
            }
            for asset in assets
        ],
    }
    write_json(out_dir / "image_manifest.json", manifest)
    write_text(out_dir / "document.md", markdown_body)
    return ExportResult(markdown=markdown_body, assets=assets, warnings=warnings, metadata=metadata)


def markdown_from_text(text: str) -> str:
    """Render prepared text as readable Markdown."""
    lines: list[str] = []
    for raw in text.split("\n"):
        stripped = raw.strip()
        if not stripped:
            lines.append("")
            continue
        if stripped.startswith("#"):
            lines.append(stripped)
            continue
        if stripped.startswith("TABLE_ROW:"):
            cells = [cell.strip() for cell in stripped[len("TABLE_ROW:"):].split("|")]
            cells = [cell for cell in cells if cell]
            if cells:
                lines.append("| " + " | ".join(cells) + " |")
            continue
        if len(stripped.split()) <= 8 and re.fullmatch(r"[A-Z][A-Za-z0-9 ,/()\-]{2,60}", stripped):
            if stripped.lower() in {
                "abstract", "introduction", "methods", "model", "parameters",
                "results", "discussion", "conclusion", "conclusions",
            }:
                lines.append("## " + stripped)
                continue
        lines.append(stripped)
    return "\n".join(lines).strip() + "\n"


def _extract_docx_images(path: Path, assets_dir: Path, warnings: list[str]) -> list[Asset]:
    assets: list[Asset] = []
    try:
        with zipfile.ZipFile(path) as archive:
            names = sorted(name for name in archive.namelist() if name.startswith("word/media/"))
            index = 0
            for name in names:
                suffix = Path(name).suffix.lower()
                if suffix not in IMAGE_SUFFIXES:
                    continue
                index += 1
                asset_id = "docx-image-" + format(index, "03d")
                target = assets_dir / (asset_id + suffix)
                try:
                    target.write_bytes(archive.read(name))
                except KeyError:
                    continue
                assets.append(Asset(asset_id=asset_id, path=target, source=name, kind="embedded"))
    except zipfile.BadZipFile as exc:
        warnings.append("Could not read DOCX archive: " + str(exc))
    return assets


def reference_jats_images_from_text(
    text: str,
    assets_dir: Path,
    warnings: list[str],
    *,
    source_label: str,
) -> list[Asset]:
    """Record figure references from JATS-like XML text without downloading files."""
    assets: list[Asset] = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return assets
    index = 0
    for figure in root.iter():
        if figure.tag.rsplit("}", 1)[-1] != "fig":
            continue
        caption = ""
        for child in figure.iter():
            if child.tag.rsplit("}", 1)[-1] == "caption":
                caption = " ".join("".join(child.itertext()).split())
                break
        for graphic in figure.iter():
            if graphic.tag.rsplit("}", 1)[-1] not in {"graphic", "inline-graphic", "media"}:
                continue
            href = next((value for key, value in graphic.attrib.items() if key.endswith("href")), "")
            if not href:
                continue
            index += 1
            asset_id = "figure-" + format(index, "03d")
            assets.append(
                Asset(
                    asset_id=asset_id,
                    path=assets_dir / asset_id,
                    source=href,
                    kind="remote_reference",
                    caption=caption,
                    warning="Figure reference recorded from XML; download the image from the publisher or PMC to bundle it.",
                )
            )
    if assets:
        warnings.append(
            "Figure files are referenced but not downloaded for " + source_label
            + "; fetch them from the publisher or PMC when the actual image files are required."
        )
    return assets


def _reference_jats_images(path: Path, assets_dir: Path, warnings: list[str]) -> list[Asset]:
    assets: list[Asset] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        warnings.append("Could not parse JATS figures: " + str(exc))
        return assets

    index = 0
    for graphic in root.iter():
        tag = graphic.tag.rsplit("}", 1)[-1]
        if tag not in {"graphic", "inline-graphic", "media"}:
            continue
        href = next((value for key, value in graphic.attrib.items() if key.endswith("href")), "")
        if not href:
            continue
        index += 1
        asset_id = "jats-image-" + format(index, "03d")
        assets.append(
            Asset(
                asset_id=asset_id,
                path=assets_dir / asset_id,
                source=href,
                kind="remote_reference",
                warning="Remote JATS image reference recorded; download it from the publisher or PMC to bundle it.",
            )
        )
    if index:
        warnings.append(
            "JATS image files are referenced but not downloaded; fetch them from the publisher or PMC when you need the actual figure files."
        )
    return assets


def _render_pdf_pages(path: Path, assets_dir: Path, warnings: list[str]) -> list[Asset]:
    payload = _run_pdf_worker("pdf_render_worker.py", path, assets_dir, warnings, "render PDF pages")
    assets: list[Asset] = []
    for item in payload.get("pages", []):
        page = int(item["page"])
        asset_id = "page-" + format(page, "03d")
        assets.append(
            Asset(
                asset_id=asset_id,
                path=assets_dir / item["file"],
                source=path.name,
                kind="page",
                page=page,
                caption="Page " + str(page),
            )
        )
    return assets


def _extract_pdf_images(path: Path, assets_dir: Path, warnings: list[str]) -> list[Asset]:
    payload = _run_pdf_worker("pdf_images_worker.py", path, assets_dir, warnings, "extract embedded PDF images")
    assets: list[Asset] = []
    for index, item in enumerate(payload.get("images", []), start=1):
        asset_id = "pdf-image-" + format(index, "03d")
        assets.append(
            Asset(
                asset_id=asset_id,
                path=assets_dir / item["file"],
                source=path.name,
                kind="embedded",
                page=item.get("page"),
            )
        )
    return assets


def _run_pdf_worker(
    worker_name: str,
    path: Path,
    assets_dir: Path,
    warnings: list[str],
    action: str,
) -> dict[str, Any]:
    python = _bundled_python()
    worker = Path(__file__).with_name(worker_name)
    if python is None or not worker.is_file():
        warnings.append("Bundled PDF runtime is unavailable; skipped: " + action + ".")
        return {}
    try:
        completed = subprocess.run(
            [str(python), str(worker), str(path), str(assets_dir)],
            capture_output=True,
            check=False,
            timeout=900,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        warnings.append("Could not " + action + ": " + str(exc))
        return {}
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        warnings.append("Could not " + action + ": " + (detail or "unknown error"))
        return {}
    try:
        payload = json.loads(completed.stdout.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        warnings.append("Worker returned invalid output while attempting to " + action + ".")
        return {}
    return payload if isinstance(payload, dict) else {}


def _run_ocr(assets: list[Asset], *, lang: str, backend: str, warnings: list[str]) -> None:
    available = detect_backend(backend)
    if available is None:
        warnings.append(
            "No local OCR backend detected; assets were saved without OCR text. "
            "Supported backends: tesseract, pytesseract, easyocr, paddleocr, rapidocr."
        )
        return
    for asset in assets:
        if asset.kind == "remote_reference" or not asset.path.exists():
            continue
        if asset.path.suffix.lower() not in _OCR_IMAGE_SUFFIXES:
            continue
        try:
            result = ocr_image(asset.path, lang=lang, preferred=backend)
        except OcrUnavailable as exc:
            warnings.append(str(exc))
            return
        asset.ocr_text = result.text
        asset.ocr_backend = result.backend
        if result.warning:
            asset.warning = result.warning


def _bundled_python() -> Path | None:
    candidate = (
        Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime"
        / "dependencies" / "python" / "python.exe"
    )
    return candidate if candidate.is_file() else None
