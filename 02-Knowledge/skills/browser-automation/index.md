# 浏览器自动化技能整理

> 2026-08-03 汇总三种浏览器自动化方案：CodeBuddy 内置 agent-browser、内置 playwright-cli、腾讯开源 BrowserSkill（bsk CLI）。

---

## 三方案对比

| | agent-browser | playwright-cli | BrowserSkill (bsk) |
|:---|:---|:---|:---|
| **来源** | CodeBuddy 内置 plugin | CodeBuddy 内置 plugin | 腾讯开源（GitHub Tencent/BrowserSkill，MIT） |
| **安装** | 无需安装，开箱即用 | 无需安装，开箱即用 | 下载 bsk CLI 二进制 + 浏览器扩展 |
| **浏览器** | 独立 Chromium 实例 | Playwright 内置 Chromium | **用户真实 Chrome/Edge**（复用登录态） |
| **核心优势** | 零配置 | 功能最全 | **免重复登录**（用你已登录的浏览器） |
| **适用场景** | 快速浏览/截图 | 表单填充/复杂交互/测试 | **含登录态网站**操作（银行/后台/社交媒体） |
| **局限性** | 无法复用登录态 | 无法复用登录态 | 需安装 CLI + 浏览器扩展 |

---

## BrowserSkill (bsk) 安装记录

- **版本**：bsk CLI 0.1.9（2026-07-29 Release）
- **下载**：`bsk-v0.1.9-x86_64-pc-windows-msvc.zip`（4.3MB）
- **安装路径**：`D:\Tools\bsk\bsk.exe`
- **扩展**：已从 Chrome 商店安装 ✅
- **launcher skill**：已从 SkillHub 安装 `bsk-browser-launcher` → `~/.workbuddy/skills-marketplace/skills/bsk-browser-launcher/` ✅
- **启动**：`bsk daemon`（后台驻留，监听 WebSocket，launcher skill 自动拉起）

### 常用命令

```bash
bsk --version     # 版本检查
bsk doctor        # 环境诊断
bsk daemon        # 启动后台进程
bsk start         # 启动浏览器控制会话
bsk stop          # 停止
bsk browse <url>  # 打开 URL
bsk click <sel>   # 点击元素
bsk snapshot      # 截图
bsk console       # 执行 JS 控制台命令
```

---

## 相关

- [GitHub 仓库](https://github.com/Tencent/BrowserSkill)
- [内置 Skills 索引](../index.md)
