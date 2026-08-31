# 会话经验模板

> 本次为 session-daily-catchup 自动化补齐（2026-08-31 当日活动沉淀）

---

## 元信息

- **会话日期**: 2026-08-31
- **对话主题**: 社区内容采集推送工具链搭建 + 千寻/嵌入式C面试准备 + LLM-Wiki 知识编译范式研究 + 北京公司账务更新
- **处理文件数**: 4 commits / 16 files（工作区已 clean，与 origin/master 无 ahead）
- **用户反馈**: 无（自动化补齐，无对话反馈）

---

## 做对了什么（保持）

1. **新建完整"社区采集→推送"工具链**：`01-Projects/.../6.community-collection-push/` 下落地 `collect_community.py`(483行采集) / `profile_loader.py`(账号画像加载) / `push_lark.py`(253行飞书推送) / `send_daily_ai_news.py`(447行每日AI资讯调度)，并配 `index.md` 说明 + `.gitignore`，职责分明。
2. **面试准备采用"分主题增量扩充"**：千寻智能 MS 清单补「自我介绍 + Linux 应用层能力 + 环形缓冲三连追问」，并新增 `embedded-c-algorithm-interview.md`（含 SyncE/PTP 时钟路线配图），结构清晰可持续追加。
3. **知识摄入走 inbox 暂存 + 范式提炼**：`02-Knowledge/inbox/LLM-Wiki-知识编译范式研究.md`(137行) 入库，保持"暂存→提炼→正式"的分层落位。
4. **.gitignore 忽略 Office 锁文件**：新增 `~$*.xlsx` 等规则，避免编辑 `信用卡主控表.xlsx` 时产生临时锁文件脏改动。

---

## 踩了什么坑（避免）

1. **工具链目录职责初建未定清**：`63d957c` 把 `send_daily_ai_news.py`(447行) / `profile_loader.py`(39行) 直接放进 `community-collection-push/`，随后 `0711674` 又整体删除重排（删 447+39 行）。属于"先散后收"——初建目录时未先界定"采集/推送/调度"边界，导致脚本位置来回搬。
2. （本日内容由 git 提交推断，对话中是否另有踩坑无法从纯提交判断，不臆造。）

---

## 下次怎么更快（优化）

1. **新工具链建目录前先画职责边界**：先定"采集 / 推送 / 调度"三类文件归属，再动手写，避免大文件来回搬。
2. **面试/文档类用模板分段**：千寻清单、嵌入式C面试文档都按固定小节（自我介绍/核心能力/高频追问/专项）组织，增量追加而非整篇重写。

---

## 可复用的模式

- **社区内容采集推送 SOP**：`collect_community.py`(采集) → `profile_loader.py`(账号画像) → `push_lark.py`(飞书推送) → `send_daily_ai_news.py`(每日AI资讯调度)；配套 `index.md` 说明 + `.gitignore` 隔离密钥/临时文件。
- **面试准备框架（嵌入式/系统岗）**：① 自我介绍 → ② 岗位核心能力(Linux应用层) → ③ 高频追问(环形缓冲三连问) → ④ 专项算法(嵌入式C) → ⑤ 项目配图(SyncE/PTP时钟)。
- **知识摄入分层**：`inbox` 暂存 → 提炼范式(如 LLM-Wiki 知识编译) → 正式入库；避免直接堆砌。
- **.gitignore 防脏**：忽略 Office 临时锁文件 `~$*.xlsx`、`~$*.docx` 等。

---

## 关联文件

- 产出（已提交）:
  - `01-Projects/.../6.community-collection-push/` — `collect_community.py` / `profile_loader.py` / `push_lark.py` / `send_daily_ai_news.py` / `index.md` / `.gitignore`（commit `63d957c` + `0711674` 重排）
  - `02-Knowledge/career-development/interview-project-summaries/01-company-interviews/千寻智能-MS准备清单.md`（+132行，commit `63d957c`+`1d38a1c`）
  - `.../embedded-c-algorithm-interview.md` + SyncE/PTP 时钟配图（commit `1d38a1c`）
  - `02-Knowledge/inbox/LLM-Wiki-知识编译范式研究.md`（commit `0711674`）
  - `05-Tools/codebuddy-chat-manager/chat-index.json` + `chat-index.md`（commit `ceec9e3`）
  - `01-Projects/family-hub/company-setup/beijing-company-accounting-ledger.md` + `beijing-company-social-insurance-plan.md` + `信用卡主控表.xlsx`（commit `0711674` + `1d38a1c` 的 .gitignore）
- 参考: —（当日无未提交工作区变更，全部已入 git）

