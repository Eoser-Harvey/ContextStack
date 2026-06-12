# OpenSpec Skill — 使用说明

## 基本信息
- **Skill名称**：openspec
- **来源**：Fission AI 开源项目（5万+ Stars）
- **类型**：npm 全局 CLI 工具
- **作用域**：项目级
- **安装日期**：2026-06-12
- **版本**：v1.4.1

## 功能描述
OpenSpec 是**规范驱动开发（SDD）**框架。核心思路：先用 `.md` 规范文件锁定需求，再让 AI 按规范写代码，避免"AI 乱写"。

## 安装

```bash
npm install -g @fission-ai/openspec@latest
# 验证
openspec --version
```

## 在项目中初始化

```bash
cd 你的项目目录
openspec init
```

初始化时会提示选择 AI 工具（CodeBuddy 原生支持），选中后项目根目录生成 `openspec/` 文件夹和 `AGENTS.md`。

## 目录结构

```
项目/
├── openspec/
│   ├── specs/          # 项目规范（按能力组织，持久化）
│   │   └── auth-login/
│   │       └── spec.md
│   └── changes/        # 每次变更提案（临时，完成后归档）
│       └── dark-mode/
│           ├── proposal.md
│           └── tasks.md
└── AGENTS.md           # 自动注入到 AI 上下文的指令
```

## 核心工作流：propose → apply → archive

### 实操示例（以 family-investment 项目为例）

**前置**：在项目目录执行 `cmd /c "openspec init --tools codebuddy"`，完成后重启 IDE。

**第1步 — 提需求**：在 CodeBuddy 对话中输入：
```
/opsx:propose 给投资报告增加月度净资产趋势图，横轴月份纵轴净值
```
OpenSpec 会读取现有 `specs/`，生成 `changes/net-worth-chart/proposal.md` 和 `tasks.md`。

**第2步 — 审阅规范**：
```
/opsx:explore 净值图的 Y 轴要显示绝对金额还是涨跌幅？数据源用哪个文件？
```
AI 会追问细节，你确认后更新 spec。

**第3步 — 写代码**：
```
/opsx:apply
```
AI 严格按 spec.md 实现代码，每完成一个 task 就标记 `[x]`。

**第4步 — 验证**：
```
/opsx:verify
```
检查代码是否符合规范，生成验证报告。

**第5步 — 归档**：
```
/opsx:archive
```
将完成的变更合并到 `specs/`，删除临时 `changes/` 目录。

### 命令速查

| 命令 | 作用 |
|------|------|
| `/opsx:propose "描述需求"` | 创建变更提案，AI 生成 proposal.md |
| `/opsx:explore "问题"` | 在写代码前打磨规范，澄清细节 |
| `/opsx:apply` | 按规范写代码，逐步完成 tasks.md |
| `/opsx:verify` | 验证实现是否符合规范 |
| `/opsx:archive` | 归档完成的需求到 specs/ |

## 与 ContextStack 现有 Skills 的关系

| ContextStack Skill | OpenSpec 对应 | 关系 |
|------|------|------|
| **brainstorming** | `/opsx:propose` + `/opsx:explore` | OpenSpec 将设计文档结构化并注入 AI 上下文 |
| **writing-plans** | `tasks.md` | OpenSpec 自动生成分步实现任务 |
| **karpathy-guidelines** | 互补 | OpenSpec 管需求层面的约束，karpathy 管编码层面的约束 |
| **pua-governance** | `/opsx:verify` | OpenSpec 提供自动化验证机制 |

> OpenSpec 和 ContextStack 不是替代关系，而是互补：ContextStack 管理**跨项目**的长期记忆和规则，OpenSpec 管理**单个项目内**的需求规范和变更流程。

## 适用场景

- 新功能开发（脑暴→规范→代码）
- 重构（先写目标规范，再逐步迁移）
- 多人/多会话协作（规范作为共识文档）
- AI 生成的代码需要严格审查的场景

## 常见问题

**Q: 和直接让 AI 写代码有什么区别？**
A: 直接写代码 AI 容易跑偏。OpenSpec 先把需求写成 `.md` 规范，AI 读规范再写，可验证可追溯。

**Q: 适配存量项目吗？**
A: 适配。`openspec init` 后，用 `/opsx:propose` 描述存量项目的首个需求即可开始。

---

> **安装位置**：全局 npm（`C:\Users\h31280\AppData\Roaming\npm\`）
> **相关文档**：[已有 SDD 工具对比](./sdd-tools-comparison.md)
