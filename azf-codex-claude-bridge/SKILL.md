---
name: azf-codex-claude-bridge
description: An Zhaofeng's Codex-to-Claude bridge workflow. Use when the user asks Codex to call Claude, ask Claude for a second opinion, have Claude review a diff, run a Claude adversarial review, compare Codex and Claude judgments, or use Claude Code CLI from inside Codex. Defaults to read-only Claude consultation through the local `claude -p` CLI, with Codex retaining implementation control.
---

# AZF Codex Claude Bridge

Use this skill to consult the local Claude Code CLI from a Codex session while keeping the workflow controlled and recoverable.

## Core Rule

Treat Claude as a read-only reviewer or second-opinion agent by default. Codex remains responsible for deciding what to do, explaining tradeoffs, and making any edits after normal confirmation rules.

Do not let Claude modify files unless An Zhaofeng explicitly asks for a Claude-driven implementation flow in the current turn.

## Before Calling Claude

1. Confirm the local CLI exists when the session has not already verified it:

```powershell
claude --version
```

2. Decide the smallest context to send:
   - Current working diff: use `git diff`.
   - Staged changes: use `git diff --staged`.
   - Branch comparison: use `git diff <base>...HEAD`.
   - Architecture or plan review: send the plan text directly.
   - Project-level review: use `--add-dir .` only when Claude needs repository file access.

3. Never send secrets, API keys, cookies, private credentials, or private logs. If the context may include secrets, inspect or summarize it first.

## Preferred Script

Use the bundled PowerShell wrapper for repeatable calls on Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\anzhaofeng\.skills-manager\skills\azf-codex-claude-bridge\scripts\invoke-claude.ps1" -Mode diff-review
```

Common modes:

```powershell
# Review current unstaged + staged working diff through git diff HEAD
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\anzhaofeng\.skills-manager\skills\azf-codex-claude-bridge\scripts\invoke-claude.ps1" -Mode diff-review

# Review staged diff only
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\anzhaofeng\.skills-manager\skills\azf-codex-claude-bridge\scripts\invoke-claude.ps1" -Mode staged-review

# Ask a direct second-opinion question
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\anzhaofeng\.skills-manager\skills\azf-codex-claude-bridge\scripts\invoke-claude.ps1" -Mode question -Prompt "请从架构角度评价这个方案：..."
```

For custom content, pipe text into the script:

```powershell
git diff | powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\anzhaofeng\.skills-manager\skills\azf-codex-claude-bridge\scripts\invoke-claude.ps1" -Mode stdin-review
```

## Direct CLI Fallback

If the wrapper is unavailable, call Claude directly:

```powershell
git diff | claude -p "Review this diff in Chinese. Focus on bugs, regressions, data-loss risks, concurrency/state issues, and missing tests. Read-only review only."
```

For project-level context:

```powershell
claude -p "Read-only project review in Chinese. Identify design risks and test gaps that Codex should verify." --add-dir .
```

## Output Contract

After Claude returns, Codex must summarize in this order:

1. Claude's main findings.
2. Codex's judgment: which findings look actionable, which are weak or need verification.
3. Suggested next step.
4. Whether any code edits are being proposed, and whether user confirmation is needed.

Do not present Claude output as automatically correct. Treat it as another review signal.

## Failure Handling

- If `claude` is missing, tell An Zhaofeng to install or log in to Claude Code before using this bridge.
- If Claude asks for login or permissions, stop and report the exact issue.
- If the diff is too large, summarize the relevant files first or split the review by subsystem.
- If Claude output is empty or malformed, retry once with a shorter prompt.
- If Claude suggests broad rewrites, ask Codex to reduce the suggestion to the smallest safe patch before acting.
