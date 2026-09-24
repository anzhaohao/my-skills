# Scientific Illustrator

## 这个 skill 解决什么问题

把一张现成的科研插图（论文图、graphical abstract、流程图、多面板示意图等）作为参考图上传，让 agent 在 **Microsoft PowerPoint、WPS 演示或 draw.io** 里用可编辑对象（文字、形状、连接线、表格、图表）重新绘制一份，并自动做结构检查、对比审查和修正，而不是只给你一张不可编辑的位图。

## 什么时候应该触发

- 需要"照着这张图重画一份可编辑的"科研插图时
- 需要把论文里的示意图做成 PPT 可编辑版本用于汇报时
- 多面板图、机制图、工作流图需要矢量化重建时

## 来源与结构

- 上游项目：<https://github.com/icebird1998/scientific-illustrator>（作者：一个地质博士，MIT 许可证）
- 2026-09-01 从上游 v1.5.4（main 分支）复制 `plugins/scientific-illustrator/` 完整内容安装到本目录
- 本目录是 Skills Manager 里的真实目录（符合"技能本体在 Skills Manager"的约定）；`.claude/skills` 整体是指向 Skills Manager 的链接，Claude Code 会自动发现本目录下的 6 个子 SKILL.md
- 根目录的 `SKILL.md` 是为 Skills Manager 安装补的路由入口；6 个子技能在 `skills/` 下：`recreate-scientific-figure`（总入口）、`recreate-scientific-figure-in-drawio`、`edit-powerpoint-live`、`design-scientific-figure`、`audit-scientific-figure`、`correct-scientific-figure`

## 关键事实与限制

- 本项目原生是 **Codex 插件**（`.codex-plugin/` + `.mcp.json` 里的三个 MCP server：`drawio-live`、`drawio-file-utils`、`powerpoint-live`，均为 Node `.mjs` 脚本）。**2026-09-01 已在 Claude Code 完成注册**：用 `claude mcp add --scope user` 注册为 user 级 MCP server（命令 `node <本目录>\scripts\<server>.mjs`），`claude mcp list` 验证三个均 Connected。server 只用 Node 内置模块，无 npm 依赖。
- DSH（Hana Agent 内嵌）侧**未接入**这些 MCP：DSH 自有插件机制（如 dsh-image-gen 走 tarball 部署），与 Claude Code MCP 是两套体系，上游也没有 DSH 适配。要在 DSH 里用需另做开发。
- 上游 README 中的 Codex 专用提示词（`plugin://scientific-illustrator@...` 前缀）在 Claude Code 中无效，用自然语言描述需求即可。
- 运行依赖：Node.js；按后端需要 draw.io Desktop / Microsoft PowerPoint / WPS 演示。
- 更新方式：重新从上游仓库复制 `plugins/scientific-illustrator/` 覆盖本目录（保留根目录的 SKILL.md 和本 README）。

## 最近一次维护

- 2026-09-01（claude-code）：首次安装到 Skills Manager 默认位置，来源为上游 v1.5.4；补充了路由入口 SKILL.md 与本 README；同日将三个 MCP server 注册为 Claude Code user 级（`claude mcp list` 验证通过），并更新顶层技能目录清单至 76 条。
