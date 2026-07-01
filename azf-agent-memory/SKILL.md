---
name: azf-agent-memory
description: >-
  An Zhaofeng's local Codex long-term memory workflow. Use at the start of
  existing-project, debugging, continuation, "last time", repository, hardware,
  deployment, or preference-sensitive tasks to recall relevant memory from
  E:\software\Obsidian\agent-memory before inspecting code. Use at task closeout
  to write stable facts, decisions, project state, reusable debugging lessons, or
  next steps back into the memory vault and rebuild its SQLite/Zvec indexes.
  Especially use for FrogTrace and other long-running local E-drive projects.
---

# AZF Agent Memory

Use this skill to connect Codex work with An Zhaofeng's local long-term memory
vault. This is not an EverOS HTTP server. It is a local Markdown fact source with
SQLite and optional Zvec semantic indexes.

## Fixed Paths

- Memory root: `E:\software\Obsidian\agent-memory`
- Vault: `E:\software\Obsidian\agent-memory\vault`
- Entry instructions: `E:\software\Obsidian\agent-memory\vault\AGENTS.md`
- Source scripts: `E:\software\Obsidian\agent-memory\source\scripts`
- Environment loader: `E:\software\Obsidian\agent-memory\Load-AgentMemoryEnv.ps1`
- Python: `E:\software\Anaconda\envs\agent-memory\python.exe`
- Basic check: `E:\software\Obsidian\agent-memory\Run-AgentMemoryCheck-Conda.ps1`
- Vector index: `E:\software\Obsidian\agent-memory\Run-AgentMemoryVectorIndex.ps1`

## Start-Of-Task Recall

Before working on an existing project, continuing a previous task, debugging, or
answering a user preference/history question:

1. Read `vault\AGENTS.md`.
2. Read `vault\INDEX.md`.
3. Search memory with project/task keywords.
4. Read only the most relevant 1-3 Markdown files.
5. Then inspect the target codebase.

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
