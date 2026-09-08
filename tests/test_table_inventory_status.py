from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from generate_table_inventory import apply_current_status, load_review_statuses  # noqa: E402


def canonical_item(table_id: str = "html-test") -> dict[str, object]:
    return {
        "id": table_id,
        "scope": "source-content",
        "representation": "html",
        "source_attributes": {
            "class": "pmtrpg-table",
            "data-table-id": table_id,
        },
        "review_required": True,
        "disposition": "待验收",
        "recommendation": "完成分发与人工验收",
        "review_owner": None,
    }


class TableInventoryStatusTests(unittest.TestCase):
    def test_closed_stage7_status_closes_review_and_marks_html_migrated(self) -> None:
        item = canonical_item()
        apply_current_status([item], {"html-test": "closed_by_user_review_policy"})
        self.assertFalse(item["review_required"])
        self.assertEqual(item["review_status"], "closed_by_user_review_policy")
        self.assertEqual(item["disposition"], "已迁移 HTML")

    def test_only_unresolved_ambiguity_is_owned_by_user(self) -> None:
        item = canonical_item()
        apply_current_status([item], {"html-test": "unresolved_semantic_ambiguity"})
        self.assertTrue(item["review_required"])
        self.assertEqual(item["review_owner"], "用户")

    def test_unconverted_source_table_remains_conversion_required(self) -> None:
        item = canonical_item()
        item["representation"] = "markdown-pipe"
        item.pop("source_attributes")
        apply_current_status([item], {"html-test": "closed_by_user_review_policy"})
        self.assertTrue(item["review_required"])
        self.assertEqual(item["review_status"], "conversion_required")
        self.assertEqual(item["disposition"], "待迁移")

    def test_manifest_loader_rejects_conflicting_duplicate_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for number, status in ((1, "accepted_by_user"), (2, "closed_by_user_review_policy")):
                payload = {"tables": [{"id": "html-test", "review_status": status}]}
                (root / f"stage7-batch-{number:02d}.json").write_text(
                    json.dumps(payload),
                    encoding="utf-8",
                )
            with self.assertRaisesRegex(ValueError, "Conflicting review status"):
                load_review_statuses(root)


if __name__ == "__main__":
    unittest.main()
