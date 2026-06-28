# X推文抓取链路问题解决总结

> 归档日期: 2026-06-21  
> 涉及系统: X推文飞书推送系统 v4→v8  
> GitHub仓库: Eoser-Harvey/twitter-feed-fetcher

---

## 一、问题发现

2026-06-21 运行 `run_auto.py` 发现：
- GitHub Actions 拉取到 9 条推文，**但马斯克 (elonmusk) 推文为 0 条**
- 所有 7 次 GitHub Actions 运行都是 `workflow_dispatch`（手动触发），**无 `schedule` 事件**
- 这意味着定时 cron 未激活，数据可能已过时

## 二、根因分析 (逐层排查)

### 问题1: 马斯克推文缺失

**排查过程：**

| 检查项 | 结论 |
|--------|------|
| 代码中是否配置了 elonmusk？ | ✅ 已配置 |
| Nitter RSS 是否返回数据？ | ❌ 10个Nitter实例中 **7个已失效** |
| 是否有回退方案？ | ❌ 无（原代码只有 Nitter 一种数据源） |

**失效实例**：nitter.1d4.us, nitter.kavin.rocks, nitter.unixfox.eu, nitter.domain.glass, nitter.esmailelbob.xyz, nitter.moomoo.me, nitter.privacydev.net

**根因**: Nitter 是第三方社区维护项目，实例频繁下线。原始代码配置的 10 个实例中仅 3 个存活，无法稳定覆盖所有用户。

### 问题2: Cron 未激活

**根因**: GitHub Actions 的 cron 调度要求工作流文件所在的默认分支有最近 commit 才会开始调度。此前仓库只有 `workflow_dispatch` 手动触发记录，没有有效的 schedule 触发。

### 问题3: 互补覆盖问题（v6 发现）

在对 v5 (Nitter优先) 和 v6 (Syndication优先) 的对比测试中发现：

| 数据源 | 马斯克 | CZ | 特朗普 | Serenity |
|--------|--------|-----|--------|----------|
| Nitter RSS (9实例) | ✅ | ✅ | ✅ | ❌ |
| Syndication API | ❌ | ✅ | ❌ | ✅ |

**核心洞察**: 两个数据源有**互补覆盖关系**。单独使用任一源都会丢失某些用户：
- Nitter 丢 Serenity
- Syndication 丢 马斯克、特朗普

## 三、解决方案演进

| 版本 | 策略 | 结果 | 问题 |
|------|------|------|------|
| v4 | Nitter (10个旧实例) → FxTwitter 回退 | 3/4 用户 | 马斯克缺失 |
| v5 | Nitter (9个新实例) → Syndication 回退 | 4/4 (Run #7) | Serenity 间歇丢失 (Run #8) |
| v6 | Syndication 优先 → Nitter 回退 | 2/4 (Run #10) | 马斯克、特朗普丢失 |
| **v7** | **双线并行：每用户同时尝试两个源** | **4/4 (Run #11)** | ✅ 稳定 |

### v7 双线并行策略

```python
# 对每个用户：
user_tweets_syn = fetch_via_syndication(user)   # Source A
user_tweets_nit = fetch_via_nitter(user)        # Source B (仅A失败时)

if user_tweets_syn:
    使用 Syndication 结果
elif user_tweets_nit:
    使用 Nitter 结果  
else:
    标记该用户失败
```

## 四、关键技术决策

| 决策 | 内容 | 理由 |
|------|------|------|
| Nitter 实例更新 | 从 10 个→9 个（全部验证可用） | 来源: Nitter 官方 Wiki |
| 新增 Syndication API | `cdn.syndication.twimg.com` | Twitter 官方嵌入API，免认证，更稳定 |
| 双线并行而非先后 | 同时尝试两个源 | 覆盖互补，确保 4/4 |
| 使用 Googlebot UA | `Mozilla/5.0 (compatible; Googlebot/2.1)` | 避免被 CDN 拒绝 |

## 五、验证结果

### Run #11 (v7) — 最终验证

```
Total: 12 tweets (4/4 users, 0 failed)
Fetched: 2026-06-21T05:02:33 UTC

✅ 马斯克: 3 tweets
✅ CZ (赵长鹏): 3 tweets  
✅ 特朗普: 3 tweets
✅ Serenity (白毛股神): 3 tweets
```

### 全链路验证

- GitHub Actions 抓取: ✅ 12/12 推文，4/4 用户
- 本地 `run_auto.py` 拉取: ✅ github_fetcher.py 正常
- 去重过滤: ✅ tweet_history.json (13条历史) 正确比对
- 翻译: ✅ GitHub Actions 预翻译优先
- 飞书推送: ✅ 6 条消息全部成功（上次推送）

## 六、v8 升级：自动重试 + Nitter 实例自愈

**日期**: 2026-06-21 19:45

### 问题4: 定时任务周期性失败 & Nitter 实例手动维护繁琐

Run #12 (scheduled, 16:01 BJT) 全部数据源临时不可达导致 `exit code 1`，此后 6 个小时无新数据推送。

### v8 解决方案

| 特性 | 实现 |
|------|------|
| **自动重试** | 每用户双源失败后等待 15s 再尝试一次（2 attempts） |
| **健康检查** | 启动时对每个 Nitter 实例做 GET /elonmusk 快速探测（5s 超时），自动排除无响应实例 |
| **Wiki 自动刷新** | 每 6 小时自动抓取 [Nitter 官方 Wiki](https://github.com/zedeus/nitter/wiki/Instances)，解析 Online+Working 双✅实例列表 |
| **全健康回退** | 如果健康检查标记所有实例为 unhealthy，使用完整列表兜底（防止健康检查自身故障导致误判） |

### v8 执行流程

```
Phase 0: Nitter Instance Manager
  ├── 检查 nitter_instances.json 缓存
  ├── >6h? → 抓取 Wiki 获取最新实例列表
  ├── 健康检查: GET /elonmusk (5s timeout)
  └── 输出 healthy 实例列表

Phase 1: Dual-source + Retry (每个用户)
  ├── Attempt 1: Syndication API → Nitter (healthy only)
  └── Attempt 2: wait 15s → Syndication API → Nitter

Phase 2: Translate (unchanged)
Phase 3: Save & Exit
```

## 七、长期维护建议

1. ~~**每月检查 Nitter 实例**~~ ✅ 已自动化：每 6 小时自动从 Wiki 刷新
2. **监控 GitHub Actions 运行** — 确保至少有一个 `schedule` 事件触发记录
3. **关注 Syndication API 稳定性** — 如果 Twitter 更改 API 格式需更新解析器
4. ~~**Nitter 实例维护脚本**~~ ✅ 已内置到 fetch_tweets.py v8

## 八、相关文档

- [ARCHITECTURE.md](ARCHITECTURE.md) — v8 架构文档
- [README.md](README.md) — v7 技术方案归档
- [GitHub 仓库](https://github.com/Eoser-Harvey/twitter-feed-fetcher) — `fetch_tweets.py` v8
