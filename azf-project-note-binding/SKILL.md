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
- Avoid duplicating the same Obsidian/Excalidraw link on the card rectangle, title, subtitle, and hint text at the same time. One intentional link per card is enough unless An Zhaofeng explicitly asks for multiple hotspots.
- Use Excalidraw as an infinite canvas, not a single-screen slide. Do not compress a project map just so every node fits in one screenshot. Prefer generous spacing, logical branches, and local readability over one-screen completeness.
- Cards must be generated with content-aware dimensions. Estimate text/code line count and longest line before creating the rectangle; then set card width/height with comfortable padding. Do not rely on fixed card sizes that cause overlap or clipping.
- Card text must never overlap, collide, or visually stack on top of other text inside the same card. Treat internal text overlap as a hard layout failure: split the text into separate elements, increase card height/width, add line spacing, or move details to a branch card before delivery.
- Prioritize readability of code identifiers in master maps. Put English file names, class names, function names, and other code identifiers in their own text elements, use Excalidraw's code/monospace font family when available, increase their font size, and use a darker/high-contrast stroke. Keep Chinese role/explanation text in the hand-drawn font. Do not mix code identifiers and Chinese explanation in one cramped text box when different fonts or emphasis are needed.
- For mixed code-and-Chinese cards, size from the actual rendered text blocks rather than from a rough rectangle template. A good card has clear internal lanes: title, code identifiers, Chinese explanation, and optional jump link. Leave visible padding around every lane; if text needs to shrink below readable size, enlarge the card or spread the node onto the infinite canvas.
- When splitting, restyling, or regenerating card text, preserve or rebuild all Obsidian note links. Visible jump labels such as `📍02_整体运行入口` must have a real Excalidraw `link` field, not just plain text. After modifying a linked diagram, inspect the decompressed drawing JSON and confirm the expected link count is greater than zero before reporting completion.
- Prefer the clean code-flow style An Zhaofeng accepted: a readable left-to-right main chain, one or two clearly placed branches, no oversized background stage frames, and no dense dashboard layout. Stage text such as `推理与评估` can be a small label near the relevant branch instead of a giant dashed container.
- For ISFC-like code overview maps, prefer this composition: title and short subtitle at top left, a small `当前已实现闭环` label, a horizontal main chain, a lower branch from `训练入口` to `输出与归档`, a right-side `推理画图 -> 测试指标` branch, and a red dashed `下一阶段数据源` card below the data node with a dashed arrow back into data preprocessing.
- Use dashed rectangles only when they are themselves meaningful nodes, such as `下一阶段数据源`. Avoid large dashed frames that make the drawing look misaligned or boxed-in. If a stage frame is truly needed, it must tightly contain its nodes with consistent padding and must not visually fight the cards.
- Master-map arrows must connect to node/card rectangles with `startBinding` and `endBinding`, and the corresponding rectangles must include matching `boundElements`.
- Master-map arrows should feel hand-drawn and explanatory, not mechanically shortest. Use gentle, readable routes that support human understanding; a slightly longer route is better if it is calmer, clearer, and more beautiful.
- Arrow elements are not allowed to overlap cards, code blocks, labels, link text, stage labels, or other meaningful elements. If an arrow crosses content in a screenshot, the diagram is not acceptable; move nodes or redraw the route.
- Arrow routes must not cross each other in the visible layout, and should not run directly over or tightly along the top edge of a card. If a route needs to pass near a node, leave clear whitespace around the card or use a simple orthogonal/dogleg path around it. Treat crossed lines or top-edge "压顶" routes found in screenshot QA as layout failures that require rerouting before delivery.
- Dashed arrows count as full arrows in QA. Do not let a dashed arrow overlap, skim, or visually merge with a card border, hachure fill, note boundary, or another arrow segment. A dashed route that only "barely touches" a card edge is still a layout failure unless that point is the intentional bound endpoint.
- Keep generous spacing between nodes so An Zhaofeng can write study notes around them. Do not pack nodes just to fit the whole map into one viewport; use the infinite canvas.
- Preserve a fresh hand-drawn style in master maps: rough lines, soft pastel fills, light hachure, clean whitespace, and non-rigid composition. Beauty and clarity come before compactness.
- The master map should present a simple, memorable logic first. Avoid adding every support file as a visible node if it makes the core code story harder to read; secondary source-level breakdowns should stay in `源码拆解/` and be linked from the index.

