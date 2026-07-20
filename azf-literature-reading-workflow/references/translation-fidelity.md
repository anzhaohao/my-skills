# 翻译与精读的边界

`【中译】...md` 是论文翻译，不是摘要、精读、解读或知识扩展。

`【精读】...md` 才负责核心理解、证据链、图表解释、概念障碍、研究启发和个人判断。两类笔记不得混写。

# 忠实翻译要求

1. 按原文章节和论证顺序翻译。
2. 原文每个有语义的句子都必须在中文稿中得到对应表达。
3. 不得用概括代替原句，不得跳过限定词、否定、条件、比较、因果、概率和不确定性表达。
4. 不得擅自补充背景知识、原理解释、评价、启发或结论。
5. 可以为中文语序拆分长句，但不得丢失或合并掉原文信息。
6. 公式、变量、编号、引用、图表标签、数值和单位必须保留。
7. 图注和表注也属于翻译范围，不得只翻正文。
8. Parser 噪声或版面不确定处必须留下明确警告，不得自行猜测补齐。

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


# 表格 LaTeX/OCR 乱码防复发规则

表格单元格里的缩写、算法名、Yes/No、星号、百分比和普通标签默认按普通文本处理，不要因为 MinerU 输出里出现 `\mathbf`、`\boldsymbol` 或 `\mathsf` 就自动保留为 LaTeX。典型例子：`SPM + P.L.`、`SPM + N.L.`、`Yes*` / `是*`、`64 × 64` 应保持可读文本。

只有真正的数学表达式才保留 LaTeX；如果 MinerU Markdown 与 PDF 表格不一致，以 PDF 或表格截图为准。无法确认时不要猜修，先在译文对应位置标记待人工复核。

质量门会提示以下高风险表格 OCR/LaTeX 乱码：`\mathbf { S P M }`、`\boldsymbol { \Upsilon }`、`\mathsf { e s }`、`$. 6 4 \times 6 4`。出现这些模式时，应回看 PDF/截图，把普通表格文本清洗为可读中文或原始缩写，而不是把乱码继续带入正式中译。

# 翻译审计

正式接受一篇中译前，需要生成 `附件/状态/translation-audit.json`：

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

接受条件是源文件哈希一致、原文句子全部覆盖、没有遗漏句、没有新增解释段，并且不含旧的“节级中译阅读初版”“阅读导入”“解析来源节选”等占位内容。

# Skill 使用原则

`azf-paper-zh-reading-translator` 用于提高术语、句法、公式、图表和引用的一致性，不允许借 Skill 名义进行总结或发散。

翻译 Skill 完成中译和审计后，工作流 CLI 只负责验证、导入、保护已有人工内容和更新质量报告。CLI 不再伪造摘要式“中译初版”。
