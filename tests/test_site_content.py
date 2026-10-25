from __future__ import annotations

import sys
import unittest
from pathlib import Path

import markdown
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from site_content import adapt_site_content, load_semantic_profile
from reader_content import content_signature


def render(path: str) -> str:
    return markdown.markdown((ROOT / 'docs' / path).read_text(encoding='utf8'),
                             extensions=['tables', 'md_in_html', 'sane_lists', 'toc'])


class SiteContentPresentationTests(unittest.TestCase):
    def test_profiled_documents_preserve_all_content_and_canonical_geometry(self):
        count = 0
        for path in load_semantic_profile()['documents']:
            with self.subTest(path=path):
                source = render(path)
                before = BeautifulSoup(source, 'html.parser')
                after = BeautifulSoup(adapt_site_content(source, path), 'html.parser')
                self.assertEqual(before.get_text(), after.get_text())
                self.assertEqual(content_signature(before), content_signature(after))
                count += len(after.select('.reader-color-cell'))
        self.assertEqual(count, 304)

    def test_identical_weapon_diagrams_keep_distinct_reference_colours(self):
        path = '核心规则/购买项/装备类/武器类与武器属性.md'
        soup = BeautifulSoup(adapt_site_content(render(path), path), 'html.parser')
        colors = [[c.get('data-source-background') for c in t.find_all('td')]
                  for t in soup.find_all('table')]
        self.assertEqual(colors, [
            ['#92d050', None, '#92d050'],
            [None, '#ffc000', None],
            ['#92d050', '#ffc000', '#92d050'],
            ['#ffc000', None, '#ffc000'],
            ['#ffc000', '#ffc000', '#ffc000'],
        ])

    def test_reference_only_effect_table_is_not_reintroduced(self):
        path = '核心规则/效果/效果表.md'
        source = render(path)
        self.assertNotIn('<table', source)
        output = adapt_site_content(source, path)
        self.assertNotIn('<table', output)
        self.assertEqual(BeautifulSoup(source, 'html.parser').get_text(),
                         BeautifulSoup(output, 'html.parser').get_text())

    def test_coloured_table_text_or_geometry_drift_fails_closed(self):
        path = '创作指南/属性平衡.md'
        source = render(path)
        for changed in (source.replace('传闻', '已修改', 1),
                        source.replace('colspan="2"', 'colspan="3"', 1),
                        source.replace('html-6d6638bed69c', 'changed-table-id', 1)):
            with self.subTest(changed=changed[:30]):
                with self.assertRaisesRegex(ValueError, 'semantic presentation drift'):
                    adapt_site_content(changed, path)

    def test_nested_table_rowspans_links_and_heading_ids_are_untouched(self):
        source = ('<h2 id="anchor">标题<a class="headerlink" href="#anchor">¶</a></h2>'
                  '<p>正文<strong>强调</strong>与<a href="other.html#x">链接</a></p>'
                  '<table data-table-id="outer"><tbody><tr><td rowspan="2">甲'
                  '<table data-table-id="nested"><tr><td>内层</td></tr></table>'
                  '</td><td colspan="2">乙</td></tr><tr><td>丙</td><td>丁</td></tr>'
                  '</tbody></table><img src="icon.png" alt="图标" width="24">')
        result = BeautifulSoup(adapt_site_content(source, 'new-page.md'), 'html.parser')
        self.assertEqual(content_signature(BeautifulSoup(source, 'html.parser')),
                         content_signature(result))
        self.assertEqual(len(result.select('.pmtrpg-table-scroll')), 1)
        self.assertEqual(result.select_one('table[data-table-id="outer"]')['data-reader-columns'], '3')
        self.assertIn('reader-nested-table', result.select_one('table[data-table-id="nested"]')['class'])
        self.assertEqual(result.h2['id'], 'anchor')
        self.assertEqual(result.select_one('.headerlink')['href'], '#anchor')

    def test_plain_prose_is_never_promoted_to_heading(self):
        path = '都市箴言/平衡参考/属性_技能参考.md'
        before = BeautifulSoup(render(path), 'html.parser')
        after = BeautifulSoup(adapt_site_content(str(before), path), 'html.parser')
        self.assertEqual(content_signature(before)['headings'], content_signature(after)['headings'])
        self.assertEqual(len(after.select('p.reader-section-label')), 6)
        self.assertFalse(any('font-size' in tag.get('style', '') for tag in after.find_all(True)))


if __name__ == '__main__':
    unittest.main()
