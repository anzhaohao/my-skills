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

Keep the total note light. Put details into linked records, then use mainline notes to explain how those records relate. For ongoing projects, treat the total note as a dashboard, not as the place where every recent record, shortcut, and folder explanation lives.

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
8. If the project will accumulate small bug/debug records, create or plan a lightweight "未归类调试记录 / 小 bug 收件箱" in the total note. Prefer an Obsidian Bases `.base` file when available; otherwise use a manual table.
9. If images or materials are added on day one, copy lightweight image files into the vault and embed them in the relevant note immediately; create the matching `Attachments/...` mirror naturally through Obsidian or move it together during cleanup.

## Total Note

Name it like `项目名总笔记.md`. It should answer "where are we now?" before anything else.

Use numbered section headings in total notes. Because the filename already carries the document title, do not add a duplicate body title; start top-level content sections at `#`. Prefer Chinese numerals, for example `# 一、现在先看这里`, `# 二、当前主线`, `# 三、目前待解决的问题`. Keep subsection headings short.

Preferred total-note dashboard flow for active projects:

1. `现在先看这里`: current status and immediate handoff.
2. `当前主线`: the few active threads that explain the project state.
3. `目前待解决的问题`: unresolved issue index and issue detail cards.
4. `未归类调试记录 / 小 bug 收件箱`: automatically or manually list records that have not yet been attached to a mainline note.

Move longer navigation material out of the total note:

- Put beginner reading order in `0_总览/项目名新手阅读顺序.md`.
- Put stable shortcuts and folder explanations in the beginner/navigation note or another supplement note.
- Do not keep long `最近调试记录`, `新手阅读顺序`, `常用入口`, or `文件夹说明` sections in the total note once the project has a stable structure.

When reorganizing an existing total note, keep the section content intact, move only whole top-level sections, then renumber the Chinese numeral prefixes to match the final order.

Use this shape. Keep it dashboard-like: the total note is for "where are we now", not for full process history.

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

理解本项目参考：[[项目流程理解总图]]

> [!summary] 当前阶段
> 项目当前处在“……”阶段。

# 二、当前主线

## 1. 主线名称

- **入口：** [[【主线】主线名称]]
- **当前状态：** 用一句话说明这条主线现在到哪了。

### 1.1 从上面主线引出的独立问题

- **入口：** [[【主线】从属问题主线]]
- **从属关系：** 这是上面主线过程中发现的问题，但仍保留为独立主线笔记。
- **当前状态：** 用一句话说明当前理解。

# 三、目前待解决的问题

> [!note] 阅读方式
> 上表只放索引，避免太挤；具体理解放在下面的问题卡片里。

| 事项 | 等级 | 问题 | 状态 |
|---|---|---|---|
| Q1 | 🚨 核心 |  | 🔥 待处理 |

## 问题理解

> [!todo] Q1
> - **理解：**  
> - **主线入口：** [[【主线】主线名称]]

# 四、未归类调试记录 / 小 bug 收件箱

> [!note] 使用方式
> 新建小 bug 或临时调试记录时，先判断它能否接入已有主线。能接入时，直接写 `归类状态: 已归类`，并补上 `关联主线`；暂时没有合适主线时，才写 `归类状态: 未归类`，让它进入这里。每次整理结束时，需要向用户说明本次记录的归类判断。

![[项目名未归类调试记录.base]]
```

If a note is renamed, add aliases for old names instead of rewriting every old record.

Total-note rules:

- The mainline display title in the total note may be more direct than the filename. Do not rename the mainline file just to improve the dashboard title.
- A mainline derived from another mainline can be shown as an indented `### 1.1 ...` block, but it should remain an independent mainline note when it has its own reusable problem logic.
- In `当前主线`, do not use tables. Use short Markdown bullets with bold field labels, such as `- **入口：** ...` and `- **当前状态：** ...`; add `- **从属关系：** ...` only for subordinate mainlines.
- Do not include `下一步` in the mainline list by default. The total note should stay clean; next actions belong in records or direct user planning unless the user explicitly asks for them.

## Unresolved Issues Table

Every total note should maintain a `目前待解决的问题` section near the top, usually after `当前主线` and before `未归类调试记录 / 小 bug 收件箱`.

