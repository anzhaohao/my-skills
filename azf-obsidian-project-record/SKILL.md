---
name: azf-obsidian-project-record
description: An Zhaofeng's Obsidian project-record system. Use when Codex needs to create a new Obsidian project record from scratch, reorganize an existing project, or maintain notes under 01-Project, especially total notes, mainline notes, debugging/experiment records, project-understanding notes, material screenshots, and project indexes, or requests such as "帮我记录这个项目", "新开一个项目", "整理项目笔记", "建立总笔记", "同步调试记录", "根据图片更新实验记录", "新项目也按这个方式记录".
---

# AZF Obsidian Project Record

Use this skill to make An Zhaofeng's Obsidian project notes easy to resume and easy for a beginner to understand. The goal is not a formal archive; the goal is a compact work-record system where relationships between records are visible.

## Core Model

Maintain five project-note roles:

1. Total note: project entrance, current status, reading order, and navigation.
2. Mainline notes: connect related records into a few clear threads.
3. Debug records: chronological process records, handoff notes, bug notes, and experiment records.
4. Project-understanding notes: code maps, process explanations, source reading, and diagrams.
5. Supplement notes: GUI guides, plans, environment/dependency explanations, old schemes, temporary investigations, and archived material.

Keep the total note light. Put details into linked records, then use mainline notes to explain how those records relate. For ongoing projects, treat the total note as a dashboard, not as the place where every recent record, shortcut, and folder explanation lives.

Hardware asset cards are outside this skill. The dedicated folder `E:\software\Obsidian\安钊锋的外置大脑\03-Academic Toolkit\2_资源与档案\仪器设备资产` is maintained manually by An Zhaofeng; this skill may link to or read those cards when a project record needs context, but must not create, reorganize, or update hardware asset cards.

## Template-First Requirement

All project-record operations are template-driven. This includes creating, updating, reorganizing, or synchronizing total notes, mainline notes, debug/experiment records, issue or requirement entries, project-understanding/supplement notes, and indexes/Bases used by those records. Hardware asset cards are excluded as stated above.

Before touching a project record:

1. Identify the active Obsidian vault.
2. First search recursively under the default template root `E:\software\Obsidian\安钊锋的外置大脑\05-Junk Drawer\2_模板` for the template or command matching the requested role.
3. If the default root has no matching role, inspect the active Templater configuration and dynamically discover another configured template/command.
4. Invoke the discovered template through Obsidian/Templater, then fill or update the generated structure with facts recovered for this project. Preserve existing note content when the operation is an update. If the total-note template references project index views, creating those structural views is part of the total-note bootstrap; it does not authorize creating empty content notes.
5. If no matching template can be found, Templater cannot be invoked, or the requested role is ambiguous, stop and ask An Zhaofeng to identify the current template/command. Do not guess a location, copy a historical template, or manually recreate a template body.

The default root is only the first discovery location; the role-matching template found there is preferred. The skill must not embed a particular template body or treat a historical filename as the only canonical template.

## Preferred Folder Pattern

For a new or substantial existing project under `01-Project`, prefer the current FrogTrace-style single-digit structure:

```text
项目文件夹/
  0_总览/
    项目名总笔记.md
    项目名主线索引.<当前Base或Components格式>
    项目名未归类调试记录.<当前Base或Components格式>
  1_主线笔记/
    主题A.md
    主题B.md
  2_调试记录/
    实验记录/              # 仅在确有实验记录时创建
      YYYYMMDD_本次测试或工作.md
  3_项目理解/
  4_补充资料/
```

Adjust names to the project, but keep the logic simple: `0` is where to start and contains the total note plus useful indexes, `1` explains the main threads, `2` keeps chronological process records, `3` explains the project, and `4` holds supporting material. Do not create a project-local `3_硬件信息` folder.

The current reference implementation is `E:\software\Obsidian\安钊锋的外置大脑\01-Project\20260527_FrogTrace`: its `0_总览` contains the total note and project indexes, `1_主线笔记` contains the dated problem threads, `2_调试记录` contains chronological evidence, `3_项目理解` contains process/source explanations, and `4_补充资料` contains plans, evaluations, and archived material. New projects should follow this logic, adapting only the project name and the records actually supported by evidence.

