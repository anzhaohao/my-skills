from __future__ import annotations

import re
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd


ALLOWED_EXTENSIONS = {".xlsx", ".xlsm", ".xls"}

DEFAULT_THRESHOLDS = {
    "excellent": 90.0,
    "good": 80.0,
    "pass": 60.0,
}

CRITICAL_THRESHOLDS = {
    "near_excellent": (85, 89),
    "near_good": (75, 79),
    "near_pass": (55, 59),
    "at_risk": (0, 54),
}

EXCLUDED_SCORE_KEYWORDS = [
    "姓名", "班级", "座号", "学号", "系统号", "性别",
    "班次", "年次", "名次", "排名", "等级", "备注",
    "name", "studentid", "rank", "ranking", "gender",
]

RANK_KEYWORDS = ["班次", "年次", "名次", "排名", "rank", "ranking"]
GRADE_RANK_KEYWORDS = ["年次", "年级名次", "grade_rank", "graderank"]
CLASS_RANK_KEYWORDS = ["班次", "班级名次", "class_rank", "classrank"]
NAME_KEYWORDS = ["姓名", "学生姓名", "名字", "学生", "name"]
GENDER_KEYWORDS = ["性别", "男女", "男/女", "sex", "gender"]
TOTAL_KEYWORDS = ["总分", "总成绩", "合计", "总计", "total", "sum"]

MAIN_SUBJECTS = ["语文", "数学", "外语"]
TEN_SUBJECTS = [
    "语文", "数学", "外语", "物理", "化学",
    "政治", "历史", "地理", "生物", "信息科技",
]
SUBJECT_ALIASES = {
    "英语": "外语", "英文": "外语",
    "信息": "信息科技", "信息技术": "信息科技",
}

GENDER_VALUES = {"male": "男", "female": "女", "unknown": "未知"}


def normalize_text(value: Any) -> str:
    return str(value).strip().lower().replace(" ", "").replace("_", "").replace("-", "")


def contains_any(text: str, keywords: list[str]) -> bool:
    normalized = normalize_text(text)
    return any(normalize_text(keyword) in normalized for keyword in keywords)


def is_rank_column(column: str) -> bool:
    return contains_any(column, RANK_KEYWORDS)


def detect_total_kind(column: str) -> str:
    normalized = normalize_text(column)
    if contains_any(column, RANK_KEYWORDS):
        return ""
    if "总分3" in normalized or "三科总分" in normalized or "total3" in normalized:
        return "total3"
    if "总分10" in normalized or "十科总分" in normalized or "total10" in normalized:
        return "total10"
    if contains_any(column, TOTAL_KEYWORDS):
        return "total"
    return ""


def standard_subject_name(column: str) -> str:
    text = str(column).strip()
    for raw, standard in SUBJECT_ALIASES.items():
        if raw in text:
            return standard
    for subject in sorted(TEN_SUBJECTS, key=len, reverse=True):
        if subject in text:
            return subject
    for suffix in ["成绩", "分数", "得分", "score"]:
        text = text.replace(suffix, "")
    return text.strip() or str(column)


def classify_columns(columns: list[str]) -> dict[str, Any]:
    info = []
    total_candidates = []
    score_candidates = []
    rank_columns = []
    name_column = ""
    gender_column = ""

    for column in columns:
        is_name = contains_any(column, NAME_KEYWORDS)
        is_gender = contains_any(column, GENDER_KEYWORDS)
        is_rank = is_rank_column(column)
        total_kind = detect_total_kind(column)
        excluded = contains_any(column, EXCLUDED_SCORE_KEYWORDS)
        selectable = not is_name and not is_gender and not is_rank and not excluded

        if is_name and not name_column:
            name_column = column
        if is_gender and not gender_column:
            gender_column = column
        if total_kind:
            total_candidates.append(column)
        if selectable and not total_kind:
            score_candidates.append(column)
        if is_rank:
            rank_columns.append(column)

        info.append({
            "name": column,
            "is_name": is_name,
            "is_gender": is_gender,
            "total_kind": total_kind,
            "is_rank": is_rank,
            "is_score": selectable and not total_kind,
        })

    return {
        "name_column": name_column,
        "gender_column": gender_column,
        "total_candidates": total_candidates,
        "score_columns": score_candidates,
        "rank_columns": rank_columns,
        "columns": info,
        "has_gender": bool(gender_column),
        "has_rank": bool(rank_columns),
    }


