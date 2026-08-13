# DeepSight Skill — 多模态能力补偿

## 解决什么问题

当前模型/Agent 缺少原生多模态能力、或无法直接访问视觉输入时，
本 Skill 自动介入，通过 DeepSight 总控台将图片与 PDF 内容转换为
结构化分析结果，使纯文本模型也能"看见"图片、图表和 PDF 页面。

## 自动触发条件

- 用户要求读取、识别、解释图片内容（照片、截图、图表、公式）
- 用户要求读取 PDF 文本或分析 PDF 中的图表/扫描页/版面
- 当前模型是纯文本模型，缺少原生多模态能力
- 图片/PDF 附件读取失败，模型只能看到占位信息

已在具备原生多模态能力的模型中默认不激活（除非用户明确要求）。

## 触发失败根因与证据完整性规则（F.2.8）

**背景**：一次黑盒验收中，纯文本模型的原生图片 Read 失败两次后，没有自动加载本
Skill，而是旁路 `ls` 同目录、读取 `SCENARIOS.json` 与生成脚本 `generate_f27.py`，
再用 Pillow 逐像素脚本反推答案。关键事实虽然答对，但这不是"自动触发通过"，且破坏
验收完整性。

**根因**：SKILL.md 的 frontmatter `description` 是主要自动触发机制，但原描述对
"原生读取失败后必须改用本 Skill"的强制性不足，缺少对"同目录答案文件/像素脚本旁路"
的显式禁止；Claude 用户级 CLAUDE.md 只有 agent-memory bootstrap，没有多模态路由兜底。

**规则（正文 fallback gate，低自由度强制）**：

- 原生视觉读取失败一次或声明无法展示后，立即调用 `invoke-deepsight`，
  不得重复转换格式或再次尝试原生 Read。
- 禁止扫描/读取目标同目录的 SCENARIOS、manifest、README、生成/校验脚本、
  sidecar、缓存、答案清单等可能泄露答案的文件来推断视觉内容。
- 禁止用 Pillow / OpenCV / 像素颜色脚本替代语义视觉调用。
- 机械读取文件存在/格式/尺寸仅用于诊断，不得作为视觉问题的答案。
- 图片/PDF 最终答案必须来自 DeepSight 实际结果或明确失败；失败就报告失败，不旁路猜测。

## 调用器结构

```text
~\.skills-manager\skills\azf-deepsight\
├── SKILL.md              # Skill 定义（本文件的同级文件）
├── local-config.json     # 本地配置（安装时生成，不提交 Git）
└── scripts\
    └── invoke-deepsight.ps1  # 稳定跨目录调用入口
```

- `invoke-deepsight.ps1`：从 `local-config.json` 读取项目根，
  使用 `uv run --project <root> deepsight` 调用 CLI，不依赖 PATH。
- 所有 Skill 命令均通过该脚本转发，确保从任意目录均可执行。

## Skills Manager 与宿主入口关系

- **Skills Manager**：`~\.skills-manager\skills\azf-deepsight` — Skill 真实副本
- **Claude Code 入口**：`~\.claude\skills\azf-deepsight` — 当前拓扑为父级 Junction
  继承（`~\.claude\skills` → `~\.skills-manager\skills`），即两个路径指向同一物理目录。
- **其他宿主**：只需将 SKILL.md 集成到对应 Agent 的 Skill 发现路径，
  命令统一通过 `invoke-deepsight.ps1` 调用。

## 更新方法

