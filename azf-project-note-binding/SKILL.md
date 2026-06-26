---
name: azf-project-note-binding
description: Bind An Zhaofeng's code projects to Obsidian project notes and maintain the `4_项目理解` code-understanding layer. Use when the user asks to bind a repository/project to Obsidian, create or update .azf/project-notes.yaml, generate or sync project-understanding notes, source breakdowns, Excalidraw code maps, or asks "代码改了笔记怎么同步", "项目和笔记绑定", "同步项目笔记", "整理项目理解", "源码拆解".
---

# AZF Project Note Binding

Use this skill to connect a code project with its Obsidian project folder, then maintain the code-understanding layer when the code changes. Pair it with `azf-obsidian-work-record` for the project work-record structure and `azf-deep-learning-experiment-record` when the code change involves training artifacts or metrics.

## Boundary With Work Records

This skill owns `4_项目理解`: code maps, source breakdowns, module notes, Excalidraw diagrams, and code-change sync records.

It does not own the whole Obsidian project structure. Let `azf-obsidian-work-record` create or maintain:

- `0_总览`
- `1_主线笔记`
- `2_调试记录`
- `3_硬件信息`
- `5_补充资料`

When starting a new project, first establish the work-record skeleton with `azf-obsidian-work-record`, then bind code understanding here.

## Core Rule

When An Zhaofeng starts a new project or asks for code understanding/code reading/code structure analysis in a project, ask before doing broad setup:

```text
这次代码理解要不要同时建立 Git 管理和 Obsidian 代码理解笔记结构？
```

When the request starts from `azf-obsidian-work-record` new-project setup, only run this skill if An Zhaofeng confirms that code breakdown/project understanding is needed. If he says it is not needed now, leave `4_项目理解/` empty and do not create `.azf/project-notes.yaml`, source breakdown notes, or Excalidraw code maps.

If he says yes, propose or create:

- Git initialization or branch/checkpoint plan, depending on whether a repo already exists.
- `.azf/project-notes.yaml`.
- Obsidian `4_项目理解/` structure and main project/code-understanding index.

If he says no, proceed with code reading only and do not create note-binding files.

Every bound code project should have a machine-readable binding file:

```text
<code project>/.azf/project-notes.yaml
```

This file is the source of truth for where the Obsidian notes live. Do not rely on memory or fuzzy path guesses once a binding exists.

## Binding Schema

Prefer this shape:

```yaml
project_id: 20260506_ISFC
project_name: ISFC模型仿真复现
code_root: D:/path/to/code/project
note_root: E:/software/Obsidian/安钊锋的外置大脑/01-Project/项目文件夹

notes:
  total_note: 0_总览/项目名总笔记.md
  reading_order: 0_总览/项目名新手阅读顺序.md
  debug_progress: 2_调试记录/项目名调试进度.md
  experiment_dir: 2_调试记录/实验记录
  project_understanding_dir: 4_项目理解
  project_understanding_map: 4_项目理解/0_项目理解总图.excalidraw.md
  project_understanding_index: 4_项目理解/1_项目理解索引.md
  source_breakdown_index: 4_项目理解/2_最低限度源码拆解.md
  source_breakdown_dir: 4_项目理解/源码拆解
  code_sync_dir: 4_项目理解/代码变更同步记录

sync:
  mode: manual
  last_sync: null
  update_policy:
    total_note: status_only
    mainline_notes: link_only_when_relationship_changes
    code_notes: affected_only
    old_notes: append_correction_do_not_rewrite_history
    require_user_confirmation_before_note_sync: true
```

Use forward slashes in YAML paths. Absolute paths are allowed because this is a personal local workflow. If the project may move across machines, also include relative paths where useful.

## Excalidraw Rule

Use native `.excalidraw` files for project master maps unless An Zhaofeng explicitly asks for `.excalidraw.md` or has already accepted the new Obsidian Excalidraw plugin format for that project.

Reason: An Zhaofeng's current Obsidian Excalidraw workflow can use `.excalidraw` files for note binding and external links. Do not force `.md` containers just for Obsidian integration. If a project already uses `.excalidraw.md`, keep it unless there is a reason to migrate.

