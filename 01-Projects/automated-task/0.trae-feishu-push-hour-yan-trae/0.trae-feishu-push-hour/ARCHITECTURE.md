# X推文全流程自动化方案 — 架构文档

> 归档时间: 2026-06-21  
> 当前版本: **v8 (自动重试 + Nitter 实例自愈)**  
> 稳定性: ✅ 4/4 用户全覆盖 (Run #14/#15 验证)  
> 目标路径: `01-Projects/automated-task/0.trae-feishu-push-hour`  
> 执行入口: `python run_auto.py`

---

## 一、问题背景

国内网络无法直接访问 X.com/Twitter，导致：
- 浏览器无法抓取推文
- Google Translate API 被墙
- 传统方案（浏览器自动化/API直连）全部失效

## 二、架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Actions (海外IP)                       │
│                                                                 │
│  cron: 0 * * * * (每小时整点)                                    │
│  ┌──────────────────────────────────────────────────┐           │
│  │  fetch_tweets.py (v7 — 双线并行)                   │           │
│  │                                                   │           │
│  │  对每个用户同时尝试两个数据源:                       │           │
│  │                                                   │           │
│  │  Source A: Twitter Syndication API                │           │
│  │    cdn.syndication.twimg.com (官方嵌入,免认证)      │           │
│  │    覆盖: CZ ✅, Serenity ✅                        │           │
│  │                                                   │           │
│  │  Source B: Nitter RSS (9个验证可用实例)             │           │
│  │    覆盖: 马斯克 ✅, CZ ✅, 特朗普 ✅                 │           │
│  │                                                   │           │
│  │  取首个成功的源 → 互补覆盖全4用户                    │           │
│  │                                                   │           │
│  │  Step 3: Google Translate (海外直连)                │           │
│  └──────────────────────┬───────────────────────────┘           │
│                         │                                       │
│                    tweets.json                                   │
│                    translation_cache.json                        │
│                         │                                       │
│                    git commit & push                             │
└─────────────────────────┼───────────────────────────────────────┘
                          │
                 GitHub API (国内可访问)
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                        本地 (国内 Windows)                        │
│                          │                                       │
│  ┌──────────────────┐   │                                       │
│  │ github_fetcher.py │ ←─┘  拉取 tweets.json                     │
│  └────────┬─────────┘                                           │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────┐                                            │
│  │ fetcher_web.py   │  数据源优先级:                              │
│  │ 数据加载 & 去重   │  1. GitHub Actions (实时)                   │
│  └────────┬─────────┘  2. fetched_tweets.json (本地缓存)          │
│           │             3. 硬编码兜底数据                           │
│           ▼                                                      │
│  ┌──────────────────┐                                            │
│  │ translator.py    │  优先使用 GitHub Actions 预翻译              │
│  │ 翻译 (缓存命中)   │  失败 → Google Translate API                │
│  └────────┬─────────┘                                            │
│           ▼                                                      │
│  ┌──────────────────┐                                            │
│  │ analyzer.py      │  基于个人画像生成:                           │
│  │ AI 分析          │  投资 / 职业 / 生活 / 家庭 四维度建议         │
│  └────────┬─────────┘                                            │
│           ▼                                                      │
│  ┌──────────────────┐                                            │
│  │ push_lark.py     │  Bot 身份 → 飞书 Open API                   │
│  │ 飞书群推送        │  POST /auth/v3/tenant_access_token/internal │
│  └──────────────────┘  POST /im/v1/messages                      │
│                                                                 │
│           ▼                                                      │
│  ┌──────────────────┐                                            │
│  │ 飞书群            │  CodeBuddy推文推送①                         │
│  │ oc_569a7503...    │                                            │
│  └──────────────────┘                                            │
└──────────────────────────────────────────────────────────────────┘
```

## 三、核心文件说明

### 3.1 本地执行文件 (01-Projects/automated-task/0.trae-feishu-push-hour)

| 文件 | 职责 | 关键逻辑 |
|------|------|---------|
| `run_auto.py` | **主控入口** | 编排全流程：加载→去重→翻译→分析→推送 |
| `github_fetcher.py` | **GitHub 数据拉取** | 从 `Eoser-Harvey/twitter-feed-fetcher` 仓库拉取 tweets.json |
| `fetcher_web.py` | **数据加载 & 去重** | 三数据源优先级，对比 tweet_history.json 去重 |
| `translator.py` | **翻译模块** | 优先 GitHub 预翻译，缓存命中，兜底 Google API |
| `analyzer.py` | **AI 分析模块** | 基于 profile_archive 个人画像的四维度分析 |
| `push_lark.py` | **飞书推送模块** | Bot 身份 → token 自动缓存 → 群消息推送 |
| `config.yaml` | **配置文件** | 目标用户、推送群、分析维度等配置 |
| `tweet_history.json` | **推送历史** | 已推送推文 ID 列表，用于去重 |
| `translation_cache.json` | **翻译缓存** | tweet_id → 中文翻译 映射 |
| `fetched_tweets.json` | **本地缓存** | GitHub 拉取结果的本地副本 |
| `latest_tweets.json` | **最新分析结果** | 含分析结果的完整推文数据 |

### 3.2 GitHub 远程仓库 (Eoser-Harvey/twitter-feed-fetcher)

| 文件 | 职责 |
|------|------|
| `fetch_tweets.py` (v7) | **抓取+翻译**：双线并行（Syndication + Nitter RSS 9实例）→ Google Translate |
| `.github/workflows/fetch-tweets.yml` | **定时触发**：`cron: 0 * * * *`（每小时整点）+ `workflow_dispatch`（手动触发） |
| `tweets.json` | **产出**：含原文+翻译的推文数据 |
| `translation_cache.json` | **翻译缓存**：跨运行复用，避免重复翻译 |

## 四、抓取方法 (fetch_tweets.py v7)

### 双线并行策略（核心创新）

| 数据源 | 类型 | 马斯克 | CZ | 特朗普 | Serenity |
|--------|------|--------|-----|--------|----------|
| **Syndication API** | Twitter 官方嵌入 | ❌ | ✅ | ❌ | ✅ |
| **Nitter RSS (9实例)** | 第三方代理 | ✅ | ✅ | ✅ | ❌ |
| **合并覆盖** | — | ✅ | ✅ | ✅ | ✅ |

> **关键洞察**：两个数据源有**互补覆盖**，单独使用任一个都会丢失某些用户。v7 对每个用户**同时尝试两个源**，取首个成功的，确保 4/4 全覆盖。

### Nitter 实例列表（来源: [官方Wiki](https://github.com/zedeus/nitter/wiki/Instances)）

| 实例 | 国家 | 状态 |
|------|------|------|
| `xcancel.com` | 🇺🇸 | ✅ |
| `nitter.poast.org` | 🇺🇸 | ✅ |
| `nitter.privacyredirect.com` | 🇫🇮 | ✅ |
| `lightbrd.com` | 🇹🇷 | ✅ |
| `nitter.space` | 🇺🇸 | ✅ |
| `nitter.tiekoetter.com` | 🇩🇪 | ✅ |
| `nuku.trabun.org` | 🇨🇱 | ✅ |
| `nitter.catsarch.com` | 🇺🇸/🇩🇪 | ✅ |
| `nitter.kareem.one` | 🇸🇬 | ✅ |

## 五、推送目标

| 目标用户 | X用户名 | 抓取数 | 覆盖率 |
|---------|---------|--------|--------|
| 马斯克 | elonmusk | 3条/次 | ✅ |
| CZ (赵长鹏) | cz_binance | 3条/次 | ✅ |
| 特朗普 | realDonaldTrump | 3条/次 | ✅ |
| Serenity (白毛股神) | aleaborteddit | 3条/次 | ✅ |

**验证**: Run #7 (v5): 12/12 | Run #11 (v7): 12/12 双线并行稳定。

## 六、飞书推送配置

| 配置项 | 值 |
|--------|-----|
| App ID | `cli_aabc86283bb85bd7` |
| App Secret | `klKMqJjy9BrCahEm1Q8gvhFFuyK6YxJn` |
| 目标群 | `oc_569a7503a8f86eeb1f4630f31f985e50` (CodeBuddy推文推送①) |
| 推送方式 | Bot 身份 → HTTP POST → 飞书 Open API |
| Token 缓存 | `.lark_token_cache.json`，提前5分钟刷新 |
| 消息间隔 | 2秒 |

## 七、运行方式

```bash
cd "E:\ProjectGroup\AI\ContextStack\01-Projects\automated-task\0.trae-feishu-push-hour"
python run_auto.py
```

- **GitHub Actions**: `cron: 0 * * * *` 每小时整点自动抓取+翻译
- **本地 TRAE Schedule**: 每小时执行 `run_auto.py`
- 每次执行先去重，只推送新推文

## 八、故障处理

| 故障 | 现象 | 处理 |
|------|------|------|
| GitHub 拉取失败 | `使用硬编码兜底数据` | 手动 workflow_dispatch |
| 某用户抓取失败 | 该用户 0 条 | **v8 自动重试（等15s再试一次）**，不影响其他用户 |
| 推送失败 | 无 msg_id | 不更新历史，下次自动重试 |
| Nitter 实例过期 | 部分失效 | **v8 每6h自动抓取 Wiki 刷新，启动时健康检查排除死节点** |
| Git push 冲突 | Run 标记 failure | 同一时刻有多个 push — 下一次自动成功 |

## 九、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1-v3 | 2026-06 | 初始版本：Nitter抓取 + 微信推送 |
| v4 | 2026-06-21 | 飞书推送迁移；FxTwitter回退 |
| v5 | 2026-06-21 | 更新9个验证可用Nitter实例；添加Syndication API回退 |
| v6 | 2026-06-21 | Syndication优先策略（发现互补覆盖问题） |
| v7 | 2026-06-21 | 双线并行策略：每用户同时尝试两个源，互补覆盖 → 4/4稳定 |
| **v8** | **2026-06-21** | **自动重试(2 attempts per user) + Nitter 实例自愈(健康检查 + Wiki每6h自动刷新)** |

## 十、技术要点

- **文本处理**: 避免 `$` `｜`，用全角 `｜` 替代
- **去重逻辑**: 推文 ID 比对 `tweet_history.json`
- **推送失败不更新历史**: 下次自动重试
- **翻译双重保障**: GitHub Actions 海外预翻译 + 本地缓存
- **Bot 永久有效**: app_id + app_secret，无需用户授权刷新
- **v8 自愈系统**: 启动时健康检查 Nitter 实例 + 每 6h 自动从 [官方Wiki](https://github.com/zedeus/nitter/wiki/Instances) 刷新实例列表 + 每用户双源失败后 15s 自动重试一次
- **Cron 调度**: 新 commit 推送 main 分支后自动激活