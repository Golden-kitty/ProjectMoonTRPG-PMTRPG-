from __future__ import annotations

import re
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
REPORT_PATH = REPO_ROOT / "docs" / "acceptance" / "export-readiness-audit.md"

EXCLUDE_FILES = {
    "PDF图片索引.md",
    "PDF章节页码映射.md",
    "project-brief.md",
    "project-memory.md",
    "project-terminology.md",
    "表格重建清单.md",
}
EXCLUDE_PREFIXES = ("acceptance/", "tasks/", "engineering/")

SAMPLE_DOCS = [
    "核心规则/基本规则/等级.md",
    "核心规则/速查图表/技能列表.md",
    "核心规则/战斗/战斗流程.md",
    "资源目录/装备/武器/奇门.md",
]

HTML_TAG_RE = re.compile(r"</?(?P<tag>\w+)[^>]*>")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.M)
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
HTML_IMAGE_RE = re.compile(r"""<img[^>]+src=['"]([^'"]+)['"]""", re.I)
TABLE_RE = re.compile(r"<table\b[\s\S]*?</table\s*>", re.I)


def iter_docs() -> list[tuple[Path, str]]:
    docs: list[tuple[Path, str]] = []
    for path in sorted(DOCS_DIR.rglob("*.md")):
        rel = path.relative_to(DOCS_DIR).as_posix()
        if rel in EXCLUDE_FILES:
            continue
        if any(rel.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
            continue
        docs.append((path, rel))
    return docs


def analyze_file(path: Path, rel: str) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    headings = [m for m in HEADING_RE.finditer(text)]
    h1_count = sum(1 for m in headings if len(m.group(1)) == 1)
    no_heading = not headings
    no_h1 = bool(headings) and h1_count == 0
    tables = len(TABLE_RE.findall(text))
    nbspace = text.count("\xa0")
    replacement_char = text.count("\ufffd")

    html_tags: Counter[str] = Counter()
    for match in HTML_TAG_RE.finditer(text):
        tag = match.group("tag").lower()
        if tag not in {"br", "img", "sub", "sup"}:
            html_tags[tag] += 1

    image_refs: list[str] = []
    image_refs.extend(m.group(1) for m in MD_IMAGE_RE.finditer(text))
    image_refs.extend(m.group(1) for m in HTML_IMAGE_RE.finditer(text))
    image_hook_dependent = [src for src in image_refs if src.startswith("../") and "assets/" in src]

    non_heading_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    stub = len(non_heading_lines) <= 1

    return {
        "rel": rel,
        "tables": tables,
        "no_heading": no_heading,
        "no_h1": no_h1,
        "nbspace": nbspace,
        "replacement_char": replacement_char,
        "html_tags": html_tags,
        "image_hook_dependent": image_hook_dependent,
        "stub": stub,
    }


def bucket_file(info: dict[str, object]) -> str | None:
    if info["tables"] or info["image_hook_dependent"] or info["no_heading"]:
        return "A-阻塞导出"
    if info["no_h1"] or info["nbspace"] or info["replacement_char"]:
        return "B-高风险退化"
    if info["stub"]:
        return "C-导航空壳"
    return None


def build_report(results: list[dict[str, object]]) -> str:
    bucketed: dict[str, list[str]] = {
        "A-阻塞导出": [],
        "B-高风险退化": [],
        "C-导航空壳": [],
    }
    html_tag_counts: Counter[str] = Counter()
    stats = Counter()

    sample_notes: list[str] = []
    for info in results:
        rel = str(info["rel"])
        bucket = bucket_file(info)
        if bucket:
            bucketed[bucket].append(rel)
        html_tag_counts.update(info["html_tags"])
        if info["tables"]:
            stats["files_with_tables"] += 1
            stats["table_blocks"] += int(info["tables"])
        if info["no_heading"]:
            stats["no_heading"] += 1
        if info["no_h1"]:
            stats["no_h1"] += 1
        if info["stub"]:
            stats["stub"] += 1
        if info["nbspace"] or info["replacement_char"]:
            stats["encoding"] += 1
        if info["image_hook_dependent"]:
            stats["hook_images"] += 1

        if rel in SAMPLE_DOCS:
            sample_notes.append(
                "- `{}`: tables={}, no_heading={}, no_h1={}, hook_image_refs={}, nbspace={}".format(
                    rel,
                    info["tables"],
                    info["no_heading"],
                    info["no_h1"],
                    len(info["image_hook_dependent"]),
                    info["nbspace"],
                )
            )

    lines = [
        "# Export Readiness Audit",
        "",
        "## Summary",
        "",
        f"- 扫描文件数：`{len(results)}`",
        f"- 含 HTML table 的文件：`{stats['files_with_tables']}`",
        f"- HTML table 块数：`{stats['table_blocks']}`",
        f"- 无任何标题的文件：`{stats['no_heading']}`",
        f"- 有标题但无 H1 的文件：`{stats['no_h1']}`",
        f"- 站点空壳页：`{stats['stub']}`",
        f"- 含编码工件的文件：`{stats['encoding']}`",
        f"- 依赖站点 hook 重写图片路径的文件：`{stats['hook_images']}`",
        "",
        "## Bucket Policy",
        "",
        "- `A-阻塞导出`：HTML table、关键图片路径依赖 hook、无标题正文页。",
        "- `B-高风险退化`：无 H1、编码工件、其他会显著影响导出结构但不必然阻塞的项。",
        "- `C-导航空壳`：主要用于站点分组、在 PDF / CHM 中会退化为空白章节的页面。",
        "- 纯站点分组页默认不进入导出书籍正文；若需要进入导出，则必须补最小概览正文。",
        "",
        "## Sample Docs",
        "",
    ]
    lines.extend(sample_notes or ["- 无"])
    lines.extend(
        [
            "",
            "## Global HTML Tag Distribution",
            "",
            "| Tag | Count |",
            "| --- | ---: |",
        ]
    )
    for tag, count in html_tag_counts.most_common(10):
        lines.append(f"| `{tag}` | {count} |")

    for bucket_name in ("A-阻塞导出", "B-高风险退化", "C-导航空壳"):
        entries = bucketed[bucket_name]
        lines.extend(
            [
                "",
                f"## {bucket_name}",
                "",
                f"- 文件数：`{len(entries)}`",
            ]
        )
        for rel in entries[:30]:
            lines.append(f"- `{rel}`")
        if len(entries) > 30:
            lines.append(f"- 其余 `{len(entries) - 30}` 个文件已省略，后续按批次处理。")

    lines.extend(
        [
            "",
            "## Export Stub Strategy",
            "",
            "- 对仅作为站点目录占位的概览页，导出阶段应过滤，不生成 PDF / CHM 正文章节。",
            "- 对需要在书籍中保留的概览页，应在后续批次补最小正文，而不是继续保留单行标题。",
            "- 样本集中的文件必须具备真实章节内容，不允许以占位页替代。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    results = [analyze_file(path, rel) for path, rel in iter_docs()]
    report = build_report(results)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
