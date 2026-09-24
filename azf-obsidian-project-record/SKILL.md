---
name: azf-obsidian-project-record
description: An Zhaofeng's Obsidian project-record system and the authoritative rule layer for AI-assisted project refresh. Use when Codex needs to create a new Obsidian project record from scratch, reorganize an existing project, or maintain notes under 01-Project (total notes, mainline notes, debugging/experiment records, project-understanding notes, project indexes), and also when refreshing a project's current-stage briefing, running a pre-work reuse check, or writing back classification and status fields. Trigger on requests such as "帮我记录这个项目", "新开一个项目", "整理项目笔记", "建立总笔记", "同步调试记录", "根据图片更新实验记录", "刷新当前项目", "刷新当前阶段", "复用检查", "这个是不是做过了", "新项目也按这个方式记录".
---

# AZF Obsidian Project Record

Use this skill to make An Zhaofeng's Obsidian project notes easy to resume and easy for a beginner to understand. The goal is not a formal archive; the goal is a compact work-record system where the relationship between records stays visible, and where the AI can refresh project state without inventing facts.

## 1. Authority And Scope

This `SKILL.md` is the authoritative rule layer for **how** project records are structured, classified, refreshed, and written back.

- **Property names and allowed values are not defined here.** The single authority for fields, value sets, scope, exemptions and protection is `00-Command Center/笔记库规范/1_全库规范/笔记属性规范.md`. Read it before writing any frontmatter field; if an example below ever drifts from it, that document wins.
- Only two facts this skill's flow depends on, restated so the flow stays readable: `项目笔记类型` is exactly one of `项目总览` / `主线笔记` / `调试记录` / `补充资料`, and `归类状态` only ever carries `未归类` (absence already means classified).
- The Command Center document `00-Command Center/笔记库规范/2_项目规范/项目笔记AI协作需求（草案）.md` is navigation, mechanism index, and acceptance scenarios only. It does not carry rules. If it ever conflicts with this skill, this skill wins — except on property names and values, where the 笔记属性规范 wins.
- The Obsidian plugin `azf-issues-db` is the executor: it assembles context, owns the managed callout anchor, appends the weekly stage record, and writes whitelisted frontmatter fields. Do not hand-edit the plugin's managed regions to work around it.
- Hardware asset cards are outside this skill. The folder `E:\software\Obsidian\安钊锋的外置大脑\03-Academic Toolkit\2_资源与档案\仪器设备资产` is maintained manually by An Zhaofeng; this skill may link to or read those cards for context, but must not create, reorganize, or update them.
- Out of scope: vault-wide knowledge notes, global templates, and any note outside a project that is not part of a project record.

## 2. Write Permission Gate

The vault is read-only by default. Only these triggers authorize writing notes:

1. An Zhaofeng explicitly asks to record, sync, 整理, refresh, or update Obsidian notes.
2. He confirms a proposed note-sync pass.
3. He runs the refresh action himself (the plugin command `azf-stage-refresh` or the 「当前阶段」 button) or explicitly asks for it in the current turn.

During ordinary code modification, debugging, Git work, hardware troubleshooting, or log reading, the Obsidian vault is read-only. Read notes for context if useful, but do not update total notes, mainline notes, debug records, or instrument-asset cards. If code or debug progress should be recorded but he did not ask for note updates, leave the vault untouched and report that note synchronization is pending.

Never write passwords, API keys, tokens, cookies, private keys, or recovery codes into notes.

## 3. Three Layers And View-vs-Evidence

Maintain five project-note roles:

1. Total note: project entrance, current status, reading order, and navigation.
2. Mainline notes: connect related records into a few clear threads. Mainlines are **not** split into classes any more: the total note shows one mainline list, and importance is read from `推进状态` (lifecycle).
3. Debug records: chronological process records, handoff notes, bug notes, and experiment records.
4. Project-understanding notes: code maps, process explanations, source reading, and diagrams.
5. Supplement notes: GUI guides, plans, environment/dependency explanations, old schemes, temporary investigations, and archived material.

Keep the total note light. Put details into linked records, then use mainline notes to explain how those records relate. For ongoing projects, treat the total note as a dashboard, not as the place where every recent record, shortcut, and folder explanation lives.

Separate the two kinds of content explicitly:

- **Views (rebuildable):** the AI briefing callout, stage summaries, and any progress digest. These may be rewritten on every refresh.
- **Evidence (durable):** debug-record bodies, mainline progress entries, original data links, and An Zhaofeng's own decisions. These are append-only; earlier text is not rewritten when a conclusion changes.

Every judgment in a view must be traceable to a record. When a later conclusion changes, record the change as new evidence and leave the earlier record as it was.