1. 更新仓库源码：`integrations/shared/azf-deepsight/`
2. 运行安装脚本：
   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\install-claude-skill.ps1" -Force
   ```
3. 验证：
   ```
   powershell -NoProfile -ExecutionPolicy Bypass -Command '& "$env:USERPROFILE\.skills-manager\skills\azf-deepsight\scripts\invoke-deepsight.ps1" @args' status
   ```

Skill 中统一使用这条 `-Command` + `@args` 模板：外层单引号阻止 Claude Code 的 Bash
提前展开 PowerShell 的 `$env:USERPROFILE`，参数仍以独立 argv 转发。不要改写成
`-File "$env:USERPROFILE\..."`；该写法在 Bash 宿主中会把 `$env` 当作 Bash 变量，
导致首次命令以无效路径退出并诱发宿主重试。

## 失败停止闸门与内部重试的边界（F.2.9）

**背景**：一次真实前向黑盒验收中，自动路由成功（Read → Skill → invoke-deepsight
vision analyze），但无标签图片的语义结果失败：首次调用约 300 秒后 ModLens 超时；
随后宿主（Claude）违规再次调用 invoke-deepsight，并在持续超时后试图把图片 base64
后直连 Ollama `/api/generate`。纯文本健康探针仍约 7.5 秒返回，说明不是 Ollama 整体
宕机，更符合视觉请求超时/后台生成排队。

**根因**：SKILL.md 只规定了"原生读取失败后立即调用 invoke-deepsight"，但没有规定
"DeepSight 自身失败后宿主必须停止"——宿主在首次失败后自行重试、换 prompt、甚至绕过
DeepSight 直连 provider，破坏失败语义与验收完整性。

**规则（低自由度失败停止闸门，F.2.9.1 修正后语义）**：

- 每个选中的路由步骤 / 答案命令最多执行一次，失败后宿主不得再次尝试该步骤；
  禁止的是同一路由步骤失败后的宿主重试，不是必要的不同路由步骤。
- 普通绝对路径图片：`vision analyze` 是最多一次的唯一答案步骤。
- PDF：`pdf inspect` 最多一次；inspect 成功后只选一个答案命令（read/search/analyze-page）
  最多一次；`pdf render` 仅当用户明确只需渲染文件才是答案命令；任一步失败即停止。
- Claude paste 无路径：`recover-paste` 最多一次；`--analyze` 已产答案则不再 analyze；
  仅恢复路径成功则随后 `vision analyze` 最多一次。
- 命令非零、timeout、result=null、所有 attempts ok=false、输出明确失败/不可用，
  任一即最终失败。
- 失败后立即停止并简短报告 + 建议；不得用更短 prompt / 不同命令 / 不同 profile 再试。
- 不得直连 Ollama `/api/generate`、`/v1/chat/completions` 或任何 provider endpoint/API；
  不得手写 base64 请求、直接调用 ModLens、读取缓存答案、调用其他视觉模型/宿主工具绕过。
- `status` / `doctor` 只做不产生答案的诊断；诊断后同一请求仍不得重试视觉。

**内部 retry once 与宿主每个路由步骤只一次的区别**：

- DeepSight 内部（VisionService/ModLensAdapter）对可重试错误（schema mismatch、
  non-JSON、no-content）最多重试一次（首次 + 1 次重试 = 总调用最多 2 次），
  这是 DeepSight 自身实现的 schema 恢复机制，由 DeepSight 内部管理。
- 宿主层面对每个选中的路由步骤 / 答案命令只允许发起一次（图片：vision analyze 一次；
  PDF：inspect 一次 + 一个答案命令一次；paste：recover-paste 一次 + 必要时 vision analyze 一次），
  不得把"内部重试"当作"宿主可以再调一次"的依据；内部重试对宿主透明，不算宿主重试。

**F.2.9.1 Codex 审查追修 — 修正失败停止闸门与合法多步骤路由冲突**：

- 初版把"每次视觉请求最多调用一次 invoke-deepsight"写为笼统闸门，误伤了已验收的
  PDF `inspect → analyze-page` 合法链路与 Claude paste `recover-paste → analyze` 链路。
- 修正语义：禁止的是同一路由步骤/答案命令失败后宿主再次尝试，而非禁止必要的不同路由步骤。
- 图片、PDF、paste 的精确规则见上方"规则（F.2.9.1 修正后语义）"。

## 最新维护

- 最后更新：2026-08-13（最终黑盒追修：调用模板改为跨 PowerShell/Bash 安全的 `-Command` + `@args`，避免宿主变量预展开导致错误重试）
- 实现提交：待提交
- 拓扑类型：parent_junction（`.claude\skills` → `.skills-manager\skills`）
- 总控台地址：`http://127.0.0.1:8765`
