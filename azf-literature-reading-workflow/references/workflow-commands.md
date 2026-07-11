# Contract: Workflow Commands

This contract describes planned Agent/CLI operations. Names are stable for planning; implementation may expose them as CLI commands, Codex tasks, or MCP tool wrappers.

## `workflow.doctor`

Checks local readiness.

**Inputs**

- `vault_path`
- `zotero_required`: boolean
- `mineru_required`: boolean
- `figure_skill_required`: boolean

**Outputs**

- Zotero local API status
- Obsidian vault status
- Docker status
- local MinerU status
- high-resolution crop skill status
- translation skill status

## `workflow.ingest_paper`

Creates or updates one paper workspace from Zotero metadata.

**Inputs**

- `zotero_key` or `citekey`
- `topic_folder`
- `dry_run`: default `true`

**Outputs**

- planned workspace name
- planned file paths
- metadata diff
- overwrite/preservation report

## `workflow.parse_with_mineru`

Runs local Docker MinerU or attaches existing local MinerU output.

**Inputs**

- `paper_workspace`
- `pdf_path`
- `mode`: `docker-run`, `docker`, or `existing`
- `container`: optional, default `mineru-gradio` for running-container mode
- `docker_image`: optional, default `mineru:latest`

**Outputs**

- `附件/原文/MinerU英文全文.md`
- `附件/原文/MinerU原始输出.json`
- raw image/output paths
- parse status

**Rules**

- MUST NOT silently use cloud/remote parsing.
- MUST mark failed or partial parse in the quality report.

## `workflow.extract_highres_figures`

Uses `pdf-figure-render-extractor` to create primary reading figures.

**Inputs**

- `paper_workspace`
- `pdf_path`
- `mineru_output`
- `clarity`: default `4k`
- `mode`: `existing`, `docker-run`, `docker`, `manual`

**Outputs**

- PNG files under `附件/图片/`
- `附件/状态/figure_extraction_manifest.json`
- optional contact sheet/debug previews
- crop status for quality report

**Rules**

- Prefer MinerU-assisted high-DPI PDF render crops.
- Do not present crops as raw embedded source images; describe them as high-resolution visual reconstructions from the PDF page.
- Verify labels, axes, legends, colorbars, scale bars, and subfigure letters.

## `workflow.layout_sanity_check`

Performs lightweight layout review before translation/deep reading.

**Inputs**

- `paper_workspace`
- `pdf_path`
- `mineru_markdown`
- `pages_to_check`: default selected first content pages, figure-heavy pages, and two-column pages

**Outputs**

- layout sanity status: `pass`, `suspect`, `fail`, `not_applicable`
- reviewed pages
- notes
- blocking flag

**Rules**

- Required for two-column pilot papers.
- `suspect` or `fail` blocks accepted translation/deep reading until reviewed.

## `workflow.generate_zh_fulltext`

Validates and imports a faithful translation produced by `azf-paper-zh-reading-translator`. It MUST NOT generate a summary-style placeholder and call it a translation.

**Inputs**

- `paper_workspace`
- `mineru_markdown`
- `figure_manifest`
- `source_anchors`
- `translated_note`
- `translation_audit` with source hash and complete sentence accounting
- `dry_run`: default `true` when updating existing notes

**Outputs**

- `阅读工作台/【中译】{完整中文标题}.md`
- `附件/状态/translation-audit.json`
- translation fidelity validation result
- source-anchor coverage report

## `workflow.generate_deep_reading`

Generates paper-level deep-reading note.

**Inputs**

- `paper_workspace`
- `zh_fulltext`
- `mineru_markdown`
- `source_anchors`
- `concept_classroom_path`

**Outputs**

- `阅读工作台/【精读】{完整中文标题}.md`
- optional concept-card updates
- optional `逐句精读/` request list

## `workflow.validate_pilot`

Validates pilot gates and decides whether batch processing can proceed.

**Inputs**

- list of five pilot paper workspaces

**Outputs**

- pass/fail per gate
- blocking issues
- batch readiness recommendation
