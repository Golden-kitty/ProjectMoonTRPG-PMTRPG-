from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

import fitz
from bs4 import BeautifulSoup, NavigableString

from export_sample_docs import DOCS_DIR, REPO_ROOT, md_to_html_body


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
LEGACY_SKILL_MARKERS = ["〔谨慎〕", "〔勇气〕", "〔自律〕", "〔双倍〕", "〔黑桃〕", "〔红桃〕", "〔方块〕", "〔梅花〕"]


def normalized_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).lower()
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", value)


def raw_brace_blocks(source_text: str, rel_path: str) -> list[dict]:
    """Use raw source, never Markdown output, as the brace-prose oracle."""
    blocks = []
    for line_number, line in enumerate(source_text.splitlines(), start=1):
        for match in re.finditer(r"[{｛][^{}｛｝\n]*[}｝]", line):
            text = match.group(0)
            if re.search(r"[\u3400-\u9fff]", text):
                blocks.append({"file": rel_path, "line": line_number, "text": text,
                               "normalized": normalized_text(text)})
    return blocks


def visible_html_text(node) -> str:
    clone = BeautifulSoup(str(node), "html.parser")
    for invisible in clone.find_all(["script", "style", "head"]):
        invisible.decompose()
    return clone.get_text(" ", strip=True)


def html_section_texts(soup: BeautifulSoup) -> dict[str, str]:
    sections: dict[str, str] = {}
    for section in soup.find_all("section"):
        marker = section.find("p", class_="source", recursive=False)
        if marker is not None:
            rel_path = marker.get_text(strip=True)
            sections[rel_path] = sections.get(rel_path, "") + visible_html_text(section)
    return sections


def text_sections_by_source_markers(text: str, files: list[str]) -> dict[str, str]:
    """Bound PDF/OOXML text by actual source-path markers in source order."""
    normalized = normalized_text(text)
    positions = []
    cursor = 0
    for rel_path in files:
        marker = normalized_text(rel_path)
        start = normalized.find(marker, cursor)
        if start < 0:
            continue
        positions.append((rel_path, start, start + len(marker)))
        cursor = start + len(marker)
    return {rel_path: normalized[end:positions[index + 1][1] if index + 1 < len(positions) else len(normalized)]
            for index, (rel_path, _start, end) in enumerate(positions)}


def raw_brace_coverage(blocks: list[dict], sections: dict[str, str]) -> dict:
    """Count occurrences within the owning source section, not the full book."""
    used: Counter = Counter()
    missing = []
    normalized_sections = {path: normalized_text(text) for path, text in sections.items()}
    for block in blocks:
        key = (block["file"], block["normalized"])
        used[key] += 1
        if normalized_sections.get(block["file"], "").count(block["normalized"]) < used[key]:
            missing.append({**block, "required_occurrence": used[key]})
    return {"source_block_count": len(blocks), "matched_block_count": len(blocks) - len(missing),
            "missing_blocks": missing,
            "missing_source_sections": sorted({block["file"] for block in blocks if block["file"] not in sections})}


def prose_blocks(soup: BeautifulSoup, rel_path: str) -> list[dict]:
    clone = BeautifulSoup(str(soup), "html.parser")
    blocks: list[dict] = []
    block_tags = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote", "li", "dt", "dd", "pre", "summary"}

    def append(value: str, tag: str) -> None:
        normalized = normalized_text(value)
        if normalized:
            blocks.append({"file": rel_path, "tag": tag, "text": value, "normalized": normalized})

    def visit(node) -> None:
        if isinstance(node, NavigableString):
            value = str(node).strip()
            if value:
                append(value, "text")
            return
        tag = getattr(node, "name", "").lower()
        if not tag or tag == "table":
            return
        if tag in block_tags:
            append(node.get_text(" ", strip=True), tag)
            return
        for child in node.children:
            visit(child)

    root = clone.body or clone
    for child in root.children:
        visit(child)
    return blocks


