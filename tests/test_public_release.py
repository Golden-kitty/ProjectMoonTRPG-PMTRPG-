import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_public_release import navigation_paths, release_sections


class PublicReleaseTests(unittest.TestCase):
    def test_navigation_order_is_preserved(self):
        self.assertEqual(navigation_paths([{"First": "a.md"}, {"Group": [{"Second": "b.md"}]}]), ["a.md", "b.md"])

    def test_public_book_covers_all_source_tables_without_duplicate_documents(self):
        sections, excluded, coverage = release_sections(ROOT)
        paths = [path for path, label in sections]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(coverage["source_table_count"], 370)
        self.assertFalse(set(paths) & set(excluded))
        self.assertTrue(all(not path.startswith(("engineering/", "acceptance/", "tasks/")) for path in paths))


if __name__ == "__main__":
    unittest.main()
