# Contract: Workflow Commands

This contract describes planned Agent/CLI operations. Names are stable for planning; implementation may expose them as CLI commands, Codex tasks, or MCP tool wrappers.

## 外部运行约定

两轮位置清单包含 `artifact_root`，且该目录必须位于 Obsidian 库外。一次完整运行对应一个不可复用名称的目录：

```text
YYYYMMDD_HHMMSS__规范化DOI/
├── run-manifest.json
├── state/
├── parser/
└── logs/
```

无 DOI 时使用 `no-doi__zotero-父条目键`。所有相关命令接受 `--artifact-id`；未指定时读取总览或 `index.json` 的最新成功运行。`latest_attempt` 可以是失败运行，`latest_successful` 只能由全部通过的 `validate-pilot --promote` 更新。

## `workflow.doctor`

Checks local readiness.

**Inputs**

- `vault_path`
- `zotero_required`: boolean
- `mineru_required`: boolean
- `figure_skill_required`: boolean
- confirmed `artifact_root`

**Outputs**

- Zotero local API status

## 原文语言

`ingest-paper` 接受 `--source-language en|zh`，默认 `en`。英文使用 `MinerU英文全文.md` 和 `【中译】`；中文使用 `MinerU中文全文.md` 和 `【原文】`，翻译质量项为 `not_applicable`。

## `repair-workspace-paths`

默认只做 dry-run；加 `--apply` 后，检查当前外部运行的 JSON、运行清单和索引绑定，修复到论文工作区内 PDF、MinerU Markdown、正式图片和笔记的跨根路径。人工 Markdown 和 Zotero 链接不在修改范围。
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
- `parser/` 下的 MinerU 原始 JSON、候选图片和解析缓存
- 库内只保留 `附件/原文/MinerU英文全文.md` 或 `MinerU中文全文.md`
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
- 当前外部运行的 `state/figure_extraction_manifest.json`
- `parser/` 下的可选 contact sheet/debug previews
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
- 当前外部运行的 `state/translation-audit.json`
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

## `workflow.validate_pilot`

Validates pilot gates and decides whether batch processing can proceed.

**Inputs**

- paper workspaces
- optional `artifact_id`
- `promote`: only after all gates pass

**Outputs**

- pass/fail per gate
- blocking issues
- batch readiness recommendation
- updated `latest_successful` and overview status fields only on successful promotion

## `migrate-artifacts`

默认 dry-run，盘点旧 `附件/状态/*.json`、运行 ID 和同哈希重复 PDF。`--apply` 时必须提供库外 `--backup-root`；命令先复制和验证外部状态，成功后才移除库内 JSON、空状态目录及同哈希重复 PDF。非同哈希额外 PDF 必须阻断并交由人工判断。
