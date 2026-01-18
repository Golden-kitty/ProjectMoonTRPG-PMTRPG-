import argparse
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup


TABLE_BLOCK_RE = re.compile(r"<table\b[\s\S]*?</table\s*>", flags=re.I)


def _norm_cell_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse whitespace inside lines
    text = re.sub(r"[ \t]+", " ", text)
    text = "\n".join([ln.strip() for ln in text.split("\n")]).strip()
    # Use <br> inside pipe tables (GitHub supports it)
    text = text.replace("\n", "<br>")
    # Escape pipes
    text = text.replace("|", r"\|")
    return text


@dataclass
class SpanCell:
    remaining: int
    text: str


def html_table_to_pipe(table_html: str) -> str:
    soup = BeautifulSoup(table_html, "html5lib")
    table = soup.find("table")
    if table is None:
        return table_html

    # Build grid with rowspan/colspan expanded (repeat content to preserve info)
    span_map: dict[int, SpanCell] = {}
    grid: list[list[str]] = []
    header_hint = False

    for tr in table.find_all("tr"):
        row: list[str] = []
        col = 0

        def fill_spans():
            nonlocal col
            while col in span_map:
                row.append(span_map[col].text)
                span_map[col].remaining -= 1
                if span_map[col].remaining <= 0:
                    del span_map[col]
                col += 1

        fill_spans()

        cells = tr.find_all(["td", "th"])
        if tr.find("th") is not None:
            header_hint = True

        for cell in cells:
            fill_spans()
            raw = cell.get_text("\n", strip=True)
            text = _norm_cell_text(raw)
            try:
                rowspan = int(cell.get("rowspan", 1) or 1)
            except ValueError:
                rowspan = 1
            try:
                colspan = int(cell.get("colspan", 1) or 1)
            except ValueError:
                colspan = 1

            if colspan < 1:
                colspan = 1
            if rowspan < 1:
                rowspan = 1

            for i in range(colspan):
                row.append(text)
                if rowspan > 1:
                    span_map[col + i] = SpanCell(remaining=rowspan - 1, text=text)
            col += colspan

        fill_spans()
        grid.append(row)

    if not grid:
        return ""

    max_cols = max(len(r) for r in grid)
    for r in grid:
        if len(r) < max_cols:
            r.extend([""] * (max_cols - len(r)))

    # Extract title-like rows that cannot be represented in pipe tables (merged cells).
    # If a row has a single meaningful value (others empty or same), hoist it as bold text above.
    titles: list[str] = []
    body: list[list[str]] = []
    for r in grid:
        non_empty = [c for c in r if c.strip()]
        uniq = sorted(set(non_empty))
        if len(non_empty) == 1:
            titles.append(non_empty[0])
            continue
        if len(uniq) == 1 and len(non_empty) >= 2:
            titles.append(uniq[0])
            continue
        body.append(r)

    if not body:
        # Only titles: render as paragraphs
        return "\n\n".join([f"**{t}**" for t in titles]) + "\n"

    # Decide header row: use first row as header (common in exports), unless it's clearly data-only
    header = body[0]
    rows = body[1:]

    # If header_hint is false but header is short phrases and not many empties, still ok.
    # Create separator
    sep = ["---"] * max_cols

    def pipe_row(r: list[str]) -> str:
        return "| " + " | ".join(r) + " |"

    out_lines: list[str] = []
    for t in titles:
        out_lines.append(f"**{t}**")
        out_lines.append("")

    out_lines.append(pipe_row(header))
    out_lines.append(pipe_row(sep))
    for r in rows:
        out_lines.append(pipe_row(r))

    return "\n".join(out_lines) + "\n"


def rebuild_file(path: str) -> bool:
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()

    matches = list(TABLE_BLOCK_RE.finditer(src))
    if not matches:
        return False

    out = []
    last = 0
    for m in matches:
        out.append(src[last : m.start()])
        out.append(html_table_to_pipe(m.group(0)))
        last = m.end()
    out.append(src[last:])
    new = "".join(out)

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="Target markdown file to rebuild HTML tables in-place")
    args = ap.parse_args()

    changed = rebuild_file(args.file)
    print("changed" if changed else "no_tables")


if __name__ == "__main__":
    main()