## New Project Bootstrap

When An Zhaofeng asks to create a project in Obsidian, create the appropriately named project folder and the current numbered structure instead of starting with a loose note. The default required note is only the total note; do not create empty mainline, debug, experiment, or project-understanding notes without evidence or an explicit request.

Minimum useful bootstrap:

```text
项目文件夹/
  0_总览/
    项目名总笔记.md
    项目名主线索引.<当前Base或Components格式>
    项目名未归类调试记录.<当前Base或Components格式>
  1_主线笔记/
  2_调试记录/
  3_项目理解/
  4_补充资料/
```

At creation time:

1. Before searching for a template or writing, recover project facts from the current request, `azf-agent-memory`, existing Vault notes, the local repository, and—when available and relevant—AgentsView/local chat history. Treat chat history as evidence to reconcile, not as unquestioned truth.
2. Derive the project folder name from the user's explicit name/path first; otherwise use the existing `YYYYMMDD_项目名` convention and normalize it to the Vault's current naming style.
3. Invoke the discovered total-note template once and fill it with the recovered goal, known facts, current state, source/repository links, and immediate next step. Do not generate an empty or generic note.
4. Keep the total-note's project index views in `0_总览`, following the current project's Base/Components pattern and the active index template. These are structural views referenced by the total note, not content notes; an empty view is acceptable, but never create placeholder mainline or debug cards merely to populate it.
5. For a request that only says to create/bootstrap the project in Obsidian, generate no mainline, debug, experiment, or project-understanding content note beyond the total note. Existing logs, screenshots, or repository facts may be summarized or linked from the total note, but do not become separate records until An Zhaofeng explicitly asks to import,整理, or generate those records.
6. When An Zhaofeng explicitly requests record import/整理, create mainline notes only for real threads supported by the recovered facts, debug/experiment records only for actual evidence, and project-understanding notes only when evidence or the request supports them. If no such records are needed, leave the corresponding folders without placeholder notes; create `实验记录/` only when an experiment record is needed.
7. Do not create `.azf/project-notes.yaml` unless explicitly requested.
8. For deep-learning runs, keep logs, metrics, predictions, checkpoints, and canonical figures in the external artifact root; in the Vault use verified `file:///` links. Copy a lightweight image into the Vault only when An Zhaofeng explicitly asks for a local embedded copy or it is explanatory non-artifact material.

## Total Note

Name it like `项目名总笔记.md`. It should answer "where are we now?" before anything else.

Use numbered section headings in total notes. Because the filename already carries the document title, do not add a duplicate body title; start top-level content sections at `#`. Prefer Chinese numerals, for example `# 一、现在先看这里`, `# 二、当前主线` / `# 二、主线与当前状态`, `# 三、目前待解决的问题 / 需求`. Keep subsection headings short.

Preferred total-note dashboard flow for active projects:

1. `现在先看这里`: current status and immediate handoff.
2. `主线与当前状态`: the few active threads that explain the project state, preferably rendered by a lightweight Obsidian Bases view.
3. `目前待解决的问题`: unresolved issue index and issue detail cards.
4. `未归类调试记录 / 小 bug 收件箱`: list records that have not yet been attached to a mainline note using the current Base/Templater view.

Generate and update total notes only through the currently discovered Templater template for the total-note role. If An Zhaofeng manually adjusts the `当前阶段` callout formatting in that template or a project total note, preserve the layout and do not force it back into a paragraph or another schema.

Move longer navigation material out of the total note:

- Put beginner reading order in a separate `0_总览` note only when a real reading order has been recovered; otherwise do not create it.
- Put stable shortcuts and folder explanations in the beginner/navigation note or `4_补充资料` only when they contain real project information.
- Do not keep long `最近调试记录`, `新手阅读顺序`, `常用入口`, or `文件夹说明` sections in the total note once the project has a stable structure.