def positive_span(node, name: str) -> int:
    try:
        return max(1, int(node.get(name, 1)))
    except (TypeError, ValueError):
        return 1


def html_table_structure(table) -> dict:
    """Reconstruct merge coordinates independently of the DOCX exporter."""
    rows = [row for row in table.find_all("tr") if row.find_parent("table") is table]
    occupied: set[tuple[int, int]] = set()
    merges: list[dict] = []
    errors: list[str] = []
    columns = 0
    for row_index, row in enumerate(rows):
        col = 0
        for cell in row.find_all(["th", "td"]):
            if cell.find_parent("table") is not table or cell.find_parent("tr") is not row:
                continue
            while (row_index, col) in occupied:
                col += 1
            rowspan = positive_span(cell, "rowspan")
            colspan = positive_span(cell, "colspan")
            slots = {(rr, cc) for rr in range(row_index, row_index + rowspan)
                     for cc in range(col, col + colspan)}
            if occupied & slots:
                errors.append(f"overlapping_span:{row_index}:{col}")
            occupied.update(slots)
            if rowspan > 1 or colspan > 1:
                merges.append({"row": row_index, "col": col, "rowspan": rowspan, "colspan": colspan})
            col += colspan
            columns = max(columns, col)
    return {
        "rows": max([len(rows), *[row + 1 for row, _col in occupied]]),
        "columns": columns,
        "nested_depth": len(table.find_parents("table")),
        "merged_cells": merges,
        "errors": errors,
    }


def docx_table_structures(document) -> list[dict]:
    """Read physical OOXML cells; continuation spans must match their anchor."""
    parent_by_node = {child: parent for parent in document.iter() for child in parent}
    structures: list[dict] = []
    for table in document.findall(f".//{{{W_NS}}}tbl"):
        depth = 0
        parent = parent_by_node.get(table)
        while parent is not None:
            depth += parent.tag == f"{{{W_NS}}}tbl"
            parent = parent_by_node.get(parent)
        rows = table.findall(f"{{{W_NS}}}tr")
        columns = len(table.findall(f"{{{W_NS}}}tblGrid/{{{W_NS}}}gridCol"))
        anchors: list[dict] = []
        errors: list[str] = []
        active: dict[tuple[int, int], dict] = {}
        for row_index, row in enumerate(rows):
            col = 0
            next_active: dict[tuple[int, int], dict] = {}
            for cell in row.findall(f"{{{W_NS}}}tc"):
                span = cell.find(f"{{{W_NS}}}tcPr/{{{W_NS}}}gridSpan")
                try:
                    colspan = int(span.get(f"{{{W_NS}}}val", "1")) if span is not None else 1
                    if colspan < 1:
                        raise ValueError
                except ValueError:
                    errors.append(f"invalid_gridspan:{row_index}:{col}")
                    colspan = 1
                merge = cell.find(f"{{{W_NS}}}tcPr/{{{W_NS}}}vMerge")
                merge_value = merge.get(f"{{{W_NS}}}val", "continue") if merge is not None else None
                key = (col, colspan)
                if merge_value == "continue":
                    anchor = active.get(key)
                    if anchor is None:
                        errors.append(f"orphan_or_width_changed_vmerge:{row_index}:{col}:{colspan}")
                    else:
                        anchor["rowspan"] += 1
                        next_active[key] = anchor
                else:
                    anchor = {"row": row_index, "col": col, "rowspan": 1, "colspan": colspan}
                    anchors.append(anchor)
                    if merge_value == "restart":
                        next_active[key] = anchor
                    elif merge_value is not None:
                        errors.append(f"invalid_vmerge:{row_index}:{col}:{merge_value}")
                col += colspan
            if col != columns:
                errors.append(f"row_grid_width_mismatch:{row_index}:{col}:{columns}")
            active = next_active
        structures.append({
            "rows": len(rows), "columns": columns, "nested_depth": depth,
            "merged_cells": [cell for cell in anchors if cell["rowspan"] > 1 or cell["colspan"] > 1],
            "errors": errors,
        })
    return structures


