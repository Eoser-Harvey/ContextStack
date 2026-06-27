#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将薛燕健康深度分析报告 .md 转换为 HTML 格式
用法：python convert_to_html.py
输出：薛燕-健康深度分析-2026.html
"""

import re
import sys

def md_to_html(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    html = []
    in_code_block = False
    in_table = False
    in_blockquote = False
    table_rows = []

    def flush_table():
        nonlocal table_rows
        if not table_rows:
            return
        result = ["<table>"]
        for i, row in enumerate(table_rows):
            cells = [c.strip() for c in row.split("|") if c.strip() != ""]
            tag = "th" if i == 0 else "td"
            result.append("<tr>")
            for cell in cells:
                result.append(f"<{tag}>{cell}</{tag}>")
            result.append("</tr>")
        result.append("</table>")
        table_rows.clear()
        return "\n".join(result)

    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")

        # Code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if in_code_block:
                html.append("<pre><code>")
            else:
                html.append("</code></pre>")
            i += 1
            continue

        if in_code_block:
            html.append(line)
            i += 1
            continue

        # Blockquote
        stripped = line.strip()
        if stripped.startswith("> "):
            html.append(f"<blockquote>{stripped[2:]}</blockquote>")
            i += 1
            continue

        # Horizontal rule
        if stripped == "---":
            html.append("<hr>")
            i += 1
            continue

        # Emoji-only lines
        if stripped in ("✅", "⬜", "❌", "⚠️", "🟡", "🟢", "🔴"):
            html.append(f"<p>{stripped}</p>")
            i += 1
            continue

        # Tables
        is_table_line = stripped.startswith("|") and stripped.endswith("|")
        is_separator = bool(re.match(r"^\|[\s\-:|\+\.]+\|$", stripped))

        if is_table_line and not is_separator:
            in_table = True
            table_rows.append(stripped)
            i += 1
            continue
        elif is_separator and in_table:
            i += 1
            continue
        else:
            if in_table:
                html.append(flush_table())
                in_table = False

        # Headers
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped.lstrip("#").strip()
            html.append(f"<h{level}>{title}</h{level}>")
            i += 1
            continue

        # Bold + inline code
        line_html = stripped
        line_html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line_html)
        line_html = re.sub(r"`([^`]+)`", r"<code>\1</code>", line_html)
        # Links
        line_html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', line_html)

        # Empty line
        if stripped == "":
            html.append("")
        else:
            html.append(f"<p>{line_html}</p>")

        i += 1

    # Flush trailing table
    if in_table:
        html.append(flush_table())

    body = "\n".join(html)

    css = """
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            color: #333;
            line-height: 1.8;
            background: #fafafa;
        }
        h1 { color: #1a1a1a; border-bottom: 3px solid #4a90d9; padding-bottom: 12px; font-size: 1.8em; }
        h2 { color: #2c3e50; border-bottom: 2px solid #ddd; padding-bottom: 8px; margin-top: 32px; font-size: 1.4em; }
        h3 { color: #34495e; font-size: 1.15em; margin-top: 24px; }
        h4 { color: #555; }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
            background: #fff;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px 14px;
            text-align: left;
        }
        th {
            background: #4a90d9;
            color: #fff;
            font-weight: 600;
        }
        tr:nth-child(even) { background: #f7f9fc; }
        blockquote {
            border-left: 4px solid #4a90d9;
            margin: 12px 0;
            padding: 8px 16px;
            background: #eef4fb;
            color: #444;
        }
        hr { border: none; border-top: 2px solid #eee; margin: 24px 0; }
        code {
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }
        pre {
            background: #2d3436;
            color: #dfe6e9;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 0.9em;
        }
        pre code { background: transparent; padding: 0; }
        strong { color: #2c3e50; }
        a { color: #4a90d9; }
    </style>
    """

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>薛燕健康深度分析报告</title>
{css}
</head>
<body>
{body}
</body>
</html>"""


if __name__ == "__main__":
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(script_dir, "薛燕-健康深度分析-2026.md")
    html = md_to_html(target)
    outfile = target.replace(".md", ".html")
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 已生成：{outfile}  ({len(html)} 字符)")