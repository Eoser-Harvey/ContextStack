# -*- coding: utf-8 -*-
import markdown

md_path = r"e:\ProjectGroup\AI\ContextStack\01-Projects\family-hub\company-setup\beijing-company-social-insurance-plan.md"
html_path = r"e:\ProjectGroup\AI\ContextStack\01-Projects\family-hub\company-setup\beijing-company-social-insurance-plan.html"

with open(md_path, "r", encoding="utf-8") as f:
    md_text = f.read()

body = markdown.markdown(md_text, extensions=["toc", "tables", "fenced_code", "nl2br"])

css = """
<style>
  body { font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif; max-width: 1100px; margin: 0 auto; padding: 32px 48px; color: #1a1a2e; line-height: 1.8; background: #fafafa; }
  h1 { font-size: 1.8em; color: #16213e; border-bottom: 3px solid #0f3460; padding-bottom: 10px; margin-top: 40px; }
  h2 { font-size: 1.45em; color: #0f3460; border-bottom: 1px solid #ccc; padding-bottom: 6px; margin-top: 36px; }
  h3 { font-size: 1.2em; color: #1a1a4e; margin-top: 28px; }
  h4 { font-size: 1.05em; color: #333; margin-top: 20px; }
  table { border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 0.92em; box-shadow: 0 2px 8px rgba(0,0,0,0.06); background: #fff; }
  th { background: #0f3460; color: #fff; padding: 10px 14px; text-align: left; font-weight: 600; }
  td { padding: 8px 14px; border-bottom: 1px solid #e0e0e0; }
  tr:nth-child(even) { background: #f5f6fa; }
  tr:hover { background: #e8eaf6; }
  code { background: #e8eaf6; padding: 2px 6px; border-radius: 4px; font-size: 0.88em; color: #c62828; font-family: "Cascadia Code", "Consolas", monospace; }
  pre { background: #f4f6fb; color: #333; padding: 16px 20px; border: 1px solid #e0e4f0; border-left: 4px solid #0f3460; border-radius: 6px; overflow-x: auto; font-size: 0.9em; line-height: 1.6; }
  pre code { background: none; color: #1a1a2e; padding: 0; font-family: "Cascadia Code", "Consolas", monospace; }
  blockquote { border-left: 4px solid #0f3460; margin: 16px 0; padding: 8px 20px; background: #e8eaf6; color: #333; }
  blockquote p { margin: 4px 0; }
  a { color: #1565c0; text-decoration: none; }
  a:hover { text-decoration: underline; }
  ul, ol { padding-left: 28px; }
  li { margin: 4px 0; }
  hr { border: none; border-top: 2px dashed #ccc; margin: 32px 0; }
  strong { color: #0f3460; }
</style>
"""

full = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>北京开公司为家人缴纳社保公积金 · 方案研究与待办</title>
  {css}
</head>
<body>
{body}
</body>
</html>"""

with open(html_path, "w", encoding="utf-8") as f:
    f.write(full)

print(f"done, {len(full)} chars")
