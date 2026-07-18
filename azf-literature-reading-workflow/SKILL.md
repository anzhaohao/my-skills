---
name: azf-literature-reading-workflow
description: An Zhaofeng's local-first, two-round literature workflow for Zotero-backed paper ingestion, local Docker MinerU parsing, layout review, reviewed high-resolution figures, faithful sentence-accounted Chinese translation, separate deep-reading notes, quality gates, and a movable central Obsidian concept library. Use when processing, migrating, validating, or continuing papers under the personal Obsidian literature workspace. Always locate and confirm note paths before any write-enabled round.
---

# Non-Negotiable Boundaries

- Treat Zotero as the source of truth for bibliographic metadata and PDF attachments.
- Treat Obsidian as the source of truth for user-owned notes and manual judgments.
- Do not write to Zotero without explicit authorization.
- Do not silently fall back to a cloud parser.
- Require a reviewed dry-run for multi-paper writes.
- Do not overwrite human notes or accepted translations without backup and explicit confirmation.
- Run commands that update one paper's external `state/quality-report.json` sequentially.

# Mandatory Two-Round Location Protocol

Use two rounds every time this Skill is invoked for a paper task.

## Round 1: Locate Only

Run from any directory:

```powershell
& 'C:/Users/anzhaofeng/.skills-manager/skills/azf-literature-reading-workflow/scripts/run_workflow.ps1' locate
```

Round 1 may read the registry, scan the Obsidian vault, check role markers, validate the Base filter, and create a pending location manifest. It must not modify paper notes, concept cards, the Base, Zotero, or paper workspaces.

Show the user these resolved roles and stop:

- `vault_root`
- `paper_root`
- `concept_library_root`
- `template_path`
- `artifact_root` (must be outside the Obsidian vault)
- source of each resolution
- stale-path warnings
- ambiguous candidates

Never treat a remembered or default path as confirmed. If multiple candidates exist, require an explicit user choice.

## Round 2: Confirm, Freeze, Execute

Only after the user explicitly confirms the paths, run:

```powershell
& 'C:/Users/anzhaofeng/.skills-manager/skills/azf-literature-reading-workflow/scripts/run_workflow.ps1' confirm-locations
```

Then run `doctor --strict` and the requested workflow command. Write-enabled commands require the confirmed manifest. If a folder moved, a fingerprint changed, a location disappeared, or a workspace is outside the confirmed `paper_root`, stop and return to Round 1.

Machine-local mutable paths live outside the Skill:

```text
C:\Users\anzhaofeng\.config\azf-literature-reading-workflow\locations.yaml
C:\Users\anzhaofeng\.config\azf-literature-reading-workflow\location-manifest.json
```

Do not store mutable machine paths inside the Skill directory. Agent-memory may provide historical candidates but is not the execution source of truth.


# Obsidian and External-Artifact Contract

- Paper note filenames must carry the visible title as `【角色】{中文题名}.md`. English sources use `【中译】`; Chinese sources use `【原文】` and must not fabricate a translation audit.
- Note bodies must not repeat the document title as an internal H1; content sections are promoted one level, so overview sections use `# 导航`, `# 进度`, `# 下一步`.
- `阅读工作台/【总览】{中文题名}.md` must start at byte 0 with exactly one YAML frontmatter block and use Chinese property names. Paper notes must not create the legacy standalone `类型` property; use public `笔记类型` plus paper-specific `论文笔记类型`.
- Do not create a legacy `类型` property or a `工作区` property.
- Overview must use `笔记类型: 索引`, `笔记状态`, and `论文笔记类型: 论文总览`; it must be named `【总览】{中文题名}.md`. Do not create nested `处理状态`; use flat booleans: `已导入`, `已解析`, `已检查版面`, `已裁剪图表`, `已中译`, `已精读`.
- Overview frontmatter must include `原文语言: en|zh`. English sources link `中文全文` to `【中译】...|中译笔记`; Chinese sources set `中译适用: false` and link it to `【原文】...|中文原文`. Note-to-note wikilinks inside the vault must be short filename links without folder paths; keep paths for assets only when needed.
- `原文PDF` and the language-appropriate `MinerU英文全文` or `MinerU中文全文` must be quoted Obsidian wikilinks with aliases.
- The overview must not expose raw JSON links. It records only `外部产物ID`, `质量状态`, `来源核对状态`, and `最近验收时间`.
- Zotero return links must use only `Zotero PDF链接: "zotero://open-pdf/library/items/{PDF_ATTACHMENT_KEY}"`. Do not create `Zotero条目链接`; the overview navigation should expose only an `打开PDF` link back to the Zotero PDF.
- A paper workspace may contain Markdown, reviewed formal images, and exactly one `附件/原文/原文.pdf`; it must contain no JSON, parser cache, log, or `附件/状态/` directory.
- All machine artifacts live under the confirmed external `artifact_root` as `YYYYMMDD_HHMMSS__doi-slug/{state,parser,logs}` plus `run-manifest.json`. `index.json` keeps `latest_attempt` and `latest_successful`; failed runs never replace the latest successful run and no run is auto-deleted.
- Paths from external state to the PDF, MinerU Markdown, notes, or formal images use paper-workspace-relative values and `path_base: paper_workspace`. After a workspace move, dry-run `repair-workspace-paths` before applying the repair.

