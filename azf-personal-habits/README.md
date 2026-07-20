# azf-personal-habits

这个 skill 是 An Zhaofeng 的全局个人协作习惯层，用来让不同智能体在编程、写文档、记录项目、调试、维护 Git 和创建 skill 时保持一致。

本 skill 只维护操作规程、话术模板、格式细则和工具启动步骤。关于用户本人的正式事实、边界和长期治理偏好，以 `agent-memory` 的 `vault/用户记忆/` 为准；两者冲突时以 vault 为准并提醒用户。定位 `agent-memory` 时优先使用 `azf-agent-memory`。

## 什么时候触发

- 开始为 An Zhaofeng 做编程、前端页面/应用、文档、实验记录、项目规划或调试任务。
- 任务涉及 Git 分支、提交、推送、回滚、备份或交接记录。
- 创建、补充、优化任何 skill。
- 创建 Markdown 文档、Obsidian 项目记录、Excalidraw 图或论文思路图。
- 使用 agent-reach/OpenCLI 进行 Twitter、Reddit、小红书、Facebook、Instagram 等依赖浏览器登录态的搜索或页面读取。
- 预览或测试本地 HTML、做响应式验收、截图，或准备调用 Codex 内置浏览器/IAB/browser-use。
- 克隆、复制、复刻、重建或逆向分析网站，或咨询相关工具和工作流。

## 当前关键规则