When reorganizing an existing total note, keep the section content intact, move only whole top-level sections, then renumber the Chinese numeral prefixes to match the final order.

Use this shape. Keep it dashboard-like: the total note is for "where are we now", not for full process history.

````markdown
---
创建时间: YYYY-MM-DDTHH:mm
修改时间: YYYY-MM-DDTHH:mm
项目名称: 项目名
笔记类型: 记录
笔记状态: 可用
项目笔记类型: 总笔记
当前状态: 一句话状态
aliases:
  - 旧总笔记名
---

# 一、现在先看这里

理解本项目参考：[[项目流程理解总图]]

> [!summary] 当前阶段
> 项目当前处在“……”阶段。

# 二、当前主线

![[项目名主线索引.<当前Base或Components格式>]]

<!-- 可选：如果项目需要解释主线分组、从属关系或当前判断，继续写在 base 下面；base 只做索引，不替代解释。 -->

# 三、目前待解决的问题 / 需求

| 事项 | 等级 | 问题名称 | 状态 |
|---|---|---|---|
<!-- AZF:ISSUE_TABLE_END -->

```button
name 新增问题/需求
type cursor template
action 新增项目问题或需求
color blue
```

等级可选：🚨 核心 / ⭐ 重要 / 🌱 后续

## 问题/需求理解

<!-- AZF:ISSUE_CALLOUTS_END -->

> [!note] Q 之间的关系（如果有多条 Q 属于同一族，在这里解释一次，主线里只链接不复述）

# 四、未归类调试记录 / 小 bug 收件箱

> [!note] 使用方式
> 新建小 bug 或临时调试记录时，先判断它能否接入已有主线。能接入时，直接写 `归类状态: 已归类`，并补上 `关联主线`；暂时没有合适主线时，才写 `归类状态: 未归类`，让它进入这里。每次整理结束时，需要向用户说明本次记录的归类判断。

![[项目名未归类调试记录.base]]
````

If a note is renamed, add aliases for old names instead of rewriting every old record.

Total-note rules:

- The mainline display title in the total note may be more direct than the filename. Do not rename the mainline file just to improve the dashboard title.
- A mainline derived from another mainline can be shown as an indented `### 1.1 ...` block, but it should remain an independent mainline note when it has its own reusable problem logic.
- In `主线与当前状态` / `当前主线`, put a lightweight `.base` view directly under the section heading as a compact index. The mainline base should show only `创建日期`, `主线` (from `file.name`, not a duplicated frontmatter property), and `当前状态`, sorted from old to new by `创建时间 ASC`.
- The mainline base is an index, not a replacement for An Zhaofeng's hand-written mainline explanation. If the total note already has grouped mainline descriptions, dependencies, or current judgments, keep them below the base instead of deleting them.
- Do not include `下一步` in the mainline base by default. The total note should stay clean; next actions belong in records or direct user planning unless the user explicitly asks for them.

When creating or updating a project mainline Base, invoke the currently discovered Base/Templater template for that role, place the generated view in the project's `0_总览/`, and replace only the project-specific filter value. If the active Vault has no matching template, ask An Zhaofeng before proceeding.

## Unresolved Issues Table

Every total note should maintain a `目前待解决的问题 / 需求` section near the top, usually after `主线与当前状态` and before `未归类调试记录 / 小 bug 收件箱`.

Use a compact index table to avoid cramped Markdown. Do not put long judgments, evidence, and next steps into the same table row. Prefer a `问题/需求理解` section below the table; it should explain the problem in plain words and link only to the mainline entrance. For old notes, `问题理解` is still accepted as a legacy heading.

````markdown
# 三、目前待解决的问题 / 需求

| 事项 | 等级 | 问题名称 | 状态 |
|---|---|---|---|
<!-- AZF:ISSUE_TABLE_END -->

```button
name 新增问题/需求
type cursor template
action 新增项目问题或需求
color blue
```

等级可选：🚨 核心 / ⭐ 重要 / 🌱 后续

## 问题/需求理解

<!-- AZF:ISSUE_CALLOUTS_END -->
````