def compare_docx_table_structures(expected: list[dict], observed: list[dict]) -> list[dict]:
    """Compare each table in source order, retaining every merge coordinate."""
    issues: list[dict] = []
    if len(expected) != len(observed):
        issues.append({"code": "table_count_mismatch", "expected": len(expected), "observed": len(observed)})
    for ordinal, (source, actual) in enumerate(zip(expected, observed), start=1):
        changed = [key for key in ("rows", "columns", "nested_depth", "merged_cells")
                   if source[key] != actual[key]]
        if changed or source["errors"] or actual["errors"]:
            issues.append({
                "table_ordinal": ordinal, "id": source.get("id"), "file": source.get("file"),
                "fields": changed,
                "expected": {key: source[key] for key in changed},
                "observed": {key: actual[key] for key in changed},
                "source_errors": source["errors"], "docx_errors": actual["errors"],
            })
    return issues


def compare_html_table_structures(expected: list[dict], observed: list[dict]) -> list[dict]:
    """HTML keeps table IDs, so compare geometry by ID instead of filename order."""
    issues: list[dict] = []
    for source in expected:
        matches = [table for table in observed if table["id"] == source["id"]]
        if len(matches) != 1:
            issues.append({"id": source["id"], "code": "table_id_count", "observed": len(matches)})
            continue
        actual = matches[0]
        changed = [key for key in ("rows", "columns", "nested_depth", "merged_cells")
                   if source[key] != actual[key]]
        if changed or source["errors"] or actual["errors"]:
            issues.append({
                "id": source["id"], "fields": changed,
                "expected": {key: source[key] for key in changed},
                "observed": {key: actual[key] for key in changed},
                "source_errors": source["errors"], "html_errors": actual["errors"],
            })
    return issues


def html_summary(paths: list[Path]) -> dict:
    table_ids: list[str] = []
    table_structures: list[dict] = []
    colspan_cells = 0
    docx_gridspan_slots = 0
    rowspan_slots = 0
    image_occurrences = 0
    image_sources: set[str] = set()
    nested_tables = 0
    labels: list[str] = []
    source_prose_blocks: list[dict] = []
    source_raw_brace_blocks: list[dict] = []
    rendered_sections: dict[str, str] = {}
    legacy_skill_markers: list[dict] = []

    for path in paths:
        source_text = path.read_text(encoding="utf-8")
        for marker in LEGACY_SKILL_MARKERS:
            if marker in source_text:
                legacy_skill_markers.append(
                    {"file": path.relative_to(DOCS_DIR).as_posix(), "marker": marker, "count": source_text.count(marker)}
                )
        labels.append(path.stem)
        soup = BeautifulSoup(md_to_html_body(path), "html.parser")
        rel_path = path.relative_to(DOCS_DIR).as_posix()
        source_raw_brace_blocks.extend(raw_brace_blocks(source_text, rel_path))
        rendered_sections[rel_path] = visible_html_text(soup)
        source_prose_blocks.extend(prose_blocks(soup, rel_path))
        tables = soup.find_all("table")
        for table in tables:
            table_ids.append(table.get("data-table-id", ""))
            table_structures.append({"id": table.get("data-table-id", ""), "file": rel_path,
                                     **html_table_structure(table)})
            if table.find_parent("table") is not None:
                nested_tables += 1
        for cell in soup.find_all(["th", "td"]):
            if positive_span(cell, "colspan") > 1:
                colspan_cells += 1
                # OOXML repeats gridSpan on each vertical-merge continuation.
                docx_gridspan_slots += positive_span(cell, "rowspan")
            row_span = positive_span(cell, "rowspan")
            if row_span > 1:
                rowspan_slots += row_span
        for image in soup.find_all("img"):
            image_occurrences += 1
            image_sources.add(image.get("src", ""))

    return {
        "files": [path.relative_to(DOCS_DIR).as_posix() for path in paths],
        "labels": labels,
        "table_count": len(table_ids),
        "table_ids": table_ids,
        "table_structures": table_structures,
        "unique_table_ids": len(set(table_ids)),
        "colspan_cells": colspan_cells,
        "docx_gridspan_slots": docx_gridspan_slots,
        "rowspan_slots": rowspan_slots,
        "nested_tables": nested_tables,
        "image_occurrences": image_occurrences,
        "unique_image_sources": len(image_sources),
        "prose_blocks": source_prose_blocks,
        "prose_block_count": len(source_prose_blocks),
        "raw_brace_blocks": source_raw_brace_blocks,
        "raw_brace_coverage": raw_brace_coverage(source_raw_brace_blocks, rendered_sections),
        "legacy_skill_markers": legacy_skill_markers,
    }


