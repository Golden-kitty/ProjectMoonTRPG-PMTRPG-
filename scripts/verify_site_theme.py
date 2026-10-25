"""独立核对网站主题迁移；只读构建结果，只写显式指定的 JSON 报告。

历史正文比较需要构建前的 .md-content__inner 快照。无快照时仍可在 CI
检查完整公开文档集合、资源、导航、搜索和语义标注，但不会声称历史保真通过。
不导入主题适配器，也不运行构建、发布或 CHM 流程。
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import fnmatch
import hashlib
from html import unescape
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup, Tag
import yaml


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "output/evidence/site-theme-20261025"
SOURCE_SELECTOR = ".pmtrpg-source-content"
SIGNATURE_FIELDS = ("text", "ids", "headings", "links", "images", "emphasis", "tables")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf8"))


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf8")).hexdigest()


def compact(node) -> str:
    return re.sub(r"\s+", "", node.get_text() if isinstance(node, Tag) else str(node))


def styles(node: Tag) -> dict[str, str]:
    return {key.lower(): value.strip().lower() for key, value in
            re.findall(r"(?:^|;)\s*([\w-]+)\s*:\s*([^;]+)", node.get("style", ""))}


def signature(content: Tag) -> dict:
    """保留原文顺序和所有非空白字符；表格逐行逐格比较，包含嵌套位置。"""
    tables = []
    for table in content.find_all("table"):
        rows = [row for row in table.find_all("tr") if row.find_parent("table") is table]
        tables.append({
            "id": table.get("data-table-id"),
            "ancestors": [parent.get("data-table-id") for parent in reversed(table.find_parents("table"))],
            "rows": [[{
                "tag": cell.name, "rowspan": cell.get("rowspan"), "colspan": cell.get("colspan"),
                "text": compact(cell),
            } for cell in row.find_all(["td", "th"])
                if cell.find_parent("tr") is row and cell.find_parent("table") is table] for row in rows],
        })
    return {
        "text": compact(content),
        "ids": [node.get("id") for node in content.find_all(id=True)],
        "headings": [{"tag": node.name, "id": node.get("id"), "text": compact(node)}
                     for node in content.find_all(re.compile(r"^h[1-6]$"))],
        "links": [{"href": node.get("href"), "text": compact(node), "title": node.get("title")}
                  for node in content.find_all("a", href=True)],
        "images": [{key: node.get(key) for key in ("src", "alt", "title", "srcset")}
                   for node in content.find_all("img")],
        "emphasis": [{"tag": node.name, "text": compact(node)}
                     for node in content.find_all(["b", "strong", "i", "em", "sup", "sub", "u", "s", "del"])],
        "tables": tables,
    }


def counts(value: dict) -> dict:
    cells = [cell for table in value["tables"] for row in table["rows"] for cell in row]
    return {
        "characters": len(value["text"]), "headings": len(value["headings"]),
        "links": len(value["links"]), "images": len(value["images"]),
        "tables": len(value["tables"]), "cells": len(cells),
        "nested_tables": sum(bool(t["ancestors"]) for t in value["tables"]),
        "colspan_cells": sum(c["colspan"] is not None for c in cells),
        "rowspan_cells": sum(c["rowspan"] is not None for c in cells),
    }


def local_target(site: Path, page: Path, url: str) -> Path | None:
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    path = unquote(parsed.path).replace("\\", "/")
    target = site / path.lstrip("/") if path.startswith("/") else page.parent / path
    return target.resolve()


def nav_paths(node) -> list[str]:
    if isinstance(node, list):
        return [path for child in node for path in nav_paths(child)]
    if isinstance(node, dict):
        return [path for child in node.values() for path in nav_paths(child)]
    return [node] if isinstance(node, str) and node.endswith(".md") else []


def public_pages(config: dict) -> set[str]:
    exclusions = [line.strip() for line in config.get("exclude_docs", "").splitlines()
                  if line.strip() and not line.lstrip().startswith("#")]
    docs = ROOT / config.get("docs_dir", "docs")
    return {path.relative_to(docs).with_suffix(".html").as_posix() for path in docs.rglob("*.md")
            if not any(fnmatch.fnmatch(path.relative_to(docs).as_posix(), pattern) for pattern in exclusions)}


def search_check(site: Path, sources: dict[str, Tag]) -> dict:
    path = site / "search/search_index.json"
    if not path.is_file():
        return {"exists": False, "issues": [{"code": "search_index_missing"}]}
    data = load(path)
    by_page = defaultdict(list)
    for item in data.get("docs", []):
        key = unquote(urlsplit(item.get("location", "")).path)
        by_page[key].append(item)
    issues = []
    checked_blocks = 0
    for relative, source in sources.items():
        if relative not in by_page:
            issues.append({"code": "search_document_missing", "page": relative})
            continue
        text_fragments = [item.get("text", "") for item in by_page[relative]]
        indexed = "".join(compact(BeautifulSoup(text, "html.parser")) if "<" in text else compact(unescape(text))
                          for text in text_fragments)
        for block in source.select("p, li, td, th, pre, blockquote"):
            text = compact(block)
            if len(text) < 4 or not re.search(r"[\u3400-\u9fff]", text):
                continue
            # Long parent blocks can include section-heading permutations. Leaf
            # prose/cells are the independent evidence that search contains rules.
            if block.find(["p", "li", "td", "th", "pre", "blockquote"]):
                continue
            checked_blocks += 1
            if text not in indexed:
                issues.append({"code": "search_body_text_missing", "page": relative, "excerpt": text[:120]})
    return {"exists": True, "entries": len(data.get("docs", [])), "indexed_documents": len(by_page),
            "chinese_body_blocks_checked": checked_blocks, "issues": issues}


def semantic_reference(reference: Path, pages: dict[str, Tag]) -> dict:
    """直接对照原呈现证据的表序/行内格序，不读取新适配器的匹配结果。

    Word 的 col 是带历史空网格的逻辑列，不能用作 HTML 物理格下标。
    每行按原 col 排序后逐格检查文字，可独立发现同文表误复用第一表的问题。
    """
    if not reference.is_file():
        return {"status": "NOT_RUN", "reason": "原始呈现证据不存在；不会以固定数量代替实际匹配。"}
    documents = load(reference)["documents"]
    matched, unmatched, issues, excluded = [], [], [], []
    expected_locations = set()
    by_document = Counter()
    weapon_diagrams = []
    for source_path, document in documents.items():
        key = Path(source_path).with_suffix(".html").as_posix()
        new = pages.get(key)
        tables = new.find_all("table") if new else []
        for table_index, old_table in enumerate(document.get("tables", [])):
            groups = defaultdict(list)
            for old_cell in old_table.get("cells", []):
                groups[old_cell["row"]].append(old_cell)
            current = tables[table_index] if table_index < len(tables) else None
            rows = [row for row in current.find_all("tr") if row.find_parent("table") is current] if current else []
            table_colors = []
            for row_index, old_cells in sorted(groups.items()):
                row = rows[row_index] if row_index < len(rows) else None
                cells = [cell for cell in row.find_all(["td", "th"]) if cell.find_parent("table") is current
                         and cell.find_parent("tr") is row] if row else []
                for cell_index, old_cell in enumerate(sorted(old_cells, key=lambda cell: cell["col"])):
                    declaration = re.search(r"(?:^|;)\s*background(?:-color)?\s*:\s*([^;]+)", old_cell.get("style", ""), re.I)
                    color = declaration[1].strip().lower() if declaration else ""
                    if color == "#2e2217" or not re.fullmatch(r"#[0-9a-f]{6}|red|yellow", color):
                        continue
                    record = {"page": key, "table_ordinal": table_index, "row": row_index, "cell": cell_index,
                              "text": compact(old_cell.get("text", "")), "reference_background": color}
                    if current is None:
                        excluded.append({**record, "reason": "现行源文不存在该参考表；不恢复旧规则内容"})
                        continue
                    record["table_id"] = current.get("data-table-id")
                    if cell_index >= len(cells) or compact(cells[cell_index]) != record["text"]:
                        unmatched.append(record)
                        continue
                    target = cells[cell_index]
                    actual = styles(target)
                    record["background"] = actual.get("--cell-bg", actual.get("background-color", ""))
                    record["foreground"] = actual.get("--cell-ink", actual.get("color", ""))
                    matched.append(record)
                    expected_locations.add((key, record["table_id"], row_index, cell_index))
                    by_document[key] += 1
                    table_colors.append({"cell": cell_index, "text": record["text"], "background": color})
                    aliases = {"red": "#ff0000", "yellow": "#ffff00"}
                    normalize = lambda value: aliases.get(value, value)
                    if normalize(record["background"]) != normalize(color):
                        issues.append({"code": "semantic_color_changed", **record})
                    try:
                        ratio = color_contrast(record["background"], record["foreground"])
                    except ValueError:
                        ratio = 0
                    record["contrast"] = round(ratio, 4)
                    if ratio < 4.5:
                        issues.append({"code": "semantic_color_contrast", **record})
            if "武器类与武器属性" in key and current:
                heading = current.find_previous(re.compile(r"^h[1-6]$"))
                weapon_diagrams.append({"table_id": current.get("data-table-id"), "heading": compact(heading) if heading else "",
                                        "colors": table_colors})
    observed_locations = set()
    for key, source in pages.items():
        for table in source.find_all("table"):
            rows = [row for row in table.find_all("tr") if row.find_parent("table") is table]
            for row_index, row in enumerate(rows):
                cells = [cell for cell in row.find_all(["td", "th"]) if cell.find_parent("table") is table and cell.find_parent("tr") is row]
                for cell_index, cell in enumerate(cells):
                    if "reader-color-cell" in cell.get("class", []):
                        observed_locations.add((key, table.get("data-table-id"), row_index, cell_index))
    if observed_locations != expected_locations:
        issues.append({"code": "semantic_color_location_set_changed", "missing": sorted(expected_locations - observed_locations),
                       "unexpected": sorted(observed_locations - expected_locations)})
    manifest_file = ROOT / "assets/site/semantic-presentation.json"
    manifest_verified = False
    if not manifest_file.is_file():
        issues.append({"code": "portable_semantic_manifest_missing"})
    else:
        manifest = load(manifest_file)
        portable = {}
        for doc_path, document in manifest.get("documents", {}).items():
            key = Path(doc_path).with_suffix(".html").as_posix()
            for table_id, table in document.get("tables", {}).items():
                for cell in table.get("cells", []):
                    if "background" in cell:
                        portable[(key, table_id, cell["row"], cell["cell"])] = (compact(cell["text"]), cell["background"])
        expected_portable = {(item["page"], item["table_id"], item["row"], item["cell"]):
                             (item["text"], {"red": "#ff0000", "yellow": "#ffff00"}.get(item["reference_background"], item["reference_background"]))
                             for item in matched}
        manifest_verified = portable == expected_portable and manifest.get("reference_sha256") == hashlib.sha256(reference.read_bytes()).hexdigest()
        if not manifest_verified:
            issues.append({"code": "portable_semantic_manifest_differs_from_reference", "manifest_cells": len(portable),
                           "independently_matched_cells": len(expected_portable)})
    return {"status": "PASS" if not issues and not unmatched else "FAIL", "reference": str(reference),
            "reference_cells": len(matched) + len(unmatched), "matched_cells": len(matched), "by_document": dict(by_document),
            "portable_manifest_independently_verified": manifest_verified,
            "unmatched": unmatched, "excluded_reference_only_cells": excluded, "issues": issues, "cells": matched,
            "weapon_diagrams": weapon_diagrams,
            "preview_difference": "旧预览将五个 A1/B2/C3 同文表误用首表颜色；原证据与现行单手/便携/重型/大型/巨型上下文支持各表 2/1/3/2/3 个色格，合计比旧预览多 1 格。"}


def color_contrast(a: str, b: str) -> float:
    def luminance(value: str) -> float:
        value = {"red": "#ff0000", "yellow": "#ffff00", "white": "#ffffff", "black": "#000000"}.get(value, value)
        if not re.fullmatch(r"#[0-9a-f]{6}", value):
            raise ValueError(value)
        channels = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
        return sum(c * weight for c, weight in zip(linear, [.2126, .7152, .0722]))
    lower, upper = sorted([luminance(a), luminance(b)])
    return (upper + .05) / (lower + .05)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=ROOT / "site")
    parser.add_argument("--baseline", type=Path, help="构建前 article HTML 快照；省略时仅使用本地现有默认快照")
    parser.add_argument("--protected", type=Path, help="受保护文件的构建前 SHA-256 清单")
    parser.add_argument("--reference", type=Path, help="原始呈现 JSON 证据；默认 assets/chm/presentation-v184.json")
    parser.add_argument("--report", type=Path, default=EVIDENCE / "static-checks.json")
    parser.add_argument("--no-history", action="store_true", help="CI 模式，不自动读取本地 output 历史证据")
    args = parser.parse_args()
    site = args.site.resolve()
    config = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf8"))
    expected = public_pages(config)
    baseline_path = args.baseline or (None if args.no_history else EVIDENCE / "baseline-content.json")
    protected_path = args.protected or (None if args.no_history else EVIDENCE / "protected-baseline.json")
    baseline = load(baseline_path) if baseline_path and baseline_path.is_file() else None
    protected = load(protected_path) if protected_path and protected_path.is_file() else None
    if args.baseline and not args.baseline.is_file():
        parser.error(f"明确指定的基线不存在：{args.baseline}")
    if args.protected and not args.protected.is_file():
        parser.error(f"明确指定的保护清单不存在：{args.protected}")
    issues, page_reports, resources = [], [], []
    soups, sources = {}, {}
    totals, old_totals = Counter(), Counter()
    resource_targets = set()
    external_resources = set()
    expected_nav = {Path(p).with_suffix(".html").as_posix() for p in nav_paths(config.get("nav", []))}
    for relative in sorted(expected):
        page = site / relative
        if not page.is_file():
            issues.append({"code": "document_missing", "page": relative})
            continue
        soup = BeautifulSoup(page.read_text(encoding="utf8"), "html.parser")
        soups[relative] = soup
        containers = soup.select(SOURCE_SELECTOR)
        if len(containers) != 1:
            issues.append({"code": "source_container_count", "page": relative, "observed": len(containers)})
            source = soup.select_one(".md-content__inner")
        else:
            source = containers[0]
        if source is None:
            continue
        sources[relative] = source
        actual = signature(source)
        totals.update(counts(actual))
        item = {"page": relative, "counts": counts(actual), "signature_sha256": digest(actual)}
        if baseline is not None:
            old = BeautifulSoup(baseline.get(relative, ""), "html.parser").select_one(".md-content__inner")
            if old is None:
                issues.append({"code": "baseline_document_missing", "page": relative})
            else:
                original = signature(old)
                old_totals.update(counts(original))
                item["matches"] = {key: actual[key] == original[key] for key in SIGNATURE_FIELDS}
                for key, match in item["matches"].items():
                    if not match:
                        issues.append({"code": "content_changed", "page": relative, "dimension": key,
                                       "expected_sha256": digest(original[key]), "actual_sha256": digest(actual[key])})
        for table in source.select("table.pmtrpg-table"):
            if table.find_parent("table") is None and table.find_parent(class_="pmtrpg-table-scroll") is None:
                issues.append({"code": "table_scroll_container_missing", "page": relative, "table_id": table.get("data-table-id")})
        primary = soup.select_one(".md-nav--primary")
        if primary is None or not soup.select_one('[data-md-component="search"]'):
            issues.append({"code": "material_navigation_or_search_missing", "page": relative})
        for node, attr in [(n, "href") for n in soup.select('link[rel~="stylesheet"][href]')] + [(n, "src") for n in soup.select("script[src], img[src]")]:
            url = node[attr]
            target = local_target(site, page, url)
            if "output/" in unquote(url).replace("\\", "/") or "127.0.0.1" in url or "localhost" in url:
                issues.append({"code": "nonportable_resource", "page": relative, "url": url})
            if target is None:
                external_resources.add(url)
                continue
            if not target.is_relative_to(site):
                issues.append({"code": "resource_outside_site", "page": relative, "url": url})
            elif not target.is_file():
                issues.append({"code": "local_resource_missing", "page": relative, "url": url})
            else:
                resource_targets.add(target)
            if url.startswith("/"):
                issues.append({"code": "root_absolute_resource_on_project_site", "page": relative, "url": url})
        # Existing rule links are compared byte-for-byte above. Only newly added
        # template links are required to resolve, so legacy source defects cannot
        # be disguised as theme regressions or silently rewritten by this gate.
        for link in soup.select("a[href]"):
            if source in link.parents:
                continue
            target = local_target(site, page, link["href"])
            if target is not None and (not target.is_relative_to(site) or not target.exists()):
                issues.append({"code": "template_link_missing", "page": relative, "href": link["href"]})
            parsed = urlsplit(link["href"])
            if not parsed.scheme and not parsed.netloc and not parsed.path and parsed.fragment and not soup.find(id=unquote(parsed.fragment)):
                issues.append({"code": "template_local_anchor_missing", "page": relative, "href": link["href"]})
        page_reports.append(item)
    # A page accidentally excluded by a new configuration must not disappear
    # from the denominator of the comparison.
    baseline_pages = set(baseline or {}) - {"index.html", "404.html"}
    if baseline is not None and expected != baseline_pages:
        issues.append({"code": "public_document_set_changed", "missing": sorted(baseline_pages - expected), "added": sorted(expected - baseline_pages)})
    home = soups.get("PM_TRPG.html")
    observed_nav = set()
    if home:
        for link in home.select(".md-nav--primary a[href]"):
            target = local_target(site, site / "PM_TRPG.html", link["href"])
            if target and target.is_relative_to(site):
                observed_nav.add(target.relative_to(site).as_posix())
    if not expected_nav.issubset(observed_nav):
        issues.append({"code": "navigation_documents_missing", "pages": sorted(expected_nav - observed_nav)})
    alias = site / "index.html"
    if not alias.is_file() or not (site / "PM_TRPG.html").is_file() or alias.read_bytes() != (site / "PM_TRPG.html").read_bytes():
        issues.append({"code": "homepage_alias_differs"})
    # Follow CSS url() references as well as HTML links: nested document pages
    # can load the stylesheet while the stylesheet's fonts/backgrounds fail.
    for path in sorted(resource_targets):
        if path.suffix.lower() not in {".css", ".js"}:
            continue
        code = path.read_text(encoding="utf8")
        if re.search(r"(?:[./])output/|127\.0\.0\.1|localhost", code):
            issues.append({"code": "resource_code_depends_on_local_output", "path": path.relative_to(site).as_posix()})
        if path.suffix.lower() == ".css":
            for raw in re.findall(r"url\(\s*([^)]*?)\s*\)", code):
                url = raw.strip("\"'")
                target = local_target(site, path, url)
                if target is not None and (not target.is_relative_to(site) or not target.is_file()):
                    issues.append({"code": "css_resource_missing", "path": path.relative_to(site).as_posix(), "url": url})
        resources.append({"path": path.relative_to(site).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    search = search_check(site, sources)
    issues.extend(search.get("issues", []))
    protected_differences = []
    for relative, expected_sha in (protected or {}).items():
        path = ROOT / relative
        actual_sha = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if actual_sha != expected_sha:
            protected_differences.append({"path": relative, "expected": expected_sha, "actual": actual_sha})
    issues.extend({"code": "protected_file_changed", **item} for item in protected_differences)
    reference = args.reference or ROOT / "assets/chm/presentation-v184.json"
    colors = semantic_reference(reference, sources)
    if colors["status"] == "NOT_RUN":
        issues.append({"code": "semantic_reference_missing", "path": str(reference)})
    issues.extend(colors.get("issues", []))
    if colors.get("unmatched"):
        issues.append({"code": "historical_semantic_cells_unmatched", "cells": colors["unmatched"]})
    report = {
        "status": "PASS" if not issues else "FAIL", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "静态保真与可移植性；不证明浏览器视觉、运行时交互、真实手机或 CHM 原生通过。",
        "site": str(site), "public_documents": len(expected), "observed_documents": len(sources),
        "navigation_documents": len(expected_nav), "baseline_comparison": "RUN" if baseline is not None else "NOT_RUN",
        "protected_comparison": "RUN" if protected is not None else "NOT_RUN", "protected_files": len(protected or {}),
        "original_counts": dict(old_totals), "current_counts": dict(totals),
        "pages": page_reports, "search": search, "semantic_colors": colors,
        "local_resources": resources, "external_resources": sorted(external_resources),
        "issue_count": len(issues), "issues": issues,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({key: report[key] for key in ("status", "public_documents", "observed_documents", "navigation_documents", "baseline_comparison", "issue_count")}, ensure_ascii=False))
    print(f"报告：{args.report}")
    return 0 if not issues else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf8")
    raise SystemExit(main())
