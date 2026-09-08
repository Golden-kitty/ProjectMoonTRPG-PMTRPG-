"""Validate canonical HTML tables and compare their structural signatures.

This tool has two independent responsibilities:

* ``structural`` compares the current source tree with a frozen inventory and
  detects missing/extra tables or changes to rows, columns, spans, nesting and
  images.
* ``canonical`` checks the target HTML contract used by the conversion plan.

The validator is read-only.  It never rewrites Markdown or HTML.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from generate_table_inventory import build_inventory, mask_markdown_code


TABLE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ALLOWED_TABLE_ATTRS = {"class", "data-table-id"}
ALLOWED_CELL_ATTRS = {"class", "colspan", "rowspan", "scope"}
ALLOWED_TAGS = {
    "a",
    "b",
    "br",
    "caption",
    "code",
    "em",
    "img",
    "p",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
}
FORBIDDEN_TAGS = {"embed", "iframe", "object", "script", "style", "svg"}


@dataclass
class Issue:
    code: str
    path: str
    line: int
    table_ordinal: int | None
    message: str
    severity: str = "error"

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "path": self.path,
            "line": self.line,
            "table_ordinal": self.table_ordinal,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class TableState:
    ordinal: int
    line: int
    attrs: dict[str, str]
    row_index: int = -1
    active_row: bool = False
    row_widths: list[int] = field(default_factory=list)
    occupied: set[tuple[int, int]] = field(default_factory=set)
    current_col: int = 0
    open_cells: list[str] = field(default_factory=list)


def parse_positive_span(value: str | None) -> int | None:
    if value is None:
        return 1
    if not value.isdigit():
        return None
    parsed = int(value)
    return parsed if parsed > 0 else None


class CanonicalHTMLParser(HTMLParser):
    def __init__(self, markdown_path: Path, repo_root: Path) -> None:
        super().__init__(convert_charrefs=False)
        self.markdown_path = markdown_path
        self.repo_root = repo_root
        self.relative = markdown_path.relative_to(repo_root).as_posix()
        self.issues: list[Issue] = []
        self.tables: list[TableState] = []
        self.table_stack: list[TableState] = []

    @property
    def current(self) -> TableState | None:
        return self.table_stack[-1] if self.table_stack else None

    def issue(self, code: str, message: str, line: int | None = None) -> None:
        current = self.current
        self.issues.append(
            Issue(
                code=code,
                path=self.relative,
                line=line or self.getpos()[0],
                table_ordinal=current.ordinal if current else None,
                message=message,
            )
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {key.lower(): value or "" for key, value in attrs}
        if tag == "table":
            state = TableState(
                ordinal=len(self.tables) + 1,
                line=self.getpos()[0],
                attrs=attr_map,
            )
            self.tables.append(state)
            self.table_stack.append(state)
            self._validate_table_attrs(state)
            return

        table = self.current
        if table is None:
            return
        if tag in FORBIDDEN_TAGS:
            self.issue("forbidden_tag", f"<{tag}> is forbidden inside canonical tables")
        elif tag not in ALLOWED_TAGS:
            self.issue("unsupported_tag", f"<{tag}> is outside the canonical HTML subset")

        if "style" in attr_map:
            self.issue("inline_style", f"inline style is forbidden on <{tag}>")
        if tag == "tr":
            if table.active_row:
                self.issue("nested_row", "a <tr> started before the previous row closed")
            table.row_index += 1
            table.active_row = True
            table.current_col = 0
            return
        if tag in {"td", "th"}:
            self._start_cell(table, tag, attr_map)
            return
        if tag == "img":
            self._validate_image(attr_map)

    def _validate_table_attrs(self, table: TableState) -> None:
        for name in table.attrs:
            if name not in ALLOWED_TABLE_ATTRS:
                self.issue("table_attribute", f"unsupported <table> attribute: {name}", table.line)
        classes = set(table.attrs.get("class", "").split())
        if "pmtrpg-table" not in classes:
            self.issue("table_class", 'table must include class="pmtrpg-table"', table.line)
        table_id = table.attrs.get("data-table-id", "")
        if not table_id:
            self.issue("table_id_missing", "table must have data-table-id", table.line)
        elif not TABLE_ID_RE.fullmatch(table_id):
            self.issue("table_id_invalid", f"invalid data-table-id: {table_id!r}", table.line)

    def _start_cell(self, table: TableState, tag: str, attrs: dict[str, str]) -> None:
        if not table.active_row:
            self.issue("cell_outside_row", f"<{tag}> must be inside <tr>")
            return
        for name in attrs:
            if name not in ALLOWED_CELL_ATTRS:
                self.issue("cell_attribute", f"unsupported <{tag}> attribute: {name}")
        colspan = parse_positive_span(attrs.get("colspan"))
        rowspan = parse_positive_span(attrs.get("rowspan"))
        if colspan is None or rowspan is None:
            self.issue("invalid_span", f"invalid rowspan/colspan on <{tag}>")
            colspan = colspan or 1
            rowspan = rowspan or 1
        if tag == "th" and attrs.get("scope") not in {"col", "row"}:
            self.issue("header_scope", '<th> must use scope="col" or scope="row"')

        while (table.row_index, table.current_col) in table.occupied:
            table.current_col += 1
        start_col = table.current_col
        for row in range(table.row_index, table.row_index + rowspan):
            for col in range(start_col, start_col + colspan):
                coordinate = (row, col)
                if coordinate in table.occupied:
                    self.issue("span_overlap", f"cell span overlaps grid position row={row + 1}, col={col + 1}")
                table.occupied.add(coordinate)
        table.current_col += colspan
        table.open_cells.append(tag)

    def _validate_image(self, attrs: dict[str, str]) -> None:
        src = attrs.get("src", "")
        if not src:
            self.issue("image_src", "image inside table is missing src")
        elif not re.match(r"^[a-z]+://", src, re.IGNORECASE):
            target = (self.markdown_path.parent / src).resolve()
            if not target.exists():
                self.issue("image_missing", f"image path does not exist: {src}")
        if "alt" not in attrs:
            self.issue("image_alt", "image inside table must declare alt text")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        table = self.current
        if table is None:
            return
        if tag in {"td", "th"}:
            if not table.open_cells:
                self.issue("cell_close", f"unexpected </{tag}>")
            else:
                opened = table.open_cells.pop()
                if opened != tag:
                    self.issue("cell_mismatch", f"opened <{opened}> but closed </{tag}>")
            return
        if tag == "tr":
            if not table.active_row:
                self.issue("row_close", "unexpected </tr>")
                return
            while (table.row_index, table.current_col) in table.occupied:
                table.current_col += 1
            table.row_widths.append(table.current_col)
            table.active_row = False
            return
        if tag == "table":
            self._finish_table(table)
            self.table_stack.pop()

    def _finish_table(self, table: TableState) -> None:
        if table.active_row:
            self.issue("row_unclosed", "table closed before its current <tr>")
        if table.open_cells:
            self.issue("cell_unclosed", "table closed with unclosed cells")
        if not table.row_widths:
            self.issue("empty_table", "table has no completed rows", table.line)
            return
        expected = max(table.row_widths)
        for index, width in enumerate(table.row_widths, start=1):
            if width != expected:
                self.issue(
                    "column_mismatch",
                    f"row {index} has effective width {width}; expected {expected}",
                    table.line,
                )

    def close(self) -> None:
        super().close()
        for table in self.table_stack:
            self.issues.append(
                Issue(
                    code="table_unclosed",
                    path=self.relative,
                    line=table.line,
                    table_ordinal=table.ordinal,
                    message="table is not closed",
                )
            )
        self.table_stack.clear()


def validate_canonical_docs(docs_root: Path, repo_root: Path, excluded: set[str]) -> list[Issue]:
    issues: list[Issue] = []
    table_ids: dict[str, tuple[str, int, int]] = {}
    docs_root = docs_root.resolve()
    for path in sorted(docs_root.rglob("*.md")):
        relative = path.relative_to(repo_root).as_posix()
        if relative in excluded:
            continue
        source = path.read_text(encoding="utf-8")
        parser = CanonicalHTMLParser(path, repo_root)
        parser.feed(mask_markdown_code(source))
        parser.close()
        issues.extend(parser.issues)
        for table in parser.tables:
            table_id = table.attrs.get("data-table-id", "")
            if not table_id or not TABLE_ID_RE.fullmatch(table_id):
                continue
            previous = table_ids.get(table_id)
            if previous is None:
                table_ids[table_id] = (relative, table.line, table.ordinal)
                continue
            previous_path, previous_line, _ = previous
            issues.append(
                Issue(
                    code="table_id_duplicate",
                    path=relative,
                    line=table.line,
                    table_ordinal=table.ordinal,
                    message=(
                        f"data-table-id {table_id!r} already appears at "
                        f"{previous_path}:{previous_line}"
                    ),
                )
            )
    return issues


def structural_records(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index source tables by stable ID across representation changes."""

    records: dict[str, dict[str, Any]] = {}
    for item in items:
        if item.get("scope") != "source-content":
            continue
        records[item["id"]] = {
            "path": item["path"],
            "line": item.get("line", 1),
            "rows": item["rows"],
            "columns": item["columns"],
            "span_signature": item["span_signature"],
            "nested_depth": item["nested_depth"],
            "images": item["images"],
        }
    return records


