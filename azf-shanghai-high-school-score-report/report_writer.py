from __future__ import annotations

from typing import Any

from analyzer import format_number, format_rate


def _num(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, str):
        value = value.replace("%", "").strip()
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _best(rows: list[dict], key: str) -> dict | None:
    valid = [r for r in rows if r.get("人数", 0)]
    return max(valid, key=lambda r: _num(r.get(key, 0))) if valid else None


def _worst(rows: list[dict], key: str) -> dict | None:
    valid = [r for r in rows if r.get("人数", 0)]
    return min(valid, key=lambda r: _num(r.get(key, 0))) if valid else None


def _class_list(names: list[str]) -> str:
    if not names:
        return ""
    return "、".join(names)


def _gender_context(result: dict) -> str:
    rt = result.get("report_type", "overall")
    if rt == "female_only":
        return "女生群体"
    elif rt == "male_only":
        return "男生群体"
    elif rt == "class_gender_compare":
        tc = result.get("target_class", "")
        return f"{tc}内部男女生"
    return ""


LQ = "“"  # Left curly double quote "
RQ = "”"  # Right curly double quote "


def _q(text: str) -> str:
    """Wrap text in Chinese curly quotes."""
    return f"{LQ}{text}{RQ}"


def build_title(result: dict) -> str:
    rt = result.get("report_type", "overall")
    classes = _class_list(result.get("class_names", []))
    if rt == "female_only":
        return f"{classes}女生全方位表现对比分析报告"
    elif rt == "male_only":
        return f"{classes}男生全方位表现对比分析报告"
    elif rt == "class_gender_compare":
        tc = result.get("target_class", classes)
        return f"{tc}男女生表现差异分析报告"
    else:
        return f"{classes}成绩教学质量分析报告"


def build_cover_info(result: dict, generated_at: str) -> dict:
    overview = result.get("data_overview", {})
    return {
        "title": build_title(result),
        "subtitle": "教学质量分析报告",
        "analysis_target": overview.get(
            "分析对象",
            _class_list(result.get("class_names", [])),
        ),
        "generated_at": generated_at,
        "data_source": "用户提供的 Excel 成绩表",
        "students": overview.get("学生人数", 0),
        "subjects": overview.get("科目数量", 0),
    }


def build_abstract(result: dict) -> str:
    overview = result.get("data_overview", {})
    summary = result.get("summary", {})
    ctx = _gender_context(result)

    primary = result.get("primary_item", "")
    class_count = overview.get('班级数量', 0)
    student_count = overview.get('学生人数', 0)
    parts = [
        f"本报告基于{class_count}"
        f"个班级、合计{student_count}"
        f"名学生的成绩数据，"
        f"以{_q(primary)}为主要分析口径，",
    ]
    if ctx:
        parts.insert(1, f"聚焦{ctx}，")

    parts.append(
        "从整体表现、达标情况、学科结构、"
        "学生分层、偏科均衡性和年级竞争力"
        "等维度展开系统分析。"
    )

    if summary:
        if summary.get("best_average"):
            parts.append(
                f"整体平均分方面，"
                f"{summary['best_average']}表现较突出。"
            )
        if summary.get("best_good_rate"):
            parts.append(
                f"优良率方面，"
                f"{summary['best_good_rate']}中高分段占比更高。"
            )

    parts.append(
        "报告在数据分析基础上给出教学建议，"
        "供教研参考和后续跟踪使用。"
    )
    return "".join(parts)


