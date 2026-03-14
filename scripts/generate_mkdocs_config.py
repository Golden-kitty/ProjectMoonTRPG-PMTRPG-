from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
CHAPTER_MAP = REPO_ROOT / "docs" / "PDF章节页码映射.md"
OUTPUT_FILE = REPO_ROOT / "mkdocs.yml"

INTERNAL_DOCS = {
    "PDF图片索引.md",
    "PDF章节页码映射.md",
    "project-brief.md",
    "project-memory.md",
    "表格重建清单.md",
}

INTERNAL_PREFIXES = (
    "acceptance/",
    "tasks/",
)

SUPPLEMENTAL_CHILDREN = {
    "4.12 成瘾品": [
        ("精神成瘾品", "资源目录/消耗品/成瘾品/精神成瘾品.md"),
    ],
    "4.19 课程": [
        ("能力课程", "资源目录/课程/能力课程.md"),
    ],
    "5.2 武器设计": [
        ("奇门", "创作指南/武器设计/奇门.md"),
    ],
}

# These entries have children but no reliable single landing page in the current
# Markdown tree, so they are rendered as section-only nodes.
SECTION_ONLY_TITLES = {
    "4.7.1 传闻",
    "4.7.2 怪谈",
    "4.8.1 传闻",
    "4.8.2 怪谈",
    "4.18.1 武器",
}

TOP_LEVEL_TITLE_OVERRIDES = {
    "1. PM_TRPG": "首页",
}

ENTRY_RE = re.compile(
    r"^(?P<indent>\s*)- \*\*(?P<title>.+?)\*\*（\[P\d+\]\([^)]+\)）(?P<tail>.*)$"
)
DOC_LINK_RE = re.compile(r"\[`docs/(?P<path>[^`]+)`\]\((?P=path)\)")


@dataclass
class NavEntry:
    level: int
    title: str
    label: str
    candidates: list[str]
    children: list["NavEntry"] = field(default_factory=list)
    path: str | None = None