## 4. Pre-Write Reuse Check

The reuse check exists so that repeated work is caught **before** it is executed, not after. It outranks the question of whether two notes should be merged.

Read, at minimum: the total note, every mainline note, the recent debug records for the configured window, and the issue database region.

Compare for each candidate piece of work: the goal, the object or sample, the conditions and batch, the scope covered, and the deliverable produced.

Report exactly three things, each naming its source note:

1. What is already done or partially covered.
2. What actually differs (condition, object, batch, range, or purpose).
3. What can be reused as-is, and what still has to be produced.

Example shape:

> 拟开展的测试与记录 T017 部分重合。已有结果覆盖低湿条件，尚缺高湿条件；建议只补充高湿测试，两条主线共用本次结果。依据：[[T017 记录]]。

Rules:

- Never claim "做过" or "重复" without naming the record and the difference. If no source can be named, say the check is inconclusive instead.
- The check is bounded by what is recorded. Work done offline and never recorded cannot be detected; say so when the evidence is thin rather than guessing.
- Unanswered suggestions must not pile up: the same unresolved suggestion appears once, and disappears once he answers or acts.
- A reuse finding does not authorize merging notes or moving files. Structure changes are proposed, never applied silently.

## 5. Classification And Sync

The total note's `Q1` / `Q2` / `Q3` issue cards are status entrances, not the final place for process history.

Default rule:

1. Create the concrete bug/debug process record under `2_调试记录/`.
2. Before setting classification, inspect existing mainline notes in `1_主线笔记/` and decide whether the new record belongs to one of them.
3. If the record belongs to an existing mainline, fill `关联主线` and append the record link to that mainline's `推进记录`. Do **not** write `归类状态: 已归类` — absence of the field already means classified; the field only ever carries `未归类`.
4. If no existing mainline fits and he did not ask to create one, write `归类状态: 未归类` (the only explicit value that field carries) and add a short `## 归类判断` section near the top explaining why it is unclassified and which future mainline might absorb it.
5. Show unclassified records only through the total note's `未归类调试记录 / 小 bug 收件箱` view.
6. In the user-facing closeout, always report the classification decision: `已归类到 [[主线名]]` or `暂未归类，原因是…`.

Explicit standalone override: treat "独立记录", "独立调试记录", "单独记录", "不要归类", or an equally direct instruction as a request to keep a record unclassified even when a mainline exists. Treat "independent note/file" and "unclassified record" as different concepts: a record can be a standalone note and still be classified.

When a new record, code change, verification result, GUI finding, or design decision changes an active Q issue and also belongs to an existing mainline, update both layers in the same pass:

1. Update the total note's Q issue table/card only as the dashboard entry: short problem understanding, mainline entrance, and status.
2. Create or update the concrete record under `2_调试记录/` with `归类状态` and `关联主线`.
3. Append the record to the relevant mainline's `推进记录`, and rewrite the progress entry in plain language if the new record changes the thread.
4. If the progress is a prerequisite for another mainline, add a short cross-link in `相关入口` or in the relevant progress entry. Do not rely on the Q card to carry that relationship.
5. End the response by reporting the sync coverage, for example `已更新总笔记 Q3、调试记录、[[根据中心波长自动选择光谱仪]] 主线` or `只更新了 Q3，主线未改，因为…`.

Avoid the common mistake of updating only the total note's Q entrance while leaving the corresponding `1_主线笔记/` page stale.

When Obsidian Bases is available, invoke the currently discovered Base/Templater template for the inbox and embed the generated view in the total note. The view can filter by `项目名称 == "项目名"` and `归类状态 == "未归类"`. Because every row is already unclassified, do not show a `归类状态` column, and do not show `关联主线` unless he explicitly wants it. Prefer compact columns such as `记录`, `项目笔记类型`, `笔记状态`, and `修改时间`. If no matching Base template is available, ask; do not fall back to a hand-written Base body.

Use a new mainline note only when the work reveals a reusable project thread, such as hardware state management, wavelength mapping, acquisition flow, reconstruction output, or dependency/environment setup. Otherwise attach it to an existing mainline, or to a broad `问题与修复总线` if no better mainline exists yet.

## 6. Refresh Action

The refresh action is how project state is rebuilt. It is one action, not a chain of separate ones.

Trigger: An Zhaofeng asks to refresh, or runs `azf-stage-refresh` / 「当前阶段」. Do not run it on your own initiative.

A saved prompt is never overwritten by changing defaults: the plugin upgrades the stored prompt only when the field is empty or still equals a historical default, and the settings tab exposes a 「恢复默认提示词」 button for a deliberate reset. Never edit the plugin's `data.json` to change a prompt while Obsidian is running.

