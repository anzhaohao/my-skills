# paper-obsidian-review

A Codex skill for turning papers, code repositories, local PDFs, and online research resources into structured Obsidian literature-review notes.

This skill is designed for workflows where a researcher wants to organize several papers into a reusable Obsidian vault with:

- local PDF links
- local code links
- online paper and repository links
- method/framework figures
- reproducibility notes
- academic Chinese section headings
- cross-paper comparison tables
- project-indicator mapping

## What This Skill Does

`paper-obsidian-review` guides Codex to build paper review notes that answer the following questions clearly:

- Why was the work proposed?
- What scientific or technical problem does it solve?
- What method does it use to solve that problem?
- What are the main innovations?
- What are the inputs, outputs, modules, and mechanisms?
- How feasible is reproduction from the released code?
- How does the paper support the user's research indicators or project goals?

The skill avoids vague summaries such as "what this paper does" and instead enforces a structured research-note format.

## Recommended Obsidian Output Structure

```text
<vault>/
  PaperA.md
  PaperB.md
  PaperC.md
  多篇论文对比.md
  attachments/
  pdfs/
```

PDFs are copied into the vault and linked using Obsidian internal links, for example:

```markdown
- 本地 PDF：[[pdfs/PaperA.pdf]]
```

Framework or method figures are stored under `attachments/` and embedded as:

```markdown
![[attachments/PaperA-method.png]]
```

## Single-Paper Note Template

The skill uses academic Chinese headings such as:

- 基本信息
- 链接
- 论文方法/框架图
- 研究背景与问题动因
- 核心科学问题
- 问题求解路径
- 方法定位
- 输入输出
- 方法框架
- 关键机制
- 主要创新贡献
- 数据集设计 / 代码结构 / 配置依赖
- 复现要点
- 与指标关联

## Multi-Paper Comparison Template

For multiple papers, the skill creates an overview note containing:

- comparison table
- local/online link table
- overall research-chain interpretation
- mapping to project indicators
- reproduction-priority recommendation

## Installation

Copy this folder into your Codex skills directory:

```text
C:\Users\<your-user>\.agents\skills\paper-obsidian-review
```

The required file is:

```text
paper-obsidian-review/SKILL.md
```

Restart Codex or reload the skill list if needed.

## Usage

Example prompts:

```text
用 paper-obsidian-review 帮我整理这三篇论文到 Obsidian。
```

```text
把这些论文、PDF 和代码仓库整理成 Obsidian 文献调研笔记，保留方法图和复现要点。
```

```text
按论文调研模板总结这几篇机器人交互论文，并映射到我的项目指标。
```

## Notes

This skill was created from a real workflow for organizing human-robot interaction papers, including CoCoDial, FAM-HRI, and TCC-IRoNL. It is general enough to support other paper-review and reproducibility-analysis tasks.

## License

MIT License. You may change this if your repository uses a different license.