- OpenCLI 浏览器搜索属于 P0 稳定性路径。搜索开始时必须先显示“正在检查 Edge 与 Browser Bridge”，运行 `scripts/opencli_guard.py preflight --json`，确认连接后再显示“OpenCLI 已连接，开始搜索”。这里显示的是执行状态，不公开模型内部思维链。
- Edge 关闭时由预检脚本最小化启动 Default profile；扩展仍未连接时只重启一次 daemon。仍失败就快速切换 agent-reach 的备用后端，禁止直接进入约 20 秒的无界等待，也禁止借 Codex IAB/browser-use 修复 OpenCLI。
- OpenCLI 原始输出必须限量。优先通过 `scripts/opencli_guard.py run` 调用，默认限制结果条目和输出字符数，避免 quoted tweet、长文或嵌套正文挤满上下文并造成任务看似“截断”。
- Codex 内置浏览器/IAB/browser-use 在当前机器上属于 P0 闪退风险路径。默认不得用它做本地 HTML 预览、响应式验收、截图或普通页面读取；优先使用独立 headless Playwright，需要可见界面、现有登录态或扩展时改用 Edge/Chrome。
- OpenCLI 与 IAB 必须分开处理：OpenCLI 搜索继续执行 Edge/Browser Bridge 预检；独立 headless Playwright 不需要 OpenCLI 预检；OpenCLI 断连时禁止回退到 IAB。
- 如果我明确要求使用 IAB，Agent 必须在真正创建 browser-use 标签前提醒它可能直接结束 Codex 进程并再次确认。看到 `No ChatGPT browser route`、`Sign in to ChatGPT`、`hidden-browser-use`、`ResizeObserver` 或 PiP 写入失败时停止重试，切换独立浏览器路径。
- 用户正式事实与边界不在本 skill 中维护完整版本；本 skill 只保留行为层规则和指向 `agent-memory` 的说明。
- 重要代码修改前检查 Git 状态，必要时提醒创建分支。
- Obsidian 笔记库 `E:\software\Obsidian\安钊锋的外置大脑` 及其 `anzhaohao/obsidian` 备份仓库是分支例外：默认始终使用 `main`。除非我在当前回合明确同意创建或切换分支，否则任何 Agent 都不得为该笔记库新建分支、切换分支或自动执行 branch-worthy 流程；需要回滚保护时改用提交、推送、tag 和外部备份。如果发现笔记库意外位于非 `main` 分支，只能先报告并询问，不能自行切换。
- 项目代码或项目文件改动前必须先二次确认：如果我只是要求“更新工作记录、分析问题、评估方案、解释行为”，不要顺手改代码；必须先给出修改方案、影响文件和风险点，等我明确确认后再改。
- 调试、修 bug、代码改动、硬件/软件排查或 Git 提交/推送时，Obsidian 笔记库默认只读。除非我在当前回合明确说“更新笔记、同步笔记、写入笔记、整理笔记”，否则不要修改 Obsidian 正文；如果确实值得补记，只在最后说明“笔记未更新，可作为后续待办”。
- 未指定备份位置时，默认把 Codex 回滚备份放到 `E:\software\CodexPlusPlus\Codex备份\YYYYMMDD_HHMMSS_任务名_修改前备份`。
- 小里程碑完成后提醒本地提交，重要节点提醒推送 GitHub，稳定成果提醒打 tag。
- 当 Codex 帮我创建分支、提交、合并、rebase、打 tag 或整理 Git 状态时，默认生成或更新 Git 分支/提交可视化交接记录；提交后优先生成 Mermaid `gitGraph`，并在图上标出当前本地 HEAD。
- 多步骤任务要留下可接手的进度线索。
- 创建或修改任何 Markdown/Obsidian 文档时，必须先读取并应用 `azf-personal-habits`，再叠加其它相关 skill，例如 `azf-server-deploy` 或论文精读类 skill；硬件事实统一写入 `03-Academic Toolkit/2_资源与档案/仪器设备资产`；不能因为任务表面上是硬件、服务器、密钥、代码或部署，就跳过本 skill。
- 创建 Markdown 文档时，默认不要在正文重复写文件标题。
- 如果 Markdown 正文没有单独标题，正文里的主要章节要从 `# 一级标题` 开始，不要直接从 `##` 开始。
- 创建或修改 Obsidian 笔记属性时，只允许文件最开头有一个 YAML frontmatter；第一行必须是纯 `---`，不能有 UTF-8 BOM 或隐藏字符。`创建时间`、`修改时间`、`项目`、`类型`、`状态`、`aliases`、`tags` 等字段必须合并在同一个属性块里，不能在正文再补一个属性块。
- Obsidian 库内笔记互相引用时，默认使用不带文件夹路径的短 wikilink，例如 `[[【中译】使用二次谐波产生的频率分辨光学门控.md|中译笔记]]`；不要写成 `[[02-Brain Cells/.../【中译】...md|中译笔记]]`。这样笔记文件夹移动时链接更稳。资源/附件或插件明确要求路径时才保留路径。
- Obsidian 附件按类型分流：图片使用全局 `Attachments/<笔记目录>/<笔记文件名.md>/` 镜像体系；PDF、PPTX、DOCX、XLSX、视频、压缩包等其他非 Markdown 文件放在当前笔记目录下的本地 `附件/` 文件夹。Markdown 文件仍留在正文目录，不当作附件。
- 创建或总结 Obsidian / Markdown 笔记时，不要写得过于专业。优先让“未来的我一眼看懂”：先写人话含义，再补必要技术细节；可以有一点温度，比如说明为什么这一步容易误解、这个结论为什么重要，但不要变成长篇抒情。
- 整理我已有的 Obsidian 笔记时，先保留原文判断链，再做结构化优化；不要把能说明“为什么后来这样决策”的解释段、截图序列或折叠 callout 压平成泛化摘要。
- An Zhaofeng 的个人 skill 文件夹名和 `SKILL.md` frontmatter `name` 都要使用 `azf-` 前缀。
- `C:\Users\anzhaofeng\.skills-manager\skills` 是本地 skill 的统一源目录，里面应保存真实 skill 目录；其它 agent 或 plugin 目录需要共用 skill 时，应从它们那边链接回 Skills Manager，而不是让 Skills Manager 反向链接到外部目录。
- 当任务同时匹配通用 skill 和 An Zhaofeng 自定义 `azf-` skill 时，优先读取并遵循 `azf-` skill。
- 如果用户明确指定自定义 skill，要优先按用户给出的 skill 做，而不是只按通用/system skill。
- 排查 Codex 自身闪退、卡顿、网络/MCP/app-server 或 SQLite 日志写入问题时，使用下面的“临时 SQLite 诊断窗口”；普通开发不要关闭日志保护。
- 网站克隆及相关咨询默认进入 `D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260720-ai-website-cloner-template`，使用 Conda 环境 `ai-website-cloner-template`。开始前读取项目的 `AGENTS.md` 和 `.codex/skills/clone-website/SKILL.md`，按 `/clone-website <url1> [<url2> ...]` 工作流执行；不同目标网站使用独立分支、worktree 或项目副本隔离。若我在当前回合明确指定其他工具、路径或流程，则以当前要求为准。
- 我说“精读文献”“精读论文”“论文精读”或要求生成论文精读笔记时，默认以 `azf-literature-reading-workflow` 作为总流程入口。只有我明确说“逐句精读”或“逐段精读”时，才参考 `【已归档】论文逐句精读与PDF++定位工作流.md`；如果我明确说“不需要跳转”，不要强制 PDF++ 链接，改用页码、段落和句子定位。
- 创建、补充、优化 skill 时，要同步维护该 skill 文件夹下的中文 `README.md`。
- 通过代码运行的 QuickAdd UserScript 统一放在 `E:\software\Obsidian\安钊锋的外置大脑\05-Junk Drawer\3_Plugin Mods\QuickAdd\Scripts`；移动或修改时同步更新 `.obsidian/plugins/quickadd/data.json`，并同步维护该目录下的 `QuickAdd脚本说明.md`，然后重新加载 QuickAdd。
- 涉及 Excalidraw、论文思路图、项目图谱等视觉产物时，实际生成、布局、箭头路由和 QA 统一使用 `excalidraw-diagram` skill；本 skill 只负责提醒优先级和路由。
- 做前端、网站、应用、dashboard、landing page、游戏或交互页面时，优先考虑 React Bits 作为 React 动画组件和视觉素材来源，优先用 GSAP 处理自定义动画编排、滚动动画、timeline 和 React 动画清理；两者可结合使用，但不要为了炫技牺牲可用性、轻量性或既有设计风格。