def html_tree_summary(root: Path, brace_blocks: list[dict] | None = None) -> dict:
    html_files = sorted(root.rglob("*.html"))
    table_ids: list[str] = []
    table_structures: list[dict] = []
    image_occurrences = 0
    missing_images: list[str] = []
    sections: dict[str, str] = {}
    for html_path in html_files:
        soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
        for rel_path, text in html_section_texts(soup).items():
            sections[rel_path] = sections.get(rel_path, "") + text
        table_ids.extend(table.get("data-table-id", "") for table in soup.find_all("table"))
        table_structures.extend(
            {"id": table.get("data-table-id", ""), **html_table_structure(table)}
            for table in soup.find_all("table")
        )
        for image in soup.find_all("img"):
            image_occurrences += 1
            source = image.get("src", "")
            if not (html_path.parent / source).resolve().exists():
                missing_images.append(f"{html_path.name}:{source}")
    return {
        "html_files": len(html_files),
        "table_count": len(table_ids),
        "table_ids": table_ids,
        "table_structures": table_structures,
        "unique_table_ids": len(set(table_ids)),
        "image_occurrences": image_occurrences,
        "image_files": len(list(root.rglob("*.jpg"))) + len(list(root.rglob("*.png"))),
        "missing_images": missing_images,
        "raw_brace_coverage": raw_brace_coverage(brace_blocks or [], sections),
    }


def docx_summary(path: Path, brace_blocks: list[dict] | None = None, files: list[str] | None = None) -> dict:
    with zipfile.ZipFile(path) as archive:
        document = ElementTree.fromstring(archive.read("word/document.xml"))
        names = archive.namelist()
    all_text = "".join(node.text or "" for node in document.findall(f".//{{{W_NS}}}t"))
    table_paragraphs = document.findall(f".//{{{W_NS}}}tbl//{{{W_NS}}}p")
    drawing_paragraphs = [
        paragraph
        for paragraph in table_paragraphs
        if paragraph.find(f".//{{{W_NS}}}drawing") is not None
    ]
    return {
        "table_count": len(document.findall(f".//{{{W_NS}}}tbl")),
        "raw_brace_coverage": raw_brace_coverage(
            brace_blocks or [], text_sections_by_source_markers(all_text, files or [])),
        "table_structures": docx_table_structures(document),
        "gridspan_count": len(document.findall(f".//{{{W_NS}}}gridSpan")),
        "vmerge_count": len(document.findall(f".//{{{W_NS}}}vMerge")),
        "drawing_count": len(document.findall(f".//{{{W_NS}}}drawing")),
        "blip_count": len(document.findall(f".//{{{A_NS}}}blip")),
        "media_files": len([name for name in names if name.startswith("word/media/")]),
        "drawing_paragraphs_in_tables": len(drawing_paragraphs),
        "duplicate_suit_alt_text": sorted(
            marker for marker in ["[黑桃]", "[红桃]", "[梅花]", "[方片]"] if marker in all_text
        ),
        "legacy_skill_markers": sorted(marker for marker in LEGACY_SKILL_MARKERS if marker in all_text),
        "explicit_page_break_count": len(
            document.findall(f".//{{{W_NS}}}br[@{{{W_NS}}}type='page']")
        ),
        "page_break_before_count": len(document.findall(f".//{{{W_NS}}}pageBreakBefore")),
    }


