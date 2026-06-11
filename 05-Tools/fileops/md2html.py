"""
MD → 排版 HTML 转换器（纯内置库，零依赖）
用法: python md2html.py input.md
输出: input.html（浏览器打开后 Ctrl+P → 另存为PDF）
"""
import re, sys, os
from pathlib import Path

# Windows GBK 兼容
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

def md_to_html(md_text, title="文档"):
    """简易 Markdown → HTML 转换，针对表格/中文/打印优化"""
    lines = md_text.split('\n')
    html = []
    in_table = False
    in_code = False
    in_list = False

    def escape(s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def format_inline(text):
        # bold: **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # italic: *text*
        text = re.sub(r'\*([^*]+?)\*', r'<em>\1</em>', text)
        # inline code: `code`
        text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', text)
        return text

    def format_link(text):
        # [text](url)
        return re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<a href="\2">\1</a>', text)

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 空行 → 关闭表格/代码块
        if stripped == '':
            if in_table:
                html.append('</tbody></table>')
                in_table = False
            if in_list:
                html.append('</ul>')
                in_list = False
            html.append('')
            i += 1
            continue

        # 代码块
        if stripped.startswith('```'):
            if in_code:
                html.append('</code></pre>')
                in_code = False
            else:
                html.append('<pre><code>')
                in_code = True
            i += 1
            continue
        if in_code:
            html.append(escape(line))
            i += 1
            continue

        # 表格行
        if stripped.startswith('|') and stripped.endswith('|'):
            cells = [c.strip() for c in stripped[1:-1].split('|')]
            # 跳过纯分隔行（如 |------|------|）
            if all(re.match(r'^[-:]+$', c) for c in cells):
                i += 1
                continue
            if not in_table:
                html.append('<table><thead>')
                in_table = True
                html.append('<tr>' + ''.join(f'<th>{format_inline(escape(c))}</th>' for c in cells) + '</tr>')
                html.append('</thead><tbody>')
            else:
                html.append('<tr>' + ''.join(f'<td>{format_link(format_inline(escape(c)))}</td>' for c in cells) + '</tr>')
            i += 1
            continue

        # 标题
        for level in range(4, 0, -1):
            prefix = '#' * level + ' '
            if stripped.startswith(prefix):
                text = format_inline(escape(stripped[len(prefix):]))
                id_slug = re.sub(r'[^\w\u4e00-\u9fff]', '-', stripped[len(prefix):]).strip('-').lower()
                html.append(f'<h{level} id="{id_slug}">{text}</h{level}>')
                break
        else:
            # 引用
            if stripped.startswith('> '):
                text = format_link(format_inline(escape(stripped[2:])))
                # 粗体在引用块内的处理
                text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
                html.append(f'<blockquote><p>{text}</p></blockquote>')
            elif stripped.startswith('>'):
                text = format_link(format_inline(escape(stripped[1:])))
                text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
                html.append(f'<blockquote><p>{text}</p></blockquote>')
            # 无序列表
            elif re.match(r'^[-*]\s', stripped):
                if not in_list:
                    html.append('<ul>')
                    in_list = True
                text = format_link(format_inline(escape(re.sub(r'^[-*]\s', '', stripped))))
                html.append(f'<li>{text}</li>')
            # 水平线
            elif stripped == '---':
                html.append('<hr>')
            # 普通段落
            else:
                if in_list:
                    html.append('</ul>')
                    in_list = False
                text = format_link(format_inline(escape(stripped)))
                html.append(f'<p>{text}</p>')
        i += 1

    # 收尾
    if in_table:
        html.append('</tbody></table>')
    if in_list:
        html.append('</ul>')

    return '\n'.join(html)


CSS = """
<style>
  @page { margin: 1.5cm 2cm; size: A4; }
  * { box-sizing: border-box; }
  body {
    font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans SC", sans-serif;
    font-size: 14px; line-height: 1.8; color: #333;
    max-width: 800px; margin: 0 auto; padding: 20px;
  }
  h1 { font-size: 26px; border-bottom: 2px solid #1a73e8; padding-bottom: 8px; margin-top: 0; color: #1a73e8; }
  h2 { font-size: 20px; margin-top: 30px; color: #222; border-left: 4px solid #1a73e8; padding-left: 12px; }
  h3 { font-size: 17px; margin-top: 24px; color: #444; }
  h4 { font-size: 15px; margin-top: 20px; color: #555; }
  table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; }
  th { background: #1a73e8; color: white; padding: 8px 10px; text-align: left; font-weight: 600; }
  td { padding: 6px 10px; border-bottom: 1px solid #e0e0e0; }
  tr:nth-child(even) td { background: #f8f9fa; }
  blockquote {
    margin: 12px 0; padding: 10px 16px;
    border-left: 4px solid #1a73e8;
    background: #f0f4ff; color: #444;
  }
  blockquote p { margin: 4px 0; }
  code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 13px; }
  pre { background: #f5f5f5; padding: 12px; border-radius: 6px; overflow-x: auto; }
  pre code { background: none; padding: 0; }
  hr { border: none; border-top: 1px solid #ddd; margin: 30px 0; }
  ul { padding-left: 24px; }
  li { margin: 4px 0; }
  strong { color: #d93025; }
  a { color: #1a73e8; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .footer { text-align: center; color: #999; font-size: 12px; margin-top: 40px; border-top: 1px solid #eee; padding-top: 16px; }

  /* 打印优化 */
  @media print {
    body { max-width: 100%; font-size: 12px; }
    h1 { font-size: 22px; }
    h2 { font-size: 17px; }
    table { page-break-inside: avoid; }
    h1, h2, h3, h4 { page-break-after: avoid; }
    a { color: #333; }
    .footer { position: fixed; bottom: 0; width: 100%; }
  }
</style>
"""

if __name__ == '__main__':
    md_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(input("MD文件路径: "))
    if not md_path.exists():
        print(f"文件不存在: {md_path}")
        sys.exit(1)

    md_text = md_path.read_text(encoding='utf-8')
    body = md_to_html(md_text, md_path.stem)

    html_output = f"""<!DOCTYPE html>
<!-- AUTO-GENERATED from {md_path.name} | DO NOT EDIT THIS FILE -->
<!-- 修改 .md 源文件后运行: python 05-Tools/fileops/md2html.py 此文件路径 -->
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{md_path.stem}</title>
{CSS}
</head>
<body>
{body}
<div class="footer">
  <p>生成自: {md_path.name} | 转换时间: 2026-06-11 | 仅供内部参考</p>
</div>
</body>
</html>"""

    out_path = md_path.with_suffix('.html')
    out_path.write_text(html_output, encoding='utf-8')
    print(f"✅ HTML 已生成: {out_path}")
    print(f"   浏览器打开此文件 → Ctrl+P → 另存为PDF")

    # 自动打开浏览器
    os.startfile(str(out_path))
