from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from generate_table_rollout_batches import (  # noqa: E402
    classify_review_status,
    high_risk_reasons,
    partition_documents,
    table_tier,
)


class TableRolloutBatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = {
            "high_risk_criteria": {
                "nested_depth_greater_than": 0,
                "rowspan_greater_than": 1,
                "columns_at_least": 10,
                "page_candidate_count_greater_than": 1,
                "ambiguous_mapping_area_at_least": 80,
            }
        }

    def test_feature_tiers_follow_rollout_order(self) -> None:
        plain = {"risk": "low", "nested_depth": 0, "images": [], "span_signature": []}
        span = {
            **plain,
            "span_signature": [{"row": 1, "colspan": 2, "rowspan": 1}],
        }
        image = {**plain, "images": ["icon.png"]}
        high_image = {**image, "risk": "high"}
        special = {**plain, "nested_depth": 1}
        high = {**plain, "risk": "high"}
        self.assertEqual(
            [table_tier(item) for item in (plain, span, image, high_image, special, high)],
            [0, 1, 2, 2, 3, 3],
        )

    def test_partition_keeps_documents_atomic_and_within_limits(self) -> None:
        documents = [
            {"path": f"docs/{index:02d}.md", "table_count": count, "tier": index // 4}
            for index, count in enumerate([7, 8, 6, 9, 12, 5, 11, 4, 10, 8, 9, 7])
        ]
        batches = partition_documents(documents, minimum=20, maximum=40, target=30)
        flattened = [document["path"] for batch in batches for document in batch]
        self.assertEqual(flattened, [document["path"] for document in documents])
        self.assertEqual(len(flattened), len(set(flattened)))
        for batch in batches:
            count = sum(document["table_count"] for document in batch)
            self.assertGreaterEqual(count, 20)
            self.assertLessEqual(count, 40)

    def test_partition_rejects_oversized_document(self) -> None:
        with self.assertRaisesRegex(ValueError, "exceed maximum"):
            partition_documents(
                [{"path": "docs/oversized.md", "table_count": 41, "tier": 0}],
                minimum=20,
                maximum=40,
                target=30,
            )

    def test_high_risk_reasons_cover_structural_and_mapping_risks(self) -> None:
        item = {
            "nested_depth": 1,
            "span_signature": [{"rowspan": 3, "colspan": 1}],
            "rows": 12,
            "columns": 10,
            "source_page_candidates": [10, 11],
        }
        self.assertEqual(
            high_risk_reasons(item, self.policy),
            ["nested_depth=1", "rowspan=3", "columns=10", "ambiguous_page_candidates=2,area=120"],
        )

    def test_mapping_ambiguity_requires_large_table(self) -> None:
        item = {
            "nested_depth": 0,
            "span_signature": [],
            "rows": 4,
            "columns": 7,
            "source_page_candidates": [10, 11],
        }
        self.assertEqual(high_risk_reasons(item, self.policy), [])

    def test_review_status_precedence_avoids_duplicate_review(self) -> None:
        item = {
            "id": "html-test",
            "nested_depth": 1,
            "span_signature": [],
            "rows": 4,
            "columns": 4,
            "source_page_candidates": [10],
        }
        status = classify_review_status(
            item,
            {"html-test": "accepted-set"},
            {"html-test": "evidence-set"},
            {"html-test": "review-set"},
            self.policy,
        )
        self.assertEqual(status, ("accepted_by_user", [], "accepted-set"))

        status = classify_review_status(
            item,
            {},
            {"html-test": "evidence-set"},
            {"html-test": "review-set"},
            self.policy,
        )
        self.assertEqual(status, ("source_verified_by_pdf_evidence", [], "evidence-set"))

        status = classify_review_status(
            item,
            {},
            {},
            {"html-test": "review-set"},
            self.policy,
        )
        self.assertEqual(
            status,
            ("source_verified_by_high_risk_review", ["nested_depth=1"], "review-set"),
        )


if __name__ == "__main__":
    unittest.main()
