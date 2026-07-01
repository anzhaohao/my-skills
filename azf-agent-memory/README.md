# 这个 skill 解决什么问题

`azf-agent-memory` 用来让 Codex 自动使用你的本地长期记忆库：

```text
E:\software\Obsidian\agent-memory
```

它把“任务开始先查记忆、任务结束写回稳定结论、然后重建索引”固定成 Codex 的工作习惯。以后调试 FrogTrace、继续旧项目、问上次结论、整理长期偏好时，不需要你手动记命令。

# 什么时候应该触发

- 继续调试某个旧项目，比如 FrogTrace。
- 用户说“上次”“继续”“之前怎么做的”“还有什么没闭环”。
- 任务涉及项目历史结论、用户偏好、硬件/服务器/部署事实、长期排查。
- 重要任务结束时，需要把稳定事实写回长期记忆。

# 当前关键事实

- 记忆库根目录：`E:\software\Obsidian\agent-memory`
- 记忆入口文件：`E:\software\Obsidian\agent-memory\vault\AGENTS.md`
- Conda Python：`E:\software\Anaconda\envs\agent-memory\python.exe`
- 基础检查脚本：`Run-AgentMemoryCheck-Conda.ps1`
- 向量索引脚本：`Run-AgentMemoryVectorIndex.ps1`
- 该项目不是 EverOS HTTP 服务，而是 Markdown + SQLite + Zvec 本地记忆库。

# 最近维护

2026-07-01：创建 skill，固化 agent-memory 的检索、写回、索引重建和旧 Codex 聊天记录导入原则。
