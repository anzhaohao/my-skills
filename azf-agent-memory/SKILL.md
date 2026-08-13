---
name: azf-agent-memory
description: >-
  An Zhaofeng's local agent-memory workflow for Codex, Claude Code, Harness ZCode,
  and other local agent harnesses. Use at the start of existing-project,
  debugging, continuation, "last time", repository, hardware, deployment, or
  preference-sensitive tasks to recall relevant memory from
  E:\software\Obsidian\agent-memory before inspecting code. Use at task closeout
  to write stable facts, decisions, project state, reusable debugging lessons, or
  next steps back into the memory vault and rebuild its SQLite/Zvec indexes.
  Especially use for FrogTrace and other long-running local E-drive projects. Also
  use when updating agent-memory prompts, workflows, source scripts, or GitHub
  backup rules.
---

# AZF Agent Memory

Use this skill to connect Agent work with An Zhaofeng's local long-term memory
vault. This is not an EverOS HTTP server. It is a local Markdown fact source with
SQLite and optional Zvec semantic indexes.

## Path Convention

All paths are based on `MEMORY_ROOT = E:\software\Obsidian\agent-memory`. This
skill is pinned to this exact machine; for portable prompts use variable-based
paths.

```text
MEMORY_ROOT = E:\software\Obsidian\agent-memory
VAULT       = MEMORY_ROOT\vault
AGENTS      = MEMORY_ROOT\vault\AGENTS.md
INDEX       = MEMORY_ROOT\vault\INDEX.md
SOURCE      = MEMORY_ROOT\source
SCRIPTS     = MEMORY_ROOT\source\scripts
MEMORYCTL   = MEMORY_ROOT\source\scripts\memoryctl
ENV_LOADER  = MEMORY_ROOT\Load-AgentMemoryEnv.ps1
CHECK       = MEMORY_ROOT\Run-AgentMemoryCheck-Conda.ps1
VECTOR      = MEMORY_ROOT\Run-AgentMemoryVectorIndex.ps1
CLOSEOUT    = MEMORY_ROOT\Run-AgentMemoryCloseout.ps1
AUDIT       = MEMORY_ROOT\Run-AgentMemoryAudit.ps1
DOCTOR      = MEMORY_ROOT\source\scripts\agent_memory_doctor.py
MAINTENANCE = MEMORY_ROOT\MAINTENANCE_PRINCIPLES.md
PYTHON      = E:\software\Anaconda\envs\agent-memory\python.exe
```

The locally integrated upstream snapshot is
`mcncarl/agent-memory-vault@3c30a684e433eb8c6842cfa6bd60473e3edea1b7`
(verified 2026-08-12). It includes the five-stage memory safety protocol,
canonical `retrieve`, write intents and immutable receipts, and native Windows
runtime support. Do not reapply superseded local locking or path patches merely
because they existed before this snapshot.

## Naming And Repository Rules

- The project name is `agent-memory`.
- Use `agent_memory_*`, `AGENT_MEMORY_*`, and `memoryctl` for current runtime
  commands. The current upstream is `mcncarl/agent-memory-vault`; keep
  `mcncarl/codex-memory` and old `codex_memory_*` names only inside historical
  records or migration backgrounds.
- Do not call the whole project `codex-memory`.
- The backup remote is `anzhaohao/agent-memory`.
- The long-term backup branch is `main`.
- `source/` is a normal tracked source directory, not a Git submodule.
- Never create `source-main`, a new source repository, a fork, or a submodule for
  `source/` unless An Zhaofeng explicitly changes this rule.
- Do not use `git clone --recurse-submodules` or `git submodule update` for this
  repository.
- If `.gitmodules` appears, report it before changing repository structure.

## First-Round Local-Only Policy

This is a local-first system. The environment loader sets offline mode:

- `HF_HUB_OFFLINE=1`
- `TRANSFORMERS_OFFLINE=1`
- `HF_HUB_CACHE=MEMORY_ROOT\runtime\hf-cache\hub`

If any dependency, model, cache, index, or permission is missing:

1. **Stop** and report:
   - What is missing
   - What still works (keyword search, etc.)
   - Whether closeout / semantic search / indexing is affected
   - Suggested fix command
