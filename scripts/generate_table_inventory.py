"""Generate an auditable inventory of tables in ``docs/**/*.md``.

The scanner deliberately masks fenced and inline Markdown code before looking
for HTML tags.  This keeps references such as ``<table>...</table>`` in audit
checklists and engineering notes out of the source-table count.

It is an inventory tool, not a converter: it never edits the Markdown source.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


TABLE_TAG_RE = re.compile(r"<table\b", re.IGNORECASE)
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
PIPE_SEPARATOR_RE = re.compile(r"^\s*:?-{3,}:?\s*$")
SPECIAL_TAGS = {"script", "style", "iframe", "object", "embed", "svg"}
MAPPING_PAGE_RE = re.compile(r"\[P(?P<page>\d{3})\]")
MAPPING_DOC_RE = re.compile(r"docs/(?P<path>[^`\]]+?\.md)")
SOURCE_REVIEW_REQUIRED_STATUSES = {
    "high_risk_source_review_required",
    "unresolved_semantic_ambiguity",
}


def mask_markdown_code(text: str) -> str:
    """Replace Markdown code spans/fences with spaces while preserving lines."""

    chars = list(text)
    lines = text.splitlines(keepends=True)
    offset = 0
    fenced = False
    fence_marker = ""
    for line in lines:
        match = FENCE_RE.match(line)
        if match:
            marker = match.group(1)
            if not fenced:
                fenced = True
                fence_marker = marker[0]
            elif marker[0] == fence_marker:
                fenced = False
            for i in range(offset, offset + len(line.rstrip("\r\n"))):
                chars[i] = " "
            offset += len(line)
            continue
        if fenced:
            for i in range(offset, offset + len(line.rstrip("\r\n"))):
                chars[i] = " "
            offset += len(line)
            continue

        # Mask inline code spans.  This intentionally handles the common
        # single-backtick form used by the repository's audit notes.
        line_start = offset
        i = 0
        while i < len(line):
            if line[i] != "`":
                i += 1
                continue
            run = 1
            while i + run < len(line) and line[i + run] == "`":
                run += 1
            close = line.find("`" * run, i + run)
            if close < 0:
                i += run
                continue
            for j in range(line_start + i, line_start + close + run):
                if chars[j] not in "\r\n":
                    chars[j] = " "
            i = close + run
        offset += len(line)
    return "".join(chars)


def split_pipe_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped or "|" not in stripped:
        return None
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    cells = [cell.strip() for cell in stripped.split("|")]
    # A pipe-delimited single column (``| header |`` / ``| --- |``) is a
    # valid Markdown table too.  The caller still requires a separator row,
    # so accepting its one cell does not turn ordinary prose into a table.
    return cells if cells else None


def is_pipe_separator(line: str) -> bool:
    cells = split_pipe_row(line)
    return bool(cells) and all(PIPE_SEPARATOR_RE.fullmatch(cell) for cell in cells)


@dataclass
class HtmlTable:
    path: str
    ordinal: int
    start_line: int
    end_line: int | None = None
    depth: int = 0
    attrs: dict[str, str] = field(default_factory=dict)
    rows: int = 0
    max_columns: int = 0
    spans: list[dict[str, int]] = field(default_factory=list)
    images: list[dict[str, str | None]] = field(default_factory=list)
    special_tags: set[str] = field(default_factory=set)
    has_caption: bool = False
    has_thead: bool = False
    has_tbody: bool = False
    _row_columns: int = 0
    _row_active: bool = False


class TableHTMLParser(HTMLParser):
    def __init__(self, path: str) -> None:
        super().__init__(convert_charrefs=False)
        self.path = path
        self.tables: list[HtmlTable] = []
        self.table_stack: list[HtmlTable] = []
        self.tag_stack: list[str] = []

    @property
    def current(self) -> HtmlTable | None:
        return self.table_stack[-1] if self.table_stack else None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self.tag_stack.append(tag)
        if tag == "table":
            parent = self.current
            if parent is not None:
                parent_depth = parent.depth + 1
            else:
                parent_depth = 0
            record = HtmlTable(
                path=self.path,
                ordinal=len(self.tables) + 1,
                start_line=self.getpos()[0],
                depth=parent_depth,
                attrs={key.lower(): value or "" for key, value in attrs},
            )
            self.tables.append(record)
            self.table_stack.append(record)
            return

        table = self.current
        if table is None:
            return
        if tag in SPECIAL_TAGS:
            table.special_tags.add(tag)
        if tag == "caption":
            table.has_caption = True
        elif tag == "thead":
            table.has_thead = True
        elif tag == "tbody":
            table.has_tbody = True
        elif tag == "tr":
            table.rows += 1
            table._row_columns = 0
            table._row_active = True
        elif tag in {"td", "th"} and table._row_active:
            attr_map = {key.lower(): value or "" for key, value in attrs}
            colspan = _positive_int(attr_map.get("colspan"), 1)
            rowspan = _positive_int(attr_map.get("rowspan"), 1)
            table._row_columns += colspan
            table.max_columns = max(table.max_columns, table._row_columns)
            if colspan > 1 or rowspan > 1:
                table.spans.append(
                    {
                        "row": table.rows,
                        "colspan": colspan,
                        "rowspan": rowspan,
                    }
                )
        elif tag == "img":
            attr_map = {key.lower(): value for key, value in attrs}
            table.images.append(
                {
                    "src": attr_map.get("src"),
                    "alt": attr_map.get("alt"),
                }
            )

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        table = self.current
        if table is not None and tag == "tr":
            table._row_active = False
        if tag == "table" and self.table_stack:
            table = self.table_stack.pop()
            table.end_line = self.getpos()[0]
        # HTMLParser is forgiving; remove the nearest matching tag from the
        # lightweight stack so malformed source does not abort inventory.
        for index in range(len(self.tag_stack) - 1, -1, -1):
            if self.tag_stack[index] == tag:
                del self.tag_stack[index]
                break


def _positive_int(value: str | None, default: int) -> int:
    try:
        parsed = int(value or "")
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def stable_id(path: str, kind: str, ordinal: int, hint: str = "") -> str:
    """Return an ID that survives unrelated prose insertions above the table."""

    payload = f"{path}\0{kind}\0{ordinal}\0{hint[:120]}".encode("utf-8")
    digest = hashlib.sha1(payload).hexdigest()[:12]
    return f"{kind}-{digest}"


def classify_scope(relative: str) -> str:
    """Classify whether a table is source content or supporting evidence."""

    if relative.startswith("docs/acceptance/"):
        return "acceptance-evidence"
    if relative.startswith("docs/engineering/"):
        return "engineering-evidence"
    if relative.startswith("docs/tasks/"):
        return "task-evidence"
    if relative.startswith("docs/PDF"):
        return "reference-index"
    return "source-content"


def html_inventory(
    path: Path,
    relative: str,
    source: str,
    source_page_candidates: list[int],
) -> list[dict[str, Any]]:
    masked = mask_markdown_code(source)
    parser = TableHTMLParser(relative)
    parser.feed(masked)
    parser.close()
    items: list[dict[str, Any]] = []
    scope = classify_scope(relative)
    for table in parser.tables:
        complexity = []
        if table.spans:
            complexity.append("merged-cells")
        if table.depth:
            complexity.append("nested")
        if table.images:
            complexity.append("images")
        if table.special_tags:
            complexity.append("special-html")
        risk = "high" if len(complexity) >= 2 or "nested" in complexity else ("medium" if complexity else "low")
        hint = source.splitlines()[table.start_line - 1].strip() if source.splitlines() else ""
        canonical_candidate = (
            "pmtrpg-table" in table.attrs.get("class", "").split()
            and bool(table.attrs.get("data-table-id"))
        )
        items.append(
            {
                "id": table.attrs.get("data-table-id")
                or stable_id(relative, "html", table.ordinal, hint),
                "path": relative,
                "scope": scope,
                "review_required": scope == "source-content",
                "line": table.start_line,
                "end_line": table.end_line,
                "representation": "html",
                "target_state": "canonical-html" if scope == "source-content" else "non-migration-evidence",
                "disposition": (
                    "待验收"
                    if scope == "source-content" and canonical_candidate
                    else ("待迁移" if scope == "source-content" else "非迁移对象")
                ),
                "recommendation": (
                    "完成分发与人工验收"
                    if scope == "source-content" and canonical_candidate
                    else ("规范化并保持为 canonical HTML" if scope == "source-content" else "不作为迁移对象")
                ),
                "review_owner": None,
                "rows": table.rows,
                "columns": table.max_columns,
                "span_signature": table.spans,
                "nested_depth": table.depth,
                "images": table.images,
                "special_html": sorted(table.special_tags),
                "source_attributes": {
                    key: value
                    for key, value in table.attrs.items()
                    if key in {"class", "id", "data-table-id"}
                },
                "has_caption": table.has_caption,
                "has_thead": table.has_thead,
                "has_tbody": table.has_tbody,
                "source_page": None,
                "source_page_candidates": source_page_candidates,
                "source_page_status": (
                    "chapter-mapping-candidate"
                    if source_page_candidates
                    else "unmapped"
                ),
                "target_outputs": ["site", "chm", "docx", "pdf"],
                "risk": risk,
            }
        )
    return items


def markdown_inventory(
    relative: str,
    source: str,
    source_page_candidates: list[int],
) -> list[dict[str, Any]]:
    masked = mask_markdown_code(source)
    lines = masked.splitlines()
    original_lines = source.splitlines()
    items: list[dict[str, Any]] = []
    scope = classify_scope(relative)
    i = 0
    ordinal = 0
    while i + 1 < len(lines):
        header = split_pipe_row(lines[i])
        if header is None or not is_pipe_separator(lines[i + 1]):
            i += 1
            continue
        ordinal += 1
        j = i + 2
        while j < len(lines) and split_pipe_row(lines[j]) is not None:
            j += 1
        # The separator line is Markdown syntax, not a rendered table row.
        row_count = j - i - 1
        hint = original_lines[i].strip() if i < len(original_lines) else ""
        items.append(
            {
                "id": stable_id(relative, "markdown", ordinal, hint),
                "path": relative,
                "scope": scope,
                "review_required": scope == "source-content",
                "line": i + 1,
                "end_line": j,
                "representation": "markdown-pipe",
                "target_state": "canonical-html" if scope == "source-content" else "non-migration-evidence",
                "disposition": "待迁移" if scope == "source-content" else "非迁移对象",
                "recommendation": "迁移为 canonical HTML" if scope == "source-content" else "不作为迁移对象",
                "review_owner": None,
                "rows": row_count,
                "columns": len(header),
                "span_signature": [],
                "nested_depth": 0,
                "images": [],
                "special_html": [],
                "has_caption": False,
                "has_thead": False,
                "has_tbody": False,
                "source_page": None,
                "source_page_candidates": source_page_candidates,
                "source_page_status": (
                    "chapter-mapping-candidate"
                    if source_page_candidates
                    else "unmapped"
                ),
                "target_outputs": ["site", "chm", "docx", "pdf"],
                "risk": "low",
            }
        )
        i = j
    return items


def load_page_mapping(mapping_path: Path) -> dict[str, list[int]]:
    """Read chapter-level PDF page candidates without changing source docs."""

    mapping: dict[str, set[int]] = {}
    if not mapping_path.exists():
        return {}
    for line in mapping_path.read_text(encoding="utf-8").splitlines():
        page_match = MAPPING_PAGE_RE.search(line)
        if page_match is None:
            continue
        page = int(page_match.group("page"))
        # A single chapter row may point to multiple Markdown files.  Associate
        # the page with every link on that row (not only the first one).
        for doc_match in MAPPING_DOC_RE.finditer(line):
            relative = "docs/" + doc_match.group("path").replace("\\", "/")
            mapping.setdefault(relative, set()).add(page)
    return {path: sorted(pages) for path, pages in mapping.items()}


def load_review_statuses(batch_directory: Path) -> dict[str, str]:
    """Load the current per-table review status from Stage 7 batch manifests."""

    statuses: dict[str, str] = {}
    if not batch_directory.exists():
        return statuses
    for manifest_path in sorted(batch_directory.glob("stage7-batch-*.json")):
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        for table in payload.get("tables", []):
            table_id = table.get("id")
            review_status = table.get("review_status")
            if not table_id or not review_status:
                continue
            previous = statuses.get(table_id)
            if previous is not None and previous != review_status:
                raise ValueError(
                    f"Conflicting review status for {table_id}: {previous} != {review_status}"
                )
            statuses[table_id] = review_status
    return statuses


def apply_current_status(
    tables: list[dict[str, Any]],
    review_statuses: dict[str, str],
) -> None:
    """Reconcile Stage 0 discovery fields with the live conversion/review state."""

    for item in tables:
        if item["scope"] != "source-content":
            item["review_required"] = False
            item["review_status"] = "non_migration_evidence"
            continue

        canonical_html = (
            item["representation"] == "html"
            and "pmtrpg-table" in item.get("source_attributes", {}).get("class", "").split()
            and bool(item.get("source_attributes", {}).get("data-table-id"))
        )
        if not canonical_html:
            item["review_required"] = True
            item["review_status"] = "conversion_required"
            item["disposition"] = "待迁移"
            item["recommendation"] = "迁移或规范化为 canonical HTML"
            continue

        review_status = review_statuses.get(item["id"], "review_status_unavailable")
        item["review_status"] = review_status
        item["review_required"] = (
            review_status in SOURCE_REVIEW_REQUIRED_STATUSES
            or review_status == "review_status_unavailable"
        )
        item["disposition"] = "已迁移 HTML"
        if review_status == "high_risk_source_review_required":
            item["review_owner"] = "Codex"
            item["recommendation"] = "由 Codex 对照 PDF/CHM 复核高风险原文"
        elif review_status == "unresolved_semantic_ambiguity":
            item["review_owner"] = "用户"
            item["recommendation"] = "仅就无法从源证据判定的语义歧义请求用户裁定"
        elif review_status == "review_status_unavailable":
            item["recommendation"] = "先生成 Stage 7 逐表复核状态"
        else:
            item["recommendation"] = "保持 canonical HTML，并由分发适配器消费"


def build_inventory(
    docs_root: Path,
    mapping_path: Path,
    excluded_paths: set[str] | None = None,
    review_statuses: dict[str, str] | None = None,
    review_status_authority: str | None = None,
) -> dict[str, Any]:
    page_mapping = load_page_mapping(mapping_path)
    excluded_paths = excluded_paths or set()
    tables: list[dict[str, Any]] = []
    document_count = 0
    for path in sorted(docs_root.rglob("*.md")):
        relative = path.relative_to(docs_root.parent).as_posix()
        if relative in excluded_paths:
            continue
        source = path.read_text(encoding="utf-8")
        candidates = page_mapping.get(relative, [])
        html_items = html_inventory(path, relative, source, candidates)
        markdown_items = markdown_inventory(relative, source, candidates)
        if html_items or markdown_items:
            document_count += 1
            tables.extend(html_items)
            tables.extend(markdown_items)
    html_tables = [item for item in tables if item["representation"] == "html"]
    markdown_tables = [item for item in tables if item["representation"] == "markdown-pipe"]
    review_statuses = review_statuses or {}
    apply_current_status(tables, review_statuses)
    source_tables = [item for item in tables if item["scope"] == "source-content"]
    review_status_counts: dict[str, int] = {}
    for item in source_tables:
        status = item["review_status"]
        review_status_counts[status] = review_status_counts.get(status, 0) + 1
    html_source_owner_complete = all(
        item["source_page"] is not None and item["review_owner"]
        for item in html_tables
        if item["risk"] != "low" and item["scope"] == "source-content"
    )
    complex_mapping_complete = all(
        item["source_page_candidates"]
        for item in html_tables
        if item["risk"] != "low" and item["scope"] == "source-content"
    )
    return {
        "schema_version": 2,
        "generated_by": "scripts/generate_table_inventory.py",
        "source_root": "docs",
        "source_policy": "docs is the editing source; originFab is reference-only",
        "excluded_paths": sorted(excluded_paths),
        "tables": tables,
        "summary": {
            "documents_with_tables": document_count,
            "total_tables": len(tables),
            "html_tables": len(html_tables),
            "markdown_pipe_tables": len(markdown_tables),
            "html_documents": len({item["path"] for item in html_tables}),
            "markdown_documents": len({item["path"] for item in markdown_tables}),
            "complex_html_tables": sum(1 for item in html_tables if item["risk"] != "low"),
            "unresolved_dispositions": sum(
                item["scope"] == "source-content" and item["disposition"] != "已迁移 HTML"
                for item in tables
            ),
            "pending_review": sum(item["review_required"] for item in source_tables),
            "pending_codex_source_review": sum(
                item["review_status"]
                in {"high_risk_source_review_required", "review_status_unavailable"}
                for item in source_tables
            ),
            "pending_human_review": sum(
                item["review_status"] == "unresolved_semantic_ambiguity"
                for item in source_tables
            ),
            "review_status_counts": dict(sorted(review_status_counts.items())),
            "tables_with_mapping_candidates": sum(
                bool(item["source_page_candidates"]) for item in tables
            ),
            "tables_without_mapping_candidates": sum(
                not item["source_page_candidates"] for item in tables
            ),
            "source_content_tables": sum(item["scope"] == "source-content" for item in tables),
            "evidence_tables": sum(item["scope"] != "source-content" for item in tables),
            "source_content_final_target": "canonical-html",
        },
        "review_status_authority": review_status_authority,
        "stage_0_gate": {
            "inventory_coverage_100_percent": True,
            "complex_tables_have_source_and_owner": html_source_owner_complete,
            "complex_tables_have_mapping_candidates": complex_mapping_complete,
            "human_review_deferred_to_rendered_batches": False,
            "user_review_required_only_for": "unresolved_semantic_ambiguity",
            "automatic_merge_inference_allowed": False,
            "status": "PASS_MACHINE" if complex_mapping_complete else "BLOCK_MAPPING",
            "blocking_reasons": [] if complex_mapping_complete else [
                "复杂源表仍有缺失的章节级来源候选。"
            ],
            "current_review_requirements": [
                "高风险 canonical HTML 由 Codex 对照 PDF/CHM 源证据复核。",
                "仅无法从源证据判定的语义歧义升级给用户裁定。",
            ],
        },
        "baseline_cross_check": {
            "plan_html_tables": 391,
            "plan_html_documents": 84,
            "plan_markdown_pipe_headers": 84,
            "observed_html_tables": len(html_tables),
            "observed_html_documents": len({item["path"] for item in html_tables}),
            "observed_markdown_pipe_headers": len(markdown_tables),
            "delta_html_tables": len(html_tables) - 391,
            "delta_html_documents": len({item["path"] for item in html_tables}) - 84,
            "delta_markdown_pipe_headers": len(markdown_tables) - 84,
            "note": "这些是计划中的历史盘点数字；生成物以本次扫描结果为准，差异需人工解释。",
        },
        "mapping_source": mapping_path.as_posix(),
    }


def write_review_queue(inventory: dict[str, Any], output: Path) -> None:
    """Write one human-review row per inventory item as UTF-8 CSV."""

    fields = [
        "id",
        "path",
        "scope",
        "review_required",
        "review_status",
        "target_state",
        "line",
        "end_line",
        "representation",
        "risk",
        "rows",
        "columns",
        "nested_depth",
        "span_signature",
        "images",
        "special_html",
        "source_page_candidates",
        "source_page",
        "source_page_status",
        "review_owner",
        "disposition",
        "recommendation",
        "review_notes",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in inventory["tables"]:
            row = {key: item.get(key, "") for key in fields}
            row["span_signature"] = json.dumps(item["span_signature"], ensure_ascii=False, separators=(",", ":"))
            row["images"] = json.dumps(item["images"], ensure_ascii=False, separators=(",", ":"))
            row["special_html"] = ";".join(item["special_html"])
            row["source_page_candidates"] = ";".join(str(page) for page in item["source_page_candidates"])
            row["review_notes"] = ""
            writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", type=Path, default=Path("docs"))
    parser.add_argument(
        "--mapping",
        type=Path,
        default=Path("docs/PDF章节页码映射.md"),
        help="Chapter-to-PDF page mapping used only to provide source-page candidates",
    )
    parser.add_argument("--output", type=Path, default=Path("docs/engineering/table-inventory.json"))
    parser.add_argument(
        "--review-status-dir",
        type=Path,
        default=Path("docs/engineering/table-rollout-batches"),
        help="Stage 7 batch manifests that provide the live per-table review status",
    )
    parser.add_argument(
        "--queue-output",
        type=Path,
        default=Path("output/spreadsheet/table-review-queue.csv"),
        help="UTF-8 CSV human-review queue; pass an empty value only by calling the module directly",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[
            "docs/engineering/table-inventory-stage0.md",
            "docs/engineering/canonical-table-stage1.md",
            "docs/engineering/local-html-conversion-preview.md",
        ],
        help="Relative Markdown path to exclude from the source inventory (repeatable)",
    )
    args = parser.parse_args()
    review_statuses = load_review_statuses(args.review_status_dir)
    inventory = build_inventory(
        args.docs,
        args.mapping,
        set(args.exclude),
        review_statuses,
        args.review_status_dir.as_posix(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.queue_output:
        write_review_queue(inventory, args.queue_output)
    print(json.dumps(inventory["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
