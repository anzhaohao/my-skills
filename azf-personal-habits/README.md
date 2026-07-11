# azf-personal-habits

这个 skill 是 An Zhaofeng 的全局个人协作习惯层，用来让不同智能体在编程、写文档、记录项目、调试、维护 Git 和创建 skill 时保持一致。

本 skill 只维护操作规程、话术模板、格式细则和工具启动步骤。关于用户本人的正式事实、边界和长期治理偏好，以 `agent-memory` 的 `vault/用户记忆/` 为准；两者冲突时以 vault 为准并提醒用户。定位 `agent-memory` 时优先使用 `azf-agent-memory`。

## 什么时候触发

- 开始为 An Zhaofeng 做编程、前端页面/应用、文档、实验记录、项目规划或调试任务。
- 任务涉及 Git 分支、提交、推送、回滚、备份或交接记录。
- 创建、补充、优化任何 skill。
- 创建 Markdown 文档、Obsidian 项目记录、Excalidraw 图或论文思路图。

## 当前关键规则

- 用户正式事实与边界不在本 skill 中维护完整版本；本 skill 只保留行为层规则和指向 `agent-memory` 的说明。
- 重要代码修改前检查 Git 状态，必要时提醒创建分支。
- Obsidian 笔记库 `E:\software\Obsidian\安钊锋的外置大脑` 及其 `anzhaohao/obsidian` 备份仓库是分支例外：默认始终使用 `main`。除非我在当前回合明确同意创建或切换分支，否则任何 Agent 都不得为该笔记库新建分支、切换分支或自动执行 branch-worthy 流程；需要回滚保护时改用提交、推送、tag 和外部备份。如果发现笔记库意外位于非 `main` 分支，只能先报告并询问，不能自行切换。
- 项目代码或项目文件改动前必须先二次确认：如果我只是要求“更新工作记录、分析问题、评估方案、解释行为”，不要顺手改代码；必须先给出修改方案、影响文件和风险点，等我明确确认后再改。
- 调试、修 bug、代码改动、硬件/软件排查或 Git 提交/推送时，Obsidian 笔记库默认只读。除非我在当前回合明确说“更新笔记、同步笔记、写入笔记、整理笔记”，否则不要修改 Obsidian 正文；如果确实值得补记，只在最后说明“笔记未更新，可作为后续待办”。
- 未指定备份位置时，默认把 Codex 回滚备份放到 `E:\software\CodexPlusPlus\Codex备份\YYYYMMDD_HHMMSS_任务名_修改前备份`。
- 小里程碑完成后提醒本地提交，重要节点提醒推送 GitHub，稳定成果提醒打 tag。
- 当 Codex 帮我创建分支、提交、合并、rebase、打 tag 或整理 Git 状态时，默认生成或更新 Git 分支/提交可视化交接记录；提交后优先生成 Mermaid `gitGraph`，并在图上标出当前本地 HEAD。
- 多步骤任务要留下可接手的进度线索。
- 创建或修改任何 Markdown/Obsidian 文档时，必须先读取并应用 `azf-personal-habits`，再叠加其它相关 skill，例如 `azf-obsidian-work-record`、`azf-hardware-skill`、`azf-server-deploy` 或论文精读类 skill；不能因为任务表面上是硬件、服务器、密钥、代码或部署，就跳过本 skill。
- 创建 Markdown 文档时，默认不要在正文重复写文件标题。
- 如果 Markdown 正文没有单独标题，正文里的主要章节要从 `# 一级标题` 开始，不要直接从 `##` 开始。
- 创建或修改 Obsidian 笔记属性时，只允许文件最开头有一个 YAML frontmatter；第一行必须是纯 `---`，不能有 UTF-8 BOM 或隐藏字符。`创建时间`、`修改时间`、`项目`、`类型`、`状态`、`aliases`、`tags` 等字段必须合并在同一个属性块里，不能在正文再补一个属性块。
- Obsidian 附件按类型分流：图片使用全局 `Attachments/<笔记目录>/<笔记文件名.md>/` 镜像体系；PDF、PPTX、DOCX、XLSX、视频、压缩包等其他非 Markdown 文件放在当前笔记目录下的本地 `附件/` 文件夹。Markdown 文件仍留在正文目录，不当作附件。
- 创建或总结 Obsidian / Markdown 笔记时，不要写得过于专业。优先让“未来的我一眼看懂”：先写人话含义，再补必要技术细节；可以有一点温度，比如说明为什么这一步容易误解、这个结论为什么重要，但不要变成长篇抒情。
- 整理我已有的 Obsidian 笔记时，先保留原文判断链，再做结构化优化；不要把能说明“为什么后来这样决策”的解释段、截图序列或折叠 callout 压平成泛化摘要。
- An Zhaofeng 的个人 skill 文件夹名和 `SKILL.md` frontmatter `name` 都要使用 `azf-` 前缀。
- `C:\Users\anzhaofeng\.skills-manager\skills` 是本地 skill 的统一源目录，里面应保存真实 skill 目录；其它 agent 或 plugin 目录需要共用 skill 时，应从它们那边链接回 Skills Manager，而不是让 Skills Manager 反向链接到外部目录。
- 当任务同时匹配通用 skill 和 An Zhaofeng 自定义 `azf-` skill 时，优先读取并遵循 `azf-` skill。
- 如果用户明确指定自定义 skill，要优先按用户给出的 skill 做，而不是只按通用/system skill。
- 我说“精读”“逐句精读”“论文精读”时，默认使用 `azf-paper-sentence-deep-reading`。如果我明确说“不需要跳转”，不要强制 PDF++ 链接，保留逐段成文、破冰前瞻、逐句卡片和扫盲班术语结构即可。
- 创建、补充、优化 skill 时，要同步维护该 skill 文件夹下的中文 `README.md`。
- 涉及 Excalidraw、论文思路图、项目图谱等视觉产物时，实际生成、布局、箭头路由和 QA 统一使用 `excalidraw-diagram` skill；本 skill 只负责提醒优先级和路由。
- 做前端、网站、应用、dashboard、landing page、游戏或交互页面时，优先考虑 React Bits 作为 React 动画组件和视觉素材来源，优先用 GSAP 处理自定义动画编排、滚动动画、timeline 和 React 动画清理；两者可结合使用，但不要为了炫技牺牲可用性、轻量性或既有设计风格。