def build_section_1_data_overview(result: dict) -> dict:
    overview = result.get("data_overview", {})
    thresholds = result.get("thresholds", {})
    gender_desc = result.get("gender_rule_description", "")
    filter_desc = result.get("filter_description", "")

    primary_item = overview.get('主要分析口径', "")
    class_count = overview.get('班级数量', 0)
    student_count = overview.get('学生人数', 0)
    subject_count = overview.get('科目数量', 0)
    paragraphs = [
        f"本次分析覆盖{class_count}"
        f"个班级，合计{student_count}"
        f"名学生，"
        f"识别到{subject_count}"
        f"个单科成绩项目。主要分析口径为"
        f"{_q(primary_item)}。",
    ]

    if filter_desc:
        paragraphs.append(filter_desc)

    if gender_desc:
        paragraphs.append(gender_desc)

    paragraphs.append(
        "为保证不同分值尺度下的可比性，"
        "本报告将总分3转换为三科平均（总分3\xf73），"
        "将总分10转换为十科平均（总分10\xf710）后，"
        "再进行优秀率、优良率、及格率及分布分析。"
        "总分3班次、总分3年次、总分10班次、总分10年次"
        "属于排名字段，"
        "仅进入排名分析，不进入平均分、优良率、"
        "分布图等成绩图表。"
    )

    paragraphs.append(
        f"本次评价标准：优秀 ≥ {thresholds.get('excellent', 90):.0f}分，"
        f"优良 ≥ {thresholds.get('good', 80):.0f}分，"
        f"及格 ≥ {thresholds.get('pass', 60):.0f}分。"
        f"低分指低于{thresholds.get('pass', 60):.0f}分。"
    )

    paragraphs.append(
        "临界生定义：冲优秀临界 85-89 分，"
        "冲优良临界 75-79 分，"
        "及格临界 55-59 分，风险学生 55 分以下。"
    )

    if overview.get("是否有排名字段"):
        paragraphs.append(
            "本数据包含年级排名字段，可用于年级竞争力分析。"
            "年级百分位计算公式：1 - (年次 - 1) / 年级总人数。"
        )

    return {
        "heading": "一、数据说明与分析口径",
        "paragraphs": paragraphs,
        "figure_refs": [],
    }


def build_section_2_overall(result: dict) -> dict:
    rows = result.get("overall_rows", [])
    primary = result.get("primary_item", "")
    ctx = _gender_context(result)

    subject_label = f"{ctx}" if ctx else "各班"
    paragraphs = [
        f"以{_q(primary)}为主要观察口径，"
        f"{subject_label}整体成绩表现如下。"
    ]

    if len(rows) == 1:
        r = rows[0]
        paragraphs.append(
            f"平均分为 {format_number(r['平均分'])}，"
            f"中位数为 {format_number(r['中位数'])}，"
            f"最高分 {format_number(r['最高分'])}，"
            f"最低分 {format_number(r['最低分'])}，"
            f"极差 {format_number(r['极差'])}，"
            f"标准差 {format_number(r['标准差'])}。"
        )
    else:
        best_avg = _best(rows, "平均分")
        worst_avg = _worst(rows, "平均分")
        best_std = _worst(rows, "标准差")
        worst_std = _best(rows, "标准差")

        if best_avg and worst_avg:
            diff = _num(best_avg["平均分"]) - _num(worst_avg["平均分"])
            paragraphs.append(
                f"从平均分来看，"
                f"{best_avg['班级']}相对较高"
                f"（{format_number(best_avg['平均分'])}），"
                f"{worst_avg['班级']}相对较低"
                f"（{format_number(worst_avg['平均分'])}），"
                f"两者相差 {diff:.2f} 分。"
            )
        if best_std:
            paragraphs.append(
                f"从稳定性看，"
                f"{best_std['班级']}标准差最低"
                f"（{format_number(best_std['标准差'])}），"
                f"班内成绩分布更为集中。"
            )
        if worst_std and _num(worst_std["标准差"]) >= 14:
            paragraphs.append(
                f"{worst_std['班级']}标准差为 "
                f"{format_number(worst_std['标准差'])}，"
                f"提示班内学生差异较明显，"
                f"后续可关注中低分段学生的稳定提升。"
            )

    paragraphs.append(
        "平均分反映整体水平，中位数衡量典型学生表现，"
        "标准差和极差反映班内分化程度。"
        "三者的综合判断比单一指标更有教学参考价值。"
    )

    return {
        "heading": "二、整体表现分析",
        "paragraphs": paragraphs,
        "figure_refs": ["average", "stability", "distribution"],
    }