## Codex 自身故障的临时 SQLite 诊断窗口

当前本机用 `codex_block_log_inserts_20260720` trigger 暂时拦截 `%USERPROFILE%\.codex\logs_2.sqlite` 的日志插入，以降低 SSD 写入放大。它不是永久修复，而且开启时 SQLite 诊断记录不完整。

### 首轮：关闭保护并要求重启复现

仅在排查 Codex 自身故障时执行：

1. 先记录 trigger 状态、`logs` 的 `COUNT(*)/MAX(id)`、`sqlite_sequence` 和 `logs_2.sqlite-wal` 大小。
2. 明确提醒我：“为获取故障证据，我将暂时关闭 SQLite 写入保护；这会恢复日志写入并增加 SSD 写入。请立即完整重启 Codex，重启后只复现一次问题，然后回来，我会先收集日志并恢复保护。”
3. 把下面的命令作为该轮最后一个动作，不要顺手继续普通工作：

   ```powershell
   $db = "$env:USERPROFILE\.codex\logs_2.sqlite"
   sqlite3 $db "PRAGMA busy_timeout=20000; DROP TRIGGER IF EXISTS codex_block_log_inserts_20260720;"
   ```

### 重启后：先取证，再恢复

下一轮先确认 trigger 仍关闭，只收集这一次复现需要的 SQLite 聚合/尾部数据、`%LOCALAPPDATA%\Codex\Logs`、Windows Event/WER/Crashpad 和对应会话 JSONL。SQLite 日志和会话 JSONL 是两套来源，不能因为前者缺行就判断会话丢失。

取证完成后立即恢复并校验：

```powershell
$db = "$env:USERPROFILE\.codex\logs_2.sqlite"
sqlite3 $db "PRAGMA busy_timeout=20000; CREATE TRIGGER IF NOT EXISTS codex_block_log_inserts_20260720 BEFORE INSERT ON logs BEGIN SELECT RAISE(IGNORE); END; PRAGMA wal_checkpoint(TRUNCATE); PRAGMA quick_check;"
```

