# AZF Auto Dev Loop

## 这个 Skill 解决什么问题

它为本地代码仓库提供一个成本可控的开发闭环：先用确定性预检生成原子 Work Item，再在 Claude Code + DS v4 Flash（60%）和 Luna（40%）之间选择执行；失败后按 `Flash/Luna → Terra → DS v4 Pro → Sol` 升级，由独立 Evaluator 检查实际 diff、测试或领域证据。HTML 视觉任务可以交给独立的 `azf-html-ui-loop` 做多候选截图探索。

## 什么时候使用

- 功能开发、Bug 修复、重构、性能优化和测试补充；
- 技术债清理或代码审查后修复；
- 需要比较任务成本、缓存命中率和返工率；
- 不希望工作流绑定 Claude、ZCode、Kandev 或某个固定 Harness。
- 需要通过 `task_profile=experiment-record` 或 `task_profile=html-ui` 使用领域流水线。

## 自动触发与默认入口

用户级 `C:\Users\anzhaofeng\.codex\AGENTS.md` 已把本 Skill 设置为本地代码修改的默认工作流。因此用户只需描述功能开发、Bug 修复、重构、测试、性能优化或审查后修复，不必显式写 `$azf-auto-dev-loop`。简单解释、状态查询和不要求实施的只读报告不会强制进入开发闭环。

用户显式指定 Skill、模型、Harness、成本模式或要求跳过自动路由时，以当前请求为准。如果本 Skill 无法加载，Agent 必须先报告实际模型、Harness 和降级方式，不能静默改用当前高价模型直接执行。

## 当前关键规则

- 普通明确任务可以跳过 Planner；中等规划复杂度使用 Terra Planner，高风险或计划根本错误才使用 Sol Planner；
- 0～5 分低/中风险任务在 DS v4 Flash（60%）和 Luna（40%）之间可复现加权选择；6～7 分使用 Terra；8～10 分或硬风险才使用 Sol；
- 失败升级顺序是 DS v4 Flash/Luna → Terra → DS v4 Pro → Sol；
- Luna medium、Terra/DS v4 Pro/Sol Executor high、Terra/Sol Evaluator high；
- 每个 Executor 只接收一个 typed Work Item，不重新规划整个仓库；
- Evaluator 必须使用全新只读会话，直接检查文件、Git diff 和测试；
- Claude Code 通过非交互 adapter 自动执行，不再生成 proposal 后暂停；
- 所有子代理使用 full-trust，主要依靠提示词约束和前后审计；禁止自动 `git add`、`commit`、`push` 或删除用户原有修改；
- PowerShell 控制器把基线、路由、Work Item、执行、确定性 Gate、验收、代理事件、usage 和最终报告保存到用户级运行目录。
- `route-history-before.json` 按任务档案、Harness 和请求模型累计样本；样本不足 20 条时只记录，不据此自动声称 cost_per_pass。
- 最终答复必须单独显示“模型调用链条”：按实际顺序列出 Planner、Executor、Evaluator、重试和升级，并包含各阶段的 Harness、请求/解析模型与 effort；跳过阶段和无额外模型调用也要明确说明。只能使用运行证据，未知值写 `unverified`，不得展示或声称展示隐藏思维链。
- API key 登录时，控制器阶段调用会关闭插件初始化以绕过 ChatGPT 会话专属的远程插件目录；本地 Skill 仍从 Skill 根目录加载。Codex 的非致命 stderr 会保留在证据目录，不会单独导致阶段失败。

## 入口和资源

- 主指令：`SKILL.md`；
- 控制器：`scripts/azf-auto-dev-loop.ps1`；
- 结构化输出：`schemas/`；
- Codex 用户级代理：`%CODEX_HOME%/agents/azf-*.toml`。

## 领域 Skill

- 实验记录：`azf-deep-learning-experiment-record` 先运行增量证据扫描；
- HTML UI：`azf-html-ui-loop` 生成隔离视觉候选、截图画廊，用户选择后才应用主版本。

## Claude Code / DS 使用

普通任务不需要手动指定 Harness，控制器会在 DS v4 Flash 和 Luna 之间按
60/40 的可复现权重选择。需要固定 Claude Code 时可以显式运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  $controller `
  -Harness claude-code `
  -ExternalProfile claude-ds-v4-flash `
  -DsFlashModel deepseek-v4-flash `
  -Task "修复当前项目的保存失败问题" `
  -RepoPath (Get-Location).Path
```

