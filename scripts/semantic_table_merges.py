from __future__ import annotations

import re

MERGE_COMMENT_RE = re.compile(r"<!--\s*pmtrpg-table-merge:\s*(?P<spec>.+?)\s*-->")


def _split_row(line: str) -> list[str] | None:
    text = line.strip()
    if not text.startswith("|") or text.count("|") < 2:
        return None
    return [cell.strip() for cell in text.strip("|").split("|")]


def _is_separator(line: str) -> bool:
    cells = _split_row(line)
    if not cells:
        return False

    for cell in cells:
        token = cell.replace(":", "").replace("-", "").strip()
        if token or "-" not in cell:
            return False
    return True


def _parse_merge_spec(spec: str) -> dict[str, int]:
    merges: dict[str, int] = {}
    for part in spec.split(","):
        item = part.strip()
        if not item or "=" not in item:
            continue
        label, raw_span = item.split("=", 1)
        label = label.strip()
        raw_span = raw_span.strip()
        if not label or not raw_span.isdigit():
            continue
        merges[label] = int(raw_span)
    return merges


def _build_html_table(rows: list[list[str]], merges: dict[str, int]) -> list[str]:
    html_lines = ["<table>"]
    for row in rows:
        label = row[0] if row else ""
        span = merges.get(label)
        if span and len(row) == span + 1 and row[1]:
            trailing = row[2:]
            if all(cell == "" for cell in trailing) or all(cell == row[1] for cell in trailing):
                html_lines.append(
                    f'<tr><td>{row[0]}</td><td colspan="{span}">{row[1]}</td></tr>'
                )
                continue

        cells = "".join(f"<td>{cell}</td>" for cell in row)
        html_lines.append(f"<tr>{cells}</tr>")
    html_lines.append("</table>")
    return html_lines


def apply_semantic_table_merges(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0

    while i < len(lines):
        match = MERGE_COMMENT_RE.fullmatch(lines[i].strip())
        if not match:
            out.append(lines[i])
            i += 1
            continue

        merges = _parse_merge_spec(match.group("spec"))
        if not merges or i + 2 >= len(lines):
            out.append(lines[i])
            i += 1
            continue

        table_start = i + 1
        if _split_row(lines[table_start]) is None or not _is_separator(lines[table_start + 1]):
            out.append(lines[i])
            i += 1
            continue

        table_end = table_start
        while table_end < len(lines) and _split_row(lines[table_end]) is not None:
            table_end += 1

        block = lines[table_start:table_end]
        rows = [_split_row(line) for line in block]
        if any(row is None for row in rows):
            out.append(lines[i])
            i += 1
            continue

        data_rows = [rows[0], *rows[2:]]  # type: ignore[list-item]
        out.extend(_build_html_table(data_rows, merges))
        i = table_end

    return "\n".join(out) + ("\n" if text.endswith("\n") else "")
