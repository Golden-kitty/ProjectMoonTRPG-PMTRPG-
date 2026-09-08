from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import export_sample_docs as exporter


class ReleaseLinkTests(unittest.TestCase):
    def test_cross_chapter_links_and_duplicate_heading_ids(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "a.md").write_text('# Shared\n\n[Other](b.md#shared)\n', encoding="utf-8")
            (root / "b.md").write_text('# Shared\n\n[Self](#shared)\n', encoding="utf-8")
            with patch.object(exporter, "DOCS_DIR", root):
                result = BeautifulSoup(exporter.build_full_html("Book", [("a.md", "A"), ("b.md", "B")]), "html.parser")
            self.assertIsNotNone(result.find(id="section-1--shared"))
            self.assertIsNotNone(result.find(id="section-2--shared"))
            self.assertEqual(result.find("a", string="Other")["href"], "#section-2--shared")
            self.assertEqual(result.find("a", string="Self")["href"], "#section-2--shared")

    def test_chm_links_are_package_relative_and_preserve_fragments(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            docs = root / "docs"
            docs.mkdir()
            (docs / "a.md").write_text('# A\n\n[Other](b.md#shared)\n', encoding="utf-8")
            (docs / "b.md").write_text('# Shared\n', encoding="utf-8")
            with patch.object(exporter, "DOCS_DIR", docs):
                exporter.export_chm(root / "out", [("a.md", "A"), ("b.md", "B")], "Book", "book", False)
            page = BeautifulSoup((root / "out/chm/html/sample-01.html").read_text(encoding="utf-8"), "html.parser")
            self.assertEqual(page.find("a", string="Other")["href"], "sample-02.html#section-1--shared")


if __name__ == "__main__":
    unittest.main()