def parse_chapter_map(chapter_map: Path) -> list[NavEntry]:
    entries: list[NavEntry] = []
    for line in chapter_map.read_text(encoding="utf-8").splitlines():
        match = ENTRY_RE.match(line)
        if not match:
            continue
        indent = match.group("indent")
        title = match.group("title").strip()
        tail = match.group("tail")
        candidates = [m.group("path").replace("\\", "/") for m in DOC_LINK_RE.finditer(tail)]
        entries.append(
            NavEntry(
                level=(len(indent) // 2) + 1,
                title=title,
                label=strip_number_prefix(title),
                candidates=candidates,
            )
        )
    if not entries:
        raise SystemExit(f"No chapter map entries parsed from: {chapter_map}")
    return entries


def build_tree(entries: list[NavEntry]) -> list[NavEntry]:
    roots: list[NavEntry] = []
    stack: list[NavEntry] = []
    for entry in entries:
        while stack and stack[-1].level >= entry.level:
            stack.pop()
        if stack:
            stack[-1].children.append(entry)
        else:
            roots.append(entry)
        stack.append(entry)
    return roots


def inject_supplemental_children(nodes: list[NavEntry]) -> None:
    for node in nodes:
        extras = SUPPLEMENTAL_CHILDREN.get(node.title, [])
        if extras:
            existing_paths = {child.path or next(iter(child.candidates), "") for child in node.children}
            for title, path in extras:
                if path in existing_paths:
                    continue
                node.children.append(
                    NavEntry(
                        level=node.level + 1,
                        title=title,
                        label=strip_number_prefix(title),
                        candidates=[path],
                        path=path,
                    )
                )
        inject_supplemental_children(node.children)


def strip_number_prefix(title: str) -> str:
    match = re.match(r"^\d+(?:\.\d+)*\s+(.*)$", title)
    return match.group(1).strip() if match else title.strip()


def should_exclude_doc(path: str) -> bool:
    path = path.replace("\\", "/")
    if path in INTERNAL_DOCS:
        return True
    return any(path.startswith(prefix) for prefix in INTERNAL_PREFIXES)


def iter_ancestors(stack: Iterable[NavEntry]) -> list[NavEntry]:
    return list(stack)


def score_candidate(entry: NavEntry, candidate: str, ancestors: list[NavEntry]) -> int:
    score = 0
    candidate = candidate.replace("\\", "/")
    stem = Path(candidate).stem

    entry_label = entry.label
    if entry_label and entry_label == stem:
        score += 6
    if entry_label and f"/{entry_label}/" in candidate:
        score += 4
    if entry_label and entry_label in candidate:
        score += 2

    ancestor_labels = [ancestor.label for ancestor in ancestors]
    for label in ancestor_labels:
        if not label:
            continue
        if f"/{label}/" in candidate:
            score += 5
        elif label in candidate:
            score += 2

    context_labels = {entry.label, *ancestor_labels}
    if "怪谈" in context_labels:
        if "/怪谈/" in candidate or stem == "怪谈":
            score += 8
        if "/传闻/" in candidate or stem == "传闻":
            score -= 4
    if "传闻" in context_labels:
        if "/传闻/" in candidate or stem == "传闻":
            score += 8
        if "/怪谈/" in candidate or stem == "怪谈":
            score -= 4
    if "医疗品" in context_labels and "/医疗品/" in candidate:
        score += 8
    if "工具" in context_labels and "/工具/" in candidate:
        score += 8
    if "机体" in context_labels and "/机体/" in candidate:
        score += 6
    if "部件" in context_labels and "/部件/" in candidate:
        score += 6

    # Prefer shorter, more specific paths when scores tie.
    score -= candidate.count("/") // 10
    return score


def resolve_entry_path(entry: NavEntry, ancestors: list[NavEntry]) -> str | None:
    if entry.title in SECTION_ONLY_TITLES:
        return None

    candidates = [candidate for candidate in entry.candidates if not should_exclude_doc(candidate)]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    scored = sorted(
        ((score_candidate(entry, candidate, ancestors), candidate) for candidate in candidates),
        key=lambda item: (item[0], -len(item[1]), item[1]),
        reverse=True,
    )
    best_score, best_candidate = scored[0]
    if len(scored) > 1 and scored[1][0] == best_score:
        return None
    return best_candidate if best_score > 0 else None


def assign_paths(nodes: list[NavEntry], ancestors: list[NavEntry] | None = None) -> None:
    chain = ancestors or []
    for node in nodes:
        node.path = resolve_entry_path(node, chain)
        assign_paths(node.children, [*chain, node])


def gather_unresolved_leaves(nodes: list[NavEntry]) -> list[NavEntry]:
    unresolved: list[NavEntry] = []
    for node in nodes:
        if node.children:
            unresolved.extend(gather_unresolved_leaves(node.children))
            continue
        if node.candidates and node.path is None:
            unresolved.append(node)
    return unresolved


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_nav(nodes: list[NavEntry], indent: int = 2) -> list[str]:
    lines: list[str] = []
    pad = " " * indent
    for node in nodes:
        title = TOP_LEVEL_TITLE_OVERRIDES.get(node.title, node.title)
        if node.children:
            lines.append(f"{pad}- {yaml_quote(title)}:")
            if node.path:
                lines.append(f"{pad}  - {yaml_quote('概览')}: {yaml_quote(node.path)}")
            lines.extend(render_nav(node.children, indent + 2))
            continue
        if not node.path:
            raise SystemExit(f"Leaf entry has no resolved path: {node.title}")
        lines.append(f"{pad}- {yaml_quote(title)}: {yaml_quote(node.path)}")
    return lines


def build_config(nav_lines: list[str]) -> str:
    exclude_docs = "\n".join(
        [
            "acceptance/**",
            "tasks/**",
            "PDF图片索引.md",
            "PDF章节页码映射.md",
            "project-brief.md",
            "project-memory.md",
            "表格重建清单.md",
        ]
    )
    lines = [
        "# Generated by scripts/generate_mkdocs_config.py. Do not edit by hand.",
        "site_name: PMTRPG",
        "site_description: Project Moon TRPG 文档站点",
        "repo_url: https://github.com/Golden-kitty/ProjectMoonTRPG-PMTRPG-",
        "repo_name: Golden-kitty/ProjectMoonTRPG-PMTRPG-",
        "docs_dir: docs",
        "site_dir: site",
        "use_directory_urls: false",
        "strict: true",
        "theme:",
        "  name: mkdocs",
        "validation:",
        "  links:",
        "    not_found: ignore",
        "    unrecognized_links: ignore",
        "plugins:",
        "  - search",
        "hooks:",
        "  - scripts/mkdocs_hooks.py",
        "markdown_extensions:",
        "  - tables",
        "  - attr_list",
        "  - md_in_html",
        "  - sane_lists",
        "  - toc:",
        "      permalink: true",
        "exclude_docs: |",
    ]
    lines.extend([f"  {line}" for line in exclude_docs.splitlines()])
    lines.append("nav:")
    lines.extend(nav_lines)
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    entries = parse_chapter_map(CHAPTER_MAP)
    roots = build_tree(entries)
    assign_paths(roots)
    inject_supplemental_children(roots)
    unresolved = gather_unresolved_leaves(roots)
    if unresolved:
        titles = "\n".join(f"- {entry.title}" for entry in unresolved)
        raise SystemExit(f"Unresolved leaf entries in chapter map:\n{titles}")
    config = build_config(render_nav(roots))
    OUTPUT_FILE.write_text(config, encoding="utf-8")
    print(f"wrote {OUTPUT_FILE}")
    print(f"nav_entries {len(entries)}")


if __name__ == "__main__":
    main()
