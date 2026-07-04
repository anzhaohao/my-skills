# Anti Vibe Writing Skill

这个 skill 用来给 AI 生成的文稿做最后一轮“去 AI 味”润色。它的目标不是把文字写得更花，而是在不改变事实和原意的前提下，去掉模板措辞、咨询腔、过重 Markdown 结构、空泛抽象、伪平衡表达、中文翻译腔和常见 AI 标点痕迹。

# 什么时候触发

- 用户说“去 AI 味”“写得像人一点”“别那么 AI”“口语一点”“像我写的”
- 需要润色推文、微博、公众号、博客、README、产品文档、报告、播客 show notes
- AI 已经写完初稿，需要发布前 final pass
- 用户提供个人样本，要求学习写作风格

# 常用模式

- 默认干净模式：适合大多数专业文档、README、报告。
- 人味儿质感模式：适合个人博客、社交媒体、创始人笔记。
- 学习模式：用户给出自己写过的样本，提炼 host profile，让后续文本更像本人。
- 场景预设：X/微博、博客、播客、专业报告等。

# 推荐用法

```text
用 anti-vibe-writing 帮我把下面这段文字去 AI 味，保留原意，不要增加事实。
```

```text
用 anti-vibe-writing，人味儿质感模式，适合发 X，别太像营销文。
```

```text
这是我以前写的几段样本。请先学习我的风格，再把新稿子改成像我写的。
```

# 和现有工作流的关系

推荐放在工作流最后：

```text
Council 想清楚需求 -> Spec Kit 落成规格/任务 -> Codex 写初稿/文档 -> anti-vibe-writing 最终去味
```

它不负责需求澄清、架构设计或代码实现，只负责文字表达的发布前清理。

# 当前安装位置

- Codex 生效目录：`C:\Users\anzhaofeng\.codex\skills\anti-vibe-writing`
- 统一管理目录：`C:\Users\anzhaofeng\.skills-manager\skills\anti-vibe-writing`

目录内包含：

- `SKILL.md`
- `references/`：中英文 AI 味模式、场景规则、学习模式等
- `assets/`：最终检查清单、改写提示词模板、风格提取模板等

# 最近维护

- 2026-07-04：从 `weijt606/anti-vibe-writing` 的 `skills/anti-vibe-writing` 子目录安装到 Codex 与 Skills Manager，并补充本中文 README。
