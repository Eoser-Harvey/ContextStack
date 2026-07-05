# ContextStack 协作框架总览

> 一个独立于特定AI助手的、基于分层Context和持久化Memory的通用协作协议

## 核心理念

### 框架独立性
- **不绑定任何AI模型/产品**：本框架不与Claude、GPT等任何特定AI助手绑定
- **通用协作协议**：定义了一套通用的"分层Context加载 + 持久化Memory"协作协议
- **可移植资产**：您积累的规则、记忆、工作台均为持久化资产，可在不同AI助手间迁移和复用
- **积累自有框架**：核心价值在于积累您自己的协作框架，而非依赖某个特定AI

### 设计哲学
```
单一入口 + 分层Context + 工作台持久化
    → 避免Agent割裂，通过Context切换实现专注
    → 记忆连续性，知识可沉淀，协作高效率
```

## 四层架构详解

### 第一层：全局规则 (`GLOBAL-RULES.md`)
- **路径**: `GLOBAL-RULES.md`
- **作用**: 定义"我是谁" - 身份、沟通风格、铁律、安全红线、操作授权范围
- **触发**: AI助手启动时自动加载
- **特点**: 常驻内存，最高优先级，不可覆盖

### 第二层：项目规则 (`{项目路径}/PROJECT-RULES.md`)
- **路径**: 各项目根目录下的`PROJECT-RULES.md`
- **作用**: 定义"哪个项目" - 项目规范、领域知识、目录结构、产品红线
- **触发**: 切换到项目/话题工作台时动态加载
- **特点**: 受全局规则约束，支持多项目上下文切换

### 第三层：规范文档库 (`02-Knowledge/system/`)
- **路径**: `02-Knowledge/system/`
- **作用**: 提供"如何做"的知识 - 方法论、SOP、模板、调研框架
- **触发**: 执行具体任务需要方法论时按需读取
- **特点**: 属于"知识"而非"规则"，主动加载，不常驻内存

### 第四层：持久化Memory (`MEMORY.md`表格索引)
- **路径**: `MEMORY.md`
- **作用**: 记录"在做什么" - user、feedback、project、reference四类记忆
- **触发**: 持续更新（开始/完成/切换时）
- **特点**: 索引式管理，详细信息在工作台，跨session持久化

## 工作台系统 (`01-Projects/`)

### 核心功能
- **Session持久化**: 记录"做到哪了"，支持跨会话恢复
- **话题切换**: 通过工作台暂存和恢复实现不同话题/项目间快速切换
- **状态管理**: 记录项目状态、任务进度、讨论历史、决策记录

### 项目标准文件
1. **WORKSPACE.md** — 工作台入口 + 导航
2. **STATE.md** — 最新状态 (✅⚠️📌❓)
3. **ACTIONS.md** — 任务清单与进度
4. **CONTEXT.md** — 稳定背景与约束
5. **REFERENCES.md** — 资料链接

### 工作台类型
1. **项目工作台** (`01-Projects/`): 长期项目跟踪
2. **话题工作台** (`01-Projects/topics/`): 特定技术话题讨论

### 切换命令
- `切换到[项目/话题名称]` / `Switch to [project/topic name]`
- `暂存[名称]工作台` / `Save [name] workbench`
- `恢复[名称]工作台` / `Restore [name] workbench`
- `结束会话` / `End session`

## 目录结构

```
ContextStack/
├── GLOBAL-RULES.md              # 第一层：全局规则
├── MEMORY.md                    # 第四层：Memory表格索引
├── FRAMEWORK-README.md          # 本文档：框架总览
├── 01-Projects/                 # 项目工作台（6标准文件/项目）
│   ├── embedded-ai-learning/
│   │   ├── WORKSPACE.md         # 工作台入口
│   │   ├── STATE.md             # 最新状态 ✅⚠️📌❓
│   │   ├── ACTIONS.md           # 任务清单
│   │   ├── CONTEXT.md           # 稳定上下文
│   │   ├── REFERENCES.md        # 参考资料
│   │   └── PROJECT-RULES.md     # 第二层：项目规则
│   ├── network-device-debug/
│   ├── btc-temperature-gauge/
│   ├── tencent-cloud-training/
│   ├── wechat-radar/
│   ├── family-hub/
│   └── topics/
├── 02-Knowledge/                # 知识库
│   ├── system/
│   │   ├── methodology/
│   │   ├── sop/
│   │   ├── research-frameworks/
│   │   └── tool-configurations/
│   ├── career-development/      # 职业发展（面试/策略/公司分析）
│   ├── skills/                  # 可复用 Skills
│   └── inbox/                   # 每日收件箱
├── 03-Memory/                   # 结构化记忆文件
│   ├── knowledge/               # 知识级记忆
│   ├── personal/                # 个人备忘
│   ├── projects/                # 项目级记忆
│   └── sessions/                # 会话级记忆
├── 04-Templates/                # 模板库
│   ├── project/                 # 项目五文件模板
│   └── project-rules-template.md
├── 05-Tools/                    # 维护工具脚本
│   ├── backup/                  # 备份 & 自动同步
│   ├── encoding/                # 编码处理
│   ├── diagnostics/
│   ├── fileops/
│   └── vscode-config/           # VSCode 配置管理
```

