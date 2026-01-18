"""
将 docs/**/*.md 中残留的 HTML 表格 <table>...</table> 逐个转换为 GitHub 可渲染的 Markdown 管道表。

特点：
- 仅替换明确的 <table>...</table> 块（逐表格重建），不做全局“瞎清理”
- 适配 WinCHM/Pandoc 产生的简化 HTML（td/th/strong/br 等）
- 单元格内换行会折叠为 <br>，避免破坏管道表结构
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List
from xml.etree import ElementTree as ET


TABLE_BLOCK_RE = re.compile(r"<table>\s*[\s\S]*?</table>", flags=re.I)


def _xml_sanitize(html: str) -> str:
    html = html.replace("&nbsp;", " ")
    html = html.replace("<br>", "<br/>").replace("<br />", "<br/>")
    html = re.sub(r"</?(?:tbody|thead|tfoot)\b[^>]*>", "", html, flags=re.I)
    return html


def _strip_surrounding_whitespace(s: str) -> str:
    s = s.strip()
    s = re.sub(r"[ \t]+", " ", s)
    return s


def _escape_pipes(s: str) -> str:
    return s.replace("|", r"\|")


def _iter_cell_parts(node: ET.Element) -> Iterable[str]:
    if node.text:
        yield node.text
    for child in list(node):
        tag = child.tag.lower()
        if tag == "br":
            yield "\n"
        elif tag == "strong":
            inner = "".join(_iter_cell_parts(child))
            if inner.strip():
                yield f"**{inner.strip()}**"
        else:
            yield "".join(_iter_cell_parts(child))
        if child.tail:
            yield child.tail


def _cell_text(cell: ET.Element) -> str:
    raw = "".join(_iter_cell_parts(cell))
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    parts = [p.strip() for p in raw.split("\n")]
    parts = [p for p in parts if p != ""]
    if not parts:
        return ""
    text = "<br>".join(parts)
    text = _strip_surrounding_whitespace(text)
    text = _escape_pipes(text)
    return text


def table_html_to_pipe(table_html: str) -> str:
    html = _xml_sanitize(table_html)
    wrapped = f"<root>{html}</root>"
    root = ET.fromstring(wrapped)
    table = root.find(".//table")
    if table is None:
        return table_html

    rows: List[List[str]] = []
    for tr in table.findall(".//tr"):
        cells: List[str] = []
        for cell in list(tr):
            tag = cell.tag.lower()
            if tag not in {"td", "th"}:
                continue
            cells.append(_cell_text(cell))
        if cells:
            rows.append(cells)

    if not rows:
        return ""

    col_count = max(len(r) for r in rows)
    rows = [r + [""] * (col_count - len(r)) for r in rows]

    header = rows[0]
    body = rows[1:] if len(rows) > 1 else []
    if all(c == "" for c in header) and body:
        header = body[0]
        body = body[1:]

    sep = ["---"] * col_count

    def fmt_row(r: List[str]) -> str:
        return "| " + " | ".join(c if c != "" else " " for c in r) + " |"

    out_lines = [fmt_row(header), "| " + " | ".join(sep) + " |"]
    for r in body:
        out_lines.append(fmt_row(r))
    return "\n".join(out_lines) + "\n"


@dataclass
class FixResult:
    file: Path
    tables_found: int
    tables_converted: int


def fix_file(path: Path) -> FixResult:
    text = path.read_text("utf-8")
    blocks = list(TABLE_BLOCK_RE.finditer(text))
    if not blocks:
        return FixResult(path, 0, 0)

    new_text = text
    converted = 0
    for m in reversed(blocks):
        table_html = m.group(0)
        try:
            pipe = table_html_to_pipe(table_html)
        except Exception:
            pipe = table_html
        new_text = new_text[: m.start()] + pipe + new_text[m.end() :]
        if pipe != table_html:
            converted += 1

    new_text = new_text.replace("\r\n", "\n")
    new_text = re.sub(r"\n{4,}", "\n\n\n", new_text).strip() + "\n"

    if new_text != text:
        path.write_text(new_text, "utf-8")

    return FixResult(path, len(blocks), converted)


def iter_md_files(docs_dir: Path) -> List[Path]:
    return sorted([p for p in docs_dir.rglob("*.md") if p.is_file()], key=lambda p: str(p))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="docs", help="Docs root directory (default: docs)")
    ap.add_argument("--only", default="", help="Only process files whose path contains this substring")
    args = ap.parse_args()

    docs_dir = Path(args.docs)
    if not docs_dir.exists():
        raise SystemExit(f"Docs dir not found: {docs_dir}")

    files = iter_md_files(docs_dir)
    if args.only:
        files = [p for p in files if args.only in str(p)]

    results: List[FixResult] = []
    for p in files:
        r = fix_file(p)
        if r.tables_found:
            results.append(r)

    total_tables = sum(r.tables_found for r in results)
    total_converted = sum(r.tables_converted for r in results)
    print(f"files_with_tables: {len(results)}")
    print(f"tables_found: {total_tables}")
    print(f"tables_converted: {total_converted}")


if __name__ == "__main__":
    main()

"""
修复丢失格式的表格
专门处理某些没有正确转换为Markdown表格的文本表格
"""
import re
from pathlib import Path


def fix_table_pattern(md_content, pattern_name, header_pattern, data_pattern):
    """修复特定模式的表格"""
    
    lines = md_content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 跳过空行和已有表格行
        if not stripped:
            fixed_lines.append(line)
            i += 1
            continue
        
        if '|' in stripped:
            fixed_lines.append(line)
            i += 1
            continue
        
        # 检测表格模式
        header_match = re.match(header_pattern, stripped)
        if header_match:
            # 找到表头，查找数据行
            table_rows = [stripped]
            look_ahead = 1
            
            while i + look_ahead < len(lines):
                next_line = lines[i + look_ahead].strip()
                if not next_line:
                    break
                if '|' in next_line:
                    break
                
                data_match = re.match(data_pattern, next_line)
                if data_match:
                    table_rows.append(next_line)
                    look_ahead += 1
                elif next_line.startswith('**等级**') or next_line.startswith('**经历点**'):
                    # 可能是下一段表格的开始
                    table_rows.append(next_line)
                    look_ahead += 1
                else:
                    break
            
            if len(table_rows) >= 2:
                # 转换为表格格式
                all_parts = []
                for row in table_rows:
                    # 提取粗体文本和数字
                    parts = []
                    # 先提取所有**文本**
                    bold_parts = re.findall(r'\*\*([^\*]+)\*\*', row)
                    parts.extend(bold_parts)
                    
                    # 提取数字（不在粗体内的）
                    numbers = re.findall(r'(?<!\*)\b(\d+)\b(?!\*)', row)
                    parts.extend(numbers)
                    
                    if len(parts) >= 2:
                        all_parts.append('|' + '|'.join(parts) + '|')
                
                # 添加表格
                if all_parts:
                    # 添加分隔行
                    col_count = all_parts[0].count('|') - 1
                    separator = '|' + '|'.join(['---'] * col_count) + '|'
                    fixed_lines.extend(all_parts[:1])  # 第一行
                    fixed_lines.append(separator)  # 分隔行
                    fixed_lines.extend(all_parts[1:])  # 剩余行
                    i += len(table_rows)
                    continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)


def fix_level_table(md_content):
    """修复等级表格（**等级** **经历点** 1 1 2 ... 格式）"""
    lines = md_content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 检测 **等级** 行
        if stripped == '**等级**' and i + 1 < len(lines):
            # 下一行应该是 **经历点** 1 1 2 ...
            next_line = lines[i + 1].strip()
            if next_line.startswith('**经历点**'):
                # 提取数据
                data_match = re.match(r'\*\*经历点\*\*\s+(.+)', next_line)
                if data_match:
                    numbers = data_match.group(1).split()
                    if len(numbers) >= 2:
                        # 构建表格
                        # 表头：等级 | 1 | 2 | 3 | ...
                        header_numbers = list(range(1, len(numbers) + 1))
                        header = '|**等级**|' + '|'.join([f'**{n}**' for n in header_numbers]) + '|'
                        separator = '|---' + '|' * len(numbers) + '|'
                        data_row = '|**经历点**|' + '|'.join(numbers) + '|'
                        
                        fixed_lines.append(header)
                        fixed_lines.append(separator)
                        fixed_lines.append(data_row)
                        i += 2
                        continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)


def fix_specific_tables(md_content):
    """修复特定文件中的表格"""
    
    # 修复 "**等级**" 单独一行 + "**经历点** 1 1 2 ..." 的格式
    lines = md_content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 检测 **等级** 单独一行
        if stripped == '**等级**':
            # 查看下一行是否是 **经历点** 数据
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith('**经历点**'):
                    # 提取数字
                    numbers = re.findall(r'\d+', next_line)
                    if len(numbers) >= 2:
                        # 构建表格
                        # 生成表头：等级 | 1 | 2 | 3 | ...
                        max_cols = len(numbers)
                        header_cols = [f'**{n}**' for n in range(1, max_cols + 1)]
                        header = '|**等级**|' + '|'.join(header_cols) + '|'
                        separator = '|---' + ('|' * max_cols) + '|'
                        # 修正separator格式
                        separator = '|---' + '|'.join(['---'] * max_cols) + '|'
                        data_row = '|**经历点**|' + '|'.join(numbers) + '|'
                        
                        fixed_lines.append(header)
                        fixed_lines.append(separator)
                        fixed_lines.append(data_row)
                        i += 2
                        
                        # 检查是否有第二段表格（11-20级）
                        if i < len(lines) and lines[i].strip() == '**等级**' and i + 1 < len(lines):
                            next_next = lines[i + 1].strip()
                            if next_next.startswith('**经历点**'):
                                next_numbers = re.findall(r'\d+', next_next)
                                if len(next_numbers) >= 2:
                                    # 继续使用相同的表格格式（11-20级）
                                    header_cols2 = [f'**{n}**' for n in range(11, 11 + len(next_numbers))]
                                    header2 = '|**等级**|' + '|'.join(header_cols2) + '|'
                                    separator2 = '|---' + '|'.join(['---'] * len(next_numbers)) + '|'
                                    data_row2 = '|**经历点**|' + '|'.join(next_numbers) + '|'
                                    
                                    fixed_lines.append('')  # 空行分隔
                                    fixed_lines.append(header2)
                                    fixed_lines.append(separator2)
                                    fixed_lines.append(data_row2)
                                    i += 2
                        continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)


def fix_combat_balance_table2(md_content):
    """修复战技平衡的第二个表格（期望 攻击 招架...）"""
    lines = md_content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 检测第二个表格的开头（包含"期望"的行）
        if '**期望**' in stripped and '**攻击**' in stripped:
            # 收集表格行
            table_rows = []
            look_ahead = 0
            
            while i + look_ahead < len(lines):
                check_line = lines[i + look_ahead].strip()
                if not check_line or '|' in check_line:
                    break
                
                # 检查是否是表格行（包含阶位名称和数字）
                if (re.search(r'\*\*(传闻|怪谈|传说|恶疾|梦魇|星辰|杂质)\*\*', check_line) or
                    (check_line.startswith('**期望**') and check_line.count('**') >= 4)):
                    table_rows.append(check_line)
                    look_ahead += 1
                elif len(table_rows) > 0:
                    # 如果已经有表格行但当前行不是，停止
                    break
                else:
                    break
            
            if len(table_rows) >= 2:
                # 转换为表格格式
                for idx, row in enumerate(table_rows):
                    # 提取**粗体**和数字
                    parts = []
                    # 提取所有**文本**
                    bold_matches = re.findall(r'\*\*([^\*]+)\*\*', row)
                    parts.extend(bold_matches)
                    
                    # 提取数字和小数（如6.5, 12.5等）
                    numbers = re.findall(r'\d+\.?\d*', row)
                    # 过滤掉已经在粗体中的数字
                    text_without_bold = re.sub(r'\*\*[^\*]+\*\*', '', row)
                    numbers_in_text = re.findall(r'\d+\.?\d*', text_without_bold)
                    parts.extend(numbers_in_text)
                    
                    # 提取特殊文本（如"+1光", "x50%", "升半阶"等）
                    special_texts = re.findall(r'[\+\-]?\d+光|x\d+%|升[半\d]+阶', row)
                    parts.extend(special_texts)
                    
                    # 过滤空字符串
                    parts = [p for p in parts if p]
                    
                    if len(parts) >= 2:
                        table_line = '|' + '|'.join(parts) + '|'
                        fixed_lines.append(table_line)
                        
                        # 在第一行后添加分隔行
                        if idx == 0:
                            col_count = len(parts)
                            separator = '|' + '|'.join(['---'] * col_count) + '|'
                            fixed_lines.append(separator)
                
                i += len(table_rows)
                continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)


def main():
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"
    
    print("=" * 70)
    print("表格格式修复工具")
    print("=" * 70)
    print()
    
    # 需要修复的文件
    files_to_fix = [
        "核心规则/基本规则/等级.md",
        "创作指南/战技平衡.md",
        "核心规则/速查图表/经历与晋升一览表.md"
    ]
    
    fixed_count = 0
    
    for file_rel_path in files_to_fix:
        md_file = docs_dir / file_rel_path
        if not md_file.exists():
            print(f"[跳过] {file_rel_path} (不存在)")
            continue
        
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore')
            original = content
            
            # 修复等级表格
            if '等级.md' in file_rel_path or '经历与晋升一览表.md' in file_rel_path:
                content = fix_specific_tables(content)
            
            # 修复战技平衡第二个表格
            if '战技平衡.md' in file_rel_path:
                content = fix_combat_balance_table2(content)
            
            if content != original:
                md_file.write_text(content, encoding='utf-8')
                fixed_count += 1
                print(f"[OK] {file_rel_path}")
            else:
                print(f"[跳过] {file_rel_path} (无需修复)")
                
        except Exception as e:
            print(f"[失败] {file_rel_path}: {e}")
    
    print()
    print("=" * 70)
    print(f"修复完成! 处理了 {fixed_count} 个文件")
    print("=" * 70)


if __name__ == "__main__":
    main()