## Visual / Excalidraw 习惯

- 实际 Excalidraw 生成规则集中维护在 `excalidraw-diagram`。
- `azf-project-note-binding`、`azf-obsidian-work-record` 等个人 workflow skill 只决定图属于哪个项目、放到哪里、承担什么记录职责。
- 如果多个 skill 都涉及图，先用个人 workflow skill 判断任务边界，再用 `excalidraw-diagram` 执行画图和检查。
- 使用 Excalidraw MCP 时，如果 `127.0.0.1:3000` 或 `api/elements` 连不上，不要直接绕开 MCP 手写 `.excalidraw.md`；先检查并启动本地 canvas 服务。当前机器的部署目录是 `E:\software\MCP\mcp_excalidraw`，在该目录运行 `npm run canvas`，再访问 `http://127.0.0.1:3000/health` 验证。
- 记住两层服务不同：`dist/index.js` 是 MCP stdio server，`npm run canvas` 才是 Excalidraw 画布 / REST API 服务。
- 生成 Excalidraw 图后必须做视觉核对，确认文字标签真实显示；只有空色块/空框不能算完成。

## 最近维护

- 2026-07-11：加入 Obsidian 附件按文件类型分流规则。图片继续进入全局 `Attachments` 镜像目录；PDF、PPTX、DOCX、XLSX、视频、压缩包等其他非 Markdown 附件放在当前笔记目录下的本地 `附件/` 文件夹。

- 2026-07-11：加入 Obsidian 笔记库 Git 分支硬规则。`E:\software\Obsidian\安钊锋的外置大脑` / `anzhaohao/obsidian` 默认只使用 `main`；未经我在当前回合明确同意，禁止新建或切换分支。宽泛改动通过 commit、push、tag 和外部备份建立回滚点。

