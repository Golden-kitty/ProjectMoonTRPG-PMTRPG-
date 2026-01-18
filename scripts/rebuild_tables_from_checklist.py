import argparse
import re
from pathlib import Path

import sys

# Allow running as a script from repo root without turning `scripts/` into a package.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rebuild_html_tables_to_pipe import TABLE_BLOCK_RE, rebuild_file  # noqa: E402


# Match checklist item like: - [ ] `docs/xxx.md`
TODO_LINE_RE = re.compile(r"^- \[ \] `([^`]+)`\s*$")


def parse_todos(checklist_text: str) -> list[str]:
    paths: list[str] = []
    for line in checklist_text.splitlines():
        m = TODO_LINE_RE.match(line)
        if m:
            paths.append(m.group(1))
    return paths


def mark_done(checklist_text: str, rel_path: str, note: str) -> str:
    # Mark checkbox
    checklist_text = checklist_text.replace(f"- [ ] `{rel_path}`", f"- [x] `{rel_path}`", 1)

    # Append note under "### 已完成"
    parts = checklist_text.splitlines()
    out = []
    inserted = False
    for i, line in enumerate(parts):
        out.append(line)
        if not inserted and line.strip() == "### 已完成":
            # keep following blank lines; append at end of file instead to avoid reordering
            inserted = True
    if not inserted:
        out.append("")
        out.append("### 已完成")
        out.append("")

    # Ensure there's a blank line before note
    if out and out[-1].strip() != "":
        out.append("")
    out.append(f"- `{rel_path}`：{note}")
    out.append("")
    return "\n".join(out).replace("\r\n", "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--checklist",
        default="docs/表格重建清单.md",
        help="Checklist markdown path",
    )
    args = ap.parse_args()

    checklist_path = Path(args.checklist)
    checklist_text = checklist_path.read_text("utf-8")
    todos = parse_todos(checklist_text)

    if not todos:
        print("no_pending")
        return

    for rel in todos:
        md_path = Path(rel)
        if not md_path.exists():
            raise SystemExit(f"missing: {rel}")

        src = md_path.read_text("utf-8")
        table_count = len(TABLE_BLOCK_RE.findall(src))
        if table_count == 0:
            # Already cleaned: just mark done
            checklist_text = mark_done(checklist_text, rel, "已无 `<table>`（无需重建）")
            continue

        rebuild_file(str(md_path))
        new = md_path.read_text("utf-8")
        if "<table" in new.lower():
            raise SystemExit(f"still_has_table: {rel}")

        checklist_text = mark_done(checklist_text, rel, f"重建 {table_count} 个 HTML table 为 GitHub 管道表（rowspan/colspan 已展开）")

    checklist_path.write_text(checklist_text, encoding="utf-8", newline="\n")
    print("done")


if __name__ == "__main__":
    main()

