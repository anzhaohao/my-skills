# azf-zuhui-ppt（组会 PPT 生成）

## 这个 skill 解决什么问题

把一篇论文做成一整套组会汇报 PPT，并且**每次都是同一个风格**：16:9、一页一张图、
标题写「主题——说明」、底部一条米黄结论条、没有边框和阴影、正文够大能投影看清。

底层用本地 `ppt-master`（SVG → 原生 DrawingML），所以产出的每个文本框、色块、箭头
都能在 PowerPoint 里直接改，不是贴图。风格规范是从你 2026-08-24 那份组会 PPT 里
逐项量出来的（字号、颜色、位置、图片透明度、柔化边缘），不是猜的。

## 什么时候触发

- "帮我做一套组会 PPT / 文献汇报 PPT / 把这篇文章讲一下"
- "按我的风格做 PPT"
- "把这份 deck 的图片调成淡化 + 边缘模糊"、"加演讲备注"、"标题改成我的写法"

## 关键事实（存下来免得每次重问）

| 项 | 值 |
|---|---|
| 组会文件夹 | `D:\Postgraduate_JilinUniversity\03_Sundries\00_组会\<日期_主题>\` |
| ppt-master | `D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260429-ppt-master` |
| Python | `<ppt-master>\.venv\Scripts\python.exe`（有 pptx / PIL / lxml / fitz） |
| 画布 | 1280×720 px（13.333×7.5 in，16:9） |
| 标题 | 44 px 微软雅黑 Bold，`#767171`，位置 (20, 60)，写法「主题——说明」 |
| 结论条 | 米黄 `#FFF7EE`，1192×64 @ (44, 648)，30 px 居中，无描边 |
| 关键词 | 蓝 `#4472C4`、红 `#E23B2E`、深蓝 `#2F5597` |
| 淡化截图 | 透明度 23–24% + PowerPoint 原生柔化边缘（整页 rad=850900 EMU） |
| 页数 | 论文汇报 12–13 页；正文一页 ≤3 条、一行 ≤40 全角字 |

## 目录结构

```
SKILL.md                      操作手册（工作流 + 踩过的坑）
README.md                     本文件
references/style-guide.md     风格规范（最权威，改风格先改这里）
references/page-recipes.md    各类页面的坐标与片段
scripts/svg_kit.py            绘图工具箱（颜色/字号常量、text/band/bar/slab/grid…）
scripts/deck_template.py      可直接跑的五页骨架，复制改文案
scripts/finalize.py           加备注 → 拆分组 → 柔化边缘 → 自检
```

## 怎么用（最短路径）

1. 读 `references/style-guide.md`（一遍就够，后面按清单走）。
2. 复制 `scripts/deck_template.py`，改 `PROJECT` 和文案，跑一遍出页面。
3. `svg_quality_checker.py` → `svg_to_pptx.py` → `finalize.py`。
4. 逐页 `officecli` 渲染截图，用眼睛看一遍再交付。

## 最近一次维护

**2026-10-30**：首版。由 2026-10-30 FROG-CNN 组会汇报这一轮的实测数据整理：
原稿 17 页的 OOXML 尺寸/颜色/透明度/柔化边缘参数、迭代出的 44 px 标题与无边框规则、
以及 13 页的最终页序。同时把当时踩到的坑（组边界重叠、tspan 括号、拆组、柔化边缘）
写进了 SKILL.md。
