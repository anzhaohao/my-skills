---
name: azf-auto-dev-loop
description: >-
  Cost-aware autonomous development loop for local code repositories: route
  bounded Work Items through Claude Code + DS v4 Flash, Luna, Terra, DS v4 Pro,
  and Sol; independently verify the real diff and tests; and perform bounded
  automatic rework. Use for local feature development, bug fixes, refactors,
  tests, performance work, technical-debt cleanup, and code review with repair.
---

# AZF Auto Dev Loop

Use this Skill when the user asks to change, debug, refactor, optimize, test,
or review a local code repository. Keep the task contract Harness-agnostic,
while allowing the controller to choose native Codex or the Claude Code adapter.
ZCode, Kandev, or another CLI remains optional and must not become a hard
dependency.

## Default policy

Use the following policy unless the user explicitly overrides it:

```yaml
planner: auto
planner_model: adaptive
executor: auto
default_executor_pool:
  claude_code_ds_v4_flash: 0.60
  azf_luna_executor: 0.40
evaluator: auto
default_evaluator: azf_terra_evaluator
max_rework_rounds: 4
permission_mode: full-trust
constraint_mode: prompt-and-audit
commit_push: forbidden
```

Deterministic preflight does not call a model for clear, low-risk work. It uses
Claude Code + DS v4 Flash with 60% probability and Luna with 40% probability.
Use Terra Planner for medium ambiguity or cross-module planning, and Sol Planner
only for high risk, fundamental ambiguity, or explicit `planner_mode=always`.

The fixed reasoning baseline is:

```yaml
sol_planner: high
terra_planner: high
luna_executor: medium
terra_executor: high
ds_v4_pro_executor: high
sol_executor: high
terra_evaluator: high
sol_evaluator: high
```

Capability order for execution is:

```text
DS v4 Flash ≈ Luna < Terra < DS v4 Pro < Sol
```

Use a same-tier targeted retry first, then upgrade to Terra, DS v4 Pro, and Sol
in that order. Do not use a single global complexity score to force Sol on
ordinary work.

## Modes

- `auto` or `balanced`: deterministic planning when possible, DS Flash/Luna
  cheap execution pool, bounded escalation and Terra evaluation.
- `reviewed`: produce the plan and route, then stop before editing until the
  user confirms.
- `dry-run`: inspect, score, route, and report only; never edit.
- `profile=economy`: keep the DS Flash/Luna cheap pool, use Terra for ordinary
  verification, and reserve Sol for hard-risk overrides.
- `profile=quality`: use Sol for execution and evaluation.
- `task_profile=generic`: use the normal repository workflow.
- `task_profile=experiment-record`: prefer deterministic incremental evidence
  extraction before model reading; delegate Vault structure to the experiment
  and Obsidian project Skills.
- `task_profile=html-ui`: delegate isolated visual variants, Playwright
  screenshots, and user selection to `azf-html-ui-loop`.
- `planner_mode=auto|always|never`: `never` is allowed only for low-risk work;
  unsafe attempts return `BLOCKED` instead of silently proceeding.
- `harness=claude-code`: automatically start the Claude Code adapter in
  non-interactive mode. The adapter resolves the requested model and effort and
  records both requested and resolved values.
- `harness=deepseek`: run the whole chain on DeepSeek only. Planner and Evaluator
  use DS v4 Pro; the Executor starts on DS v4 Flash and escalates to DS v4 Pro
  after a same-tier retry (never Sol/GPT unless the Harness is explicitly
  switched back to `codex`). Reasoning effort is auto-resolved per stage: Flash
  low/medium, Pro high, Planner medium (Sol tier) / high, Evaluator high.
- `executor=luna|terra|sol`: explicitly pin the Executor. Never silently
  replace an explicitly pinned model.

External Harness profiles are optional adapters, not Skill dependencies:

```text
claude-ds-v4-flash
claude-ds-v4-pro
claude-ds-flash (legacy alias)
claude-ds-pro-hybrid (legacy alias)
claude-ds-pro-all (legacy alias)
```

For the runtime record and external-model safety rules, read
`references/external-harness.md` only when an external Harness is selected.

For deterministic CLI orchestration, use the bundled controller:

```powershell
$codexHome = if ([string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
  Join-Path $HOME '.codex'
} else {
  $env:CODEX_HOME
}
$controller = Join-Path $codexHome 'skills\azf-auto-dev-loop\scripts\azf-auto-dev-loop.ps1'
powershell -NoProfile -ExecutionPolicy Bypass -File `
  $controller `
  -Task "修复当前项目的保存失败问题" -RepoPath (Get-Location).Path
```

Use `-Mode reviewed -Approve` when you want a human gate before editing. Use
`-Mode dry-run` to validate routing without any write. Normal Claude Code routes
do not pause for confirmation.

When the Codex CLI is API-key authenticated, the controller disables plugin
initialization for its isolated stage calls. This prevents the CLI from
trying to access ChatGPT-session-only remote plugin catalogs; local Skills
under the configured Skill root remain available. Non-fatal stderr diagnostics
are retained in the run evidence and are not treated as a failed stage unless
the CLI exit code or required structured output fails.

The controller also disables Codex's internal multi-agent fan-out for each
stage. Planner, Executor, and Evaluator are already separate, auditable stages;
an extra nested delegation would add latency and make the structured handoff
non-deterministic.

## Mandatory workflow

1. Read the user's request, project instructions, `AGENTS.md`, and relevant
   repository documentation.
2. Confirm the target is a Git repository and record branch, HEAD,
   `git status --short`, tracked/untracked files, and the pre-existing diff.
