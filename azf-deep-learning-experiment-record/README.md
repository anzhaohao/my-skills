# azf-deep-learning-experiment-record

这个 skill 用来读取库外深度学习实验产物，并把证据整理成可读、可复查的 Markdown/Obsidian 实验记录。项目目录和笔记结构由 `azf-obsidian-project-record` 负责，笔记骨架由当前 Vault 的 Templater 模板负责。

## 什么时候触发

- 用户要求“整理实验记录”“填入实验记录”“总结训练结果”。
- 需要从 `manifest.md`、配置文件、训练日志、指标 JSON、图片、预测结果、checkpoint 等归档材料中提炼结论。
- 需要把实验写成适合初学者复盘的研究日志。

## 自动触发与默认入口

用户级 `C:\Users\anzhaofeng\.codex\AGENTS.md` 已将实验配置、训练日志、指标、预测、checkpoint 和实验记录生成默认路由到本 Skill。用户不必显式写 `$azf-deep-learning-experiment-record`；只要任务核心是整理或分析深度学习实验产物，就应优先触发本 Skill。

需要模型成本路由、独立验收或返工闭环时，由 `azf-auto-dev-loop` 提供控制层；需要确定 Obsidian 位置、模板、链接和归档规则时，交给 `azf-obsidian-project-record`。用户显式指定其它 Skill 或只要求简单解释时，不强制进入完整记录流程。

## 当前关键规则

- 先确认外部实验归档路径和目标实验记录；路径不明确时不要擅自写入。
- 实验记录属性使用中文：`项目名称`、`项目笔记类型`、`实验编号`、`实验归档路径`。
- 只写有证据支撑的内容，指标、图表、checkpoint 都要能回到具体文件。
- 日志、指标、预测、checkpoint 和规范图表默认留在库外，库内只记录理解并使用 `file:///` 链接。
- 先运行 `scripts/azf-experiment-scan.ps1` 做增量扫描；通过修改时间、大小和 SHA-256 只重新处理变化的文件。
- 写作风格要适合初学者理解：说明每个文件用来判断什么、读到了什么、能说明什么、还不能说明什么。
- 如果实验记录属于 An Zhaofeng 的 Obsidian 项目，先通过 `azf-obsidian-project-record` 调用当前模板并决定位置；除非用户明确要求，不自动同步总笔记或主线。

## 维护、验证与删除

- 唯一维护源：`C:\Users\anzhaofeng\.skills-manager\skills\azf-deep-learning-experiment-record`。
- Codex 入口：`C:\Users\anzhaofeng\.codex\skills\azf-deep-learning-experiment-record`，应为指向维护源的 Junction。
- 修改字段、证据规则或增量算法时，同时更新 `SKILL.md`、本 README、`scripts/azf-experiment-scan.ps1` 和 `schemas/experiment-evidence.schema.json`；若改变 Obsidian 分工，再同步检查 `azf-obsidian-project-record` 的接口说明。
- 修改后运行 PowerShell 语法解析、Schema JSON 解析、首次扫描和第二次增量扫描，并以 UTF-8 模式运行 `skill-creator/scripts/quick_validate.py`。测试只能使用临时实验目录，不要把原始日志或 checkpoint 复制进 Vault。
- 删除前先备份并确认 Junction 目标；然后移除用户级 `AGENTS.md` 的实验默认路由、`azf-auto-dev-loop` 中的 `experiment-record` 路由和依赖说明、顶层 Skill 索引及 Marketplace 条目，最后删除已确认的 Junction 和维护源目录。
- 删除本 Skill 不代表删除 `azf-obsidian-project-record`、实验原始目录或 Obsidian 记录；这些都是独立资源，必须分别确认。

## 最近维护

- 2026-08-14：增加增量证据扫描、文件哈希和结构化实验摘要，减少重复读取训练日志。
- 2026-08-14：记录无需显式点名的全局自动触发规则，以及维护、验证和安全删除步骤。
- 2026-07-18：职责收敛为库外实验证据分析；项目结构和 Templater 调用交给 `azf-obsidian-project-record`，实验属性统一使用中文。
