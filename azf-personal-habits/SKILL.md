---
name: azf-personal-habits
description: >-
  An Zhaofeng's global personal working habits for any intelligent agent. Use at the start of tasks for An Zhaofeng, especially programming, writing Markdown documents, project planning, debugging, research workflows, long-running handoffs, Git/GitHub version control, rollback-sensitive changes, or any task where personal preferences affect execution. Prioritize these habits: proactive Git branch/commit/push/tag/rollback reminders during coding, progress handoff files for multi-step projects, concise checkpointing, and no duplicate title inside Markdown document body content when creating .md files.
---

# AZF Personal Habits

Use this skill as An Zhaofeng's global personal preference layer. Treat it as a standing collaboration habit: protect rollback ability, keep work recoverable, leave a clean handoff trail, and follow document-format preferences.

## Core Rules

- Prefer reading this skill first when a task is for An Zhaofeng and personal workflow preferences may matter.
- Be proactive, but keep reminders concise and timed to natural checkpoints.
- For multi-step work, keep a visible next-step trail so a new chat/model can resume quickly.
- When creating Markdown documents, do not write the document title again inside the body content unless the user explicitly asks for an in-document heading.
- Before substantial code edits, inspect repository state with `git status` when inside a Git repo.
- If the workspace is not a Git repo and the user is starting meaningful coding work, recommend initializing Git before edits.
- Before risky or broad changes, remind the user to create a branch.
- After each small completed milestone, remind the user to make a local commit.
- At important checkpoints, remind the user to push to GitHub.
- At confirmed success points, remind the user to create a Git tag.
- If a change goes wrong, prefer safe rollback commands such as `git restore --source=<commit> -- <file>` or `git revert <commit>`; avoid destructive reset unless the user explicitly asks.
- Maintain or update a progress handoff file for multi-step projects so a new chat/model can resume quickly.

## Markdown Document Habit

When creating a `.md` document file for the user:

- Do not duplicate the document title as a first `# ...` heading in the body by default.
- Let the filename, Obsidian note title, or surrounding context carry the title.
- Start the body directly with the substantive content, metadata block, summary, or first necessary section.
- Add a body title only when the user explicitly requests it, the template requires it, or the document would be ambiguous without it.

Example preferred body start:

```markdown
---
created: 2026-05-28
tags:
  - frogtrace
---

## 背景

...
```

Avoid this unless requested:

```markdown
# FrogTrace 调试记录

## 背景

...
```

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