Rules:

- In issue detail cards and status cards, prefer list syntax inside the callout: `> - **字段：** 内容`. This renders as a cleaner card with stable alignment, especially for `描述` and `主线入口`.
- Do not include an `入口` column in the issue index table. Put links and evidence in the issue detail card.
- Use clear item markers in the form `Q1`, `Q2`, `Q3` so unresolved issues are easy to cite in conversation and commits.
- Keep priority visually distinctive with icon labels instead of bare `P0` / `P1`.
- Preferred priority labels: `🚨 核心`, `⭐ 重要`, `🌱 后续`.
- `🚨 核心`: blocks the next experiment, debugging step, or core conclusion.
- `⭐ 重要`: important but can wait until the current core path is handled.
- `🌱 后续`: known limitation, cleanup, or future improvement.
- For the total-note issue table, status has only two values: `未创建主线` and `已有主线`. Default new entries to `未创建主线`.
- Keep detailed progress states such as "待排查", "待补充", "待设计", "进行中", or "已解决" out of this table; write them in the issue card, mainline note, or debug record instead.
- Link each issue primarily to the mainline note that carries the relationship. Do not put debug/work/experiment records from `2_调试记录/` in a Q issue card; attach those process records to the relevant mainline note instead.
- When new progress arrives, update this table first if it changes an active issue.
- If an issue needs more than one short phrase of explanation, put the detail in the `问题/需求理解` card, not in the table.
- Do not let old problems disappear without trace. If they no longer need to stay in the active table, archive the detail in the relevant mainline/debug note before removing the row.

Use the currently discovered Templater command/template for issue or requirement entries. It should show only three prompts: problem name, problem description, and priority level (choice list: `🚨 核心`, `⭐ 重要`, `🌱 后续`). It must automatically create the next `Q` id, append one row before `<!-- AZF:ISSUE_TABLE_END -->`, append a matching callout under `问题/需求理解` (or legacy `问题理解`) before `<!-- AZF:ISSUE_CALLOUTS_END -->` when the anchor exists, and default the table status to `未创建主线`.

When the Buttons plugin is available, put a button directly under the issue table and before the priority reference line, and configure it to call the currently discovered issue/requirement Templater command. Do not hard-code a historical action name in the skill. Use the plugin's normal cursor-template invocation; do not pre-process the button with `templater true` unless the current template explicitly requires it. The command should modify the active total note itself and return empty output, so the button should not visibly insert template text into the note.

When a Q later gains a real mainline, update its issue callout `主线入口` to the mainline link and change the table status to `已有主线`. The Templater command may sync existing table statuses by reading whether each callout has a non-placeholder wiki link in `主线入口`.

## Small Bug Inbox And Mainline Attachment

Small bugs should not each become their own mainline note by default, but every bug/debug record must be findable from a common entrance.

### Explicit Standalone Record Override

Treat "independent note/file" and "unclassified record" as different concepts. A record can be a standalone Markdown note and still be classified if a mainline already carries or references it.

Only default a new record to `归类状态: 未归类` when An Zhaofeng explicitly says "独立记录", "独立调试记录", "单独记录", "不要归类", or gives an equally direct instruction that the record must not be attached to a mainline.

Otherwise keep the normal mainline-attachment rule:

1. If a relevant mainline exists and this record is already referenced there, set `归类状态: 已归类` and fill `关联主线`.
2. If the current note-sync task includes adding the record reference to a relevant mainline, set `归类状态: 已归类` and fill `关联主线`.
3. If no suitable mainline exists and the user did not ask to create one, set `归类状态: 未归类`.
4. In the user-facing closeout, report whether the record was kept unclassified by explicit request or classified because it is connected to a mainline.

## Q Issue Card And Mainline Sync

The total note's `Q1` / `Q2` / `Q3` issue cards are status entrances, not the final place for process history. When a new record, code change, verification result, GUI finding, or design decision changes an active Q issue and also belongs to an existing mainline, update both layers in the same sync pass.

Important permission boundary:

- This synchronization rule applies only when An Zhaofeng explicitly asks to update/sync/write/organize Obsidian notes or confirms a proposed note-sync pass.
- During ordinary code modification, debugging, Git work, hardware troubleshooting, or log reading, the Obsidian vault is read-only by default. Read notes for context if useful, but do not update total notes, mainline notes, debug records, or the separately maintained instrument-asset cards.
- If code/debug progress should be recorded but An Zhaofeng did not ask for note updates, leave the note vault untouched and report that note synchronization is pending.

Use this rule especially when the user asks to update a work record, debug record, or project status:

1. Update the total note's Q issue table/card only as the dashboard entry: short problem understanding, mainline entrance, and status. Link only mainline notes by default; never link concrete debug/work/experiment records from `2_调试记录/`.
2. Create or update the concrete debug/work record under `2_调试记录/`, including frontmatter `归类状态: 已归类` and `关联主线`.
3. Append the record to the relevant mainline note's `推进记录`, then rewrite the relevant progress entry in plain language if the new record changes the thread.
4. If the progress is a prerequisite for another mainline, add a short cross-link in `相关入口` or the relevant progress entry; do not rely on the Q card alone to carry that relationship. Keep concrete debug-record links in mainline `推进记录`, not in the Q card.
5. End the user-facing response by reporting the sync coverage, for example: `已更新总笔记 Q3、调试记录、[[根据中心波长自动选择光谱仪]] 主线` or `只更新了 Q3，主线未改，因为...`.

Avoid the common mistake: updating only `FrogTrace项目总笔记.md` 的 Q 入口 while leaving the corresponding `1_主线笔记/` page stale. For example, a change such as "analysis wavelength range is automatically derived from spectrometer wavelengths and pixel window" may appear in Q3, but if it is a prerequisite for "根据中心波长自动选择光谱仪", it must also be appended to that mainline as process context.

Default rule:

1. Create the concrete bug/debug process record under `2_调试记录/`.
2. Before setting classification, inspect existing mainline notes in `1_主线笔记/` and decide whether the new record belongs to one of them.
3. If the record belongs to an existing mainline, add frontmatter like this:

```yaml
项目名称: 项目名
笔记类型: 记录
笔记状态: 已验证 / 待复测 / 待补证据
项目笔记类型: 调试记录
归类状态: 已归类
关联主线:
  - 主线名称
```

Then update the relevant mainline note's `推进记录` section with a link to the record.

4. If no existing mainline is a good fit, add frontmatter like this:

```yaml
项目名称: 项目名
笔记类型: 记录
笔记状态: 已验证 / 待复测 / 待补证据
项目笔记类型: 调试记录
归类状态: 未归类
关联主线:
```

Also add a short `## 归类判断` section near the top of the record explaining why it is currently unclassified and what future mainline might absorb it.

5. Show only unclassified records from the total note's `未归类调试记录 / 小 bug 收件箱`.
6. At the end of the user-facing response, always report the classification decision: either `已归类到 [[主线名]]` or `暂未归类，原因是...`.

Use a new mainline note only when the bug reveals a reusable project thread, such as hardware state management, wavelength mapping, acquisition flow, reconstruction output, dependency/environment setup, or another theme that will likely connect multiple records. Otherwise attach it to an existing mainline or a broad `问题与修复总线` if no better mainline exists yet.

When Obsidian Bases is available, invoke the currently discovered Base/Templater template for the inbox and embed the generated view in the total note. The view can filter by `项目名称 == "项目名"` and `归类状态 == "未归类"`. Because every row is already unclassified, do not show a `归类状态` column in the view. Because unclassified rows usually have no mainline yet, do not show an `关联主线` column unless the user explicitly wants it. Prefer compact columns such as `记录`, `项目笔记类型`, `笔记状态`, and `修改时间`. If no matching Base template is available, ask the user; do not fall back to a hand-written Base body.

## Mainline Notes

Use mainline notes when raw records are too isolated to show relationships. A mainline note should summarize one thread, not duplicate every detail. An Zhaofeng prefers a concise linear mainline: use date-based progress entries instead of Step diary structure.

