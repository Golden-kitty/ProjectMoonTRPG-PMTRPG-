import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import fitz  # pymupdf


@dataclass(frozen=True)
class TocItem:
    level: int
    title: str
    page: int  # 1-based

    @property
    def number_prefix(self) -> str:
        m = re.match(r"^\s*(\d+(?:\.\d+)*)(?:\.)?\s+", self.title)
        return m.group(1) if m else ""

    @property
    def title_wo_number(self) -> str:
        m = re.match(r"^\s*\d+(?:\.\d+)*(?:\.)?\s+(.+?)\s*$", self.title)
        return m.group(1) if m else self.title.strip()


HEADING_RE = re.compile(r"^\s*(#{1,6})\s+(.+?)\s*$")


def norm_key(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.strip().lower()
    # Drop common punctuation/spaces
    s = re.sub(r"[\s·•・、，,。．.：:；;！!？?\(\)（）\[\]【】《》“”\"'‘’`]+", "", s)
    return s


def md_first_title(md_path: Path) -> str:
    try:
        text = md_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = md_path.read_text(encoding="utf-8", errors="replace")

    for line in text.splitlines()[:80]:
        m = HEADING_RE.match(line)
        if m:
            return m.group(2).strip()
    return md_path.stem


def section_root_dir(major: str) -> str | None:
    # Map PDF major section number -> docs subtree
    return {
        "1": "docs",
        "2": "docs/核心规则",
        "4": "docs/资源目录",
        "5": "docs/创作指南",
        "6": "docs/都市箴言",
    }.get(major)


def main() -> None:
    pdf = Path("originFab/Project Moon Trpg Rule Book V1.8.4.pdf")
    out = Path("docs/PDF章节页码映射.md")

    doc = fitz.open(str(pdf))
    toc_raw = doc.get_toc(simple=True)
    toc: list[TocItem] = [TocItem(level=l, title=t, page=p) for l, t, p in toc_raw]

    md_files = [p for p in Path("docs").rglob("*.md") if p.name not in {"PDF图片索引.md", "PDF章节页码映射.md"}]

    # Build lookup: normalized title -> list[Path]
    title_map: dict[str, list[Path]] = {}
    for p in md_files:
        title = md_first_title(p)
        for k in {norm_key(title), norm_key(p.stem)}:
            if not k:
                continue
            title_map.setdefault(k, []).append(p)

    matched: dict[int, list[Path]] = {}
    unmatched: list[TocItem] = []

    for i, item in enumerate(toc):
        # Prefer match without section number, fallback to full title
        keys = [norm_key(item.title_wo_number), norm_key(item.title)]
        cands: list[Path] = []
        for k in keys:
            cands = title_map.get(k, [])
            if cands:
                break

        if not cands:
            unmatched.append(item)
            continue

        # Disambiguate by major section directory when possible
        major = item.number_prefix.split(".", 1)[0] if item.number_prefix else ""
        root = section_root_dir(major)
        if root:
            rooted = [p for p in cands if str(p).replace("\\", "/").startswith(root + "/")]
            if rooted:
                cands = rooted

        # If still ambiguous, keep up to 3 shortest paths
        cands = sorted(cands, key=lambda p: (len(str(p)), str(p)))[:3]
        matched[i] = cands

    lines: list[str] = []
    lines.append("#### PDF章节页码映射（基于书签目录）")
    lines.append("")
    lines.append(f"来源：`{pdf.as_posix()}`")
    lines.append("")
    lines.append("- 页码链接指向整页缩略图：`assets/pdf_pages_small/page_XXX.jpg`")
    lines.append("- 章节链接指向仓库内对应 `docs/**/*.md` 文件（自动匹配，少量可能需人工确认）")
    lines.append("")
    lines.append("## 目录 → 页码 → Markdown")
    lines.append("")

    for idx, item in enumerate(toc):
        indent = "  " * max(0, item.level - 1)
        page_link = f"[P{item.page:03d}](../assets/pdf_pages_small/page_{item.page:03d}.jpg)"
        md_links = ""
        if idx in matched:
            rels = []
            for p in matched[idx]:
                rel = p.as_posix().removeprefix("docs/")
                rels.append(f"[`docs/{rel}`]({rel})")
            md_links = " → " + ", ".join(rels)
        else:
            md_links = " → （未匹配）"
        lines.append(f"{indent}- **{item.title}**（{page_link}）{md_links}")

    if unmatched:
        lines.append("")
        lines.append("## 未匹配清单（需要人工确认）")
        lines.append("")
        for item in unmatched:
            page_link = f"[P{item.page:03d}](../assets/pdf_pages_small/page_{item.page:03d}.jpg)"
            lines.append(f"- **{item.title}**（{page_link}）")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", out)
    print("toc_items", len(toc))
    print("md_files", len(md_files))
    print("unmatched", len(unmatched))


if __name__ == "__main__":
    main()

