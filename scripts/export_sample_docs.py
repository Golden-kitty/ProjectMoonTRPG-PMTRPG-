from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
from pathlib import Path

import markdown
from bs4 import BeautifulSoup


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
OUTPUT_DIR = REPO_ROOT / "output" / "export_samples"

DEFAULT_SAMPLES: list[tuple[str, str]] = [
    ("核心规则/基本规则/等级.md", "等级"),
    ("核心规则/速查图表/技能列表.md", "技能列表"),
    ("核心规则/战斗/战斗流程.md", "战斗流程"),
    ("资源目录/装备/武器/奇门.md", "奇门"),
]


def md_to_html_body(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    md = markdown.Markdown(
        extensions=["tables", "attr_list", "md_in_html", "sane_lists", "toc"]
    )
    body = md.convert(text)

    def repl(match: re.Match[str]) -> str:
        attr = match.group(1)
        raw = match.group(2)
        if re.match(r"^[a-z]+://", raw, re.I) or raw.startswith("data:") or raw.startswith("#"):
            return match.group(0)
        resolved = (md_path.parent / raw).resolve()
        return f'{attr}="{resolved.as_uri()}"'

    body = re.sub(r'(src|href)="([^"]+)"', repl, body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body


def build_full_html(title: str, sections: list[tuple[str, str]]) -> str:
    toc = "\n".join(
        f'<li><a href="#section-{idx}">{html.escape(label)}</a></li>'
        for idx, (_path, label) in enumerate(sections, start=1)
    )
    section_html = []
    for idx, (rel_path, label) in enumerate(sections, start=1):
        body = md_to_html_body(DOCS_DIR / rel_path)
        section_html.append(
            "\n".join(
                [
                    f'<section id="section-{idx}">',
                    f"<h1>{html.escape(label)}</h1>",
                    f'<p class="source">{html.escape(rel_path)}</p>',
                    body,
                    "</section>",
                ]
            )
        )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '  <meta charset="utf-8">',
            f"  <title>{html.escape(title)}</title>",
            "  <style>",
            "    body { font-family: 'Microsoft YaHei', sans-serif; line-height: 1.6; margin: 24px; }",
            "    h1, h2, h3 { page-break-after: avoid; }",
            "    section { page-break-before: always; }",
            "    section:first-of-type { page-break-before: auto; }",
            "    table { border-collapse: collapse; width: 100%; font-size: 12px; }",
            "    th, td { border: 1px solid #999; padding: 4px 6px; vertical-align: top; }",
            "    img { max-width: 100%; height: auto; }",
            "    .source { color: #666; font-size: 12px; }",
            "  </style>",
            "</head>",
            "<body>",
            f"  <h1>{html.escape(title)}</h1>",
            "  <p>本文件用于 PMTRPG 导出就绪样本验证。</p>",
            "  <h2>目录</h2>",
            f"  <ul>{toc}</ul>",
            *section_html,
            "</body>",
            "</html>",
            "",
        ]
    )


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def parse_stub_policy(policy_path: Path | None) -> set[str]:
    if not policy_path or not policy_path.exists():
        return set()

    filtered: set[str] = set()
    current = ""
    for raw in policy_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("## "):
            current = line[3:].strip().lower()
            continue
        if not line.startswith("- `"):
            continue
        if current not in {"导出过滤", "export filter"}:
            continue
        filtered.add(line.split("`", 2)[1].replace("docs/", ""))
    return filtered


def build_sections(
    files: list[str] | None,
    file_list: Path | None,
    stub_policy: Path | None,
) -> list[tuple[str, str]]:
    rel_paths: list[str]
    if files:
        rel_paths = [path.replace("\\", "/").removeprefix("docs/") for path in files]
    elif file_list:
        rel_paths = []
        for raw in file_list.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            rel_paths.append(line.replace("\\", "/").removeprefix("docs/"))
    else:
        rel_paths = [path for path, _label in DEFAULT_SAMPLES]

    filtered = parse_stub_policy(stub_policy)
    rel_paths = [path for path in rel_paths if path not in filtered]
    return [(path, Path(path).stem) for path in rel_paths]


def batch_paths(batch_name: str) -> tuple[Path, str]:
    if batch_name == "sample-export":
        return OUTPUT_DIR, "PMTRPG Export Samples"
    return OUTPUT_DIR / batch_name, f"PMTRPG Export Batch: {batch_name}"


