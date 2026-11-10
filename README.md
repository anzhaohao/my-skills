# Skill 规范库

这个目录是 An Zhaofeng 的 **skill 规范库**，真实位置为 `E:\software\skills-manager\skills`，同时也是它的 GitHub 备份仓库（`github.com/anzhaohao/my-skills`，分支 `main`）。

各个 agent / harness 通过 **逐个 skill 的 junction 指向这里**读取已部署的 skill：

- 部署位置包括 `~/.agents/skills`、`~/.claude/skills`、`~/.codex/skills`、`~/.cursor/skills`、`~/.trae/skills`、`~/.antigravity/skills` 等。
- 哪些 skill 部署到哪些 harness，由 Skills Manager 当前预设及客户端部署设置决定；harness 自带的 skill 和运行时插件保留在各自原生目录。

因此**改这里的 skill = 已部署该 skill 的 agent 同时读取更新**；往这里放东西前请先看下面的收纳规则。

## 收纳规则（只放两类）

1. **第三方 skill** —— harness 厂商以外的人 / 组织发布的。例如社区包 `nature-*`、`xxd-panel-*`，其它公司官方出的 `gsap-*`（GreenSock）、`cloudflare-deploy`（Cloudflare）、`obsidian-*` 等；
2. **自建 skill** —— 自己写的，命名带 `azf-` / `azq-` 前缀。

新安装或接管的这两类 skill 都必须加入 **“通用技能” preset**。本机数据库已配置自动归组规则，软件界面与命令行安装共用；Agent 安装后仍须核对成员关系，遗漏时补加。自动归组不额外部署到其它客户端，部署范围按当前设置与用户要求决定。规则定义和恢复说明在 `E:\software\skills-manager\maintenance`。

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
- **2026-11-10 · Codex 统一接管**：原先 25 个未部署记录中，24 个是 Codex 独立目录，先保留修改合回中央库，再将原件移入 E 盘备份并部署中央库链接；另 1 个是 `officecli` 内嵌 skill 的重复登记，去掉重复管理记录，实际项目文件保留。备份位于 `E:\software\AI改前备份\20261110_182449_Codex技能接管_修改前备份_codex`。

## 关于旧管理软件（Skills Manager）留下的东西

- `.claude-plugin/marketplace.json`（Claude Code 市场清单）与本文档原先那张 `## Skills (NNN)` 自动表格，都是旧工具生成的。**2026-09-24：清单已删除**（准备更换 skill 管理软件），本文档改为**手写维护**，不再放会过期的自动表格。
- **2026-11-10：中央库已迁移至 E 盘**。当前管理器根目录为 `E:\software\skills-manager`，中央库为其 `skills` 子目录，数据库为 `skills-manager.db`。`C:\Users\anzhaofeng\.skills-manager` 只保留 `bin` 下的 CLI 桥接，不再存放 skill 或数据库；禁止把它当作备用库。旧数据仅作历史追溯，迁移备份位于 `E:\software\AI改前备份\20261110_174900_SkillsManager中央库迁移_修改前备份_codex`。

## 当前规模

**“通用技能” preset 有 106 个有效成员，Codex 已部署 106/106**（2026-11-10 核对）。原 107 个成员中包含 1 个 `officecli` 重复记录，去重后实际技能文件保留。主要构成：

- 自建：`azf-*`（个人习惯、agent 记忆、项目管理、论文工作流、管理器生成、校园网代理修复等）、`azq-*`
- 第三方：`nature-*` 学术写作系列、`gsap-*` 动画系列、`understand-*`、`xxd-panel-*`、`officecli` 等

> 需要实时成员与部署状态时，以 Skills Manager 中的“通用技能”预设及其状态为准；文件夹列表还可能包含项目内嵌目录或未纳入该预设的历史内容。