When creating or updating a mainline note, invoke the currently discovered Templater template for the mainline role. Do not write the body from a copied example in this skill. If the active Vault has no matching template or the operation is happening outside Obsidian without a callable Templater bridge, ask An Zhaofeng before proceeding; never recreate a guessed template.

Good mainline topics include "光谱仪连接与采集", "波长映射与频率插值", "FROG迹图反演与结果保存", or the equivalent threads for another project.

Mainline-writing rules:

- Start mainline filenames with `【主线】` unless the user says otherwise. Do not force rename older files without asking.
- Mainline frontmatter should include `当前状态: 一句话状态` for the total note's mainline base. Do not add a separate `主线` frontmatter property; the base's `主线` column should read the note name via `file.name`. Keep `笔记状态` only as a coarse compatibility field when it already exists.
- Mainlines should sound like a clear handoff for a future beginner: "具体来说就是..." is better than formal abstract wording.
- Use `# 推进记录` with date headings such as `## YYYY-MM-DD：一句话结论`; do not use `Step 1/2/3` as the mainline structure.
- Each progress entry should bind the progress, the plan used for this progress, and the debug record for this progress. If every debug run has a different plan, put `本次方案` under the matching progress entry instead of collecting all方案 links at the bottom.
- Keep `# 相关入口` for stable cross-progress context only: total note, neighboring mainlines, manually maintained instrument-asset links, project-understanding notes, and long-lived references. Do not dump every per-run方案 there.
- Do not include code status in mainline notes. Branch, commit, working tree, gitGraph, commands, logs, and verification output belong in the matching debug record Step.
- Use three progress sizes: (1) one or two sentences with no evidence -> write a progress entry and mark `调试记录: 无单独记录`; (2) one paragraph plus explanatory screenshot -> write a progress entry plus a folded callout; (3) evidence screenshot, real-device result, CSV/log/command output, detours, or a point that needs future audit -> create a debug record and link it.
- For folded mainline callouts, use them only for explanatory screenshots or light context. If the screenshot is evidence of real-device behavior, an error, an experiment result, or a conclusion that may be challenged later, create a debug record instead.
- For explanatory folded callouts in mainline notes, preserve An Zhaofeng's original reasoning chain instead of flattening it into an agent summary. Preferred shape: title the callout as the question/reason, e.g. `> [!note]- 为什么要校准 Zolix 波长轴`; start with the date/context; place screenshots immediately after the claim they support; use short bullet groups such as `当时的操作是：` and `原因和代码依据见：`; keep background links under those bullets; end with the decision or consequence. Do not turn this kind of callout into a table unless it is truly comparing multiple items, and do not delete screenshots that explain why a later decision happened.
- After each debugging or implementation progress entry, write what it taught the mainline, not only that the work happened.
- Keep `当前理解`, `当前卡点`, and detailed `下一步` out of mainline notes by default; fold useful parts into `当前状态` or the specific progress entry.
- Use highlighted `<mark style="background:#fff88f">...</mark>` sparingly for the one judgment a future reader must not miss.
- A mainline derived from another mainline can remain independent. Show the hierarchy in the total note; keep the mainline note itself focused on its own problem.

## Debug Records

Use `2_调试记录` for things that happened while working: code debugging, hardware tests, bug reviews, log reading, real-device validation, Git-backed changes, and progress handoff.

There is only one debug-record body format for FrogTrace-style records: the current Templater timeline template. Do not create separate debug-record templates such as `实机验证记录`, `代码修改记录`, test-sheet records, or standalone Git-card records. If a note is a debug/process record, invoke the currently discovered Templater template for that role and use the same timeline structure regardless of whether the work is code-only, hardware-only, real-device validation, or mixed code + hardware. If no matching template can be found, ask An Zhaofeng; do not write a guessed minimal body.