def parse_gender_rules(rules_str: str) -> dict[str, int]:
    """Parse gender rules like '7班:male_first=23;8班:male_first=22'."""
    rules: dict[str, int] = {}
    if not rules_str or not rules_str.strip():
        return rules
    for part in rules_str.split(";"):
        part = part.strip()
        if not part:
            continue
        match = re.match(r"(.+?):male_first=(\d+)", part)
        if match:
            class_name = match.group(1).strip()
            count = int(match.group(2))
            rules[class_name] = count
    return rules


def apply_gender_rules(
    df: pd.DataFrame,
    class_name: str,
    gender_rules: dict[str, int],
    existing_gender_column: str,
) -> pd.DataFrame:
    """Apply gender rules to add or override gender column."""
    df = df.copy()

    if existing_gender_column and existing_gender_column in df.columns:
        df["性别"] = df[existing_gender_column].apply(_normalize_gender_value)
    elif class_name in gender_rules:
        male_count = gender_rules[class_name]
        genders = []
        for i in range(len(df)):
            genders.append("男" if i < male_count else "女")
        df["性别"] = genders
    else:
        df["性别"] = "未知"

    return df


def _normalize_gender_value(value: Any) -> str:
    text = normalize_text(value)
    if text in {"男", "男生", "m", "male", "boy", "1"}:
        return "男"
    if text in {"女", "女生", "f", "female", "girl", "0", "2"}:
        return "女"
    return "未知"


