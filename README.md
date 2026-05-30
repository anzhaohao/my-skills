# Skills Backup

> Synced by [Skills Manager](https://github.com/cchao123/skills-managers) — a desktop app for managing AI coding agent skills.

## Use as a Claude Code marketplace

This repository is auto-generated as a [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces). Each skill below is exposed as an individually installable plugin.

In Claude Code, add this marketplace:

```bash
/plugin marketplace add anzhaohao/my-skills
```

Then install any skill you want:

```bash
/plugin install api-relay-audit@my-skills
```

Browse all available skills with `/plugin` after adding the marketplace, or see the full list in [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json).

## Skills (12)

| # | Skill | Description |
|---|-------|-------------|
| 1 | **api-relay-audit** | Audit third-party AI API relay/proxy services for security risks. Detects hidden prompt injection, prompt leakage, instruction override, identity hijacking (Chinese-market substitutes), jailbreak vulnerabilities, context truncation, tool-call package substitution (AC-1.a), error response header leakage (AC-2 adjacent), SSE-level stream integrity anomalies (AC-1 streaming), and Web3 prompt injection (SlowMist signature isolation). Use when: test relay, audit API, audit relay, detect injection, relay security, API relay audit, is this relay safe, does it inject prompts, test proxy API, check API key, 中转站安全, 测试中转站, 中转站审计. |
| 2 | **azf-obsidian-workflow** | An Zhaofeng's Obsidian project-record workflow. Use when Codex needs to create, evaluate, reorganize, or maintain Obsidian notes for a new or ongoing project, especially project folders under 01-Project, research/debugging workflows, experiment records, material/status images, hardware/software notes, progress handoff notes, or requests such as "帮我记录这个项目", "整理项目笔记", "建立主笔记", "根据图片更新实验记录", "维护工作流", "新项目也按这个方式记录". |
| 3 | **azf-personal-habits** | An Zhaofeng's global personal working habits for any intelligent agent. Use at the start of tasks for An Zhaofeng, especially programming, writing Markdown documents, project planning, debugging, research workflows, long-running handoffs, Git/GitHub version control, rollback-sensitive changes, or any task where personal preferences affect execution. Prioritize these habits: proactive Git branch/commit/push/tag/rollback reminders during coding, progress handoff files for multi-step projects, concise checkpointing, and no duplicate title inside Markdown document body content when creating .md files. |
| 4 | **deep-learning-experiment-record** | Fill or update deep-learning experiment records in Markdown or Obsidian from archived experiment artifacts such as configs, manifests, train logs, metrics JSON, figures, predictions, checkpoints, and prior baseline notes. Use when the user asks to 整理实验记录, 填入实验记录, update an Obsidian experiment note, summarize a training run, compare deep-learning experiments, or convert training outputs into a beginner-friendly research log across any project or agent environment. |
| 5 | **karpathy-guidelines** | Behavioral guidelines to reduce common LLM coding mistakes. Use when writing, reviewing, or refactoring code to avoid overcomplication, make surgical changes, surface assumptions, and define verifiable success criteria. |
| 6 | **nature-data** | Prepare, audit, or revise Nature-ready Data Availability statements, data repository plans, dataset citations, and FAIR metadata checklists for manuscripts. Use when the user asks about Nature data availability, research data sharing, repository selection, accession numbers, restricted or sensitive data, source data, supplementary datasets, DataCite-style dataset references, FAIR metadata for academic publication, or Chinese-to-English data availability wording for Chinese-speaking authors preparing Nature-family submissions. |
| 7 | **nature-figure** | Submission-grade Nature/high-impact journal figure workflow for Python or R. Use whenever the user asks to create, revise, audit, or polish manuscript figures, multi-panel scientific plots, or journal-ready SVG/PDF/TIFF outputs, especially for Nature-family or other high-impact journals. Before plotting, define the figure's conclusion, evidence logic, export needs, and review risks. If the user has not chosen Python or R, ask "Python or R?" and stop. Use only the selected backend for figure generation, previewing, exporting, and QA. Supports matplotlib/seaborn and ggplot2/patchwork/ComplexHeatmap. Not for dashboards or Illustrator/Figma-first infographics. |
| 8 | **nature-paper2ppt** | Build a complete but efficient Nature-style Chinese PPTX presentation from a scientific paper, preprint, PDF, article text, abstract, figure legends, or reading notes. Use this skill whenever the user asks to make slides/PPT/PPTX for journal club, group meeting, paper sharing, thesis seminar, lab meeting, department report, or academic presentation from a research paper, not only medical papers. It identifies the paper type and argument, selects only the figures needed for the story, writes Chinese slide content and speaker notes, creates the actual .pptx deck, and performs lightweight verification with cross-platform Python tooling by default. |
| 9 | **nature-polishing** | Polish, restructure, or translate academic prose into Nature-leaning English using the paper-architecture and writing-strategy principles from Scientific English Writing & Communication, with phrase-level support from Academic Phrasebank. Use whenever the user asks to polish a manuscript paragraph, abstract, introduction, results, discussion, conclusion, title, methods section, or Chinese academic draft for publication-quality English. |
| 10 | **officecli** | Create, analyze, proofread, and modify Office documents (.docx, .xlsx, .pptx) using the officecli CLI tool. Use when the user wants to create, inspect, check formatting, find issues, add charts, or modify Office documents. |
| 11 | **** |  |
| 12 | **** |  |

