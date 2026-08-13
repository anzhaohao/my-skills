---
name: azf-deepsight
description: >-
  Automatically compensates for missing multimodal capability when the model or
  agent lacks native vision, or native image/PDF reading fails or returns only a
  placeholder or metadata. Use to read, recognize, interpret, or extract image
  and PDF content. MUST be used immediately when reading a real image or PDF
  fails visually, even if the user did not mention DeepSight. Do NOT bypass with
  same-directory answer files, manifests, or pixel-color scripts. Do NOT invoke
  when native vision already handles the input reliably unless explicitly
  requested. Each selected routing step / answer command may run at most once;
  on non-zero exit, timeout, null result, or all attempts ok=false, stop and
  report failure — do NOT retry at host level or call Ollama/provider/API
  directly.
---

# DeepSight — 多模态能力补偿

## 定位

DeepSight 为缺少原生多模态能力、或无法直接访问视觉输入的模型与 Agent 补充
图片和 PDF 阅读能力。它不绑定任何特定平台、模型或供应商；Claude Code 是当前
第一个宿主适配实现。

## 何时自动激活

以下任一条件满足时，Agent 应自动使用本 Skill：

- 用户要求读取、识别、解释、比较或提取图片内容（照片、截图、图表、公式）；
- 用户要求读取 PDF 文本，或分析 PDF 中的扫描页、图表、公式、图片、表格或版面；
- 当前模型是纯文本模型，缺少原生多模态能力；
- 当前 Agent 无法直接访问、解码或理解该视觉输入；
- 图片/PDF 附件读取失败，或模型只能看到占位信息而非真实文件内容；

以下情况默认**不**激活：

- 当前模型已经能够直接、可靠地处理该视觉输入，且用户未明确要求使用 DeepSight；
- 用户只是提及"图片"或"PDF"但无实际文件需要处理。

## 原生读取失败后的降级闸门（fallback gate，低自由度强制）

当用户要求读取实际图片/PDF 路径或附件，而当前模型或 Read 工具的原生视觉读取
失败一次、或明确声明无法展示/不支持该格式、或只能返回占位/元数据时，Agent 必须：

1. **立即调用 `invoke-deepsight`**（走下方路由规则），不得重复转换格式、再次尝试原生 Read；
2. **不得旁路推断视觉内容**：禁止扫描或读取目标文件同目录下的 SCENARIOS、manifest、
   README、生成/校验脚本、sidecar、缓存、答案清单或其他可能泄露答案的文件来推断视觉内容；
3. **禁止像素脚本替代语义视觉**：不得用 Pillow / OpenCV / 像素颜色取样脚本等机械手段
   反推图片/PDF 的语义答案；
4. **诊断与答案分离**：机械读取文件是否存在、格式、尺寸可用于诊断，但不得作为对视觉问题的答案；
5. **最终答案来源唯一**：图片/PDF 的最终答案必须来自 DeepSight 实际结果，或明确报告失败；
   若 DeepSight 失败，报告失败，不得旁路猜测或从同目录文件拼凑答案。

## 失败停止闸门（stop-on-failure gate，低自由度强制）

视觉请求一旦发起，宿主端必须遵守以下硬性闸门，DeepSight 失败时不得自行绕过。本闸门禁止的是
**同一路由步骤 / 答案命令失败后由宿主再次尝试**，不是禁止必要的不同路由步骤（例如 PDF 先
`pdf inspect` 再按结果执行一个答案命令是合法链路）。

1. **每个选中的路由步骤 / 答案命令最多执行一次**：同一路由步骤或其答案命令（如 `vision
   analyze`、`pdf inspect`、`pdf read` / `pdf search` / `pdf analyze-page`、`recover-paste`）
   最多执行一次；DeepSight 内部的 schema mismatch 重试由 DeepSight 自己管理，不算宿主重试。