When An Zhaofeng asks for or approves the new Obsidian Excalidraw format, treat `.excalidraw.md` as the canonical editable diagram file for that project. Keep raw `.excalidraw` files only as backups, legacy artifacts, or tooling intermediates; do not leave the main note links pointing at the old raw file.

For actual Excalidraw generation, layout, card sizing, arrow routing, text overflow prevention, link preservation, and screenshot/visual QA, use the dedicated `excalidraw-diagram` skill. This skill only defines where code-understanding diagrams belong and what project role they serve.

## Code Visualization In Excalidraw

When An Zhaofeng asks for code visualization, prefer detailed Excalidraw code workbenches over prose-heavy Markdown module notes.

Default Obsidian structure for a new code-understanding project:

```text
4_项目理解/
  0_项目理解总图.excalidraw.md
  1_项目理解索引.md
  2_最低限度源码拆解.md
  源码拆解/
    <source-file-learning-name>.md
    <source-file-learning-name>.excalidraw.md
  流程理解/
  代码变更同步记录/
```

In this workflow, `4_项目理解` means code-first project understanding. Do not create a separate `代码理解/` folder unless An Zhaofeng explicitly asks for it. The master file `0_项目理解总图.excalidraw.md` is the code/project understanding overview map: it should look like a clean code flow map, not a project-management dashboard, background note, or concept encyclopedia. Markdown in the project-understanding root should stay thin and serve as indexes only.

For source-code breakdowns, keep the Markdown source note and its Excalidraw code diagram side by side under `4_项目理解/源码拆解/`. Do not create a separate current-level `文件结构图/` directory for source-code breakdown diagrams unless An Zhaofeng explicitly asks for that structure.

The `4_项目理解` root should have only a few beginner-friendly entrances. Use single-digit prefixes for the current root entrance notes. Older `00_` / `01_` names can be kept as aliases during migration, but new projects should use `0_`, `1_`, `2_`.

For project-level master maps, keep each node focused on code understanding:

- Card content should be `module role -> script/file name -> one short plain-Chinese responsibility`.
- Do not write implementation/status phrases such as `子图已连接`, `已同步`, or other tool-maintenance text inside the card body.
- Use only one visible jump entry per card, usually a small bottom-right text such as `打开结构图`, `打开配置笔记`, or `打开输出笔记`.
- The master map should present a simple, memorable logic first. Avoid adding every support file as a visible node if it makes the core code story harder to read; secondary source-level breakdowns should stay in `源码拆解/` and be linked from the index.

For file-level code understanding, create native `.excalidraw` diagrams that include:

- Real code snippets pasted as text blocks, especially class/function signatures and important logic blocks.
- Prefer complete code coverage for learning diagrams. Do not summarize away large parts of a source file by default. Split long functions into multiple cards or branches, and keep all important imports, helpers, main functions, loops, saves, and CLI entrypoints represented.
- Structure boxes for imports, dataclasses, classes, helper functions, entry functions, outputs, and error-prone details.
- Arrows showing call flow and data flow.
- Plain-Chinese explanations next to the relevant code blocks.
- A small "当前理解 / 待验证 / 下一步" area.
- Prefer clear data-flow or mind-map structures over grid dashboards for code reading. The diagram should feel like a readable whiteboard, not a UI panel mockup.
- When a source file has too much code for one readable map, keep the main file map as the trunk and create logical branch maps as separate `.excalidraw` files. Leave a clearly named link on the trunk card to the branch map.

Recommended location:

```text
4_项目理解/源码拆解/<source-file-learning-name>.md
4_项目理解/源码拆解/<source-file-learning-name>.excalidraw.md
```

Keep Markdown notes as thin indexes, sync records, experiment records, or searchable summaries. Do not replace a detailed code-structure Excalidraw with a long Markdown explanation unless the user asks for Markdown.

## Initial Binding Workflow

