"""Render every PDF page and build a compact contact sheet for visual review."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


def render(pdf_path: Path, output_dir: Path, dpi: int, columns: int, thumb_width: int) -> dict:
    pdf_path = pdf_path.resolve()
    output_dir = output_dir.resolve()
    if not pdf_path.is_file():
        raise ValueError(f"PDF does not exist: {pdf_path}")
    if dpi <= 0 or columns <= 0 or thumb_width <= 0:
        raise ValueError("dpi, columns, and thumb-width must be positive")

    output_dir.mkdir(parents=True, exist_ok=True)
    for existing in [*output_dir.glob("page-*.png"), output_dir / "contact-sheet.png"]:
        if existing.is_file():
            existing.unlink()

    document = fitz.open(pdf_path)
    page_paths: list[Path] = []
    thumbnails: list[Image.Image] = []
    matrix = fitz.Matrix(dpi / 72, dpi / 72)
    try:
        for index, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            page_path = output_dir / f"page-{index:03d}.png"
            pixmap.save(page_path)
            page_paths.append(page_path)

            image = Image.open(page_path).convert("RGB")
            thumb_height = max(1, round(image.height * thumb_width / image.width))
            thumbnails.append(image.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS))
    finally:
        document.close()

    if not thumbnails:
        raise ValueError(f"PDF has no pages: {pdf_path}")
    label_height = 28
    gap = 18
    cell_width = thumb_width + gap
    cell_height = max(image.height for image in thumbnails) + label_height + gap
    rows = math.ceil(len(thumbnails) / columns)
    sheet = Image.new("RGB", (columns * cell_width + gap, rows * cell_height + gap), "white")
    draw = ImageDraw.Draw(sheet)
    for index, image in enumerate(thumbnails, start=1):
        row, column = divmod(index - 1, columns)
        x = gap + column * cell_width
        y = gap + row * cell_height
        sheet.paste(image, (x, y))
        draw.text((x, y + image.height + 5), f"Page {index}", fill="black")
    contact_sheet = output_dir / "contact-sheet.png"
    sheet.save(contact_sheet, optimize=True)
    return {
        "status": "PASS",
        "pdf": str(pdf_path),
        "page_count": len(page_paths),
        "dpi": dpi,
        "page_files": [str(path) for path in page_paths],
        "contact_sheet": str(contact_sheet),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--dpi", type=int, default=144)
    parser.add_argument("--columns", type=int, default=3)
    parser.add_argument("--thumb-width", type=int, default=380)
    args = parser.parse_args()
    print(
        json.dumps(
            render(args.pdf, args.output_dir, args.dpi, args.columns, args.thumb_width),
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
