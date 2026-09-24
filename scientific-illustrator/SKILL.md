---
name: scientific-illustrator
description: 把参考图复刻为可编辑的科研插图（Microsoft PowerPoint、WPS 演示或 draw.io）。上传 PNG/JPEG/SVG/PDF 参考图后，按 Designer → Drawer → Reviewer → Corrector 四角色流程逐区域重建为可编辑对象。这是本插件的路由入口，实际流程见 skills/ 下的子技能。
---

# Scientific Illustrator（路由入口）

本 skill 是 [icebird1998/scientific-illustrator](https://github.com/icebird1998/scientific-illustrator) 插件在 Skills Manager 中的安装副本，按 Skills Manager 惯例以真实目录形式存放在 `C:\Users\anzhaofeng\.skills-manager\skills\scientific-illustrator`。

## 子技能（本目录 skills/ 下）

- `recreate-scientific-figure` — 总入口：复刻整张科研图为可编辑插图，支持 draw.io / PowerPoint / WPS
- `recreate-scientific-figure-in-drawio` — draw.io 后端适配
- `edit-powerpoint-live` — PowerPoint / WPS 后端适配
- `design-scientific-figure` — Designer 角色
- `audit-scientific-figure` — Reviewer 角色
- `correct-scientific-figure` — Corrector 角色

## 运行依赖

- Node.js（MCP 服务与脚本均为 `.mjs`）
- 本目录 `.mcp.json` 定义了三个 MCP server：`drawio-live`、`drawio-file-utils`、`powerpoint-live`，`cwd` 均为本目录（相对路径）。要让 MCP 生效，需在本目录或包含它的上下文中注册这些 MCP server（Claude Code 中可配置为本地 MCP server）。
- draw.io Desktop、Microsoft PowerPoint 或 WPS 演示（按所选后端）
- Mac PowerPoint 实时模式需额外的 officejs 证书与加载项配置（见上游 README）

## 使用提示

上传参考图后，明确指定目标软件（PowerPoint / WPS / draw.io），让 `recreate-scientific-figure` 编排即可。上游 README 的 Codex 专用提示词（含 `plugin://` 前缀）不适用于 Claude Code，直接使用自然语言描述即可。
