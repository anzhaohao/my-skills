---
name: azf-obsidian-workflow
description: An Zhaofeng's Obsidian project-record workflow. Use when Codex needs to create, evaluate, reorganize, or maintain Obsidian notes for a new or ongoing project, especially project folders under 01-Project, research/debugging workflows, experiment records, material/status images, hardware/software notes, progress handoff notes, or requests such as "帮我记录这个项目", "整理项目笔记", "建立主笔记", "根据图片更新实验记录", "维护工作流", "新项目也按这个方式记录".
---

# AZF Obsidian Workflow

Use this skill to help An Zhaofeng turn a project folder into a clear, recoverable Obsidian workflow. The goal is not to make notes look formal; the goal is to make future work easy to resume.

## Core Idea

Maintain five kinds of notes:

1. Main workflow note: the project entrance, current status, and navigation.
2. Progress handoff note: what has been confirmed, what is blocked, and what to do next.
3. Daily or event-based records: what happened in one experiment, debugging session, meeting, or test.
4. Stable reference notes: hardware info, environment info, dependencies, background, protocol, or concept explanation.
5. Supplement notes: bug reviews, plans, code-reading notes, version comparisons, and temporary investigations.

Keep the main note light. Put long details in linked records or supplement notes.

## Style

Write like a clear lab handoff in An Zhaofeng's own working-note tone.

- Prefer common Chinese.
- Explain necessary technical terms in one short sentence.
- Separate "what I saw" from "what I think it means".
- Do not pretend uncertain things are confirmed.
- Keep old mistaken records when they explain the real debugging path, but add a visible "后续更正".
- Avoid jargon piles. A note should still make sense when An Zhaofeng opens it two weeks later while tired.
- When creating a Markdown note, do not repeat the filename as a first `# ...` heading unless requested.

## Before Editing Existing Notes

When changing existing project notes:

1. Read the folder structure first with `rg --files`.
2. Read the main note, progress note, and the most recent experiment/supplement notes before deciding.
3. If the change is broad or the user asks for backup, create a rollback backup before edits.
4. If no backup path is specified, use:

```text
Desktop\Codex备份\YYYYMMDD_HHMMSS_任务名_修改前备份
```

Preserve the useful directory structure inside the backup folder.

## New Project Folder Pattern

For a new project under `01-Project`, prefer this shape:

```text
项目文件夹/
  项目名工作流.md
  项目名进度交接.md
  实验记录/
    YYYYMMDD_本次测试或工作.md
  硬件信息/
    设备名.md
  补充笔记/
    项目理解.md
    依赖与环境.md
    【Bug】YYYYMMDD-问题.md
    方案-v0.md
    方案-v1.md
```

Adjust folder names to match the project. For non-experiment projects, replace `实验记录` with `工作记录`, `调试记录`, or another natural name.

## Main Workflow Note

The main note should answer "where are we now?" before anything else.

Use this opening structure:

```markdown
---
创建时间: YYYY-MM-DDTHH:mm
修改时间: YYYY-MM-DDTHH:mm
项目: 项目名
类型: 工作流
状态: in-progress
---

## 当前状态

> [!summary] 现在先看这里
> 更新时间：
> 当前阶段：
> 当前结论：
> 已验证：
> 还没完成：
> 下一步：

## 工作流入口

- 项目理解：[[项目理解]]
- 阶段进度：[[项目名进度交接]]
- 最近记录：
- 关键资料：
- 图片/材料记录模板：
```

The main note may also include background, final goal, important decisions, and a compact workflow map. Do not let it become a long raw log.

## Progress Handoff Note

Use this when a future chat, future model, or tired future self needs to resume quickly.

It should include:

- First sentence for the next model.
- Current status table.
- Confirmed facts.
- Important file paths and source materials.
- Current blockers.
- Do-not-do-first warnings.
- Next recommended steps.
- Dated update sections near the end.

When old notes are superseded, say so explicitly instead of deleting them.

## Event Records

Use one note per experiment, debugging session, hardware test, meeting, or meaningful work block.

Suggested structure:

```markdown
---
创建时间: YYYY-MM-DDTHH:mm
修改时间: YYYY-MM-DDTHH:mm
项目: 项目名
类型: 实验记录
阶段:
结果: success / partial / fail
---

## 本次目标

## 材料状态

## 操作记录

## 结果

## 问题与原因判断

## 下一步

## 后续更正
```

Use `后续更正` when a later finding changes the interpretation of this record.

## Stable Reference Notes

Use stable reference notes for information that should not be rediscovered every time:

- Hardware cards: model, serial number, power, cable, driver, connection method, current status.
- Dependencies and environment: conda env, packages, drivers, DLLs, external software.
- Project understanding: what the project does, important modules, main workflow, risks.
- Protocol or SOP: how to run a repeated operation.

Put a compact table near the top when the note is a device or environment card.

## Supplement Notes

Use supplement notes for deep dives:

- Bug notes: `【Bug】YYYYMMDD-问题.md`
- Fix notes: `【修Bug】YYYYMMDD-问题.md`
- Plans: `方案-v0.md`, `方案-v1.md`
- Code-reading notes: `模块名介绍.md`
- Result evaluations: `某次测试结果评价.md`

Mark version notes clearly:

```yaml
status: 当前参考 / 已归档 / 已被后续方案替代
```

## Image And Material Recording

When An Zhaofeng sends photos or screenshots, classify them first:

| Type | Examples | Likely destination |
|---|---|---|
| Hardware status | equipment, labels, cables, power, ports | hardware info or event record |
| Software status | GUI, settings, device manager, terminal | event record |
| Result | spectrum, trace, plots, reconstruction result | event record and main status |
| Error | dialog, logs, stack trace | bug note |
| Source material | SDK folders, manuals, driver packages | reference or supplement note |

For each image, record:

```markdown
### 图片：文件名

图片类型：

我能直接看到的事实：
- 

我的判断：
- 

还不能确定的地方：
- 

应该更新到的笔记：
- 
```

If image evidence changes the project status, update the main workflow note's `当前状态` block.

## Maintenance Rules

At the end of a project-note maintenance pass:

1. Check whether the main note has a fresh `当前状态`.
2. Check whether the progress note reflects the latest conclusion.
3. Check whether old wrong assumptions are marked with `后续更正`.
4. Check whether long details live outside the main note.
5. Check whether the next step is concrete enough to act on.
6. Tell An Zhaofeng exactly which notes changed and where the backup is.