Use a compact index table to avoid cramped Markdown. Do not put long judgments, evidence, and next steps into the same table row. Prefer a `问题理解` section below the table; it should explain the problem in plain words and link only to the mainline entrance.

```markdown
# 四、目前待解决的问题

| 事项 | 等级 | 问题 | 状态 |
|---|---|---|---|
| Q1 | 🚨 核心 |  | 🔥 待处理 |

## 问题理解

> [!todo] Q1
> - **理解：**  
> - **主线入口：** [[【主线】主线名称]]
```

Rules:

- In issue detail cards and status cards, prefer list syntax inside the callout: `> - **字段：** 内容`. This renders as a cleaner card with stable alignment, especially for `理解` and `主线入口`.
- Do not include an `入口` column in the issue index table. Put links and evidence in the issue detail card.
- Use clear item markers in the form `Q1`, `Q2`, `Q3` so unresolved issues are easy to cite in conversation and commits.
- Keep priority visually distinctive with icon labels instead of bare `P0` / `P1`.
- Preferred priority labels: `🚨 核心`, `⭐ 重要`, `🌱 后续`.
- `🚨 核心`: blocks the next experiment, debugging step, or core conclusion.
- `⭐ 重要`: important but can wait until the current core path is handled.
- `🌱 后续`: known limitation, cleanup, or future improvement.
- Keep the status set small, but make the icons visually obvious. Preferred status values are only: `🔥 待处理`, `⚙️ 进行中`, `✅ 已解决`, `💤 暂缓`.
- Put details such as "待排查", "待补充", or "待设计" in the issue card, not in the status column.
- Link each issue primarily to the mainline note that carries the relationship. Do not put debug/work/experiment records from `2_调试记录/` in a Q issue card; attach those process records to the relevant mainline note instead.
- When new progress arrives, update this table first if it changes an active issue.
- If an issue needs more than one short phrase of explanation, put the detail in the `问题理解` card, not in the table.
- Do not let solved problems disappear without trace; mark them `✅ 已解决` or move the details to the relevant debug/mainline note if the table is getting too long.

## Small Bug Inbox And Mainline Attachment

Small bugs should not each become their own mainline note by default, but every bug/debug record must be findable from a common entrance.

## Q Issue Card And Mainline Sync

The total note's `Q1` / `Q2` / `Q3` issue cards are status entrances, not the final place for process history. When a new record, code change, verification result, GUI finding, or design decision changes an active Q issue and also belongs to an existing mainline, update both layers in the same sync pass.

Important permission boundary:

- This synchronization rule applies only when An Zhaofeng explicitly asks to update/sync/write/organize Obsidian notes or confirms a proposed note-sync pass.
- During ordinary code modification, debugging, Git work, hardware troubleshooting, or log reading, the Obsidian vault is read-only by default. Read notes for context if useful, but do not update total notes, mainline notes, debug records, or hardware cards.
- If code/debug progress should be recorded but An Zhaofeng did not ask for note updates, leave the note vault untouched and report that note synchronization is pending.

Use this rule especially when the user asks to update a work record, debug record, or project status:

1. Update the total note's Q issue table/card only as the dashboard entry: short problem understanding, mainline entrance, and status. Link only mainline notes by default; never link concrete debug/work/experiment records from `2_调试记录/`.
2. Create or update the concrete debug/work record under `2_调试记录/`, including frontmatter `归类状态: 已归类` and `关联主线`.
3. Append the record to the relevant mainline note's `过程脉络`, then rewrite the relevant Step in plain language if the new record changes the thread.
4. If the progress is a prerequisite for another mainline, add a short cross-link in `辅助说明与相关入口`; do not rely on the Q card alone to carry that relationship. Keep concrete debug-record links in mainline `过程脉络`, not in the Q card.
5. End the user-facing response by reporting the sync coverage, for example: `已更新总笔记 Q3、调试记录、[[根据中心波长自动选择光谱仪]] 主线` or `只更新了 Q3，主线未改，因为...`.

Avoid the common mistake: updating only `FrogTrace项目总笔记.md` 的 Q 入口 while leaving the corresponding `1_主线笔记/` page stale. For example, a change such as "analysis wavelength range is automatically derived from spectrometer wavelengths and pixel window" may appear in Q3, but if it is a prerequisite for "根据中心波长自动选择光谱仪", it must also be appended to that mainline as process context.

