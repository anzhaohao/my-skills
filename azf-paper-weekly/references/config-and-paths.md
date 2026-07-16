# 配置、路径与命令

## 当前生产路径

- 项目：`D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260715-ai-paper-weekly`
- Conda Python：`E:\software\Anaconda\envs\20260715-ai-paper-weekly\python.exe`
- 生产配置：`D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260715-ai-paper-weekly\config\paper-weekly.production.local.yaml`
- 正式模板：`E:\software\Obsidian\安钊锋的外置大脑\05-Junk Drawer\2_模板\2.0 Default template\论文周报模板.md`
- 周报根目录：`E:\software\Obsidian\安钊锋的外置大脑\02-Brain Cells\98_论文周报`
- 运行目录：`%LOCALAPPDATA%\paper-weekly`
- 数据库：`%LOCALAPPDATA%\paper-weekly\paper-weekly.db`
- 日志：`%LOCALAPPDATA%\paper-weekly\logs`
- 计划任务包装脚本：`D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260715-ai-paper-weekly\scripts\run-scheduled.ps1`
- 配置管理器：`D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260715-ai-paper-weekly\scripts\open-config-manager.ps1`
- 一键启动器：`D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260715-ai-paper-weekly\启动论文周报配置管理器.cmd`
- 配置档案：`D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260715-ai-paper-weekly\config\profiles\*.local.yaml`，整个目录被 Git 忽略
- 本地期刊分区：`D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260715-ai-paper-weekly\data\local\journal-rankings\2025中科院分区表完整版（附2023vs2025对比版）.xlsx`，整个 `data/local/` 被 Git 忽略

路径可能由用户迁移。实际执行前先检查存在性；不要在 Skill 内复制配置或模板。含 Key 的档案复制只能由用户在配置管理器中明确触发，目标只能是被忽略的 `config/profiles/`。

生产配置是纯 YAML，可用 Windows 记事本编辑；推荐 UTF-8 无 BOM，加载器兼容 UTF-8 BOM。旧 `.md`/`.txt` YAML frontmatter 只用于向后兼容，不再作为生产事实源。

## 模型配置

当前生产模型可能由配置管理器切换，不要依赖 Skill 内的历史模型名。每次先运行 `config model-info`，只使用其不含密钥的 provider、model、Base URL 和 `requires_local_ollama` 结果。

## 本地期刊分区

- 配置段为 `期刊评价`；当前年份 2025。
- `config validate --json` 必须报告 `records: 21770`、`ambiguous_names: 1` 且 `journal_ranking_issues` 为空。
- 1至4区分别加 5、4、2.5、1 分；未收录、预印本和名称歧义为 2.5 分中性值。
- 只做 Unicode NFKC、大小写、标点、空格、连字符与 `&/and` 规范化后的精确匹配，不做模糊匹配。
- 来源说明使用“经官网抽样核验的中科院升级版2025数据副本”；不要声称 XLSX 是可证明的官网原始导出。
- 不读取学校账户、不联网查询官网，也不把 XLSX 复制进 Skill、备份仓库或聊天。

官方云 API 示例位于项目的 `examples/model.cloud-openai-compatible.yaml`；第三方中转站示例位于 `examples/model.third-party-relay.yaml`。远程接口必须：

- 使用 HTTPS。
- 把真实密钥直接写入被 Git 忽略的生产 YAML `API密钥`；`api_key_env` 只作旧配置兼容，二者不能同时配置。
- 使用厂商或中转站提供的准确模型 ID 与 Base URL。
- 填写实际 token 单价和正数费用上限；示例的上限 `0` 是防误调用安全锁。
- 不显示、复制、备份或逐行读取含真实密钥的生产配置；只检查字段是否非空和 Git 忽略状态。

本地和自定义模型：

- Ollama、LM Studio、llama.cpp server、vLLM、LocalAI、Xinference 等兼容接口使用 `provider: openai_compatible`。
- Ollama 原生 `/api/chat` 使用 `provider: ollama_native`；`思考强度: none` 映射为 `think: false`。
- 本机回环地址允许 HTTP 且密钥可空；私有局域网 HTTP 要显式设置 `允许不安全HTTP: true`，公网始终强制 HTTPS 并要求直接或兼容密钥。
- 自定义 GGUF、safetensors 或模型目录必须先由上述运行时加载；`paper-weekly` 不直接打开模型文件。
- 示例位于 `examples/model.local-openai-compatible.yaml` 和 `examples/model.local-ollama-native.yaml`。

## 安全命令映射

调用 Skill 脚本：

```powershell
$Config = "D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260715-ai-paper-weekly\config\paper-weekly.production.local.yaml"
& "<Skill目录>\scripts\paper-weekly.ps1" -Operation config-validate -ConfigPath $Config
& "<Skill目录>\scripts\paper-weekly.ps1" -Operation production-preview -ConfigPath $Config
& "<Skill目录>\scripts\paper-weekly.ps1" -Operation model-info -ConfigPath $Config
& "<Skill目录>\scripts\paper-weekly.ps1" -Operation scheduled-dry-run -ConfigPath $Config
& "<Skill目录>\scripts\paper-weekly.ps1" -Operation validate -Week 2026-W28 -ConfigPath $Config
& "<Skill目录>\scripts\paper-weekly.ps1" -Operation generate -Week 2026-W28 -ConfigPath $Config -ConfirmProductionWrite
& "<Skill目录>\scripts\paper-weekly.ps1" -Operation backfill-preview -Weeks 2026-W24,2026-W26 -ConfigPath $Config
```

`generate`、`scheduled-run`、`backfill` 均由脚本强制要求 `-ConfirmProductionWrite`。
也可以设置 `PAPER_WEEKLY_CONFIG`，此时脚本可省略 `-ConfigPath`。

## 计划任务

- 名称：`AZF Paper Weekly`
- 计划：每周一 09:00，Windows 本地时区。
- 设置：`StartWhenAvailable`、`IgnoreNew`、最长 2 小时、当前交互用户、受限权限。
- 任务可持续保留 `-EnsureOllama`。包装脚本会调用 `config model-info`；只有本机 Ollama 配置才做健康检查，其他本地运行时和云端/中转站自动跳过。
