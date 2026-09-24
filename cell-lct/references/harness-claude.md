# Claude Code harness adapter

Claude Code is supported through the same principle as every other harness:
the skill owns the SOP, the CLI/MCP owns execution, and the image-edit backend
is a configured provider. Nothing assumes a Claude Code built-in image editor.

## Skill installation

- Claude Code does not (yet) define a single canonical user-skill directory
  on Windows. Install to your personal skill location with the installer:
  `installers/setup.ps1 -Target claude -SkillDestination <path>`.
- If you use a personal skill manager or a shared skill root, pass that path;
  Cell-lct follows your convention instead of inventing one.
- This adapter does not fabricate a native mechanism that does not exist: no
  fake `~/.claude/skills` requirement is imposed.

## Execution paths

- The skill drives the stable CLI: `scripts/cell-lct.ps1 doctor|verify|image-clean|vectorize|prepare|draw|reconstruct`.
- Claude Code supports MCP servers; `mcp/server.py` can be registered as an
  MCP server to expose `cell_lct_*` tools.

## Image-edit backend

- Configure `image_edit_provider` in `~/.cell-lct/config.json`:
  `openai-compatible` (HTTP), `custom` (command template), or a future
  provider. No Claude built-in image tool is assumed.
