# WeChat Radar — 安装文档

微信公众号 AI 智能日报：自动抓取 → 规则过滤 → AI 多维度评分 → 多渠道推送。

## 前置条件

| 依赖 | 要求 |
|------|------|
| Python | 3.9+ |
| pip | 自动安装 |
| 微信订阅号 | 免费即可，用来扫码登录公众号后台 |
| AI API Key | DeepSeek / OpenAI / 通义千问 等（任选一个） |

## 安装步骤

### 1. 获取代码

项目已纳入 ContextStack 框架，克隆框架仓库即可：

```bash
git clone https://github.com/Eoser-Harvey/ContextStack.git
cd ContextStack/01-Projects/wechat-radar
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

依赖清单：`anthropic`、`openai`、`beautifulsoup4`、`lxml`、`requests`、`python-dotenv`、`PyYAML`、`qrcode`、`tqdm`

### 4. 配置 .env

```bash
cp .env.example .env
```

编辑 `.env`，至少填入：

```
AI_PROVIDER=openai-compatible
AI_API_KEY=你的API-Key
AI_BASE_URL=https://api.deepseek.com      # 以 DeepSeek 为例
AI_MODEL=deepseek-chat
```

**常用服务商参考**（选一个即可）：

| 服务商 | AI_BASE_URL | AI_MODEL |
|--------|-------------|----------|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| 硅基流动 | `https://api.siliconflow.cn/v1` | `Qwen/Qwen2.5-72B-Instruct` |

**推送渠道**（可选，在 `.env` 中取消注释并填入）：
- 飞书机器人 Webhook
- 钉钉机器人 Webhook
- 企业微信机器人 Webhook
- 邮件推送
- Telegram Bot
- Bark（iOS）
- Server酱 / PushPlus（微信）

### 5. 配置 config.yaml

编辑 `config.yaml` 中的 `profile` 部分，填入你的背景和兴趣偏好，AI 会据此调整评分：

```yaml
profile:
  background: "网络工程师，关注AI落地和自动化"
  interests:
    - "AI"
    - "网络技术"
    - "效率工具"
```

### 6. 扫码登录微信公众号平台

```bash
python main.py --login
```

终端会显示二维码，用绑定了公众号的微信扫码即可。

### 7. 测试运行

```bash
python main.py --test         # 测试模式（每个公众号取1篇）
python main.py --dry-run      # 试运行（完整抓取，不推送）
python main.py                # 正式运行
```

## 常用命令

| 命令 | 作用 |
|------|------|
| `python main.py` | 正式运行，抓取 + 评分 + 推送 |
| `python main.py --test` | 测试模式，每个公众号只取 1 篇 |
| `python main.py --dry-run` | 试运行，不实际推送 |
| `python main.py --login` | 重新扫码登录 |
| `python main.py --setup-cron` | 配置定时任务 |

## 文件说明

| 文件 | 用途 |
|------|------|
| `.env` | API Key + 推送渠道配置（不纳入 git） |
| `config.yaml` | 公众号列表、评分维度、推送偏好 |
| `main.py` | 入口 |
| `fetcher.py` | 公众号文章抓取 |
| `filter.py` | AI 评分与过滤 |
| `notifier.py` | 多渠道推送 |
| `auth.py` | 微信登录认证 |