def write_verification_record(
    out_dir: Path,
    batch_name: str,
    sections: list[tuple[str, str]],
    generated: list[Path],
) -> Path:
    record_path = out_dir / "verification.md"
    lines = [
        f"# {batch_name}",
        "",
        "## Files",
        "",
        *[f"- `{rel_path}`" for rel_path, _label in sections],
        "",
        "## Generated",
        "",
        *[f"- `{path.relative_to(REPO_ROOT).as_posix()}`" for path in generated if path.exists()],
        "",
    ]
    record_path.write_text("\n".join(lines), encoding="utf-8")
    return record_path


def build_html_preview(out_dir: Path, sections: list[tuple[str, str]], title: str, batch_name: str) -> Path:
    html_path = out_dir / f"{batch_name}.html"
    html_path.write_text(build_full_html(title, sections), encoding="utf-8")
    return html_path


def _inline_html(node) -> str:
    node = BeautifulSoup(str(node), "html.parser")
    for img in node.find_all("img"):
        src = img.get("src", "")
        name = Path(src.replace("file:///", "")).name if src else "image"
        img.replace_with(node.new_string(f"[图:{name}]"))
    text = str(node)
    text = re.sub(r"</?(?:p|div|section|tbody|thead|tfoot)>", "", text)
    return text.strip()


def _add_images_from_node(node, flowables, max_width: int = 420) -> None:
    for img in node.find_all("img"):
        src = img.get("src", "")
        if not src.startswith("file:///"):
            continue
        local_path = Path(src.replace("file:///", ""))
        if not local_path.exists():
            continue
        try:
            from reportlab.lib import utils
            from reportlab.platypus import Image, Spacer

            reader = utils.ImageReader(str(local_path))
            width, height = reader.getSize()
            scale = min(1.0, max_width / width) if width else 1.0
            flowables.append(Image(str(local_path), width=width * scale, height=height * scale))
            flowables.append(Spacer(1, 6))
        except Exception:
            continue


def _html_sections_to_pdf_flowables(sections: list[tuple[str, str]]):
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.pdfbase.pdfmetrics import registerFont
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "reportlab is required for PDF export. Install it with "
            "`python -m pip install -r requirements-export.txt`."
        ) from exc

    registerFont(UnicodeCIDFont("STSong-Light"))

    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "PmBase",
        parent=styles["BodyText"],
        fontName="STSong-Light",
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
    )
    h1 = ParagraphStyle("PmH1", parent=base, fontSize=18, leading=22, spaceAfter=10)
    h2 = ParagraphStyle("PmH2", parent=base, fontSize=14, leading=18, spaceAfter=8)
    meta = ParagraphStyle("PmMeta", parent=base, fontSize=8, leading=10, textColor=colors.grey)

    flowables = [Paragraph("PMTRPG Export Samples", h1), Paragraph("本文件用于 PMTRPG 导出就绪样本验证。", base), Spacer(1, 8)]

    for idx, (rel_path, label) in enumerate(sections, start=1):
        if idx > 1:
            flowables.append(PageBreak())
        flowables.append(Paragraph(label, h1))
        flowables.append(Paragraph(rel_path, meta))
        flowables.append(Spacer(1, 8))

        body = md_to_html_body(DOCS_DIR / rel_path)
        soup = BeautifulSoup(f"<root>{body}</root>", "html.parser")
        for node in soup.root.children:
            if not getattr(node, "name", None):
                continue
            tag = node.name.lower()
            if tag in {"h1", "h2", "h3"}:
                flowables.append(Paragraph(_inline_html(node), h2))
                continue
            if tag in {"p", "blockquote"}:
                text = _inline_html(node)
                if text:
                    flowables.append(Paragraph(text, base))
                    flowables.append(Spacer(1, 4))
                _add_images_from_node(node, flowables)
                continue
            if tag in {"ul", "ol"}:
                for li in node.find_all("li", recursive=False):
                    text = _inline_html(li)
                    if text:
                        flowables.append(Paragraph(f"• {text}", base))
                flowables.append(Spacer(1, 4))
                continue
            if tag == "table":
                rows = []
                for tr in node.find_all("tr", recursive=False):
                    cells = tr.find_all(["th", "td"], recursive=False)
                    if not cells:
                        continue
                    rows.append([Paragraph(_inline_html(cell) or " ", base) for cell in cells])
                if rows:
                    col_count = max(len(r) for r in rows)
                    normalized = [r + [Paragraph(" ", base)] * (col_count - len(r)) for r in rows]
                    table = Table(normalized, repeatRows=1)
                    table.setStyle(
                        TableStyle(
                            [
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                                ("TOPPADDING", (0, 0), (-1, -1), 3),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ]
                        )
                    )
                    flowables.append(table)
                    flowables.append(Spacer(1, 8))
                continue

    return flowables


