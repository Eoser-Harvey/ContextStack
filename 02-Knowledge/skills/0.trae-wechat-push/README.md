# X推文微信推送系统

> 源项目: `C:\Users\h31280\CodeBuddy\automation-20260616181324\x_tweets\`
> 归档日期: 2026-06-17
> 同步策略: 优化后双向同步

## 架构

```
run_auto.py (主入口)
  ├── fetcher_web.py  → web_search/web_fetch 实时抓取推文
  ├── translator.py   → Google 翻译
  ├── analyzer.py     → 个人画像四维度分析(投资/职业/生活/家庭)
  ├── push_wechat.py  → 消息构建 + Bun JSON-RPC 推送
  │    └── send_one_wechat() → subprocess(Bun) → JSON-RPC 2.0 → 微信
  └── pusher.py       → Server酱备用方案
config.yaml           → 用户配置 + 个人画像
```

## 推送通道

| 通道 | 原理 | 稳定性 |
|------|------|--------|
| Bun JSON-RPC (主力) | Python subprocess → Bun → mcp-wechat-server → JSON-RPC 2.0 | ✅ 独立进程，无状态 |
| Server酱 (备用) | HTTP POST → sctapi.ftqq.com → 微信 | ⚠️ 收费 |

## 关注用户
- 马斯克 (@elonmusk)
- CZ赵长鹏 (@cz_binance)  
- 特朗普 (@realDonaldTrump)

## 同步清单

| 文件 | 说明 | 修改时需同步 |
|------|------|-------------|
| push_wechat.py | 消息构建 + Bun推送核心 | ✅ 双向同步 |
| fetcher_web.py | 推文抓取 | ✅ |
| translator.py | 翻译模块 | ✅ |
| analyzer.py | 分析引擎 | ✅ |
| config.yaml | 配置/画像 | ✅ |
| pusher.py | Server酱备用 | ⬜ 备用 |
| run_auto.py | 主入口 | ✅ |

## 依赖
- Bun: `C:\Users\h31280\.bun\bin\bun.exe`
- mcp-wechat-server: `C:\Users\h31280\AppData\Roaming\npm\node_modules\mcp-wechat-server\src\index.ts`
- Python 依赖: requests, pyyaml, deep-translator
