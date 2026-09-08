"""Attach canonical class names and frozen stable IDs to existing HTML tables.

The inventory supplies the IDs for the 343 pre-conversion HTML tables.  Newly
converted pipe tables already carry their frozen IDs and are left untouched.
The default mode is read-only; ``--apply`` is required to rewrite source files.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generate_table_inventory import mask_markdown_code


TABLE_OPEN_RE = re.compile(r"<table\b[^>]*>", re.IGNORECASE)
CLASS_RE = re.compile(r"\bclass\s*=\s*([\"'])(.*?)\1", re.IGNORECASE | re.DOTALL)
TABLE_ID_RE = re.compile(r"\bdata-table-id\s*=", re.IGNORECASE)


@dataclass
class Annotation:
    table_id: str
    path: str
    line: int

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.table_id, "path": self.path, "line": self.line}


def annotate_open_tag(tag: str, table_id: str) -> str:
    if TABLE_ID_RE.search(tag):
        raise ValueError("refusing to replace an existing data-table-id")
    class_match = CLASS_RE.search(tag)
    if class_match:
        classes = class_match.group(2).split()
        if "pmtrpg-table" not in classes:
            classes.append("pmtrpg-table")
        replacement = f'class={class_match.group(1)}{" ".join(classes)}{class_match.group(1)}'
        tag = tag[: class_match.start()] + replacement + tag[class_match.end() :]
    else:
        tag = tag[:-1].rstrip() + ' class="pmtrpg-table">'
    return tag[:-1].rstrip() + f' data-table-id="{table_id}">'


def execute(
    repo_root: Path,
    inventory: dict[str, Any],
    *,
    apply: bool,
    selected_paths: set[str] | None = None,
) -> list[Annotation]:
    selected_paths = selected_paths or set()
    baseline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in inventory["tables"]:
        if item["scope"] != "source-content" or item["representation"] != "html":
            continue
        if selected_paths and item["path"] not in selected_paths:
            continue
        baseline[item["path"]].append(item)

    annotations: list[Annotation] = []
    rewrites: dict[Path, str] = {}
    for relative, items in sorted(baseline.items()):
        path = repo_root / relative
        source = path.read_text(encoding="utf-8")
        masked = mask_markdown_code(source)
        matches = list(TABLE_OPEN_RE.finditer(masked))
        unannotated = [match for match in matches if not TABLE_ID_RE.search(match.group(0))]
        if len(unannotated) != len(items):
            raise ValueError(
                f"{relative}: found {len(unannotated)} unannotated HTML tables; "
                f"inventory expects {len(items)}"
            )
        replacements: list[tuple[int, int, str, str, int]] = []
        for match, item in zip(unannotated, items, strict=True):
            line = source.count("\n", 0, match.start()) + 1
            replacements.append(
                (
                    match.start(),
                    match.end(),
                    annotate_open_tag(source[match.start() : match.end()], item["id"]),
                    item["id"],
                    line,
                )
            )
        rewritten = source
        for start, end, replacement, table_id, line in reversed(replacements):
            rewritten = rewritten[:start] + replacement + rewritten[end:]
            annotations.append(Annotation(table_id, relative, line))
        rewrites[path] = rewritten

    if apply:
        for path, rewritten in rewrites.items():
            path.write_text(rewritten, encoding="utf-8", newline="\n")
    return sorted(annotations, key=lambda item: (item.path, item.line))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("docs/engineering/table-inventory.json"),
    )
    parser.add_argument("--path", action="append", default=[], help="Annotate only this repo-relative path")
    parser.add_argument("--apply", action="store_true", help="Write changes; omission is a dry run")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    inventory_path = args.inventory.resolve()
    repo_root = inventory_path.parents[2]
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    annotations = execute(
        repo_root,
        inventory,
        apply=args.apply,
        selected_paths=set(args.path),
    )
    payload = {
        "mode": "apply" if args.apply else "dry-run",
        "status": "PASS",
        "annotated_tables": len(annotations),
        "annotated_documents": len({item.path for item in annotations}),
        "tables": [item.as_dict() for item in annotations],
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({key: payload[key] for key in ("mode", "status", "annotated_tables", "annotated_documents")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
