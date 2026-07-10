---
name: azf-paper-zh-reading-translator
description: Translate English academic paper Markdown, especially MinerU/PDF parser output, into an Obsidian-ready Chinese fulltext reading note. Use when creating or revising `中文全文.md`, preserving paper structure, formulas, citations, figure/table references, and original images stored under the paper workspace `附件/图片` directory.
---

# AZF Paper Chinese Fulltext Translator

## Overview

Create the main Chinese reading document for one paper workspace. The output is `中文全文.md`: a fluent Chinese fulltext version of the paper for actual reading in Obsidian, with original figures embedded near the corresponding translated content.

This skill combines two ideas:

- From `academic-zh-translator`: translate by meaning and rewrite into natural Chinese, avoiding translationese.
- From manuscript-translation workflows: maintain a working glossary and run consistency checks for terms, figure/table references, formulas, and omissions.

## Paper Workspace Assumptions

Expect, when available:

```text
论文文件夹/
  中文全文.md
  附件/
    原文/
      原文.pdf
      MinerU英文全文.md
    图片/
      Fig-01.png
      Fig-02.png
      Table-01.png
```

Do not require metadata from the filename. Use the source Markdown and available workspace files. If an image is missing, leave a short `> [!warning]` note at the expected position instead of inventing an image.

## Output Contract

`中文全文.md` must be a reading document, not a database card. Keep YAML minimal:

```yaml
---
type: paper-zh-fulltext
title_en: "Original English Paper Title"
---
```

Do not add author, year, DOI, Zotero key, citekey, paths, status, tags, or processing metadata to this note. Those belong in the overview note or Bases-oriented metadata notes.

After YAML, start directly with translated paper sections. Do not add a repeated paper title unless the user asks for it.

## Translation Style

Translate for sustained reading:

- Use fluent modern Chinese, not word-by-word alignment.
- Preserve the paper's argument, evidence, hedging, citations, formulas, variables, numbering, and section order.
- Split or reorder long English sentences when Chinese readability requires it.
- Keep key English terms on first mention as `中文术语 (English term)`; then use the Chinese term consistently.
- Keep interface names, model names, datasets, equations, commands, file names, and official abbreviations in English when translation would reduce recognizability.
- Do not include large bilingual blocks. The English source lives in `附件/原文/MinerU英文全文.md`.

## Structure Rules

Map the source paper into readable Chinese sections:

```markdown
# 摘要

...

# 引言

...

![[附件/图片/Fig-01.png]]

图 1. 中文图注……

# 方法

...
```

Use `#` for main paper sections and `##` for subsections unless the existing document has a clear deeper hierarchy. Translate headings into Chinese while preserving conventional names such as `Abstract`, `Methods`, or `References` only when useful.

## Image And Table Rules

- Embed original figures from `附件/图片` at the nearest corresponding location in the translated text.
- Use Obsidian embeds: `![[附件/图片/Fig-01.png]]`.
- Translate captions into Chinese below the image; preserve original labels such as `Fig. 1`, `Table 2`, or `Extended Data Fig. 3`.
- If tables are available as Markdown, translate table titles, headers, and notes while preserving numeric values and units.
- If a table is available only as an image, embed it and translate the caption/notes below.

## Workflow

1. Inspect the source Markdown structure, image links, captions, formulas, references, and unusual parser artifacts.
2. Build a small working glossary for recurrent technical terms, materials, methods, variables, and abbreviations.
3. Translate section by section. Internally use three passes: first Chinese rewrite, translationese/terminology review, final Chinese rewrite. Output only the final Chinese unless the user asks for drafts.
4. Reinsert images and table assets using the workspace-relative `附件/图片/...` paths.
5. Run a final consistency check:
   - no major section omitted
   - formulas and variables preserved
   - figure/table references still match
   - citations and reference numbers preserved
   - terminology consistent
   - no unsupported explanation added

## Editing Safety

When modifying an existing `中文全文.md`, preserve user-written edits outside the requested regeneration scope. If a full regeneration would overwrite substantial manual edits, report that and ask before replacing the file.
