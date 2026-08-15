# AZF HTML UI Loop

这个 Skill 用于 HTML/CSS 视觉探索：一次生成多套差异明显的候选方案，用真实浏览器截图比较，再只把用户选中的方案应用到主版本。

## 适用场景

- Landing page、Dashboard、原型页面和前端视觉美化；
- 想一次查看多种布局、配色、背景、卡片或动效；
- 需要桌面端和移动端截图对比；
- 不希望模型直接覆盖当前页面。

## 自动触发与默认入口

用户级 `C:\Users\anzhaofeng\.codex\AGENTS.md` 已将 HTML/CSS 美化、视觉原型、多设计候选、响应式截图和视觉比较默认路由到本 Skill。用户不必显式写 `$azf-html-ui-loop`；提出“一次生成多套效果”“截图后选择”“不要直接覆盖现有页面”等需求时应优先触发。

本 Skill 负责视觉候选和截图证据，`azf-auto-dev-loop` 负责 Luna/Terra/Sol 路由、独立 Evaluator 和成本记录。用户明确指定其它前端 Skill、只要求代码解释或不需要视觉比较时，以当前请求为准。

## 关键规则

- 不冻结设计契约，只有功能约束保持不变；
- 每个候选方案使用隔离目录或临时 worktree；
- 默认生成 4 套，普通批量 8 套，用户明确要求时可到 20 套；
- 使用独立 Playwright 截图，不使用 Codex 内置浏览器做本地 HTML QA；
- 先生成候选画廊，等用户选择后再改主版本；
- 由 `azf-auto-dev-loop` 提供模型路由、成本记录和人工闸门；
- 禁止自动提交或推送。

## 资源

- `scripts/azf-ui-batch.ps1`：生成候选目录和调用截图流程；
- `scripts/azf-ui-capture.ps1`：调用独立 Playwright 截图并记录基础检查；
- `scripts/azf-ui-compare.ps1`：生成候选清单和静态比较画廊；
- `scripts/azf-ui-apply.ps1`：用户选中候选后安全应用到主工作树；
- `schemas/`：变体清单和 UI 评估结果结构。

## 维护、验证与删除

- 唯一维护源：`C:\Users\anzhaofeng\.skills-manager\skills\azf-html-ui-loop`。
- Codex 入口：`C:\Users\anzhaofeng\.codex\skills\azf-html-ui-loop`，应为指向维护源的 Junction。
- 修改候选数量、截图尺寸、隔离方式或应用闸门时，同时更新 `SKILL.md`、本 README、相关 PowerShell/Node 脚本、`schemas/` 和 `agents/openai.yaml`。不要把审美方向重新冻结成单一设计契约。
- 修改后运行 PowerShell 和 Node 语法检查、Schema JSON 解析、批量候选清单、画廊生成、候选应用确认闸门、已有修改保护，并以 UTF-8 模式运行 `skill-creator/scripts/quick_validate.py`。真实截图测试缺少 Playwright 时应失败关闭，不自动安装依赖。
- 删除前先备份并确认 Junction 目标；然后移除用户级 `AGENTS.md` 的 HTML UI 默认路由、`azf-auto-dev-loop` 中的 `html-ui` 路由和依赖说明、顶层 Skill 索引及 Marketplace 条目，最后删除已确认的 Junction 和维护源目录。
- 删除本 Skill 不应删除用户项目中的 HTML/CSS、Playwright 安装、候选证据目录或通用 GSAP/设计 Skill；这些资源需要单独确认。

## 最近维护

2026-08-14：首次创建，采用“多候选视觉探索 → 截图比较 → 用户选择 → 定点落地”流程，不要求提前确定审美方向；记录无需显式点名的全局自动触发规则，以及维护、验证和安全删除步骤。
