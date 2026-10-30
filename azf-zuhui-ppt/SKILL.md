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
- 要把论文图 + 自绘示意图按"一页一图"重排。

不做：商业路演、答辩模板、纯文字大纲、HTML 演示（那是 `html-ppt`）。

## 依赖（本机固定）

```
PPT_MASTER = D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260429-ppt-master
SKILL_DIR  = <ppt-master>\skills\ppt-master
PY         = <PPT_MASTER>\.venv\Scripts\python.exe      # 有 pptx / PIL / lxml / fitz
CHECKER    = <SKILL_DIR>\scripts\svg_quality_checker.py
EXPORTER   = <SKILL_DIR>\scripts\svg_to_pptx.py
```

先跑一次完整性闸门，非零就停：`& PY <SKILL_DIR>\scripts\attribution_guard.py`。
项目目录按用户习惯放 `D:\Postgraduate_JilinUniversity\03_Sundries\00_组会\<日期_主题>\`，**不要放 E 盘**。

## 工作流

### 1. 建项目
```powershell
Push-Location <组会文件夹>
& $PY "<SKILL_DIR>\scripts\project_manager.py" init <slug> --quick-generate --format ppt169
Pop-Location
```
得到 `<组会文件夹>\projects\<slug>_ppt169_<date>\`，里面要有 `svg_output\`、`images\`、`validation\`。
（已有项目直接复用，不要重建。）

### 2. 取图
- 论文图：`paper.pdf` 用 fitz 渲染/裁剪，存进 `images\`，文件名 `paper_p<页>_<序>.png`。
- 论文首页截图：`images\paper_first_page.png`（整页，给第 2 页）。
- 封面用摘要片段：`images\cover_paper_excerpt.png`，按 1165:480 = 2.427 的比例裁。
- **裁图 QA 是硬门槛**：坐标轴标题、行/列标签、色条、编号都不能被裁掉；裁完必须看图确认。

### 3. 写页面
复制 `scripts\deck_template.py` 改文案；工具函数在 `scripts\svg_kit.py`。
- 按 `references/style-guide.md` 的骨架与字号，一页一图。
- 页面文件按 `01_…svg` 到 `13_…svg` 命名（文件名排序 = 页序）。
- 顶层模块用 `band()`，同一页的 `data-pptx-bounds` **不能重叠**。

### 4. 质检（必须 0 error）
```powershell
& $PY "<CHECKER>" <PROJECT> --quick-generate --canonical-authoring --stage final --json
```
`Noncanonical compact authoring` 是建议项，可以不管；`data-pptx-bounds` 溢出/重叠必须修。

### 5. 导出
```powershell
& $PY "<EXPORTER>" <PROJECT> --quick-generate --no-notes
```
产物在 `<PROJECT>\exports\ppt-master-*.pptx`。看 `[POSTFLIGHT] status=... quality_gate=passed`。

### 6. 备注 + 后处理
写 `notes.json`（`{"1": "…", "2": "…"}`），然后：
```powershell
& $PY scripts\finalize.py --pptx <导出.pptx> --notes notes.json `
    --soft-edge "1:285750,2:850900" --out "<组会文件夹>\组会PPT_<主题>.pptx"
```
- 拆组：让每个文本框回到顶层（否则要双击进组才能改）。
- 柔化边缘：默认给第 1、2 页的淡化截图；其它页不需要。

### 7. 逐页目检（不能只看检查器）
```powershell
1..N | % { officecli view <交付.pptx> screenshot --page $_ -o "$env:TEMP\p$_.png" }
```
用 `read_image` 一张张看，重点查：遮挡、越界、换行断在词中间、标注重叠、图被裁。
发现问题回到第 3 步改 SVG，重跑 4–6。

### 8. 交付
- 文件放组会文件夹根目录，命名 `组会PPT_<关键词>_<页数>页.pptx`。
- 汇报备注都在 notes 里；提醒用户"短板答法在备注里"。
- 旧的中间版本保留作回滚点，不主动删。

## 常见坑（都踩过）

| 现象 | 原因 / 处理 |
|---|---|
| `data-pptx-bounds overlaps ... ` | 同页两个顶层 `<g>` 重叠；拆成 3 条带（标题 / 主体 / 结论条） |
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
<组会文件夹>\
  组会PPT_<主题>_<N>页.pptx          ← 交付
  ppt-master-<slug>\
    svg_output\01_…svg …            ← 页面源
    images\                         ← 论文图 / 截图
    exports\                        ← 每次导出的历史
    validation\                     ← 质检报告 + 渲染截图
```

## 维护

- 风格有变化（用户改了口径、换了配色）先改 `references/style-guide.md`，再改脚本常量。
- `scripts/svg_kit.py` 里的颜色/字号常量是唯一真源，模板和配方都引用它。
- 新页面类型先在 `references/page-recipes.md` 记坐标，再考虑要不要加进模板。
