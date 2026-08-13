# 用途

这是安钊锋的本地文献阅读 Personal Skill。它封装 Zotero 元数据核对、中文短标题命名、本地 Docker MinerU、忠实中文全文、库外运行记录、可选精读/图表/问答、中央扫盲班和质量门。

中央扫盲班当前确认目录是：

```text
E:\software\Obsidian\安钊锋的外置大脑\02-Brain Cells\99_扫盲班
```

这个目录本身就是概念卡目录，只放概念卡 Markdown。Skill 不得在里面创建 `入口和索引/`、`概念卡/`、Base、领域、主题或状态子文件夹；如果以后需要索引视图，应放在该目录之外。

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
英文论文使用 `【原文】中文短标题.pdf`、`【MinerU原文】中文短标题.md`、`【总览】中文短标题.md`、`【中译】中文短标题.md` 和逐句审计。
中文论文使用同样命名的 PDF、总览和 `【中译】`；MinerU 正文直接合并进 `【中译】`，库内不另留 MinerU Markdown，并将中译审计标记为不适用。
`【总览】` 和 `【中译】` 是默认主阅读笔记。`【精读】`、`【图表】`、`【问答】` 只有在用户明确要求时才生成。
Vault 内指向笔记、PDF、图片和其它附件的 Wikilink 全部使用短文件名，不在前面加文件夹路径，也不写 `../`、`/` 或 `\`。写入前先确认目标文件名在整个 Vault 中唯一；发生冲突时给生成资产增加论文短标题等稳定前缀。库外审计 JSON 中的工作区相对文件系统路径继续保留，因为它们不是 Wikilink。

# 中译脚注

正文参考文献标号使用 Obsidian 原生 / Tidy Footnotes 兼容的数字脚注格式：`[1]` 转为 `[^1]`，`[2,3]` 转为 `[^2][^3]`，定义直接替代文末参考文献列表，标题仍叫 `# 参考文献`。处理范围按排除区判断：作者/机构区、通讯作者区、摘要前元信息、参考文献区、已生成脚注定义区和公式块内部不动；`# 摘要` / `# Abstract` 默认纳入处理。正式笔记中不保留 `<!-- azf-footnotes:... -->` 可见托管注释，也不生成 `azf-ref` 长命名脚注锚点。

常用命令：

```powershell
.\scripts\run_workflow.ps1 optimize-translation-footnotes --workspace <论文工作区>
.\scripts\run_workflow.ps1 optimize-translation-footnotes --workspace <论文工作区> --apply --backup-root <库外备份目录>
.\scripts\run_workflow.ps1 optimize-translation-footnotes --all-translations
```

写入前必须已经完成两轮位置确认。


# 表格 LaTeX/OCR 乱码防复发

表格里的缩写、标签、Yes/No、百分比和算法名默认是普通文本。典型如 `SPM + P.L.`、`SPM + N.L.`、`Yes*`、`64 × 64`，不要因为 MinerU 误识别成 `\mathbf`、`\boldsymbol` 或 `\mathsf` 就保留为公式。真公式才保留 LaTeX；表格区 MinerU 与 PDF 不一致时以 PDF/截图为准，无法确认就标记人工复核。

质量门会提示 `\mathbf { S P M }`、`\boldsymbol { \Upsilon }`、`\mathsf { e s }`、`$. 6 4 \times 6 4` 等典型表格 OCR/LaTeX 乱码。

# 库内与库外分工

Obsidian 单篇工作区只保留面向人的 Markdown、已复核正式图片、唯一的短标题 PDF，以及英文论文所需的 `【MinerU原文】`。质量报告、来源锚点、翻译审计、解析缓存和日志全部放在已确认的库外目录：

```text
output/
├── index.json
└── YYYYMMDD_HHMMSS__doi-slug/
    ├── run-manifest.json
    ├── state/
    ├── parser/
    └── logs/
```

`index.json` 分别记录最新尝试和最新成功运行。失败、调试和迁移运行永久保留，但不会覆盖最新质量验收成功结果。质量门全部通过后，`validate-pilot` 才会提升当前运行。

旧布局迁移默认只预演：

```powershell
.\scripts\run_workflow.ps1 migrate-core-layout <工作区...>
.\scripts\run_workflow.ps1 migrate-core-layout <工作区...> --apply --backup-root <库外回滚目录>
```

迁移只归档 `阅读工作台` 下文件名精确以 `【问答】`、`【图表】`、`【精读】` 开头的 Markdown；其它用户自建笔记不动。写入前检查哈希、目标冲突和入链，库内旧 JSON 验证后迁到外部 `artifact_root`。

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

# Zotero 输出后端

安装并启动 Zotero Research Database 插件后，质量验收通过的论文可以把 MinerU 原文和中译 Markdown 交付到对应 Zotero 父条目。命令默认只预演，不会连接 Zotero：

```powershell
python -X utf8 -m workflow.cli deliver-zotero-artifacts --workspace <论文工作区>
python -X utf8 -m workflow.cli deliver-zotero-artifacts --workspace <论文工作区> --apply
```