Default rule:

1. Create the concrete bug/debug process record under `2_调试记录/`.
2. Before setting classification, inspect existing mainline notes in `1_主线笔记/` and decide whether the new record belongs to one of them.
3. If the record belongs to an existing mainline, add frontmatter like this:

```yaml
项目: 项目名
类型: 调试记录
状态: 已验证 / 待复测 / 待补证据
归类状态: 已归类
关联主线:
  - 主线名称
```

Then update the relevant mainline note's `过程脉络` or `关键证据` section with a link to the record.

4. If no existing mainline is a good fit, add frontmatter like this:

```yaml
项目: 项目名
类型: 调试记录
状态: 已验证 / 待复测 / 待补证据
归类状态: 未归类
关联主线:
```

Also add a short `## 归类判断` section near the top of the record explaining why it is currently unclassified and what future mainline might absorb it.

5. Show only unclassified records from the total note's `未归类调试记录 / 小 bug 收件箱`.
6. At the end of the user-facing response, always report the classification decision: either `已归类到 [[主线名]]` or `暂未归类，原因是...`.

Use a new mainline note only when the bug reveals a reusable project thread, such as hardware state management, wavelength mapping, acquisition flow, reconstruction output, dependency/environment setup, or another theme that will likely connect multiple records. Otherwise attach it to an existing mainline or a broad `问题与修复总线` if no better mainline exists yet.

When Obsidian Bases is available, create a `.base` file for the inbox and embed it in the total note. The `.base` file can filter by `项目 == "项目名"` and `归类状态 == "未归类"`. Because every row is already unclassified, do not show a `归类状态` column in the view. Because unclassified rows usually have no mainline yet, do not show an `关联主线` column unless the user explicitly wants it. Prefer compact columns such as `记录`, `类型`, `状态`, and `修改时间`. If Bases is unavailable or the format is uncertain, use a manual Markdown table and leave a note to convert it later.

## Mainline Notes

Use mainline notes when raw records are too isolated to show relationships. A mainline note should summarize one thread, not duplicate every detail.

Suggested structure:

```markdown
---
项目: 项目名
类型: 主线笔记
状态: in-progress
---

# 一句话说明

# 辅助说明与相关入口

先用几句话写清楚这条主线的问题语义、背景、为什么它需要单独成线。这里可以写“背景是”“具体来说就是”，并放一条最重要的高亮判断。

> [!NOTE] 关系说明
> - 这条主线解决什么。
> - 它和相邻主线的边界是什么。

- 相邻主线：[[【主线】相邻主线]]
- 相关硬件：[[硬件卡片]]
- 参考方案：[[【方案】方案名称v0]]、[[【方案】方案名称v1]]
- 代码修改：[[YYYYMMDD_主题代码修改]]

# 过程脉络

## Step 1：实际发生的一段推进（YYYY-MM-DD）

写这一步实际发生了什么，以及它让这条主线的理解发生了什么变化。只有真实发生过或正在发生的推进才写进 Step；不要提前铺满未来空步骤。

- <mark style="background:#fff88f">用一句话写出这一步带来的关键判断。</mark>
```

Good mainline topics include "光谱仪连接与采集", "波长映射与频率插值", "FROG迹图反演与结果保存", or the equivalent threads for another project.

`过程脉络` is a chronological/process section written as `Step 1`, `Step 2`, `Step 3`. Each step should explain why that step exists, what it changed in the understanding, and which concrete record or plan carries the detail. Do not use the old four-part debug style (`为什么做` / `这次想确认` / `得到的判断` / `对本主线的影响`) inside mainline notes.

Mainline note body sections should normally start at `#` level, because the filename already acts as the document title. Use `# 辅助说明与相关入口` as a separate top-level chapter after `# 一句话说明` when it helps keep entrances visible.

If a reader needs context notes before reading the process, place them near the beginning in `# 辅助说明与相关入口`. Typical entries are `相邻主线`, `相关硬件`, `参考方案`, `代码修改`, `GUI说明`, and `源码理解`. Keep neighboring mainlines, hardware cards, and方案 notes in this entrance section unless they are the subject of an actual process step.

