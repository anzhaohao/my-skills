---
name: azf-zuhui-ppt
description: 用本地 ppt-master 生成安钊锋风格的组会文献汇报 PPT（16:9、图优先、无边框、标题“主题——说明”）。当用户要做组会/文献汇报/paper report 的 PPT，说“做一套组会 PPT”“按我的风格做 PPT”“把这篇文章做成汇报幻灯片”，或要给已完成的 deck 加备注/柔化边缘/改版式时使用。
---

# 组会 PPT（ppt-master + 安钊锋风格）

把一篇论文变成 10–14 页的组会汇报：SVG 手写 → ppt-master 质检与导出 → 加备注/拆组/柔化边缘 → 逐页目检。

**风格规范是硬约束，先读 `references/style-guide.md`，不要自由发挥。**
页面坐标与片段见 `references/page-recipes.md`。

## 何时用

- 要做组会 / 文献汇报 / journal club 的 PPT。
- 已有 deck 要改版式、加备注、改图片透明度/柔化边缘。
- 要把论文图 + 自绘示意图按“一页一图”重排。

不做：商业路演、答辩模板、纯文字大纲、HTML 演示（那是 `html-ppt`）。

## 依赖（本机固定）

```
PPT_MASTER = D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260429-ppt-master
SKILL_DIR  = <ppt-master>\skills\ppt-master
WORK_ROOT  = <ppt-master>\output
PY         = <PPT_MASTER>\.venv\Scripts\python.exe      # 有 pptx / PIL / lxml / fitz
CHECKER    = <SKILL_DIR>\scripts\svg_quality_checker.py
EXPORTER   = <SKILL_DIR>\scripts\svg_to_pptx.py
```

先跑一次完整性闸门，非零就停：`& PY <SKILL_DIR>\scripts\attribution_guard.py`。

## 两个根目录（硬规则）

| 根 | 路径 | 放什么 |
|---|---|---|
| 工作区 `<WORK>` | `<PPT_MASTER>\output\<YYYYMMDD>-<名字>\` | 完整项目：`svg_output`、`images`、`validation`、`exports`、`sources`、`scripts`、`project.json` |
| 交付区 `<DELIVERY>` | `<用户确认的目标根>\<YYYYMMDD>-<名字>\` | **只放最终 `.pptx`**，一个文件 |

- 目标根**每次必须人工确认**，例如 `D:\Postgraduate_JilinUniversity\03_Sundries\00_组会`；没有默认值，未确认前不得创建任何目录。
- 两个文件夹同名，格式固定 `YYYYMMDD-名字`；日期用**组会日期**，不是生成日期。
- 工作区里可以有任何中间物；交付区出现 `.venv`、脚本、`svg_output`、`.png`、`.md`、`projects` 都算失败。
- 旧格式文件夹（如 `2026-10-30_JLT光频梳锁定`）不按本规则追溯改名。

## 工作流

### 0. 人工确认（不能跳过）

先问用户三件事：目标根目录、组会日期、名字（主题）。然后**只打印**将创建的路径：

```powershell
& $PY scripts\workspace.py prepare --date 20261030 --topic "FROG啁啾不稳定性" `
    --target "D:\Postgraduate_JilinUniversity\03_Sundries\00_组会"
```

用户确认后加 `--confirm` 再跑一次，得到 `<WORK>` 与 `<DELIVERY>`：

```powershell
& $PY scripts\workspace.py prepare --date 20261030 --topic "FROG啁啾不稳定性" `
    --target "D:\Postgraduate_JilinUniversity\03_Sundries\00_组会" --confirm
```

`prepare` 会建好 `<WORK>\svg_output|images|validation|exports|sources|scripts` 和空的 `<DELIVERY>`，并写 `<WORK>\project.json`。重复运行只复用、不覆盖。

### 1. 取图

- 论文图：`paper.pdf` 用 fitz 渲染/裁剪，存进 `<WORK>\images\`，文件名 `paper_p<页>_<序>.png`。
- 论文首页截图：`images\paper_first_page.png`（整页，给第 2 页）。
- 封面用摘要片段：`images\cover_paper_excerpt.png`，按 1165:480 = 2.427 的比例裁。
- **裁图 QA 是硬门槛**：坐标轴标题、行/列标签、色条、编号都不能被裁掉；裁完必须看图确认。

### 2. 写页面

复制 `scripts\deck_template.py` 改文案；工具函数在 `scripts\svg_kit.py`。
- 把 `PROJECT` 指到当前的 `<WORK>`，`FIG` 指到 `<WORK>\images\` 下的文件名。
- 按 `references/style-guide.md` 的骨架与字号，一页一图。
- 页面文件按 `01_…svg` 到 `13_…svg` 命名（文件名排序 = 页序）。
- 顶层模块用 `band()`，同一页的 `data-pptx-bounds` **不能重叠**。

### 3. 质检（必须 0 error）

```powershell
& $PY "<CHECKER>" "<WORK>" --quick-generate --canonical-authoring --stage final --json
```

`Noncanonical compact authoring` 是建议项，可以不管；`data-pptx-bounds` 溢出/重叠必须修。

### 4. 导出

```powershell
& $PY "<EXPORTER>" "<WORK>" --quick-generate --no-notes
```

产物在 `<WORK>\exports\ppt-master-*.pptx`。看 `[POSTFLIGHT] status=... quality_gate=passed`。

### 5. 备注 + 后处理

写 `<WORK>\notes.json`（`{"1": "…", "2": "…"}`），然后：

```powershell
& $PY scripts\finalize.py --pptx "<WORK>\exports\<导出>.pptx" --notes "<WORK>\notes.json" `
    --soft-edge "1:285750,2:850900" --out "<WORK>\exports\组会PPT_<主题>_<N>页_final.pptx"
```

