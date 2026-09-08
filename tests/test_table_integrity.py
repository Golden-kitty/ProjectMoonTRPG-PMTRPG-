from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_table_integrity import (  # noqa: E402
    INVENTORY, MANIFEST_DIR, REGISTRIES, REVIEW_DIR, check_conflicts,
    check_git_changes, check_implicit_conversion, check_lossy_guards,
    check_manifests, check_source, check_source_images, digest,
)
from generate_table_inventory import build_inventory  # noqa: E402


TABLE = '''<table class="pmtrpg-table" data-table-id="sample-1">
<tr><th scope="col">名称</th><th scope="col">效果</th></tr>
<tr><td>A</td><td><img src="../assets/icon.png" alt="红心">数字 3</td></tr>
</table>
'''


class IntegrityFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name).resolve()
        self.source = self.repo / "docs/sample.md"
        self.source.parent.mkdir()
        self.source.write_text("# 规则\n\n" + TABLE, encoding="utf-8")
        self.write("assets/icon.png", b"fixture")
        self.baseline = self.inventory()
        self.freeze()

    def write(self, relative: str, content: bytes) -> None:
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def write_json(self, relative: str, content: dict) -> None:
        self.write(relative, (json.dumps(content, ensure_ascii=False) + "\n").encode("utf-8"))

    def inventory(self) -> dict:
        return build_inventory(self.repo / "docs", self.repo / "docs/missing-map.md")

    def freeze(self) -> None:
        self.write_json(INVENTORY, self.baseline)
        documents = [{"path": "docs/sample.md", "sha256": digest(self.source.read_bytes()), "table_count": 1}]
        snapshot = "".join(f"{doc['path']}\0{doc['sha256']}\n" for doc in documents)
        self.write_json(f"{MANIFEST_DIR}/stage7-batch-01.json", {
            "tables": [{**table, "review_status": "closed_by_user_review_policy"} for table in self.baseline["tables"]],
            "documents": documents, "table_count": 1, "document_count": 1,
            "inventory_sha256": digest((self.repo / INVENTORY).read_bytes()),
            "source_snapshot_sha256": digest(snapshot.encode("utf-8")),
        })
        self.write_json(REGISTRIES[0], {"accepted_sets": []})
        self.write_json(REGISTRIES[1], {
            "mode": "high-risk-source-only", "source_verified_sets": [],
            "high_risk_criteria": {"nested_depth_greater_than": 0, "rowspan_greater_than": 1,
                                   "columns_at_least": 10, "page_candidate_count_greater_than": 1,
                                   "ambiguous_mapping_area_at_least": 80},
        })
        self.write_json(REGISTRIES[2], {"reviewed_sets": []})

    def codes(self) -> list[str]:
        current, errors = check_source(self.repo, self.baseline)
        errors.extend(check_manifests(self.repo, current))
        return [error["code"] for error in errors]

    def git(self, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=self.repo, check=True,
                              capture_output=True, text=True, encoding="utf-8").stdout.strip()

    def git_baseline(self) -> str:
        self.git("init")
        self.git("config", "core.autocrlf", "false")
        self.git("config", "user.name", "Integrity Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("add", ".")
        self.git("commit", "-m", "Fixture baseline")
        return self.git("rev-parse", "HEAD")


class SourceIntegrityTests(IntegrityFixture):
    def test_unchanged_canonical_source_and_frozen_manifest_pass(self) -> None:
        self.assertEqual(self.codes(), [])

    def test_deleted_table_fails(self) -> None:
        self.source.write_text("# No table\n", encoding="utf-8")
        self.assertIn("table_missing", self.codes())
        self.assertIn("table_count_decreased", self.codes())

    def test_valid_but_changed_span_fails(self) -> None:
        self.source.write_text(TABLE.replace('<td>A</td><td>', '<td colspan="2">'), encoding="utf-8")
        self.assertIn("structure_changed", self.codes())

    def test_missing_image_fails(self) -> None:
        (self.repo / "assets/icon.png").unlink()
        self.assertIn("image_missing", self.codes())

    def test_missing_markdown_image_in_prose_also_fails(self) -> None:
        self.source.write_text("![icon](../assets/missing.png)\n" + TABLE, encoding="utf-8")
        self.assertIn("image_missing", [error["code"] for error in check_source_images(self.repo)])

    def test_forged_manifest_acceptance_does_not_replace_review_registry(self) -> None:
        relative = f"{MANIFEST_DIR}/stage7-batch-01.json"
        manifest = json.loads((self.repo / relative).read_text(encoding="utf-8"))
        manifest["tables"][0]["review_status"] = "accepted_by_user"
        self.write_json(relative, manifest)
        self.assertIn("review_status_mismatch", self.codes())

    def test_remote_image_fails_even_when_it_looks_resolvable(self) -> None:
        self.source.write_text(TABLE.replace("../assets/icon.png", "https://example.invalid/icon.png"), encoding="utf-8")
        self.assertIn("nonlocal_image", self.codes())

    def test_rule_text_change_without_structure_change_fails(self) -> None:
        self.source.write_text(self.source.read_text(encoding="utf-8").replace("数字 3", "数字 4"), encoding="utf-8")
        codes = self.codes()
        self.assertIn("source_hash_changed", codes)
        self.assertNotIn("structure_changed", codes)

    def test_prose_outside_table_is_hash_pinned_too(self) -> None:
        self.source.write_text("New rule outside table\n" + TABLE, encoding="utf-8")
        self.assertIn("source_hash_changed", self.codes())

    def test_markdown_table_reintroduction_fails(self) -> None:
        self.source.write_text("| A | B |\n| --- | --- |\n| x | y |\n", encoding="utf-8")
        self.assertIn("non_html_source_table", self.codes())

    def test_manifest_removal_and_duplicate_fail(self) -> None:
        original = self.repo / MANIFEST_DIR / "stage7-batch-01.json"
        shutil.copyfile(original, original.with_name("stage7-batch-02.json"))
        self.assertIn("manifest_table_duplicate", self.codes())
        self.assertIn("manifest_document_duplicate", self.codes())
        original.unlink()
        original.with_name("stage7-batch-02.json").unlink()
        self.assertIn("manifest_missing", self.codes())

    def test_inventory_cannot_exempt_a_rule_document(self) -> None:
        self.baseline["excluded_paths"] = ["docs/sample.md"]
        self.assertIn("source_excluded", self.codes())

    def test_unresolved_conflict_fails(self) -> None:
        self.source.write_text("<<<<<<< ours\n" + TABLE + "=======\n>>>>>>> theirs\n", encoding="utf-8")
        self.assertEqual(check_conflicts(self.repo)[0]["code"], "conflict_marker")


class ReviewTraceabilityTests(IntegrityFixture):
    def test_git_baseline_is_not_required_for_local_structure_check(self) -> None:
        audit, errors = check_git_changes(self.repo, None)
        self.assertEqual(audit["status"], "NOT_RUN")
        self.assertEqual(errors, [])

    def test_rewriting_source_and_all_local_pins_does_not_hide_git_change(self) -> None:
        base = self.git_baseline()
        self.source.write_text(TABLE.replace("数字 3", "数字 9"), encoding="utf-8")
        self.baseline = self.inventory()
        self.freeze()
        self.assertEqual(self.codes(), [])
        audit, errors = check_git_changes(self.repo, base)
        self.assertEqual(audit["status"], "CHECKED")
        self.assertIn("docs/sample.md", [error["path"] for error in errors])
        self.assertTrue(all(error["code"] == "unreviewed_source_or_pin_change" for error in errors))

    def test_exact_review_record_allows_reviewed_change_not_wrong_hash(self) -> None:
        base = self.git_baseline()
        self.source.write_text(TABLE.replace("数字 3", "数字 9"), encoding="utf-8")
        self.baseline = self.inventory()
        self.freeze()
        audit, errors = check_git_changes(self.repo, base)
        self.assertTrue(errors)
        self.write("docs/acceptance/review.md", b"Reviewed correction and source evidence.\n")
        record = {"reason": "Source-backed correction", "reviewer": "fixture reviewer",
                  "evidence": "docs/acceptance/review.md", "changes": audit["changes"]}
        self.write_json(f"{REVIEW_DIR}/fixture.json", record)
        self.assertEqual(check_git_changes(self.repo, base)[1], [])
        record["changes"][0]["after_sha256"] = "0" * 64
        self.write_json(f"{REVIEW_DIR}/fixture.json", record)
        self.assertTrue(check_git_changes(self.repo, base)[1])

    def test_new_prose_only_document_requires_a_record(self) -> None:
        base = self.git_baseline()
        self.write("docs/another-rule.md", b"A new rule without tables.\n")
        errors = check_git_changes(self.repo, base)[1]
        self.assertIn("docs/another-rule.md", [error["path"] for error in errors])

    def test_first_introduction_reports_bootstrap_instead_of_claiming_comparison(self) -> None:
        inventory_path = self.repo / INVENTORY
        frozen = inventory_path.read_bytes()
        inventory_path.unlink()
        base = self.git_baseline()
        inventory_path.write_bytes(frozen)
        audit, errors = check_git_changes(self.repo, base)
        self.assertEqual(audit["status"], "BOOTSTRAP")
        self.assertEqual(errors, [])


class ConversionProtectionTests(unittest.TestCase):
    def test_real_emergency_clis_refuse_default_writes(self) -> None:
        self.assertEqual(check_lossy_guards(ROOT), [])

    def test_implicit_production_import_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            (repo / "scripts").mkdir()
            for name in ("mkdocs_hooks.py", "export_sample_docs.py", "build_site.py"):
                (repo / "scripts" / name).write_text("pass\n", encoding="utf-8")
            (repo / "scripts/mkdocs_hooks.py").write_text(
                "from semantic_table_merges import apply_semantic_table_merges as merge\n",
                encoding="utf-8",
            )
            self.assertEqual(check_implicit_conversion(repo)[0]["code"], "implicit_conversion")

    def test_workflow_runs_on_release_branches_and_prs_with_full_history(self) -> None:
        workflow = yaml.load((ROOT / ".github/workflows/table-integrity.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        for event in ("push", "pull_request"):
            self.assertEqual(set(workflow["on"][event]["branches"]), {"main", "hotFix", "Halcyon'edit"})
        steps = workflow["jobs"]["table-integrity"]["steps"]
        checkout = next(step for step in steps if step.get("uses", "").startswith("actions/checkout@"))
        self.assertEqual(checkout["with"]["fetch-depth"], "0")
        gate = next(step["run"] for step in steps if "check_table_integrity.py" in step.get("run", ""))
        self.assertIn("--base-ref", gate)


if __name__ == "__main__":
    unittest.main()
