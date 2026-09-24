# -*- coding: utf-8 -*-
"""Update news references using unicode matching"""
fp = r"E:\ProjectGroup\AI\ContextStack\01-Projects\automated-task\1.trae-feishu-push-day\send_daily_ai_news.py"
with open(fp, "r", encoding="utf-8") as f:
    txt = f.read()

# The old text in the file uses \uXXXX unicode escapes
# Let's find the invest_head section by looking for "【融资/并购】NVIDIA 129亿"
old_unicode = "\\u3010\\u878d\\u8d44/\\u5e76\\u8d2d\\u3011NVIDIA 129\\u4ebf\\u7f8e\\u5143\\u6536\\u8d2dHugging Face+Nscale\\u7ebd\\u7ebfIPO(350\\u4ebf\\u4f30\\u503c\\u624b\\u63e1900\\u4ebf\\u5408\\u540c);"

new_unicode = "\\u3010\\u878d\\u8d44/\\u5e76\\u8d2d\\u3011\\u7845\\u57fa\\u6d41\\u52a829\\u4ebf\\u878d\\u8d44+ADI 13.5\\u4ebf\\u6536\\u8d2dAlif+Cognex 5\\u4ebf\\u6536\\u8d2dRealSense;"

# Try replacing each of the 6 lines in invest_head
# Line 1: 融资/并购
count = 0
if old_unicode in txt:
    txt = txt.replace(old_unicode, new_unicode)
    print("✅ Line 1: 融资/并购 replaced")
    count += 1
else:
    print("❌ Line 1 NOT found")

# Line 2: 产品发布
old_p = "\\u3010\\u4ea7\\u54c1\\u53d1\\u5e03\\u3011OpenAI Presence\\u4f01\\u4e1aAI Agent+OpenAI Grok Bot\\u5bf9\\u6297+Grok\\u667a\\u80fd\\u4f53\\u91cd\\u7ec4;"
new_p = "\\u3010\\u4ea7\\u54c1\\u53d1\\u5e03\\u3011Anthropic Opus 5.5(\\u6210\\u672c\\u964d40%)+OpenAI GPT-6 Sol/Luna(\\u964d\\u4ef750%)+\\u9ad8\\u901a\\u664b\\u9f998 Elite Gen 6(2nm/300B\\u7aef\\u4fa7);"
if old_p in txt:
    txt = txt.replace(old_p, new_p)
    print("✅ Line 2: 产品发布 replaced")
    count += 1
else:
    print("❌ Line 2 NOT found")

# Line 3: 技术突破
old_t = "\\u3010\\u6280\\u672f\\u7a81\\u7834\\u3011DeepSeek-V4.1-Flash(552B MoE MIT\\u5f00\\u6e90)+\\u667a\\u8c31GLM-5.3-Flash\\u56fd\\u4ea7\\u82af\\u72473.2\\u500d\\u63d0\\u5347;"
new_t = "\\u3010\\u6280\\u672f\\u7a81\\u7834\\u3011DeepSeek-V4.1-Flash(552B MoE\\u975e\\u5bf9\\u79f0/KV\\u7f13\\u5b581/4)+Google Gemini 3.8 Flash/Cyber;"
if old_t in txt:
    txt = txt.replace(old_t, new_t)
    print("✅ Line 3: 技术突破 replaced")
    count += 1
else:
    print("❌ Line 3 NOT found")

# Line 4: 法规
old_r = "\\u3010\\u6cd5\\u89c4\\u3011OpenAI\\u547c\\u5401\\u7f8e\\u56fd\\u5934\\u7b79\\u5168\\u7403AI\\u6807\\u51c6+\\u6fb3\\u5927\\u5229\\u4e9a\\u652f\\u6301\\u52a0\\u5f3aAI\\u76d1\\u7ba1;"
new_r = "\\u3010\\u6cd5\\u89c4\\u3011\\u7ebd\\u7ea6\\u5ddeRAISE\\u6cd5\\u684872\\u5c0f\\u65f6\\u5b89\\u5168\\u62a5\\u544a+\\u4e2d\\u56fdAI\\u5b89\\u5168\\u6cbb\\u7406\\u6846\\u67b63.0;"
if old_r in txt:
    txt = txt.replace(old_r, new_r)
    print("✅ Line 4: 法规 replaced")
    count += 1
