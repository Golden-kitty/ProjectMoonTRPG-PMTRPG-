"""Compare rendered MkDocs table DOM with the canonical source inventory."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup, Tag

from generate_table_inventory import classify_scope


def rendered_page(site_root: Path, source_path: str) -> Path:
    relative = Path(source_path).relative_to("docs")
    return site_root / relative.with_suffix(".html")


def direct_descendants(table: Tag, name: str | list[str]) -> list[Tag]:
    return [
        node
        for node in table.find_all(name)
        if node.find_parent("table") is table
    ]


def dom_signature(table: Tag) -> dict[str, Any]:
    rows = direct_descendants(table, "tr")
    max_columns = 0
    spans: list[dict[str, int]] = []
    for row_index, row in enumerate(rows, start=1):
        cells = [
            cell
            for cell in row.find_all(["td", "th"])
            if cell.find_parent("table") is table and cell.find_parent("tr") is row
        ]
        columns = 0
        for cell in cells:
            try:
                colspan = max(1, int(cell.get("colspan", 1)))
            except (TypeError, ValueError):
                colspan = 1
            try:
                rowspan = max(1, int(cell.get("rowspan", 1)))
            except (TypeError, ValueError):
                rowspan = 1
            columns += colspan
            if colspan > 1 or rowspan > 1:
                spans.append(
                    {"row": row_index, "colspan": colspan, "rowspan": rowspan}
                )
        max_columns = max(max_columns, columns)
    images = [
        {"src": image.get("src"), "alt": image.get("alt")}
        for image in direct_descendants(table, "img")
    ]
    return {
        "rows": len(rows),
        "columns": max_columns,
        "span_signature": spans,
        "nested_depth": len(table.find_parents("table")),
        "images": images,
    }


def image_identity(image: dict[str, Any]) -> tuple[str | None, str | None]:
    src = image.get("src")
    if src:
        normalized = unquote(str(src)).replace("\\", "/")
        marker = "/assets/"
        if marker in normalized:
            normalized = "assets/" + normalized.split(marker, 1)[1]
    else:
        normalized = None
    return normalized, image.get("alt")


def rendered_image_exists(page: Path, src: str | None, site_root: Path) -> bool:
    if not src:
        return False
    parsed = urlparse(src)
    if parsed.scheme or parsed.netloc:
        return True
    clean = unquote(parsed.path)
    target = site_root / clean.lstrip("/") if clean.startswith("/") else page.parent / clean
    return target.resolve().exists()


def article_tables(soup: BeautifulSoup) -> list[Tag]:
    """Return actual content tables, not theme navigation or code examples."""

    return [
        table
        for table in soup.select("article table")
        if table.find_parent(["pre", "code", "nav"]) is None
    ]


def validate_rendered(inventory: dict[str, Any], site_root: Path) -> dict[str, Any]:
    expected = [item for item in inventory["tables"] if item["scope"] == "source-content"]
    issues: list[dict[str, Any]] = []
    page_cache: dict[Path, BeautifulSoup] = {}
    expected_by_page: dict[Path, set[str]] = {}
    for item in expected:
        expected_by_page.setdefault(rendered_page(site_root, item["path"]), set()).add(item["id"])
    observed_ids: list[str] = []
    structural_fields = ("rows", "columns", "span_signature", "nested_depth")
    for item in expected:
        page = rendered_page(site_root, item["path"])
        if not page.exists():
            issues.append({"code": "page_missing", "id": item["id"], "path": page.as_posix()})
            continue
        soup = page_cache.get(page)
        if soup is None:
            soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
            page_cache[page] = soup
        matches = [table for table in article_tables(soup) if table.get("data-table-id") == item["id"]]
        if len(matches) != 1:
            issues.append(
                {
                    "code": "table_dom_count",
                    "id": item["id"],
                    "path": page.as_posix(),
                    "observed": len(matches),
                    "expected": 1,
                }
            )
            continue
        table = matches[0]
        observed_ids.append(item["id"])
        actual = dom_signature(table)
        changed = [field for field in structural_fields if actual[field] != item[field]]
        if changed:
            issues.append(
                {
                    "code": "rendered_structure_changed",
                    "id": item["id"],
                    "path": page.as_posix(),
                    "fields": changed,
                    "expected": {field: item[field] for field in changed},
                    "observed": {field: actual[field] for field in changed},
                }
            )
        expected_images = [image_identity(image) for image in item["images"]]
        observed_images = [image_identity(image) for image in actual["images"]]
        if expected_images != observed_images:
            issues.append(
                {
                    "code": "rendered_images_changed",
                    "id": item["id"],
                    "path": page.as_posix(),
                    "expected": expected_images,
                    "observed": observed_images,
                }
            )
        for image in actual["images"]:
            if not rendered_image_exists(page, image.get("src"), site_root):
                issues.append(
                    {
                        "code": "rendered_image_missing",
                        "id": item["id"],
                        "path": page.as_posix(),
                        "src": image.get("src"),
                    }
                )

    # Reverse coverage is essential: checking only known IDs lets an omitted
    # source table (or an entire omitted page) silently pass the inventory gate.
    # Inspect every rendered source-content article, including pages absent
    # from the inventory, but never count theme tables or literal code samples.
    scanned_documents = 0
    observed_article_tables = 0
    for page in sorted(site_root.rglob("*.html")):
        relative = page.relative_to(site_root).with_suffix(".md")
        # The build hook copies PM_TRPG.html to the root index.html.
        if relative.as_posix() == "index.md":
            relative = Path("PM_TRPG.md")
        if classify_scope((Path("docs") / relative).as_posix()) != "source-content":
            continue
        soup = page_cache.get(page)
        if soup is None:
            soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        if soup.find("article") is None:
            continue
        scanned_documents += 1
        tables = article_tables(soup)
        observed_article_tables += len(tables)
        expected_ids = expected_by_page.get(site_root / relative.with_suffix(".html"), set())
        for index, table in enumerate(tables, start=1):
            table_id = table.get("data-table-id")
            if not table_id:
                issues.append({
                    "code": "rendered_table_id_missing",
                    "path": page.as_posix(),
                    "table_ordinal": index,
                })
            elif table_id not in expected_ids:
                issues.append({
                    "code": "rendered_table_not_in_inventory",
                    "path": page.as_posix(),
                    "id": table_id,
                    "table_ordinal": index,
                })

    duplicates = sorted(table_id for table_id, count in Counter(observed_ids).items() if count > 1)
    for table_id in duplicates:
        issues.append({"code": "rendered_id_duplicate", "id": table_id})
    return {
        "status": "PASS" if not issues else "FAIL",
        "expected_tables": len(expected),
        "observed_tables": len(observed_ids),
        "rendered_documents": len(page_cache),
        "scanned_documents": scanned_documents,
        "article_tables": observed_article_tables,
        "issue_count": len(issues),
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("docs/engineering/table-inventory.json"),
    )
    parser.add_argument("--site", type=Path, default=Path("site"))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    payload = validate_rendered(inventory, args.site.resolve())
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                key: payload[key]
                for key in (
                    "status",
                    "expected_tables",
                    "observed_tables",
                    "rendered_documents",
                    "issue_count",
                )
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
