"""Read-only Stage 8 source-table gate; never regenerate an accepted baseline.

Run after editing and before publishing::

    python scripts/check_table_integrity.py --base-ref HEAD --report output/table-integrity.json

The inventory supplies the frozen structure, Stage 7 manifests pin complete
source documents (including prose), and review registries retain their existing
hash/evidence checks. With --base-ref, changing those pins cannot silently hide
an edit: every changed pin or source document needs a checked-in JSON review
record under docs/acceptance/table-integrity-changes/. A record has the form::

    {"reason": "...", "reviewer": "...", "evidence": "docs/acceptance/review.md",
     "changes": [{"path": "docs/...", "before_sha256": "...",
                  "after_sha256": "..."}]}

Use null for a missing before/after file. This records review accountability;
it cannot establish human authorization or visual correctness by itself. On the
initial rollout only, when the Git base predates the inventory, bootstrap is
reported explicitly and the new inventory/manifests are still fully checked.
Review records do not bypass malformed tables or stale source hashes.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import markdown
from bs4 import BeautifulSoup

from generate_table_inventory import build_inventory, classify_scope, mask_markdown_code
from generate_table_rollout_batches import (
    classify_review_status, load_acceptances, load_high_risk_reviews, load_review_policy,
)
from validate_canonical_tables import compare_structure, validate_canonical_docs


INVENTORY = "docs/engineering/table-inventory.json"
MANIFEST_DIR = "docs/engineering/table-rollout-batches"
REVIEW_DIR = "docs/acceptance/table-integrity-changes"
REGISTRIES = (
    "docs/engineering/canonical-table-acceptance-registry.json",
    "docs/engineering/canonical-table-review-policy.json",
    "docs/engineering/canonical-table-high-risk-review-registry.json",
)
PROTECTED = (INVENTORY, *REGISTRIES)
CONFLICT_RE = re.compile(r"^(?:<{7,}|>{7,}|\|{7,})(?:\s|$)|^={7,}\s*$", re.MULTILINE)
CLOSED_STATUSES = {
    "accepted_by_user", "source_verified_by_pdf_evidence",
    "source_verified_by_high_risk_review", "closed_by_user_review_policy",
}


def digest(content: bytes | None) -> str | None:
    return hashlib.sha256(content).hexdigest() if content is not None else None


def git_text_digest(content: bytes | None) -> str | None:
    """Compare textual Git content, independent of a CRLF checkout.

    Frozen document/media pins remain raw byte hashes. Review records for Git
    changes use LF-normalized Markdown/JSON bytes, as stored in the index.
    """
    return digest(content.replace(b"\r\n", b"\n")) if content is not None else None


def issue(code: str, path: str, message: str) -> dict[str, Any]:
    return {"code": code, "path": path, "message": message, "severity": "error"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_tables(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in inventory["tables"] if item.get("scope") == "source-content"]


def check_source(repo: Path, baseline: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    excluded = set(baseline.get("excluded_paths", []))
    # Exemptions may only be engineering/evidence documents, never rules.
    errors = [issue("source_excluded", path, "A source document cannot be excluded from the gate")
              for path in excluded if classify_scope(path) == "source-content"]
    current = build_inventory(repo / "docs", repo / "docs/PDF章节页码映射.md", excluded)
    baseline_ids = [table["id"] for table in source_tables(baseline)]
    if len(baseline_ids) != len(set(baseline_ids)):
        errors.append(issue("baseline_duplicate_id", INVENTORY, "Frozen source table IDs must be unique"))
    if len(source_tables(current)) < len(baseline_ids):
        errors.append(issue("table_count_decreased", INVENTORY, "Source table count is below the frozen baseline"))
    errors.extend(item.as_dict() for item in compare_structure(baseline, current))
    errors.extend(item.as_dict() for item in validate_canonical_docs(repo / "docs", repo, excluded))
    tables = source_tables(current)
    if not tables:
        errors.append(issue("empty_inventory", INVENTORY, "No source-content tables found"))
    for table in tables:
        if table["representation"] != "html":
            errors.append(issue("non_html_source_table", table["path"], table["id"]))
        for image in table["images"]:
            src = image.get("src") or ""
            parsed = urlparse(src)
            if parsed.scheme or parsed.netloc or src.startswith(("/", "\\")):
                errors.append(issue("nonlocal_image", table["path"], f"Image must be repository-relative: {src}"))
                continue
            target = (repo / table["path"]).parent / unquote(parsed.path)
            if not target.resolve().is_relative_to(repo) or not target.is_file():
                errors.append(issue("image_missing", table["path"], src))
    return current, errors


def check_manifests(repo: Path, current: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = {item["id"]: item for item in source_tables(current)}
    tables: list[dict[str, Any]] = []
    documents: list[str] = []
    manifests = sorted((repo / MANIFEST_DIR).glob("stage7-batch-*.json"))
    if not manifests:
        return [issue("manifest_missing", MANIFEST_DIR, "Frozen Stage 7 manifests are required")]
    inventory_hash = digest((repo / INVENTORY).read_bytes())
    for path in manifests:
        relative = path.relative_to(repo).as_posix()
        manifest = read_json(path)
        batch_tables = manifest["tables"]
        batch_docs = manifest["documents"]
        if manifest.get("inventory_sha256") != inventory_hash:
            errors.append(issue("inventory_pin_changed", relative, "Manifest inventory SHA256 does not match frozen inventory"))
        if manifest.get("table_count") != len(batch_tables) or manifest.get("document_count") != len(batch_docs):
            errors.append(issue("manifest_count", relative, "Manifest counts do not match its records"))
        snapshot = "".join(f"{doc['path']}\0{doc['sha256']}\n" for doc in batch_docs)
        if manifest.get("source_snapshot_sha256") != digest(snapshot.encode("utf-8")):
            errors.append(issue("manifest_snapshot", relative, "Document snapshot hash does not match"))
        for doc in batch_docs:
            documents.append(doc["path"])
            target = repo / doc["path"]
            if not target.resolve().is_relative_to(repo) or not target.is_file():
                errors.append(issue("source_missing", doc["path"], "Manifest source is missing or outside repository"))
            elif digest(target.read_bytes()) != doc["sha256"]:
                errors.append(issue("source_hash_changed", doc["path"], "Source changed after recorded review; do not auto-refresh its pin"))
            matching = [table for table in batch_tables if table["path"] == doc["path"]]
            if len(matching) != doc["table_count"]:
                errors.append(issue("document_table_count", relative, doc["path"]))
        if {table["path"] for table in batch_tables} != {doc["path"] for doc in batch_docs}:
            errors.append(issue("manifest_document_coverage", relative, "Table/document paths differ"))
        for table in batch_tables:
            tables.append({**table, "scope": "source-content"})
            if table.get("review_status") not in CLOSED_STATUSES:
                errors.append(issue("review_pending", relative, table["id"]))
    for table_id, count in Counter(table["id"] for table in tables).items():
        if count != 1:
            errors.append(issue("manifest_table_duplicate", MANIFEST_DIR, table_id))
    for path, count in Counter(documents).items():
        if count != 1:
            errors.append(issue("manifest_document_duplicate", MANIFEST_DIR, path))
    errors.extend(item.as_dict() for item in compare_structure({"tables": tables}, current))
    loaded: list[Any] = []
    for loader, registry in zip((load_acceptances, load_review_policy, load_high_risk_reviews), REGISTRIES):
        try:
            loaded.append(loader(repo / registry, expected, repo))
        except (ValueError, OSError, KeyError) as exc:
            errors.append(issue("review_registry_invalid", registry, str(exc)))
    if len(loaded) == 3:
        accepted, (policy, verified), reviewed = loaded
        for table in tables:
            if table["id"] not in expected:
                continue
            status, _, review_set = classify_review_status(expected[table["id"]], accepted, verified, reviewed, policy)
            actual_set = table.get("acceptance_set") if status == "accepted_by_user" else table.get("evidence_set")
            if table.get("review_status") != status or actual_set != review_set:
                errors.append(issue("review_status_mismatch", table["path"], f"{table['id']} does not match the independent review registries/policy"))
    return errors


def check_source_images(repo: Path) -> list[dict[str, Any]]:
    """Include prose icons and Markdown images, not just table-local images."""
    errors = []
    for path in sorted((repo / "docs").rglob("*.md")):
        relative = path.relative_to(repo).as_posix()
        if classify_scope(relative) != "source-content":
            continue
        body = markdown.markdown(mask_markdown_code(path.read_text(encoding="utf-8")), extensions=["tables"])
        for image in BeautifulSoup(body, "html.parser").find_all("img"):
            src = str(image.get("src", ""))
            parsed = urlparse(src)
            if parsed.scheme or parsed.netloc or src.startswith(("/", "\\")):
                errors.append(issue("nonlocal_image", relative, f"Image must be repository-relative: {src}"))
                continue
            target = path.parent / unquote(parsed.path)
            if not src or not target.resolve().is_relative_to(repo) or not target.is_file():
                errors.append(issue("image_missing", relative, src))
            if not image.has_attr("alt"):
                errors.append(issue("image_alt", relative, src))
    return errors


def check_conflicts(repo: Path) -> list[dict[str, Any]]:
    errors = []
    for folder in ("docs", "scripts", "tests", ".github"):
        for path in (repo / folder).rglob("*"):
            if path.is_file() and path.suffix in {".md", ".py", ".yml", ".yaml", ".json", ".txt", ".css"}:
                match = CONFLICT_RE.search(path.read_text(encoding="utf-8"))
                if match:
                    errors.append(issue("conflict_marker", path.relative_to(repo).as_posix(), f"Unresolved conflict at character {match.start()}"))
    return errors


def check_implicit_conversion(repo: Path) -> list[dict[str, Any]]:
    errors = []
    forbidden = {"apply_semantic_table_merges", "rebuild_file", "html_table_to_pipe"}
    modules = {"semantic_table_merges", "rebuild_html_tables_to_pipe", "rebuild_tables_from_checklist"}
    for relative in ("scripts/mkdocs_hooks.py", "scripts/export_sample_docs.py", "scripts/build_site.py"):
        path = repo / relative
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        for node in ast.walk(tree):
            imported = (isinstance(node, ast.ImportFrom) and node.module in modules
                        or isinstance(node, ast.Import) and any(alias.name in modules for alias in node.names))
            called = isinstance(node, ast.Call) and (
                isinstance(node.func, ast.Name) and node.func.id in forbidden
                or isinstance(node.func, ast.Attribute) and node.func.attr in forbidden)
            script_argument = isinstance(node, ast.Constant) and isinstance(node.value, str) and any(
                f"{module}.py" in node.value for module in modules)
            if imported or called or script_argument:
                errors.append(issue("implicit_conversion", relative, f"Legacy automatic table converter referenced at line {node.lineno}"))
    for path in (repo / ".github/workflows").glob("*.y*ml"):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.lstrip().startswith("#") and any(f"{module}.py" in line for module in modules):
                errors.append(issue("implicit_conversion", path.relative_to(repo).as_posix(), f"Emergency converter cannot run in publishing/CI workflows (line {number})"))
    return errors


def check_lossy_guards(repo: Path) -> list[dict[str, Any]]:
    """Exercise the actual CLIs in a disposable fixture, never against rules."""
    errors = []
    with tempfile.TemporaryDirectory(prefix="pmtrpg-table-guard-") as raw:
        temporary = Path(raw)
        sample = temporary / "sample.md"
        checklist = temporary / "checklist.md"
        original = '<table><tr><td colspan="2">Preserve</td></tr></table>\n'
        for name, arguments in (
            ("rebuild_html_tables_to_pipe.py", ["--file", str(sample)]),
            ("rebuild_tables_from_checklist.py", ["--checklist", str(checklist)]),
        ):
            sample.write_text(original, encoding="utf-8")
            checklist_text = f"- [ ] `{sample.as_posix()}`\n"
            checklist.write_text(checklist_text, encoding="utf-8")
            result = subprocess.run([sys.executable, str(repo / "scripts" / name), *arguments],
                                    cwd=temporary, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            output = result.stdout + result.stderr
            unchanged = sample.read_text(encoding="utf-8") == original and checklist.read_text(encoding="utf-8") == checklist_text
            if result.returncode == 0 or "refusing lossy" not in output or not unchanged:
                errors.append(issue("lossy_guard_failed", f"scripts/{name}", "Default CLI must explicitly refuse and leave the fixture unchanged"))
    return errors


def git_bytes(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True).stdout


def git_file(repo: Path, revision: str, relative: str) -> bytes | None:
    result = subprocess.run(["git", "show", f"{revision}:{relative}"], cwd=repo, capture_output=True)
    return result.stdout if result.returncode == 0 else None


def check_git_changes(repo: Path, base_ref: str | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not base_ref:
        return {"status": "NOT_RUN", "reason": "Supply --base-ref to detect simultaneous baseline rewrites"}, []
    revision = git_bytes(repo, "rev-parse", "--verify", f"{base_ref}^{{commit}}").decode().strip()
    bootstrap = git_file(repo, revision, INVENTORY) is None
    base_paths = set(git_bytes(repo, "ls-tree", "-r", "--name-only", "-z", revision).decode("utf-8").split("\0"))
    current_paths = {path.relative_to(repo).as_posix() for folder in ("docs",) for path in (repo / folder).rglob("*") if path.is_file()}
    candidates = sorted(path for path in base_paths | current_paths if path and (
        path in PROTECTED or path.startswith(MANIFEST_DIR + "/") and path.endswith(".json")
        or path.startswith("docs/") and path.endswith(".md") and classify_scope(path) == "source-content"))
    reviews: set[tuple[str, str | None, str | None]] = set()
    errors = []
    for record_path in sorted((repo / REVIEW_DIR).glob("*.json")):
        record = read_json(record_path)
        evidence = record.get("evidence", "")
        evidence_path = repo / evidence
        if not record.get("reason") or not record.get("reviewer") or not evidence.startswith("docs/acceptance/") or not evidence_path.resolve().is_relative_to(repo) or not evidence_path.is_file():
            errors.append(issue("review_record_invalid", record_path.relative_to(repo).as_posix(), "Review needs reason, reviewer and repository acceptance evidence"))
            continue
        for change in record.get("changes", []):
            reviews.add((change["path"], change["before_sha256"], change["after_sha256"]))
    changes = []
    for relative in candidates:
        before = git_text_digest(git_file(repo, revision, relative))
        target = repo / relative
        after = git_text_digest(target.read_bytes()) if target.is_file() else None
        if before == after:
            continue
        reviewed = (relative, before, after) in reviews
        changes.append({"path": relative, "before_sha256": before, "after_sha256": after, "review_record_matched": reviewed})
        if not bootstrap and not reviewed:
            errors.append(issue("unreviewed_source_or_pin_change", relative, "Changed source or frozen pin requires an exact-hash review record; regenerating baselines is not approval"))
    return {"status": "BOOTSTRAP" if bootstrap else "CHECKED", "base_commit": revision,
            "bootstrap_reason": "Git base predates the first frozen inventory" if bootstrap else None,
            "changed_file_count": len(changes), "changes": changes}, errors


def run_checks(repo: Path, base_ref: str | None = None) -> dict[str, Any]:
    baseline = read_json(repo / INVENTORY)
    current, errors = check_source(repo, baseline)
    errors.extend(check_manifests(repo, current))
    errors.extend(check_source_images(repo))
    errors.extend(check_conflicts(repo))
    errors.extend(check_implicit_conversion(repo))
    errors.extend(check_lossy_guards(repo))
    git_audit, git_errors = check_git_changes(repo, base_ref)
    errors.extend(git_errors)
    tables = source_tables(current)
    return {"status": "FAIL" if errors else "PASS", "source_tables": len(tables),
            "source_documents": len({table["path"] for table in tables}),
            "baseline_tables": len(source_tables(baseline)), "issue_count": len(errors),
            "issues": errors, "git_change_audit": git_audit,
            "scope": "Static source and traceability checks only; no visual or human acceptance claim"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--base-ref")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        payload = run_checks(args.repo_root.resolve(), args.base_ref)
    except (OSError, ValueError, KeyError, SyntaxError, subprocess.SubprocessError) as exc:
        payload = {"status": "FAIL", "issue_count": 1, "issues": [issue("gate_error", "", str(exc))]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
