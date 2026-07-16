这是安钊锋的论文周报生产编排 Skill。它调用已安装的 `paper-weekly` CLI，负责权限检查、命令映射、质量门禁、计划任务检查和精读交接，不保存数据库、日志、密钥或生产配置副本。

# 适用场景

- 验证或预演项目内纯 YAML 生产配置。
- 生成上一完整 ISO 周、指定周或明确选择的不连续补跑周次。
- 校验既有周报和重复运行的幂等性。
- 维护项目内 Git 忽略的中科院升级版期刊分区 XLSX，并核验分区评分证据。
- 用户明确要求时，先外部备份并删除唯一旧周报，再用仍保持 `skip` 的正常流程安全重建。
- 检查 `AZF Paper Weekly` Windows 计划任务。
- 启动 Tkinter 配置管理器，在 Git 忽略目录维护并切换多个主题/模型配置。
- 切换 Ollama、LM Studio、llama.cpp、vLLM、LocalAI、Xinference、自定义本地模型、官方云 API或第三方中转站。
- 用户从周报选中论文后，交接既有两轮文献阅读工作流。

# 默认事实

- 生产配置：`D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260715-ai-paper-weekly\config\paper-weekly.production.local.yaml`。
- 生产 Python：`E:\software\Anaconda\envs\20260715-ai-paper-weekly\python.exe`。
- 计划任务：`AZF Paper Weekly`，周一 09:00。
- 正式模板仍只从 Obsidian 原路径读取，Skill 不复制模板。
- 模型 API Key 默认直接写入被 Git 忽略的唯一生产 YAML；`api_key_env` 仅保留旧配置兼容。Skill 不显示或复制密钥。
- 期刊分区数据：项目内 `data/local/journal-rankings/`，不复制进 Skill 或 Git；当前使用中科院升级版 2025 本地副本。

# 模型边界

通用本地运行时使用 `openai_compatible`，Ollama 原生 `/api/chat` 使用 `ollama_native`。程序不直接加载 GGUF 或 safetensors；先由本地运行时暴露 HTTP 接口。私有局域网 HTTP 需要显式开启 `允许不安全HTTP`，公网接口始终要求 HTTPS 和直接或兼容密钥。

# 最近维护

- 2026-07-16：增加本地中科院升级版 2025 分区数据门禁、5 分期刊权重、精确匹配证据检查；增加“当前请求明确授权后，项目外备份并删除唯一旧周报再重建”的受控流程，CLI 冲突策略仍固定为 `skip`。

- 2026-07-16：默认生产配置从 Obsidian Markdown 迁移到项目内 Git 忽略的纯 YAML；新增 Ollama 原生与多种 OpenAI-compatible 本地自定义模型接法，并保留旧 frontmatter 兼容。
- 2026-07-16：按最新决定允许模型 API Key 直接明文写入唯一生产 YAML；增加 `SecretStr` 遮蔽、不序列化和错误防泄露规则，不创建额外 `.env` 文件。
- 2026-07-16：增加 Windows Tkinter 配置管理器和 Git 忽略的 `config/profiles/`；档案严格验证后原子切换，计划任务自动识别 Ollama/云端模式。
- 2026-07-16：增加项目根目录中文 CMD 一键启动器，双击即可打开配置管理器，无需手动进入 PowerShell。