def build_section_3_quality(result: dict) -> dict:
    rows = result.get("overall_rows", [])
    ctx = _gender_context(result)
    subject_label = f"{ctx}" if ctx else "各班"

    paragraphs = [
        f"优秀率、优良率、及格率和低分率是"
        f"衡量{subject_label}整体达标水平的核心指标。"
    ]

    best_good = _best(rows, "优良率")
    worst_good = _worst(rows, "优良率")
    worst_pass = _worst(rows, "及格率")

    if best_good:
        paragraphs.append(
            f"{best_good['班级']}优良率为 "
            f"{format_rate(best_good['优良率'])}，"
            f"说明该班中高分段学生占比较高。"
        )
    if worst_good and best_good and worst_good["班级"] != best_good["班级"]:
        paragraphs.append(
            f"{worst_good['班级']}优良率为 "
            f"{format_rate(worst_good['优良率'])}，"
            f"与领先班级存在一定差距，"
            f"建议关注中高分段学生的培养和拔高。"
        )
    if worst_pass and _num(worst_pass["及格率"]) < 90:
        paragraphs.append(
            f"{worst_pass['班级']}及格率为 "
            f"{format_rate(worst_pass['及格率'])}，"
            f"不及格学生占 "
            f"{format_rate(worst_pass['低分率'])}，"
            f"建议优先关注及格线附近学生的基础巩固。"
        )

    paragraphs.append(
        f"分数段结构可以帮助教师直观判断"
        f"班级成绩的{_q('金字塔')}形态。"
        f"理想的成绩结构应当是底部窄、中部宽、"
        f"顶部有一定比例的优秀层。"
    )

    return {
        "heading": "三、达标情况分析",
        "paragraphs": paragraphs,
        "figure_refs": ["quality", "segment"],
    }


def build_section_4_core(result: dict) -> dict | None:
    all_data = result.get("_all_data")
    class_names = result.get("class_names", [])

    if all_data is None or all_data.empty:
        return None

    subjects = ["语文", "数学", "外语"]
    available = [s for s in subjects if s in all_data["分析项"].values]
    if not available:
        return None

    paragraphs = [
        "语文、数学、外语是高中阶段综合成绩的重要基础，"
        "三科基础直接影响总分3排名和后续选科竞争力。"
    ]

    for cn in class_names:
        parts = [f"{cn}："]
        for subj in available:
            subset = all_data[(all_data["班级"] == cn) & (all_data["分析项"] == subj)]
            if not subset.empty:
                avg = subset["成绩"].mean()
                parts.append(f"{subj}平均 {avg:.2f}")
        paragraphs.append("，".join(parts))

    avg_3 = all_data[all_data["分析项"] == "三科平均"]
    if not avg_3.empty:
        for cn in class_names:
            subset = avg_3[avg_3["班级"] == cn]
            if not subset.empty:
                m = subset["成绩"].mean()
                good_rate = (subset["成绩"] >= 80).sum() / len(subset) * 100
                paragraphs.append(
                    f"{cn}三科平均为 {m:.2f}，"
                    f"优良率 {format_rate(good_rate)}。"
                )

    paragraphs.append(
        "主科稳定的学生，综合成绩往往也具有较强的稳定性。"
        "若某班主科平均或三科优良率明显偏低，"
        "建议优先从基础题型梳理、"
        "课堂即时反馈和错题归因三个环节入手。"
    )

    return {
        "heading": "四、主科基础分析",
        "paragraphs": paragraphs,
        "figure_refs": ["core_subjects"],
    }


