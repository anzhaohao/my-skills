#!/usr/bin/env python3
"""
上海高中成绩单教学分析 PDF 报告生成工具

用法示例：

    # 多班级整体对比
    python generate_score_report.py \\
      --files "7班整体成绩.xlsx" "8班整体成绩.xlsx" \\
      --class-names "7班" "8班" \\
      --output "整体分析报告.pdf"

    # 女生专项分析
    python generate_score_report.py \\
      --files "7班整体成绩.xlsx" "8班整体成绩.xlsx" \\
      --class-names "7班" "8班" \\
      --gender-rules "7班:male_first=23;8班:male_first=22" \\
      --report-type "female_only" \\
      --output "女生专项分析报告.pdf"

    # 某班男女生对比
    python generate_score_report.py \\
      --files "7班整体成绩.xlsx" \\
      --class-names "7班" \\
      --gender-rules "7班:male_first=23" \\
      --report-type "class_gender_compare" \\
      --target-class "7班" \\
      --output "7班男女生对比报告.pdf"
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from analyzer import analyze, parse_gender_rules, DEFAULT_THRESHOLDS
from chart_builder import build_all_charts
from report_writer import build_report
from pdf_exporter import export_pdf


REPORT_TYPES = [
    "overall",
    "female_only",
    "male_only",
    "class_gender_compare",
    "custom_group",
]


def parse_thresholds_arg(raw: str) -> dict[str, float]:
    """Parse --thresholds 'excellent=90,good=80,pass=60'."""
    thresholds = dict(DEFAULT_THRESHOLDS)
    if not raw:
        return thresholds
    mapping = {
        "excellent": "excellent",
        "ex": "excellent",
        "good": "good",
        "g": "good",
        "pass": "pass",
        "p": "pass",
    }
    for part in raw.split(","):
        part = part.strip()
        if "=" not in part:
            continue
        key, val = part.split("=", 1)
        key = mapping.get(key.strip().lower(), key.strip().lower())
        try:
            thresholds[key] = float(val.strip())
        except ValueError:
            print(f"警告：无法解析阈值 '{part}'，已忽略。")
    return thresholds


def main():
    parser = argparse.ArgumentParser(
        description="上海高中成绩单教学分析 PDF 报告生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python generate_score_report.py --files "7班.xlsx" "8班.xlsx" --class-names "7班" "8班"
  python generate_score_report.py --files "7班.xlsx" --class-names "7班" --gender-rules "7班:male_first=23" --report-type female_only
  python generate_score_report.py --files "7班.xlsx" --class-names "7班" --gender-rules "7班:male_first=23" --report-type class_gender_compare --target-class "7班"
        """,
    )
    parser.add_argument(
        "--files", nargs="+", required=True,
        help="Excel 成绩文件路径（支持 .xlsx .xls .xlsm）",
    )
    parser.add_argument(
        "--class-names", nargs="+", required=True,
        help="班级名称，与 --files 一一对应",
    )
    parser.add_argument(
        "--gender-rules", type=str, default="",
        help='性别规则，格式："7班:male_first=23;8班:male_first=22"',
    )
    parser.add_argument(
        "--report-type", type=str, default="overall",
        choices=REPORT_TYPES,
        help="报告类型（overall / female_only / male_only / class_gender_compare）",
    )
    parser.add_argument(
        "--target-class", type=str, default="",
        help="目标班级名称（class_gender_compare 模式下必填）",
    )
    parser.add_argument(
        "--output", "-o", type=str, default="",
        help="输出 PDF 文件路径（默认自动生成）",
    )
    parser.add_argument(
        "--output-dir", type=str, default="",
        help="输出目录（默认当前目录下的 output/）",
    )
    parser.add_argument(
        "--thresholds", type=str, default="",
        help='评价标准，格式："excellent=90,good=80,pass=60"',
    )
    parser.add_argument(
        "--no-charts", action="store_true",
        help="不生成图表，仅输出文字报告",
    )

    args = parser.parse_args()

    # Validate
    if len(args.files) != len(args.class_names):
        print("错误：--files 与 --class-names 数量不一致。")
        sys.exit(1)

    if args.report_type == "class_gender_compare" and not args.target_class:
        print("错误：class_gender_compare 模式需要 --target-class 参数。")
        sys.exit(1)

    for fp in args.files:
        if not Path(fp).exists():
            print(f"错误：文件不存在：{fp}")
            sys.exit(1)

    # Setup output dir
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path.cwd() / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse gender rules
    gender_rules = parse_gender_rules(args.gender_rules)
    if args.report_type in ("female_only", "male_only", "class_gender_compare") and not gender_rules:
        print("提示：未提供 --gender-rules 参数。如果 Excel 中已有性别列，将自动使用；否则性别分析将受限。")

    # Parse thresholds
    thresholds = parse_thresholds_arg(args.thresholds)

    print("=" * 60)
    print("  上海高中成绩单教学分析 PDF 报告生成工具")
    print("=" * 60)
    print(f"  报告类型：{args.report_type}")
    print(f"  班级数量：{len(args.files)}")
    print(f"  性别规则：{args.gender_rules if args.gender_rules else '未提供（使用 Excel 内置性别列）'}")
    print(f"  评价标准：优秀≥{thresholds['excellent']:.0f} "
          f"优良≥{thresholds['good']:.0f} "
          f"及格≥{thresholds['pass']:.0f}")
    print()

    # Step 1: Analyze
    print("[1/4] 正在分析成绩数据...")
    try:
        result = analyze(
            file_paths=args.files,
            class_names=args.class_names,
            gender_rules=gender_rules,
            report_type=args.report_type,
            target_class=args.target_class,
            thresholds=thresholds,
        )
    except ValueError as e:
        print(f"分析失败：{e}")
        sys.exit(1)

    overview = result["data_overview"]
    print(f"      分析对象：{overview['分析对象']}")
    print(f"      学生人数：{overview['学生人数']}")
    print(f"      科目数量：{overview['科目数量']}")
    print(f"      主要口径：{overview['主要分析口径']}")
    if result["warnings"]:
        for w in result["warnings"]:
            print(f"      [注意] {w}")

    # Step 2: Build charts
    chart_dir = output_dir / "charts"
    charts = {}
    if not args.no_charts:
        print("[2/4] 正在生成图表...")
        charts = build_all_charts(result, chart_dir)
        print(f"      生成图表：{len(charts)} 张")
    else:
        print("[2/4] 跳过图表生成（--no-charts）。")

    result["chart_paths"] = charts

    # Step 3: Build report
    print("[3/4] 正在撰写报告...")
    generated_at = time.strftime("%Y-%m-%d %H:%M:%S")
    report = build_report(result, generated_at)
    print(f"      报告标题：{report['title']}")
    print(f"      章节数量：{len(report['sections'])}")

    # Step 4: Export PDF
    print("[4/4] 正在导出 PDF...")
    pdf_filename = args.output if args.output else ""
    export_result = export_pdf(report, result, output_dir, pdf_filename)

    print()
    if export_result["ok"]:
        print(f"  PDF 报告已生成：")
        print(f"    {export_result['pdf']}")
    else:
        print(f"  {export_result['message']}")
        print(f"  HTML 报告路径：")
        print(f"    {export_result['print_html']}")
        print()
        print("  降级处理说明：")
        print("    1. 用浏览器打开上述 HTML 文件")
        print("    2. 按 Ctrl+P 打开打印对话框")
        print('    3. 目标打印机选择＂另存为 PDF＂')
        print("    4. 纸张尺寸选择 A4")
        print('    5. 勾选＂背景图形＂')
        print('    6. 边距设置为＂无＂或＂最小＂')

    # Summary
    print()
    print(f"  图表目录：{chart_dir}")
    if result["warnings"]:
        print(f"  数据提醒：{len(result['warnings'])} 条")
    print()
    print("  分析完成。")

    return export_result


if __name__ == "__main__":
    main()
