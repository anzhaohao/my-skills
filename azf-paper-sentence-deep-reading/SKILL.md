---
name: azf-paper-sentence-deep-reading
description: An Zhaofeng's Obsidian paper sentence-by-sentence deep reading workflow. Use when the user asks to 精读文献, 逐句精读论文, 生成论文精读笔记, read a paper paragraph by paragraph, create beginner-friendly paper notes in Obsidian, build core glossary notes in 扫盲班, or preserve PDF++ sentence-level selection links.
---

# Workflow

Use this skill to turn a paper section, especially an abstract, into Obsidian sentence-by-sentence deep-reading notes for a beginner. Preserve the user's preferred layout and PDF++ source anchors.

## Start

1. Confirm the paper root folder and the `逐句精读` folder path. If `逐句精读` does not exist, create it after confirmation.
2. Confirm the PDF file and the source paragraph/section. If the user says "摘要", treat the full abstract as one natural paragraph.
3. Confirm or infer the glossary folder as `扫盲班`. Create only core terms required to understand the current paragraph.
4. If scope or source text is ambiguous, ask before editing. If the user already approved generation, proceed.

## Note Scope

- Create one reading note per natural paragraph; title lines count as paragraphs when the user asks to read them.
- Use concise filenames such as `01_摘要.md`, `02_引言第1段.md`, or `03_方法总览.md`.
- Keep the note body title-free unless the user requests a visible title. Use `#` for major sections.
- Maintain a navigation note such as `00_精读导航.md` when processing multiple paragraphs.

## Required Note Structure

Use this order:

1. `# 原文段落定位`
2. `# 破冰前瞻`
3. `# 逐句精读`
4. `# 本段犀利总结与定位`
5. `# 工程实战推演题`
6. `# 关联扫盲班术语`

Do not put "本句功能" at the start of sentence blocks. Sentence function belongs in the paragraph summary when needed.

## Break-Ice Section

Before sentence analysis, write a high-level preview using this four-step engineering logic:

1. `## 明确知识储备与重点`
2. `## 工程师的初级尝试`
3. `## 现实的毒打与工程翻车现场`
4. `## 核心破局之问`

Keep the tone professional, plain, and vivid. Explain why the paragraph exists in the paper's argument.

## Sentence Card Layout

Before every sentence card, add a sentence-level heading in this exact style:

```markdown
## 第 1 句：简明小标题
```

Rules for the sentence heading:

- Use `## 第 N 句：小标题`, where `N` is the sentence number in the current paragraph.
- The short title after `：` must summarize the sentence's role, claim, or key meaning.
- Keep the short title concise, usually 6-18 Chinese characters.
- Prefer plain functional titles such as `AI进入物理大背景`, `提出核心测量对象`, `说明trace可直接判读`.
- Do not use only `## 第 N 句`; the short title is required.
- Do not put "本句功能" at the start of the sentence block. The heading already provides the quick navigational summary, while deeper sentence function belongs in the paragraph summary or explanation.

Then use exactly this non-nested callout layout:

```markdown
> [!note] 中英文对照
> - 【英文原文】：
>   - [[Paper.pdf#page=1&selection=44,0,48,8|Paper, p.1]]
> - 【中文直译】：中文直译。
```

Then add these sections under each sentence:

```markdown
### 【🧅 剥洋葱式概念拆解与深度比喻】

> [!LEARN] 核心概念名
> [[核心概念名]]：先解释物理机制、工程含义或数据含义。解释要面向零基础新手，但不能牺牲准确性。
> > [!EXAMPLE] 💡通俗例子
> > 紧跟一个贴近日常或实验室现场的例子，帮助用户抓住直觉。

### 【💬 大白话解构】

### 【🔧 实验室真相与背景扩展】
```

Explain every key concept for a beginner. In the onion section, format each core concept as an Obsidian callout block:

```markdown
> [!LEARN] 概念名
> [[扫盲班术语]]：概念解释。
> > [!EXAMPLE] 💡通俗例子
> > 通俗例子。
```

Use one `LEARN` block per core concept. Keep the glossary wikilink in the explanation line when a glossary note exists. The nested `EXAMPLE` callout belongs only inside the onion concept card; do not nest the `中英文对照` source callout. For small temporary concepts that do not deserve a glossary note, still use the `LEARN` card but omit the wikilink if needed. Connect formulas or theory to actual lab components, operations, or failure modes.

## PDF++ Selection Links

Prefer exact PDF++ links if the user pasted them. Otherwise generate sentence-level links with `scripts/generate_pdfpp_selection_links.js`. Do not copy full English source sentences into new notes unless the user supplied that short quote directly and it remains a brief excerpt. For paper-wide reading notes, leave `【英文原文】` blank and let the PDF++ selection link carry the source text.

The script follows PDF.js text-layer item indexing, matching PDF++ links of the form:

```markdown
[[Paper.pdf#page=N&selection=beginIndex,beginOffset,endIndex,endOffset|Paper, p.N]]
```

Use a temporary local PDF.js 3.x install if needed:

```powershell
New-Item -ItemType Directory -Force '.codex-tmp/pdfjs-probe' | Out-Null
npm install pdfjs-dist@3.11.174 --prefix '.codex-tmp/pdfjs-probe'
```

Run:

```powershell
node 'C:/Users/anzhaofeng/.skills-manager/skills/azf-paper-sentence-deep-reading/scripts/generate_pdfpp_selection_links.js' `
  --pdf 'path/to/paper.pdf' `
  --page 1 `
  --pdfjs-root '.codex-tmp/pdfjs-probe' `
  --sentence 'First sentence.' `
  --sentence 'Second sentence.'
```

Only trust rows where `matches` is `true`. If a row fails, inspect the nearby PDF.js text items and fix the sentence boundary before writing links.

## Glossary Notes

Create glossary notes only for core terms needed for the current paragraph. Put them in `扫盲班`.

Each glossary note should include:

- What the term means.
- The physical or engineering mechanism.
- A beginner-friendly analogy.
- Why it matters for this paper.
- Common lab failure modes or misunderstandings.

Avoid building a huge encyclopedia before the paragraph requires it.

## Validation

Before final response, verify:

- Every sentence card is preceded by a heading like `## 第 N 句：简明小标题`.
- Every sentence card has blank `【英文原文】：` and a `#page=...&selection=` link.
- No placeholder text such as `请用 PDF++ 粘贴` remains.
- No page-only PDF links remain inside sentence cards.
- The callout is not nested.
- `摘要` has been treated as one natural paragraph when applicable.
- Core glossary notes exist in `扫盲班` and are linked from the reading note.
- The final answer names the changed files and any links the user should click-test in Obsidian.