确认 trigger 存在、`quick_check` 返回 `ok`、WAL 已截断或受控，再继续分析。若新一轮开始时发现 trigger 意外关闭且没有明确的活动诊断窗口，先恢复保护再做普通工作。

### 官方修复后的弃用条件

不能只因为 GitHub issue 关闭或版本号变化就删除本地方案。必须有官方稳定版/官方配置明确修复，并在本机做受控的无 trigger 采样，确认写入不再异常增长。满足后改用官方策略，停止安装本地 trigger，并从本 `SKILL.md` 与本 README 删除整段临时规范，同时把 SQLite 问题笔记标记为“已退役”。

## Visual / Excalidraw 习惯

- 实际 Excalidraw 生成规则集中维护在 `excalidraw-diagram`。
- 项目现有的 Obsidian 工作流只决定图属于哪个项目、放到哪里、承担什么记录职责。
- 如果多个 skill 都涉及图，先用个人 workflow skill 判断任务边界，再用 `excalidraw-diagram` 执行画图和检查。
- 使用 Excalidraw MCP 时，如果 `127.0.0.1:3000` 或 `api/elements` 连不上，不要直接绕开 MCP 手写 `.excalidraw.md`；先检查并启动本地 canvas 服务。当前机器的部署目录是 `E:\software\MCP\mcp_excalidraw`，在该目录运行 `npm run canvas`，再访问 `http://127.0.0.1:3000/health` 验证。
- 记住两层服务不同：`dist/index.js` 是 MCP stdio server，`npm run canvas` 才是 Excalidraw 画布 / REST API 服务。
- 生成 Excalidraw 图后必须做视觉核对，确认文字标签真实显示；只有空色块/空框不能算完成。

## 最近维护

- 2026-07-20：加入 Codex 自身故障的临时 SQLite 诊断窗口。首轮短暂关闭 trigger 并要求完整重启、只复现一次；下一轮先取证再恢复保护。官方稳定修复经本机验证后删除本临时规范。

- 2026-07-20：加入网站克隆默认路由。以后未指定其他工具时，网站克隆、复刻、重建、逆向分析及相关咨询默认使用本地 `ai-website-cloner-template` 项目和同名 Conda 环境，并按目标网站隔离工作区。

- 2026-07-18：集中管理 QuickAdd UserScript：脚本迁移到 `05-Junk Drawer/3_Plugin Mods/QuickAdd/Scripts`，配置路径和脚本说明文档必须与每次移动/修改同步更新。

- 2026-07-18：归档逐句精读 Skill；“精读文献”“精读论文”“论文精读”继续进入 `azf-literature-reading-workflow`，明确逐句或逐段时参考论文精读工作流目录下的已归档 PDF++ 定位方法。

- 2026-07-17：加入 Obsidian 库内笔记短 wikilink 规则。笔记到笔记的引用默认只写文件名和别名，例如 `[[【中译】...md|中译笔记]]`，不在前面加文件夹路径；资源和附件链接可按需要保留路径。

- 2026-07-16：加入 Codex IAB P0 闪退保护。当前便携 Gate-off `26.707.12708.0` 在无可用 ChatGPT browser route 时，创建 `hidden-browser-use` WebView 后可于页面加载完成后直接退出；以后本地 HTML 验收默认使用独立 headless Playwright，OpenCLI 与 IAB 的门禁和回退路径严格分离。

- 2026-07-16：把 OpenCLI 浏览器连接提升为 P0 搜索门禁。新增 `scripts/opencli_guard.py`，搜索前自动检查 daemon、最小化启动 Edge、轮询 Browser Bridge、必要时重启一次 daemon；同时增加有界输出执行模式，避免插件未连接等待和超长网页正文造成任务截断。

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
- 2026-06-23：首次加入论文精读默认路由规则；该规则已于 2026-07-17 调整为优先进入总流程 Skill。
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
