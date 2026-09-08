from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

from bs4 import BeautifulSoup
from docx import Document

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_distribution_tables as validator
from export_sample_docs import _add_docx_table


COMBINED = (
    '<table data-table-id="combined"><tr><td colspan="2" rowspan="3">A</td><td>B</td></tr>'
    '<tr><td>C</td></tr><tr><td>D</td></tr></table>'
)


class DistributionTableStructureTests(unittest.TestCase):
    def converted(self, markup: str):
        soup = BeautifulSoup(markup, "html.parser")
        document = Document()
        for table in soup.find_all("table", recursive=False):
            _add_docx_table(document, table)
        expected = [validator.html_table_structure(table) for table in soup.find_all("table")]
        xml = ElementTree.fromstring(document._element.xml)
        return expected, xml

    def test_combined_merge_counts_every_physical_continuation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "sample.md"
            source.write_text(COMBINED, encoding="utf-8")
            with patch.object(validator, "DOCS_DIR", root):
                summary = validator.html_summary([source])
        self.assertEqual(summary["colspan_cells"], 1)
        self.assertEqual(summary["docx_gridspan_slots"], 3)
        self.assertEqual(summary["rowspan_slots"], 3)

    def test_combined_merge_retains_anchor_geometry(self):
        expected, xml = self.converted(COMBINED)
        actual = validator.docx_table_structures(xml)
        self.assertEqual(actual[0]["merged_cells"], [
            {"row": 0, "col": 0, "rowspan": 3, "colspan": 2},
        ])
        self.assertEqual(validator.compare_docx_table_structures(expected, actual), [])

    def test_continuation_width_corruption_fails_with_unchanged_gridspan_count(self):
        expected, xml = self.converted(COMBINED)
        spans = xml.findall(f".//{{{validator.W_NS}}}gridSpan")
        self.assertEqual(len(spans), 3)
        spans[1].set(f"{{{validator.W_NS}}}val", "3")
        actual = validator.docx_table_structures(xml)
        self.assertEqual(len(xml.findall(f".//{{{validator.W_NS}}}gridSpan")), 3)
        self.assertTrue(validator.compare_docx_table_structures(expected, actual))
        self.assertTrue(any("orphan_or_width_changed_vmerge" in item for item in actual[0]["errors"]))

    def test_broken_vertical_chain_fails_with_unchanged_vmerge_count(self):
        expected, xml = self.converted(COMBINED)
        merges = xml.findall(f".//{{{validator.W_NS}}}vMerge")
        self.assertEqual(len(merges), 3)
        merges[1].set(f"{{{validator.W_NS}}}val", "restart")
        actual = validator.docx_table_structures(xml)
        self.assertTrue(validator.compare_docx_table_structures(expected, actual))
        self.assertIn("merged_cells", validator.compare_docx_table_structures(expected, actual)[0]["fields"])

    def test_removed_continuation_gridspan_is_detected(self):
        expected, xml = self.converted(COMBINED)
        rows = xml.findall(f".//{{{validator.W_NS}}}tbl/{{{validator.W_NS}}}tr")
        properties = rows[1].find(f"{{{validator.W_NS}}}tc/{{{validator.W_NS}}}tcPr")
        properties.remove(properties.find(f"{{{validator.W_NS}}}gridSpan"))
        self.assertTrue(validator.compare_docx_table_structures(expected, validator.docx_table_structures(xml)))

    def test_nested_table_is_compared_separately_in_source_order(self):
        markup = '<table><tr><td>Outer' + COMBINED + '</td><td>X</td></tr></table>'
        expected, xml = self.converted(markup)
        actual = validator.docx_table_structures(xml)
        self.assertEqual([table["nested_depth"] for table in actual], [0, 1])
        self.assertEqual(validator.compare_docx_table_structures(expected, actual), [])

    def test_moved_horizontal_merge_fails_with_unchanged_counts(self):
        markup = '<table><tr><td colspan="2">A</td><td>B</td></tr><tr><td>C</td><td colspan="2">D</td></tr></table>'
        expected, xml = self.converted(markup)
        first_row = xml.find(f".//{{{validator.W_NS}}}tbl/{{{validator.W_NS}}}tr")
        first, second = first_row.findall(f"{{{validator.W_NS}}}tc")
        properties = first.find(f"{{{validator.W_NS}}}tcPr")
        span = properties.find(f"{{{validator.W_NS}}}gridSpan")
        properties.remove(span)
        second.find(f"{{{validator.W_NS}}}tcPr").append(span)
        actual = validator.docx_table_structures(xml)
        self.assertEqual(actual[0]["errors"], [])
        self.assertTrue(validator.compare_docx_table_structures(expected, actual))

    def test_chm_geometry_uses_table_ids_independent_of_filename_sort(self):
        tables = BeautifulSoup(COMBINED + '<table data-table-id="plain"><tr><td>X</td></tr></table>',
                               "html.parser").find_all("table")
        records = [{"id": table["data-table-id"], **validator.html_table_structure(table)} for table in tables]
        self.assertEqual(validator.compare_html_table_structures(records, list(reversed(records))), [])

    def test_chm_colspan_corruption_fails_even_when_id_survives(self):
        table = BeautifulSoup(COMBINED, "html.parser").find("table")
        expected = [{"id": table["data-table-id"], **validator.html_table_structure(table)}]
        table.find("td")["colspan"] = "3"
        actual = [{"id": table["data-table-id"], **validator.html_table_structure(table)}]
        self.assertTrue(validator.compare_html_table_structures(expected, actual))


if __name__ == "__main__":
    unittest.main()
