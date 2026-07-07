---
title: 微信公众号批量下载工具 wechatDownload
tags:
  - tool-config
  - wechat
  - crawler
summary: 基于 PC 微信登录态批量下载公众号全部历史文章的开源 GUI 工具（qiye45/wechatDownload），支持导出 Markdown/HTML/PDF/Word
created: 2026-07-07
updated: 2026-07-07
---

# 微信公众号批量下载工具 wechatDownload

## 说明

抓取某个微信公众号的**全部历史文章**并批量导出。微信对"历史文章列表"接口做了登录态校验，纯无登录态抓取只能拿到空壳（已实测：profile_ext 主页和文章内链均被反爬挡住）。本工具通过 **PC 微信客户端**获取登录态（key/cookie），绕过限制，是成本最低的方案。

## 基本信息

- **项目**：[qiye45/wechatDownload](https://github.com/qiye45/wechatDownload)
- **作者**：qiye45（GitHub）
- **当前版本**：4.6（Release 页：https://github.com/qiye45/wechatDownload/releases/tag/4.6）
- **类型**：Windows / macOS GUI 程序（无命令行接口，4.x 起支持 MCP/Skill 调用）
- **本地存放**：`D:\wechatDownload\微信公众号批量下载工具4.6.exe`
  - 解压目录 `D:\wechatDownload\` 还含 `缓存\docx.exe`、`缓存\pdf.exe`（文档格式转换依赖）

## 工作原理

1. 文章列表来自微信内部接口：
   ```
   GET https://mp.weixin.qq.com/mp/profile_ext?action=getmsg
       &__biz=<biz>&f=json&offset=0&count=10
   ```
   该接口**必须带登录态 cookie（uin / key / pass_ticket）**，否则返回"请在微信客户端打开链接"。
2. 单篇文章短链 `mp.weixin.qq.com/s/<token>` 不需登录态可读，但**列表接口不行**——所以"读全部文章"= 拿到 PC 微信的登录态。
3. 工具做法：PC 微信打开一篇公众号文章时，工具 hook 该页面、提取 key，从而调用 getmsg 接口翻页拉取全部历史文章。

## 使用 SOP（GUI，需人工点）

> 关键两步必须人工操作：① 取 key（在 PC 微信里做，要用户登录态）；② 选公众号+导出（在工具窗口里点）。AI 无法代做图形界面与登录态。

1. 确认 **PC 微信已登录**（本机正常登录着）。
2. 在 PC 微信里打开目标公众号**任意一篇文章**（从订阅号消息点开，勿用系统浏览器）。
3. 工具自动捕获该文章页的 key，关联上这个公众号（若界面有"监听微信/自动捕获"开关，确保开启）。
4. 回到工具窗口，找到/搜索到目标公众号。
5. 选中 → 点「获取文章列表 / 批量下载」→ 导出格式选 **Markdown**。
6. 跑完（文章多需几分钟），记录导出目录路径。

## 本次用途

- 目标公众号：**「老薛的晨间日记」**（biz=`MzI0NzcwODc5NQ==`）
- 目的：抓取其全部历史文章，提炼要点、写进知识框架（目前仅有一篇转发稿《毕业十年｜每一步都算数》已入库，缺逐年细化数据与打新/社群/AI 等专题文）。

## 下载方式（国内可达）

- 直链：`https://github.com/qiye45/wechatDownload/releases/download/4.6/wechatDownload4.6.zip`
- 代理镜像（直链慢时用）：`https://ghproxy.net/https://github.com/qiye45/wechatDownload/releases/download/4.6/wechatDownload4.6.zip`
- 注：本机 `github.com` 主站超时，但 `api.github.com` 与 `objects.githubusercontent.com` 可达；可用 `api.github.com/repos/qiye45/wechatDownload/releases/assets/<id>`（带 `Accept: application/octet-stream`）走 302 跳转下载。

## 注意事项

1. **第三方工具触及微信登录态**，使用前建议先读仓库 README 与免责声明，自行评估安全与隐私风险。
2. 需 **PC 微信客户端在运行**，且文章要在微信内打开（非浏览器）才能取 key。
3. 导出后 Markdown 可能含图片/样式，需人工核对正文完整性。
4. 仅用于个人备份与学习，遵守平台与版权规范。

## 相关

- [[index|工具配置索引]]
- 同类方案参考（未采用）：hzhu212/wechat-mp-crawler（需 Fiddler 抓包）、wechat-article-exporter（需自有公众号后台）、wewe-rss（微信读书 session）。
