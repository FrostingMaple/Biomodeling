"""Extract embedded raster images from a PDF using the bundled runtime."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    source = Path(sys.argv[1])
    assets_dir = Path(sys.argv[2])
    assets_dir.mkdir(parents=True, exist_ok=True)

    from pypdf import PdfReader

    reader = PdfReader(str(source))
    images = []
    index = 0
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            page_images = list(page.images)
        except Exception:
            continue
        for image in page_images:
            index += 1
            original = Path(getattr(image, "name", "") or "image.png")
            suffix = original.suffix.lower() or ".png"
            filename = "pdf-image-" + format(index, "03d") + suffix
            try:
                (assets_dir / filename).write_bytes(image.data)
            except Exception:
                index -= 1
                continue
            images.append({"page": page_number, "file": filename})

    sys.stdout.write(json.dumps({"images": images}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
