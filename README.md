# Skill 规范库

这个目录是 An Zhaofeng 的 **skill 规范库**，同时也是它的 GitHub 备份仓库（`github.com/anzhaohao/my-skills`，分支 `main`）。

各个 agent / harness 通过 **junction 指向这里**读取 skill：

- 整目录链接：`~/.agents/skills`、`~/.claude/skills`
- 逐个 skill 链接：`~/.codex/skills`、`~/.cursor/skills`、`~/.trae/skills`、`~/.antigravity/skills` 等

因此**改这里的 skill = 所有 agent 同时生效**；往这里放东西前请先看下面的收纳规则。

## 收纳规则（只放两类）

1. **第三方 skill** —— harness 厂商以外的人 / 组织发布的。例如社区包 `nature-*`、`xxd-panel-*`，其它公司官方出的 `gsap-*`（GreenSock）、`cloudflare-deploy`（Cloudflare）、`obsidian-*` 等；
2. **自建 skill** —— 自己写的，命名带 `azf-` / `azq-` 前缀。

**不收**：

- **harness 厂商自家发布的 skill**（OpenAI 为 Codex、Cursor 为 Cursor、Anthropic 为 Claude Code、DeepSeek 为 DSH 出的）——它们只放在**对应 harness 自己的 skill 目录**里；
- 绑定某个 harness 生态的移植件 / 工具件（同样按上一条处理）。

> 判定线索：skill 文档里引用该 harness 的私有路径或专有 frontmatter，例如 `.cursor/rules/`、`.cursor/hooks.json`、`~/.cursor/cli-config.json`、`disable-model-invocation`。

## 处置流程（发现库里有不该在这儿的东西）

1. **安置**（不要只备份 + 删除）：放进它对应 harness 的目录
   - Cursor 系 → `~/.cursor/skills/`
   - OpenAI / Codex 系 → `~/.codex/skills/`
   - 其他厂商按各自 harness 目录类推
2. **删链接**：清掉各 agent 目录里指向它的 junction，避免留下悬空链接；
3. **留档**：内容副本进 `E:\software\AI改前备份\<时间戳>_skill库移出<原因>_codex\`；
4. **提交**：在本仓库提交并推送。

## 已处理记录

- **2026-09-24 · Cursor 自带 9 个**：`canvas`、`create-hook`、`create-rule`、`create-skill`、`create-subagent`、`statusline`、`update-cli-config`、`update-cursor-settings`、`migrate-to-skills` → 安置到 `~/.cursor/skills/`；删除 `~/.codex`、`~/.trae`、`~/.antigravity` 下指向 `create-skill` 的 3 个 junction；备份 `20260924_161220_skill库移出Cursor自带skill_codex`。
- **2026-09-24 · harness 厂商一方 2 个**：`chatgpt-apps`、`pdf` → 安置到 `~/.codex/skills/`；删除 `~/.codex/skills` 下对应 junction；备份 `20260924_162943_skill库移出一方vendor skill_codex`。
- **2026-09-24 · 删除 `dshx`**：DSH 插件开发工具，原始内容在 `C:\Users\anzhaofeng\Desktop\test\deepseek-harness\tools\dshx\skill\dshx`，需要时从源头取用；库内副本与 Codex 链接一并移除。
- **2026-09-24 · 清理 40 个悬空链接**：11 个在库里已不存在的 skill 名（`api-relay-audit`、`azf-codex-claude-bridge`、`azf-hardware-skill`、`azf-obsidian-work-record`、`azf-obsidian-workflow`、`azf-paper-sentence-deep-reading`、`azf-project-note-binding`、`azf-shanghai-high-school-score-report`、`deep-learning-experiment-record`、`paper-obsidian-review`、`shanghai-high-school-score-report`）残留在各 agent 目录里的死链。它们在 6/1、7/18、8/13 就被旧软件的 `Force sync` 删除过，内容可从 git 历史取回（如 `git checkout e74ebc3^ -- <名字>`）。
- **2026-09-24 · 其它清理**：`eli5` 从内嵌 git 仓库（gitlink 空指针）改为随库保存的真实内容；`dshx` 的外链方向问题已随删除解决；`.gitignore` 已忽略 `__pycache__` / `*.pyc` 等噪音并停止跟踪 145 个缓存文件。

## 关于旧管理软件（Skills Manager）留下的东西

- `.claude-plugin/marketplace.json`（Claude Code 市场清单）与本文档原先那张 `## Skills (NNN)` 自动表格，都是旧工具生成的。**2026-09-24：清单已删除**（准备更换 skill 管理软件），本文档改为**手写维护**，不再放会过期的自动表格。
- 旧工具的数据仍在 `.skills-manager` 根目录下（不在本仓库内）：`config.json`、`github-config.json`、`usage.db`、`cache/`、`hooks/`、`link-backups/`、`logs/`、`retired-skills/`、`update-backups/`。

## 当前规模

**105 个 skill 目录**（2026-09-24 整理后）。主要构成：

- 自建：`azf-*`（个人习惯、agent 记忆、项目管理、论文工作流、管理器生成等）、`azq-*`
- 第三方：`nature-*` 学术写作系列、`gsap-*` 动画系列、`obsidian-*`、`speckit-*`、`understand-*`、`xxd-panel-*`、`officecli`、`pdf` 之外的文档类工具等

> 需要完整的实时清单时，直接看本目录的文件夹列表（`Get-ChildItem -Directory`），不要依赖任何缓存清单。
