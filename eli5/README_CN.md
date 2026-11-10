# ELI5 — 把任何话题解释给任何人听

## 这个 skill 解决什么问题

把复杂的技术概念、代码、报错、文档，用指定听众能听懂的方式解释出来。支持按年龄（5 岁 / 10 岁 / 15 岁 / 大学生 / 研究生）、按职业（经理 / 工程师 / 设计师 / 产品经理）、按关系（父母 / 配偶 / 孩子 / 朋友）等多种受众画像，自动调整词汇、类比、语气和深度。

## 什么时候触发

- 用户说"ELI5"、"explain like I am"、"用 XXX 能听懂的方式解释"
- 用户说"把 xxx 解释给我的经理 / 父母 / 孩子听"
- 用户想以某个特定背景知识水平来理解某个概念

## 当前保存的关键事实

- 来源仓库：https://github.com/DreambigOu/ELI5 （MIT 协议）
- 安装位置：`E:\software\skills-manager\skills\eli5`
- 不是个人自定义 skill，不加 `azf-` 前缀
- 默认受众：如果用户没指定，按 5 岁小孩解释（经典 ELI5）
- 原始 SKILL.md 在 `skills/eli5/SKILL.md`，顶层也复制了一份方便 Codex 发现
- Skills Manager 已关联上游 `main` 分支，来源子目录为 `skills/eli5`。
- 技能正文保持上游默认内容，不再读取个人知识画像；明确指定受众时，仍按本次指定的受众解释。

## 最近一次维护

- 2026-11-10：核实并同步上游 `main` 最新提交 `a766623b062331fdde53467001379b4ddf3acc2f`；恢复上游默认受众规则，移除 `SKILL.md` 中的个人知识画像定制，并在备份后删除原 `C:\Users\anzhaofeng\.codex\eli5-profile.md`。Codex、Claude Code 和其他现有工具通过共享目录引用同一份技能；全局说明与 CC Switch 提示词检查中未发现相关定制残留。
- 2026-09-16：首次安装，从 GitHub 克隆 DreambigOu/ELI5，将 SKILL.md 复制到顶层以便 skill 发现