本机令牌从环境变量 `ZOTERO_RESEARCH_DB_TOKEN` 或以下不参与同步的文件读取：

```text
C:\Users\anzhaofeng\.config\azf-literature-reading-workflow\zotero-research-db-token
```

命令只接受 `validate-pilot` 已通过并提升为 `latest_successful` 的运行。英文论文交付 `【MinerU原文】` 与 `【中译】`，中文论文交付已经合并 MinerU 正文的 `【中译】`；插件按“角色＋SHA-256”去重。

若本次从开始就选择 Zotero 作为唯一长期阅读后端，可在核对 dry-run 后使用：

```powershell
python -X utf8 -m workflow.cli deliver-zotero-artifacts --workspace <论文工作区> --apply --retire-workspace
```

只有 Zotero 确认全部产物已经导入或内容未变后，工作区才会从 Obsidian 移到库外 `<artifact_root>/<run-id>/zotero-delivered-workspace/`，并写入 `zotero-delivery.json`。这是可恢复归档，不是永久删除；已有必须继续在 Obsidian 使用的人工笔记时不要启用该选项。

# 维护

项目源码修改后，从正式项目运行：

```powershell
python -X utf8 scripts/package_skill_runtime.py
```

打包脚本只更新 `scripts/runtime/`，不会覆盖本机位置注册表。

## Skill 更新同步契约

安装版 `SKILL.md` 是执行事实源，但只要更新涉及默认产物、文件命名、中英文来源分支、位置角色、库内/库外边界、可选阶段、迁移规则或质量门，就不能只改 Skill。必须同时：

1. 更新 `SKILL.md` 和本 README，并检查 `agents/openai.yaml` 是否仍匹配。
2. 从 agent-memory 定位并校验文献工作流源项目，同步根 README、核心 plan/spec/quickstart/data-model、paper-workspace/workflow-commands 契约、requirements checklist、operator runbook、translation fidelity，以及受影响的当前交接文档。
3. 更新 `E:\software\Obsidian\agent-memory\vault\项目\文献阅读工作流.md` 的稳定规则和 `verified_at`。`tasks.md`、research、Pilot 总结等历史记录只追加“已被新契约覆盖”的说明，不改写历史事实。
4. 搜索旧默认命名、库内状态 JSON、把可选笔记写成默认产物、以及把高清图提取和 `【图表】.md` 错误绑定的残留。
5. 运行 scoped diff/BOM 检查、Skill 自检和 runtime 测试；记忆写回后运行 agent-memory check、向量索引和 closeout。未经明确要求不提交 Git。

只有以上同步全部完成，才能报告一次会改变执行契约的 Skill 更新已完成。纯 runtime bug 修复如果确实不改变用户可见契约，可以不改整套文档，但仍要验证这一判断并运行对应测试。

# 最近维护

- 2026-07-31：增加 Zotero Research Database 输出后端；仅交付 `latest_successful`，令牌本机保存，角色＋哈希幂等；显式 `--retire-workspace` 可在完整确认后把 QA 工作区可恢复地移到库外，避免维护第二套长期数据库。
- 2026-07-28：取消旧的“附件可保留路径”例外；所有 Vault 内部 Wikilink 统一使用短文件名，运行时生成器、迁移器、全库同名歧义检查和质量门同步执行该规则；同时修正高清图 Skill 的 `azf-` 规范目录发现；内置测试 `53 passed`。
- 2026-07-28：新增 Skill 更新同步契约；以后执行契约变化必须同步源项目执行性 Markdown 和 agent-memory，避免安装版 Skill 已更新但旧方案仍驱动执行。
- 2026-07-24：统一中文短标题命名；英文默认四件核心物料，中文 MinerU 直接合并到 `【中译】`；默认停止生成精读/图表/问答；库内 JSON 全部迁往外部并完整保留 parser/log；增加旧辅助笔记精确前缀归档、回滚备份和重命名后源哈希恢复校验。
- 2026-07-17：增加首版 `en/zh` 分支与工作区相对路径（其中“中文独立原文笔记”方案已被 2026-07-24 契约取代）。
- 2026-07-18：清理旧的论文阅读专用路由；保留论文级独立精读和翻译完整性审计。
- 2026-07-18：引入库外 `ArtifactRun`、永久运行历史和显式 promote；Obsidian 单篇工作区不再保存 JSON、缓存或日志。
- 2026-07-20：中央扫盲班改为平铺概念卡目录，`99_扫盲班` 根目录只放概念卡，不再生成入口、Base 或 `概念卡/` 子文件夹。
- 2026-07-20：纠正中译脚注优化方向；按“排除区模型”处理正文参考文献标号，摘要默认纳入，作者/机构/通讯作者和参考文献定义区不动；输出 Obsidian 原生 / Tidy Footnotes 兼容的 `[^1]` 数字脚注，定义直接放在 `# 参考文献` 下，不再生成 `# 参考文献脚注`、`azf-ref` 长锚点或可见 HTML 托管标记。
- 2026-07-20：新增 SHG-FROG 表格 LaTeX/OCR 乱码防复发规则；表格普通文本不自动 LaTeX 化，质量门提示典型坏模式。