Input context, in the plugin's keep order (earlier survives budget cuts): issue database managed region → recent debug-record bodies → mainline bodies. The window is the configured `weeks` (default 4). The total budget is `contextBudget` (default 80000 characters). Record bodies contribute `调试目标` and `调试结论` only; Step process text stays out. When a section is cut, the briefing must say so rather than silently losing it.

Writes, and nothing else:

1. **The stage callout**, between `%%azf-stage:begin%%` and `%%azf-stage:end%%` in the project total note. Replace in place only. Write it **collapsed** — `> [!azf-stage]- 当前阶段：<one-line status>（更新于 YYYY-MM-DD HH:mm）` — so the folded card still shows where the project stands; the title line is regenerated on every refresh. When the markers are absent, the plugin inserts the block after the first `# ` heading; in a real project, place the markers by hand inside `# 一、现在先看这里` so the position is intentional.
2. **one file per ISO week: `0_总览/当前阶段记录/<项目名>当前阶段记录 <周键>.md`** (e.g. `FrogTrace当前阶段记录 2026-W38.md`), appending one entry per run: the file's `# 2026-W38（09-14 ~ 09-20）` heading is the week itself, frontmatter carries `项目名称` and `覆盖周`, and the newest entry sits directly under that heading, and containing the full model output including the `%%azf-writes%%` audit block. A legacy `0_总览/当前阶段记录.md` is migrated into that subfolder once.
3. **Whitelisted frontmatter fields only.** `记录` targets may receive `关联主线`, plus `归类状态` only when the value is `未归类` (a classified record carries no such field); `主线` targets may receive `推进状态` and `当前状态`. Note bodies are never rewritten by this action.

**The stage anchor decides which note is updated** — never "the first match in the folder":

1. the note An Zhaofeng is viewing, when it carries the anchor or declares `项目笔记类型: 项目总览`; if that note has no anchor yet, ask before inserting one;
2. the only note named `<项目名>项目总笔记`;
3. the only candidate that already carries the anchor;
4. the single remaining candidate;
5. otherwise stop, list the candidates, and mark which of them carry the anchor.

A note under `0_总览` that neither carries the anchor nor declares `项目笔记类型: 项目总览` is refused with a message instead of being written to. Only the region between `%%azf-stage:begin%%` and `%%azf-stage:end%%` is ever replaced, so the note that owns the anchor owns the briefing. Place the anchor in the total note (the total-note template already contains it); when a target note has none, the plugin asks before inserting it and inserts nothing until confirmed.

The briefing must contain, in order: `当前阶段：`, 3-5 进展 items naming their mainline, 2-3 阻塞/风险/待验证 items, a `**复用检查**` section, and a `**需要你决定**` section. Facts that are missing must be stated as missing; never fill in sample batches, conditions, or units by inference.

Idempotence:

- Callout replacement is naturally idempotent; a repeated refresh must not stack blocks or duplicate links.
- Unanswered `**需要你决定**` items are merged: existing unanswered items are kept once, new ones are appended, duplicates drop out, and the list is capped at 8 with the oldest evicted.
- An evicted decision is never dropped silently: it stays in the weekly record, and the callout ends with a plain line such as `另有 N 条较早的待决定，见本项目「当前阶段记录」笔记`. That notice carries no `-` marker, so it is not counted as a decision item.
- The weekly record intentionally keeps one entry per run; that is an audit trail, not duplication.

Conflict handling: before writing a field, compare the file against the snapshot taken while building the context. If the file changed in the meantime, skip that file and report it. For the callout, compare the current region body (title line and the `**需要你决定**` section excluded) with the newest entry in the weekly record: when they differ, ask `覆盖 / 保留当前内容`. Choose-keep leaves the callout byte-identical and still appends the weekly record and applies field writes. Never overwrite a human edit silently — a manual reformat, a hand-written note inside the card, or a changed heading must survive or be acknowledged.

After the refresh, report in three parts: what was updated, what the reuse check found, and what needs his decision. Include how many notes received field writes, how many were skipped due to conflict, and how many targets were not found.

## 7. Fact, Judgment, And Decision Separation

Keep three kinds of statement visibly different in every note and every report:

- **His decision** — what An Zhaofeng decided to do.
- **Measured result** — what the instrument, the log, or the test actually produced.
- **AI inference** — what the agent concluded, and from which evidence.

And keep three states different: a **suggestion** is not a **decision**, and a decision is not a **completion**. Do not record a proposal as if it were decided, and do not record a decision as if the work were finished.

## 8. Acceptance Checklist

A refresh pass is only acceptable when all of these hold:

1. Only the managed callout region changed; text outside the markers is byte-identical.
2. A repeated refresh produces no duplicated callout, links, or suggestions.
3. If the callout was edited by hand, the refresh asks `覆盖 / 保留当前内容` instead of overwriting it; choose-keep leaves the callout byte-identical while the weekly record is still appended.
4. Missing sample batch, condition, or unit information is asked for, never invented.
5. A record attached to a mainline gets `关联主线` and no `归类状态` field; an unattached one gets `归类状态: 未归类` with a stated reason.
6. The reuse check names its source records and states the difference.
7. An earlier record is never rewritten when a conclusion changes.
8. A truncated context is declared in the briefing.
9. A failed backend call leaves every file untouched and reports an error.
10. No placeholder note is created, no mainline is merged, and no file is moved by this action.
11. The callout is written collapsed, and its title carries the one-line current stage.
12. Issue `Q` numbers never change: deleting one leaves a gap, and the next new item takes max+1.
13. An issue is only marked `已完成` when a real-device or acceptance result backs it; code that is finished but not yet verified is `待验证`.

## 9. Template-First Requirement

All project-record operations are template-driven. This includes creating, updating, reorganizing, or synchronizing total notes, mainline notes, debug/experiment records, issue or requirement entries, project-understanding/supplement notes, and the indexes/Bases those records use. Hardware asset cards are excluded.

Before touching a project record:

1. Identify the active Obsidian vault.
2. First search recursively under the default template root `E:\software\Obsidian\安钊锋的外置大脑\05-Junk Drawer\2_模板` for the template or command matching the requested role.
3. If the default root has no matching role, inspect the active Templater configuration and dynamically discover another configured template/command.
4. Invoke the discovered template through Obsidian/Templater, then fill or update the generated structure with facts recovered for this project. Preserve existing note content when the operation is an update. If the total-note template references project index views, creating those structural views is part of the total-note bootstrap; it does not authorize creating empty content notes.
5. If no matching template can be found, Templater cannot be invoked, or the requested role is ambiguous, stop and ask An Zhaofeng to identify the current template/command. Do not guess a location, copy a historical template, or manually recreate a template body.

The default root is only the first discovery location. The skill must not embed a particular template body or treat a historical filename as the only canonical template.

## 10. Preferred Folder Pattern

For a new or substantial existing project under `01-Project`, prefer the current FrogTrace-style single-digit structure:

```text
项目文件夹/
  0_总览/
    项目名总笔记.md
    项目名主线笔记索引.components
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

Keep the logic simple: `0` is where to start and holds the total note plus useful indexes, `1` explains the main threads, `2` keeps chronological process records, `3` explains the project, and `4` holds supporting material. Do not create a project-local `3_硬件信息` folder.

The current reference implementation is `E:\software\Obsidian\安钊锋的外置大脑\01-Project\20260527_FrogTrace`. New projects follow this logic, adapting only the project name and the records actually supported by evidence.

## 11. New Project Bootstrap

When An Zhaofeng asks to create a project in Obsidian, create the appropriately named project folder and the current numbered structure instead of starting with a loose note. The default required note is only the total note; do not create empty mainline, debug, experiment, or project-understanding notes without evidence or an explicit request.

```text
项目文件夹/
  0_总览/
    项目名总笔记.md
    项目名主线笔记索引.components
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
4. Keep the total note's project index views in `0_总览`. Create `项目名主线笔记索引.components` from its active Components template, replacing only the project-folder path in its filter (folder filter only — no tag filter), and keep the unclassified-debug index in its active Base/Components format. These are structural views, not content notes; an empty view is acceptable, but never create placeholder mainline or debug cards to populate it.
5. For a request that only says to create/bootstrap the project in Obsidian, generate no mainline, debug, experiment, or project-understanding content note beyond the total note. Existing logs, screenshots, or repository facts may be summarized or linked from the total note, but do not become separate records until An Zhaofeng explicitly asks to import or 整理 them.
6. When he explicitly requests record import/整理, create mainline notes only for real threads supported by the recovered facts, debug/experiment records only for actual evidence, and project-understanding notes only when evidence or the request supports them. Leave folders without placeholder notes; create `实验记录/` only when an experiment record is needed.
7. Do not create `.azf/project-notes.yaml` unless explicitly requested.
8. For deep-learning runs, keep logs, metrics, predictions, checkpoints, and canonical figures in the external artifact root; in the Vault use verified `file:///` links. Copy a lightweight image into the Vault only when he explicitly asks for a local embedded copy or it is explanatory non-artifact material.

## 12. Total Note

Name it like `项目名总笔记.md`. It should answer "where are we now?" before anything else.

Use numbered section headings. Because the filename already carries the document title, do not add a duplicate body title; start top-level content sections at `#`. Prefer Chinese numerals, for example `# 一、现在先看这里`, `# 二、当前主线`, `# 三、目前待解决的问题 / 需求`.