For newly created or lightly developed mainlines, prefer this layout:

1. Put problem semantics, background, "具体来说就是", and the key highlighted judgment in `# 辅助说明与相关入口`.
2. Put the callout after the plain explanation, using it to summarize relationships or boundaries rather than replacing the explanation.
3. Put ordinary entrance links after the explanation/callout so the reader first understands the problem and then chooses where to jump.
4. Use `# 过程脉络` only for work that has actually happened or is actively being performed.
5. Do not pre-create many empty future Steps. If An Zhaofeng explicitly asks to leave not-yet-done Steps blank, keep at most one broad next-action Step, such as `## Step 1：制定 GUI 与流程方案并修改代码（YYYY-MM-DD）`, instead of splitting it into multiple empty `Step 2/3/4/5`.

Mainline-writing rules:

- Start mainline filenames with `【主线】` unless the user says otherwise. Do not force rename older files without asking.
- Mainlines should sound like a clear handoff for a future beginner: "具体来说就是..." is better than formal abstract wording.
- `过程脉络` may include方案 links when the step is about制定方案, but do not pretend a方案 note is a调试记录.
- After each debugging or implementation step, write what that step taught us, not only that the step happened.
- Step titles should describe a natural chunk of progress. If design and implementation are one continuous work chunk, combine them in one Step title rather than forcing artificial substeps.
- Keep `当前理解`, `当前卡点`, and `下一步` out of mainline notes by default; fold useful parts into `过程脉络`.
- Use highlighted `<mark style="background:#fff88f">...</mark>` sparingly for the one judgment a future reader must not miss.
- A mainline derived from another mainline can remain independent. Show the hierarchy in the total note; keep the mainline note itself focused on its own problem.

## Debug Records

Use `2_调试记录` for things that happened while working: code debugging, hardware tests, bug reviews, log reading, real-device validation, Git-backed changes, and progress handoff.

There is only one debug-record body format for FrogTrace-style records: the timeline debug process format below. Do not create separate debug-record templates such as `实机验证记录`, `代码修改记录`, test-sheet records, or standalone Git-card records. If a note is a debug/process record, use the same timeline structure regardless of whether the work is code-only, hardware-only, real-device validation, or mixed code + hardware.

- Existing experiment-record Markdown files should be moved under `2_调试记录/实验记录/` when the user wants a simpler structure.
- Do not rewrite old experiment records unless the user asks. If a later conclusion changes the interpretation, add a new note or a `后续更正` section only when appropriate.
- Keep chronological evidence in records; keep relationship summaries in mainline notes.
- If a debug/work/experiment record is tied to code in a Git repository, include code version information inside the relevant chronological Step. Do not put the Git version only in a project progress file, code-sync note, or commit message.

Git-bound debug records must state:

- code repository path;
- current branch and remote tracking branch when known;
- base/start commit, feature commit, and current/record commit;
- push status and working-tree status;
- the verification commands that belong to that code version;
- the Git graph command used;
- a complete visualization, preferably a Mermaid `gitGraph`, placed inside the Step where the branch/commit/code change actually happened. If Mermaid would be misleading, include a raw `git log --oneline --graph --decorate` excerpt in that same Step.

For modern FrogTrace-style records, use top-level `#` headings because the filename already carries the title. Avoid a duplicate body title.

### Timeline Debug Process Record

```markdown
---
创建时间: YYYY-MM-DDTHH:mm
修改时间: YYYY-MM-DDTHH:mm
项目: 项目名
类型: 调试记录
记录类型: 代码调试 / 硬件调试 / 代码与硬件联合调试 / 实机验证 / 结果复测
调试日期: YYYY-MM-DD
状态: 已记录 / 进行中 / 待复测
归类状态: 未归类 / 已归类
关联主线:
  - 主线名
---

# 一、调试目标

用几句话说明这次到底在解决什么问题。先写外行也能看懂的现象和目标，不要一上来写代码细节。

# 二、调试过程

## Step 1：先发生了什么

操作：

现象：

判断：

证据入口：

## Step 2：接着怎么排查或修改

操作：

涉及文件：

现象：

处理：

验证：

判断：

## Step 3：如果发生了代码提交或分支变化，把 Git 放在这里

操作：

涉及文件：

验证：

Git 信息：

```text
代码仓库：
当前分支：
远端分支：
起点提交：
当前/记录提交：
推送状态：
工作区状态：
验证命令：
Git 图命令：
```

Git 可视化：

```mermaid
gitGraph
   commit id: "base"
   branch "feature-or-current"
   checkout "feature-or-current"
   commit id: "current HEAD"