else:
    print("❌ Line 4 NOT found")

# Line 5: 半导体
old_s = "\\u3010\\u534a\\u5bfc\\u4f53\\u3011\\u53f0\\u79ef\\u7535\\u6da8\\u4ef710%+AMD\\u5168\\u7ebf\\u6da8\\u4ef710%+\\u8054\\u7535\\u529b\\u79ef\\u7535\\u917f\\u917f\\u6da8\\u4ef7+IBM 10\\u4ebf\\u91cf\\u5b50\\u6676\\u5706;"
new_s = "\\u3010\\u534a\\u5bfc\\u4f53\\u3011\\u53f0\\u79ef\\u7535\\u6da8\\u4ef75-10%+AMD\\u5168\\u7ebf\\u6da8\\u4ef710%+\\u4e09\\u661f\\u5f97\\u5dde\\u6cf0\\u52d2\\u5de5\\u53822nm\\u6708\\u5e95\\u8bd5\\u4ea7;"
if old_s in txt:
    txt = txt.replace(old_s, new_s)
    print("✅ Line 5: 半导体 replaced")
    count += 1
else:
    print("❌ Line 5 NOT found")

# Line 6: 机器人
old_rob = "\\u3010\\u673a\\u5668\\u4eba\\u3011\\u7279\\u65af\\u62c9Optimus\\u5f97\\u5dde\\u5de5\\u5382\\u63a5\\u8fd1\\u5b8c\\u5de5+Humanoids Summit\\u9996\\u5c14\\u5c06Physical AI\\u5217\\u4e3a\\u56fd\\u5bb6\\u4f18\\u5148+\\u5927\\u6653\\u673a\\u5668\\u4eba\\u52a0\\u6cb9\\u7ad9\\u96f6\\u552e\\u5177\\u8eab\\u667a\\u80fd\\u8bd5\\u8fd0\\u8425\\u3002"
new_rob = "\\u3010\\u673a\\u5668\\u4eba\\u3011\\u6ce2\\u58eb\\u987f\\u52a8\\u529bAtlas\\u73b0\\u4ee3\\u5de5\\u5382\\u8bad\\u7ec3\\u4e2d\\u5fc3+\\u5177\\u8eab\\u667a\\u80fd2026H1\\u878d\\u8d44935\\u4ebf+\\u7279\\u65af\\u62c9Optimus\\u53cc\\u7ebf\\u63a8\\u8fdb\\u3002"

if old_rob in txt:
    txt = txt.replace(old_rob, new_rob)
    print("✅ Line 6: 机器人 replaced")
    count += 1
else:
    print("❌ Line 6 NOT found (trying partial match)")
    # Try shorter match
    for test in ["\\u3010\\u673a\\u5668\\u4eba\\u3011\\u7279\\u65af\\u62c9Optimus\\u5f97\\u5dde\\u5de5\\u5382"]:
        if test in txt:
            print(f"  Found partial: {test[:50]}")
    short_old = "Optimus\\u5f97\\u5dde\\u5de5\\u5382\\u63a5\\u8fd1\\u5b8c\\u5de5+Humanoids Summit\\u9996\\u5c14"
    short_new = "Optimus\\u53cc\\u7ebf\\u63a8\\u8fdb+\\u6ce2\\u58eb\\u987f\\u52a8\\u529bAtlas\\u8bad\\u7ec3\\u4e2d\\u5fc3+\\u5177\\u8eab\\u667a\\u80fd935\\u4ebf\\u878d\\u8d44"
    if short_old in txt:
        txt = txt.replace(short_old, short_new)
        print("✅ Line 6 replaced via short match")
        count += 1

with open(fp, "w", encoding="utf-8") as f:
    f.write(txt)

print(f"\nTotal replacements: {count}/6")

import os
os.remove(__file__)
print("Done")