def filter_by_report_type(
    all_data: pd.DataFrame,
    student_data: pd.DataFrame,
    report_type: str,
    target_class: str = "",
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Filter data based on report type. Returns (all_data, student_data, filter_description)."""
    desc = ""

    if report_type == "female_only":
        all_data = all_data[all_data["性别"] == "女"]
        student_data = student_data[student_data["性别"] == "女"]
        desc = "本报告仅分析女生群体。"

    elif report_type == "male_only":
        all_data = all_data[all_data["性别"] == "男"]
        student_data = student_data[student_data["性别"] == "男"]
        desc = "本报告仅分析男生群体。"

    elif report_type == "class_gender_compare" and target_class:
        all_data = all_data[all_data["班级"] == target_class]
        student_data = student_data[student_data["班级"] == target_class]
        desc = f"本报告针对{target_class}内部男女生进行对比分析。"

    elif report_type == "overall":
        desc = "本报告对所有班级进行整体对比分析。"

    return all_data, student_data, desc


def percent(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round(float(numerator) / float(denominator) * 100, 2)


def format_rate(value: float) -> str:
    return f"{float(value):.2f}%"


def format_number(value: float | int | None) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "-"
    return f"{float(value):.2f}"


def compute_stats(
    scores: pd.Series,
    thresholds: dict[str, float],
    class_name: str = "",
    item: str = "",
    label: str = "",
) -> dict[str, Any]:
    """Compute comprehensive statistics for a set of scores."""
    scores = pd.to_numeric(scores, errors="coerce").dropna()
    count = int(scores.count())
    if not count:
        return {
            "班级": class_name, "分析项": item, "分组": label,
            "人数": 0, "平均分": 0.0, "中位数": 0.0,
            "最高分": 0.0, "最低分": 0.0, "极差": 0.0, "标准差": 0.0,
            "优秀率": 0.0, "优良率": 0.0, "及格率": 0.0, "低分率": 0.0,
            "优秀人数": 0, "优良人数": 0, "及格人数": 0, "低分人数": 0,
        }

    excellent = int((scores >= thresholds["excellent"]).sum())
    good = int((scores >= thresholds["good"]).sum())
    passed = int((scores >= thresholds["pass"]).sum())
    low = int((scores < thresholds["pass"]).sum())

    return {
        "班级": class_name, "分析项": item, "分组": label,
        "人数": count,
        "平均分": round(float(scores.mean()), 2),
        "中位数": round(float(median(scores.tolist())), 2),
        "最高分": round(float(scores.max()), 2),
        "最低分": round(float(scores.min()), 2),
        "极差": round(float(scores.max() - scores.min()), 2),
        "标准差": round(float(scores.std(ddof=0)), 2),
        "优秀率": percent(excellent, count),
        "优良率": percent(good, count),
        "及格率": percent(passed, count),
        "低分率": percent(low, count),
        "优秀人数": excellent, "优良人数": good,
        "及格人数": passed, "低分人数": low,
    }


def load_and_process_file(
    file_path: str,
    class_name: str,
    gender_rules: dict[str, int],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], list[str]]:
    """Load a single Excel file, detect columns, apply gender rules, return analysis-ready data."""
    warnings: list[str] = []
    df = pd.read_excel(file_path, engine="openpyxl")
    if df.empty:
        raise ValueError(f"{class_name} 文件没有可分析的数据。")

    df.columns = [str(c).strip() for c in df.columns]
    col_info = classify_columns(list(df.columns))

    # Apply gender rules
    df = apply_gender_rules(
        df, class_name, gender_rules, col_info["gender_column"]
    )
    unknown_gender = (df["性别"] == "未知").sum()
    if unknown_gender and class_name not in gender_rules and not col_info["gender_column"]:
        warnings.append(
            f"{class_name} 未提供性别规则且文件中无性别列，性别相关分析将受限。"
        )

    # Extract names
    if col_info["name_column"]:
        names = df[col_info["name_column"]].fillna("").astype(str).str.strip()
    else:
        names = pd.Series([f"学生{i+1}" for i in range(len(df))], index=df.index)

    # Build student frame
    student_frame = pd.DataFrame({
        "班级": class_name,
        "来源文件": Path(file_path).name,
        "学生序号": range(1, len(df) + 1),
        "姓名": names,
        "性别": df["性别"],
    })

    # Process scores and totals
    frames, item_values, item_meta = _build_score_frames(
        df, class_name, Path(file_path).name, names, df["性别"],
        col_info, warnings
    )

    if not frames:
        raise ValueError(f"{class_name} 没有可用于统计的有效成绩。")

    # Add items to student frame
    for item_name, values in item_values.items():
        student_frame[item_name] = values

    # Add rank columns
    for column in col_info["rank_columns"]:
        if column in df.columns:
            student_frame[column] = pd.to_numeric(df[column], errors="coerce")

    student_frame.attrs["item_meta"] = item_meta
    student_frame.attrs["col_info"] = col_info

    all_data = pd.concat(frames, ignore_index=True)
    return all_data, student_frame, col_info, warnings


def _build_score_frames(
    df: pd.DataFrame,
    class_name: str,
    file_name: str,
    names: pd.Series,
    genders: pd.Series,
    col_info: dict[str, Any],
    warnings: list[str],
) -> tuple[list[pd.DataFrame], dict[str, pd.Series], list[dict[str, Any]]]:
    """Build normalized score frames with total3/total10 → average conversion."""
    used_names: set[str] = set()
    frames: list[pd.DataFrame] = []
    item_values: dict[str, pd.Series] = {}
    item_meta: list[dict[str, Any]] = []
    subject_values: dict[str, pd.Series] = {}

    def _unique(name: str) -> str:
        base = name.strip()
        candidate = base
        idx = 2
        while candidate in used_names:
            candidate = f"{base}_{idx}"
            idx += 1
        used_names.add(candidate)
        return candidate

    def _add_item(item_name: str, item_type: str, source: str,
                  values: pd.Series, rate_base: bool = True) -> str:
        numeric = pd.to_numeric(values, errors="coerce")
        invalid = int(numeric.isna().sum())
        if invalid:
            warnings.append(
                f'{class_name} 的“{source}”有 {invalid} 行为空或无法识别，已排除。'
            )
        name = _unique(item_name)
        item_values[name] = numeric
        item_meta.append({
            "班级": class_name, "分析项": name, "分析类型": item_type,
            "来源列": source, "可用于达标率": rate_base,
        })
        frame = pd.DataFrame({
            "班级": class_name, "来源文件": file_name,
            "姓名": names, "性别": genders,
            "分析项": name, "分析类型": item_type,
            "来源列": source, "可用于达标率": rate_base,
            "成绩": numeric,
        }).dropna(subset=["成绩"])
        if not frame.empty:
            frame["成绩"] = frame["成绩"].astype(float)
            frames.append(frame)
        return name

    # Process single-subject scores
    for column in col_info["score_columns"]:
        if column not in df.columns or is_rank_column(column):
            continue
        values = pd.to_numeric(df[column], errors="coerce")
        subject = standard_subject_name(column)
        item = _add_item(subject, "subject", str(column), values, rate_base=True)
        subject_values[item] = values

    # Process total columns with the critical total3/total10 → average conversion
    for column in col_info["total_candidates"]:
        if column not in df.columns:
            continue
        kind = detect_total_kind(column)
        values = pd.to_numeric(df[column], errors="coerce")
        if kind == "total3":
            _add_item("总分3", "total_raw", str(column), values, rate_base=False)
            _add_item("三科平均", "aggregate_average", f"{column}/3",
                      values / 3, rate_base=True)
        elif kind == "total10":
            _add_item("总分10", "total_raw", str(column), values, rate_base=False)
            _add_item("十科平均", "aggregate_average", f"{column}/10",
                      values / 10, rate_base=True)
        else:
            _add_item(str(column), "total_raw", str(column), values, rate_base=False)

    # Auto-generate 三科平均 from individual subjects if not present
    available_mains = [s for s in MAIN_SUBJECTS if s in subject_values]
    if len(available_mains) >= 3 and "三科平均" not in item_values:
        main_frame = pd.DataFrame({
            s: subject_values[s] for s in available_mains
        })
        _add_item("三科平均", "aggregate_average", "语文、数学、外语平均",
                  main_frame.mean(axis=1, skipna=True), rate_base=True)

    # Auto-generate 十科平均 from individual subjects if enough present
    available_ten = [s for s in TEN_SUBJECTS if s in subject_values]
    if len(available_ten) >= 5 and "十科平均" not in item_values:
        ten_frame = pd.DataFrame({s: subject_values[s] for s in available_ten})
        _add_item("十科平均", "aggregate_average", "多科成绩平均",
                  ten_frame.mean(axis=1, skipna=True), rate_base=True)

    return frames, item_values, item_meta


def choose_primary_item(all_data: pd.DataFrame) -> str:
    """Choose the best primary analysis item."""
    rate_data = all_data[all_data["可用于达标率"] == True]  # noqa: E712
    items = list(dict.fromkeys(rate_data["分析项"].astype(str).tolist()))
    for preferred in ("十科平均", "三科平均", "多科平均"):
        if preferred in items:
            return preferred
    agg = rate_data[rate_data["分析类型"] == "aggregate_average"]["分析项"].drop_duplicates().tolist()
    if agg:
        return str(agg[0])
    subj = rate_data[rate_data["分析类型"] == "subject"]["分析项"].drop_duplicates().tolist()
    if subj:
        return str(subj[0])
    return str(all_data["分析项"].iloc[0])


# ─── Analysis result builders ───────────────────────────────────────────

def make_overall_rows(all_data: pd.DataFrame, class_names: list[str],
                      primary_item: str, thresholds: dict[str, float]) -> list[dict]:
    rows = []
    for cn in class_names:
        subset = all_data[(all_data["班级"] == cn) & (all_data["分析项"] == primary_item)]
        rec = compute_stats(subset["成绩"], thresholds, class_name=cn, item=primary_item)
        rows.append(rec)
    return rows


def make_subject_rows(all_data: pd.DataFrame, class_names: list[str],
                      thresholds: dict[str, float]) -> list[dict]:
    items = [i for i in all_data[all_data["分析类型"] == "subject"]["分析项"].drop_duplicates().tolist()
             if not contains_any(i, RANK_KEYWORDS + TOTAL_KEYWORDS)]
    rows = []
    for cn in class_names:
        for item in items:
            subset = all_data[(all_data["班级"] == cn) & (all_data["分析项"] == item)]
            rec = compute_stats(subset["成绩"], thresholds, class_name=cn, item=item)
            rows.append({
                "班级": cn, "学科": item,
                "平均分": format_number(rec["平均分"]),
                "优秀率": format_rate(rec["优秀率"]),
                "优良率": format_rate(rec["优良率"]),
                "及格率": format_rate(rec["及格率"]),
                "标准差": format_number(rec["标准差"]),
                "_raw": rec,
            })
    return rows


def make_segment_rows(all_data: pd.DataFrame, class_names: list[str],
                      primary_item: str) -> list[dict]:
    rows = []
    for cn in class_names:
        subset = all_data[(all_data["班级"] == cn) & (all_data["分析项"] == primary_item)]
        scores = pd.to_numeric(subset["成绩"], errors="coerce").dropna()
        total = int(scores.count())
        rows.append({
            "班级": cn,
            "优秀层(90及以上)": int((scores >= 90).sum()),
            "优良层(80-89)": int(((scores >= 80) & (scores < 90)).sum()),
            "中上层(70-79)": int(((scores >= 70) & (scores < 80)).sum()),
            "基础层(60-69)": int(((scores >= 60) & (scores < 70)).sum()),
            "待提升层(60以下)": int((scores < 60).sum()),
            "总人数": total,
        })
    return rows


def make_layering_rows(student_data: pd.DataFrame, class_names: list[str],
                       primary_item: str) -> list[dict]:
    rows = []
    if primary_item not in student_data.columns:
        return rows
    for cn in class_names:
        scores = pd.to_numeric(
            student_data.loc[student_data["班级"] == cn, primary_item],
            errors="coerce"
        ).dropna()
        total = int(scores.count())
        if not total:
            continue
        rows.append({
            "班级": cn,
            "优秀层(90及以上)": int((scores >= 90).sum()),
            "优良层(80-89)": int(((scores >= 80) & (scores < 90)).sum()),
            "中上层(70-79)": int(((scores >= 70) & (scores < 80)).sum()),
            "基础层(60-69)": int(((scores >= 60) & (scores < 70)).sum()),
            "待提升层(60以下)": int((scores < 60).sum()),
            "冲优秀临界生(85-89)": int(((scores >= 85) & (scores < 90)).sum()),
            "冲优良临界生(75-79)": int(((scores >= 75) & (scores < 80)).sum()),
            "及格临界生(55-59)": int(((scores >= 55) & (scores < 60)).sum()),
            "风险学生(55以下)": int((scores < 55).sum()),
            "总人数": total,
        })
    return rows


def make_rank_rows(student_data: pd.DataFrame, class_names: list[str]) -> list[dict]:
    rank_cols = [c for c in student_data.columns if is_rank_column(c)]
    rows = []
    for column in rank_cols:
        values = pd.to_numeric(student_data[column], errors="coerce").dropna()
        if values.empty:
            continue
        grade_total = int(max(values.max(), 1))
        for cn in class_names:
            subset = pd.to_numeric(
                student_data.loc[student_data["班级"] == cn, column],
                errors="coerce"
            ).dropna()
            if subset.empty:
                continue
            percentile = 1 - (subset - 1) / grade_total
            rows.append({
                "班级": cn, "排名项目": column,
                "参考总人数": grade_total,
                "平均年级百分位": format_rate(round(float(percentile.mean() * 100), 2)),
                "前10%人数": int((subset <= grade_total * 0.10).sum()),
                "前25%人数": int((subset <= grade_total * 0.25).sum()),
                "后25%人数": int((subset > grade_total * 0.75).sum()),
            })
    return rows


def make_balance_rows(student_data: pd.DataFrame, class_names: list[str],
                      subject_items: list[str]) -> list[dict]:
    rows = []
    available = [s for s in subject_items if s in student_data.columns]
    if len(available) < 2:
        return rows
    main_avail = [s for s in MAIN_SUBJECTS if s in student_data.columns]

    subj_scores = student_data[available].apply(pd.to_numeric, errors="coerce")
    student_data = student_data.copy()
    student_data["偏科指数"] = subj_scores.std(axis=1, ddof=0)
    if len(main_avail) >= 2:
        student_data["主科稳定指数"] = (
            student_data[main_avail].apply(pd.to_numeric, errors="coerce").std(axis=1, ddof=0)
        )
    else:
        student_data["主科稳定指数"] = None

    for cn in class_names:
        subset = student_data[student_data["班级"] == cn]
        bias = pd.to_numeric(subset["偏科指数"], errors="coerce").dropna()
        if bias.empty:
            continue
        means = subset[available].apply(pd.to_numeric, errors="coerce").mean().dropna()
        rows.append({
            "班级": cn,
            "平均偏科指数": format_number(float(bias.mean())),
            "主科稳定指数": format_number(
                float(pd.to_numeric(subset["主科稳定指数"], errors="coerce").dropna().mean())
            ) if "主科稳定指数" in subset.columns else "-",
            "均衡型学生(偏科指数≤8)": int((bias <= 8).sum()),
            "偏科明显学生(偏科指数≥18)": int((bias >= 18).sum()),
            "优势科目": str(means.idxmax()) if not means.empty else "-",
            "短板科目": str(means.idxmin()) if not means.empty else "-",
        })
    return rows


def make_gender_comparison(all_data: pd.DataFrame, class_names: list[str],
                           primary_item: str, thresholds: dict[str, float]) -> list[dict]:
    """Make gender comparison rows for class_gender_compare mode."""
    rows = []
    target = all_data[all_data["性别"].isin(["男", "女"])]
    if target.empty:
        return rows
    for cn in class_names:
        for gender, label in [("男", "男生"), ("女", "女生")]:
            subset = target[(target["班级"] == cn) & (target["性别"] == gender) &
                            (target["分析项"] == primary_item)]
            rec = compute_stats(subset["成绩"], thresholds, class_name=cn, item=primary_item, label=label)
            rows.append(rec)
    return rows


# ─── Main analysis entry ────────────────────────────────────────────────

def analyze(
    file_paths: list[str],
    class_names: list[str],
    gender_rules: dict[str, int],
    report_type: str = "overall",
    target_class: str = "",
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Main analysis entry point. Returns complete analysis result dict."""
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    if len(file_paths) != len(class_names):
        raise ValueError("文件数量与班级名称数量不一致。")

    all_frames = []
    all_students = []
    all_warnings = []

    for file_path, class_name in zip(file_paths, class_names):
        ad, sd, ci, warns = load_and_process_file(file_path, class_name, gender_rules)
        all_frames.append(ad)
        all_students.append(sd)
        all_warnings.extend(warns)

    all_data = pd.concat(all_frames, ignore_index=True)
    student_data = pd.concat(all_students, ignore_index=True)

    # Apply report type filter
    filter_desc = ""
    if report_type in ("female_only", "male_only", "class_gender_compare"):
        all_data, student_data, filter_desc = filter_by_report_type(
            all_data, student_data, report_type, target_class
        )

    class_names = list(dict.fromkeys(
        all_data["班级"].drop_duplicates().tolist()
    ))
    if not class_names:
        raise ValueError("筛选后没有可分析的数据，请检查报告类型和性别规则。")

    primary_item = choose_primary_item(all_data)
    subject_items = [
        i for i in all_data[all_data["分析类型"] == "subject"]["分析项"].drop_duplicates().tolist()
        if not contains_any(i, RANK_KEYWORDS + TOTAL_KEYWORDS)
    ]

    overall_rows = make_overall_rows(all_data, class_names, primary_item, thresholds)
    subject_rows = make_subject_rows(all_data, class_names, thresholds)
    segment_rows = make_segment_rows(all_data, class_names, primary_item)
    layering_rows = make_layering_rows(student_data, class_names, primary_item)
    rank_rows = make_rank_rows(student_data, class_names)
    balance_rows = make_balance_rows(student_data, class_names, subject_items)
    gender_rows = make_gender_comparison(all_data, class_names, primary_item, thresholds)

    # Data overview
    overview = {
        "班级数量": len(class_names),
        "分析对象": "、".join(class_names),
        "学生人数": int(student_data.groupby("班级").size().sum()),
        "科目数量": len(subject_items),
        "主要分析口径": primary_item,
        "是否有性别数据": bool(gender_rows) or any(
            student_data["性别"].isin(["男", "女"])
        ),
        "是否有排名字段": bool(rank_rows),
    }

    # Summary cards
    valid_overall = [r for r in overall_rows if r["人数"]]
    summary = {
        "class_count": len(class_names),
        "student_count": sum(r["人数"] for r in valid_overall),
        "primary_item": primary_item,
    }
    if valid_overall:
        best_avg = max(valid_overall, key=lambda r: r["平均分"])
        best_good = max(valid_overall, key=lambda r: r["优良率"])
        most_stable = min(valid_overall, key=lambda r: r["标准差"])
        summary.update({
            "best_average": f"{best_avg['班级']}（{best_avg['平均分']:.2f}）",
            "best_good_rate": f"{best_good['班级']}（{format_rate(best_good['优良率'])}）",
            "most_stable": f"{most_stable['班级']}（标准差 {most_stable['标准差']:.2f}）",
        })

    # Gender rule description
    gender_rule_desc = ""
    if gender_rules:
        parts = [
            f"{cn}前{count}条记录为男生，其余为女生"
            for cn, count in gender_rules.items()
        ]
        gender_rule_desc = "本报告性别划分依据用户补充规则：" + "；".join(parts) + "。"

    result = {
        "thresholds": thresholds,
        "report_type": report_type,
        "target_class": target_class,
        "class_names": class_names,
        "primary_item": primary_item,
        "subject_items": subject_items,
        "filter_description": filter_desc,
        "gender_rule_description": gender_rule_desc,
        "data_overview": overview,
        "summary": summary,
        "overall_rows": overall_rows,
        "subject_rows": subject_rows,
        "segment_rows": segment_rows,
        "layering_rows": layering_rows,
        "rank_rows": rank_rows,
        "balance_rows": balance_rows,
        "gender_rows": gender_rows,
        "warnings": all_warnings,
        # Keep raw data for chart building
        "_all_data": all_data,
        "_student_data": student_data,
    }
    return result
