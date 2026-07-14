# 用途

这是安钊锋的本地文献阅读 Personal Skill。它封装 Zotero 元数据核对、本地 Docker MinerU、高清图表、逐句忠实中译、独立精读、中央扫盲班和质量门。

# 强制两轮

第一轮只定位：

```powershell
.\scripts\run_workflow.ps1 locate
```

Agent 必须展示 Obsidian 库、论文根目录、中央扫盲班和模板位置，然后停止。

用户确认后进入第二轮：

```powershell
.\scripts\run_workflow.ps1 confirm-locations
.\scripts\run_workflow.ps1 doctor --strict
```

写入命令没有确认清单时会拒绝执行。文件夹移动或工作区越界时也会停止并要求重新定位。

Zotero 回跳只写 `Zotero PDF链接: "zotero://open-pdf/library/items/{PDF附件键}"`；不要生成 `Zotero条目链接`。

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