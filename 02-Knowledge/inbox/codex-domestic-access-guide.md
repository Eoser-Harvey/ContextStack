# Codex 国内接入三种方案教程

> 来源: https://mp.weixin.qq.com/s/Qvfr9LC2wF9ltCEyKFqK3g
> 作者: 苍何（第540篇原创）
> 整理时间: 2026-05-29
> 标签: AI技术、Codex、国内接入、工具配置

---

## 问题背景

Codex 默认需要 GPT 账号登录，国内用户面临：
- Plus 充值门槛
- 支付方式折腾
- 第三方 API 接入复杂

**解决方案**: 三种接入方法，按需选择。

---

## 三种方案对比

| 方案 | 适合谁 | 优点 | 注意事项 |
|------|--------|------|---------|
| **手动配置** | 想理解底层原理的人 | 透明、可控、方便排障 | 要自己维护 config.toml，写错就不生效 |
| **Codex++** | 用桌面 App，想图形化管理的人 | 有管理界面，配置一键写入，支持插件 | 第三方工具，Codex 更新后可能需要适配 |
| **CCX + CC Switch** | 有多个供应商、需要协议转换的人 | 网关路由 + 一键切换供应商 | 组件多，需要理解端口和代理链路 |

**推荐**: 小白直接用方案二 Codex++，最省心。

---

## 方案一：手动配置

### 核心文件
```
~/.codex/config.toml
~/.codex/auth.json
```

### 前置步骤
```bash
# 备份原配置
cp ~/.codex/config.toml ~/.codex/config.toml.backup
cp ~/.codex/auth.json ~/.codex/auth.json.backup
```

### 两类登录思路

| 思路 | 说明 | 适合场景 |
|------|------|---------|
| **GPT 登录态** | 保留官方登录态，只改请求转发地址 | 想保留官方账号能力，同时用中转 |
| **API Key 登录** | 用环境变量里的 Key，直接请求第三方 | 用 OpenAI API Key 或自建兼容服务 |

### GPT 登录态配置示例

**第一步：修改 config.toml**
```toml
model = "gpt-5-codex"  # 填你想要的模型
model_reasoning_effort = "high"
disable_response_storage = true
preferred_auth_method = "apikey"

[model_providers.ciyuan]
name = "ciyuan"  # 模型提供商名字
base_url = "https://ciyuan.today/v1"  # 只写到 /v1
wire_api = "responses"  # 不要改
env_key = "OPENAI_API_KEY"
requires_openai_auth = false
```

**踩坑点**:
- `model_provider` 要和 `[model_providers.xxx]` 里的 `xxx` 完全一致
- `base_url` 只写到 `/v1`，不要写 `/v1/responses`
- `wire_api = "responses"` 表示用 Responses API 形态，别改
- `requires_openai_auth = false` 表示不走官方登录态

**第二步：设置环境变量**
```bash
export OPENAI_API_KEY="这里填你的key"
```

**第三步：从终端启动 Codex APP**
```bash
# Mac 必须从终端启动，直接点图标可能读不到模型
open -a Codex
```

### API Key 登录配置示例

```bash
export OPENAI_API_KEY="sk-your-api-key"
```

```toml
model = "gpt-5.1-codex-max"
model_provider = "my-api-provider"

[model_providers.my-api-provider]
name = "My API Provider"
base_url = "https://example.com/v1"
wire_api = "responses"
env_key = "OPENAI_API_KEY"
requires_openai_auth = false
```

**注意**: 如果上游只支持 Chat Completions，不支持 Responses API，需要用 CCX 做协议转换（方案三）。

### 验证配置成功

1. 完全退出 Codex，重新打开
2. 执行只读任务测试（如总结当前目录结构）
3. 报错先检查 `model_provider` 名称、`base_url`、环境变量
4. 认证错误先切回备份配置

---

## 方案二：Codex++（推荐）

### 适合人群
- 主要用 Codex 桌面 App
- 不想手写配置文件
- 想随时切回官方模式
- **需要插件功能**（方案一做不到）

### 安装步骤

**1. 下载安装包**
- 打开 Codex++ Releases
- 下载两个安装包：「Codex++ 管理工具」和「Codex++ app」

**2. 安装管理工具**
- 首次打开若弹错误，去「系统设置」-「隐私与安全性」-「仍要打开」
- 确认检测到 GPT 登录状态

**3. 添加中转配置**
- 选「供应商配置」- 添加供应商
- 填写 Base URL 和 Key
- 接入方式选「纯API」
- 模型列表可从上游自动获取

**4. 从 Codex++ 启动**
- 必须从 Codex++ 启动，不是原版 Codex
- 重启后看到自定义模型供应商生效
- 插件功能可用

### 回滚方法
- 在管理工具里清除 API 模式，切回官方配置
- Codex 更新后 Codex++ 不适配，等适配即可，不影响原版

---

## 方案三：CCX + CC Switch

### 适合人群
- 有多个国产模型 API、多个中转服务、多个 Key
- 上游只支持 Chat Completions，需要转换成 Responses API
- 重度玩家

### 架构说明
- **CCX**: API 代理网关，负责协议转换和路由
- **CC Switch**: 桌面管理工具，一键切换供应商配置

### 第1步：部署 CCX

```bash
docker run -d \
  --name ccx \
  -p 3000:3000 \
  -e PROXY_ACCESS_KEY=your-proxy-access-key \
  -e APP_UI_LANGUAGE=zh-CN \
  -v $(pwd)/.config:/app/.config \
  crpi-i19l8zl0ugidq97v.cn-hangzhou.personal.cr.aliyuncs.com/bene/ccx:latest
```

启动后浏览器打开 `http://localhost:3000` 即可看到管理界面。

### 第2步：添加上游渠道

在 CCX 管理界面：
1. 选择上游服务类型
2. 填 API Key 和 Base URL
3. 配置模型映射和路由规则
4. 测试确认能通

**关键**: Codex 需要 Responses API 入口，CCX 会帮你做协议转换。

### 第3步：安装 CC Switch

```bash
npm install -g cc-switch
cc-switch init
```

初始化时填入 CCX 的地址作为中转入口。

### 第4步：切换配置并启动

```bash
cc-switch use <配置名>
```

重启 Codex 即生效。

---

## 常见踩坑排错表

| 现象 | 先检查什么 |
|------|-----------|
| 切换后没生效 | 是否完全重启了 Codex，model_provider 名称是否一致 |
| 报认证错误 | API Key 是否有效，环境变量是否被当前 shell 继承 |
| 报接口路径错误 | base_url 是否只写到 /v1，别重复拼 /responses |
| 国产模型无响应 | 上游是否支持 Responses API，不支持就得用 CCX 转换 |
| 插件配置不见了 | 切换工具是否覆盖了配置，有没有提前备份 |

---

## 关联资源

- **原文**: https://mp.weixin.qq.com/s/Qvfr9LC2wF9ltCEyKFqK3g
- **作者**: 苍何
- **CodexGuide**: 教程同步上线