2. **普通绝对路径图片**：`vision analyze` 是最多一次的唯一答案步骤。
3. **PDF 合法多步骤链路**：
   - `pdf inspect` 最多一次；
   - inspect 成功后，只选择一个与用户目标匹配的答案命令（`pdf read` / `pdf search` /
     `pdf analyze-page`）并最多执行一次；
   - `pdf render` 仅当用户明确只需要渲染文件时才是答案命令；不要为了 `pdf analyze-page`
     另行手工 render（analyze-page 内部会渲染）；
   - 任一步失败即停止，不得继续下一个步骤或重跑。
4. **Claude paste 无路径**：`recover-paste` 最多一次；若 `recover-paste --analyze` 已经生成视觉答案，
   则不得再 analyze；若只恢复到路径且成功，随后 `vision analyze` 最多一次。
5. **任一失败信号即最终失败**：命令退出码非零、timeout、result 为 null、所有 attempts 的
   ok=false、或输出明确失败/不可用，任一满足即判定为最终失败。
6. **失败后立即停止**：失败后立即停止视觉流程，向用户简短报告失败与可操作建议；
   不得改用更短 prompt、不同命令或不同 profile 再次尝试，除非用户之后明确要求重新发起。
7. **禁止直连绕过**：不得直连 Ollama `/api/generate`、`/v1/chat/completions` 或任何
   provider endpoint/API；不得手写 base64 请求、直接调用 ModLens、读取缓存答案、
   或调用其他视觉模型/宿主工具绕过 DeepSight。
8. **诊断与重试分离**：`status` / `doctor` 只可用于不产生答案的诊断；诊断完成后，
   同一已失败步骤仍不得再次发起视觉调用。
9. **最终答案唯一来源**：最终答案只能来自成功的 DeepSight result；失败则报告失败，
   不得旁路猜测或拼接答案。

## 答不出自动降级（answer-fallback，服务层内建）

当某个视觉模型调用**成功**、但**明确表示没能回答**图片问题（结果中 `uncertainty`
非空，或 `summary` 含"无法识别 / 无法确定 / cannot identify"等措辞）时，
DeepSight 服务层会自动按档案优先级切换到下一个档案重试，**无需宿主手动再发一次**。

- 触发信号：`result.summary` 或 `result.uncertainty` 条目命中内置的"无法识别 / 无法确定 /
  cannot identify"措辞。仅 `uncertainty` 非空**不算**答不出（模型常把截断文字、引号样式等
  次要细节写进 uncertainty，但主体已作答）。
- 降级链：按总控台配置的 fallback 顺序进行，**跳过本地 ollama**（provider=ollama 且
  is_local=True 的档案，如 `ollama-qwen35-9b`）。
- 结果标记：`attempts[].did_not_answer` 为 `true` 表示该档案答不出；
  `warnings` 会注明"按优先级降级到 <档案>"。
- 全部可降级档案都无法回答时，返回最后一份结果并附 `warnings`；宿主应如实向用户说明
  "当前可用模型都未能回答该问题"，不得自行拼接或猜测答案。
- 关闭方式：`vision.answer_fallback=false`（默认 `true`）；`--no-fallback` 会同时禁用
  异常降级与答不出降级。
- 宿主约束：该降级由 DeepSight 服务层完成，**不算宿主重试**；宿主仍只调用一次目标命令
  （`vision analyze` / `pdf analyze-page`），读完返回即可。

## 路由规则

> **调用方式**：所有 `deepsight` 命令通过稳定调用器执行，不依赖 PATH。
> 安装脚本自动生成 `local-config.json`（项目根路径）。

### 1. 普通图片（有绝对路径）

```
powershell -NoProfile -ExecutionPolicy Bypass -Command '& "$env:USERPROFILE\.skills-manager\skills\azf-deepsight\scripts\invoke-deepsight.ps1" @args' vision analyze <image-path> [--prompt <text>] [--profile <id>] [--no-fallback]
```

- 默认使用 DeepSight 总控台中当前活动档案。
- 不硬编码任何模型、provider 或 endpoint。
- 视觉档案由用户在总控台中配置和切换。

### 2. 粘贴图片且无可用路径（仅 Claude Code 宿主）

仅当当前宿主为 Claude Code 且粘贴的图片没有可访问文件路径时：

