# 使用示例

## 示例 1：多班级整体对比

```bash
python generate_score_report.py \
  --files "7班整体成绩.xlsx" "8班整体成绩.xlsx" \
  --class-names "7班" "8班" \
  --output "7班8班整体对比报告.pdf"
```

## 示例 2：女生专项分析

```bash
python generate_score_report.py \
  --files "7班整体成绩.xlsx" "8班整体成绩.xlsx" \
  --class-names "7班" "8班" \
  --gender-rules "7班:male_first=23;8班:male_first=22" \
  --report-type "female_only" \
  --output "7班8班女生全方位表现对比分析报告.pdf"
```

## 示例 3：男生专项分析

```bash
python generate_score_report.py \
  --files "7班整体成绩.xlsx" "8班整体成绩.xlsx" \
  --class-names "7班" "8班" \
  --gender-rules "7班:male_first=23;8班:male_first=22" \
  --report-type "male_only" \
  --output "7班8班男生全方位表现对比分析报告.pdf"
```

## 示例 4：7班男女生内部对比

```bash
python generate_score_report.py \
  --files "7班整体成绩.xlsx" \
  --class-names "7班" \
  --gender-rules "7班:male_first=23" \
  --report-type "class_gender_compare" \
  --target-class "7班" \
  --output "7班男女生表现差异分析报告.pdf"
```

## 示例 5：自定义评价标准

```bash
python generate_score_report.py \
  --files "7班整体成绩.xlsx" \
  --class-names "7班" \
  --gender-rules "7班:male_first=23" \
  --report-type "female_only" \
  --thresholds "excellent=85,good=70,pass=60" \
  --output "7班女生分析_85分优秀线.pdf"
```

## 示例 6：指定输出目录

```bash
python generate_score_report.py \
  --files "7班整体成绩.xlsx" "8班整体成绩.xlsx" \
  --class-names "7班" "8班" \
  --output-dir "./reports/202405" \
  --output "期中成绩分析报告.pdf"
```

## 性别规则示例

| 规则 | 含义 |
|------|------|
| `7班:male_first=23` | 7班前23条记录为男生，其余为女生 |
| `8班:male_first=22` | 8班前22条记录为男生，其余为女生 |
| `7班:male_first=23;8班:male_first=22` | 组合使用 |

## 输出说明

运行后会在输出目录生成：

```
output/
├── 教学质量分析报告_20240524_143025.pdf   # PDF 报告（Playwright 可用时）
├── print_report.html                        # HTML 报告（始终生成）
└── charts/                                  # 图表 PNG 文件
    ├── chart_average.png
    ├── chart_quality.png
    ├── chart_heatmap.png
    ├── chart_segment.png
    ├── chart_layering.png
    ├── chart_core.png
    ├── chart_stability.png
    ├── chart_distribution.png
    ├── chart_balance.png
    └── chart_gender.png
```
