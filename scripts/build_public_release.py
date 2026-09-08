"""Build a source-pinned public book using the existing site navigation order.

This consumes canonical source without writing it. Pure navigation stubs are
filtered by the accepted export policy; coverage of every source table is
mandatory. Existing release directories are never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import yaml

import export_sample_docs as exporter


def navigation_paths(node) -> list[str]:
    if isinstance(node, dict):
        return [path for value in node.values() for path in navigation_paths(value)]
    if isinstance(node, list):
        return [path for value in node for path in navigation_paths(value)]
    return [node] if isinstance(node, str) and node.endswith(".md") else []


def release_sections(root: Path) -> tuple[list[tuple[str, str]], list[str], dict]:
    config = yaml.safe_load((root / "mkdocs.yml").read_text(encoding="utf-8"))
    nav = list(dict.fromkeys(navigation_paths(config["nav"])))
    filtered = exporter.parse_stub_policy(root / "docs/acceptance/export-stub-page-policy.md")
    paths = [path for path in nav if path not in filtered]
    counts = Counter(Path(path).stem for path in paths)
    sections = [(path, Path(path).stem if counts[Path(path).stem] == 1 else path.removesuffix(".md")) for path in paths]
    inventory = json.loads((root / "docs/engineering/table-inventory.json").read_text(encoding="utf-8"))
    source_tables = [item for item in inventory["tables"] if item["scope"] == "source-content"]
    missing = sorted({item["path"].removeprefix("docs/") for item in source_tables} - set(paths))
    if missing:
        raise ValueError(f"Public release omits source tables: {missing}")
    if any(not (root / "docs" / path).is_file() for path in paths):
        raise ValueError("A selected source document is missing")
    return sections, [path for path in nav if path in filtered], {
        "source_table_count": len(source_tables),
        "source_table_ids": [item["id"] for item in source_tables],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-name", required=True)
    parser.add_argument("--title", default="PMTRPG 规则书 - HTML 统一版审阅稿")
    parser.add_argument("--compile-chm", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,90}", args.batch_name):
        raise SystemExit("Unsafe batch name")
    root = exporter.REPO_ROOT
    output = exporter.OUTPUT_DIR / args.batch_name
    if output.exists():
        raise SystemExit(f"Refusing to overwrite release: {output}")
    sections, excluded, coverage = release_sections(root)
    output.mkdir(parents=True)
    documents = [
        {"path": f"docs/{path}", "label": label, "sha256": hashlib.sha256((root / "docs" / path).read_bytes()).hexdigest()}
        for path, label in sections
    ]
    manifest = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "title": args.title,
        "batch_name": args.batch_name,
        "source_base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "source_commit": None,
        "source_state": "working-tree-candidate; pin source_commit after checking all hashes",
        "document_count": len(documents),
        "documents": documents,
        "excluded_navigation_stubs": excluded,
        **coverage,
    }
    (output / "release-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "source-files.txt").write_text("\n".join(path for path, _label in sections) + "\n", encoding="utf-8")
    (output / "pdf").mkdir()
    print(f"Building {len(sections)} documents / {coverage['source_table_count']} tables", flush=True)
    pdf = exporter.export_pdf(output / "pdf", sections, args.title, args.batch_name)
    print(f"pdf {pdf}", flush=True)
    docx = exporter.export_docx(output / "docx", sections, args.title, args.batch_name)
    print(f"docx {docx}", flush=True)
    project = exporter.export_chm(output, sections, args.title, args.batch_name, args.compile_chm)
    print(f"chm {project.with_suffix('.chm')}", flush=True)
    if args.compile_chm and not project.with_suffix(".chm").is_file():
        raise SystemExit("CHM compiler did not produce a binary")
    exporter.write_verification_record(output, args.batch_name, sections, [pdf, docx, project.with_suffix(".chm")])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
