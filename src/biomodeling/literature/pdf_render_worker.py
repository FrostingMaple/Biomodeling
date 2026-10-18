"""Render every PDF page to PNG using the bundled Python runtime."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    source = Path(sys.argv[1])
    assets_dir = Path(sys.argv[2])
    assets_dir.mkdir(parents=True, exist_ok=True)

    import pypdfium2

    pages = []
    document = pypdfium2.PdfDocument(str(source))
    try:
        for index, page in enumerate(document, start=1):
            bitmap = page.render(scale=2.0)
            image = bitmap.to_pil()
            filename = "page-" + format(index, "03d") + ".png"
            image.save(assets_dir / filename)
            pages.append({"page": index, "file": filename})
            image.close()
            page.close()
    finally:
        document.close()

    sys.stdout.write(json.dumps({"pages": pages}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
