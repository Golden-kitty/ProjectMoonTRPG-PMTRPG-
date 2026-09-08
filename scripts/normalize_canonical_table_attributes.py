"""Remove legacy presentation attributes from inventoried canonical tables.

Each eligible opening tag is reduced to the canonical class and its existing
stable ID.  Cell content, row/cell tags, spans, images and text are untouched.
The default mode is a read-only dry run; ``--apply`` is required to write.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from generate_table_inventory import mask_markdown_code


TABLE_OPEN_RE = re.compile(r"<table\b[^>]*>", re.IGNORECASE)
TABLE_ID_RE = re.compile(r"\bdata-table-id\s*=\s*([\"'])(?P<id>.*?)\1", re.IGNORECASE)


def canonical_open_tag(tag: str) -> str:
    match = TABLE_ID_RE.search(tag)
    if match is None:
        raise ValueError("table is missing the stable data-table-id")
    table_id = match.group("id")
    return f'<table class="pmtrpg-table" data-table-id="{table_id}">'


def execute(repo_root: Path, inventory: dict[str, Any], *, apply: bool) -> list[dict[str, Any]]:
    source_paths = sorted(
        {
            item["path"]
            for item in inventory["tables"]
            if item["scope"] == "source-content" and item["representation"] == "html"
        }
    )
    changes: list[dict[str, Any]] = []
    rewrites: dict[Path, str] = {}
    for relative in source_paths:
        path = repo_root / relative
        source = path.read_text(encoding="utf-8")
        masked = mask_markdown_code(source)
        replacements: list[tuple[int, int, str]] = []
        for match in TABLE_OPEN_RE.finditer(masked):
            original = source[match.start() : match.end()]
            replacement = canonical_open_tag(original)
            if original == replacement:
                continue
            replacements.append((match.start(), match.end(), replacement))
            changes.append(
                {
                    "path": relative,
                    "line": source.count("\n", 0, match.start()) + 1,
                    "id": TABLE_ID_RE.search(original).group("id"),  # type: ignore[union-attr]
                    "before": original,
                    "after": replacement,
                }
            )
        rewritten = source
        for start, end, replacement in reversed(replacements):
            rewritten = rewritten[:start] + replacement + rewritten[end:]
        rewrites[path] = rewritten
    if apply:
        for path, rewritten in rewrites.items():
            path.write_text(rewritten, encoding="utf-8", newline="\n")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("docs/engineering/table-inventory.json"),
    )
    parser.add_argument("--apply", action="store_true", help="Write changes; omission is a dry run")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    inventory_path = args.inventory.resolve()
    repo_root = inventory_path.parents[2]
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    changes = execute(repo_root, inventory, apply=args.apply)
    payload = {
        "mode": "apply" if args.apply else "dry-run",
        "status": "PASS",
        "normalized_tables": len(changes),
        "normalized_documents": len({item["path"] for item in changes}),
        "tables": changes,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                key: payload[key]
                for key in ("mode", "status", "normalized_tables", "normalized_documents")
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