def build_section_5_ten_subjects(result: dict) -> dict | None:
    subject_rows = result.get("subject_rows", [])

    if not subject_rows:
        return None

    paragraphs = [
        "十科平均用于观察学生综合学习状态，"
        "各科平均分和优良率帮助识别"
        "优势学科、薄弱学科和可能存在明显分化的学科。"
    ]

    class_names = result.get("class_names", [])
    for cn in class_names:
        class_subs = [r for r in subject_rows if r["班级"] == cn]
        if not class_subs:
            continue
        sorted_subs = sorted(class_subs, key=lambda r: _num(r["平均分"]), reverse=True)
        strong = sorted_subs[:2]
        weak = sorted_subs[-2:]
        paragraphs.append(
            f"{cn}：优势学科为"
            f"{'、'.join(s['学科'] for s in strong)}"
            f"（平均分分别为"
            f"{'、'.join(s['平均分'] for s in strong)}），"
            f"薄弱学科为"
            f"{'、'.join(s['学科'] for s in weak)}"
            f"（平均分分别为"
            f"{'、'.join(s['平均分'] for s in weak)}）。"
        )

    high_std_subs = [r for r in subject_rows if _num(r["标准差"]) >= 12]
    if high_std_subs:
        subjects_set = {r['学科'] for r in high_std_subs}
        paragraphs.append(
            f"在分化程度方面，"
            f"{'、'.join(subjects_set)}"
            f"等学科标准差较高，提示学生间差异较大，"
            f"建议教学中关注差异化策略。"
        )

    paragraphs.append(
        "后续教研建议围绕薄弱学科进行题型归因，"
        "明确是知识掌握、审题习惯还是训练节奏造成的差异。"
    )

    return {
        "heading": "五、十科综合与单科结构分析",
        "paragraphs": paragraphs,
        "figure_refs": ["subject_heatmap", "subject_quality"],
    }


def build_section_6_rank(result: dict) -> dict | None:
    rank_rows = result.get("rank_rows", [])
    if not rank_rows:
        return None

    paragraphs = [
        "年级百分位基于年次字段估算，"
        "用于判断学生在年级中的相对竞争位置。"
        "百分位越高，表示年级内相对位置越靠前。"
    ]

    for r in rank_rows:
        rank_item = r['排名项目']
        paragraphs.append(
            f"{r['班级']}在{_q(rank_item)}口径下，"
            f"平均年级百分位 {r['平均年级百分位']}，"
            f"前10%学生 {r['前10%人数']} 人，"
            f"前25%学生 {r['前25%人数']} 人，"
            f"后25%学生 {r['后25%人数']} 人。"
        )

    paragraphs.append(
        "年级竞争力分析适合辅助判断班级在年级中的相对位置，"
        "但不应作为唯一评价依据，"
        "需结合平均分、优良率等指标综合判断。"
    )

    return {
        "heading": "六、排名与年级竞争力分析",
        "paragraphs": paragraphs,
        "figure_refs": ["grade_competitiveness"],
    }


def build_section_7_layering(result: dict) -> dict | None:
    layering_rows = result.get("layering_rows", [])
    if not layering_rows:
        return None

    paragraphs = [
        "学生分层将成绩结构拆分为优秀层（90及以上）、"
        "优良层（80-89）、"
        "中上层（70-79）、基础层（60-69）和待提升层（60以下），"
        "并进一步统计冲优秀临界生、冲优良临界生、"
        "及格临界生和风险学生数量。"
    ]

    for r in layering_rows:
        total = r.get("总人数", 1) or 1
        excellent_pct = r.get("优秀层(90及以上)", 0) / total * 100
        risk = r.get("风险学生(55以下)", 0)
        near_good = r.get("冲优良临界生(75-79)", 0)
        cls = r['班级']
        paragraphs.append(
            f"{cls}：优秀层 "
            f"{r.get('优秀层(90及以上)', 0)} 人（{excellent_pct:.1f}%），"
            f"冲优秀临界生 "
            f"{r.get('冲优秀临界生(85-89)', 0)} 人，"
            f"冲优良临界生 {near_good} 人，"
            f"及格临界生 "
            f"{r.get('及格临界生(55-59)', 0)} 人，"
            f"风险学生 {risk} 人。"
        )
        if risk > 0:
            paragraphs.append(
                f"{cls}存在 {risk} 名风险学生（55分以下），"
                f"建议重点关注其基础知识掌握情况，"
                f"制定个别化帮扶方案。"
            )

    paragraphs.append(
        "该模块更适合用于教学跟踪和帮扶安排。"
        "本报告只呈现统计数量，不暴露学生个人私信息。"
    )

    return {
        "heading": "七、分层与临界生分析",
        "paragraphs": paragraphs,
        "figure_refs": ["layering"],
    }