For file-level code understanding, create native `.excalidraw` diagrams that include:

- Real code snippets pasted as text blocks, especially class/function signatures and important logic blocks.
- Prefer complete code coverage for learning diagrams. Do not summarize away large parts of a source file by default. Split long functions into multiple cards or branches, and keep all important imports, helpers, main functions, loops, saves, and CLI entrypoints represented.
- Structure boxes for imports, dataclasses, classes, helper functions, entry functions, outputs, and error-prone details.
- Arrows showing call flow and data flow.
- Plain-Chinese explanations next to the relevant code blocks.
- A small "当前理解 / 待验证 / 下一步" area.
- Bound arrows: set arrow `startBinding` / `endBinding` to the card rectangles and add matching `boundElements` on the cards so arrows follow when cards move.
- Polished code cards: each card should have a title bar, a visually separate code block area, and a short explanation area. Do not let code text exceed its card.
- Inside every code card, title text, code text, data traces, Chinese notes, and jump links must occupy non-overlapping lanes. Any internal text overlap, stacked text, clipped text, or border-touching text is a hard failure; enlarge the card or split the card before delivery.
- Code-card titles should start with a short Chinese learning name and then keep the Python identifier after a separator, for example `权重初始化 · ISFCMLP._initialize` or `训练批次循环 · run_training`. Prefer one-line titles so the title bar does not push the code block into a cramped layout.
- For code-flow cards, use An Zhaofeng's accepted input/output style: keep arrows text-free and avoid visually prominent input/output labels. For every real processing, shape-changing, loading, saving, training, inference, metric, or configuration card, add a very subtle data-trace line inside the code block's lower-right corner. Format it as a compact one-liner such as `frames + fs_hz -> x: (N, 94)`, `cfg + .mat -> MatDatasetArrays`, or `y_true/y_pred -> metrics.json`. It should be small, right-aligned, low-opacity, and muted gray/blue, like a faint code-block annotation rather than a separate UI label. Do not use visible `接收`, `处理`, or `输出` tags unless specifically requested. If there is not enough blank space in the code block, enlarge the code block and card before omitting the trace. The trace must never overlap code text, card notes, borders, or arrows. Tiny router/branch nodes can stay minimal.
- Preserve a fresh hand-drawn Excalidraw feel: prefer rough lines, light pastel paper cards, airy spacing, and minimal UI chrome. Avoid rigid dashboard-style cards unless the user asks for that look.
- Route arrows through whitespace using short, natural paths. Avoid arrows crossing over existing cards, code blocks, or explanatory text; if overlap appears, redesign the layout rather than forcing the arrow through content.
- Keep file-level arrow routing planar where possible: lines should not cross each other, and they should not skim across card tops. When branches would create crossings, spread the branch nodes, add a small router point, or use a calm dogleg path through open canvas space.
- During screenshot QA, inspect dashed arrows separately from solid arrows because they are easier to miss. Check that every dashed arrow has clean white-space clearance from card borders, hatch marks, notes, and other connectors.
- For branch/router nodes, avoid sending multiple arrows from the exact same point if it creates a knot or loop. Use separate visual exits, such as an upper-right exit for the upper branch and a lower-right exit for the lower branch, while keeping arrows bound to the router/card elements.
- Prefer clear data-flow or mind-map structures over grid dashboards for code reading. The diagram should feel like a readable whiteboard, not a UI panel mockup.
- When a source file has too much code for one readable map, keep the main file map as the trunk and create logical branch maps as separate `.excalidraw` files. Leave a clearly named link on the trunk card to the branch map.
- Leave intentional blank space for An Zhaofeng's own study notes. Do not fill the whole canvas. For simple learning notes, leave writable space directly near the related node; for complex explanations, create or link a separate Markdown note.
- When arranging the canvas, include a lightly indicated "我的补充笔记" or equivalent blank zone only when it helps orientation; otherwise leave clean open whitespace around major branches.
- Screenshot QA: after generating or updating an Excalidraw code diagram, render or screenshot a preview when possible and inspect for cramped cards, text overflow, broken arrows, or incoherent overlap before reporting completion.
- Screenshot QA must include visual layout judgment, not only element counts. Check both the full canvas and any dense/local problem area. Do not accept a diagram if text touches or crosses a card border, code annotations overlap real code, arrows awkwardly collide with content, or a card looks visually unbalanced. Prefer at least 16 px of internal breathing room around explanatory text.

