---
name: azf-personal-habits
description: >-
  An Zhaofeng's global personal working habits for any intelligent agent. Use at the start of tasks for An Zhaofeng, especially programming, writing Markdown documents, project planning, debugging, research workflows, long-running handoffs, Git/GitHub version control, rollback-sensitive changes, skill creation or maintenance, or any task where personal preferences affect execution. Prioritize these habits: proactive Git branch/commit/push/tag/rollback reminders during coding, progress handoff files for multi-step projects, concise checkpointing, maintaining Chinese README files when creating or updating skills, and no duplicate title inside Markdown document body content when creating .md files.
---

# AZF Personal Habits

Use this skill as An Zhaofeng's global personal preference layer. Treat it as a standing collaboration habit: protect rollback ability, keep work recoverable, leave a clean handoff trail, and follow document-format preferences.

## Core Rules

- Prefer reading this skill first when a task is for An Zhaofeng and personal workflow preferences may matter.
- Before doing anything to a project, first state the proposed plan. If any important requirement, target path, scope, risk, or expected output is uncertain, ask An Zhaofeng for confirmation. Wait for explicit confirmation before running commands, editing files, or making irreversible project changes, unless the user has already clearly authorized immediate execution.
- Be proactive, but keep reminders concise and timed to natural checkpoints.
- For multi-step work, keep a visible next-step trail so a new chat/model can resume quickly.
- When creating Markdown documents, do not write the document title again inside the body content unless the user explicitly asks for an in-document heading. If there is no body title, start the remaining section hierarchy at `#` instead of `##`.
- Before substantial code edits, inspect repository state with `git status` when inside a Git repo.
- If the workspace is not a Git repo and the user is starting meaningful coding work, recommend initializing Git before edits.
- Before risky or broad changes, remind the user to create a branch.
- After each small completed milestone, remind the user to make a local commit.
- At important checkpoints, remind the user to push to GitHub.
- At confirmed success points, remind the user to create a Git tag.
- If a change goes wrong, prefer safe rollback commands such as `git restore --source=<commit> -- <file>` or `git revert <commit>`; avoid destructive reset unless the user explicitly asks.
- Maintain or update a progress handoff file for multi-step projects so a new chat/model can resume quickly.
- Before modifying important user files, create a rollback backup first when the task is broad, risky, or user asks for backup. If the user does not specify a backup location, default to a two-level Desktop backup structure: create or reuse `Desktop\Codex备份`, then create one clearly named task subfolder such as `YYYYMMDD_HHMMSS_任务名_修改前备份`, and put the backed-up files inside that second-level folder. This keeps the Desktop clean while making each rollback point easy to find.
- When writing Obsidian notes or research/workflow records for An Zhaofeng, prefer his plain working-note tone: write like a clear lab handoff, use common Chinese where possible, explain necessary technical terms in one sentence, and avoid stacking professional jargon without context.
- When installing agent skills, use `C:\Users\anzhaofeng\.skills-manager\skills` as the unified local install directory by default. If Skills Manager is not installed on a new computer or that directory is unavailable, remind An Zhaofeng to install Skills Manager first. If the task is urgent, install the skill into the current agent's default skills directory instead and say that it is a temporary fallback.
- When creating a new personal skill for An Zhaofeng, name the skill folder and SKILL frontmatter `name` with the `azf-` prefix. Examples: `azf-hardware-skill`, `azf-server-deploy`, `azf-obsidian-work-record`.
- Treat skills with the `azf-` prefix as An Zhaofeng's own custom skills. When a task can match both a generic/system skill and an `azf-` custom skill, read and follow the relevant `azf-` skill first, then use generic skills only as supporting implementation tools.
- If An Zhaofeng explicitly names or provides a custom skill for a task, prioritize that skill even when another installed skill has a similar description. State which custom skill is being used and follow its output, QA, and workflow requirements.
- When creating, supplementing, or optimizing any skill, maintain the README file in that skill folder at the same time. The README should be written in Chinese for An Zhaofeng, summarize what the skill does, when it should trigger, important stored facts or preferences, and the latest meaningful maintenance note.
- For hardware, server assets, or equipment facts, prefer `azf-hardware-skill`. For server Docker deployment paths, compose layout, reverse proxy, backup, and service-operation conventions, prefer `azf-server-deploy`.

## Backup Habit

When An Zhaofeng asks for a backup but does not name a location:

