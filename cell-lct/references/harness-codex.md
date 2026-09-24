# Codex harness adapter

This adapter keeps the original Codex Desktop workflow fully compatible.

## Default image-edit backend

- Provider: `codex-agent` (default in `~/.cell-lct/config.json`).
- Execution: the Codex agent runs the fixed text-removal instruction inline with
  Codex Desktop's built-in Image 2 editing capability. `cell-lct.ps1 image-clean
  -Provider codex-agent` reports `AGENT_INLINE_REQUIRED` with the instruction and
  the expected output path; the agent performs the edit and confirms the output
  file exists. The CLI then proceeds.
- The image-edit provider never vectorizes. Text-only cleanup only.

## Workflow compatibility

- Invoke with the original prompt pattern:
  `使用 $cell-lct，根据我上传的内容或图片在当前 Illustrator 画板中作图，保留全部已有内容。`
- Skill id stays `cell-lct`.
- Image 2 remains the recommended text-cleanup path on Codex; it is now one
  configured backend instead of a hard-coded prerequisite.

## Installation

- Install with `installers/setup.ps1 -Target codex`.
- The default skill destination follows Codex's convention
  (`~/.codex/skills`), but any custom destination is accepted:
  `installers/setup.ps1 -Target codex -SkillDestination <path>`.
- After installation, restart or reload the active harness (Codex Desktop)
  if required, then start a new task.

## Secrets

- New installs store the key at `~/.cell-lct/secrets/xiaomiao-api-key.dpapi`
  (Windows DPAPI, same encryption as before).
- Existing `~/.codex/secrets/xiaomiao-api-key.dpapi` files remain readable as a
  legacy fallback; nothing is migrated or copied in plaintext.
