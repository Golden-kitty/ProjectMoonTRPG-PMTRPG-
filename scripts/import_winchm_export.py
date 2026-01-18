import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path


IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


def find_pandoc(repo_root: Path) -> str:
    cand = repo_root / "tools" / "Pandoc" / "pandoc.exe"
    if cand.exists():
        return str(cand)
    return "pandoc"


def detect_encoding(html_bytes: bytes) -> str:
    # Try meta charset=...
    m = re.search(br"charset\s*=\s*([A-Za-z0-9_\-]+)", html_bytes[:4096], flags=re.I)
    if m:
        enc = m.group(1).decode("ascii", errors="ignore").lower()
        # Word/WinCHM exports often label as gb2312 but include GBK characters.
        if enc in {"gb2312", "gb_2312-80"}:
            return "gbk"
        return enc
    return "utf-8"


STYLE_RE = re.compile(r"<style\b[\s\S]*?</style>", flags=re.I)
SCRIPT_RE = re.compile(r"<script\b[\s\S]*?</script>", flags=re.I)
SPAN_OPEN_RE = re.compile(r"<span\b[^>]*>", flags=re.I)
SPAN_CLOSE_RE = re.compile(r"</span\s*>", flags=re.I)
VML_RE = re.compile(r"</?(?:v|o|w):[^>]*>", flags=re.I)
COMMENT_RE = re.compile(r"<!--[\s\S]*?-->", flags=re.I)

TAG_STRIP_ATTRS = [
    "div",
    "p",
    "table",
    "thead",
    "tbody",
    "tfoot",
    "tr",
    "td",
    "th",
    "colgroup",
    "col",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
]
TAG_ATTR_RE = re.compile(
    r"<(" + "|".join(TAG_STRIP_ATTRS) + r")\b[^>]*>",
    flags=re.I,
)

IMG_TAG_RE = re.compile(r"<img\b[^>]*>", flags=re.I)
IMG_SRC_ONLY_RE = re.compile(r'src\s*=\s*"([^"]+)"', flags=re.I)
ANCHOR_TAG_RE = re.compile(r"<a\b[^>]*>", flags=re.I)
ANCHOR_HREF_ONLY_RE = re.compile(r'href\s*=\s*"([^"]+)"', flags=re.I)


def strip_heavy_blocks(html: str) -> str:
    html = STYLE_RE.sub("", html)
    html = SCRIPT_RE.sub("", html)
    html = COMMENT_RE.sub("", html)
    return html


def sanitize_word_html(html: str) -> str:
    """
    Make Word-exported HTML more Pandoc-friendly:
    - drop Word/VML tags
    - remove span wrappers
    - strip attributes from common structural tags
    - shrink <img> to only src
    - shrink <a> to only href
    """
    html = VML_RE.sub("", html)
    html = SPAN_OPEN_RE.sub("", html)
    html = SPAN_CLOSE_RE.sub("", html)

    # Strip attributes from structural tags
    html = TAG_ATTR_RE.sub(lambda m: f"<{m.group(1)}>", html)

    # Normalize img tags to keep only src
    def img_repl(m: re.Match) -> str:
        tag = m.group(0)
        mm = IMG_SRC_ONLY_RE.search(tag)
        if not mm:
            return "<img>"
        return f"<img src=\"{mm.group(1)}\">"

    html = IMG_TAG_RE.sub(img_repl, html)

    # Normalize anchor tags to keep only href
    def a_repl(m: re.Match) -> str:
        tag = m.group(0)
        mm = ANCHOR_HREF_ONLY_RE.search(tag)
        if not mm:
            return "<a>"
        return f"<a href=\"{mm.group(1)}\">"

    html = ANCHOR_TAG_RE.sub(a_repl, html)
    return html


IMG_SRC_RE = re.compile(r'(<img\b[^>]*?\bsrc\s*=\s*")([^"]+)(")', flags=re.I)


def is_probably_nav_asset(src: str) -> bool:
    s = src.replace("\\", "/").lower()
    return s.startswith("template/") or s.startswith("template2/") or "/template/" in s or "/template2/" in s


def rewrite_and_collect_images(
    html: str,
    src_html_path: Path,
    out_md_path: Path,
    assets_root: Path,
    src_root: Path,
) -> tuple[str, list[tuple[Path, Path]]]:
    """
    Rewrite <img src="..."> to point to assets_root, and return list of copy operations (src_file -> dst_file).
    """
    copy_ops: list[tuple[Path, Path]] = []

    def repl(m: re.Match) -> str:
        prefix, src, suffix = m.group(1), m.group(2), m.group(3)
        if is_probably_nav_asset(src):
            # keep as-is (or drop later); but don't copy
            return prefix + src + suffix

        src_norm = src.replace("\\", "/")
        # Ignore external URLs/data URIs
        if re.match(r"^(https?:)?//", src_norm, flags=re.I) or src_norm.startswith("data:"):
            return prefix + src + suffix

        src_file = (src_html_path.parent / src_norm).resolve()
        if not src_file.exists():
            # Leave as-is; we'll handle missing manually later
            return prefix + src + suffix

        if src_file.suffix.lower() not in IMG_EXTS:
            return prefix + src + suffix

        # Keep the original relative structure under assets/chm/
        rel_under_src_root = src_html_path.parent.relative_to(src_root)
        dst_file = (assets_root / "chm" / rel_under_src_root / src_norm).resolve()
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        copy_ops.append((src_file, dst_file))

        rel_link = os.path.relpath(dst_file, out_md_path.parent).replace("\\", "/")
        return prefix + rel_link + suffix

    return IMG_SRC_RE.sub(repl, html), copy_ops


