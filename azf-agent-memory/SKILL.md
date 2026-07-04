---
name: azf-agent-memory
description: >-
  An Zhaofeng's local agent-memory long-term memory workflow. Use at the start of
  existing-project, debugging, continuation, "last time", repository, hardware,
  deployment, or preference-sensitive tasks to recall relevant memory from
  E:\software\Obsidian\agent-memory before inspecting code. Use at task closeout
  to write stable facts, decisions, project state, reusable debugging lessons, or
  next steps back into the memory vault and rebuild its SQLite/Zvec indexes.
  Especially use for FrogTrace and other long-running local E-drive projects. Also
  use when updating agent-memory prompts, workflows, source scripts, or GitHub
  backup rules.
---

# AZF Agent Memory

Use this skill to connect Codex work with An Zhaofeng's local long-term memory
vault. This is not an EverOS HTTP server. It is a local Markdown fact source with
SQLite and optional Zvec semantic indexes.

## Fixed Paths

- Memory root: `E:\software\Obsidian\agent-memory`
- Vault: `E:\software\Obsidian\agent-memory\vault`
- Entry instructions: `E:\software\Obsidian\agent-memory\vault\AGENTS.md`
- Index: `E:\software\Obsidian\agent-memory\vault\INDEX.md`
- Maintenance principles: `E:\software\Obsidian\agent-memory\MAINTENANCE_PRINCIPLES.md`
- Source scripts: `E:\software\Obsidian\agent-memory\source\scripts`
- Environment loader: `E:\software\Obsidian\agent-memory\Load-AgentMemoryEnv.ps1`
- Python: `E:\software\Anaconda\envs\agent-memory\python.exe`
- Basic check: `E:\software\Obsidian\agent-memory\Run-AgentMemoryCheck-Conda.ps1`
- Vector index: `E:\software\Obsidian\agent-memory\Run-AgentMemoryVectorIndex.ps1`

## Naming And Repository Rules

- The project name is `agent-memory`.
- Keep `codex_memory_*`, `CODEX_MEMORY_*`, and `mcncarl/codex-memory` only for
  inherited script/API names, environment variables, or the upstream repository.
- Do not call the whole project `codex-memory`.
- The backup remote is `anzhaohao/agent-memory`.
- The long-term backup branch is `main`.
- `source/` is a normal tracked source directory, not a Git submodule.
- Never create `source-main`, a new source repository, a fork, or a submodule for
  `source/` unless An Zhaofeng explicitly changes this rule.
- Do not use `git clone --recurse-submodules` or `git submodule update` for this
  repository.
- If `.gitmodules` appears, report it before changing repository structure.

## Start-Of-Task Recall

Before working on an existing project, continuing a previous task, debugging, or
answering a user preference/history question:

1. Read `vault\AGENTS.md`.
2. Read `vault\INDEX.md`.
3. Read `MAINTENANCE_PRINCIPLES.md` when the task touches agent-memory itself,
   prompts, scripts, source updates, Git, backup, or onboarding other agents.
4. Search memory with project/task keywords.
5. Read only the most relevant 1-3 Markdown files.
6. Then inspect the target codebase.

PowerShell keyword search:

```powershell
. "E:\software\Obsidian\agent-memory\Load-AgentMemoryEnv.ps1"
Set-Location "E:\software\Obsidian\agent-memory\source"
& "E:\software\Anaconda\envs\agent-memory\python.exe" .\scripts\codex_memory_index.py --search "<query>" --limit 5 --include-open-loops
```

Semantic search for fuzzy memories:

```powershell
. "E:\software\Obsidian\agent-memory\Load-AgentMemoryEnv.ps1"
Set-Location "E:\software\Obsidian\agent-memory\source"
& "E:\software\Anaconda\envs\agent-memory\python.exe" .\scripts\codex_memory_zvec_index.py --search "<natural language query>" --limit 5
```

For FrogTrace, start with queries such as:

```text
FrogTrace frogtrace 调试 硬件 SDK GUI 光谱 连接 失败
```

## During Debugging

- Keep detailed volatile debugging notes in the target project's own handoff
  file, such as `FROGTRACE_PROGRESS.md`, not directly in agent-memory.
- Use agent-memory for stable facts and reusable lessons only.
- Do not write raw terminal dumps, full private chat transcripts, credentials,
  cookies, API keys, serial numbers, or sensitive screenshots into memory.
- When code changes are needed, follow `azf-personal-habits`: inspect git status,
  preserve rollback options, and keep edits focused.

## Closeout Writeback

At the end of meaningful work, decide whether there are stable facts to keep.
Write concise, source-grounded notes into the matching vault area:

- User preference or boundary: `vault\用户记忆\`
- Project state: `vault\项目\`
- Reusable workflow: `vault\工作流\`
- Decision and rationale: `vault\决策\`
- Agent debugging case: `vault\agent\cases\` or `vault\agent\case-candidates\`
- Possible future skill: `vault\agent\skill-candidates\`

Use exactly one YAML frontmatter block at byte 0. Prefer these fields:

```yaml
---
memory_type: project
track: project
project_id: frogtrace
app_id: agent-memory
user_id: azf
agent_id: codex
session_id: ""
status: active
sensitivity: normal
verified_at: 2026-07-01
keywords:
  - FrogTrace
---
```

After writing or changing memory, rebuild and check:

```powershell
powershell -ExecutionPolicy Bypass -File "E:\software\Obsidian\agent-memory\Run-AgentMemoryCheck-Conda.ps1"
powershell -ExecutionPolicy Bypass -File "E:\software\Obsidian\agent-memory\Run-AgentMemoryVectorIndex.ps1"
```

When changing agent-memory prompts, workflow notes, source scripts, or repository
rules, run the closeout entry too:

```powershell
powershell -ExecutionPolicy Bypass -File "E:\software\Obsidian\agent-memory\Run-AgentMemoryCloseout.ps1"
```

## Prompt Maintenance

When asked to update prompts for Claude Code, other local agents, or generic
agentic tools:

1. Keep the prompt path-relative around `MEMORY_ROOT`; do not bake in the local
   E-drive path unless the target is this exact machine.
2. Require the agent to ask for `MEMORY_ROOT` if it was not provided.
3. Require first-round local-only diagnosis for missing dependencies, indexes,
   HF cache, or embedding models.
4. Allow联网下载, dependency installation, or large rebuilds only after the user
   explicitly confirms in a later turn.
5. Include the repository rule: only use `anzhaohao/agent-memory` `main`; no
   `source-main`, no submodule, no extra repo/fork.
6. Tell agents to read `AGENTS.md`, `INDEX.md`, and `MAINTENANCE_PRINCIPLES.md`
   before touching agent-memory itself.

## Git Backup

When the user asks to commit or push agent-memory:

- Show `git status -sb` and `git diff --stat` before committing.
- Commit only files related to the current task.
- Push only `origin main` for `anzhaohao/agent-memory`.
- Do not create PRs, branches, submodules, forks, or new GitHub repositories
  unless the user explicitly asks for that exact action.

## Importing Old Codex Chats

Previous Codex conversations may exist under `C:\Users\anzhaofeng\.codex`, for
example `sessions`, `archived_sessions`, `session_index.jsonl`, or SQLite logs.
When the user asks to maintain memory from old chats:

1. Search only for relevant thread names, keywords, or project names first.
2. Prefer project-specific terms such as `FrogTrace`, repository path, hardware
   names, error messages, or filenames.
3. Summarize stable facts, decisions, root causes, and next steps.
4. Do not import full transcripts verbatim.
5. Ask before broad bulk import, because old chats may contain private or stale
   information.
6. Mark unverified imported facts as `status: draft` or put them in
   `agent\case-candidates\` until confirmed.

Old chat import is a curation task, not a blind migration.