## 快速接入指南

### 新AI助手接入步骤
1. **读取全局规则**: 加载`GLOBAL-RULES.md`
2. **理解四层架构**: 阅读本文档`FRAMEWORK-README.md`
3. **检查当前项目**: 识别用户当前工作目录
4. **加载项目规则**: 如果存在`PROJECT-RULES.md`则加载
5. **初始化Memory**: 读取`MEMORY.md`了解上下文
6. **等待用户指令**: 准备接收任务

### 日常协作流程
```
用户指令
    → 分析任务类型和上下文需求
    → 按需加载规范文档（第三层）
    → 执行任务（使用工具、编辑文件）
    → 更新工作台状态（Session持久化）
    → 必要时更新Memory索引（第四层）
    → 报告结果
```

### 话题切换流程
```
保存当前工作台状态
    → 清理不相关Context
    → 加载新项目规则（第二层）
    → 打开对应工作台文件
    → 恢复相关Memory上下文
    → 继续工作
```

## 文件命名规范

### 原则
- **目录和文件名**: 使用英文，便于跨平台移植和工具兼容
- **文件内容**: 使用中文，便于您阅读和理解
- **命名格式**: 小写字母、数字、连字符，避免空格

### 示例
- ✅ `01-Projects/embedded-ai-learning/`
- ✅ `02-Knowledge/system/methodology/debug-methodology.md`
- ✅ `02-Knowledge/skills/vscode-config-management/vscode-config-management-guide.md`

## 关键配置项

### 路径配置（必须保持一致）
```markdown
# 在GLOBAL-RULES.md中定义
- Skill保存路径: `02-Knowledge/skills/`
- VSCode配置路径: `05-Tools/vscode-config/`
- 项目路径: `01-Projects/`
- 知识库路径: `02-Knowledge/`
- Memory索引路径: `MEMORY.md`
```

## 协作角色定位

### 您（用户）
- **角色**: 项目决策者 + 任务发布者
- **职责**: 明确需求、提供上下文、审核重要变更、管理Memory更新
- **特点**: 像老板一样发号施令，AI助手具体执行

### AI助手（任何适配本框架的AI）
- **角色**: 专业编程助手 + 技术顾问
- **职责**: 理解需求、执行任务、维护记忆、更新工作台
- **特点**: 同一个"我"，通过Context切换适配不同场景

## 最佳实践

### 新项目接入
1. 创建项目目录和`PROJECT-RULES.md`规则文件
2. 创建工作台文件（基于模板）
3. 更新Memory索引
4. 按需创建规范文档

### 日常使用
1. 使用`切换到`命令明确切换上下文
2. 重要变更后及时更新工作台状态
3. 定期更新Memory索引
4. 使用规范文档作为知识参考

### 知识沉淀
1. 成功经验记录到规范文档库
2. 问题解决方案记录到Memory
3. 常用操作沉淀为Skill
4. 定期整理和优化框架

---

**框架版本**: v3.0
**创建时间**: 2026-04-30
**最后更新**: 2026-06-10
**变更**: family-investment→family-hub 升级为家庭决策枢纽；目录树同步实际结构；补全 wechat-radar 项目、images/ 目录；移除已合并的 system/templates/；03-Memory/ 子目录完善
**设计原则**: 独立于AI助手、分层Context、持久化Memory、工作台驱动
**文件规范**: 英文目录/文件名，中文文件内容
**核心价值**: 积累您自己的通用协作框架，提升长期协作效率

## 框架落地状态

| 阶段 | 状态 | 要点 |
|------|------|------|
| L1 全局规则 | ✅ 完成 | GLOBAL-RULES.md + Skills rules |
| L2 项目规则 | ✅ 完成 | 6个项目均有 PROJECT-RULES.md |
| L3 规范文档 | 🔄 充实中 | methodology / SOP / 调研框架已具，待深化 |
| L4 Memory | ✅ 可用 | MEMORY.md 索引 + 03-Memory/ 结构化记忆 |
| 工作台系统 | ✅ 运行中 | 6个活跃项目、6标准文件模板 |
| 模板层 | ✅ 完成 | 04-Templates/ 统一管理所有模板 |
| 工具链 | ✅ 完备 | 备份自动化 / 编码修复 / Git同步 |

### 风险备忘

| 风险 | 应对 |
|------|------|
| 编码问题导致文件损坏 | 定期备份，UTF-8编码 |
| 规则冲突 | 全局规则不可覆盖 |
| Memory膨胀 | 定期归档，清理过时记忆 |
| 框架与AI助手绑定 | 保持框架独立性，通用格式 |

### 成功指标
1. 所有活跃项目有完整 PROJECT-RULES.md
2. Memory索引准确反映项目状态
3. 规范文档能有效指导工作
4. 项目/话题切换在合理时间内完成

> **原 `ContextStack协作架构-落地计划.md` 和 `ContextStack协作架构-交互协议.md` 已合并/删除，此段为仅存状态摘要。**
