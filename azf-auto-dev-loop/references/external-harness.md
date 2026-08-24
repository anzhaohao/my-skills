# Claude Code adapter policy

This reference documents the first-class Claude Code adapter. The controller may
launch it automatically for the cheap execution pool; it records requested and
resolved model/effort values and preserves the user's baseline evidence.

## Named profiles

```yaml
claude-ds-v4-flash:
  primary: deepseek-v4-flash
  role: ordinary bounded execution

claude-ds-v4-pro:
  primary: deepseek-v4-pro
  role: upgraded complex execution after Terra

legacy_aliases:
  claude-ds-flash: claude-ds-v4-flash
  claude-ds-pro-hybrid: claude-ds-v4-pro
  claude-ds-pro-all: claude-ds-v4-pro
```

Provider aliases and actual model IDs can change. Before claiming success, verify
the model reported by Claude Code. Never infer Pro from a profile name alone, and
never accept a silent fallback to Flash.

## Runtime record

Each route and stage must include:

```yaml
run_id:
route_stage:
route_reason:
repo_head:
git_status_hash:
harness: claude-code
profile:
requested_model:
resolved_model:
requested_effort:
resolved_effort:
permission_mode: full-trust
max_rework_rounds:
user_billed_cost:
provider_equivalent_cost:
```

Normal execution does not wait for confirmation. A hard blocker (missing CLI,
authentication failure, unresolved model, or an out-of-scope external effect)
returns `BLOCKED` with evidence. Full-trust is a requested execution mode, not a
preventive sandbox; prompt constraints and before/after audit remain mandatory.

## Full-DeepSeek harness (`harness=deepseek`)

`harness=deepseek` is a full-DS chain distinct from the mixed `claude-code`
adapter. It keeps Planner, Executor, and Evaluator all on DeepSeek, so a Claude
Code or DSH session wired to DeepSeek never falls back to Codex GPT tiers.

```yaml
planner:
  model: deepseek-v4-pro
  effort: medium          # high when the planning tier is Sol
executor:
  model: deepseek-v4-flash  # low/medium effort
  upgrade_after_retry: deepseek-v4-pro  # high effort
evaluator:
  model: deepseek-v4-pro
  effort: high
```

The Executor escalation chain in this mode is `DS v4 Flash → DS v4 Flash retry
→ DS v4 Pro`. It does not upgrade to Terra or Sol. GPT tiers are reachable only
by switching `-Harness` back to `codex`.

## Cost and upgrade policy

For a new task class, use the configured DS Flash/Luna 60/40 default. Only after
at least 20 comparable tasks per route should historical `cost_per_pass` and
PASS-rate tolerance adjust the default. The execution capability order is:

```text
DS v4 Flash ≈ Luna < Terra < DS v4 Pro < Sol
```

DS v4 Pro is an automatic execution upgrade after Terra, not a proposal-only
route. Record all retries, evaluator calls, cache usage, and failures in the
final cost calculation.

Do not place API keys, cookies, tokens, or private Harness configuration in this
reference or in a Skill README.
