"""Adapt legacy CHM presentation for the web reader without rewriting rule content."""
from __future__ import annotations

import hashlib
import re
from bs4 import BeautifulSoup


def declarations(value: str) -> dict[str, str]:
    return {key.strip().lower(): val.strip() for part in value.split(';')
            if ':' in part for key, val in [part.split(':', 1)]}


def add_class(tag, name):
    tag['class'] = list(dict.fromkeys([*tag.get('class', []), name]))


def ink_for(background: str) -> str:
    rgb = [int(background[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb]
    luminance = sum(c * w for c, w in zip(linear, (.2126, .7152, .0722)))
    return '#151715' if luminance > .18 else '#ffffff'


def content_signature(topic) -> dict:
    """Independent of CSS, including nested cell geometry and inline semantics."""
    def text(tag):
        return re.sub(r'\s+', ' ', tag.get_text()).strip()
    return {
        'text': text(topic),
        'ids': [e['id'] for e in topic.find_all(id=True)],
        'links': [(e.get('href'), text(e)) for e in topic.find_all('a')],
        'images': [dict(e.attrs) for e in topic.find_all('img')],
        'headings': [(e.name, e.get('id'), text(e)) for e in topic.find_all(re.compile('^h[1-6]$'))],
        'emphasis': [(e.name, text(e)) for e in topic.find_all(['strong', 'b', 'em', 'i', 'sup', 'sub'])],
        'tables': [
            {'id': t.get('data-table-id'),
             'parent': t.find_parent('table').get('data-table-id') if t.find_parent('table') else None,
             'rows': [[(c.name, c.get('rowspan', '1'), c.get('colspan', '1'), text(c))
                       for c in row.find_all(['td', 'th'], recursive=False)]
                      for row in t.find_all('tr') if row.find_parent('table') is t]}
            for t in topic.find_all('table')],
    }


def adapt_topic(source: str, page_id: int, theme_revision: str = '') -> tuple[str, dict]:
    soup = BeautifulSoup(source, 'html.parser')
    topic = soup.select_one('.pmtrpg-topic')
    before = content_signature(topic)
    stats = {'legacy_inline_styles_removed': 0, 'semantic_color_cells': 0,
             'paragraphs_normalized': len(topic.find_all('p'))}

    # Only web-reader copies are transformed. CHM and Markdown remain the reference.
    for tag in [topic, *topic.find_all(True)]:
        props = declarations(tag.get('style', ''))
        if 'style' in tag.attrs:
            stats['legacy_inline_styles_removed'] += 1
            del tag['style']
        for attr in ('bgcolor', 'color', 'face', 'size', 'align', 'valign', 'nowrap'):
            tag.attrs.pop(attr, None)
        if tag.name != 'img':
            for attr in ('width', 'height', 'border', 'cellspacing', 'cellpadding'):
                tag.attrs.pop(attr, None)
        if props.get('font-weight') in ('bold', '700', '800', '900'):
            add_class(tag, 'reader-weight')
        elif props.get('font-weight') in ('normal', '400'):
            add_class(tag, 'reader-regular')
        if props.get('font-style') == 'italic':
            add_class(tag, 'reader-italic')
        elif props.get('font-style') == 'normal':
            add_class(tag, 'reader-upright')
        if props.get('text-decoration') == 'underline':
            add_class(tag, 'reader-underline')
        color = props.get('color', '').lower()
        if color in ('red', '#ff0000'):
            add_class(tag, 'reader-warning')
        elif color in ('gray', 'grey', '#808080', '#404040'):
            add_class(tag, 'reader-note')
        elif color == '#ed7d31':
            add_class(tag, 'reader-accent')
        if tag.name in ('td', 'th'):
            if len(tag.get_text(strip=True)) > 40:
                add_class(tag, 'reader-prose-cell')
            background = props.get('background', props.get('background-color', '')).lower()
            normalized = {'red': '#ff0000', 'yellow': '#ffff00'}.get(background, background)
            if re.fullmatch(r'#[0-9a-f]{6}', normalized) and normalized != '#2e2217':
                tag['data-source-background'] = background
                tag['style'] = f'--cell-bg:{normalized};--cell-ink:{ink_for(normalized)}'
                add_class(tag, 'reader-color-cell')
                stats['semantic_color_cells'] += 1
            if props.get('white-space') == 'nowrap':
                add_class(tag, 'reader-nowrap')
        if tag.name == 'p':
            classes = tag.get('class', [])
            if any(c in classes for c in ('MsoQuote', 'MsoIntenseQuote', 'af9')):
                add_class(tag, 'reader-quote')
            text = tag.get_text(strip=True)
            if text in ('D100 + 加值 - 减值', '.rd100+ 加值 - 减值'):
                add_class(tag, 'reader-formula')
            # These are explicit section labels in the original reference article.
            if page_id == 161 and text in ('传闻', '怪谈', '传说', '恶疾', '梦魇', '星辰'):
                add_class(tag, 'reader-section-label')

    for table in topic.find_all('table'):
        rows = [r for r in table.find_all('tr') if r.find_parent('table') is table]
        columns = max((sum(int(c.get('colspan', 1)) for c in r.find_all(['td', 'th'], recursive=False))
                       for r in rows), default=1)
        table['data-reader-columns'] = str(columns)
        if columns > 6:
            add_class(table, 'reader-matrix-table')
        if table.find_parent('table'):
            add_class(table, 'reader-nested-table')
        else:
            min_width = max(0, columns * (62 if columns > 6 else 115))
            table['style'] = f'--table-min-width:{min_width}px'
        for row in rows:
            cells = row.find_all(['td', 'th'], recursive=False)
            # Retain visibly emphasized label rows without inventing table semantics.
            if cells and all(c.get_text(strip=True) and not c.find('table') and
                             any(e.get_text(strip=True) == c.get_text(strip=True) for e in c.select('b,strong,.reader-weight'))
                             for c in cells):
                add_class(row, 'reader-label-row')

    for wrapper in topic.select('.pmtrpg-table-scroll'):
        wrapper['tabindex'] = '0'
        wrapper['role'] = 'region'
        preceding = wrapper.find_previous_sibling()
        caption = preceding.get_text(' ', strip=True) if preceding else ''
        wrapper['aria-label'] = (caption if 0 < len(caption) <= 24 else '规则表格') + '；宽表可横向滚动'
        if preceding and preceding.name == 'p' and 0 < len(caption) <= 24 and not re.search('[。！？：]', caption):
            add_class(preceding, 'reader-table-caption')

    for style in soup.find_all('style'):
        style.decompose()
    for link in soup.find_all('link', rel='stylesheet'):
        link.decompose()
    soup.html['lang'] = 'zh-CN'
    soup.body.attrs = {'class': 'reader-content'}
    viewport = soup.new_tag('meta', attrs={'name': 'viewport', 'content': 'width=device-width, initial-scale=1'})
    soup.head.append(viewport)
    stylesheet = '../../reader-content.css' + (f'?v={theme_revision}' if theme_revision else '')
    soup.head.append(soup.new_tag('link', rel='stylesheet', href=stylesheet))
    output = str(soup)
    after = content_signature(BeautifulSoup(output, 'html.parser').select_one('.pmtrpg-topic'))
    assert before == after, f'Rule content changed in page {page_id}'
    stats['content_signature_sha256'] = hashlib.sha256(repr(before).encode('utf8')).hexdigest()
    stats['content_unchanged'] = True
    return output, stats
