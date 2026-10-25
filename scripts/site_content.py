"""Apply the shared reader presentation to MkDocs HTML without changing rules.

The checked-in manifest uses document paths and canonical table IDs. No build
reads an old export or performs approximate text matching. Updating a coloured
table requires reviewing its presentation manifest as well as its rule text.
"""
from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

try:
    from scripts.reader_content import add_class, content_signature, declarations, ink_for
except ModuleNotFoundError:  # Direct execution and the existing unittest runner.
    from reader_content import add_class, content_signature, declarations, ink_for

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / 'assets/site/semantic-presentation.json'


def normalized(text: str) -> str:
    return re.sub(r'\s+', '', text)


def _classes(style: str) -> list[str]:
    props = declarations(style)
    result = []
    for prop, mapping in (
        ('font-weight', {'bold': 'reader-weight', '700': 'reader-weight',
                         'normal': 'reader-regular', '400': 'reader-regular'}),
        ('font-style', {'italic': 'reader-italic', 'normal': 'reader-upright'}),
        ('text-decoration', {'underline': 'reader-underline'}),
        ('color', {'red': 'reader-warning', '#ff0000': 'reader-warning',
                   'gray': 'reader-note', 'grey': 'reader-note', '#808080': 'reader-note',
                   '#404040': 'reader-note', '#ed7d31': 'reader-accent'}),
    ):
        name = mapping.get(props.get(prop, '').lower())
        if name:
            result.append(name)
    return result


def _background(style: str) -> str | None:
    props = declarations(style)
    value = props.get('background', props.get('background-color', '')).lower()
    value = {'red': '#ff0000', 'yellow': '#ffff00'}.get(value, value)
    if re.fullmatch(r'#[0-9a-f]{6}', value) and value != '#2e2217':
        return value
    return None


def _runs(record: dict) -> list[dict]:
    result = []
    for run in record.get('runs', []):
        classes = _classes(run.get('style', ''))
        if not classes:
            continue
        if result and result[-1]['end'] == run['start'] and result[-1]['classes'] == classes:
            result[-1]['end'] = run['end']
        else:
            result.append({'start': run['start'], 'end': run['end'], 'classes': classes})
    return result


def _apply_runs(node, runs: list[dict], soup) -> None:
    """Wrap the original text nodes; never replace inline semantic elements."""
    if not runs:
        return
    cursor = 0
    for text_node in list(node.find_all(string=True)):
        text = str(text_node)
        pieces = []
        current = ()
        buffer = ''
        for char in text:
            classes = tuple(next((r['classes'] for r in runs
                                  if r['start'] <= cursor < r['end']), []))
            if classes != current and buffer:
                pieces.append((current, buffer))
                buffer = ''
            current = classes
            buffer += char
            if not char.isspace():
                cursor += 1
        if buffer:
            pieces.append((current, buffer))
        for classes, value in pieces:
            if classes:
                span = soup.new_tag('span', attrs={'class': list(classes)})
                span.string = value
                text_node.insert_before(span)
            else:
                text_node.insert_before(NavigableString(value))
        text_node.extract()


def _rows(table):
    return [r for r in table.find_all('tr') if r.find_parent('table') is table]


def _shape(table) -> list:
    return [[(c.name, str(c.get('rowspan', '1')), str(c.get('colspan', '1')),
              normalized(c.get_text()))
             for c in row.find_all(['td', 'th'], recursive=False)] for row in _rows(table)]


def _shape_hash(table) -> str:
    return hashlib.sha256(json.dumps(_shape(table), ensure_ascii=False,
                                    separators=(',', ':')).encode('utf8')).hexdigest()


def _columns(table) -> int:
    """Count the logical grid, including columns occupied by rowspans."""
    occupied = set()
    maximum = 1
    for ri, row in enumerate(_rows(table)):
        ci = 0
        for cell in row.find_all(['td', 'th'], recursive=False):
            while (ri, ci) in occupied:
                ci += 1
            rs, cs = int(cell.get('rowspan', 1)), int(cell.get('colspan', 1))
            occupied.update((r, c) for r in range(ri, ri + rs) for c in range(ci, ci + cs))
            ci += cs
            maximum = max(maximum, ci)
    return maximum


@lru_cache(maxsize=1)
def load_semantic_profile() -> dict:
    profile = json.loads(MANIFEST_PATH.read_text(encoding='utf8'))
    if profile.get('schema_version') != 1:
        raise ValueError('Unsupported site semantic-presentation schema')
    return profile


