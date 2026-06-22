# X推文飞书推送系统 — 技术方案归档

> 归档日期: 2026-06-21  
> 当前版本: **v7 (双线并行: Syndication + Nitter 互补覆盖, 4/4稳定)**

---

## 一、系统架构

```
┌─────────────────────────────────────────────────────────┐
│           GitHub Actions (海外IP, 每小时整点)              │
│  fetch_tweets.py v7: 双线并行 (Syndication + Nitter)     │
│  → Google Translate → git push tweets.json               │
└────────────────────────┬────────────────────────────────┘
                         │ GitHub API
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   run_auto.py (主控)                      │
│  1. github_fetcher.py  ← 拉取 tweets.json               │
│  2. fetcher_web.py     ← 加载 & 去重                     │
│  3. translator.py      ← 翻译 (GitHub预翻译优先)          │
│  4. analyzer.py        ← AI分析 (四维度)                  │
│  5. push_lark.py       ← 飞书群推送 (Bot → Open API)     │
└─────────────────────────────────────────────────────────┘
```

## 二、文件清单

| 文件 | 用途 |
|------|------|
| `run_auto.py` | 主控脚本：拉取→去重→翻译→分析→推送→更新历史 |
| `github_fetcher.py` | GitHub数据拉取：从 Eoser-Harvey/twitter-feed-fetcher 拉取 tweets.json |
| `fetcher_web.py` | 数据加载：三数据源优先级（GitHub Actions → 本地缓存 → 硬编码兜底） |
| `translator.py` | 翻译模块：优先GitHub预翻译，缓存命中，兜底Google API |
| `analyzer.py` | AI分析：基于个人画像生成投资/职业/生活/家庭四维度建议 |
| `config.yaml` | 系统配置：关注用户、翻译引擎、个人画像、输出配置 |
| `push_lark.py` | 飞书推送：Bot身份 → HTTP POST → 飞书 Open API |
| `tweet_history.json` | 已推送推文ID列表（去重用） |
| `latest_tweets.json` | 最近一次分析的推文结果（含翻译+分析） |
| `fetched_tweets.json` | GitHub拉取结果的本地副本 |
| `translation_cache.json` | 翻译缓存（tweet_id → 中文翻译） |
| `profile_archive/` | 每日个人画像快照归档 |

## 三、推送流程

1. **GitHub 拉取** — `github_fetcher.py` 从 `Eoser-Harvey/twitter-feed-fetcher` 仓库 API 拉取 tweets.json
2. **去重过滤** — 对比 `tweet_history.json`，只处理未推送过的新推文
3. **翻译** — 优先使用 GitHub Actions 预翻译（海外Google Translate），缓存命中
4. **AI 分析** — `analyzer.py` 基于 `config.yaml` 个人画像对每条推文生成四维度建议
5. **构建消息** — 摘要头 + 每条推文详情（推送号/标签/时间/原文/翻译/洞察）
6. **分段推送** — 每条消息间隔2秒，通过 Bot 身份发送到飞书群
7. **更新历史** — 推送成功后将新推文ID写入 `tweet_history.json`

## 四、目标用户 (v5 全覆盖)

| 用户 | X用户名 | 抓取数 | 状态 |
|------|---------|--------|------|
| 马斯克 | elonmusk | 3条/次 | ✅ |
| CZ (赵长鹏) | cz_binance | 3条/次 | ✅ |
| 特朗普 | realDonaldTrump | 3条/次 | ✅ |
| Serenity (白毛股神) | aleabitoreddit | 3条/次 | ✅ |

**Run #7 验证**: 12/12 推文，4/4 用户全部成功。

## 五、抓取技术栈 (v7 双线并行)

| 数据源 | 类型 | 马斯克 | CZ | 特朗普 | Serenity |
|--------|------|--------|-----|--------|----------|
| **Syndication API** | Twitter 官方嵌入 | ❌ | ✅ | ❌ | ✅ |
| **Nitter RSS (9实例)** | 第三方代理 | ✅ | ✅ | ✅ | ❌ |
| **合并覆盖** | — | ✅ | ✅ | ✅ | ✅ |

> **核心创新**: 两个数据源有互补覆盖关系。v7 对每个用户**同时尝试两个源**，取首个成功的，确保 4/4 全覆盖。

**Nitter 实例（9个，来源官方Wiki）**:
xcancel.com, nitter.poast.org, nitter.privacyredirect.com, lightbrd.com,
nitter.space, nitter.tiekoetter.com, nuku.trabun.org, nitter.catsarch.com, nitter.kareem.one

## 六、关键技术决策

### 6.1 飞书Bot推送 (v4起)

- 使用 `app_id` + `app_secret` 获取 tenant_access_token
- 直接 HTTP POST 调用飞书 Open API，不依赖 lark-cli
- Token 自动缓存到 `.lark_token_cache.json`，提前5分钟刷新
- 稳定性：Bot token 永久有效，无需用户授权刷新

### 6.2 特殊字符处理

- `$` 和 `|` 在飞书消息中可能被误解析
- 推文文本中使用全角 `｜` 替代半角 `|`
- `$` 符号在 analyzer.py 中用 `$$` 转义

### 6.3 推送失败与历史记录

- `push_to_lark()` 返回 `success_count > 0` 即视为成功
- 只有返回 True 时才更新 `tweet_history.json`
- 如果所有消息都失败，历史不更新，下次自动重试

### 6.4 Nitter实例维护

- 旧实例（nitter.1d4.us, kavin.rocks, unixfox.eu等）已全部失效
- v5 更新为官方Wiki验证的9个可用实例
- 建议每月检查一次 [Nitter官方Wiki](https://github.com/zedeus/nitter/wiki/Instances)

## 七、自动化任务配置

| 任务 | 频率 | 说明 |
|------|------|------|
| X推文飞书推送 | 每小时 | GitHub Actions抓取+翻译 → 本地拉取→分析→推送 |
| 投资职业档案归档 | 每天 0:00 | 读取最新持仓/职业档案，更新 config.yaml |

## 八、故障排查

| 问题 | 处理 |
|------|------|
| 某用户0条推文 | Nitter自动回退到Syndication API；不影响其他用户 |
| 推送失败 | 不更新历史，下次自动重试 |
| GitHub Actions未触发 | 手动 workflow_dispatch；或等待cron下个整点 |
| Nitter实例过期 | 定期检查官方Wiki更新实例列表 |

## 九、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1-v3 | 2026-06 | 初始版本：Nitter抓取 + 微信推送 |
| v4 | 2026-06-21 | 飞书推送迁移；FxTwitter回退 |
| v5 | 2026-06-21 | 更新9个验证可用Nitter实例；Syndication回退 |
| v6 | 2026-06-21 | Syndication优先策略（发现互补覆盖问题） |
| **v7** | **2026-06-21** | **双线并行策略：每用户同时尝试两个源，互补覆盖 → 4/4 稳定** |