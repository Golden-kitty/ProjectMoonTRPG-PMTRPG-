from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


HEADING_RE = re.compile(r"^\s*(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class DocInfo:
    path: Path
    title: str
    title_level: int
    body_nonempty_lines: int
    body_chars: int

    @property
    def is_title_only(self) -> bool:
        return self.body_nonempty_lines == 0


def norm_key(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).strip().lower()
    # Drop common markdown emphasis/code markers and simple HTML tags
    s = re.sub(r"</?[^>]+?>", "", s)
    s = s.replace("*", "").replace("_", "").replace("~", "").replace("`", "")
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[\s·•・、，,。．.：:；;！!？?\(\)（）\[\]【】《》“”\"'‘’`]+", "", s)
    return s


def parse_doc(md_path: Path) -> DocInfo | None:
    try:
        text = md_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = md_path.read_text(encoding="utf-8", errors="replace")

    lines = text.splitlines()
    # Only treat the file's title as "the first heading" if it is the first non-empty line.
    first_nonempty_idx = None
    for i, line in enumerate(lines[:120]):
        if line.strip():
            first_nonempty_idx = i
            break

    title = ""
    lvl = 0
    title_idx = None
    if first_nonempty_idx is not None:
        m = HEADING_RE.match(lines[first_nonempty_idx])
        if m:
            title = m.group(2).strip()
            # strip simple markdown emphasis noise
            title = title.strip("*_`~ ").strip()
            lvl = len(m.group(1))
            title_idx = first_nonempty_idx

    if not title:
        # no top heading; skip for title-based grouping to avoid false positives
        return None

    body_lines = lines[title_idx + 1 :] if title_idx is not None else []
    # remove whitespace-only lines; also ignore common pure separators
    nonempty = []
    for ln in body_lines:
        s = ln.strip()
        if not s:
            continue
        if s in {"---", "***", "___"}:
            continue
        nonempty.append(ln)

    body_text = "\n".join(nonempty).strip()
    return DocInfo(
        path=md_path,
        title=title,
        title_level=lvl,
        body_nonempty_lines=len(nonempty),
        body_chars=len(body_text),
    )


def main() -> None:
    docs = Path("docs")
    infos: list[DocInfo] = []
    for p in docs.rglob("*.md"):
        if p.name in {"PDF图片索引.md", "PDF章节页码映射.md"}:
            continue
        info = parse_doc(p)
        if info:
            infos.append(info)

    title_groups: dict[str, list[DocInfo]] = {}
    for info in infos:
        k = norm_key(info.title)
        if not k:
            continue
        title_groups.setdefault(k, []).append(info)

    # candidates: same title appears in 2+ files, and at least one title-only + one non-title-only
    title_candidates: list[tuple[str, list[DocInfo], list[DocInfo]]] = []
    for k, items in title_groups.items():
        if len(items) < 2:
            continue
        title_only = [x for x in items if x.is_title_only]
        non_empty = [x for x in items if not x.is_title_only]
        if title_only and non_empty:
            title_candidates.append((k, title_only, non_empty))

    # sort for stable output
    title_candidates.sort(key=lambda t: (t[0], min(str(x.path) for x in t[1])))

    # stem-based candidates: same filename (stem) appears in 2+ files
    stem_groups: dict[str, list[DocInfo]] = {}
    for info in infos:
        stem_k = norm_key(info.path.stem)
        if not stem_k:
            continue
        stem_groups.setdefault(stem_k, []).append(info)

    stem_candidates: list[tuple[str, list[DocInfo], list[DocInfo]]] = []
    for k, items in stem_groups.items():
        if len(items) < 2:
            continue
        title_only = [x for x in items if x.is_title_only]
        non_empty = [x for x in items if not x.is_title_only]
        if title_only and non_empty:
            stem_candidates.append((k, title_only, non_empty))
    stem_candidates.sort(key=lambda t: (t[0], min(str(x.path) for x in t[1])))

    out_lines: list[str] = []
    out_lines.append("TITLE_ONLY_DUPLICATES_REPORT")
    out_lines.append("")
    out_lines.append("A) 标题同名候选：同标题分组中，若存在“仅标题无正文”的文件，且同组有正文文件，则这些仅标题文件为候选删除项。")
    out_lines.append("")
    out_lines.append(f"候选组数：{len(title_candidates)}")
    out_lines.append("")

    for _, title_only, non_empty in title_candidates:
        title = title_only[0].title
        out_lines.append(f"== {title} ==")
        out_lines.append("title_only:")
        for x in sorted(title_only, key=lambda i: i.path.as_posix()):
            out_lines.append(f"- {x.path.as_posix()}")
        out_lines.append("has_content:")
        for x in sorted(non_empty, key=lambda i: (-(i.body_chars), i.path.as_posix()))[:10]:
            out_lines.append(f"- {x.path.as_posix()}  (body_lines={x.body_nonempty_lines}, body_chars={x.body_chars})")
        out_lines.append("")

    out_lines.append("")
    out_lines.append("B) 文件同名候选：同文件名（stem）分组中，若存在“仅标题无正文”的文件，且同组有正文文件，则这些仅标题文件为候选删除项。")
    out_lines.append("")
    out_lines.append(f"候选组数：{len(stem_candidates)}")
    out_lines.append("")

    for _, title_only, non_empty in stem_candidates:
        stem = title_only[0].path.stem
        out_lines.append(f"== {stem} ==")
        out_lines.append("title_only:")
        for x in sorted(title_only, key=lambda i: i.path.as_posix()):
            out_lines.append(f"- {x.path.as_posix()}")
        out_lines.append("has_content:")
        for x in sorted(non_empty, key=lambda i: (-(i.body_chars), i.path.as_posix()))[:10]:
            out_lines.append(f"- {x.path.as_posix()}  (body_lines={x.body_nonempty_lines}, body_chars={x.body_chars})")
        out_lines.append("")

    Path("output_title_only_dupes.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print("wrote output_title_only_dupes.txt")


if __name__ == "__main__":
    main()

