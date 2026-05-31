# azf-shanghai-high-school-score-report

这个 skill 是 An Zhaofeng 的个人上海高中成绩单分析工具，用于分析上海高中成绩单 Excel 并生成正式教学质量分析 PDF/HTML 报告。

## 什么时候触发

- 用户要求分析上海高中成绩单、班级成绩对比、女生/男生群体分析。
- 用户要求根据性别规则补充性别字段。
- 用户要求生成教学质量分析报告 PDF 或 HTML。

## 最近维护

- 2026-05-31：按个人 skill 命名规范补齐 `azf-` 前缀，并补充触发说明。

## 安装

```bash
pip install -r requirements.txt
```

### Playwright 浏览器（可选，用于自动生成 PDF）

```bash
playwright install chromium
```

如果不安装 Playwright，工具会保留 HTML 报告供手动打印。

## 快速开始

```bash
python generate_score_report.py \
  --files "7班整体成绩.xlsx" "8班整体成绩.xlsx" \
  --class-names "7班" "8班" \
  --gender-rules "7班:male_first=23;8班:male_first=22" \
  --report-type "female_only" \
  --output "女生专项分析报告.pdf"
```

更多示例见 `examples/usage.md`。

## 命令行参数

| 参数 | 说明 | 必填 |
|------|------|------|
| `--files` | Excel 文件路径列表 | 是 |
| `--class-names` | 班级名称列表 | 是 |
| `--gender-rules` | 性别规则 | 否 |
| `--report-type` | 报告类型 | 否（默认 overall） |
| `--target-class` | 目标班级 | class_gender_compare 时必填 |
| `--output` / `-o` | 输出 PDF 路径 | 否 |
| `--output-dir` | 输出目录 | 否（默认 ./output/） |
| `--thresholds` | 评价标准 | 否（默认 90/80/60） |
| `--no-charts` | 不生成图表 | 否 |

## 报告类型

- `overall` — 多班级整体对比
- `female_only` — 女生专项分析
- `male_only` — 男生专项分析
- `class_gender_compare` — 某班男女生对比
- `custom_group` — 预留

## 关键设计

### 总分3 / 总分10 处理

总分3（满分约 300）和总分10（满分约 1000）会**自动转换**为百分制的"三科平均"和"十科平均"后再计算优秀率、优良率、及格率。排名字段不会混入成绩分析。

### 图表

使用 matplotlib 生成静态 PNG 图表，嵌入 PDF 报告对应章节。图表风格温和、低饱和，作为文字分析的辅助。

### PDF 导出

优先使用 Playwright Chromium 自动生成 PDF。如果 Playwright 不可用，保留 HTML 报告供浏览器手动打印。

## 常见问题

**Q: 如何提供性别信息？**

A: 如果 Excel 中有性别列，工具会自动识别并使用。如果没有，可通过 `--gender-rules` 参数指定。

**Q: 评价标准可以自定义吗？**

A: 可以，通过 `--thresholds "excellent=85,good=75,pass=60"` 自定义。

**Q: 如何生成 HTML 而不是 PDF？**

A: 不安装 Playwright 即可，工具会自动生成 `print_report.html`，用浏览器打开后打印为 PDF。

**Q: 支持多少个班级？**

A: 无硬性限制，但建议不超过 5 个班级以保证报告可读性。

## 依赖

- Python ≥ 3.9
- pandas, openpyxl — Excel 读取
- matplotlib — 图表生成
- jinja2 — HTML 模板渲染
- playwright — PDF 自动生成（可选）
