# X推文飞书推送系统 — 技术方案归档

> 归档日期: 2026-06-20
> 当前版本: v3 (飞书推送版，从微信推送迁移)

---

## 一、系统架构

```
┌─────────────────────────────────────────────────────┐
│                  TRAE 自动化定时任务                   │
│            (每小时触发 run_auto.py)                    │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│                   run_auto.py (主控)                  │
│  1. build_tweets_from_fetch()  ← fetcher_web.py     │
│  2. translator.translate_tweets() ← translator.py   │
│  3. analyze_tweets()           ← analyzer.py         │
│  4. push_to_lark()             ← push_lark.py        │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              push_lark.py (飞书推送)                  │
│  Python subprocess.run → node → lark-cli → 飞书 IM API│
└─────────────────────────────────────────────────────┘
```

## 二、文件清单 (1.feishu-push/)

| 文件 | 用途 |
|------|------|
| `run_auto.py` | 主控脚本：加载→翻译→分析→推送→更新历史 |
| `fetcher_web.py` | 推文数据源（硬编码，因公司网络无法访问X.com） |
| `translator.py` | 翻译模块：优先读 translation_cache.json，备选 Google 翻译 API |
| `translation_cache.json` | AI 预翻译缓存（tweet_id → 中文翻译） |
| `analyzer.py` | AI 分析模块：基于个人画像生成投资/职业/生活/家庭四维度建议 |
| `config.yaml` | 系统配置：关注用户、翻译引擎、个人画像、输出配置 |
| `push_lark.py` | 飞书推送模块：通过 lark-cli 发送消息到飞书群 |
| `tweet_history.json` | 已推送推文 ID 列表（去重用） |
| `latest_tweets.json` | 最近一次分析的推文结果（含翻译+分析） |
| `profile_archive/` | 每日个人画像快照归档 |

## 三、推送流程

1. **加载推文** — `fetcher_web.py` 返回硬编码推文列表（4个用户：马斯克、CZ、特朗普、白毛股神）
2. **去重过滤** — 对比 `tweet_history.json`，只处理未推送过的新推文
3. **翻译** — 优先从 `translation_cache.json` 读取 AI 预翻译，缓存未命中则调用 Google 翻译 API
4. **AI 分析** — `analyzer.py` 基于个人画像（config.yaml 中的 profile）对每条推文生成四维度建议
5. **构建消息** — 摘要头 + 每条推文详情（emoji头像/标签/时间/原文/翻译/洞察）+ 行动清单
6. **分段推送** — 每条消息间隔 2 秒，通过 lark-cli 发送到飞书群
7. **更新历史** — 推送成功后将新推文 ID 写入 `tweet_history.json`

## 四、关键技术决策与踩坑记录

### 4.1 lark-cli 调用方式（核心问题）

**问题**: Python `subprocess.run` 传 JSON 字符串给 lark-cli 时，双引号被吞掉，导致 `--content` 参数解析失败。

**根因分析**:
- `push_lark.py` 最初设计使用 `lark-cli.cmd`（.cmd 文件内部调用 cmd.exe）
- cmd.exe 会将 `"` 双引号作为特殊字符处理，吞掉 JSON 中的双引号
- 即使改用 `node` 直接调用 lark-cli 脚本，如果通过 PowerShell 命令行手动测试，PowerShell 也会吞双引号

**最终方案**:
```python
# push_lark.py 中的关键设计
USE_DIRECT_NODE = os.path.exists(LARK_NODE) and os.path.exists(LARK_SCRIPT)

cmd = [LARK_NODE, LARK_SCRIPT, "im", "+messages-send",
       "--chat-id", chat_id,
       "--content", content_json,  # json.dumps 生成的 JSON 字符串
       "--as", "user"]

result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=20)
```

**为什么这个方案能工作**:
- `subprocess.run(cmd)` 传参列表模式（不是 shell=True），参数直接传递给 node 进程，**不经过任何 shell 解析**
- node 进程接收到完整的 JSON 字符串（含双引号），lark-cli 正确解析
- 这个问题只在 PowerShell/cmd.exe 命令行手动测试时才会出现，Python 脚本中不存在

**以后不会再有的原因**:
- `push_lark.py` 使用 `subprocess.run` 参数列表模式，绕过了所有 shell 解析
- 自动化任务由 TRAE 直接执行 Python 脚本，不经过 PowerShell 命令行
- lark-cli 的 token 由 TRAE IDE 外部管理，不需要在脚本中处理认证

### 4.2 lark-cli 身份与 strict mode

- 当前 lark-cli 配置为 **strict mode = user**，只允许 `--as user` 身份
- `--as bot` 会被拒绝（`strict mode is "user"`）
- user token 由 TRAE IDE 管理，脚本中无需处理登录
- 如果 token 过期，需要在 TRAE IDE 中重新授权飞书连接

### 4.3 特殊字符处理

- `$` 和 `|` 在 cmd.exe 中是特殊字符，会被误解析
- 推文文本中使用全角 `｜` 替代半角 `|`
- `$` 符号在 analyzer.py 的 f-string 中需要用 `$$` 转义（如 `$$10,500`）

### 4.4 推送失败与历史记录

- `push_to_lark()` 返回 `success_count > 0` 即视为成功
- 只有返回 True 时才更新 `tweet_history.json`
- 如果所有消息都失败（success_count = 0），历史不更新，下次自动重试

## 五、自动化任务配置

| 任务 | 频率 | 说明 |
|------|------|------|
| X推文飞书推送 | 每小时 | 抓取→翻译→分析→推送 |
| 投资职业档案归档 | 每天 0:00 | 读取最新持仓/职业档案，更新 config.yaml |

## 六、从微信迁移到飞书的变更

- 删除: `push_wechat.py`, `pusher.py`, `test_wechat_login.py`, `wechat_message.txt`, `heartbeat.py`, `keepalive.py`, `setup_keepalive.bat`
- 新增: `push_lark.py`（通过 lark-cli 发送飞书消息）
- 路径: `0.wechat-push/` → `1.feishu-push/`
- 推送通道: 微信（需登录+心跳保活）→ 飞书（lark-cli，无需保活）