- 2026-07-09：加入 Markdown/Obsidian 文档创建与修改的流程改进规则。本次漏用原因是任务表面上被归类为服务器、SSH、Zed 和 Key 管理，导致只叠加了领域 skill，而没有先把“正在创建 Markdown/Obsidian 文档”作为更高优先级触发条件；以后凡是创建或修改 `.md`、Obsidian 笔记、项目记录、Key 索引等文档，必须先读取 `azf-personal-habits` 作为格式和流程基线，再叠加其它领域 skill。
- 2026-07-08：补充笔记写作语气偏好：创建和总结 Obsidian / Markdown 笔记时，优先让未来的我快速看懂，不要为了显得专业而堆术语；先写清楚人话含义，再补必要技术细节，可以保留一点温度。
- 2026-07-08：补充 Obsidian 旧笔记整理偏好：整理已有主线、调试记录或 callout 时，要保留原文的观察、证据截图、依据链接和后续判断顺序；结构化不等于压缩成泛化摘要。
- 2026-07-07：确认 skill 与 `agent-memory vault` 分层。`azf-personal-habits` 保留为行为层，负责自动触发的操作规程；用户正式事实、边界和长期治理偏好改由 `agent-memory/vault/用户记忆/` 维护。冲突时以 vault 为准并提醒用户。
- 2026-07-04：加入独立前端偏好。以后做前端、网站、应用、dashboard、landing page、游戏或交互页面时，优先考虑 React Bits + GSAP 的组合：React Bits 用于现成动画组件和视觉素材，GSAP 用于自定义动画编排和 React 动画工程规范，但以可用性、项目风格和轻量性优先。
- 2026-07-04：加入 Skills Manager 链接方向规则。`C:\Users\anzhaofeng\.skills-manager\skills` 必须作为真实源目录；其它 agent/plugin 目录需要共用 skill 时，反向链接回 Skills Manager。
- 2026-07-02：将 Codex 默认回滚备份根目录从桌面迁移到 `E:\software\CodexPlusPlus\Codex备份`，以后只在该目录下创建时间戳任务子目录。
- 2026-06-30：加入 Obsidian frontmatter 防重复规则。以后创建/补充 AI 笔记属性时，必须使用 UTF-8 无 BOM、文件首行纯 `---`、全文件只保留一个顶部 YAML 属性块，避免 `Update time on edit` 误判后重复创建 `创建时间/修改时间`。
- 2026-06-23：加入论文精读默认路由规则。以后我说“精读”默认指 `azf-paper-sentence-deep-reading`；若明确说“不需要跳转”，则不强制 PDF++ 链接。
- 2026-06-15：修正代码调试与 Obsidian 同步边界。调试、修 bug、硬件排查和代码修改时，笔记库默认只读；只有我在当前回合明确要求更新/同步/写入/整理笔记，才允许改 Obsidian，并且结构性改动前必须先备份。
- 2026-06-04：加入“项目代码/项目文件改动前必须二次确认”的硬规则。只要求记录、分析、评估或解释时，不得顺手修改代码；必须先给方案、影响范围和风险，得到明确确认后再改。
- 2026-06-04：曾加入“每次调试记录也同步一份到 Obsidian 调试记录”的习惯规则；2026-06-15 已废止这个默认自动同步规则，避免代码调试时误改笔记结构。
- 2026-06-04：加入 Excalidraw MCP 本地服务启动规则：3000 端口不通时先主动启动 `E:\software\MCP\mcp_excalidraw` 的 `npm run canvas`，并做视觉核对，不再绕开 MCP 生成可能缺字的图。
- 2026-06-02：补充 Git 可视化偏好：每次 Codex 提交 Git 后，优先按 Mermaid `gitGraph` 生成“分支故事图”，在图上标出当前本地 HEAD；如果还有未提交修改，要在图后说明 `HEAD + 未提交修改` 并列出文件。
- 2026-06-02：加入 Git 可视化交接习惯：Codex 做分支、提交、合并、rebase、tag 或回滚点时，默认记录分支来源、起点提交、关键提交，并生成 `git log --graph` 文本图；复杂项目可同步维护 `GIT_BRANCH_MAP.md` / `BRANCH_MAP.md` 或 Obsidian Git 分支记录。
- 2026-06-03：将 Excalidraw 具体生成、无限画布、卡片、箭头和 QA 规则集中到 `excalidraw-diagram`，本 skill 只保留路由习惯。
- 2026-06-01：补充 Markdown 标题层级习惯：不写正文标题时，正文主要章节从 `#` 开始；只有正文已经有 `# 标题` 时，后续章节才从 `##` 开始。
- 2026-05-31：加入“优先参考 An Zhaofeng 自定义 `azf-` skill”的长期习惯。
- 2026-05-31：曾加入 Excalidraw/视觉产物截图 QA 习惯；具体规则已在 2026-06-03 迁移到 `excalidraw-diagram`。
- 2026-05-31：重写中文 README，修复乱码并同步最新习惯。
