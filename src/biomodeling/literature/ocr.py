"""Optional OCR backends for extracted document images.

OCR is deliberately optional. The converter detects local engines at runtime
and reports a warning when none is available; it never downloads models or
installs packages by itself.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OcrResult:
    text: str
    backend: str
    warning: str = ""


class OcrUnavailable(RuntimeError):
    """Raised when no supported OCR backend is available."""


def detect_backend(preferred: str = "auto") -> str | None:
    """Return the name of the first available local OCR backend."""
    candidates = ["tesseract", "pytesseract", "easyocr", "paddleocr", "rapidocr"]
    if preferred != "auto":
        candidates = [preferred] + [name for name in candidates if name != preferred]
    for candidate in candidates:
        if candidate == "tesseract" and shutil.which("tesseract"):
            return candidate
        if candidate == "pytesseract" and importlib.util.find_spec("pytesseract"):
            return candidate
        if candidate == "easyocr" and importlib.util.find_spec("easyocr"):
            return candidate
        if candidate == "paddleocr" and importlib.util.find_spec("paddleocr"):
            return candidate
        if candidate == "rapidocr" and (
            importlib.util.find_spec("rapidocr_onnxruntime") or importlib.util.find_spec("rapidocr")
        ):
            return candidate
    return None


def ocr_image(image_path: Path, *, lang: str = "eng", preferred: str = "auto") -> OcrResult:
    """Run OCR on one image with the first available backend."""
    backend = detect_backend(preferred)
    if backend is None:
        raise OcrUnavailable(
            "No local OCR backend was found. Install one of: tesseract, pytesseract, "
            "easyocr, paddleocr, or rapidocr."
        )

    if backend == "tesseract":
        return _ocr_tesseract_cli(image_path, lang=lang)
    if backend == "pytesseract":
        return _ocr_pytesseract(image_path, lang=lang)
    if backend == "easyocr":
        return _ocr_easyocr(image_path, lang=lang)
    if backend == "paddleocr":
        return _ocr_paddleocr(image_path, lang=lang)
    if backend == "rapidocr":
        return _ocr_rapidocr(image_path, lang=lang)
    raise OcrUnavailable(f"Unsupported OCR backend: {backend}")


def _ocr_tesseract_cli(path: Path, *, lang: str) -> OcrResult:
    executable = shutil.which("tesseract")
    if not executable:
        raise OcrUnavailable("tesseract executable disappeared from PATH.")
    completed = subprocess.run(
        [executable, str(path), "stdout", "-l", lang],
        capture_output=True,
        check=False,
        timeout=300,
    )
    text = completed.stdout.decode("utf-8", errors="replace").strip()
    warning = "" if completed.returncode == 0 else completed.stderr.decode("utf-8", errors="replace").strip()
    return OcrResult(text=text, backend="tesseract", warning=warning)


def _ocr_pytesseract(path: Path, *, lang: str) -> OcrResult:
    import pytesseract  # type: ignore[import-not-found]
    from PIL import Image

    with Image.open(path) as image:
        text = pytesseract.image_to_string(image, lang=lang)
    return OcrResult(text=text.strip(), backend="pytesseract")


def _ocr_easyocr(path: Path, *, lang: str) -> OcrResult:
    import easyocr  # type: ignore[import-not-found]

    reader = easyocr.Reader([lang if len(lang) <= 3 else "en"], gpu=False)
    lines = reader.readtext(str(path), detail=0, paragraph=True)
    return OcrResult(text="\n".join(str(line) for line in lines).strip(), backend="easyocr")


def _ocr_paddleocr(path: Path, *, lang: str) -> OcrResult:
    from paddleocr import PaddleOCR  # type: ignore[import-not-found]

    engine = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
    result = engine.ocr(str(path), cls=True)
    texts: list[str] = []
    for page in result or []:
        for line in page or []:
            if len(line) >= 2 and line[1]:
                texts.append(str(line[1][0]))
    return OcrResult(text="\n".join(texts).strip(), backend="paddleocr")


def _ocr_rapidocr(path: Path, *, lang: str) -> OcrResult:
    try:
        from rapidocr_onnxruntime import RapidOCR  # type: ignore[import-not-found]
    except ImportError:
        from rapidocr import RapidOCR  # type: ignore[import-not-found,no-redef]

    engine = RapidOCR()
    result, _ = engine(str(path))
    lines = [str(item[1]) for item in result or [] if len(item) >= 2]
    return OcrResult(text="\n".join(lines).strip(), backend="rapidocr")