# Bundled Runtime

The complete Python workflow runtime, configuration, templates, contracts tests, and CLI are bundled under `scripts/runtime/`.

Use `scripts/run_workflow.ps1` from any working directory. It must not depend on a D-drive project folder. Use `scripts/test_runtime.ps1` for the bundled test suite and `scripts/self_test.py` for a fast structural check.

# One-Paper Workflow

1. Complete Round 1 and stop for path confirmation.
2. Complete Round 2, then run `doctor --strict`; local Docker MinerU is the default. If the user explicitly states that existing MinerU output should be reused, run `doctor --strict --reuse-existing`, audit the existing output against the source PDF, and only then use reuse mode.
3. Resolve the exact Zotero parent item and stored PDF attachment. Confirm title, authors, year, venue, DOI, citekey, Zotero key, and the PDF attachment key used by `--zotero-pdf-key`.
4. Name the workspace `{English identification anchor} - {Chinese short title}` under the confirmed `paper_root`.
5. Run `ingest-paper --dry-run`, review the plan, then apply with the confirmed location manifest.
6. Run local Docker MinerU by default. Reuse `--mode existing` or `--mode reuse` only when the user explicitly identifies existing output and the audit confirms source identity, section order, formulas, captions, and figure mapping.
7. Run layout sanity review before accepting translation or deep reading.
8. Extract high-resolution figures. Only reviewed paper figures and tables may enter `附件/图片/`.
9. For English sources, use `azf-paper-zh-reading-translator` to produce the Chinese fulltext and the current external run's `state/translation-audit.json`. For Chinese sources, retain `MinerU中文全文.md`, generate `【原文】`, and mark translation not applicable.
10. Import English translation with `generate-zh-fulltext --translated-note ... --translation-audit ...`; for a Chinese workspace the same command builds the linked original-fulltext note without a translation audit.
11. Generate the separate `【精读】...md` note. Interpretation, explanation, evidence-chain analysis, and research inspiration belong here, never in the translation.
12. Update or create reusable concepts only under the confirmed `concept_library_root/概念卡`.
13. Run `validate-pilot --artifact-id <id> --promote`. Promotion is allowed only when every gate passes; on failure keep the run as history and leave `latest_successful` unchanged.

# Artifact Migration and Retention

- Use `migrate-artifacts <workspaces...>` for a read-only legacy-layout plan. Apply only with `--apply --backup-root <external-path>` after counts, hashes, and targets are reviewed.
- Migration copies and validates state before removing in-vault JSON or same-hash duplicate PDFs. Never remove a non-identical PDF automatically.
- Keep every successful, failed, and debugging run indefinitely. `artifact_root` is not part of Git; back it up manually at important successful milestones.

# Translation Gate

The Chinese fulltext must account for every meaningful source sentence. Preserve qualifications, formulas, citations, figures, tables, values, units, and uncertainty. Forbid summary substitution, explanatory expansion, evaluation, and unsupported interpretation.

Read `references/translation-fidelity.md` before generating or revising a Chinese fulltext note.

# Central Concept Library

Logical structure:

```text
<concept_library_root>/
├── 入口和索引/
│   ├── 扫盲班总览.md
│   └── 扫盲班索引.base
└── 概念卡/
```

The index note must carry:

```yaml
系统角色: 中央扫盲班
系统标识: azf-literature-concept-library-v1
```

Generate all Wikilink prefixes and Base `file.folder` filters from `concept_library_root` relative to `vault_root`. Never hardcode an old folder hierarchy.

Never create domain, topic, or status subfolders. Keep card paths stable and classify with properties. Before creating a card, search file names, `英文名`, and `aliases`. Reuse or merge existing cards instead of creating paper-local copies.

Read `references/concept-library-maintenance.md` before concept migration, duplicate merging, Base edits, or template changes. Current auto-generated central cards are not user-curated knowledge; do not restore deleted cards automatically or treat their presence as a completion requirement.

# Migration Safety

1. Complete both location rounds.
2. Run dry-run and staging validation.
3. Back up or archive an existing central target before replacement.
4. Archive paper-local `扫盲班/` directories outside the vault instead of permanently deleting them by default.
5. Require zero unresolved old `../扫盲班/...` links.
6. Validate card count, fixed properties, Base views, Templater template, and all central link targets.

# Completion Gate

Do not report completion until:

- the location manifest is confirmed and still valid;
- project or bundled tests pass;
- CLI help and relevant dry-run commands work;
- Docker readiness is stated accurately;
- no placeholder translation is accepted as fulltext;
- translation audit and strict paper quality gate pass;
- central links and Base filters match the confirmed vault-relative path;
- no human note was overwritten;
- each paper workspace contains zero JSON files and exactly one PDF;
- the selected external artifact exists, validates across roots, and is registered as latest successful only after a full pass;
- changed files and rollback locations are reported.