def export_pdf(out_dir: Path, sections: list[tuple[str, str]], title: str, batch_name: str) -> Path:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate

    build_html_preview(out_dir, sections, title, batch_name)
    pdf_path = out_dir / f"{batch_name}.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, title=title)
    doc.build(_html_sections_to_pdf_flowables(sections))
    return pdf_path


def build_chm_name_map(entries: list[tuple[str, str]]) -> dict[str, str]:
    return {
        rel_path: f"sample-{index:02d}.html"
        for index, (rel_path, _label) in enumerate(entries, start=1)
    }


def build_hhc(entries: list[tuple[str, str]], name_map: dict[str, str]) -> str:
    items = []
    for rel_path, label in entries:
        html_name = name_map[rel_path]
        items.extend(
            [
                "<LI> <OBJECT type=\"text/sitemap\">",
                f"    <param name=\"Name\" value=\"{html.escape(label)}\">",
                f"    <param name=\"Local\" value=\"html/{html_name}\">",
                "  </OBJECT>",
            ]
        )
    return "\n".join(
        [
            "<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML//EN\">",
            "<HTML>",
            "<BODY>",
            "<UL>",
            *items,
            "</UL>",
            "</BODY>",
            "</HTML>",
            "",
        ]
    )


def export_chm(out_dir: Path, sections: list[tuple[str, str]], title: str, batch_name: str, compile_chm: bool) -> Path:
    chm_dir = out_dir / "chm"
    html_dir = chm_dir / "html"
    ensure_clean_dir(chm_dir)
    html_dir.mkdir(parents=True, exist_ok=True)

    name_map = build_chm_name_map(sections)
    html_files: list[str] = []
    for rel_path, label in sections:
        html_name = name_map[rel_path]
        html_files.append(f"html/{html_name}")
        page_html = build_full_html(f"{label} - PMTRPG Export Sample", [(rel_path, label)])
        (html_dir / html_name).write_text(page_html, encoding="utf-8")

    hhc_path = chm_dir / f"{batch_name}.hhc"
    hhc_path.write_text(build_hhc(sections, name_map), encoding="utf-8")

    hhp_path = chm_dir / f"{batch_name}.hhp"
    hhp_path.write_text(
        "\n".join(
            [
                "[OPTIONS]",
                "Compatibility=1.1 or later",
                f"Compiled file={batch_name}.chm",
                f"Contents file={batch_name}.hhc",
                f"Default topic=html/{name_map[sections[0][0]]}",
                "Display compile progress=No",
                "Full-text search=Yes",
                "Language=0x804 Chinese (Simplified, PRC)",
                f"Title={title}",
                "",
                "[FILES]",
                *html_files,
                "",
            ]
        ),
        encoding="utf-8",
    )

    hhc_exe = shutil.which("hhc")
    if compile_chm and hhc_exe:
        subprocess.run([hhc_exe, str(hhp_path)], cwd=chm_dir, check=False)
    return hhp_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=["pdf", "chm", "all"], default="all")
    parser.add_argument("--compile-chm", action="store_true")
    parser.add_argument("--batch-name", default="sample-export")
    parser.add_argument("--files", nargs="*")
    parser.add_argument("--file-list", type=Path)
    parser.add_argument("--stub-policy", type=Path, default=REPO_ROOT / "docs" / "acceptance" / "export-stub-page-policy.md")
    args = parser.parse_args()

    sections = build_sections(args.files, args.file_list, args.stub_policy)
    if not sections:
        raise SystemExit("No exportable files selected.")

    out_dir, title = batch_paths(args.batch_name)
    out_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    if args.format in {"pdf", "all"}:
        pdf_dir = out_dir / "pdf"
        ensure_clean_dir(pdf_dir)
        pdf_path = export_pdf(pdf_dir, sections, title, args.batch_name)
        generated.extend([pdf_path, pdf_dir / f"{args.batch_name}.html"])
        print(f"pdf {pdf_path}")

    if args.format in {"chm", "all"}:
        chm_path = export_chm(out_dir, sections, title, args.batch_name, compile_chm=args.compile_chm)
        generated.extend(
            [
                chm_path,
                chm_path.with_suffix(".hhc"),
                chm_path.with_suffix(".chm"),
            ]
        )
        print(f"chm {chm_path}")
        if args.compile_chm and not shutil.which("hhc"):
            print("chm_compile_skipped missing_hhc")

    record_path = write_verification_record(out_dir, args.batch_name, sections, generated)
    print(f"record {record_path}")


if __name__ == "__main__":
    main()