def adapt_site_content(html: str, source_path: str) -> str:
    """Return a lossless themed HTML fragment for MkDocs on_page_content."""
    path = str(source_path).replace('\\', '/').removeprefix('docs/')
    profile = load_semantic_profile()['documents'].get(path, {})
    soup = BeautifulSoup(html, 'html.parser')
    before = content_signature(soup)
    original_text = soup.get_text()

    # Exact block text is the key: revised prose simply keeps canonical markup.
    # Old font sizes and fonts are deliberately absent from the shared profile.
    for node in soup.find_all(['p', 'li']):
        if node.find_parent('table') or (node.name == 'li' and node.find('p')):
            continue
        record = profile.get('blocks', {}).get(normalized(node.get_text()))
        if record:
            for name in record.get('classes', []):
                add_class(node, name)
            _apply_runs(node, record.get('runs', []), soup)
        text = node.get_text(strip=True)
        if text in ('D100 + 加值 - 减值', '.rd100+ 加值 - 减值'):
            add_class(node, 'reader-formula')
        if (path == '都市箴言/平衡参考/属性_技能参考.md'
                and text in ('传闻', '怪谈', '传说', '恶疾', '梦魇', '星辰')):
            add_class(node, 'reader-section-label')

    tables = soup.find_all('table')
    by_id = {}
    for table in tables:
        table_id = table.get('data-table-id')
        if table_id:
            if table_id in by_id:
                raise ValueError(f'{path}: duplicate canonical table ID {table_id}')
            by_id[table_id] = table
    for table_id, record in profile.get('tables', {}).items():
        table = by_id.get(table_id)
        if table is None or _shape_hash(table) != record['shape_sha256']:
            raise ValueError(f'{path}: semantic presentation drift in table {table_id}; '
                             'review assets/site/semantic-presentation.json against current source')
        rows = _rows(table)
        for cell_record in record['cells']:
            cell = rows[cell_record['row']].find_all(['td', 'th'], recursive=False)[cell_record['cell']]
            if normalized(cell.get_text()) != cell_record['text']:
                raise ValueError(f'{path}: semantic cell text changed in {table_id}')
            background = cell_record.get('background')
            if background:
                add_class(cell, 'reader-color-cell')
                cell['data-source-background'] = background
                cell['style'] = (cell.get('style', '').rstrip(';') + ';' if cell.get('style') else '') + (
                    f'--cell-bg:{background};--cell-ink:{ink_for(background)}')
            for name in cell_record.get('classes', []):
                add_class(cell, name)
            _apply_runs(cell, cell_record.get('runs', []), soup)

    for table in tables:
        add_class(table, 'pmtrpg-table')
        columns = _columns(table)
        table['data-reader-columns'] = str(columns)
        if columns > 6:
            add_class(table, 'reader-matrix-table')
        if table.find_parent('table'):
            add_class(table, 'reader-nested-table')
        else:
            width = columns * (62 if columns > 6 else 115)
            table['style'] = (table.get('style', '').rstrip(';') + ';' if table.get('style') else '') + (
                f'--table-min-width:{width}px')
            parent = table.parent
            if not (parent.name == 'div' and 'pmtrpg-table-scroll' in parent.get('class', [])):
                parent = soup.new_tag('div', attrs={'class': 'pmtrpg-table-scroll'})
                table.wrap(parent)
            parent['tabindex'] = '0'
            parent['role'] = 'region'
            preceding = parent.find_previous_sibling()
            caption = preceding.get_text(' ', strip=True) if preceding else ''
            parent['aria-label'] = (caption if 0 < len(caption) <= 24 else '规则表格') + '；宽表可横向滚动'
            if preceding and preceding.name == 'p' and 0 < len(caption) <= 24 and not re.search('[。！？：]', caption):
                add_class(preceding, 'reader-table-caption')
        for row in _rows(table):
            cells = row.find_all(['td', 'th'], recursive=False)
            for cell in cells:
                if len(cell.get_text(strip=True)) > 40:
                    add_class(cell, 'reader-prose-cell')
            if cells and all(c.get_text(strip=True) and not c.find('table') and
                             any(e.get_text(strip=True) == c.get_text(strip=True)
                                 for e in c.select('b,strong,.reader-weight')) for c in cells):
                add_class(row, 'reader-label-row')

    output = str(soup)
    after = BeautifulSoup(output, 'html.parser')
    if original_text != after.get_text() or before != content_signature(after):
        raise ValueError(f'{path}: site presentation changed rule content or table structure')
    return output


