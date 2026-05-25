# Agent Harness 最小结构解析

> 来源: 微信公众号（Datawhale干货，作者：陈思州）  
> 原文: https://mp.weixin.qq.com/s/yVFQej3dFk9KHv6J2u6Lew  
> 收集日期: 2026-05-24  
> 分类: AI / 技术

---

## 核心观点

> **Agent = model + harness**

Harness 是把 Agentic model 放进一个**可运行、可记录、可评分**的小环境里。

---

## Mini Harness 五模块

| 模块 | 作用 | 说明 |
|------|------|------|
| **Task** | 任务输入 | 明确的目标和要求 |
| **Environment** | 可操作环境 | 代码仓库、文件组等 |
| **Tools** | 工具接口 | read_file、list_files、run_tests 等 |
| **Trace** | 执行记录 | 每一步的工具调用、参数、返回值 |
| **Grader** | 评分器 | 判断成功/失败，给出原因 |

---

## Eval Case 示例结构

```json
{
  "id": "case_001",
  "task": "判断项目是否支持插件系统",
  "environment": { "files": { "README.md": "...", "config.md": "..." } },
  "tools": ["list_files", "read_file"],
  "grader": {
    "must_read": ["README.md"],
    "answer_should_include": "不能确认支持插件系统",
    "answer_should_not_include": "支持插件系统"
  }
}
```

---

## Trace 记录示例

```json
{
  "case_id": "case_001",
  "trace": [
    { "tool": "list_files", "arguments": {"path": "."}, "result": ["README.md", "config.md"] },
    { "tool": "read_file", "arguments": {"path": "README.md"}, "result": "..." }
  ],
  "answer": "当前 README 没有插件系统相关说明，不能确认支持插件系统。",
  "grade": { "success": true, "reason": "读取了 README，回答没有超出文件内容。" }
}
```

---

## 公开参考资料

| 资料 | 核心价值 |
|------|----------|
| **Anthropic Agent Evals** | eval harness vs agent harness 的区分 |
| **SWE-agent** | Agent-Computer Interface 设计 |
| **Terminal-Bench** | 任务结构：instruction + 隔离环境 + 测试脚本 |
| **SWE-bench** | coding agent 评测流程：issue → patch → 测试 |

---

## 与 ContextStack 的关联与借鉴

### 直接对应关系

| Harness 模块 | ContextStack 对应 | 成熟度 |
|-------------|-----------------|:------:|
| **Task** | 用户指令 / 工作台任务 | ✅ 已有 |
| **Environment** | 项目文件夹 / 文件系统 | ✅ 已有 |
| **Tools** | 文件操作 / 命令执行 / Web搜索 | ✅ 已有 |
| **Trace** | ❌ **缺失** | ❌ 没有 |
| **Grader** | ❌ **缺失** | ❌ 没有 |

### 关键借鉴：Trace（执行记录）

ContextStack 目前**没有 Trace 机制**。每次会话结束后，执行过程就丢失了。

**建议增加**：
- 每次任务记录：用户指令 → AI 执行步骤 → 工具调用 → 产出文件
- 存储位置：`memory/trace/` 或 `workbench/trace/`
- 格式参考文章的 JSON trace 结构

### 关键借鉴：Grader（评分/复盘）

ContextStack 目前**没有任务评分机制**。

**建议增加**：
- 任务完成后自评：目标是否达成？哪些步骤多余？哪些可以改进？
- 存储位置：`memory/feedback/`（已有 feedback 目录，可利用）
- 与 inbox 处理日志结合：每次整理后记录质量自评

### 关键借鉴：Eval Case（测试用例）

可以为 ContextStack 的核心流程写 eval case：

| 测试场景 | Task | Grader |
|---------|------|--------|
| inbox 处理 | 收集链接 → 整理 → 归档 | 检查三个文件是否都创建 |
| 项目切换 | 切换到 embedded-ai-learning | 检查 PROJECT-RULES.md 是否加载 |
| Memory 更新 | 完成任务后更新 MEMORY.md | 检查索引是否同步 |

---

## 对 ContextStack 框架的具体提升建议

### 1. 增加 Trace 层（优先级：高）

```
memory/
├── trace/
│   ├── 2026-05-24-session-001.md   # 会话级执行记录
│   └── trace-template.md           # Trace 模板
```

Trace 模板：
```markdown
## Session: YYYY-MM-DD-NNN
- **任务**: xxx
- **工具调用**: 
  1. Read(file) → ...
  2. Write(file) → ...
  3. WebFetch(url) → ...
- **产出**: xxx.md
- **耗时**: N 分钟
- **自评**: 成功/部分成功/失败
```

### 2. 增加 Grader 机制（优先级：中）

每次 inbox 处理后自评：
- 信息提取是否完整？
- 分类是否准确？
- 索引是否同步更新？
- 有无遗漏步骤？

### 3. 增加 Eval Case（优先级：低）

为核心流程写最小测试用例，定期验证框架运行质量。

---

## 总结

| 维度 | ContextStack 现状 | 借鉴后 |
|------|------------------|--------|
| **可运行** | ✅ 已有 | — |
| **可记录（Trace）** | ❌ 缺失 | ✅ 增加 trace 层 |
| **可评分（Grader）** | ❌ 缺失 | ✅ 增加自评机制 |
| **可复现** | 部分（有 MEMORY.md） | ✅ trace + eval case |