2. **Do not** auto-download, install, or rebuild.
3. Only after An Zhaofeng explicitly confirms ("确认下载 / 确认联网 / 确认重建 /
   继续修复"), proceed with the fix in the next turn.

This applies to: pip packages, Hugging Face models, zvec rebuilds, lock file
removal, cache clearing, and large-scale index regeneration.

## Start-Of-Task Recall

Before working on an existing project, continuing a previous task, debugging, or
answering a user preference/history question:

1. Read `vault\AGENTS.md`.
2. Read `vault\INDEX.md`.
3. Read `MAINTENANCE_PRINCIPLES.md` when the task touches agent-memory itself,
   prompts, scripts, source updates, Git, backup, or onboarding other agents.
4. Use `memoryctl retrieve` for host-facing recall. It generates candidates from
   SQLite/Zvec, then reopens current Markdown and reapplies containment, scope,
   status, UTF-8, sensitivity, and byte-budget checks.
5. Use raw keyword or Zvec search only for diagnosis or candidate inspection;
   search indexes are not truth or authorization sources.
6. Read only the most relevant 1-3 current Markdown files.
7. Then inspect the target codebase.

PowerShell safe retrieval:

```powershell
. "E:\software\Obsidian\agent-memory\Load-AgentMemoryEnv.ps1"
Set-Location "E:\software\Obsidian\agent-memory\source"
& $env:AGENT_MEMORY_PYTHON .\scripts\memoryctl --actor codex retrieve "<query>" --max-results 5 --json
```

Diagnostic raw keyword search:

```powershell
& $env:AGENT_MEMORY_PYTHON .\scripts\memoryctl --actor codex search "<query>" --limit 5 --include-open-loops
```

Diagnostic semantic search (only when local zvec is confirmed available):

```powershell
. "E:\software\Obsidian\agent-memory\Load-AgentMemoryEnv.ps1"
Set-Location "E:\software\Obsidian\agent-memory\source"
& $env:AGENT_MEMORY_PYTHON .\scripts\agent_memory_zvec_index.py --search "<natural language query>" --limit 5
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

At the end of meaningful work, decide whether there are stable facts to keep. Do
not skip closeout by default.

### 1. Prewrite Reconcile

Before writing anything, run `memoryctl prewrite` to classify the evidence and
check whether similar facts already exist. Source classification is mandatory in
the new safety protocol; `SOURCE_UNKNOWN` must fail closed:

```powershell
. "E:\software\Obsidian\agent-memory\Load-AgentMemoryEnv.ps1"
Set-Location "E:\software\Obsidian\agent-memory\source"
& $env:AGENT_MEMORY_PYTHON .\scripts\memoryctl `
  --actor codex `
  prewrite "<stable fact summary to write>" `
  --source-class local_verified `
  --knowledge-kind fact `
  --asserted-by codex `
  --evidence-ref "<local file, Git commit, test result, or current conversation>" `
  --json
```

Choose the truthful source class: `user_direct` for an explicit user statement,
`local_verified` for locally inspected evidence, `agent_inferred` for an
inference, and `external_untrusted` for unverified external material. Do not
upgrade an inference or external claim to a verified fact.

Possible results (automatically returned by prewrite):

| Result | Action |
|--------|--------|
| `ADD` | Create new memory file |
| `UPDATE` | Edit the existing file |
| `NOOP` | Skip — already recorded |
| `MERGE_REQUIRED` | Stop and explain the conflict to An Zhaofeng |
| `ASK_USER` | Stop and ask An Zhaofeng for a decision |

`MARK_OUTDATED` is an allowed manual decision (listed in `allowed_actions`) but
is not automatically returned by the prewrite recommendation function. Use it
explicitly when you determine an old fact has been superseded.

Never skip prewrite and create files based on filename guesses alone.

### 2. Claim Files (Collaborative Declaration)

Before editing any existing shared memory file, declare intent by claiming it
for the current session:

```powershell
& $env:AGENT_MEMORY_PYTHON .\scripts\memoryctl `
  --actor codex `
  claim `
  --session-id "<current session ID>" `
  --file "<absolute path to Markdown in vault>"
```

Claim is a collaborative declaration, not a file lock. The primary key is
`(session_hash, path)`, so multiple sessions can claim the same file
concurrently with different session hashes. There is no cross-session mutual
exclusion. Use claims to signal intent and help other sessions discover active
work on a file, but do not rely on them to prevent concurrent edits.

New files created after a successful `ADD` prewrite result should be claimed
immediately.

The session ID can be obtained from `AGENT_MEMORY_SESSION_ID`, `CODEX_THREAD_ID`,
or the Claude session bridge. Do not forge or reuse a fixed session ID.

Claims older than 24 hours are treated as abandoned. Preview them first; only
use `--apply` after confirming they are stale:

```powershell
& $env:AGENT_MEMORY_PYTHON .\scripts\memoryctl --actor human claims-expire --older-than-hours 24
& $env:AGENT_MEMORY_PYTHON .\scripts\memoryctl --actor human claims-expire --older-than-hours 24 --apply
```

### 3. Write Memory

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
agent_scope: shared
session_id: ""
status: active
sensitivity: normal
verified_at: 2026-07-01
keywords:
  - FrogTrace
---
```

Use `agent_scope: shared` for general cross-agent facts. Use `codex` or `claude`
only when the fact depends on a specific host environment.

The five-stage safety sequence is: source gate → reconcile → intent/approval when
required → apply with current-content checks → immutable receipt/outcome. Normal
Codex, Claude Code, and ZCode sessions may edit ordinary Markdown only after
prewrite and claim. Protected-path or host-application writes must use the
content-bound two-phase intent flow. `memoryctl write` is currently restricted to
the `yichen-content-studio` adapter; do not call it as another actor or bypass its
stdin/session rules.

### 4. Run Unified Closeout

After writing or changing memory files, run a dry-run first, review the claimed
scope, then run the unified closeout. It refreshes SQLite/Zvec, runs checks, and
writes closeout logs:

```powershell
powershell -ExecutionPolicy Bypass -File "E:\software\Obsidian\agent-memory\Run-AgentMemoryCloseout.ps1" `
  -Actor codex `
  -SessionId "<current session ID>" `
  -DryRun

powershell -ExecutionPolicy Bypass -File "E:\software\Obsidian\agent-memory\Run-AgentMemoryCloseout.ps1" `
  -Actor codex `
  -SessionId "<current session ID>"
```

The outer wrapper automatically adds `--claimed-only` whenever a real session ID
is supplied. The closeout then processes files claimed by that session, excludes
files owned by other sessions, and fails closed on unclaimed memory changes. A
no-op is successful when the session has nothing to process. Still inspect
`git status` because unrelated user changes must never be folded into this task.

The script does **not** commit to Git unless `-Commit` is explicitly passed.
Only add `-Commit` after An Zhaofeng confirms the scope of changes.

## Zvec / Embedding Troubleshooting

If zvec semantic search fails, returns stale results, or keyword search can find
results that semantic search cannot, check in this exact order:

1. Has `Load-AgentMemoryEnv.ps1` been sourced?
2. Are offline flags set?
   - `HF_HUB_OFFLINE=1`
   - `TRANSFORMERS_OFFLINE=1`
3. Does `HF_HUB_CACHE` point to `MEMORY_ROOT\runtime\hf-cache\hub` (not the
   user home directory's incomplete cache)?
4. Is the embedding model cache complete? Check for weight files, tokenizer, and
   sentence-transformers modules under the snapshot path.
5. Does zvec have lock, permission, or index errors?
6. Is the target memory file's frontmatter `status` excluded? Files with
   `status: draft`, `archived`, or `deleted` are excluded from zvec.
7. Run Doctor to check SQLite/Zvec parity.

If the target file is `status: draft`, `archived`, or `deleted`, do not change
it to `active` without permission. Explain why it was excluded, whether keyword
search is still available, and the basis and risk of changing its status. Wait
for confirmation before touching that single file.

If the local model or dependency is actually missing, stop and report
suggestions. Do not download in the first round.

## Infrastructure Check

### Doctor v2.2 (Read-Only)

Doctor checks: SQLite integrity, Markdown-SQLite parity, FTS coverage, Zvec
parity, session claim hygiene, remote backup freshness, semantic Python
interpreter, model/dependency evidence, offline semantic query, and automation
freshness.

```powershell
. "E:\software\Obsidian\agent-memory\Load-AgentMemoryEnv.ps1"
Set-Location "E:\software\Obsidian\agent-memory\source"
& $env:AGENT_MEMORY_PYTHON .\scripts\agent_memory_doctor.py
```

Doctor v2.2 is read-only by default. It will report stale claims and parity gaps
but not modify anything.

### Audit (Runs Doctor as Sidecar)

```powershell
powershell -ExecutionPolicy Bypass -File "E:\software\Obsidian\agent-memory\Run-AgentMemoryAudit.ps1"
```

Audit runs Doctor as a sidecar check. Content audit success is recorded even if
Doctor produces warnings (Doctor failure does not erase a good audit timestamp).

### Repair Derived Indexes

`--repair-derived` rebuilds reproducible indexes (SQLite FTS, zvec) but requires
the configured semantic Python. Explain the scope before running:

```powershell
& $env:AGENT_MEMORY_PYTHON .\scripts\agent_memory_doctor.py --repair-derived
```

### Vector Index Rebuild

```powershell
. "E:\software\Obsidian\agent-memory\Load-AgentMemoryEnv.ps1"
powershell -ExecutionPolicy Bypass -File "E:\software\Obsidian\agent-memory\Run-AgentMemoryVectorIndex.ps1"
```

Only run when local dependencies and embedding model are fully cached. If
anything is missing, follow the first-round local-only policy.

## Prompt Maintenance

When asked to update prompts for Claude Code, other local agents, or generic
agentic tools:

1. Keep the prompt path-relative around `MEMORY_ROOT`; do not bake in the local
   E-drive path unless the target is this exact machine.
2. Require the agent to ask for `MEMORY_ROOT` if it was not provided.
3. Require first-round local-only diagnosis for missing dependencies, indexes,
   HF cache, or embedding models.
4. Allow network downloads, dependency installation, or large rebuilds only
   after An Zhaofeng explicitly confirms in a later turn.
5. Include the repository rule: only use `anzhaohao/agent-memory` `main`; no
   `source-main`, no submodule, no extra repo/fork.
6. Tell agents to read `AGENTS.md`, `INDEX.md`, and `MAINTENANCE_PRINCIPLES.md`
   before touching agent-memory itself.

## Harness Adapters

Keep one canonical skill at
`C:\Users\anzhaofeng\.skills-manager\skills\azf-agent-memory\SKILL.md`. Harness
adapters must be thin bootstraps; never copy the full skill into each harness.

- Claude Code discovers the Skills Manager through `~\.claude\skills` and reads
  broad defaults from `~\.claude\CLAUDE.md`.
- Harness ZCode discovers `~\.zcode\skills` before `~\.agents\skills`, and reads
  user defaults from `~\.zcode\AGENTS.md`.
- On this machine those skill roots are junctions to the same Skills Manager.
  Preserve them and check for shadowing before creating any duplicate.
- A new harness adapter should only identify the canonical skill, point to
  `vault\AGENTS.md`, explain when recall/closeout applies, and state how a real
  session identity is obtained.
- If a harness exposes no stable real session ID, recall may remain read-only,
  but claim/write/closeout must pause until a truthful session bridge exists. Do
  not forge a fixed ID or reuse another harness's session ID.

## Git Backup

When An Zhaofeng asks to commit or push agent-memory:

- Show `git status -sb` and `git diff --stat` before committing.
- Commit only files related to the current task.
- Push only `origin main` for `anzhaohao/agent-memory`.
- Do not create PRs, branches, submodules, forks, or new GitHub repositories
  unless An Zhaofeng explicitly asks for that exact action.

Standard flow:

```powershell
Set-Location E:\software\Obsidian\agent-memory
git status -sb
git diff --stat
git add <this-round related files>
git commit -m "<clear commit message>"
git push origin main
```

## Importing Old Codex Chats

Previous Codex conversations may exist under `C:\Users\anzhaofeng\.codex`, for
example `sessions`, `archived_sessions`, `session_index.jsonl`, or SQLite logs.
When asked to find, inspect, summarize, or maintain memory from old chats, prefer
AgentsView first if it is deployed locally.

AgentsView lightweight probe:

```powershell
try {
  Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8080" -TimeoutSec 1 | Out-Null
  $true
} catch {
  $false
}
```

AgentsView is a raw conversation evidence layer, not a source of truth. Extract
only stable facts, decisions, root causes, and next steps from old sessions.
Reconcile them against `vault\INDEX.md`, SQLite/FTS, and Zvec before writing
formal memory. Mark unverified imported facts as `status: draft` or place them in
`agent\case-candidates\` until confirmed.

Old chat import is a curation task, not a blind migration.
