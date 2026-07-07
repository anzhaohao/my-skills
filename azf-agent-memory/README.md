# 这个 skill 解决什么问题

`azf-agent-memory` 用来让 Codex 自动使用安钊锋的本地长期记忆库：任务开始先查记忆，任务结束把稳定事实写回正式 Markdown 记忆，并刷新 SQLite/Zvec 索引。

这个 skill 面向本地 `agent-memory` 系统。它不是 EverOS HTTP 服务，而是 Markdown 事实源 + SQLite 全文索引 + Zvec 语义索引 + Git 备份规则的个人长期记忆工作流。

# 什么时候应该触发

- 继续旧项目、调试旧问题、追问“上次”“之前”“还有什么未闭环”。
- 任务涉及项目历史结论、用户偏好、硬件、服务器、部署事实或长期排查。
- 需要维护 `agent-memory` 自身的脚本、提示词、source 更新、GitHub 备份规则。
- 重要任务结束时，需要把稳定事实、决策、项目状态或可复用经验写回长期记忆。
- 用户要查旧聊天、历史 session、之前和 Claude/Codex/Cursor 聊过什么。

# 当前关键事实

- 记忆系统统一叫 `agent-memory`。
- `vault/` 是正式事实源，SQLite/Zvec/日志/缓存都是可重建运行产物。
- `source/` 是普通源码目录，随 `anzhaohao/agent-memory` 的 `main` 分支备份，不是 submodule。
- 不创建 `source-main`、额外远程仓库、fork 或 submodule，除非用户明确改变规则。
- 写入正式记忆前要 reconcile，只能给出 `ADD`、`UPDATE`、`NOOP`、`MARK_OUTDATED`、`MERGE_REQUIRED`、`ASK_USER` 等动作。
- 不把 API key、token、cookie、密码、原始聊天全文、SQLite/Zvec、模型缓存、运行日志写入或提交。

# AgentsView 规则

旧聊天查询优先使用 AgentsView，但只在用户明确要查旧聊天、历史 session、上次聊过什么或整理原始会话时触发。普通 `agent-memory` recall 不触发 AgentsView。

AgentsView 只是原始会话证据层，不是事实源。它可以帮助定位 Claude Code、Codex、Cursor 等会话中的线索、时间、项目、工具来源和候选片段，但不能把整段旧聊天直接注入上下文，也不能把旧 Agent 的说法直接当结论。

探测顺序应保持轻量：

1. 先用 1 秒 HTTP 请求检查本地入口。
2. HTTP 不通时，再按个人习惯、本地记忆和常见软件目录定位 AgentsView。
3. 已部署但未运行时，自动后台启动。
4. `Get-NetTCPConnection` 只作为后备诊断，不放在普通热路径。

从 AgentsView 找到的线索，必须再对照 `agent-memory/vault`、当前代码仓库或项目文件确认；稳定事实再写回正式记忆。

# 最近维护

- 2026-07-05：优化旧聊天检索规则。AgentsView 仅在旧聊天/历史 session 场景启用；探测改为轻量 HTTP 优先，避免 `Get-NetTCPConnection` 拖慢普通聊天。
- 2026-07-04：加入 `MAINTENANCE_PRINCIPLES.md` 必读规则、单 `main` 分支备份规则，以及通用 agent-memory 接入提示词维护要求。
- 2026-07-01：创建 skill，固化 agent-memory 的检索、写回、索引重建和旧 Codex 聊天记录导入原则。