Preferred dashboard flow for active projects:

1. `现在先看这里`: current status and immediate handoff.
2. `当前主线`: show one lightweight Components view (`项目名主线笔记索引.components`) listing every mainline; do not split it into classes.
3. `目前待解决的问题`: unresolved issue index and issue detail cards.
4. `未归类调试记录 / 小 bug 收件箱`: list records not yet attached to a mainline, using the current Base/Templater view.

The issue database (`azf-issues`) is rendered by the plugin, not by hand. Its status values are `待处理` / `处理中` / `阻塞` / `待验证` / `已完成`, and they mean what they say: `待验证` covers "code or plan is finished, but no real-device or acceptance evidence yet", `已完成` requires that evidence. The table shows 编号 / 事项 / 类型 / 状态 / 主线入口 / 操作 — there is no 描述 column; clicking a row expands the full description underneath, and clicking that description starts inline editing. Do not add a description column back.

Generate and update total notes only through the currently discovered Templater template for the total-note role. If An Zhaofeng manually adjusts the `当前阶段` callout formatting in a total note, preserve the layout and do not force it back into another schema.

Move longer navigation material out of the total note:

- Put beginner reading order in a separate `0_总览` note only when a real reading order has been recovered.
- Put stable shortcuts and folder explanations in the beginner/navigation note or `4_补充资料`, and only when they contain real project information.
- Do not keep long `最近调试记录`, `新手阅读顺序`, `常用入口`, or `文件夹说明` sections in the total note once the project has a stable structure.

When reorganizing an existing total note, keep section content intact, move only whole top-level sections, then renumber the Chinese numeral prefixes to match the final order.

Reference shape:

````markdown
---
创建时间: YYYY-MM-DDTHH:mm
修改时间: YYYY-MM-DDTHH:mm
项目名称: 项目名
笔记类型: 记录
笔记状态: 可用
项目笔记类型: 项目总览
当前状态: 一句话状态
aliases:
  - 旧总笔记名
---

# 一、现在先看这里

理解本项目参考：[[项目流程理解总图]]

%%azf-stage:begin%%
> [!azf-stage]- 当前阶段（尚未生成）
> 执行「AI：刷新当前阶段」后，这一段会被自动替换。
%%azf-stage:end%%

# 二、当前主线

## 主线笔记

![[项目名主线笔记索引.components]]

<!-- 可选：主线分组、从属关系或当前判断继续写在两个 Components 视图下面；组件视图只做索引，不替代解释。 -->

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

# 四、未归类调试记录 / 小 bug 收件箱

> [!note] 使用方式
> 新建小 bug 或临时调试记录时，先判断它能否接入已有主线。能接入时只要补 `关联主线`（不要再写 `归类状态`，缺省就表示已归类）；暂时没有合适主线时才写 `归类状态: 未归类`，让它进入这里。每次整理结束时，需要向用户说明本次记录的归类判断。

![[项目名未归类调试记录.base]]
````

Total-note rules:

- If a note is renamed, add aliases for old names instead of rewriting every old record.
- The mainline display title in the total note may be more direct than the filename. Do not rename the mainline file just to improve the dashboard title.
- A mainline derived from another mainline can be shown as an indented `### 1.1 ...` block, but it should remain an independent mainline note when it has its own reusable problem logic.
- In `当前主线`, keep exactly one Components view under the `主线笔记` heading. It shows only `文件名`, `创建时间`, and `当前状态`, sorted oldest-first by `创建时间 ASC`.
- These views are indexes, not replacements for hand-written mainline explanation. If the total note already has grouped descriptions, dependencies, or current judgments, keep them below the views.
- Do not add a `下一步` frontmatter field to mainlines: next actions belong in the mainline's `当前状态`, its progress entries, or direct planning. It is not a writable field for the refresh action either.

When creating the mainline Components view, use the currently discovered `项目主线笔记索引Components模板.components`, place the copy in the project's `0_总览/`, name it `项目名主线笔记索引.components`, and replace the placeholder folder with the exact Vault-relative path `01-Project/<项目文件夹>/1_主线笔记`. Keep exactly one filter condition: `${file.parent}` equals that path. Do not add filters for file extension, `项目笔记类型`, project name, filename prefix, status, or tags — mainlines are no longer classified, so the view lists every note in the folder. If the active Vault has no matching template, ask before proceeding.

## 13. Unresolved Issues Table

Every total note maintains a `目前待解决的问题 / 需求` section near the top, usually after `主线与当前状态` and before `未归类调试记录 / 小 bug 收件箱`. Use a compact index table; do not put long judgments, evidence, and next steps into the same row.

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