def compare_structure(baseline: dict[str, Any], current: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    old = structural_records(baseline["tables"])
    new = structural_records(current["tables"])
    for key in sorted(old.keys() - new.keys()):
        record = old[key]
        issues.append(
            Issue("table_missing", record["path"], record["line"], None, f"baseline table is missing: {key}")
        )
    for key in sorted(new.keys() - old.keys()):
        record = new[key]
        issues.append(
            Issue("table_added", record["path"], record["line"], None, f"table was added after baseline: {key}")
        )
    for key in sorted(old.keys() & new.keys()):
        structural_fields = ("rows", "columns", "span_signature", "nested_depth", "images")
        changed = [field for field in structural_fields if old[key][field] != new[key][field]]
        if not changed:
            continue
        issues.append(
            Issue(
                "structure_changed",
                new[key]["path"],
                new[key]["line"],
                None,
                f"{key} structural fields changed: " + ", ".join(changed),
            )
        )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", type=Path, default=Path("docs"))
    parser.add_argument("--mapping", type=Path, default=Path("docs/PDF章节页码映射.md"))
    parser.add_argument("--baseline", type=Path, default=Path("docs/engineering/table-inventory.json"))
    parser.add_argument("--mode", choices=["structural", "canonical", "all"], default="all")
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--exclude",
        action="append",
        default=[
            "docs/engineering/table-inventory-stage0.md",
            "docs/engineering/canonical-table-stage1.md",
            "docs/engineering/local-html-conversion-preview.md",
        ],
    )
    args = parser.parse_args()
    docs_root = args.docs.resolve()
    mapping_path = args.mapping.resolve()
    baseline_path = args.baseline.resolve()
    repo_root = docs_root.parent
    excluded = set(args.exclude)
    issues: list[Issue] = []
    if args.mode in {"structural", "all"}:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        current = build_inventory(docs_root, mapping_path, excluded)
        issues.extend(compare_structure(baseline, current))
    if args.mode in {"canonical", "all"}:
        issues.extend(validate_canonical_docs(docs_root, repo_root, excluded))
    payload = {
        "mode": args.mode,
        "status": "PASS" if not issues else "FAIL",
        "issue_count": len(issues),
        "issues": [issue.as_dict() for issue in issues],
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("mode", "status", "issue_count")}, ensure_ascii=False))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