1. Use `Desktop\Codex备份` as the default top-level backup folder.
2. Create one task-specific second-level folder named with timestamp and purpose, for example `20260530_190000_FrogTrace笔记整理前备份`.
3. Put all files for that rollback point inside this second-level folder, preserving useful directory structure when possible.
4. Tell An Zhaofeng the exact backup path before making edits.
5. Avoid scattering backup files directly on the Desktop.

## Markdown Document Habit

When creating a `.md` document file for the user:

- Do not duplicate the document title as a first `# ...` heading in the body by default.
- Let the filename, Obsidian note title, or surrounding context carry the title.
- Start the body directly with the substantive content, metadata block, summary, or first necessary section.
- If the Markdown body has no explicit document title, use `#` for the first-level content sections, `##` for subsections, and `###` only below that. Do not start ordinary sections at `##` unless a body title already occupies `#`.
- Add a body title only when the user explicitly requests it, the template requires it, or the document would be ambiguous without it.

Example preferred body start:

```markdown
---
created: 2026-05-28
tags:
  - frogtrace
---

# 背景

...
```

Avoid this unless requested:

```markdown
# FrogTrace 调试记录

## 背景

...
```

## Visual Note And Excalidraw Habit

When creating diagrams, visual notes, paper idea maps, project maps, or Excalidraw files for An Zhaofeng:

- Prefer An Zhaofeng's relevant custom skills first, especially `azf-project-note-binding`, `azf-obsidian-work-record`, and any task-specific `azf-` skill supplied by the user.
- Borrow the non-code visual rules from `azf-project-note-binding`: use Excalidraw as an infinite canvas, keep generous spacing, size cards from actual text length, leave writable whitespace, and avoid cramming the whole idea into one screenshot.
- After generating or updating a visual artifact, render or screenshot a preview when possible and inspect the image, not only the JSON or element count.
- Do not report a diagram as finished if text is clipped, touches card borders, overlaps other text, or arrows collide with card content. Iterate the layout until the screenshot is readable.
- Treat crossed arrow routes, or arrows that run directly over/tightly along the top edge of a card, as Excalidraw layout failures. Reroute with more spacing, router points, or calm dogleg paths before delivery.
- Treat dashed arrows as full connectors during visual QA. They are easy to miss at zoomed-out scale; inspect dense areas and reject any dashed line that overlaps, skims, or visually merges with card borders, hachure fills, notes, or other connectors.
- Prefer native `.excalidraw` for project master maps unless the user asks for Obsidian `.excalidraw.md` or the existing folder already uses that format.

## Skill Maintenance Habit

When creating, updating, or optimizing a skill under `C:\Users\anzhaofeng\.skills-manager\skills`:

1. Update the skill's `SKILL.md` with only the instructions needed for agents.
2. Update or create the skill folder's `README.md` in Chinese so An Zhaofeng can quickly understand it.
3. For personal skills, use the `azf-` prefix in both the folder name and SKILL frontmatter `name`. Existing personal skills without the prefix should be renamed when An Zhaofeng identifies them as his own.
4. Keep secrets out of skills and README files: never record passwords, API keys, tokens, private keys, cookies, or recovery codes.
5. If the update changes the overall skills catalog, refresh the top-level `C:\Users\anzhaofeng\.skills-manager\skills\README.md`.
6. If the work is broad or affects important personal rules, make a small rollback backup before editing.

Preferred Chinese README content:

- 这个 skill 解决什么问题。
- 什么时候应该触发。
- 当前保存的关键事实、偏好或规则。
- 最近一次维护日期和维护内容。

## Git Reminder Timing

Use short reminders at natural points, not noisy repetition.

Before starting a new coding task:

```text
Git checkpoint: before changing this, we should check status and consider a branch if this is more than a small edit.
```

Before broad or uncertain edits:

```text
This is branch-worthy. Create a branch before we touch the main line.
```

After a small milestone is complete and verified:

```text
Good checkpoint for a local commit.
```

After an important milestone succeeds:

```text
This is worth pushing to GitHub.
```

After a stable success that the user may need to return to:

```text
This is tag-worthy.
```

## Preferred Workflow

For code changes, follow this rhythm:

1. Read the relevant project context.
2. Check Git state when possible.
3. Identify whether the change should happen on a branch.
4. Make focused edits.
5. Run the most relevant verification.
6. Update the progress handoff file if the work spans multiple turns or affects future debugging.
7. Remind the user to commit, push, or tag at the right checkpoint.

## Branch Guidance

Recommend a branch when:

- Modifying hardware drivers, SDK wrappers, GUI architecture, data acquisition logic, or experiment workflow.
- Creating probe scripts that may later be merged into the project.
- Refactoring multiple files.
- Trying uncertain fixes.
- The user says they may need to roll back.

