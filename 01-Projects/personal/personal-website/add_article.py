"""
add_article.py — 从微信公众号文章HTML/MD添加文章到个人网站

使用方法:
  python add_article.py <input_file> <slug> [--title "自定义标题"] [--date "2026-07-12"]

示例:
  python add_article.py "D:\\Downloads\\我的投资复盘.html" "investment-review-2026-07"
  python add_article.py article.md "embedded-ai-week1" --title "嵌入式AI学习Week1" --date "2026-07-12"

功能:
  1. 从HTML文件提取正文（支持微信公众号/浏览器保存的HTML）
  2. 从Markdown文件转换（支持标准MD语法）
  3. 使用template.html生成文章页面
  4. 自动更新index.html的"最新文章"区块
"""

import os
import re
import sys
import shutil
import argparse
from datetime import datetime
from html.parser import HTMLParser


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, 'articles', 'template.html')
INDEX_PATH = os.path.join(BASE_DIR, 'index.html')


# ─── HTML正文提取器 ───
class WeChatArticleExtractor(HTMLParser):
    """从微信公众号文章HTML中提取标题和正文"""

    def __init__(self):
        super().__init__()
        self.in_content = False
        self.in_title = False
        self.depth = 0
        self.title = ''
        self.content_parts = []
        self.current_tag = ''
        self.current_attrs = {}

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get('class', '')

        if 'rich_media_title' in cls:
            self.in_title = True
        elif 'rich_media_content' in cls:
            self.in_content = True
            self.depth = 1
        elif self.in_content:
            self.depth += 1
            self.current_tag = tag
            self.current_attrs = attrs_dict

            if tag in ('h1', 'h2', 'h3'):
                self.content_parts.append(f'<{tag}>')
            elif tag == 'p':
                self.content_parts.append('<p>')
            elif tag == 'blockquote':
                self.content_parts.append('<blockquote>')
            elif tag == 'strong' or tag == 'b':
                self.content_parts.append('<strong>')
            elif tag == 'br':
                self.content_parts.append('<br>')
            elif tag == 'img':
                src = attrs_dict.get('data-src', attrs_dict.get('src', ''))
                if src:
                    self.content_parts.append(f'<img src="{src}" alt="">')
            elif tag == 'a':
                href = attrs_dict.get('href', '')
                self.content_parts.append(f'<a href="{href}">')

    def handle_endtag(self, tag):
        if self.in_title and tag in ('h1', 'h2', 'div'):
            self.in_title = False

        if self.in_content:
            self.depth -= 1
            if self.depth <= 0:
                self.in_content = False
                return

            if tag in ('h1', 'h2', 'h3', 'p', 'blockquote'):
                self.content_parts.append(f'</{tag}>')
            elif tag in ('strong', 'b'):
                self.content_parts.append('</strong>')
            elif tag == 'a':
                self.content_parts.append('</a>')

    def handle_data(self, data):
        if self.in_title:
            self.title += data.strip()
        elif self.in_content:
            text = data.strip()
            if text:
                self.content_parts.append(text)


def extract_from_html(html_content):
    """从HTML文件提取标题和正文"""
    extractor = WeChatArticleExtractor()
    extractor.feed(html_content)

    title = extractor.title or '无标题文章'
    content = ''.join(extractor.content_parts).strip()

    if not content:
        content = '<p>（正文提取失败，请手动粘贴内容）</p>'

    return title, content


def markdown_to_html(md_content):
    """简单的Markdown转HTML"""
    lines = md_content.split('\n')
    html_parts = []
    in_list = False
    in_code = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('```'):
            if in_code:
                html_parts.append('</code></pre>')
                in_code = False
            else:
                html_parts.append('<pre><code>')
                in_code = True
            continue

        if in_code:
            html_parts.append(stripped)
            continue

        if stripped.startswith('### '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h3>{stripped[4:]}</h3>')
        elif stripped.startswith('## '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h2>{stripped[3:]}</h2>')
        elif stripped.startswith('# '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h2>{stripped[2:]}</h2>')
        elif stripped.startswith('> '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<blockquote>{stripped[2:]}</blockquote>')
        elif stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            html_parts.append(f'<li>{stripped[2:]}</li>')
        elif stripped:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            # 处理粗体和行内代码
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
            text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
            html_parts.append(f'<p>{text}</p>')

    if in_list:
        html_parts.append('</ul>')
    if in_code:
        html_parts.append('</code></pre>')

    return '\n'.join(html_parts)


def extract_from_md(md_content):
    """从Markdown提取标题和正文"""
    title_match = re.match(r'^#\s+(.+)', md_content)
    title = title_match.group(1) if title_match else '无标题文章'
    content = markdown_to_html(md_content)
    return title, content


def generate_article_page(title, date, content, slug):
    """使用模板生成文章页面"""
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template = f.read()

    desc = re.sub(r'<[^>]+>', '', content)[:150].strip()

    page = template
    page = page.replace('<!-- ARTICLE_TITLE -->',
                        f'<meta name="description" content="{desc}">')
    page = page.replace('<!-- ARTICLE_DATE -->',
                        f'<meta property="article:published_time" content="{date}">')
    page = page.replace('<!-- ARTICLE_DESCRIPTION -->',
                        f'<meta property="og:title" content="{title} · Harvey">')
    page = page.replace('<!-- ARTICLE_TITLE_TEXT -->', title)
    page = page.replace('<!-- ARTICLE_DATE_TEXT -->', date)
    page = page.replace('<!-- ARTICLE_CONTENT -->', content)

    output_path = os.path.join(BASE_DIR, 'articles', f'{slug}.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(page)

    return output_path


def update_index(slug, title, date):
    """更新index.html的"最新文章"区块"""
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        index = f.read()

    article_link = f'        <a href="articles/{slug}.html" class="article-link">\n          <span class="article-date">{date}</span>\n          <span class="article-title">{title}</span>\n        </a>'

    # 查找"最新文章"区块的插入位置
    pattern = r'(<div class="articles-list">)([\s\S]*?)(</div>)'
    match = re.search(pattern, index)

    if match:
        # 在列表开头插入新文章
        existing = match.group(2)
        new_content = match.group(1) + '\n' + article_link + existing + match.group(3)
        index = index[:match.start()] + new_content + index[match.end():]

        with open(INDEX_PATH, 'w', encoding='utf-8') as f:
            f.write(index)
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description='添加文章到个人网站')
    parser.add_argument('input', help='输入文件路径（HTML或MD）')
    parser.add_argument('slug', help='文章URL标识符（如 investment-review-2026-07）')
    parser.add_argument('--title', help='自定义标题（默认从文件提取）')
    parser.add_argument('--date', help='发布日期 YYYY-MM-DD（默认今天）')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f'错误：文件不存在 - {args.input}')
        sys.exit(1)

    # 日期
    date = args.date or datetime.now().strftime('%Y-%m-%d')

    # 读取文件
    with open(args.input, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取内容
    if args.input.lower().endswith('.md'):
        title, body = extract_from_md(content)
    else:
        title, body = extract_from_html(content)

    if args.title:
        title = args.title

    print(f'标题: {title}')
    print(f'日期: {date}')
    print(f'Slug: {args.slug}')

    # 生成文章页面
    output_path = generate_article_page(title, date, body, args.slug)
    print(f'已生成: {output_path}')

    # 更新index.html
    if update_index(args.slug, title, date):
        print(f'已更新: {INDEX_PATH}')
    else:
        print(f'警告: 未找到"最新文章"区块，请手动在index.html添加链接')

    print(f'\n完成！访问 articles/{args.slug}.html 查看文章')


if __name__ == '__main__':
    main()