```
powershell -NoProfile -ExecutionPolicy Bypass -Command '& "$env:USERPROFILE\.skills-manager\skills\azf-deepsight\scripts\invoke-deepsight.ps1" @args' vision recover-paste [--count N] [--session <id>] [--transcript <path>] [--cwd <path>] [--analyze] [--prompt <text>]
```

- 这是宿主特定适配能力，不是通用前置条件。
- 自动恢复：无需手工查找 transcript；DeepSight 会按 `--session` / `CLAUDE_CODE_SESSION_ID` /
  `CLAUDE_SESSION_ID` 精确定位，否则按当前目录选择最近包含可恢复图片的 Claude 会话。
- 若宿主能替换 `${CLAUDE_SESSION_ID}`，建议传 `--session ${CLAUDE_SESSION_ID}` 提升精确度；
  替换或环境变量不可用时默认自动恢复仍可用。
- 其他 Agent 宿主不需实现此功能。
- 成功恢复路径后立即使用规则 1 分析。

### 3. 电子文本 PDF

先检查 PDF 基本信息，再决定读取策略：

```
powershell -NoProfile -ExecutionPolicy Bypass -Command '& "$env:USERPROFILE\.skills-manager\skills\azf-deepsight\scripts\invoke-deepsight.ps1" @args' pdf inspect <pdf-path>
powershell -NoProfile -ExecutionPolicy Bypass -Command '& "$env:USERPROFILE\.skills-manager\skills\azf-deepsight\scripts\invoke-deepsight.ps1" @args' pdf read <pdf-path> [--dpi 200] [--pages 1-5] [--no-cache]
powershell -NoProfile -ExecutionPolicy Bypass -Command '& "$env:USERPROFILE\.skills-manager\skills\azf-deepsight\scripts\invoke-deepsight.ps1" @args' pdf search <pdf-path> <query> [--max 20] [--case] [--no-cache]
```

- 不要为了读取普通文本把每页都送入视觉模型。
- 普通电子 PDF 使用 PyMuPDF4LLM 转为 Markdown，不消耗视觉调用。
- `pdf inspect` 返回页数/字符数/每页文本状态，帮助判断是否有扫描页。
- 如果 `pdf inspect` 报告大量无文本层页面，考虑使用 MinerU（规则 5）。

### 4. PDF 指定页面 / 图表 / 扫描页 / 公式 / 版面

```
powershell -NoProfile -ExecutionPolicy Bypass -Command '& "$env:USERPROFILE\.skills-manager\skills\azf-deepsight\scripts\invoke-deepsight.ps1" @args' pdf render <pdf-path> [--page 1] [--dpi 200] [--output <path>] [--no-cache]
powershell -NoProfile -ExecutionPolicy Bypass -Command '& "$env:USERPROFILE\.skills-manager\skills\azf-deepsight\scripts\invoke-deepsight.ps1" @args' pdf analyze-page <pdf-path> [--page 1] [--prompt <text>] [--profile <id>] [--no-fallback] [--dpi 200] [--no-cache]
```

- 需要页面图像时使用 `pdf render`。
- 需要语义视觉分析（图表解读、公式识别、版面理解）时使用 `pdf analyze-page`。
- 只分析任务所需页码，避免无意义地处理整份 PDF。
- `pdf analyze-page` 将页面渲染为 PNG 后通过视觉模型分析。

### 5. 复杂 / 扫描 PDF（MinerU Docker）

```
powershell -NoProfile -ExecutionPolicy Bypass -Command '& "$env:USERPROFILE\.skills-manager\skills\azf-deepsight\scripts\invoke-deepsight.ps1" @args' mineru run <pdf-path> [--mode auto|fast|mineru] [--gpu] [--timeout 1800] [--no-cache]
powershell -NoProfile -ExecutionPolicy Bypass -Command '& "$env:USERPROFILE\.skills-manager\skills\azf-deepsight\scripts\invoke-deepsight.ps1" @args' mineru check-gpu
powershell -NoProfile -ExecutionPolicy Bypass -Command '& "$env:USERPROFILE\.skills-manager\skills\azf-deepsight\scripts\invoke-deepsight.ps1" @args' mineru status
```

