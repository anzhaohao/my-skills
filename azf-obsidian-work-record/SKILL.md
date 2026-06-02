---
name: azf-obsidian-work-record
description: An Zhaofeng's Obsidian project work-record system. Use when Codex needs to create a new Obsidian project record from scratch, reorganize an existing project, or maintain notes under 01-Project, especially total notes, mainline notes, debugging records, experiment records, hardware/software facts, project-understanding notes, material screenshots, or requests such as "帮我记录这个项目", "新开一个项目", "整理项目笔记", "建立总笔记", "同步调试记录", "根据图片更新实验记录", "新项目也按这个方式记录".
---

# AZF Obsidian Work Record

Use this skill to make An Zhaofeng's Obsidian project notes easy to resume and easy for a beginner to understand. The goal is not a formal archive; the goal is a compact work-record system where relationships between records are visible.

## Core Model

Maintain six note roles:

1. Total note: project entrance, current status, reading order, and navigation.
2. Mainline notes: connect related records into a few clear threads.
3. Debug records: chronological process records, handoff notes, bug notes, and experiment records.
4. Stable reference notes: hardware, environment, dependencies, protocols, and reusable facts.
5. Project-understanding notes: code maps, process explanations, source reading, and diagrams.
6. Supplement notes: GUI guides, plans, old schemes, temporary investigations, and archived material.

Keep the total note light. Put details into linked records, then use mainline notes to explain how those records relate.

## Preferred Folder Pattern

For a new or substantial existing project under `01-Project`, prefer single-digit numbered folders:

```text
项目文件夹/
  0_总览/
    项目名总笔记.md
    项目名新手阅读顺序.md
  1_主线笔记/
    主题A.md
    主题B.md
  2_调试记录/
    项目名调试进度.md
    实验记录/
      YYYYMMDD_本次测试或工作.md
  3_硬件信息/
  4_项目理解/
  5_补充资料/
```

Adjust names to the project, but keep the logic simple: `0` is where to start, `1` explains the main threads, `2` keeps process records, and later folders hold stable context.

## New Project Bootstrap

When An Zhaofeng opens a new project and asks to record it, create the same structure from the beginning instead of starting with a single loose main note.

Minimum useful bootstrap:

```text
项目文件夹/
  0_总览/
    项目名总笔记.md
    项目名新手阅读顺序.md
  1_主线笔记/
  2_调试记录/
    项目名调试进度.md
  3_硬件信息/
  4_项目理解/
  5_补充资料/
```

At creation time:

1. Put the current goal, known facts, immediate next step, and reading order in the total note.
2. Create a short debug progress note even if it only contains the first status snapshot.
3. Create an empty or initial `目前待解决的问题` section in the total note.
4. Ask whether code understanding/source breakdown is needed now:

```text
这个新项目要不要同时做代码拆解和项目理解笔记？如果暂时不需要，我会保留 `4_项目理解/` 空文件夹，先只维护工作记录。
```

5. If An Zhaofeng says no, keep `4_项目理解/` empty and do not create code maps, source breakdowns, or `.azf/project-notes.yaml`.
6. If An Zhaofeng says yes, let `azf-project-note-binding` own `.azf/project-notes.yaml` and the `4_项目理解/` code-understanding notes.
7. Create mainline notes only for real threads already known; otherwise leave `1_主线笔记/` empty or create one placeholder named after the first active thread.
8. If images or materials are added on day one, copy lightweight image files into the vault and embed them in the relevant note immediately; create the matching `Attachments/...` mirror naturally through Obsidian or move it together during cleanup.

## Total Note

Name it like `项目名总笔记.md`. It should answer "where are we now?" before anything else.

Use numbered section headings in total notes. Because the filename already carries the document title, do not add a duplicate body title; start top-level content sections at `#`. Prefer Chinese numerals, for example `# 一、现在先看这里`, `# 二、当前主线`, `# 三、最近调试记录`. Keep subsection headings short.

Preferred total-note flow:

1. `现在先看这里`: current status and immediate handoff.
2. `当前主线`: the few active threads that explain the project state.
3. `最近调试记录`: newest chronological records worth opening next.
4. `目前待解决的问题`: unresolved issue index and issue detail cards.
5. `新手阅读顺序`: beginner reading path.
6. `常用入口`: stable links and shortcuts.
7. `文件夹说明`: folder map.