Suggested branch names should be short and descriptive, for example:

```text
zolix-probe
fix-zolix-dll-loading
gui-spectrometer-id
single-spectrum-test
```

## Commit Guidance

Recommend commits after small verified chunks, for example:

```text
git add <files>
git commit -m "记录 Zolix 调试进度交接"
git commit -m "添加 Zolix 最小直连探针脚本"
git commit -m "修复 Zolix DLL 依赖目录加载"
git commit -m "补充 Zolix SDK 错误码日志"
git commit -m "添加光谱仪 S/N 输入项"
```

Keep commits focused. Do not bundle unrelated refactors, generated data, logs, and code changes together.

Prefer Chinese commit messages for An Zhaofeng's projects unless the user explicitly asks for English or the repository already enforces an English-only convention. Commit messages should be detailed enough to explain the concrete change and why it matters, not just a terse generic label.

Good Chinese commit style:

```text
git commit -m "修复 Tkinter 延迟回调访问异常变量导致崩溃"
git commit -m "更新 FROG 调试进度：确认驱动缺失是连接失败根因"
git commit -m "保留硬件初始化错误提示的小修并移除调试性改动"
```

When a change has multiple important parts, use a Chinese subject plus a detailed body:

```text
git commit -m "修复硬件初始化错误提示崩溃" -m "将 except 中的异常先转换为 error_msg，再通过 lambda 默认参数传入 Tkinter after 回调，避免 Python 清理异常变量后触发 NameError。"
```

## Push And Tag Guidance

Recommend `git push` when:

- A milestone is complete.
- A working hardware connection is confirmed.
- A probe script works.
- A GUI path works.
- A long debugging session ends.

Recommend a tag when:

- A previously broken connection now works.
- Single-spectrum acquisition succeeds.
- Full GUI spectrometer connection succeeds.
- A stable version is worth preserving before a risky next step.

Example tags:

```text
zolix-probe-works
zolix-adapter-connects
single-spectrum-works
gui-connects-sgm1700
```

## Rollback Guidance

When the user wants to undo or compare:

- Use `git log --oneline` to find candidates.
- Use `git diff` to inspect local changes.
- Use `git show <commit>:<path>` to inspect an old file.
- Use `git restore --source=<commit> -- <path>` to restore a file from an old commit.
- Use `git revert <commit>` to undo a committed change safely.

Do not use `git reset --hard` or destructive checkout/reset commands unless the user clearly requests that exact operation and understands data loss.

## Progress Handoff Files

When building, modifying, debugging, or maintaining a project, always maintain a progress Markdown document unless the task is truly tiny and one-off. The document is required so a new model, new chat window, or future agent can resume immediately without reconstructing context from scratch.

For long-running projects, keep a progress file updated. Prefer a project-root file with a clear name such as:

```text
FROGTRACE_PROGRESS.md
PROJECT_PROGRESS.md
DEBUG_PROGRESS.md
```

Update it after:

- A new fact is confirmed.
- A new failure mode is found.
- A plan changes.
- A probe or test succeeds.
- A Git checkpoint is created.
- A branch is created, pushed, synced, renamed, or selected as the current working branch.
- The root cause of a previous assumption changes.
- A set of changes is intentionally kept or intentionally discarded.
- The next step becomes clear.

The progress file should include:

- Current goal.
- Current branch, important commit IDs, and whether local/remote are synced.
- Confirmed facts.
- Key file paths.
- Known suspects or failure modes.
- Retained decisions and discarded alternatives.
- Next recommended step.
- Verification checklist.
- Do-not-do-first warnings.

When updating a progress handoff file, put the newest status in a clearly dated section near the end, and if old notes are superseded, explicitly say so instead of deleting useful history.

## GitHub Hygiene

Before recommending GitHub upload, remind the user to avoid uploading:

- Virtual environments.
- `__pycache__`.
- Build outputs.
- Large generated data.
- Sensitive logs.
- Private screenshots.
- Credentials, keys, tokens, serial numbers, or authorization files.
- Vendor installers or proprietary files unless the user has decided it is acceptable.

Prefer `.gitignore` before first commit.

## Interaction Style

- Be proactive but not nagging.
- Keep Git reminders short and actionable.
- If the user is actively coding manually, remind them at checkpoint moments.
- If Codex is making the changes, state the Git checkpoint recommendation in progress updates and final answers.
- When the task is only conceptual and no files are changed, no Git reminder is needed unless version control is directly relevant.