def build_section_8_balance(result: dict) -> dict | None:
    balance_rows = result.get("balance_rows", [])
    if not balance_rows:
        return None

    paragraphs = [
        "偏科指数以学生各科成绩的标准差来衡量，"
        "数值越高说明学生学科间差异越明显。"
        "主科稳定指数聚焦语文、数学、外语三科的标准差。"
    ]

    for r in balance_rows:
        cls = r['班级']
        paragraphs.append(
            f"{cls}：平均偏科指数 {r['平均偏科指数']}，"
            f"主科稳定指数 {r['主科稳定指数']}，"
            f"均衡型学生（偏科指数≤8）"
            f"{r['均衡型学生(偏科指数≤8)']} 人，"
            f"偏科明显学生（偏科指数≥18）"
            f"{r['偏科明显学生(偏科指数≥18)']} 人，"
            f"班级优势科目为{r['优势科目']}，"
            f"短板科目为{r['短板科目']}。"
        )

    paragraphs.append(
        f"对偏科明显学生，建议采用"
        f"{_q('一科一策')}的短板补强方式，"
        f"同时保留其优势科目的信心来源，"
        f"避免因单纯用总分评价而忽视学科特长。"
    )

    return {
        "heading": "八、偏科与均衡性分析",
        "paragraphs": paragraphs,
        "figure_refs": ["balance"],
    }


def build_section_9_gender(result: dict) -> dict | None:
    gender_rows = result.get("gender_rows", [])
    rt = result.get("report_type", "overall")

    if not gender_rows:
        return None

    if rt in ("female_only", "male_only"):
        return None

    paragraphs = [
        "基于性别维度的分析有助于了解男女生在成绩结构上的差异，"
        "为差异化教学提供数据参考。"
    ]

    for r in gender_rows:
        cls = r['班级']
        group = r['分组']
        paragraphs.append(
            f"{cls}{group}：平均分 {format_number(r['平均分'])}，"
            f"优良率 {format_rate(r['优良率'])}，"
            f"及格率 {format_rate(r['及格率'])}，"
            f"标准差 {format_number(r['标准差'])}。"
        )

    class_names = sorted(set(r["班级"] for r in gender_rows))
    for cn in class_names:
        male = next((r for r in gender_rows if r["班级"] == cn and r["分组"] == "男生"), None)
        female = next((r for r in gender_rows if r["班级"] == cn and r["分组"] == "女生"), None)
        if male and female:
            diff = _num(male["平均分"]) - _num(female["平均分"])
            if abs(diff) > 1:
                higher = "男生" if diff > 0 else "女生"
                paragraphs.append(
                    f"{cn}内部：{higher}平均分高出 {abs(diff):.2f} 分，"
                    f"提示可能存在的性别差异值得进一步关注。"
                )

    paragraphs.append(
        "性别差异分析应结合课堂参与、作业完成和学科兴趣等"
        "多元因素综合判断，"
        "避免简单归因或标签化。"
    )

    return {
        "heading": "九、性别专项分析",
        "paragraphs": paragraphs,
        "figure_refs": ["gender"],
    }