When reorganizing an existing total note, keep the section content intact, move only whole top-level sections, then renumber the Chinese numeral prefixes to match the final order.

Use this shape:

```markdown
---
创建时间: YYYY-MM-DDTHH:mm
修改时间: YYYY-MM-DDTHH:mm
项目: 项目名
类型: 项目总笔记
状态: in-progress
aliases:
  - 旧总笔记名
---

# 一、现在先看这里

> [!summary] 当前状态
> - 当前阶段：
> - 当前结论：
> - 已经做通：
> - 还没做通：
> - 下一步：

# 二、当前主线

## 1. 主线名称

入口：[[主线笔记A]]
状态：
下一步：

# 三、最近调试记录

# 四、目前待解决的问题

> [!note] 阅读方式
> 上表只放索引；具体判断和下一步放在下面的问题卡片里。

| 事项 | 等级 | 问题 | 状态 |
|---|---|---|---|
| Q1 | 🚨 核心 |  | 🔥 待处理 |

## 问题详情

> [!todo] Q1
> - **当前判断：**  
> - **关联证据：**  
> - **下一步：**

# 五、新手阅读顺序

1. [[项目名新手阅读顺序]]
2. [[主线笔记A]]
3. [[主线笔记B]]

# 六、常用入口

# 七、文件夹说明
```

If a note is renamed, add aliases for old names instead of rewriting every old record.

## Unresolved Issues Table

Every total note should maintain a `目前待解决的问题` section near the top, usually after `当前主线` and `最近调试记录`, and before `新手阅读顺序`.

Use a compact index table to avoid cramped Markdown. Do not put long judgments, evidence, and next steps into the same table row.

```markdown
# 四、目前待解决的问题

| 事项 | 等级 | 问题 | 状态 |
|---|---|---|---|
| Q1 | 🚨 核心 |  | 🔥 待处理 |

## 问题详情

> [!todo] Q1
> - **当前判断：**  
> - **关联证据：**  
> - **下一步：**
```

Rules:

- In issue detail cards and status cards, prefer list syntax inside the callout: `> - **字段：** 内容`. This renders as a cleaner card with stable alignment, especially for `当前判断`, `关联证据`, `关联入口`, and `下一步`.
- Do not include an `入口` column in the issue index table. Put links and evidence in the issue detail card.
- Use clear item markers in the form `Q1`, `Q2`, `Q3` so unresolved issues are easy to cite in conversation and commits.
- Keep priority visually distinctive with icon labels instead of bare `P0` / `P1`.
- Preferred priority labels: `🚨 核心`, `⭐ 重要`, `🌱 后续`.
- `🚨 核心`: blocks the next experiment, debugging step, or core conclusion.
- `⭐ 重要`: important but can wait until the current core path is handled.
- `🌱 后续`: known limitation, cleanup, or future improvement.
- Keep the status set small, but make the icons visually obvious. Preferred status values are only: `🔥 待处理`, `⚙️ 进行中`, `✅ 已解决`, `💤 暂缓`.
- Put details such as "待排查", "待补充", or "待设计" in the issue card, not in the status column.
- Link each issue to the mainline note, debug record, hardware card, or project-understanding note that carries details.
- When new progress arrives, update this table first if it changes an active issue.
- If an issue needs more than one short phrase of explanation, put the detail in the `问题详情` card, not in the table.
- Do not let solved problems disappear without trace; mark them `✅ 已解决` or move the details to the relevant debug/mainline note if the table is getting too long.

## Mainline Notes

Use mainline notes when raw records are too isolated to show relationships. A mainline note should summarize one thread, not duplicate every detail.

Suggested structure:

```markdown
---
项目: 项目名
类型: 主线笔记
状态: in-progress
---

## 一句话说明

## 当前结论

## 过程脉络

1. [[相关记录1]]
2. [[相关记录2]]

## 关键证据

## 还没完成

## 下一步
```

Good mainline topics include "光谱仪连接与采集", "波长映射与频率插值", "FROG迹图反演与结果保存", or the equivalent threads for another project.

## Debug Records

Use `2_调试记录` for things that happened while working: progress handoff, debugging sessions, bug reviews, hardware tests, and experiment records.

- Existing experiment-record Markdown files should be moved under `2_调试记录/实验记录/` when the user wants a simpler structure.
- Do not rewrite old experiment records unless the user asks. If a later conclusion changes the interpretation, add a new note or a `后续更正` section only when appropriate.
- Keep chronological evidence in records; keep relationship summaries in mainline notes.