1. Inspect the code project root.
2. Search the Obsidian vault under `01-Project` for the matching project folder.
3. If no obvious match exists, propose a note folder but do not create many files without confirmation.
4. Create `.azf/project-notes.yaml`.
5. Ensure the note folder has:
   - total work-record note
   - debug progress note or equivalent
   - `4_项目理解/0_项目理解总图.excalidraw.md`
   - `4_项目理解/1_项目理解索引.md`
   - `4_项目理解/2_最低限度源码拆解.md`
   - `4_项目理解/源码拆解/`
6. Add a short reciprocal link in the total work-record note pointing to the code index.

## Sync After Code Changes

When code changes have been made and the notes may need to be synchronized, remember that code work is not permission to edit the Obsidian vault.

Default boundary:

- Ordinary coding, debugging, hardware troubleshooting, Git commits, or test runs must not modify Obsidian notes unless An Zhaofeng explicitly asks in the current turn to update/sync/write/organize notes.
- It is acceptable to read `.azf/project-notes.yaml` and relevant notes for context.
- If the user did not ask for note synchronization, do not create sync records, do not update total notes, and do not rewrite mainline notes. At most, say in the final response that note synchronization was not performed and can be done later.

When An Zhaofeng explicitly asks for note synchronization after code changes:

0. Stop and ask An Zhaofeng whether to sync the Obsidian notes before editing the note vault, unless he has already explicitly authorized note synchronization in the same turn. The question should be short and concrete, for example:

```text
这次代码改动影响了数据流和运行入口，我建议同步 Obsidian 的代码理解笔记。要现在同步吗？
```

Only modify notes after confirmation. It is okay to inspect the binding file and read relevant notes before asking, but do not write to the Obsidian vault until confirmed.

When the user asks to sync notes after code changes, or confirms synchronization:

1. Read `.azf/project-notes.yaml`.
2. Inspect code changes:
   - If Git exists, use `git status --short` and focused `git diff -- <files>`.
   - If Git does not exist, use file mtimes and focused reads; recommend initializing Git before ongoing development.
3. Classify changes:
   - `entrypoint`: CLI commands, scripts, run flow
   - `data_flow`: data loading, preprocessing, formats, shapes
   - `model_or_core`: model, algorithms, hardware-control core, simulation core
   - `config`: config files, environment, paths, parameters
   - `experiment`: training outputs, metrics, figures, checkpoints
   - `docs_only`: README, comments, prose
4. Update only affected notes:
   - `entrypoint` -> `4_项目理解/源码拆解/` and `4_项目理解/1_项目理解索引.md`
   - `data_flow` -> `4_项目理解/流程理解/` and relevant source-breakdown notes
   - `model_or_core` -> `4_项目理解/源码拆解/` and `4_项目理解/0_项目理解总图.excalidraw.md`
   - `config` -> relevant source-breakdown or environment reference note
   - `experiment` -> ask whether to update `2_调试记录/实验记录/` via `azf-deep-learning-experiment-record`
5. Always create or append one dated sync record:

```text
4_项目理解/代码变更同步记录/YYYYMMDD_代码变更同步.md
```

The sync record should include:

- changed files
- what changed in plain Chinese
- which notes were updated
- what is still uncertain
- next recommended check

## What Not To Do

- Do not rewrite old experiment records just to make them look consistent.
- Do not move attachments during a code-note sync.
- Do not update every code note for every code change.
- Do not silently sync notes after code edits; code edits do not imply note-edit permission.
- Do not write Obsidian notes during ordinary code/debug/hardware work unless An Zhaofeng explicitly requested note updates in the current turn.
- Do not pretend an unverified behavior is confirmed. Mark it as "待验证".
- Do not create one note per source file unless the file is truly a stable module worth revisiting.
- Do not create project-wide navigation in `4_项目理解`; that belongs in `0_总览` and `1_主线笔记`.

## Good Sync Output

At the end of a sync pass, report:

```text
绑定文件:
笔记根目录:
代码变更类型:
已更新笔记:
新增同步记录:
未处理/待验证:
```

Keep the user-facing summary short. The detailed reasoning belongs in the dated sync record.
