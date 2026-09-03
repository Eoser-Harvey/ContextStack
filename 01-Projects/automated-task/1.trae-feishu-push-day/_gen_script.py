# -*- coding: utf-8 -*-
"""Generate send_daily_ai_news.py with proper string handling"""
import json

# Read the original file
with open('send_daily_ai_news.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all Chinese left/right double quotes with the word markers
# These are the problematic characters that get interpreted as ASCII quotes
replace_map = {
    '\u201c': '「',  # left double quotation mark -> left corner bracket
    '\u201d': '」',  # right double quotation mark -> right corner bracket
}

for old, new in replace_map.items():
    content = content.replace(old, new)

# Also check for any remaining ASCII " inside f-strings that are meant as Chinese quotes
# Let's just do a global replace of the known problematic patterns
# The issue is that in the Write tool, Chinese quotes might have been converted to ASCII

# Check if there are still problematic patterns
lines = content.split('\n')
fixed = []
for i, line in enumerate(lines):
    # Check for lines that have the pattern: 从"技术验证"走向"价值兑现"
    # These should have been converted to 从「技术验证」走向「价值兑现」
    if '从"技术验证"走向"价值兑现"' in line:
        line = line.replace('从"技术验证"走向"价值兑现"', '从技术验证走向价值兑现')
    fixed.append(line)

content = '\n'.join(fixed)

with open('send_daily_ai_news.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')