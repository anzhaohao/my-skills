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

Round 1 may read the registry, scan the Obsidian vault, check the flat central concept-card directory, and create a pending location manifest. It must not modify paper notes, concept cards, Zotero, or paper workspaces, and must not create in-directory index/Base/card subfolders.

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
- A paper workspace may contain Markdown, reviewed formal images, exactly one `附件/原文/原文.pdf`, and controlled audit JSON under `附件/状态/`. It must contain no raw parser cache, MinerU raw JSON, logs, rejected previews, or generated debug directories.
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
9. For English sources, use `azf-paper-zh-reading-translator` to produce the Chinese fulltext and the current external run's `state/translation-audit.json`. Footnotes are part of faithful translation: original source footnotes must remain in the `【中译】` note at the corresponding location and must not be moved to `【精读】`. For Chinese sources, retain `MinerU中文全文.md`, generate `【原文】`, and mark translation not applicable.
10. Import English translation with `generate-zh-fulltext --translated-note ... --translation-audit ...`; for a Chinese workspace the same command builds the linked original-fulltext note without a translation audit.
11. Run `optimize-translation-footnotes --workspace <workspace>` as a dry-run when source footnotes may exist; apply only after the confirmed location manifest and an external backup root. Formula footnotes keep LaTeX unchanged and place the Obsidian footnote anchor in a PDF formula screenshot caption, never inside the formula block.
12. Generate the separate `【精读】...md` note. Interpretation, explanation, evidence-chain analysis, and research inspiration belong here, never in the translation unless it is an original source footnote being translated faithfully.
12. Update or create reusable concepts directly under the confirmed `concept_library_root`. Do not create `入口和索引/`, `概念卡/`, domain, topic, or status subfolders inside it.
13. Run `validate-pilot --artifact-id <id> --promote`. Promotion is allowed only when every gate passes; on failure keep the run as history and leave `latest_successful` unchanged.

# Artifact Migration and Retention

- Use `migrate-artifacts <workspaces...>` for a read-only legacy-layout plan. Apply only with `--apply --backup-root <external-path>` after counts, hashes, and targets are reviewed.
- Migration copies and validates state before removing in-vault JSON or same-hash duplicate PDFs. Never remove a non-identical PDF automatically.
- Keep every successful, failed, and debugging run indefinitely. `artifact_root` is not part of Git; back it up manually at important successful milestones.

# Translation Gate

The Chinese fulltext must account for every meaningful source sentence. Preserve qualifications, formulas, citations, figures, tables, values, units, and uncertainty. Forbid summary substitution, explanatory expansion, evaluation, and unsupported interpretation.

Read `references/translation-fidelity.md` before generating or revising a Chinese fulltext note.


# 表格 LaTeX/OCR 乱码防复发

In translated Chinese fulltext, table cells containing abbreviations, labels, Yes/No values, percentages, algorithm names, and asterisk markers are ordinary table text by default. Do not preserve MinerU hallucinated LaTeX for labels such as `SPM + P.L.`, `SPM + N.L.`, `Yes*`, or `64 × 64`. Keep true mathematical expressions as LaTeX, but when table text in MinerU conflicts with the PDF/table screenshot, trust the PDF. If uncertain, mark the exact table cell for manual review rather than guessing.

The translation quality gate flags typical table OCR/LaTeX artifacts including `\mathbf { S P M }`, `\boldsymbol { \Upsilon }`, `\mathsf { e s }`, and `$. 6 4 \times 6 4`; these should be cleaned back to readable table text before accepting the `【中译】` note.

# 中译脚注规范

正文参考文献标号属于中译笔记的可读性增强对象。处理范围采用排除区模型：除作者/机构区、通讯作者区、摘要前元信息、参考文献区、已生成脚注定义区和公式块内部外，其余正文都处理；`# 摘要` / `# Abstract` 默认纳入处理。可处理标号包括 `[1]`、`[2,3]`、`[1]-[3]`；作者名上标、作者机构、通讯作者和文末参考文献列表本身必须原样保留。

脚注采用 Obsidian 原生 / Tidy Footnotes 兼容的数字脚注格式：正文 `[1]` 转为 `[^1]`，`[2,3]` 转为 `[^2][^3]`，`[1]-[3]` 转为 `[^1][^2][^3]`。脚注定义直接替代文末参考文献列表，仍使用标题 `# 参考文献`；定义写成 `[^1]: 原文参考文献 [1]：...`，用定义文本显式保留原文参考文献编号。正式笔记中不得保留 `<!-- azf-footnotes:... -->` 这类可见托管注释，也不得生成 `azf-ref` 长命名脚注锚点。

公式区域最危险，禁止把 `[^...]` 插入 `$$...$$` 公式块内部，也不要改写原 LaTeX 公式。若后续确认公式处确有必须处理的引用或脚注，先记录待人工复核；需要 PDF 公式截图时，只截公式区域，并把说明和脚注放在公式块外。

可用命令：

```powershell
python -X utf8 -m workflow.cli optimize-translation-footnotes --workspace <论文工作区>
python -X utf8 -m workflow.cli optimize-translation-footnotes --workspace <论文工作区> --apply --backup-root <库外备份目录>
python -X utf8 -m workflow.cli optimize-translation-footnotes --all-translations
python -X utf8 -m workflow.cli optimize-translation-footnotes --all-translations --apply --backup-root <库外备份目录>
```

`--apply` 或 `--all-translations` 必须依赖已经确认的两轮 location manifest；单篇 `--workspace` dry-run 可以只读预检，但正式写入仍要先完成位置确认。验证器会检查脚注引用/定义一一对应、公式块内部无脚注锚点、公式截图链接可解析、参考文献脚注定义保留原文编号或来源说明。

# Central Concept Library

Logical structure:

```text
<concept_library_root>/
├── 概念A.md
├── 概念B.md
└── ...
```

`concept_library_root` itself is the concept-card directory. The current confirmed location is `E:\software\Obsidian\安钊锋的外置大脑\02-Brain Cells\99_扫盲班`, and only concept-card Markdown files should live there. If an external index, Base, or dashboard is needed, it must live outside this directory.

Generate all Wikilink prefixes from `concept_library_root` relative to `vault_root`. Never hardcode an old folder hierarchy.

Never create domain, topic, or status subfolders. Keep card paths stable and classify with properties. Before creating a card, search file names, `英文名`, and `aliases`. Reuse or merge existing cards instead of creating paper-local copies.

Read `references/concept-library-maintenance.md` before concept migration, duplicate merging, Base edits, or template changes. Current auto-generated central cards are not user-curated knowledge; do not restore deleted cards automatically or treat their presence as a completion requirement.

# Migration Safety

1. Complete both location rounds.
2. Run dry-run and staging validation.
3. Back up or archive an existing central target before replacement.
4. Archive paper-local `扫盲班/` directories outside the vault instead of permanently deleting them by default.
5. Require zero unresolved old `../扫盲班/...` links.
6. Validate card count, fixed properties, Templater template, no in-directory subfolders, and all central link targets.

# Completion Gate

Do not report completion until:

- the location manifest is confirmed and still valid;
- project or bundled tests pass;
- CLI help and relevant dry-run commands work;
- Docker readiness is stated accurately;
- no placeholder translation is accepted as fulltext;
- translation audit and strict paper quality gate pass;
- central links match the confirmed vault-relative flat concept-card directory;
- no human note was overwritten;
- each paper workspace contains exactly one source PDF, controlled audit JSON only under `附件/状态/`, and no raw parser/cache/log JSON;
- the selected external artifact exists, validates across roots, and is registered as latest successful only after a full pass;
- changed files and rollback locations are reported.

