"""Convert inventoried source-content pipe tables to canonical HTML.

The default mode is a read-only dry run.  ``--apply`` is required before any
source file is rewritten.  Only records frozen in the inventory with
``scope=source-content`` and ``representation=markdown-pipe`` are eligible.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import markdown

from generate_table_inventory import is_pipe_separator, split_pipe_row


PARAGRAPH_RE = re.compile(r"^<p>(.*)</p>$", re.DOTALL)


@dataclass
class Conversion:
    table_id: str
    path: str
    line: int
    rows: int
    columns: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.table_id,
            "path": self.path,
            "line": self.line,
            "rows": self.rows,
            "columns": self.columns,
        }


def render_inline(source: str) -> str:
    """Render Markdown cell content without wrapping it in a paragraph."""

    rendered = markdown.markdown(source, extensions=[], output_format="html").strip()
    match = PARAGRAPH_RE.fullmatch(rendered)
    return match.group(1) if match else rendered


def alignment_class(separator: str) -> str | None:
    stripped = separator.strip()
    if stripped.startswith(":") and stripped.endswith(":"):
        return "align-center"
    if stripped.endswith(":"):
        return "align-right"
    if stripped.startswith(":"):
        return "align-left"
    return None


def cell_tag(tag: str, value: str, *, scope: str | None, css_class: str | None) -> str:
    attrs: list[str] = []
    if scope:
        attrs.append(f'scope="{scope}"')
    if css_class:
        attrs.append(f'class="{css_class}"')
    suffix = " " + " ".join(attrs) if attrs else ""
    return f"      <{tag}{suffix}>{render_inline(value)}</{tag}>"


def convert_block(lines: list[str], table_id: str) -> tuple[str, int, int]:
    if len(lines) < 2:
        raise ValueError("pipe table must contain a header and separator")
    header = split_pipe_row(lines[0])
    separators = split_pipe_row(lines[1])
    if header is None or separators is None or not is_pipe_separator(lines[1]):
        raise ValueError("inventory range no longer starts with a pipe-table header")
    if len(header) != len(separators):
        raise ValueError("header and alignment separator use different column counts")
    body: list[list[str]] = []
    for index, line in enumerate(lines[2:], start=3):
        row = split_pipe_row(line)
        if row is None:
            raise ValueError(f"line {index} is not a pipe-table row")
        if len(row) != len(header):
            raise ValueError(
                f"line {index} has {len(row)} cells; expected {len(header)}"
            )
        body.append(row)

    alignments = [alignment_class(value) for value in separators]
    output = [f'<table class="pmtrpg-table" data-table-id="{table_id}">', "  <thead>", "    <tr>"]
    output.extend(
        cell_tag("th", value, scope="col", css_class=alignments[index])
        for index, value in enumerate(header)
    )
    output.extend(["    </tr>", "  </thead>", "  <tbody>"])
    for row in body:
        output.append("    <tr>")
        output.extend(
            cell_tag("td", value, scope=None, css_class=alignments[index])
            for index, value in enumerate(row)
        )
        output.append("    </tr>")
    output.extend(["  </tbody>", "</table>"])
    return "\n".join(output), 1 + len(body), len(header)


def eligible_items(inventory: dict[str, Any], selected_paths: set[str]) -> list[dict[str, Any]]:
    items = [
        item
        for item in inventory["tables"]
        if item["scope"] == "source-content"
        and item["representation"] == "markdown-pipe"
        and (not selected_paths or item["path"] in selected_paths)
    ]
    return sorted(items, key=lambda item: (item["path"], item["line"]))


def execute(
    repo_root: Path,
    inventory: dict[str, Any],
    *,
    apply: bool,
    selected_paths: set[str] | None = None,
) -> list[Conversion]:
    selected_paths = selected_paths or set()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in eligible_items(inventory, selected_paths):
        grouped[item["path"]].append(item)

    conversions: list[Conversion] = []
    rewrites: dict[Path, str] = {}
    for relative, items in grouped.items():
        path = repo_root / relative
        source = path.read_text(encoding="utf-8")
        lines = source.splitlines()
        trailing_newline = source.endswith(("\n", "\r"))
        for item in sorted(items, key=lambda value: value["line"], reverse=True):
            start = item["line"] - 1
            end = item["end_line"]
            block, rows, columns = convert_block(lines[start:end], item["id"])
            if rows != item["rows"] or columns != item["columns"]:
                raise ValueError(
                    f"{relative}:{item['line']} structure differs from inventory: "
                    f"observed {rows}x{columns}, expected {item['rows']}x{item['columns']}"
                )
            lines[start:end] = block.splitlines()
            conversions.append(
                Conversion(item["id"], relative, item["line"], rows, columns)
            )
        rewritten = "\n".join(lines) + ("\n" if trailing_newline else "")
        rewrites[path] = rewritten

    if apply:
        for path, rewritten in rewrites.items():
            path.write_text(rewritten, encoding="utf-8", newline="\n")
    return sorted(conversions, key=lambda item: (item.path, item.line))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("docs/engineering/table-inventory.json"),
    )
    parser.add_argument("--path", action="append", default=[], help="Convert only this repo-relative path")
    parser.add_argument("--apply", action="store_true", help="Write changes; omission is a dry run")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    inventory_path = args.inventory.resolve()
    repo_root = inventory_path.parents[2]
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    conversions = execute(
        repo_root,
        inventory,
        apply=args.apply,
        selected_paths=set(args.path),
    )
    payload = {
        "mode": "apply" if args.apply else "dry-run",
        "status": "PASS",
        "converted_tables": len(conversions),
        "converted_documents": len({item.path for item in conversions}),
        "tables": [item.as_dict() for item in conversions],
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({key: payload[key] for key in ("mode", "status", "converted_tables", "converted_documents")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