- In issue detail cards and status cards, prefer list syntax inside the callout: `> - **字段：** 内容`. It renders as a cleaner card with stable alignment.
- Do not include an `入口` column in the issue index table. Put links and evidence in the issue detail card.
- Use `Q1`, `Q2`, `Q3` item markers so unresolved issues are easy to cite in conversation and commits.
- Keep priority visually distinctive with icon labels instead of bare `P0` / `P1`: `🚨 核心` blocks the next experiment or core conclusion; `⭐ 重要` can wait until the current core path is handled; `🌱 后续` is a known limitation or future improvement.
- For the total-note issue table, status has only two values: `未创建主线` and `已有主线`. Default new entries to `未创建主线`.
- Keep detailed progress states such as "待排查", "待补充", "待设计", "进行中", or "已解决" out of this table; write them in the issue card, mainline note, or debug record instead.
- Link each issue primarily to the mainline note that carries the relationship. Never put debug/work/experiment records from `2_调试记录/` in a Q issue card.
- Update this table first when new progress changes an active issue.
- Do not let old problems disappear without trace. Archive the detail in the relevant mainline or debug note before removing a row.

Use the currently discovered Templater command/template for issue or requirement entries. It should prompt only for problem name, problem description, and priority; create the next `Q` id; append one row before `<!-- AZF:ISSUE_TABLE_END -->`; append a matching callout under `问题/需求理解` (or legacy `问题理解`) before `<!-- AZF:ISSUE_CALLOUTS_END -->` when that anchor exists; and default the table status to `未创建主线`.

When the Buttons plugin is available, put a button directly under the issue table and before the priority reference line, configured to call the currently discovered issue/requirement Templater command. Do not hard-code a historical action name. Use the plugin's normal cursor-template invocation; do not pre-process the button with `templater true` unless the current template explicitly requires it. The command should modify the active total note itself and return empty output, so the button does not visibly insert template text.

When a Q later gains a real mainline, update its issue callout `主线入口` to the mainline link and change the table status to `已有主线`.

## 14. Mainline Notes

Use mainline notes when raw records are too isolated to show relationships. A mainline note summarizes one thread; it does not duplicate every detail. Prefer a concise linear mainline using date-based progress entries instead of a Step diary.

Mainlines are **not classified**: there is no `主要主线` / `临时主线` tag and the total note shows a single mainline list. Lifecycle lives in `推进状态` (`待处理` / `进行中` / `待验证` / `阻塞` / `已完成`), and a short-lived thread split off another mainline records its origin in `上位主线: "[[上位主线名]]"` instead of a tag. When the split-off thread is accepted, merge the stable conclusion back into the parent mainline, set its `当前状态` to say where it merged, and leave the note in place — do not move or delete it without asking.

All mainlines live directly under `1_主线笔记/`; do not split them into subfolders.

When creating or updating a mainline note, invoke the currently discovered Templater template for the mainline role. Do not write the body from a copied example. If the active Vault has no matching template, or the operation happens outside Obsidian without a callable Templater bridge, ask before proceeding; never recreate a guessed template.

Good mainline topics include "光谱仪连接与采集", "波长映射与频率插值", "FROG迹图反演与结果保存", or the equivalent threads for another project.

Mainline-writing rules:

- Start mainline filenames with `【主线】` unless the user says otherwise. Do not force rename older files without asking.
- Frontmatter includes `当前状态: 一句话状态` and `推进状态`; a split-off mainline also carries `上位主线`. There is no `当前焦点`, `阶段`, `阶段顺序`, `下一步`, or `关联问题` property any more, and there is **no stage configuration** at all: the project-stage model (the `阶段配置.json` file, its settings-page editor and the `## 阶段` block in the AI context) was removed on 2026-09-15. The briefing's opening line `当前阶段：<一句话现状>` is now a one-line state summary the model derives from the recorded facts. Do not add a `主要主线` / `临时主线` tag or a separate `主线` frontmatter property; the view's filename column reads the note name via `file.name`. Keep `笔记类型` and `笔记状态` filled as the required common properties; see the 笔记属性规范 for their value sets.
- The `【主线】` filename prefix is a naming convention only; never use it as a Components filter.
- Mainlines should sound like a clear handoff for a future beginner: "具体来说就是…" is better than formal abstract wording.
- Use `# 推进记录` with date headings such as `## YYYY-MM-DD：一句话结论`; do not use `Step 1/2/3` as the mainline structure.
- Each progress entry binds the progress, the plan used for it, and the debug record for it. If every run has a different plan, put `本次方案` under the matching progress entry instead of collecting all plan links at the bottom.
- Keep `# 相关入口` for stable cross-progress context only: total note, neighboring mainlines, manually maintained instrument-asset links, project-understanding notes, and long-lived references.
- Do not include code status in mainline notes. Branch, commit, working tree, gitGraph, commands, logs, and verification output belong in the matching debug record Step.
- Use three progress sizes: (1) one or two sentences with no evidence → a progress entry marked `调试记录: 无单独记录`; (2) one paragraph plus an explanatory screenshot → a progress entry plus a folded callout; (3) evidence screenshot, real-device result, CSV/log/command output, detours, or a point needing future audit → create a debug record and link it.
- Use folded callouts only for explanatory screenshots or light context. If the screenshot is evidence of real-device behavior, an error, a result, or a conclusion that may be challenged later, create a debug record instead.
- For explanatory folded callouts, preserve the original reasoning chain instead of flattening it into an agent summary. Title the callout as the question, start with date/context, place screenshots immediately after the claim they support, use short bullet groups such as `当时的操作是：` and `原因和代码依据见：`, keep background links under those bullets, and end with the decision or consequence. Do not turn this into a table unless truly comparing multiple items, and do not delete screenshots that explain a later decision.
- After each progress entry, write what it taught the mainline, not only that the work happened.
- Keep `当前理解`, `当前卡点`, and detailed `下一步` out of mainline notes by default; fold useful parts into `当前状态` or the specific progress entry.
- Use highlighted `<mark style="background:#fff88f">…</mark>` sparingly, for the one judgment a future reader must not miss.
- A mainline derived from another mainline can remain independent. Show the hierarchy in the total note; keep the note itself focused on its own problem.

## 15. Debug Records

Use `2_调试记录` for things that happened while working: code debugging, hardware tests, bug reviews, log reading, real-device validation, Git-backed changes, and progress handoff.

There is only one debug-record body format: the current Templater timeline template. Do not create separate templates for `实机验证记录`, `代码修改记录`, test sheets, or standalone Git cards. If a note is a debug/process record, invoke the currently discovered Templater template for that role and use the same timeline structure regardless of whether the work is code-only, hardware-only, real-device validation, or mixed. If no matching template can be found, ask; do not write a guessed minimal body.

- Existing experiment-record Markdown files should be moved under `2_调试记录/实验记录/` when the user wants a simpler structure.
- Do not rewrite old experiment records unless asked. If a later conclusion changes the interpretation, add a new note or a `后续更正` section.
- Keep chronological evidence in records; keep relationship summaries in mainline notes.
- If a note contains code changes, branch work, verification commands, SDK probing, calibration adoption, or future audit evidence, treat it as a real debug record: place it under `2_调试记录/` with `项目笔记类型: 调试记录`. Do not leave it under `4_补充资料/` merely because it began as supporting material.
- When cleaning a mainline entry that links to a debug record, inspect the linked record first. If the work involved Git, confirm that branch/commit/worktree/verification information exists in the chronological Step where the change happened. The mainline may omit Git details; the debug record must not.
- If a debug record is tied to code in a Git repository, include code version information inside the relevant Step, not only in a progress file or commit message.

Git-bound debug records must state: the repository path; current branch and remote tracking branch when known; base/start commit, feature commit, and current commit; push status and working-tree status; the verification commands belonging to that code version; the Git graph command used; and a complete visualization, preferably a Mermaid `gitGraph`, inside the Step where the change happened. If Mermaid would be misleading, include a raw `git log --oneline --graph --decorate` excerpt in that same Step.

For modern records, use top-level `#` headings because the filename already carries the title.

### Timeline Debug Process Record

Use the body generated by the currently discovered Templater template. The conceptual shape is:

```text
frontmatter
# 一、调试目标
# 二、调试过程
## Step 1：…
  操作 / 现象 / 证据入口 / 判断
  Git 信息（only when this Step involves code, branch, commit, push, rollback, or code-version verification）
## Step 2：…
## Step 3：…
# 三、调试结论
# 四、同步判断
```

Timeline rules:

- Keep the main structure fixed as `调试目标` → `调试过程` → `调试结论`.
- Write Steps in real chronological order. Each Step explains what was done, what was seen, and what judgment changed.
- Step fields are flexible: use only what the step needs among `操作`, `现象`, `证据入口`, `涉及文件`, `处理`, `验证`, `判断`, `Git 信息`, `Git 可视化`.
- Tables are allowed inside Steps when comparing devices, expected/actual behavior, pass/fail items, files, commands, or result paths. Do not turn the whole record into a test sheet.
- Do not manually expand code diffs. For code steps, write the intent, affected files, verification result, Git commit/branch, and evidence paths; exact diffs can be recovered from Git later.
- Put Git cards and Mermaid `gitGraph` inside the Step where the change happened; do not create a separate top-level Git chapter. Make the visualization complete enough to reconstruct the branch story.
- Use highlighted `<mark style="background:#fff88f">…</mark>` sparingly.
- Planned on-site checklists are allowed under `2_调试记录`, written in the same timeline format with `笔记状态: 待复测` and future-tense Steps.

