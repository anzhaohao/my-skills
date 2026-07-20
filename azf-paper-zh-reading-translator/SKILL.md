---
name: azf-paper-zh-reading-translator
description: Faithfully translate English academic paper Markdown, especially MinerU/PDF parser output, into an Obsidian-ready Chinese fulltext note. Use for `【中译】...md` or `中文全文.md` when every source sentence must be accounted for while preserving structure, formulas, citations, figures, tables, values, units, hedging, and original footnotes. This is translation only, not summary or deep reading.
---

# Core Boundary

The output is a faithful Chinese translation of the paper. It is not a summary, explanation, review, tutorial, or deep-reading note.

Never replace source sentences with a shorter overview. Never add background knowledge, evaluation, research inspiration, mechanism explanation, or conclusions that are absent from the source. Put those materials in the separate `【精读】...md` note.

# Required Inputs

Prefer this workspace structure:

```text
论文工作区/
├── 阅读工作台/
│   └── 【中译】完整中文题名.md
├── 附件/
│   ├── 原文/
│   │   ├── 原文.pdf
│   │   └── MinerU英文全文.md
│   └── 图片/
└── figure_extraction_manifest.json
```

Before translation, confirm that MinerU layout order has passed review. If the parser has uncertain text order, missing formulas, or damaged captions, stop acceptance and mark the exact location instead of guessing.

# Translation Contract

- Translate in the source section and argument order.
- Account for every meaningful source sentence.
- Preserve negation, conditions, comparisons, causality, probability, limitations, uncertainty, and hedging.
- Preserve formulas, variables, equation numbers, citations, figure/table labels, values, units, footnotes, and captions.
- Long English sentences may be split for natural Chinese, but no source information may disappear.
- Keep a technical English term on first mention when it improves searchability: `中文术语 (English term)`.
- Do not output large bilingual blocks. The English source remains in `附件/原文/MinerU英文全文.md`.
- Do not insert “核心理解”“方法解读”“对我的启发”“通俗解释”等精读内容。


# Table OCR / LaTeX Artifact Contract

In tables, abbreviations, labels, Yes/No cells, asterisks, percentages, and algorithm names are plain text by default. Do not convert or preserve ordinary table labels as LaTeX just because MinerU produced commands such as `\mathbf`, `\boldsymbol`, or `\mathsf`. For example, keep `SPM + P.L.`, `SPM + N.L.`, `Yes*`, `No`, percentages, and `64 × 64` as readable table text unless the PDF shows a real formula.

True formulas remain LaTeX. When MinerU table text disagrees with the PDF/table screenshot, the PDF wins. If the cell cannot be verified, mark it for manual review instead of guessing or carrying damaged LaTeX into the final `【中译】` note. Treat patterns like `\mathbf { S P M }`, `\boldsymbol { \Upsilon }`, `\mathsf { e s }`, and `$. 6 4 \times 6 4` as high-risk OCR artifacts.

# Footnote And Citation Contract

Do not normalize the paper front matter into Obsidian footnotes. Author lines, author superscripts, affiliations, correspondence notes, received/revised/accepted dates, copyright notes, and DOI lines should remain in the same visible structure as the source/MinerU output unless the user explicitly asks for a different layout.

Body bibliography citations such as `[1]`, `[2,3]`, and `[1]-[3]` are citations, not author-affiliation footnotes. Preserve them faithfully during translation. The literature workflow may later run `optimize-translation-footnotes` using an exclusion model: author/affiliation/correspondence/front-matter metadata, bibliography definitions, generated footnote definitions, and LaTeX formula blocks are excluded; abstract sections are included by default. The optimizer converts bibliography citations into Obsidian-native numeric footnotes: `[1]` becomes `[^1]`, `[2,3]` becomes `[^2][^3]`, and definitions replace the bibliography body under `# 参考文献`. Do not generate long IDs such as `azf-ref-*` and do not emit visible `<!-- azf-footnotes:... -->` management comments.

If the source has a real explanatory footnote outside the bibliography system, keep it in the corresponding translated location and preserve e-mail addresses, URLs, institution names, formula symbols, citation numbers, and the original visible marker. Do not move it to `【精读】...md`. If reliable placement cannot be confirmed from MinerU/PDF, mark it for manual review instead of guessing.

Never insert an Obsidian footnote anchor inside a LaTeX formula block. If a formula needs a footnote/citation treatment, preserve the LaTeX formula, add a PDF screenshot of only the formula region when required, and place the footnote anchor in the screenshot caption/说明 line outside the formula block. Use MinerU Markdown for text when reliable; PDF overrides MinerU on disagreement.

# Output Contract

Use minimal YAML:

```yaml
---
类型: 论文中文全文
英文题名: "Original English Title"
翻译状态: 已逐句忠实翻译
---
```

After YAML, begin directly with translated paper sections. Do not repeat the document title in the body.

Embed reviewed original figures near their source position and translate captions without changing labels or numeric content.

# Sentence-Accounting Workflow

1. Inspect headings, paragraphs, lists, captions, tables, formulas, references, and parser artifacts.
2. Build a working glossary for repeated terms and abbreviations.
3. Divide the source into stable sentence-level translation units.
4. Translate every unit. Maintain a checklist of source unit IDs and translated unit IDs.
5. Reassemble the Chinese note in the original section order without exposing unit IDs in the final prose.
6. Compare the source and translation section by section for omissions and unsupported additions.
7. Generate `translation-audit.json` with:

```json
{
  "mode": "faithful_sentence_by_sentence",
  "status": "pass",
  "source_sha256": "...",
  "source_sentence_count": 0,
  "accounted_sentence_count": 0,
  "omitted_source_sentences": [],
  "added_explanatory_passages": []
}
```

The audit may be `pass` only when source and accounted counts match and both exception lists are empty.

# Final Review

Check all of the following before delivery:

- no source section or meaningful sentence omitted;
- no summary substituted for original prose;
- no explanation or interpretation added;
- formulas, variables, numbering, citations, values, and units preserved;
- figure/table references and captions preserved;
- terminology consistent;
- uncertain parser regions explicitly marked rather than invented;
- `translation-audit.json` matches the current source hash.

# Editing Safety

Existing translations and user edits are user-owned. Never overwrite an existing `【中译】...md` without an explicit reviewed replacement and a recoverable backup. Use the literature workflow CLI to validate and import the finished translation artifact.