```

判断：

# 三、调试结论

1. 已经确认什么。
2. 已经修掉什么。
3. 还没有彻底解决什么。
4. 下一次应该从哪里继续。
```

Timeline debug process rules:

- Keep the main structure fixed as `调试目标` -> `调试过程` -> `调试结论`.
- Write `Step 1`, `Step 2`, `Step 3` in real chronological order. Each Step should explain what was done, what was seen, and what judgment changed.
- The small fields inside each Step are flexible. Use only what the step needs: `操作`, `现象`, `证据入口`, `涉及文件`, `处理`, `验证`, `判断`, `Git 信息`, or `Git 可视化`.
- Tables are allowed inside Steps when they compare devices, expected/actual behavior, pass/fail items, files, commands, or result paths. Do not turn the whole record into a test sheet.
- Do not manually expand code diffs. For code-related steps, write the intent, affected files, verification result, Git commit/branch/card, and evidence paths. Codex can recover exact code changes from Git later.
- Put Git cards and Mermaid `gitGraph` inside the Step where the code change, branch change, commit, push, or rollback happened. Do not create a separate top-level Git chapter.
- Make Git visualization complete enough to reconstruct the branch story. For a simple linear branch, include the relevant current-branch commits from the branch/start point through the current HEAD, not only a three-node sketch. If there are important side branches in the visible history, either include them in Mermaid or add the raw `git log --graph` excerpt under the Mermaid.
- Use highlighted `<mark style="background:#fff88f">...</mark>` sparingly for the one judgment future An Zhaofeng must not miss.
- Planned on-site checklists are still allowed, but if they live under `2_调试记录`, write them in the same timeline format with `状态: 待复测` and future-tense Steps. Do not introduce a separate top-level template.

## Reference And Supplement Notes

Use stable reference notes for facts that should not be rediscovered:

- Hardware cards: model, serial number, wavelength range, driver, cable, connection method, current status.
- Environment cards: conda env, packages, DLLs, vendor software, data paths.
- Project understanding: what the project does, source modules, data flow, risks.
- SOP notes: repeated operation steps.

Use supplement notes for GUI guides, dependency notes, old plans, code-reading introductions, and result evaluations.

### Hardware Information Notes

Hardware notes should stay fact-first. They are reference cards, not debug records.

For a hardware type or model index card, the core content is the index. When there are multiple physical devices, prefer an Obsidian Bases `.base` table filtered by `项目`, `类型`, and `设备类型`. Show useful columns such as device card, serial number, status, and modified time. Do not filter the index by a code-specific field such as `FrogTrace类型` unless the user explicitly wants that.

Recommended type/model card shape:

```markdown
# 光谱仪索引

![[设备索引.base]]

# 型号通用信息

| 项目 | 记录 |
|---|---|
| 设备类型 |  |
| FrogTrace 类型 | `...` |
| 波长范围来源 |  |

# 可选补充

- 关联记录：
```

For a concrete physical device card, the core content is `# 硬件信息` plus a two-column table. Put serial number, current status, wavelength range, pixel count, source file, connection/cable facts, and data source there first. Photos, connection method, warnings, and related records are optional supplements after the hardware table.

Recommended concrete-device card shape:

```markdown
# 硬件信息

| 项目 | 记录 |
|---|---|
| 设备类型 |  |
| FrogTrace 类型 | `...` |
| S/N | `...` |
| 当前状态 |  |

# 可选补充

- 关联记录：
```

Avoid using `当前结论`, `YYYY-MM-DD 记录`, or `下一步` as the main section structure of hardware cards. If the content is process history, put it in `2_调试记录/` and link it from the hardware card only when it helps identify the device.

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
3. Create a rollback backup under `E:\software\CodexPlusPlus\Codex备份\YYYYMMDD_HHMMSS_任务名_修改前备份`.
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