def extract_semantic_profile() -> dict:
    """Explicit maintenance helper; never called by website builds.

    Reference grids contain Word layout-only columns. Row-local cell ordinals
    identify the same actual cells without copying those obsolete column spans.
    Identical A1/B2/C3 examples are paired by audited source table order, then
    locked to distinct canonical IDs. Every coloured cell must match exactly.
    """
    import markdown

    reference_path = ROOT / 'assets/chm/presentation-v184.json'
    reference = json.loads(reference_path.read_text(encoding='utf8'))
    result = {'schema_version': 1, 'reference': 'assets/chm/presentation-v184.json',
              'reference_sha256': hashlib.sha256(reference_path.read_bytes()).hexdigest(),
              'mapping': 'Stable document path and canonical table ID; strict current table shape digest; '
                         'row-local cell ordinal and normalized text. Reference-only tables are not imported.',
              'documents': {}}
    for path, source_profile in reference['documents'].items():
        source = ROOT / 'docs' / path
        if not source.exists():
            continue
        soup = BeautifulSoup(markdown.markdown(source.read_text(encoding='utf8'),
                             extensions=['tables', 'md_in_html', 'sane_lists', 'toc']), 'html.parser')
        document = {'blocks': {}, 'tables': {}}
        for node in soup.find_all(['p', 'li']):
            if node.find_parent('table') or (node.name == 'li' and node.find('p')):
                continue
            key = normalized(node.get_text())
            record = source_profile.get('blocks', {}).get(key)
            if not record:
                continue
            classes = _classes(record.get('style', ''))
            if any(c in record.get('class', []) for c in ('MsoQuote', 'MsoIntenseQuote', 'af9')):
                classes.append('reader-quote')
            runs = _runs(record)
            if classes or runs:
                document['blocks'][key] = {'classes': classes, 'runs': runs}
        tables = soup.find_all('table')
        refs = source_profile.get('tables', [])
        # A historical table absent in canonical Markdown is never recreated.
        if len(tables) == len(refs):
            for table, ref in zip(tables, refs):
                table_id = table.get('data-table-id')
                if not table_id:
                    continue
                cells = []
                for ri, row in enumerate(_rows(table)):
                    actual = row.find_all(['td', 'th'], recursive=False)
                    expected = [c for c in ref.get('cells', []) if c['row'] == ri]
                    if len(actual) != len(expected):
                        if any(_background(c.get('style', '')) for c in expected):
                            raise ValueError(f'{path}: reference colour row does not match canonical cells')
                        continue
                    for ci, (cell, old) in enumerate(zip(actual, expected)):
                        color = _background(old.get('style', ''))
                        if normalized(cell.get_text()) != old['text']:
                            if color:
                                raise ValueError(f'{path}: coloured reference cell differs at {ri}/{ci}')
                            continue
                        classes = _classes(old.get('style', ''))
                        if declarations(old.get('style', '')).get('white-space') == 'nowrap':
                            classes.append('reader-nowrap')
                        # Canonical b/strong tags already carry bold semantics.
                        runs = [r for r in _runs(old) if r['classes'] != ['reader-weight']]
                        if color or classes or runs:
                            item = {'row': ri, 'cell': ci, 'text': old['text']}
                            if color:
                                item['background'] = color
                            if classes:
                                item['classes'] = classes
                            if runs:
                                item['runs'] = runs
                            cells.append(item)
                if cells:
                    document['tables'][table_id] = {'shape_sha256': _shape_hash(table), 'cells': cells}
        if document['blocks'] or document['tables']:
            result['documents'][path] = document
    result['semantic_color_cells'] = sum(bool(c.get('background'))
        for d in result['documents'].values() for t in d['tables'].values() for c in t['cells'])
    return result


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-profile', action='store_true',
                        help='Explicitly regenerate the reviewable source presentation manifest')
    args = parser.parse_args()
    if args.write_profile:
        profile = extract_semantic_profile()
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        print(json.dumps({'documents': len(profile['documents']),
                          'semantic_color_cells': profile['semantic_color_cells']}, ensure_ascii=False))
    else:
        parser.print_help()
