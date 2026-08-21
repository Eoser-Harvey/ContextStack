# 框架维护经验

> 工具脚本 bug 修复、框架演进决策、跨系统协作规则。独立于具体 AI 工具，换 AI 也能用。

---

## 记忆系统分工（2026-07-31 确立）

| 系统 | 归属 | 用途 | 生命周期 |
|:-----|:-----|:-----|:---------|
| `.workbuddy/memory/` | AI 当前工作记忆 | 每日工作流水账、临时决策记录 | 随 AI 工具迁移（CodeBuddy/WorkBuddy） |
| `03-Memory/` | 框架长期资产 | 可复用经验、方法论、维护记录 | 永久，换 AI 也能用 |
| `MEMORY.md` | 索引层 | 四类记忆快速检索 | 永久 |

**同步规则**：`.workbuddy/memory/` 中有价值的内容（工具修复、架构决策、维护经验）**必须同步沉淀到 03-Memory/**，不是两边各写各的。

---

## 工具维护记录

### Git 仓库治理 + auto_push 编码加固（2026-08-18）

**背景**：框架体检发现 `.git` 有 23 个垃圾对象 + 21 个孤儿 .idx、size-pack 336MB；全历史有 1 条中文乱码 commit。

**修复三处**：
1. `git gc --prune=now`：垃圾对象 23→0，4 个 pack 合并为 1 个
2. `.gitignore` `"*.html"` 引号 bug → `*.html`（gitignore 不支持引号包裹，原 pattern 从未生效，html 被误跟踪）
3. `auto_push.ps1` 提交改 `git commit -m` → `git commit -F` + UTF-8 消息文件（`[System.IO.File]::WriteAllText(..., UTF8Encoding($false))`），杜绝 GBK 控制台把中文写乱码

**乱码根因**：仅 1 条（80bc201，`docs:` 前缀），非 auto_push 产生，是某台电脑 GBK 控制台手动 `git commit -m "中文"` 所致。历史修复需 rebase+force push，仅 1 条不值得，留着当纪念。

**体积根因（未解决，待决策）**：373MB 非垃圾而是二进制入库——>500KB blob 共 153 个（腾讯云培训 44MB PDF / 13MB zip、role-model 277 个 PDF）。瘦身需 `git filter-repo` 重写历史 + force push + 家里电脑重新克隆，已给用户 A/B 方案待选。

**教训**：①git 仓库健康度纳入定期体检；②大文件（PDF/图片/zip）入库前先判断是否进 `.gitignore` 或走外部存储，不无脑 `git add -A`。

---

### auto_push.ps1 中文文件名 commit 失败 bug（2026-07-29 修复）

**根因**：脚本 Step 4 从 `git status --porcelain` 提取目录名时未清洗引号——git 对中文文件名加引号输出（`M  "01-Projects/.../嵌入式AI笔记...md"`），残留引号混入 commit message，PowerShell 传参时引号边界被破坏，git 把 message 片段 `(no-ext)` 误认为 pathspec。

**修复**：dirs/exts 提取处加 `-replace '"',''`（2 行改动，commit d0bb077）。

**验证**：①模拟中文文件名输出 → message 干净无引号 ②git commit 解析正常。

**教训**：近 3 周含中文文件名的自动提交全部静默失败（7-10、7-17、7-28 共 3 次），未丢数据（靠手动 push 带走）。**自动备份系统缺失败告警机制**——连续 2 次失败时应生成桌面提醒或推送通知。

---

### .gitignore 新增 .workbuddy/（2026-07-28）

**背景**：`.workbuddy/memory/` 是 AI 工作记忆目录，不应入库（与 `.codebuddy/` 同类）。

**规则**：`.workbuddy/` 加入 `.gitignore` IDE 区，每晚 22:00 auto_push.ps1 的 `git add -A` 不会误提交。

---

### MEMORY.md 瘦身（2026-07-31）

**问题**：行为约束区 17 行索引 + 24 行 GLOBAL-RULES.md 复制内容，两层冗余。

**修复**：索引表 17 行→8 行（合并同类项，摘要 ≤15 字，统一指向 GLOBAL-RULES.md）；删除正文复制内容，只留一行索引说明。

**原则**：MEMORY.md 只做索引，正文权威源 = GLOBAL-RULES.md。

---

## 框架演进决策

### 学习讨论收尾纪律（2026-07-28 新增，GLOBAL-RULES.md v3.2）

**触发**：技术讨论连续追问 ≥3 层，或讨论已覆盖"原理→对比→设计决策"完整知识链。

**动作**：主动提醒停止提问，转向"合上文档，用自己的话复述"；给出明确复述目标。

**考核**：用户复述时，AI 按面试官标准打分（百分制）+ 挑刺（✓⚠❌标注/术语硬伤点名/修正骨架/卡壳二次作业/80 分通过）。

**原理**：文档里存的是 AI 的输出，能讲出来才是用户的资产；警惕"收藏式学习"。

---

### 文件操作红线历史教训（持续记录）

- **2026-05-19**：误删 btc-temperature-gauge 的 server.py/server.js → 只删/改自己创建的文件
- **2026-07-06**：擅改 beijing-company-social-insurance-plan.md → 修改用户文件必须明确授权
- **2026-07-08**：擅移 25 个 PDF 并删 laoxue 文件夹 → 未经明确授权不执行写盘/移动/删除（含修正自己误创建的文件）

---

## 相关
- [[../index|03-Memory 索引]]
- [[../../GLOBAL-RULES|全局规则]]
- [[../../MEMORY|MEMORY.md 索引]]
