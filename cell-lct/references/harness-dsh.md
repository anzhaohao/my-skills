# DSH harness adapter

DSH (DeepSeek Harness) is a supported first-class harness. The core Cell-lct
runtime is model-agnostic: it does not care whether the active DSH model is
DeepSeek V4 Flash, DeepSeek V4 Pro, or any other model.

## Skill discovery

- DSH discovers skills from user/project skill directories. Install the skill
  to your existing DSH skill location (the installer accepts any destination):
  `installers/setup.ps1 -Target dsh -SkillDestination <path>`.
- If you already manage skills through a personal skill manager, point
  `-SkillDestination` at that manager's directory instead; Cell-lct never
  forces a fixed path.

## Execution paths

- The skill drives the stable CLI: `scripts/cell-lct.ps1 doctor|verify|image-clean|vectorize|prepare|draw|reconstruct`.
- If an MCP host is available, `mcp/server.py` exposes the same operations as
  MCP tools (`cell_lct_health`, `cell_lct_verify`, `cell_lct_vectorize`,
  `cell_lct_prepare`, `cell_lct_draw`, `cell_lct_reconstruct`).

## Image-edit backend

- If DSH is configured with a `dsh-image-gen` capability, configure
  `image_edit_provider: "dsh-image-gen"` in `~/.cell-lct/config.json`; the
  skill then performs text-only cleanup through it (agent-inline).
- Otherwise use any other provider: `openai-compatible` (HTTP), `custom`
  (user command template), or a future provider. No DSH model or built-in
  image tool is assumed.

## Secrets and config

- Keys live in `~/.cell-lct/secrets/` (DPAPI), config in
  `~/.cell-lct/config.json`. No plaintext key is ever placed in chat, argv,
  logs, or the repository.
