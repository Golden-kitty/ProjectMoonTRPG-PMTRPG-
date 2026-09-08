"""Apply grid repairs confirmed against rendered PDF pages 136, 138, 213, 334 and 340."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def replace_exact(text: str, old: str, new: str, count: int, label: str) -> str:
    observed = text.count(old)
    if observed != count:
        raise ValueError(f"{label}: expected {count} matches, found {observed}")
    return text.replace(old, new)


def repair_origins(text: str, count: int, label: str) -> str:
    text = replace_exact(text, 'colspan="7"', 'colspan="8"', count * 3, label)
    text = replace_exact(
        text,
        '<td  rowspan="3" ><b>初始美德</td>',
        '<td colspan="2" rowspan="3"><b>初始美德</td>',
        count,
        label,
    )
    text = replace_exact(
        text,
        '<td><b>额外光之种</td>',
        '<td colspan="2"><b>额外光之种</td>',
        count,
        label,
    )
    pattern = re.compile(
        r'(<td colspan="2">[^<]*</td>\s*<td colspan="2">[^<]*</td>\s*)'
        r'<td><b>([^<]+)</td>'
    )
    text, changed = pattern.subn(r'\1<td colspan="2"><b>\2</td>', text)
    if changed != count:
        raise ValueError(f"{label}: expected {count} light-value rows, found {changed}")
    return text


def repair_table(text: str, table_id: str, *, placeholder_row: bool) -> str:
    pattern = re.compile(
        rf'(<table\b[^>]*data-table-id="{re.escape(table_id)}"[^>]*>)(.*?)(</table>)',
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(text)
    if match is None:
        raise ValueError(f"missing table {table_id}")
    body = match.group(2)
    body = replace_exact(body, 'colspan="1">具现化等级', 'colspan="2">具现化等级', 1, table_id)
    body = replace_exact(body, 'colspan="4">类型', 'colspan="3">类型', 1, table_id)
    body = replace_exact(body, 'colspan="2">具现化特性', '>具现化特性', 1, table_id)
    if placeholder_row:
        old = '<td>(占位)</td><td></td><td></td><td></td><td></td><td colspan="2"></td>'
        new = '<td>(占位)</td><td></td><td></td><td></td><td></td><td></td>'
        body = replace_exact(body, old, new, 1, table_id)
    return text[: match.start()] + match.group(1) + body + match.group(3) + text[match.end() :]


def repair_races(text: str, table_ids: list[str]) -> str:
    for table_id in table_ids:
        pattern = re.compile(
            rf'(<table\b[^>]*data-table-id="{re.escape(table_id)}"[^>]*>)(.*?)(</table>)',
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(text)
        if match is None:
            raise ValueError(f"missing table {table_id}")
        body = replace_exact(
            match.group(2),
            '</td>\n  </tr>\n  <tr>\n    <td><b>恢复骰',
            '</td>\n    <td><b>恢复骰',
            1,
            table_id,
        )
        text = text[: match.start()] + match.group(1) + body + match.group(3) + text[match.end() :]
    return text


def repair_skill_icon_alts(text: str) -> str:
    icons = {
        "image002.jpg": ("黑桃", 5),
        "image004.jpg": ("红心", 4),
        "image006.jpg": ("方块", 2),
        "image008.jpg": ("梅花", 12),
    }
    for filename, (alt, count) in icons.items():
        pattern = re.compile(rf'<img src="([^"]*{re.escape(filename)})"/>')
        text, changed = pattern.subn(rf'<img src="\1" alt="{alt}"/>', text)
        if changed != count:
            raise ValueError(f"{filename}: expected {count} images, found {changed}")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    repairs = {
        "docs/资源目录/出身/基础出身.md": lambda value: repair_origins(value, 4, "基础出身"),
        "docs/资源目录/出身/传统武人.md": lambda value: repair_origins(value, 2, "传统武人"),
        "docs/创作指南/具现化特性设计.md": lambda value: repair_table(value, "html-aa8f8353d441", placeholder_row=False),
        "docs/创作指南/资源设计表格.md": lambda value: repair_table(value, "html-659f22fceac2", placeholder_row=True),
        "docs/资源目录/种族/基本种族.md": lambda value: repair_races(
            value,
            ["html-3c0bd5ac4021", "html-f8d6557f23d4", "html-ccb1ef7e905d"],
        ),
        "docs/核心规则/速查图表/技能列表.md": repair_skill_icon_alts,
    }
    changed: list[str] = []
    results: dict[Path, str] = {}
    for relative, transform in repairs.items():
        path = repo / relative
        source = path.read_text(encoding="utf-8")
        updated = transform(source)
        if updated != source:
            changed.append(relative)
            results[path] = updated
    if args.apply:
        for path, updated in results.items():
            path.write_text(updated, encoding="utf-8", newline="\n")
    payload = {
        "mode": "apply" if args.apply else "dry-run",
        "status": "PASS",
        "changed_documents": changed,
        "pdf_pages": [119, 136, 138, 213, 334, 340],
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
