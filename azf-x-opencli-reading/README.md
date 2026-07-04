# 这个 skill 解决什么问题

这个个人 skill 用来固定“读取 X/Twitter 链接”的正确流程，尤其是你当前使用 Edge + OpenCLI 的环境。它避免下次 Agent 只看到 X 登录页、文章卡片摘要，或者因为 Chrome 扩展未连接就误判 OpenCLI 不可用。

# 什么时候应该触发

- 你发来 `x.com` 或 `twitter.com` 链接。
- 你让 Agent 理解一条推文、长推、X Article 或 thread。
- 之前 X 内容没有读全，需要重新读取或解释失败原因。

# 当前保存的关键规则

- 你的桌面环境主要使用 Microsoft Edge。
- Edge 已安装 OpenCLI。
- 读取 X 长文时优先使用 `opencli twitter article "<URL>" -f yaml`。
- 读取普通推文或推文串时使用 `opencli twitter tweets "<URL>" -f yaml`。
- 不再使用错误命令 `opencli twitter tweet`。
- `agent-reach doctor` 或 `opencli doctor` 提到 Chrome 扩展未连接时，不代表 Edge 的 OpenCLI 一定不可用，应直接测试 OpenCLI 命令。
- Jina Reader 和普通网页抓取只作为兜底；如果只读到登录页、卡片摘要或 `x.com/i/article/...` 入口，不能当作完整正文。

# 最近维护

- 2026-07-04：从 Skills Manager 误删中恢复。恢复来源为 2026-07-03 的 Codex 会话记录；保持原始规则不变。
- 2026-07-03：创建此 skill。背景是读取 `gengdaJ` 的 X Article 时，第一次停在网页/卡片层，后续通过 OpenCLI article 命令成功读取全文。