## 16. Reference And Supplement Notes

Use project-understanding and supplement notes for facts that should not be rediscovered:

- Environment/dependencies: conda environments, packages, DLLs, vendor software, data paths, and setup constraints.
- Project understanding: what the project does, source modules, data flow, risks, and diagrams.
- SOP/material notes: repeated operation steps, GUI guides, old plans, code-reading introductions, and result evaluations.

Hardware asset facts stay in `03-Academic Toolkit/2_资源与档案/仪器设备资产`. For a hardware status image or test, record the event in `2_调试记录/`; do not create or update a project-local hardware card.

## 17. Images And Attachments

Images are first-class evidence, not secondary attachments.

- If he provides a lightweight image, screenshot, GUI capture, plot, result figure, equipment photo, or document photo, copy it into the vault and embed it directly in the most relevant note with `![[...]]`.
- Put the image close to the explanation that depends on it, usually before the bullet list of observed facts or directly under a section such as `图片证据`, `实验结果`, `官方资料截图`, or `现象截图`.
- Prefer one well-placed embedded image over a text-only summary. A note should be understandable by looking at the image first, then reading the interpretation.
- Use an external path only for large, sensitive, proprietary, or bulky raw files that should not be duplicated into the vault, and explain why it was not copied.
- For repeated images, embed the image in the canonical evidence note and link to that note from lighter summary/mainline notes.

When reorganizing notes:

1. Move the matching attachment mirror folders under `Attachments/...` together with the Markdown files.
2. Preserve image filenames; do not rename images to make the tree prettier.
3. Use readable copied filenames for new evidence images when possible, for example `Zolix_SGM1700_官方波长范围_20260601.png`.
4. If a note embeds `![[image.png]]`, verify the image still exists somewhere in the vault.
5. If an attachment path uses an explicit folder path, update it to the new folder.

Classify incoming photos first:

| Type | Examples | Destination |
|---|---|---|
| Hardware status | equipment, labels, cables, ports | project debug record; link to the manual instrument asset when useful |
| Software status | GUI, settings, device manager, terminal | debug record |
| Result | spectrum, trace, plots, reconstruction | debug record and mainline note |
| Error | dialog, logs, stack trace | bug review |
| Source material | SDK folders, manuals, drivers | reference or supplement note |

Record each image as fact first, judgment second:

```markdown
![[图片文件名.png]]

- 图片来源：
- 直接可见事实：
- 当前判断：
- 应同步到：
```

## 18. Reorganization Rules

Before broad changes:

1. Read the current tree with `rg --files`.
2. Read the total note, progress/debug note, and recent records.
3. Create a rollback backup under `E:\software\CodexPlusPlus\Codex备份\YYYYMMDD_HHMMSS_任务名_修改前备份`.
4. Move notes and attachment mirrors together.
5. Update navigation notes, old aliases, and direct attachment paths.
6. Verify ordinary wikilinks and embedded images after the move.

Report counts like:

```text
WIKILINK_MISSING=0
EMBED_MISSING_OUTSIDE_CODE=0
```

Ignore placeholder image names inside fenced code templates when checking embeds.

## 19. Writing Style

- Use plain Chinese and write like a clear lab handoff.
- Separate "what I saw" from "what I think it means".
- Do not write uncertain things as confirmed.
- Keep names short and beginner-friendly.
- Avoid making the total note a raw log.
- When creating a Markdown note, do not repeat the filename as a first `# ...` heading.

## 20. Deep Learning Experiment Link

When the record involves deep-learning runs, metrics, checkpoints, figures, or baselines, use `azf-deep-learning-experiment-record` for evidence writing. This skill remains responsible for the project-level note structure, total note, mainline notes, and debug-record placement.

## 21. Maintenance Closeout

At the end of a maintenance pass:

1. Confirm the total note's current status is fresh.
2. Confirm the total note's `目前待解决的问题` section is fresh.
3. Confirm mainline notes explain how different records relate.
4. Confirm debug records are in `2_调试记录` and project-understanding notes are in `3_项目理解`.
5. Confirm old links are covered by aliases or updated paths.
6. Confirm attachment embeds still resolve.
7. Do not audit or mutate the separate instrument-asset folder as part of this closeout.
8. Report what changed, what the reuse check found, what needs An Zhaofeng's decision, and where the backup is.
