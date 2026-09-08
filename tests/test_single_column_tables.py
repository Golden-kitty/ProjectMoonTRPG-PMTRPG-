from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import markdown
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from convert_markdown_tables_to_html import convert_block, execute  # noqa: E402
from generate_table_inventory import is_pipe_separator, markdown_inventory, split_pipe_row  # noqa: E402
from validate_rendered_tables import validate_rendered  # noqa: E402


SINGLE_COLUMN = "| 调整表 |\n| --- |\n| **耗时修正项** |\n| 第一行<br>第二行 |\n"


class SingleColumnInventoryTests(unittest.TestCase):
    def test_single_column_rows_and_separator_are_recognized(self) -> None:
        self.assertEqual(split_pipe_row("| 调整表 |"), ["调整表"])
        self.assertEqual(split_pipe_row("| |"), [""])
        self.assertTrue(is_pipe_separator("| --- |"))
        self.assertTrue(is_pipe_separator("| :---: |"))
        self.assertIsNone(split_pipe_row("ordinary prose"))

    def test_single_column_inventory_counts_rendered_rows_and_stable_id(self) -> None:
        item, = markdown_inventory("docs/sample.md", SINGLE_COLUMN, [])
        self.assertEqual((item["rows"], item["columns"]), (3, 1))
        self.assertEqual((item["line"], item["end_line"]), (1, 4))
        shifted, = markdown_inventory("docs/sample.md", "# Heading\n\n" + SINGLE_COLUMN, [])
        self.assertEqual(item["id"], shifted["id"])

    def test_single_column_examples_inside_code_are_ignored(self) -> None:
        source = "```md\n" + SINGLE_COLUMN + "```\n\n`| a |`\n`| --- |`\n"
        self.assertEqual(markdown_inventory("docs/sample.md", source, []), [])

    def test_converter_preserves_text_emphasis_and_line_breaks(self) -> None:
        converted, rows, columns = convert_block(SINGLE_COLUMN.splitlines(), "single-stable")
        self.assertEqual((rows, columns), (3, 1))
        before = BeautifulSoup(markdown.markdown(SINGLE_COLUMN, extensions=["tables"]), "html.parser")
        after = BeautifulSoup(converted, "html.parser")
        self.assertEqual(
            [cell.decode_contents() for cell in before.select("th,td")],
            [cell.decode_contents() for cell in after.select("th,td")],
        )
        self.assertEqual(after.table["data-table-id"], "single-stable")

    def test_single_item_execute_preserves_other_tables_and_surrounding_text(self) -> None:
        prefix = '# 保留标题\n\n<table data-table-id="existing"><tr><td>原文</td></tr></table>\n\n'
        suffix = "\n## 保留后文\n"
        source = prefix + SINGLE_COLUMN + suffix
        item, = markdown_inventory("docs/sample.md", source, [])
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            path = repo / "docs/sample.md"
            path.parent.mkdir()
            path.write_text(source, encoding="utf-8")
            converted = execute(repo, {"tables": [item]}, apply=True)
            result = path.read_text(encoding="utf-8")
            self.assertEqual(len(converted), 1)
            self.assertTrue(result.startswith(prefix))
            self.assertTrue(result.endswith(suffix))
            self.assertIn('data-table-id="existing"', result)
            self.assertIn(f'data-table-id="{item["id"]}"', result)
            self.assertEqual(markdown_inventory("docs/sample.md", result, []), [])


class RenderedInventoryCoverageTests(unittest.TestCase):
    def validate(self, html: str, *, inventory: dict | None = None, filename: str = "sample.html") -> dict:
        with tempfile.TemporaryDirectory() as raw:
            site = Path(raw)
            path = site / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(html, encoding="utf-8")
            return validate_rendered(inventory or {"tables": []}, site)

    def test_known_article_table_passes_but_extra_table_on_same_page_fails(self) -> None:
        inventory = {"tables": [{
            "scope": "source-content", "path": "docs/sample.md", "id": "known",
            "rows": 1, "columns": 1, "span_signature": [], "nested_depth": 0, "images": [],
        }]}
        known = '<table data-table-id="known"><tr><td>x</td></tr></table>'
        result = self.validate(f"<article>{known}</article>", inventory=inventory)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["observed_tables"], 1)
        result = self.validate(f"<article>{known}<table><tr><td>missed</td></tr></table></article>", inventory=inventory)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual([issue["code"] for issue in result["issues"]], ["rendered_table_id_missing"])

    def test_extra_single_column_table_without_id_fails(self) -> None:
        table = markdown.markdown(SINGLE_COLUMN, extensions=["tables"])
        result = self.validate(f"<article>{table}</article>")
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["issues"][0]["code"], "rendered_table_id_missing")
        self.assertEqual(result["article_tables"], 1)

    def test_unlisted_canonical_table_on_unlisted_page_fails(self) -> None:
        result = self.validate('<article><table data-table-id="unknown"><tr><td>x</td></tr></table></article>')
        self.assertEqual(result["issues"][0]["code"], "rendered_table_not_in_inventory")

    def test_theme_navigation_and_code_examples_are_ignored(self) -> None:
        table = "<table><tr><td>example</td></tr></table>"
        result = self.validate(
            f"<nav>{table}</nav><article><nav>{table}</nav><pre>{table}</pre>"
            f"<code>{table}</code><pre><code>&lt;table&gt;&lt;/table&gt;</code></pre></article>"
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["article_tables"], 0)

    def test_supporting_evidence_page_is_not_source_content(self) -> None:
        result = self.validate('<article><table><tr><td>evidence</td></tr></table></article>', filename="engineering/audit.html")
        self.assertEqual(result["status"], "PASS")

    def test_known_id_in_navigation_does_not_satisfy_body_inventory(self) -> None:
        inventory = {"tables": [{"scope": "source-content", "path": "docs/sample.md", "id": "known"}]}
        result = self.validate('<nav><table data-table-id="known"></table></nav><article>正文</article>', inventory=inventory)
        self.assertEqual(result["issues"][0]["code"], "table_dom_count")


if __name__ == "__main__":
    unittest.main()