- Existing experiment-record Markdown files should be moved under `2_调试记录/实验记录/` when the user wants a simpler structure.
- Do not rewrite old experiment records unless the user asks. If a later conclusion changes the interpretation, add a new note or a `后续更正` section only when appropriate.
- Keep chronological evidence in records; keep relationship summaries in mainline notes.
- If a note is named, linked, or used as a debug record and it contains code changes, branch work, verification commands, SDK probing, calibration-file adoption, or future audit evidence, treat it as a real debug record: place it under `2_调试记录/` and set frontmatter `项目笔记类型: 调试记录`. Do not leave it under `4_补充资料/` with `项目笔记类型: 补充资料` merely because it began as supporting material.
- When cleaning a mainline entry that links to a debug record, inspect the linked debug record before finishing. If the work involved Git, confirm that branch/commit/worktree/verification information exists in the chronological Step where the code or branch change happened. The mainline may omit Git details, but the debug record must not.
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

Use the body generated by the currently discovered Templater template for the exact structure. The conceptual shape is:

```text
frontmatter
# 一、调试目标
# 二、调试过程
## Step 1：...
  操作 / 现象 / 证据入口 / 判断
  Git 信息（only when this Step involves code, branch, commit, push, rollback, or verification tied to a code version）
## Step 2：...
## Step 3：...
# 三、调试结论
# 四、同步判断
```

Keep Git cards and Git visualization inside the Step where the code change, branch change, commit, push, rollback, or code-version verification happened. This is intentional: it makes the note easier for agents and An Zhaofeng to resume from the exact chronological point where Git mattered.

Timeline debug process rules:

- Keep the main structure fixed as `调试目标` -> `调试过程` -> `调试结论`.
- Write `Step 1`, `Step 2`, `Step 3` in real chronological order. Each Step should explain what was done, what was seen, and what judgment changed.
- The small fields inside each Step are flexible. Use only what the step needs: `操作`, `现象`, `证据入口`, `涉及文件`, `处理`, `验证`, `判断`, `Git 信息`, or `Git 可视化`.
- Tables are allowed inside Steps when they compare devices, expected/actual behavior, pass/fail items, files, commands, or result paths. Do not turn the whole record into a test sheet.
- Do not manually expand code diffs. For code-related steps, write the intent, affected files, verification result, Git commit/branch/card, and evidence paths. Codex can recover exact code changes from Git later.
- Put Git cards and Mermaid `gitGraph` inside the Step where the code change, branch change, commit, push, or rollback happened. Do not create a separate top-level Git chapter.
- Make Git visualization complete enough to reconstruct the branch story. For a simple linear branch, include the relevant current-branch commits from the branch/start point through the current HEAD, not only a three-node sketch. If there are important side branches in the visible history, either include them in Mermaid or add the raw `git log --graph` excerpt under the Mermaid.
- Use highlighted `<mark style="background:#fff88f">...</mark>` sparingly for the one judgment future An Zhaofeng must not miss.
- Planned on-site checklists are still allowed, but if they live under `2_调试记录`, write them in the same timeline format with `笔记状态: 待复测` and future-tense Steps. Do not introduce a separate top-level template.

## Reference And Supplement Notes

Use project-understanding and supplement notes for facts that should not be rediscovered:

- Environment/dependencies: conda environments, packages, DLLs, vendor software, data paths, and setup constraints.
- Project understanding: what the project does, source modules, data flow, risks, and diagrams.
- SOP/material notes: repeated operation steps, GUI guides, old plans, code-reading introductions, and result evaluations.

Hardware asset facts are maintained in `E:\software\Obsidian\安钊锋的外置大脑\03-Academic Toolkit\2_资源与档案\仪器设备资产` outside the project structure. For a hardware status image or test, record the event in `2_调试记录/`; do not create or update a project-local hardware card.

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
| Hardware status | equipment, labels, cables, ports | project debug record; link to the manually maintained instrument asset when useful |
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
4. Confirm debug records are in `2_调试记录` and project-understanding notes are in `3_项目理解`.
5. Confirm old links are covered by aliases or updated paths.
6. Confirm attachment embeds still resolve.
7. Do not audit or mutate the separate instrument-asset folder as part of this project-record closeout.
8. Tell An Zhaofeng what changed and where the backup is.