3. Protect all pre-existing uncommitted work. Never clean, reset, or revert it.
4. Run deterministic preflight. If `planner_mode=auto` and the task is clear,
   repetitive, and low-risk, create a structured plan without a model call. Use
   `azf_terra_planner` for medium planning complexity and `azf_sol_planner` only
   for high-risk, fundamental ambiguity, or explicit `planner_mode=always`.
5. Require a structured plan containing the five-dimension score, risk level,
   selected Executor/Evaluator, typed atomic `work_items`, files, tests, and
   acceptance criteria.
6. Before editing, write and verify a route record containing Harness, requested
   and resolved model, requested and resolved effort, approval state, and
   baseline hash. Any route drift is `BLOCKED`.
7. In `reviewed` or `dry-run`, stop at the appropriate boundary.
8. Start exactly one write-capable Executor with full-trust permissions. Never
   run two write agents against the same worktree concurrently. Use prompt
   constraints and before/after audit; full-trust is not a sandbox.
9. Require the Executor to inspect the baseline, make the smallest scoped
   change, run relevant checks, and report evidence. Forbid `git add`, commit,
   push, PR creation, destructive Git commands, and unrelated deletion.
10. Start a fresh read-only Evaluator. It must inspect the actual files, diff,
    tests, and session evidence rather than trusting the Executor summary.
11. Return `PASS` only when every acceptance criterion is verified. Return
    `REWORK` with concrete files, evidence, and repair requirements otherwise.
12. For automatic routing, use the following capability order:
    `DS v4 Flash/Luna → Terra → DS v4 Pro → Sol`. Retry the same cheap executor
    once with the current Work Item, then upgrade. Re-plan when the Evaluator
    marks the plan fundamentally wrong. Allow at most four rework rounds.
13. Write run evidence outside the repository by default, including route,
    baseline, plan, execution, evaluation, stage logs, and usage fields.
14. If Claude Code is selected, start it automatically through the bundled
    adapter. Record `requested_model`, `resolved_model`, `requested_effort`,
    `resolved_effort`, `harness`, `permission_mode`, and `route_reason`.

## Full-DeepSeek chain (`harness=deepseek`)

When the user selects `-Harness deepseek` (or the request is framed as
"Claude Code + DeepSeek" / "DSH + DeepSeek" and asks to stay on DeepSeek), the
controller keeps the entire loop on DeepSeek instead of mixing Codex GPT tiers:

```text
Planner  -> DS v4 Pro  (effort medium, or high on Sol-tier planning)
Executor -> DS v4 Flash (effort low/medium), retry once, then DS v4 Pro (effort high)
Evaluator-> DS v4 Pro  (effort high)
```

The Executor never escalates to Terra/Sol/GPT in this mode. The only way to
reach GPT tiers is to switch `-Harness` back to `codex` explicitly. This is the
default cost-saving configuration for a Claude Code or DSH session wired to
DeepSeek.

## Routing rubric

Score each dimension from 0 to 2:

1. requirement ambiguity;
2. change breadth and cross-module impact;
3. technical risk and blast radius;
4. debugging/reasoning depth;
5. verification complexity.

Use this route unless a high-risk override applies:

| Score | Initial Executor | Evaluator |
|---:|---|---|
| 0–5, low/medium risk | DS v4 Flash (60%) or Luna (40%) | Terra |
| 6–7 | Terra | Terra |
| 8–10 or hard-risk override | Sol | Sol |

Always route authentication, authorization, security, migrations,
concurrency, transactions, public API compatibility, core architecture,
high-impact deployment, irreversible changes, or large unexplained failures to
Sol.

Claude Code is a first-class executor Harness in this Skill, not a proposal-only
route. Historical `cost_per_pass` can adjust routing only after at least 20
comparable tasks per route; new task classes use the 60/40 default and do not
pretend to know their future cost.

## Evidence and cost telemetry

For every stage record:

```yaml
stage: planner | executor | evaluator
harness:
requested_model:
resolved_model:
requested_effort:
resolved_effort:
input_tokens:
cached_input_tokens:
cache_write_tokens:
output_tokens:
retry_count:
elapsed_seconds:
estimated_cost:
approval_status:
permission_mode:
route_reason:
failure_class:
cost_per_pass:
```

Keep stable instructions, tools, schemas, and shared context before changing
task-specific content. Read provider usage fields when available:
`cached_tokens`/`cache_write_tokens` for Codex-compatible providers and
`prompt_cache_hit_tokens`/`prompt_cache_miss_tokens` for DeepSeek-compatible
providers. Do not claim a saving from theoretical cache discounts; calculate
`cost_per_success` from actual usage and final PASS counts.

## Final report

Report:

- `PASS`, `REWORK`, or `BLOCKED`;
- complexity score and selected route;
- requested and resolved models plus Harness/Profile;
- modified files and pre-existing changes preserved;
- commands and test results;
- independent Evaluator verdict;
- retry/upgrade count and available cache telemetry;
- task profile, planner invocation decision, and approval status;
- unverified items and remaining risks;
- explicit statement that no commit or push was performed.

Always include a standalone `模型调用链条` section in the user-facing final
response. Build it only from the run's route, resolution, and agent-event
evidence, and list every Planner, Executor, Evaluator, retry, and upgrade in
actual chronological order. For each stage, report the Harness,
`requested_model`, `resolved_model`, `requested_effort`, and
`resolved_effort`. Mark any skipped Planner or Evaluator as `skipped` or
`not_invoked`; when no additional model was called, explicitly state
`无额外模型调用`. Use `unverified` for values the runtime did not verify. This
section exposes auditable routing metadata only and must never claim to reveal
hidden chain-of-thought.

For schema and deterministic execution details, read the bundled files
`schemas/plan.schema.json`, `schemas/execution.schema.json`,
`schemas/evaluation.schema.json`, and `scripts/azf-auto-dev-loop.ps1`.
