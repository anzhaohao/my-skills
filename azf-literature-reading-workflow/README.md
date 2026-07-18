# 用途

这是安钊锋的本地文献阅读 Personal Skill。它封装 Zotero 元数据核对、本地 Docker MinerU、高清图表、逐句忠实中译、独立精读、中央扫盲班和质量门。

# 强制两轮

第一轮只定位：

```powershell
.\scripts\run_workflow.ps1 locate
```

Agent 必须展示 Obsidian 库、论文根目录、中央扫盲班、模板和库外 `artifact_root` 五个位置，然后停止。

用户确认后进入第二轮：

```powershell
.\scripts\run_workflow.ps1 confirm-locations
.\scripts\run_workflow.ps1 doctor --strict
```

写入命令没有确认清单时会拒绝执行。文件夹移动或工作区越界时也会停止并要求重新定位。

Zotero 回跳只写 `Zotero PDF链接: "zotero://open-pdf/library/items/{PDF附件键}"`；不要生成 `Zotero条目链接`。
英文论文使用 `MinerU英文全文.md`、`【中译】...md` 和逐句审计；中文论文使用 `MinerU中文全文.md`、`【原文】...md`，并将中译标记为不适用。
总览属性区的 `中文全文` 对英文链接到中译笔记，对中文链接到中文原文笔记。
库内笔记引用使用短 wikilink，不在前面加文件夹路径；附件和资源链接按需要保留路径。

工作区移动后先运行只读检查，再明确应用：

```powershell
.\scripts\run_workflow.ps1 repair-workspace-paths <工作区...>
.\scripts\run_workflow.ps1 repair-workspace-paths <工作区...> --apply
```

该命令检查当前外部运行目录，修复外部 JSON 到库内 PDF、MinerU Markdown、正式图片和笔记的跨根路径，并同步运行清单中的工作区绑定；不改人工 Markdown 或 Zotero 地址。

# 库内与库外分工

Obsidian 单篇工作区只保留 Markdown、已复核正式图片，以及唯一的 `附件/原文/原文.pdf`。质量报告、来源锚点、翻译审计、解析缓存和日志全部放在已确认的库外目录：

```text
output/
├── index.json
└── YYYYMMDD_HHMMSS__doi-slug/
    ├── run-manifest.json
    ├── state/
    ├── parser/
    └── logs/
```

`index.json` 分别记录最新尝试和最新成功运行。失败运行永久保留但不会覆盖最新成功结果。命令可用 `--artifact-id` 指定历史运行；不指定时读取总览或索引中的最新成功运行。质量门全部通过后，使用 `validate-pilot --artifact-id <id> --promote` 显式提升。

旧布局迁移默认只预演：

```powershell
.\scripts\run_workflow.ps1 migrate-artifacts <工作区...>
.\scripts\run_workflow.ps1 migrate-artifacts <工作区...> --apply --backup-root <库外回滚目录>
```

本机可变配置保存在：

```text
C:\Users\anzhaofeng\.config\azf-literature-reading-workflow
```

该目录独立于 Skill，重新打包或升级 Skill 不会覆盖已确认位置。

# 自检

```powershell
python -X utf8 .\scripts\self_test.py
.\scripts\test_runtime.ps1
```

# 维护

项目源码修改后，从正式项目运行：

```powershell
python -X utf8 scripts/package_skill_runtime.py
```

打包脚本只更新 `scripts/runtime/`，不会覆盖本机位置注册表。

# 最近维护

- 2026-07-17：增加 `en/zh` 原文语言分支、中文原文笔记与 `repair-workspace-paths`；生成状态改用工作区相对路径。
- 2026-07-18：清理旧的论文阅读专用路由；保留论文级独立精读和翻译完整性审计。
- 2026-07-18：引入库外 `ArtifactRun`、永久运行历史和显式 promote；Obsidian 单篇工作区不再保存 JSON、缓存或日志。