def build_section_10_conclusions(result: dict) -> dict:
    rows = result.get("overall_rows", [])
    primary = result.get("primary_item", "")
    ctx = _gender_context(result)
    subject_label = f"{ctx}" if ctx else "各班"

    paragraphs = []

    best_avg = _best(rows, "平均分")
    best_good = _best(rows, "优良率")
    most_stable = _worst(rows, "标准差")
    worst_pass = _worst(rows, "及格率")

    if best_avg:
        cls = best_avg['班级']
        avg = format_number(best_avg['平均分'])
        paragraphs.append(
            f"从整体成绩来看，以{_q(primary)}为口径，"
            f"{cls}平均分相对较高（{avg}），"
            f"说明该班{subject_label}整体学习基础较为扎实。"
        )
    if best_good:
        cls = best_good['班级']
        rate = format_rate(best_good['优良率'])
        paragraphs.append(
            f"{cls}优良率达到 {rate}，"
            f"中高分段学生占比较高，"
            f"在教学策略上有一定的示范价值。"
        )
    if most_stable:
        cls = most_stable['班级']
        std = format_number(most_stable['标准差'])
        paragraphs.append(
            f"{cls}标准差最低（{std}），"
            f"成绩分布更集中，班内学生水平较为齐整。"
        )
    if worst_pass and _num(worst_pass["及格率"]) < 90:
        cls = worst_pass['班级']
        rate = format_rate(worst_pass['及格率'])
        paragraphs.append(
            f"需要关注的是，{cls}及格率为 {rate}，"
            f"仍有提升空间，建议优先帮扶及格线附近学生。"
        )

    balance_rows = result.get("balance_rows", [])
    if balance_rows:
        high_bias = max(balance_rows, key=lambda r: _num(r["平均偏科指数"]))
        cls = high_bias['班级']
        bias_val = high_bias['平均偏科指数']
        strong_subj = high_bias.get('优势科目', '')
        weak_subj = high_bias.get('短板科目', '')
        paragraphs.append(
            f"偏科方面，{cls}平均偏科指数较高"
            f"（{bias_val}），"
            f"建议结合优势科目{strong_subj}"
            f"和短板科目{weak_subj}进行针对性补强。"
        )

    layering_rows = result.get("layering_rows", [])
    if layering_rows:
        total_risk = sum(r.get("风险学生(55以下)", 0) for r in layering_rows)
        total_near = sum(r.get("及格临界生(55-59)", 0) for r in layering_rows)
        if total_risk > 0:
            paragraphs.append(
                f"本次分析共识别 {total_risk} 名风险学生"
                f"（55分以下），"
                f"{total_near} 名及格临界生（55-59分），"
                f"建议对这两类学生建立重点跟踪和帮扶机制。"
            )

    return {
        "heading": "十、主要发现与结论",
        "paragraphs": paragraphs if paragraphs else [
            "本次分析未发现需要特别关注的异常指标。"
        ],
        "figure_refs": [],
    }


