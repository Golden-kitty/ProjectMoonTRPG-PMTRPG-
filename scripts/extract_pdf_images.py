import argparse
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

import fitz  # pymupdf


@dataclass
class ExtractedImage:
    page: int
    index: int
    ext: str
    path: Path


def sha1(data: bytes) -> str:
    h = hashlib.sha1()
    h.update(data)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, help="PDF path")
    ap.add_argument("--out", default="assets/pdf_images", help="Output directory")
    ap.add_argument("--min-bytes", type=int, default=2048, help="Skip tiny images below this size")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))

    seen_hashes: set[str] = set()
    extracted: list[ExtractedImage] = []
    skipped_dupe = 0
    skipped_small = 0

    for page_idx in range(doc.page_count):
        page_no = page_idx + 1
        page = doc[page_idx]
        imgs = page.get_images(full=True)
        for j, img in enumerate(imgs, start=1):
            xref = img[0]
            base = doc.extract_image(xref)
            data = base.get("image", b"")
            if not data or len(data) < args.min_bytes:
                skipped_small += 1
                continue

            h = sha1(data)
            if h in seen_hashes:
                skipped_dupe += 1
                continue
            seen_hashes.add(h)

            ext = base.get("ext", "bin")
            # Normalize common ext
            if ext.lower() == "jpeg":
                ext = "jpg"
            ext = ext.lower()

            fname = f"page_{page_no:03d}_img_{j:02d}.{ext}"
            out_path = out_dir / fname
            out_path.write_bytes(data)
            extracted.append(ExtractedImage(page=page_no, index=j, ext=ext, path=out_path))

    # Summary
    print("pdf_pages", doc.page_count)
    print("images_extracted", len(extracted))
    print("skipped_dupe", skipped_dupe)
    print("skipped_small", skipped_small)
    print("out_dir", os.path.abspath(out_dir))


if __name__ == "__main__":
    main()

