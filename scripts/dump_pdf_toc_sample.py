from pathlib import Path

import fitz  # pymupdf


def main() -> None:
    pdf = Path("originFab/Project Moon Trpg Rule Book V1.8.4.pdf")
    doc = fitz.open(str(pdf))
    toc = doc.get_toc(simple=True)

    out_lines: list[str] = []
    for lvl, title, page in toc[:50]:
        # show both raw title and a safe escaped form to detect U+FFFD etc.
        escaped = title.encode("unicode_escape", errors="backslashreplace").decode("ascii")
        out_lines.append(f"{lvl}\t{page}\t{title}\t{escaped}")

    Path("output_toc_sample.txt").write_text("\n".join(out_lines), encoding="utf-8")
    print("wrote output_toc_sample.txt")


if __name__ == "__main__":
    main()

