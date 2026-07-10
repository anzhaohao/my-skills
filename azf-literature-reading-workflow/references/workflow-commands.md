# CLI 调用

工作流运行时已经内置在 Skill 的 `scripts/runtime/`，不需要切换到外部项目目录。

默认新解析流程：

```powershell
scripts\run_workflow.ps1 doctor --strict
scripts\run_workflow.ps1 parse-with-mineru --workspace <workspace> --mode docker-run
```

只有用户明确说明已有 MinerU 结果时，才先审计后复用：

```powershell
scripts\run_workflow.ps1 doctor --strict --reuse-existing
scripts\run_workflow.ps1 parse-with-mineru --workspace <workspace> --mode existing
# 或显式指定已审计材料：
scripts\run_workflow.ps1 parse-with-mineru --workspace <workspace> --mode reuse --reuse-markdown <md> --reuse-raw-output <json>
```

其余主要命令：

```powershell
scripts\run_workflow.ps1 ingest-paper ...
scripts\run_workflow.ps1 layout-sanity-check ...
scripts\run_workflow.ps1 extract-highres-figures ...
scripts\run_workflow.ps1 generate-zh-fulltext --translated-note ... --translation-audit ...
scripts\run_workflow.ps1 generate-deep-reading ...
scripts\run_workflow.ps1 validate-pilot ...
```

自检：

```powershell
python -X utf8 scripts\self_test.py
scripts\test_runtime.ps1
```

不要并行运行会更新同一个 `quality-report.json` 的命令。