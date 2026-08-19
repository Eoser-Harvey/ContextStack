# 知识库 (02-Knowledge)

ContextStack 的知识管理中心，存放规范文档、技能模块和知识笔记。

## 目录结构

| 目录 | 用途 | 文件数 |
|------|------|--------|
| [system/](./system/) | 系统规范文档 — 方法论、SOP、调研框架、工具配置 | 19 |
| [skills/](./skills/) | 可复用技能模块（每个 skill 独立文件夹，20 个子目录） | 62 |
| [career-development/](./career-development/) | 职业发展知识库 — 面试记录、职业画像、项目设计、嵌入式基础、盖洛普测评 | 217 |
| [inbox/](./inbox/) | 每日收件箱 — 未消化内容暂存区（含 role-model 子目录 408 文件，⚠️ 待清理，详见下文） | 466 |

---

## system/ — 系统规范

| 子目录 | 内容 |
|--------|------|
| `methodology/` | 调试方法论 |
| `sop/` | 项目接入 SOP |
| `research-frameworks/` | 技术调研框架 |
| `tool-configurations/` | VSCode 配置备份、自动备份脚本、settings.json |

根目录文件：`knowledge-sharing.md`、`trae-skills-reference.md`

---

## skills/ — 技能模块（20 个子目录）

| Skill | 用途 |
|-------|------|
| `0.trae-wechat-push` | Trae 微信推送（含缓存/历史/翻译/档案） |
| `ai-berkshire` | AI Berkshire 投资研究套件（公司研究/财报/行业/组合） |
| `bazi-ziwei` | 八字紫微排盘（含水墨风HTML海报） |
| `brainstorming` | 头脑风暴 |
| `browser-automation` | 浏览器自动化（含离线包打包） |
| `device-debugging` | 设备调试 |
| `find-skills` | 技能发现 |
| `interview-prep` | 面试准备（输入公司名生成 8 模块清单） |
| `karpathy-guidelines` | Karpathy 编码准则（always 自动生效） |
| `lanqichang` | 蓝启长（待补充说明） |
| `network-packet-analysis` | 网络抓包分析 |
| `openspec` | OpenSpec 规范 |
| `pua-governance` | PUA 治理（manual） |
| `qiuxing` | 求行（待补充说明） |
| `systematic-debugging` | 系统化调试（manual） |
| `tsn-protocol` | TSN 时间敏感网络协议 |
| `vscode-config-management` | VSCode 配置管理 |
| `wangchuan` | 网传（待补充说明） |
| `wechat-cli` | 微信命令行 |
| `writing-plans` | 写作计划 |

> 根目录另有：`awesome-agent-skills-resources.md` / `codebuddy-builtin-skills-analysis.md` / `sdd-tools-comparison.md` / `skills-building-best-practices.md` / `视频号下载方案对比.md` / `视频转文字方案对比.md`

---

## career-development/ — 职业发展

| 子目录 | 内容 |
|--------|------|
| `career-strategy/` | 职业策略（端侧 AI 企业定制攻略） |
| `interview-project-summaries/01-company-interviews/` | 公司面试记录（九号/ISHO/思朗等） |
| `interview-project-summaries/02-interview-prep/` | 面试准备（职业画像、技术笔记） |
| `interview-project-summaries/03-project-design/` | 项目设计（AcuOS 源码、DSP 模块图、Gerrit-Jenkins CI/CD） |
| `interview-project-summaries/04-embedded-fundamentals/` | 嵌入式基础（RTOS 笔记、嵌入式 AI、C++ 基础） |

---

## inbox/ — 每日收件箱

> 未消化内容暂存区。所有整理产物保留在此目录，用户手动要求时才移入对应知识分区。
> 归档记录见 [inbox/archive/archive-log.md](./inbox/archive/archive-log.md)

### 内容分类统计（2026-08-20 重计）

| 分类 | 文件数 | 最新更新 | 备注 |
|------|--------|----------|------|
| AI/技术 | 25+ | 2026-07-16 | 含 Codex/Agent/Skill 设计/视频创作 |
| 投资理财 | 18+ | 2026-07-30 | 含 BTC熊市穿越者反思/嘉信/港美股 |
| 个人成长 | 6+ | 2026-07-18 | 含 Tina Seelig 培养运气/个人成长产品化 |
| 商业模式 | 3+ | 2026-07-15 | 生财有术 Agent 时代策略 |
| 健康/生活 | 2+ | 2026-07-18 | 海外号/giffgaff |
| 生活工具 | 4+ | 2026-07-14 | libtv/social-auto-upload/codex 国内接入 |
| **根目录 .md 合计** | **60+** | — | ⚠️ 已超 30 条阈值，建议清理 |

### ⚠️ 待处理问题（2026-08-20 重新识别）

- **inbox/ 根目录 .md 60+ 条堆积**（超过框架 30 条阈值）→ 建议逐条归档或删除
- **inbox/role-model/ 子目录 408 文件**（277 PDF + 94 jpg + 28 md + 5 png + 3 docx + 1 json）→ 疑似外部源（如老薛课程 PDF）误入框架，违反"外部交付物写外部路径"规则，需用户审视后决定是否移回外部目录
- **inbox/professional-technology/** 子目录内容待识别

---

## 相关入口

- 全局规则：`../GLOBAL-RULES.md`
- Memory 索引：`../MEMORY.md`
- 框架总览：`../FRAMEWORK-README.md`
- Inbox 归档日志：`./inbox/archive/archive-log.md`

---

**最后更新**: 2026-08-20
**变更**: 同步实际目录结构（skills 17→20 子目录，inbox 40→60+ 文件，career-development 32→217）；新增 role-model/professional-technology 子目录警告