def pdf_summary(path: Path, labels: list[str], source_prose_blocks: list[dict],
                brace_blocks: list[dict] | None = None, files: list[str] | None = None) -> dict:
    document = fitz.open(path)
    pages = []
    all_text = ""
    image_xrefs: set[int] = set()
    fonts: dict[int, dict] = {}
    for index, page in enumerate(document):
        text = page.get_text()
        all_text += text
        images = page.get_images(full=True)
        image_xrefs.update(item[0] for item in images)
        for xref, extension, font_type, base_font, resource_name, encoding, _referencer in page.get_fonts(full=True):
            fonts[xref] = {
                "xref": xref,
                "extension": extension,
                "type": font_type,
                "base_font": base_font,
                "resource_name": resource_name,
                "encoding": encoding,
                "embedded": extension != "n/a",
            }
        pages.append({"page": index + 1, "text_chars": len(text), "images": len(images)})
    normalized_pdf = normalized_text(all_text)
    missing_prose = [
        {"file": block["file"], "tag": block["tag"], "text": block["text"]}
        for block in source_prose_blocks
        if block["normalized"] not in normalized_pdf
    ]
    return {
        "page_count": document.page_count,
        "raw_brace_coverage": raw_brace_coverage(
            brace_blocks or [], text_sections_by_source_markers(all_text, files or [])),
        "text_chars": len(all_text),
        "unique_image_xrefs": len(image_xrefs),
        "missing_section_labels": [label for label in labels if label not in all_text],
        "source_prose_block_count": len(source_prose_blocks),
        "matched_prose_block_count": len(source_prose_blocks) - len(missing_prose),
        "missing_prose_blocks": missing_prose,
        "duplicate_suit_alt_text": sorted(
            marker for marker in ["[黑桃]", "[红桃]", "[梅花]", "[方片]"] if marker in all_text
        ),
        "legacy_skill_markers": sorted(marker for marker in LEGACY_SKILL_MARKERS if marker in all_text),
        "fonts": sorted(fonts.values(), key=lambda item: item["xref"]),
        "unembedded_cjk_fonts": sorted(
            item["base_font"]
            for item in fonts.values()
            if item["type"] == "Type0" and not item["embedded"]
        ),
        "embedded_font_count": sum(1 for item in fonts.values() if item["embedded"]),
        "pages": pages,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot-dir", type=Path, required=True)
    parser.add_argument("--batch-name", required=True)
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--files", nargs="+")
    sources.add_argument("--file-list", type=Path)
    parser.add_argument("--chm-decompiled", type=Path)
    parser.add_argument("--docx-word-print", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--chm-payload-visual-status",
        choices=["pending", "passed_by_implementer", "accepted_by_user", "fixed_pending_user_recheck"],
        default="pending",
    )
    parser.add_argument(
        "--chm-viewer-status",
        choices=[
            "pending",
            "passed_by_implementer",
            "accepted_by_user",
            "fixed_pending_user_recheck",
            "user_reported_defect",
        ],
        default="pending",
    )
    parser.add_argument(
        "--docx-open-status",
        choices=["pending", "passed"],
        default="pending",
    )
    parser.add_argument(
        "--pdf-visual-status",
        choices=["pending", "passed_by_implementer", "accepted_by_user", "fixed_pending_user_recheck", "user_reported_defect"],
        default="pending",
    )
    parser.add_argument(
        "--docx-page-visual-status",
        choices=[
            "pending",
            "passed_by_implementer",
            "blocked_by_local_renderer",
            "accepted_by_user",
            "fixed_pending_user_recheck",
            "user_reported_defect",
        ],
        default="pending",
    )
    args = parser.parse_args()

    pilot_dir = args.pilot_dir.resolve()
    chm_decompiled = args.chm_decompiled.resolve() if args.chm_decompiled else None
    docx_word_print_path = args.docx_word_print.resolve() if args.docx_word_print else None
    report_path = args.report.resolve()

    source_files = args.files if args.files else [
        line.strip() for line in args.file_list.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    source_paths = [DOCS_DIR / value.replace("\\", "/").removeprefix("docs/") for value in source_files]
    source = html_summary(source_paths)
    chm_dir = pilot_dir / "chm"
    docx_path = pilot_dir / "docx" / f"{args.batch_name}.docx"
    pdf_path = pilot_dir / "pdf" / f"{args.batch_name}.pdf"
    chm_path = chm_dir / f"{args.batch_name}.chm"

    brace_blocks = source["raw_brace_blocks"]
    generated_chm = html_tree_summary(chm_dir / "html", brace_blocks)
    decompiled_chm = html_tree_summary(chm_decompiled, brace_blocks) if chm_decompiled else None
    docx = docx_summary(docx_path, brace_blocks, source["files"])
    docx_word_print = (
        pdf_summary(docx_word_print_path, source["labels"], source["prose_blocks"], brace_blocks, source["files"])
        if docx_word_print_path
        else None
    )
    pdf = pdf_summary(pdf_path, source["labels"], source["prose_blocks"], brace_blocks, source["files"])
    pdf_html_path = pdf_path.with_suffix(".html")
    pdf_html_braces = raw_brace_coverage(brace_blocks, html_section_texts(
        BeautifulSoup(pdf_html_path.read_text(encoding="utf-8"), "html.parser")))

    issues: list[str] = []
    for name, coverage in [
        ("source_rendered", source["raw_brace_coverage"]),
        ("chm_generated", generated_chm["raw_brace_coverage"]),
        ("chm_decompiled", decompiled_chm["raw_brace_coverage"] if decompiled_chm else None),
        ("docx", docx["raw_brace_coverage"]),
        ("docx_word_print", docx_word_print["raw_brace_coverage"] if docx_word_print else None),
        ("pdf", pdf["raw_brace_coverage"]), ("pdf_html", pdf_html_braces),
    ]:
        if coverage and (coverage["missing_blocks"] or coverage["missing_source_sections"]):
            issues.append(f"{name}_raw_brace_text_missing")
    if source["legacy_skill_markers"]:
        issues.append("source_legacy_skill_markers_present")
    if not all(source["table_ids"]) or source["unique_table_ids"] != source["table_count"]:
        issues.append("source_table_ids_missing_or_duplicate")
    expected_ids = sorted(source["table_ids"])
    if sorted(generated_chm["table_ids"]) != expected_ids:
        issues.append("chm_generated_table_ids_mismatch")
    generated_chm["table_structure_issues"] = compare_html_table_structures(
        source["table_structures"], generated_chm["table_structures"]
    )
    if generated_chm["table_structure_issues"]:
        issues.append("chm_generated_table_structure_mismatch")
    if generated_chm["missing_images"]:
        issues.append("chm_generated_images_missing")
    if not chm_path.exists() or chm_path.stat().st_size == 0:
        issues.append("chm_binary_missing")
    if decompiled_chm is not None:
        if sorted(decompiled_chm["table_ids"]) != expected_ids:
            issues.append("chm_decompiled_table_ids_mismatch")
        decompiled_chm["table_structure_issues"] = compare_html_table_structures(
            source["table_structures"], decompiled_chm["table_structures"]
        )
        if decompiled_chm["table_structure_issues"]:
            issues.append("chm_decompiled_table_structure_mismatch")
        if decompiled_chm["missing_images"]:
            issues.append("chm_decompiled_images_missing")
        if decompiled_chm["image_files"] < source["unique_image_sources"]:
            issues.append("chm_decompiled_image_files_missing")

    if docx["table_count"] != source["table_count"]:
        issues.append("docx_table_count_mismatch")
    if docx["gridspan_count"] != source["docx_gridspan_slots"]:
        issues.append("docx_gridspan_count_mismatch")
    if docx["vmerge_count"] != source["rowspan_slots"]:
        issues.append("docx_vmerge_count_mismatch")
    docx["table_structure_issues"] = compare_docx_table_structures(
        source["table_structures"], docx["table_structures"]
    )
    if docx["table_structure_issues"]:
        issues.append("docx_table_structure_mismatch")
    if docx["drawing_count"] != source["image_occurrences"]:
        issues.append("docx_drawing_count_mismatch")
    if docx["media_files"] < source["unique_image_sources"]:
        issues.append("docx_media_files_missing")
    if docx["duplicate_suit_alt_text"]:
        issues.append("docx_duplicate_suit_alt_text")
    if docx["legacy_skill_markers"]:
        issues.append("docx_legacy_skill_markers_present")
    if docx["explicit_page_break_count"] or docx["page_break_before_count"]:
        issues.append("docx_forced_page_break_present")
    if docx_word_print is not None:
        if docx_word_print["page_count"] == 0 or docx_word_print["text_chars"] == 0:
            issues.append("docx_word_print_empty")
        if docx_word_print["missing_section_labels"]:
            issues.append("docx_word_print_section_labels_missing")
        if docx_word_print["missing_prose_blocks"]:
            issues.append("docx_word_print_prose_blocks_missing")
        if docx_word_print["unique_image_xrefs"] < source["unique_image_sources"]:
            issues.append("docx_word_print_images_missing")
        if docx_word_print["duplicate_suit_alt_text"]:
            issues.append("docx_word_print_duplicate_suit_alt_text")
        if docx_word_print["legacy_skill_markers"]:
            issues.append("docx_word_print_legacy_skill_markers_present")

    if pdf["page_count"] == 0 or pdf["text_chars"] == 0:
        issues.append("pdf_empty")
    if pdf["missing_section_labels"]:
        issues.append("pdf_section_labels_missing")
    if pdf["missing_prose_blocks"]:
        issues.append("pdf_prose_blocks_missing")
    if pdf["duplicate_suit_alt_text"]:
        issues.append("pdf_duplicate_suit_alt_text")
    if pdf["legacy_skill_markers"]:
        issues.append("pdf_legacy_skill_markers_present")
    if pdf["unique_image_xrefs"] < source["unique_image_sources"]:
        issues.append("pdf_images_missing")
    if pdf["unembedded_cjk_fonts"] or pdf["embedded_font_count"] == 0:
        issues.append("pdf_cjk_font_not_embedded")

    report = {
        "schema_version": 1,
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "source": source,
        "chm": {
            "compiled_path": chm_path.relative_to(REPO_ROOT).as_posix(),
            "compiled_bytes": chm_path.stat().st_size if chm_path.exists() else 0,
            "generated": generated_chm,
            "decompiled": decompiled_chm,
        },
        "docx": docx,
        "docx_word_print": {
            "path": docx_word_print_path.relative_to(REPO_ROOT).as_posix(),
            **docx_word_print,
        }
        if docx_word_print_path and docx_word_print is not None
        else None,
        "pdf": pdf,
        "pdf_html_raw_brace_coverage": pdf_html_braces,
        "manual_gates": {
            "chm_decompiled_payload_visual": args.chm_payload_visual_status,
            "chm_viewer_visual": args.chm_viewer_status,
            "docx_word_open": args.docx_open_status,
            "docx_page_visual": args.docx_page_visual_status,
            "pdf_page_visual": args.pdf_visual_status,
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "issues": issues}, ensure_ascii=False))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