Event record template:

```markdown
---
创建时间: YYYY-MM-DDTHH:mm
修改时间: YYYY-MM-DDTHH:mm
项目: 项目名
类型: 实验记录 / 调试记录 / Bug复盘
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

## Reference And Supplement Notes

Use stable reference notes for facts that should not be rediscovered:

- Hardware cards: model, serial number, wavelength range, driver, cable, connection method, current status.
- Environment cards: conda env, packages, DLLs, vendor software, data paths.
- Project understanding: what the project does, source modules, data flow, risks.
- SOP notes: repeated operation steps.

Use supplement notes for GUI guides, dependency notes, old plans, code-reading introductions, and result evaluations.

## Images And Attachments

Images are first-class evidence in An Zhaofeng's notes. Do not treat them as secondary attachments.

Default rule:

- If An Zhaofeng provides a lightweight image, screenshot, GUI capture, plot, result figure, equipment photo, or document photo, copy it into the Obsidian vault and embed it directly in the most relevant Markdown note with `![[...]]`.
- Put the image close to the explanation that depends on it, usually before the bullet list of observed facts or directly under a section such as `图片证据`, `实验结果`, `官方资料截图`, or `现象截图`.
- Prefer one well-placed embedded image over a text-only summary. A note should be understandable by looking at the image first, then reading the interpretation.
- Use an external path only for large, sensitive, proprietary, or bulky raw files that should not be duplicated into the vault. In that case, explain why the file was not copied.
- For repeated images, embed the image in the canonical evidence note and link to that note from lighter summary/mainline notes.

When reorganizing Obsidian notes:

1. Move the matching attachment mirror folders under `Attachments/...` as well as the Markdown files.
2. Preserve image filenames; do not rename images just to make the tree prettier.
3. Use readable copied filenames for newly added evidence images when possible, for example `Zolix_SGM1700_官方波长范围_20260601.png`.
4. If a note embeds `![[image.png]]`, verify that the image still exists somewhere in the vault.
5. If an attachment path uses an explicit folder path, update it to the new folder.

When An Zhaofeng sends photos or screenshots, classify them first:

| Type | Examples | Destination |
|---|---|---|
| Hardware status | equipment, labels, cables, ports | hardware info or debug record |
| Software status | GUI, settings, device manager, terminal | debug record |
| Result | spectrum, trace, plots, reconstruction | debug record and mainline note |
| Error | dialog, logs, stack trace | bug review |
| Source material | SDK folders, manuals, drivers | reference or supplement note |

Record each image as fact first, judgment second. For important images, include the embedded image, then a short list:

```markdown
![[图片文件名.png]]

- 图片来源：
- 直接可见事实：
- 当前判断：
- 应同步到：
```

## Reorganization Rules

Before broad changes:

1. Read the current tree with `rg --files`.
2. Read the total note, progress/debug note, and recent records.
3. Create a rollback backup under `Desktop\Codex备份\YYYYMMDD_HHMMSS_任务名_修改前备份`.
4. Move notes and attachment mirrors together.
5. Update navigation notes, old aliases, and direct attachment paths.
6. Verify ordinary wikilinks and embedded images after the move.

For verification, report counts like:

```text
WIKILINK_MISSING=0
EMBED_MISSING_OUTSIDE_CODE=0
```

Ignore placeholder image names inside fenced code templates when checking embeds.

## Writing Style

- Use plain Chinese and write like a clear lab handoff.
- Separate "what I saw" from "what I think it means".
- Do not write uncertain things as confirmed.
- Keep names short and beginner-friendly.
- Avoid making the total note a raw log.
- When creating a Markdown note, do not repeat the filename as a first `# ...` heading unless requested.

## Deep Learning Experiment Link

When the record involves deep-learning runs, metrics, checkpoints, figures, or baselines, use `azf-deep-learning-experiment-record` for evidence writing. This skill remains responsible for the project-level note structure, total note, mainline notes, and debug-record placement.

## Maintenance Closeout

At the end of a maintenance pass:

1. Confirm the total note's current status is fresh.
2. Confirm the total note's `目前待解决的问题` section is fresh.
3. Confirm mainline notes explain how different records relate.
4. Confirm debug records are in `2_调试记录`.
5. Confirm old links are covered by aliases or updated paths.
6. Confirm attachment embeds still resolve.
7. Tell An Zhaofeng what changed and where the backup is.