### Excalidraw Pitfalls To Avoid

These pitfalls came from the ISFC code-understanding iteration and should be treated as hard lessons for new windows/models:

- Do not make the graph look like a cramped single-screen slide. An Zhaofeng wants an infinite whiteboard for learning, with readable local detail and blank space for notes.
- Do not add big dashed stage frames just to show phases. They often drift, look misaligned, and make the drawing feel boxed-in. Use small labels or meaningful dashed cards instead.
- Do not use card text for maintenance status, such as `子图已连接`, `已同步`, or `打开 xxx 已连接`. The card must explain the code: Chinese role name, script/function name, and what it does.
- Do not duplicate the same link on every text element inside a card. Use one intentional card-level or bottom-right jump link, so the drawing stays clean.
- Do not leave visible jump text without a real Excalidraw `link` property. A label that looks like a note entrance but cannot be clicked is a broken diagram.
- Do not let arrows cross cards, code blocks, notes, link text, or stage labels. If an arrow collides with content, move nodes or redraw the route through whitespace.
- Do not accept arrow crossings as "good enough" in Excalidraw maps. Also avoid arrows that travel across the top edge of a card, because they visually press on the card even when they do not technically overlap text.
- Do not excuse dashed-arrow collisions as minor decoration. Dashes can hide border overlaps in a zoomed-out screenshot; zoom or crop dense areas and reroute if any dash touches a card edge or another connector.
- Do not chase mathematically shortest arrows if they look stiff or awkward. Prefer a calm hand-drawn route that helps the eye understand the flow.
- Do not leave arrows unbound. Arrows that represent node relationships must use `startBinding` and `endBinding`, and the related cards should include matching `boundElements`.
- Do not rely on fixed card dimensions. Measure or estimate title length, code line count, note length, and trace text before sizing the card.
- Do not let internal card text overlap under any circumstance. If rendered text collisions appear in the preview, the correct fix is to enlarge the card, split the content, or move details to a branch map, not to accept the collision.
- Do not let code text, Chinese notes, or faint data traces touch borders. Increase code block/card height first; shrinking the content is a last resort.
- Do not omit large chunks of source code in file-level learning diagrams. If a file is long, split the function into multiple cards or branch maps while preserving complete learning coverage.
- Do not make input/output labels visually loud. For code cards, keep data traces as faint lower-right code-block annotations. If there is no spare line, enlarge the code block and card.
- Do not reserve a separate obvious "blank note zone" unless it improves orientation. Usually, leave natural whitespace around the relevant node instead.
- Do not report completion from JSON inspection alone. Always render or screenshot important diagrams, then visually check alignment, overlap, card balance, arrow routing, and whether the style still feels fresh and hand-drawn.

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

When code changes have been made and the notes may need to be synchronized:

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
- Do not silently sync notes after code edits; ask first unless the user already confirmed.
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