失败时会自动经历 `DS v4 Flash → Terra → DS v4 Pro → Sol`；如果首轮是
Luna，则为 `Luna → Terra → DS v4 Pro → Sol`。每个阶段的模型、思维强度、
Harness、权限和路由原因保存在 `agent-events.jsonl` 与对应的 route 文件中。
Claude Code 的实际模型别名可以用 `-DsFlashModel`、`-DsProModel` 覆盖；
如果 CLI 没有返回实际模型，记录会标为 `unverified`，不会假装完成解析。

## DeepSeek 全链路（`harness=deepseek`）

想让 Claude Code + DeepSeek 或 DSH + DeepSeek 整条链路都不碰 GPT 时，用
`-Harness deepseek`：Planner / Evaluator 固定走 DS v4 Pro，Executor 从 DS v4
Flash 起步、同档重试一次后升到 DS v4 Pro，不会再升到 Terra / Sol / GPT。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  $controller `
  -Harness deepseek `
  -Task "修复当前项目的保存失败问题" `
  -RepoPath (Get-Location).Path
```

思维强度按阶段自动解析：Flash 低/中、Pro 高、Planner 中（Sol 档为高）、
Evaluator 高。这是纯 DeepSeek 会话默认的省钱配置；只有显式切回
`-Harness codex` 才会重新启用 GPT 分层。

## Kimi + Qwen 链路（`harness=kimi-qwen`）

想让规划与评估走 Kimi、执行走 Qwen 时，用 `-Harness kimi-qwen`：Planner /
Evaluator 固定 Kimi（默认 `k3-256k`），Executor 固定 Qwen（默认
`qwen3.8-27b`），思维强度全部交给模型自决（不向 CLI 传 `--effort`，CLI 侧
`effort=auto`），失败只做一次同档 Qwen 定向重试，不升级 GPT。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  $controller `
  -Harness kimi-qwen `
  -Task "修复当前项目的保存失败问题" `
  -RepoPath (Get-Location).Path
```

可用 `-KimiModel`、`-QwenModel` 覆盖默认模型；只有想显式钉住某档强度时才传
`-ExternalEffort`（如 `high`），否则保持 `auto`。

## 维护、验证与删除

- 唯一维护源：`C:\Users\anzhaofeng\.skills-manager\skills\azf-auto-dev-loop`。
- Codex 入口：`C:\Users\anzhaofeng\.codex\skills\azf-auto-dev-loop`，当前应为指向维护源的 Junction；不要复制出第二份独立正文。
- 修改路由、模型、参数或执行逻辑时，同时检查 `SKILL.md`、本 README、`scripts/`、`schemas/`、用户级 `agents/` TOML 和 `references/external-harness.md`，并保留用户已有修改。
- 修改后至少运行 PowerShell 语法解析、全部 JSON Schema 解析、确定性 `dry-run`，再以 UTF-8 模式运行 `skill-creator/scripts/quick_validate.py`。真实模型验证必须单独记录 API、模型、耗时和证据目录。
- 删除前先备份维护源，并用 `Get-Item -Force` 确认 Codex 入口的 `LinkType` 和 `Target`。随后依次移除本文件在用户级 `AGENTS.md` 中的默认路由、两个领域 Skill README/SKILL 中的依赖说明、顶层 Skill 索引和 Marketplace 条目；最后只删除已确认的 Junction 和维护源目录。
- 不要使用宽泛递归删除、环境变量展开后的不确定路径，或顺手删除用户级代理 TOML。是否删除 `azf-sol-planner`、`azf-*-executor`、`azf-*-evaluator` 必须单独确认，因为其它工作流也可能复用它们。

## 最近维护

2026-08-25：新增 `harness=kimi-qwen` —— Planner / Evaluator 固定 Kimi（`k3-256k`），Executor 固定 Qwen（`qwen3.8-27b`），思维强度全部交给模型自决（不传 `--effort`，`effort=auto`），Executor 失败只做一次同档重试、不升级 GPT；新增 `-KimiModel` / `-QwenModel` 参数。

2026-08-21：新增 `harness=deepseek` 全 DS 链路 —— Planner / Evaluator 固定 DS v4 Pro，Executor 用 DS v4 Flash 起步并只升到 DS v4 Pro，思维强度按阶段自动解析；纯 DeepSeek 会话不再回退 GPT。

2026-08-17：要求最终答复新增独立的“模型调用链条”段落，展示可审计的实际模型与 Harness 路由，并明确跳过或未验证的阶段。

2026-08-15：将 Claude Code + DS v4 Flash 接入自动执行；增加 DS Flash/Luna 60/40 初始池、Terra → DS v4 Pro → Sol 升级链、typed Work Item、确定性 Gate、full-trust 提示词约束与审计、代理模型/强度事件记录，并新增 Terra Planner。
