from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_canonical_tables import (  # noqa: E402
    CanonicalHTMLParser,
    compare_structure,
    validate_canonical_docs,
)
from generate_table_inventory import mask_markdown_code, stable_id  # noqa: E402
from rebuild_html_tables_to_pipe import (  # noqa: E402
    LossyTableConversionError,
    rebuild_file,
)
from convert_markdown_tables_to_html import convert_block, execute  # noqa: E402
from annotate_canonical_tables import annotate_open_tag  # noqa: E402
from normalize_canonical_table_attributes import canonical_open_tag  # noqa: E402


class CanonicalTableValidationTests(unittest.TestCase):
    def validate(self, source: str, assets: dict[str, bytes] | None = None) -> list[str]:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            path = repo / "docs" / "sample.md"
            path.parent.mkdir(parents=True)
            path.write_text(source, encoding="utf-8")
            for relative, content in (assets or {}).items():
                target = repo / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            parser = CanonicalHTMLParser(path, repo)
            parser.feed(mask_markdown_code(source))
            parser.close()
            return [issue.code for issue in parser.issues]

    def test_valid_canonical_table_passes(self) -> None:
        source = """
<table class="pmtrpg-table" data-table-id="sample-1">
<thead><tr><th scope="col">名称</th><th scope="col">效果</th></tr></thead>
<tbody><tr><th scope="row">示例</th><td>文本</td></tr></tbody>
</table>
"""
        self.assertEqual(self.validate(source), [])

    def test_invalid_rowspan_and_colspan_fail(self) -> None:
        source = """
<table class="pmtrpg-table" data-table-id="broken-span">
<tr><th scope="col">A</th><th scope="col">B</th></tr>
<tr><td rowspan="0">x</td><td colspan="2">y</td></tr>
</table>
"""
        codes = self.validate(source)
        self.assertIn("invalid_span", codes)
        self.assertIn("column_mismatch", codes)

    def test_missing_image_and_alt_fail(self) -> None:
        source = """
<table class="pmtrpg-table" data-table-id="broken-image">
<tr><th scope="col">图</th></tr>
<tr><td><img src="../assets/missing.png"></td></tr>
</table>
"""
        codes = self.validate(source)
        self.assertIn("image_missing", codes)
        self.assertIn("image_alt", codes)

    def test_unclosed_nested_table_fails(self) -> None:
        source = """
<table class="pmtrpg-table" data-table-id="outer">
<tr><td>
<table class="pmtrpg-table" data-table-id="inner">
<tr><td>x</td></tr>
</table>
"""
        codes = self.validate(source)
        self.assertIn("table_unclosed", codes)

    def test_duplicate_ids_across_documents_fail(self) -> None:
        source = """
<table class="pmtrpg-table" data-table-id="duplicate-id">
<tr><th scope="col">名称</th></tr><tr><td>示例</td></tr>
</table>
"""
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            docs = repo / "docs"
            docs.mkdir()
            (docs / "one.md").write_text(source, encoding="utf-8")
            (docs / "two.md").write_text(source, encoding="utf-8")
            issues = validate_canonical_docs(docs, repo, set())
            self.assertEqual(
                [issue.code for issue in issues].count("table_id_duplicate"),
                1,
            )

    def test_inventory_id_does_not_depend_on_source_line(self) -> None:
        first = stable_id("docs/sample.md", "html", 2, "<table>")
        after_prose_insertion = stable_id("docs/sample.md", "html", 2, "<table>")
        self.assertEqual(first, after_prose_insertion)


class StructuralComparisonTests(unittest.TestCase):
    def item(
        self,
        *,
        columns: int = 2,
        spans: list[dict[str, int]] | None = None,
        representation: str = "html",
    ) -> dict:
        return {
            "id": "table-stable-id",
            "path": "docs/sample.md",
            "scope": "source-content",
            "line": 2,
            "representation": representation,
            "rows": 2,
            "columns": columns,
            "span_signature": spans or [],
            "nested_depth": 0,
            "images": [],
        }

    def test_identical_structure_passes(self) -> None:
        baseline = {"tables": [self.item()]}
        current = {"tables": [self.item()]}
        self.assertEqual(compare_structure(baseline, current), [])

    def test_representation_change_with_same_structure_passes(self) -> None:
        baseline = {"tables": [self.item(representation="markdown-pipe")]}
        current = {"tables": [self.item(representation="html")]}
        self.assertEqual(compare_structure(baseline, current), [])

    def test_changed_span_fails(self) -> None:
        baseline = {"tables": [self.item()]}
        current = {
            "tables": [
                self.item(columns=3, spans=[{"row": 1, "colspan": 2, "rowspan": 1}])
            ]
        }
        issues = compare_structure(baseline, current)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "structure_changed")
        self.assertIn("span_signature", issues[0].message)


class LossyConversionGuardTests(unittest.TestCase):
    def test_html_to_pipe_rewrite_is_refused_by_default(self) -> None:
        source = "<table><tr><td>不得隐式降级</td></tr></table>\n"
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "sample.md"
            path.write_text(source, encoding="utf-8")
            with self.assertRaises(LossyTableConversionError):
                rebuild_file(str(path))
            self.assertEqual(path.read_text(encoding="utf-8"), source)


class MarkdownToCanonicalHTMLTests(unittest.TestCase):
    def test_block_conversion_preserves_inline_markup_and_structure(self) -> None:
        block, rows, columns = convert_block(
            [
                "| **名称** | 效果 |",
                "| :--- | ---: |",
                "| 示例 | 第一行<br>第二行 |",
            ],
            "markdown-stable-id",
        )
        self.assertEqual((rows, columns), (2, 2))
        self.assertIn('data-table-id="markdown-stable-id"', block)
        self.assertIn('<th scope="col" class="align-left"><strong>名称</strong></th>', block)
        self.assertIn('<td class="align-right">第一行<br>第二行</td>', block)

    def test_dry_run_does_not_rewrite_source(self) -> None:
        source = "| 名称 | 效果 |\n| --- | --- |\n| 示例 | 文本 |\n"
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            path = repo / "docs" / "sample.md"
            path.parent.mkdir(parents=True)
            path.write_text(source, encoding="utf-8")
            inventory = {
                "tables": [
                    {
                        "id": "markdown-stable-id",
                        "path": "docs/sample.md",
                        "scope": "source-content",
                        "representation": "markdown-pipe",
                        "line": 1,
                        "end_line": 3,
                        "rows": 2,
                        "columns": 2,
                    }
                ]
            }
            converted = execute(repo, inventory, apply=False)
            self.assertEqual(len(converted), 1)
            self.assertEqual(path.read_text(encoding="utf-8"), source)


class CanonicalAnnotationTests(unittest.TestCase):
    def test_annotation_preserves_legacy_attributes(self) -> None:
        annotated = annotate_open_tag(
            '<table border="1" class="wide">',
            "html-stable-id",
        )
        self.assertEqual(
            annotated,
            '<table border="1" class="wide pmtrpg-table" data-table-id="html-stable-id">',
        )

    def test_annotation_refuses_existing_id(self) -> None:
        with self.assertRaises(ValueError):
            annotate_open_tag(
                '<table data-table-id="already-present">',
                "replacement",
            )

    def test_legacy_table_attributes_are_removed_without_changing_id(self) -> None:
        self.assertEqual(
            canonical_open_tag(
                '<table border="1" width="600" class="pmtrpg-table" '
                'data-table-id="html-stable-id">'
            ),
            '<table class="pmtrpg-table" data-table-id="html-stable-id">',
        )


if __name__ == "__main__":
    unittest.main()
