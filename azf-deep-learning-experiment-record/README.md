# azf-deep-learning-experiment-record

这个 skill 用来读取库外深度学习实验产物，并把证据整理成可读、可复查的 Markdown/Obsidian 实验记录。项目目录和笔记结构由 `azf-obsidian-project-record` 负责，笔记骨架由当前 Vault 的 Templater 模板负责。

## 什么时候触发

- 用户要求“整理实验记录”“填入实验记录”“总结训练结果”。
- 需要从 `manifest.md`、配置文件、训练日志、指标 JSON、图片、预测结果、checkpoint 等归档材料中提炼结论。
- 需要把实验写成适合初学者复盘的研究日志。

## 当前关键规则

- 先确认外部实验归档路径和目标实验记录；路径不明确时不要擅自写入。
- 实验记录属性使用中文：`项目名称`、`项目笔记类型`、`实验编号`、`实验归档路径`。
- 只写有证据支撑的内容，指标、图表、checkpoint 都要能回到具体文件。
- 日志、指标、预测、checkpoint 和规范图表默认留在库外，库内只记录理解并使用 `file:///` 链接。
- 写作风格要适合初学者理解：说明每个文件用来判断什么、读到了什么、能说明什么、还不能说明什么。
- 如果实验记录属于 An Zhaofeng 的 Obsidian 项目，先通过 `azf-obsidian-project-record` 调用当前模板并决定位置；除非用户明确要求，不自动同步总笔记或主线。

## 最近维护

- 2026-07-18：职责收敛为库外实验证据分析；项目结构和 Templater 调用交给 `azf-obsidian-project-record`，实验属性统一使用中文。