def pandoc_html_to_md(pandoc: str, html_utf8: str) -> str:
    p = subprocess.run(
        [pandoc, "-f", "html", "-t", "gfm", "--wrap=none"],
        input=html_utf8.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode("utf-8", errors="replace"))
    return p.stdout.decode("utf-8", errors="replace")


def normalize_md(md: str) -> str:
    md = md.replace("\r\n", "\n")
    # Remove leading blank lines
    md = md.lstrip("\n")
    # Collapse excessive blank lines
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    return md


DIV_ONLY_LINE_RE = re.compile(r"^\s*</?div>\s*$", flags=re.I)
COLGROUP_BLOCK_RE = re.compile(r"<colgroup\b[\s\S]*?</colgroup\s*>", flags=re.I)
COL_TAG_RE = re.compile(r"<col\b[^>]*>", flags=re.I)
TABLE_TAG_RE = re.compile(r"<table\b[^>]*>", flags=re.I)
P_OPEN_RE = re.compile(r"<p\b[^>]*>", flags=re.I)
P_CLOSE_RE = re.compile(r"</p\s*>", flags=re.I)
IMG_HTML_RE = re.compile(r"<img\b[^>]*\bsrc\s*=\s*\"([^\"]+)\"[^>]*>", flags=re.I)


def postprocess_for_github(md: str) -> str:
    """
    GitHub-flavored Markdown friendly cleanup:
    - drop standalone <div> wrappers
    - drop colgroup/col (GitHub ignores most styling anyway)
    - simplify <table ...> to <table>
    - convert <img ...> to Markdown image syntax for readability
    - remove <p> wrappers inside HTML tables (optional but improves readability)
    """
    md = md.replace("\r\n", "\n")

    # Remove line-only div tags
    lines = []
    for line in md.split("\n"):
        if DIV_ONLY_LINE_RE.match(line):
            continue
        lines.append(line)
    md = "\n".join(lines)

    md = COLGROUP_BLOCK_RE.sub("", md)
    md = COL_TAG_RE.sub("", md)
    md = TABLE_TAG_RE.sub("<table>", md)

    # Convert img tags to markdown images
    md = IMG_HTML_RE.sub(lambda m: f"![]({m.group(1)})", md)

    # Remove p wrappers (common in pandoc's HTML table output)
    md = P_OPEN_RE.sub("", md)
    md = P_CLOSE_RE.sub("", md)

    # Normalize whitespace again
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    md = md.strip() + "\n"
    return md


def should_skip_html(rel_path: Path) -> bool:
    parts = [p.lower() for p in rel_path.parts]
    if not parts:
        return True
    if parts[0] in {"template", "template2"}:
        return True
    if rel_path.name.lower() == "header.htm" and rel_path.parent.name.lower().endswith(".files"):
        return True
    # Skip internal WinCHM files
    if rel_path.name.lower().endswith((".hhc", ".hhk", ".wcp")):
        return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="WinCHM export root directory (HTML Tree)")
    ap.add_argument("--out-docs", default="docs", help="Output docs root (default: docs)")
    ap.add_argument("--assets", default="assets", help="Assets root (default: assets)")
    ap.add_argument("--clean", action="store_true", help="Delete output docs directory before generating")
    ap.add_argument(
        "--target",
        default="github",
        choices=["github", "raw"],
        help="Postprocess output for target renderer (default: github)",
    )
    args = ap.parse_args()

    repo_root = Path.cwd()
    src = Path(args.src).resolve()
    out_docs = (repo_root / args.out_docs).resolve()
    assets_root = (repo_root / args.assets).resolve()

    if args.clean and out_docs.exists():
        shutil.rmtree(out_docs)
    out_docs.mkdir(parents=True, exist_ok=True)
    assets_root.mkdir(parents=True, exist_ok=True)

    pandoc = find_pandoc(repo_root)

    html_files = sorted([p for p in src.rglob("*.htm")])
    if not html_files:
        raise SystemExit(f"No .htm files found under: {src}")

    copied = 0
    converted = 0

    for html_path in html_files:
        rel = html_path.relative_to(src)
        if should_skip_html(rel):
            continue

        out_md = out_docs / rel.with_suffix(".md")
        out_md.parent.mkdir(parents=True, exist_ok=True)

        data = html_path.read_bytes()
        enc = detect_encoding(data)
        try:
            html_text = data.decode(enc, errors="replace")
        except LookupError:
            html_text = data.decode("utf-8", errors="replace")

        html_text = strip_heavy_blocks(html_text)
        html_text = sanitize_word_html(html_text)
        html_text, copy_ops = rewrite_and_collect_images(html_text, html_path, out_md, assets_root, src)

        md = pandoc_html_to_md(pandoc, html_text)
        md = normalize_md(md)
        if args.target == "github":
            md = postprocess_for_github(md)
        out_md.write_text(md, encoding="utf-8")
        converted += 1

        for s, d in copy_ops:
            if not d.exists():
                shutil.copy2(s, d)
                copied += 1

    print(f"Converted: {converted} .htm -> .md")
    print(f"Copied images: {copied}")
    print(f"Docs output: {out_docs}")
    print(f"Assets output: {assets_root}")


if __name__ == "__main__":
    main()