- 需要 Docker Desktop 运行中 + MinerU 镜像已构建。
- `--mode auto` 自动根据文本密度判断是否使用 MinerU。
- `--gpu` 显式启用 GPU（会自动检测显存冲突）。
- Docker 不可用时自动降级为 PyMuPDF 文本提取。

### 6. 诊断

```
powershell -NoProfile -ExecutionPolicy Bypass -Command '& "$env:USERPROFILE\.skills-manager\skills\azf-deepsight\scripts\invoke-deepsight.ps1" @args' doctor
powershell -NoProfile -ExecutionPolicy Bypass -Command '& "$env:USERPROFILE\.skills-manager\skills\azf-deepsight\scripts\invoke-deepsight.ps1" @args' status
```

检查各组件状态并给出可操作建议。

## 能力判断优先级

1. 当前模型可以直接可靠处理视觉输入 → 优先使用原生能力。
2. 当前模型是纯文本模型 → 自动使用 DeepSight。
3. 附件读取失败 / 模型只能看到占位 → 自动降级到 DeepSight，不要求用户再次明确。
4. 原生读取尝试失败 → 自动使用 DeepSight，无需用户重复指令。

## 输入不足时的处理

- 已有绝对文件路径：直接处理。
- 没有路径且宿主适配器无法恢复：向用户索要路径或页码范围。
- 不猜测文件位置，不扫描用户文件系统。

## 输出规范

- 最终向用户回答图片或 PDF 本身的问题，不要只倾倒原始 JSON。
- 必要时简短注明：使用的视觉档案、页码、是否使用了视觉分析。
- 不要声称自己"直接看见"了没有实际读取的内容。
- 引用视觉分析结果时标注置信度标记（如有）。

### 识图思维链（recognition chain）必报

对图片做视觉识别时，最终回复必须给出**识图思维链**：按执行顺序说明每个节点用到的
模型及其作用，让用户看清"是谁识别出来的、中途发生了什么、为什么"。信息只来自本次
实际返回结果的 `attempts[]`（每次尝试的 provider / model / ok / did_not_answer /
error）与 `warnings`（降级原因），**不得编造节点**。

- 每个节点至少说明：使用的**模型**（档案 id 或模型名）、该节点**起到的作用**
  （初判 / 补充识别 / 兜底）、**结果**（成功回答 / 答不出 / 调用失败及其原因）。
- 发生降级时说明**触发原因**：是调用失败（non-JSON / 超时 / 鉴权等）还是答不出
  （uncertainty 命中无法识别措辞），以及跳过了哪些本地 ollama 档案。
- 只用了单个模型也须明说："本次仅用 <模型> 一步完成，无降级"。
- 示例（仅示意格式，不得照抄）：
  1. 节点1 `aliyun-qwen3-vl-flash`（初判）：输出非法 JSON，调用失败 → 降级；
  2. 节点2 `Gemini / gemini-3.6-flash`（补充识别）：成功，识别出品牌 X；
  3. 兜底：无（未再需要）。

## 安全约束

- 不读取、显示或记录 API Key、Token、Credential Manager 密钥值。
- 不修改主模型连接配置（ANTHROPIC_BASE_URL、ANTHROPIC_AUTH_TOKEN 等）。
- 不允许任意 shell 命令或用户传入 Docker 参数。
- 不删除原始图片或 PDF。
- 缓存只能操作 DeepSight 自管范围。
- 子进程一律固定命令 + argv，禁用 shell 字符串拼接。

## 当前实现状态

- 图片视觉分析：已支持（ModLens + 活动视觉档案）。
- 电子 PDF 阅读/搜索/渲染/视觉页面分析：已支持。
- 复杂/扫描 PDF (MinerU)：已集成但需 Docker Desktop 运行 + 镜像构建。
- Claude Code 粘贴恢复 (recover-paste)：已支持（仅 Claude Code 宿主）。
- 总控台 (Web UI)：已支持（127.0.0.1:8765），总控台关闭时 CLI 仍独立可用。