def build_section_11_suggestions(result: dict) -> dict:
    rows = result.get("overall_rows", [])
    rt = result.get("report_type", "overall")

    suggestions = []

    weak_pass = _worst(rows, "及格率")
    if weak_pass and _num(weak_pass["及格率"]) < 95:
        cls = weak_pass['班级']
        suggestions.append(
            f"及格率提升建议：关注{cls}及格线附近学生"
            f"（55-59分），"
            f"建立错题归因记录，区分知识漏洞、审题习惯和"
            f"训练不足等不同原因，"
            f"有针对性地布置基础巩固练习。"
        )

    high_std = _best(rows, "标准差")
    if high_std and _num(high_std["标准差"]) >= 12:
        cls = high_std['班级']
        suggestions.append(
            f"分层教学建议：{cls}班内差异较明显，"
            f"建议在课堂练习中采用分层设计，"
            f"为不同层次学生提供差异化任务，"
            f"同时利用小步反馈机制帮助中低分段学生"
            f"建立稳定的提升路径。"
        )

    suggestions.append(
        "主科提升建议：语数外三科是总分3的核心构成，"
        "建议优先梳理基础题型和常见失分点，"
        "建立课堂即时反馈机制，"
        "确保主科对综合成绩形成稳定支撑。"
    )

    layering_rows = result.get("layering_rows", [])
    if layering_rows:
        suggestions.append(
            f"临界生管理建议：对冲优秀、冲优良和"
            f"及格临界生建立名单化跟踪，"
            f"按照{_q('一人一策')}原则制定阶段目标，"
            f"定期复盘进步情况并及时调整策略。"
        )

    if result.get("balance_rows"):
        suggestions.append(
            "偏科干预建议：对偏科明显学生，"
            "避免因总分评价而掩盖其学科特长，"
            "一方面保持优势科目的学习信心，"
            "另一方面通过专项练习和个别辅导补齐短板。"
        )

    if rt == "female_only":
        suggestions.append(
            "女生群体建议：在保持女生群体整体优势的基础上，"
            "关注理科思维训练和应试心理建设，"
            "同时关注女生在物理、化学等学科的持续兴趣培养。"
        )
    elif rt == "male_only":
        suggestions.append(
            f"男生群体建议：针对男生群体常见的"
            f"{_q('重理轻文')}倾向，"
            f"加强语文和外语学科的阅读积累和表达训练，"
            f"同时引导男生在优势理科科目上追求更高层次。"
        )
    elif rt == "class_gender_compare":
        suggestions.append(
            "性别差异教学建议：根据本班男女生在不同学科上的表现差异，"
            "在课堂提问、作业布置和课后辅导中注意性别均衡，"
            "避免形成固定的学科性别刻板印象。"
        )

    suggestions.append(
        "后续跟踪建议：建议在下一次阶段测试后继续使用"
        "同一口径和分析框架，"
        "重点观察本次报告中指出的薄弱环节和临界生群体的变化趋势，"
        "为学期末教学质量总结提供数据支撑。"
    )

    return {
        "heading": "十一、教学建议",
        "paragraphs": suggestions,
        "figure_refs": [],
    }


def build_closing(result: dict) -> dict:
    return {
        "heading": "结语",
        "paragraphs": [
            "本次教学质量分析报告通过对成绩数据的多维度解析，"
            "从整体水平、达标结构、学科优劣、学生分层和偏科均衡性等角度，"
            "为教师提供了较为全面的数据参考。",
            "数据本身不能替代教师的专业判断，但可以帮助教师从日常教学中"
            "发现结构性问题，并为后续课堂教学、分层辅导和阶段跟踪提供依据。",
            "建议以本次报告为基线，在下一阶段测试后持续复盘变化，"
            f"形成{_q('分析—教学—评估—再分析')}的闭环，"
            "逐步提升教学针对性。",
        ],
        "figure_refs": [],
    }


def build_report(result: dict, generated_at: str) -> dict:
    sections = []

    sections.append(build_section_1_data_overview(result))
    sections.append(build_section_2_overall(result))
    sections.append(build_section_3_quality(result))

    sec4 = build_section_4_core(result)
    if sec4:
        sections.append(sec4)

    sec5 = build_section_5_ten_subjects(result)
    if sec5:
        sections.append(sec5)

    sec6 = build_section_6_rank(result)
    if sec6:
        sections.append(sec6)

    sec7 = build_section_7_layering(result)
    if sec7:
        sections.append(sec7)

    sec8 = build_section_8_balance(result)
    if sec8:
        sections.append(sec8)

    sec9 = build_section_9_gender(result)
    if sec9:
        sections.append(sec9)

    sections.append(build_section_10_conclusions(result))
    sections.append(build_section_11_suggestions(result))
    sections.append(build_closing(result))

    return {
        "title": build_title(result),
        "cover": build_cover_info(result, generated_at),
        "abstract": build_abstract(result),
        "sections": sections,
        "chart_paths": result.get("chart_paths", {}),
        "warnings": result.get("warnings", []),
    }