- 拆组：让每个文本框回到顶层（否则要双击进组才能改）。
- 柔化边缘：默认给第 1、2 页的淡化截图；其它页不需要。
- `_final` 文件留在工作区，交付时再 publish。

### 6. 逐页目检（不能只看检查器）

```powershell
1..N | % { officecli view "<WORK>\exports\组会PPT_<主题>_<N>页_final.pptx" screenshot --page $_ -o "$env:TEMP\p$_.png" }
```

用 `read_image` 一张张看，重点查：遮挡、越界、换行断在词中间、标注重叠、图被裁。
发现问题回到第 2 步改 SVG，重跑 3–5。

### 7. 交付（只把最终 pptx 放进交付区）

```powershell
& $PY scripts\workspace.py publish --work "<WORK>" `
    --pptx "<WORK>\exports\组会PPT_<主题>_<N>页_final.pptx" `
    --name "组会PPT_<主题>_<N>页.pptx"

& $PY scripts\workspace.py check --delivery "<DELIVERY>" --expect-one
```

- `publish` 只接受 `.pptx`；交付区有非 pptx 时会拒绝。
- 重名要覆盖时加 `--force`。
- `check --expect-one` 必须通过：交付区有且只有一个 `.pptx`。
- 旧的中间版本留在 `<WORK>\exports\` 作回滚点，不主动删。

## 常见坑（都踩过）

| 现象 | 原因 / 处理 |
|---|---|
| 交付区出现 `.venv`、`build_*.py`、`svg_output\` | 工作区放错位置；全部移回 `<WORK>`，交付区只留最终 pptx |
| `check` 报 `non-pptx entries` | 交付区混进图片/笔记/目录；移回 `<WORK>` 后重跑 |
| `prepare` 报 target not found | 目标根不存在或写错；让用户重新确认，别自动创建父目录 |
| `prepare` 报 illegal characters | 名字含 `\ / : * ? " < > |`；换短名字 |
| `publish` 报 destination exists | 需要覆盖就加 `--force` |
| `data-pptx-bounds overlaps ...` | 同页两个顶层 `<g>` 重叠；拆成 3 条带（标题 / 主体 / 结论条） |
| `exceeds <g ...> data-pptx-bounds` | 文字基线离模块边界太近；文本占位 = 基线−0.85×字号 到 基线+0.35×字号，阈值 5% |
| `too many values to unpack` | `text()` 少了一层括号：行是 `[(片段,颜色),…]`，页是 `[行, 行]` |
| 中文在控制台乱码 | PowerShell 是 GBK；文件本身没问题，别据此判断失败 |
| PowerShell 里写不了 heredoc | 用 `write` 工具落一个临时 `.py` 再执行 |
| 图片报 role 错 | `<image>` 包在 `band()` 里，图片自身不加 `data-pptx-role` |
| 导出后文件 4–5 MB | 论文图是 3000 px 宽；需要小文件用 `--image-sizing display`（会降分辨率） |
| 页码列表渲染互相覆盖 | `officecli screenshot` 的 `--page` 只给单页，逐页跑 |
| 拆组后渲染异常 | 只拆恒等变换的组合；`finalize.py` 会自动跳过有真实变换的 |

## 产物结构

```
<WORK>\                                  # PPT_MASTER\output\<YYYYMMDD>-<名字>\
  svg_output\01_…svg …                  # 页面源
  images\                               # 论文图 / 截图
  validation\                           # 质检报告 + 渲染截图
  exports\                              # 每次导出 + 最终 _final.pptx
  sources\paper.pdf                     # 原始论文
  scripts\                              # 本项目的构建脚本
  project.json                          # 日期、名字、交付路径

<DELIVERY>\                              # <目标根>\<YYYYMMDD>-<名字>\
  组会PPT_<主题>_<N>页.pptx              # 唯一交付物
```

## 维护

- 风格有变化（用户改了口径、换了配色）先改 `references/style-guide.md`，再改脚本常量。
- `scripts/svg_kit.py` 里的颜色/字号常量是唯一真源，模板和配方都引用它。
- 新页面类型先在 `references/page-recipes.md` 记坐标，再考虑要不要加进模板。
- **2026-10-30 第二版**：改成双根目录（工作区在 `ppt-master\output`，交付区只留最终 pptx），加入 `scripts/workspace.py` 与人工确认步骤；不再往组会文件夹里放代码或中间物。
