# Bunx 安装与微信 MCP 配置

> 原始来源：`bunx使用步骤.docx`
> 整理日期：2026-06-12

## 安装 bunx

```powershell
npm install bunx
```

## 配置 CodeBuddy MCP

编辑 CodeBuddy 的 MCP 配置文件，添加 wechat server：

```json
"wechat": {
  "command": "bunx",
  "args": ["mcp-wechat-server"]
}
```

保存后重启 CodeBuddy。

## 使用

与 CodeBuddy 对话，使用 `mcp-wechat-server` 连接微信。
