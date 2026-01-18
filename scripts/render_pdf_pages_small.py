import argparse
import os
from pathlib import Path

import fitz  # pymupdf


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, help="PDF path")
    ap.add_argument("--out", default="assets/pdf_pages_small", help="Output directory")
    ap.add_argument("--max-width", type=int, default=900, help="Max image width in px")
    ap.add_argument("--start", type=int, default=1, help="Start page (1-based, inclusive)")
    ap.add_argument("--end", type=int, default=0, help="End page (1-based, inclusive). 0 means last page.")
    ap.add_argument("--format", choices=["jpg", "png"], default="jpg", help="Output format")
    ap.add_argument("--jpg-quality", type=int, default=75, help="JPG quality (1-100)")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    start = max(1, args.start)
    end = args.end if args.end and args.end >= start else doc.page_count
    end = min(end, doc.page_count)

    rendered = 0
    for page_idx in range(start - 1, end):
        page_no = page_idx + 1
        page = doc[page_idx]

        rect = page.rect
        scale = args.max_width / rect.width if rect.width else 1.0
        scale = min(scale, 4.0)  # guardrail
        mat = fitz.Matrix(scale, scale)

        pix = page.get_pixmap(matrix=mat, alpha=False)

        fname = f"page_{page_no:03d}.{args.format}"
        out_path = out_dir / fname
        if args.format == "jpg":
            out_path.write_bytes(pix.tobytes("jpeg", jpg_quality=args.jpg_quality))
        else:
            out_path.write_bytes(pix.tobytes("png"))
        rendered += 1

    print("pdf_pages", doc.page_count)
    print("rendered_pages", rendered)
    print("range", f"{start}-{end}")
    print("out_dir", os.path.abspath(out_dir))


if __name__ == "__main__":
    main()

