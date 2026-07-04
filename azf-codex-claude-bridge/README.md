# azf-codex-claude-bridge

这个 skill 用来让 Codex 在需要第二意见时，稳定调用本机 Claude Code CLI，把 Claude 当作只读审查员、反方顾问或架构复核员。

# 什么时候触发

- 用户说“让 Claude 审一下”“用 Claude 反方审查”“Codex 调 Claude 看看”。
- 需要 Claude 审查当前 diff、staged diff、分支差异或实现方案。
- 需要比较 Codex 与 Claude 对同一个工程问题的判断。
- 需要在 Codex 内部用 `claude -p` 做非交互式咨询。

# 当前关键规则

- 默认只读调用 Claude，Claude 只输出意见，不直接改文件。
- Codex 负责复核 Claude 的建议，并决定哪些建议值得采纳。
- 真正修改代码前，仍按 An Zhaofeng 的个人习惯执行确认、Git 状态检查和最小安全改动。
- 不向 Claude 发送密码、API key、token、cookie、私密日志或其它敏感信息。
- 优先使用 `scripts/invoke-claude.ps1`，必要时才直接用 `git diff | claude -p ...`。

# 最近维护

- 2026-07-04：创建第一版。加入 Codex 调 Claude 的只读审查工作流、PowerShell 包装脚本和失败处理规则。
