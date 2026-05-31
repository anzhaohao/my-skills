from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd


WARM_COLORS = [
    "#4F8F7F",
    "#D9A441",
    "#8AA8C8",
    "#D98982",
    "#8FB996",
    "#B7A4D8",
    "#C7A27C",
]

WARM_BG = "#FAFAF8"
WARM_GRID = "#E8E4DC"
WARM_TEXT = "#3A3630"


def _setup_chinese_font():
    """Configure matplotlib for Chinese font display."""
    font_candidates = [
        "Microsoft YaHei",
        "SimHei",
        "PingFang SC",
        "WenQuanYi Micro Hei",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
    ]
    import matplotlib.font_manager as fm
    available = {f.name for f in fm.fontManager.ttflist}
    for font in font_candidates:
        if font in available:
            plt.rcParams["font.sans-serif"] = [font, "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
            return font
    # Fallback: try to find any CJK font
    for f in fm.fontManager.ttflist:
        if any(kw in f.name.lower() for kw in ["cjk", "hei", "song", "ming", "yahei", "chinese"]):
            plt.rcParams["font.sans-serif"] = [f.name, "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
            return f.name
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return "DejaVu Sans"


_setup_chinese_font()


def _set_style():
    """Apply warm, clean style to matplotlib."""
    plt.rcParams.update({
        "figure.facecolor": WARM_BG,
        "axes.facecolor": WARM_BG,
        "axes.edgecolor": WARM_GRID,
        "axes.labelcolor": WARM_TEXT,
        "text.color": WARM_TEXT,
        "xtick.color": WARM_TEXT,
        "ytick.color": WARM_TEXT,
        "grid.color": WARM_GRID,
        "grid.alpha": 0.6,
        "axes.grid": True,
        "grid.linestyle": "--",
        "grid.linewidth": 0.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.framealpha": 0.85,
        "legend.edgecolor": WARM_GRID,
        "legend.fontsize": 9,
    })


_set_style()


def _save_and_close(fig, output_dir: Path, name: str) -> str:
    """Save figure as PNG and close."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{name}.png"
    fig.savefig(str(path), dpi=150, bbox_inches="tight",
                facecolor=WARM_BG, edgecolor="none")
    plt.close(fig)
    return str(path)


def _num(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, str):
        value = value.replace("%", "").strip()
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


# ─── Chart builders ─────────────────────────────────────────────────────

def average_bar_chart(overall_rows: list[dict], primary_item: str,
                      output_dir: Path) -> str:
    """各班平均分对比水平条形图"""
    rows = [r for r in overall_rows if r.get("人数", 0)]
    if not rows:
        return ""
    rows = sorted(rows, key=lambda r: r["平均分"])
    labels = [r["班级"] for r in rows]
    values = [r["平均分"] for r in rows]

    fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.55)))
    bars = ax.barh(labels, values, color=WARM_COLORS[0], height=0.55, edgecolor="none")
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", va="center", fontsize=9.5, color=WARM_TEXT)
    ax.set_xlabel("平均分", fontsize=10)
    ax.set_title(f"各班平均分对比（{primary_item}）", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlim(0, max(values) * 1.15 if values else 100)
    ax.tick_params(labelsize=9.5)
    fig.tight_layout()
    return _save_and_close(fig, output_dir, "chart_average")


def quality_rate_chart(overall_rows: list[dict], output_dir: Path) -> str:
    """各班达标率结构对比"""
    rows = [r for r in overall_rows if r.get("人数", 0)]
    if not rows:
        return ""
    labels = [r["班级"] for r in rows]
    metrics = ["优秀率", "优良率", "及格率", "低分率"]
    data = {m: [r[m] for r in rows] for m in metrics}

    x = np.arange(len(labels))
    width = 0.18
    fig, ax = plt.subplots(figsize=(max(7, len(labels) * 1.5), 4.5))

    for i, (metric, color) in enumerate(zip(metrics, WARM_COLORS[:4])):
        bars = ax.bar(x + i * width, data[metric], width, label=metric,
                      color=color, edgecolor="none")
        for bar in bars:
            h = bar.get_height()
            if h > 2:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.5,
                        f"{h:.1f}%", ha="center", fontsize=7.5, color=WARM_TEXT)

    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_ylabel("比例（%）", fontsize=10)
    ax.set_title("各班达标率结构对比", fontsize=13, fontweight="bold", pad=12)
    ax.legend(loc="upper right", ncol=2)
    ax.set_ylim(0, 105)
    ax.tick_params(labelsize=9)
    fig.tight_layout()
    return _save_and_close(fig, output_dir, "chart_quality")


def subject_heatmap(subject_rows: list[dict], output_dir: Path) -> str:
    """各科平均分热力图"""
    if not subject_rows:
        return ""
    class_names = sorted(set(r["班级"] for r in subject_rows))
    subjects = list(dict.fromkeys(r["学科"] for r in subject_rows))

    data = np.zeros((len(class_names), len(subjects)))
    for i, cn in enumerate(class_names):
        for j, subj in enumerate(subjects):
            for r in subject_rows:
                if r["班级"] == cn and r["学科"] == subj:
                    data[i, j] = _num(r["平均分"])
                    break

    fig, ax = plt.subplots(figsize=(max(8, len(subjects) * 0.9), max(2.5, len(class_names) * 0.6)))
    im = ax.imshow(data, cmap="YlOrRd", aspect="auto", vmin=data.min() * 0.9 if data.size else 0)

    for i in range(len(class_names)):
        for j in range(len(subjects)):
            ax.text(j, i, f"{data[i, j]:.1f}", ha="center", va="center",
                    fontsize=8.5, color="white" if data[i, j] < data.mean() else WARM_TEXT)

    ax.set_xticks(range(len(subjects)))
    ax.set_xticklabels(subjects, fontsize=8.5, rotation=30, ha="right")
    ax.set_yticks(range(len(class_names)))
    ax.set_yticklabels(class_names, fontsize=9.5)
    ax.set_title("各科平均分热力图", fontsize=13, fontweight="bold", pad=12)
    fig.colorbar(im, ax=ax, shrink=0.8, label="平均分")
    fig.tight_layout()
    return _save_and_close(fig, output_dir, "chart_heatmap")


def segment_chart(segment_rows: list[dict], output_dir: Path) -> str:
    """分数段结构堆叠条形图"""
    if not segment_rows:
        return ""
    labels = [r["班级"] for r in segment_rows]
    keys = [k for k in segment_rows[0].keys() if k not in ("班级", "总人数")]
    data = {k: [r.get(k, 0) for r in segment_rows] for k in keys}

    fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.55)))
    left = np.zeros(len(labels))
    for i, (key, color) in enumerate(zip(keys, WARM_COLORS)):
        vals = data[key]
        bars = ax.barh(labels, vals, left=left, color=color, height=0.55,
                       label=key, edgecolor="none")
        for j, (bar, val) in enumerate(zip(bars, vals)):
            if val > 0:
                ax.text(left[j] + val / 2, bar.get_y() + bar.get_height() / 2,
                        str(val), ha="center", va="center", fontsize=7.8, color="white")
        left += vals

    ax.set_xlabel("人数", fontsize=10)
    ax.set_title("分数段结构", fontsize=13, fontweight="bold", pad=12)
    ax.legend(loc="lower right", fontsize=8, ncol=2)
    ax.tick_params(labelsize=9.5)
    fig.tight_layout()
    return _save_and_close(fig, output_dir, "chart_segment")


def layering_chart(layering_rows: list[dict], output_dir: Path) -> str:
    """学生分层结构"""
    if not layering_rows:
        return ""
    labels = [r["班级"] for r in layering_rows]
    keys = ["优秀层(90及以上)", "优良层(80-89)", "中上层(70-79)",
            "基础层(60-69)", "待提升层(60以下)"]
    data = {k: [r.get(k, 0) for r in layering_rows] for k in keys}

    fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.55)))
    left = np.zeros(len(labels))
    for key, color in zip(keys, WARM_COLORS):
        vals = data[key]
        bars = ax.barh(labels, vals, left=left, color=color, height=0.55,
                       label=key, edgecolor="none")
        for j, (bar, val) in enumerate(zip(bars, vals)):
            if val > 0:
                ax.text(left[j] + val / 2, bar.get_y() + bar.get_height() / 2,
                        str(val), ha="center", va="center", fontsize=7.8, color="white")
        left += vals

    ax.set_xlabel("人数", fontsize=10)
    ax.set_title("学生分层结构", fontsize=13, fontweight="bold", pad=12)
    ax.legend(loc="lower right", fontsize=8, ncol=2)
    ax.tick_params(labelsize=9.5)
    fig.tight_layout()
    return _save_and_close(fig, output_dir, "chart_layering")


def core_subject_chart(overall_rows: list[dict], all_data: pd.DataFrame,
                       output_dir: Path) -> str:
    """语数外主科基础对比"""
    if all_data is None or all_data.empty:
        return ""
    subjects = ["语文", "数学", "外语"]
    available = [s for s in subjects if s in all_data["分析项"].values]
    if not available:
        return ""

    class_names = sorted(all_data["班级"].drop_duplicates().tolist())
    x = np.arange(len(class_names))
    width = 0.22
    fig, ax = plt.subplots(figsize=(max(7, len(class_names) * 1.3), 4.5))

    for i, (subj, color) in enumerate(zip(available, WARM_COLORS[:len(available)])):
        vals = []
        for cn in class_names:
            subset = all_data[(all_data["班级"] == cn) & (all_data["分析项"] == subj)]
            v = subset["成绩"].mean() if not subset.empty else 0
            vals.append(v)
        bars = ax.bar(x + i * width, vals, width, label=subj, color=color, edgecolor="none")
        for bar, v in zip(bars, vals):
            if v:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                        f"{v:.1f}", ha="center", fontsize=8, color=WARM_TEXT)

    ax.set_xticks(x + width * (len(available) - 1) / 2)
    ax.set_xticklabels(class_names, fontsize=9.5)
    ax.set_ylabel("平均分", fontsize=10)
    ax.set_title("语数外主科基础对比", fontsize=13, fontweight="bold", pad=12)
    ax.legend(fontsize=9)
    ax.tick_params(labelsize=9)
    fig.tight_layout()
    return _save_and_close(fig, output_dir, "chart_core")


def grade_percentile_chart(rank_rows: list[dict], output_dir: Path) -> str:
    """年级竞争力对比"""
    rows = [r for r in rank_rows if r.get("平均年级百分位", "-") != "-"]
    if not rows:
        return ""
    focus = [r for r in rows if "总分" in r.get("排名项目", "")]
    use = focus or rows[:12]
    labels = [f"{r['班级']} · {r['排名项目']}" for r in use]
    values = [_num(r["平均年级百分位"]) for r in use]

    fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.5)))
    bars = ax.barh(labels, values, color=WARM_COLORS[2], height=0.5, edgecolor="none")
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=9, color=WARM_TEXT)
    ax.set_xlabel("百分位（越高越靠前）", fontsize=10)
    ax.set_title("年级竞争力：平均年级百分位", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlim(0, 105)
    ax.tick_params(labelsize=9.5)
    fig.tight_layout()
    return _save_and_close(fig, output_dir, "chart_grade")


def stability_chart(all_data: pd.DataFrame, primary_item: str,
                    class_names: list[str], output_dir: Path) -> str:
    """稳定性箱线图"""
    if all_data is None or all_data.empty:
        return ""
    subset = all_data[all_data["分析项"] == primary_item]
    if subset.empty:
        return ""
    data_groups = []
    labels = []
    for cn in class_names:
        scores = pd.to_numeric(
            subset.loc[subset["班级"] == cn, "成绩"], errors="coerce"
        ).dropna()
        if not scores.empty:
            data_groups.append(scores.tolist())
            labels.append(cn)

    if not data_groups:
        return ""
    fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.55)))
    bp = ax.boxplot(data_groups, labels=labels, vert=False, patch_artist=True,
                    widths=0.5, showmeans=True,
                    meanprops=dict(marker="D", markerfacecolor=WARM_COLORS[3], markersize=6))
    for patch, color in zip(bp["boxes"], WARM_COLORS[:len(labels)]):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.set_xlabel("分数", fontsize=10)
    ax.set_title(f"稳定性分析（{primary_item}）", fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(labelsize=9.5)
    fig.tight_layout()
    return _save_and_close(fig, output_dir, "chart_stability")


def balance_chart(balance_rows: list[dict], output_dir: Path) -> str:
    """偏科指数对比"""
    if not balance_rows:
        return ""
    rows = sorted(balance_rows, key=lambda r: _num(r["平均偏科指数"]))
    labels = [r["班级"] for r in rows]
    values = [_num(r["平均偏科指数"]) for r in rows]

    fig, ax = plt.subplots(figsize=(7, max(3, len(labels) * 0.55)))
    bars = ax.barh(labels, values, color=WARM_COLORS[5], height=0.5, edgecolor="none")
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", va="center", fontsize=9, color=WARM_TEXT)
    ax.set_xlabel("偏科指数（越低越均衡）", fontsize=10)
    ax.set_title("偏科与均衡性分析", fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(labelsize=9.5)
    fig.tight_layout()
    return _save_and_close(fig, output_dir, "chart_balance")


def gender_chart(gender_rows: list[dict], output_dir: Path) -> str:
    """男女生对比图"""
    if not gender_rows:
        return ""
    rows = [r for r in gender_rows if r.get("人数", 0)]
    if not rows:
        return ""
    class_names = sorted(set(r["班级"] for r in rows))
    x = np.arange(len(class_names))
    width = 0.3
    male_vals = []
    female_vals = []
    for cn in class_names:
        male_vals.append(next(
            (r["平均分"] for r in rows if r["班级"] == cn and r["分组"] == "男生"), 0
        ))
        female_vals.append(next(
            (r["平均分"] for r in rows if r["班级"] == cn and r["分组"] == "女生"), 0
        ))

    fig, ax = plt.subplots(figsize=(max(6, len(class_names) * 1.2), 4))
    b1 = ax.bar(x - width / 2, male_vals, width, label="男生",
                color=WARM_COLORS[2], edgecolor="none")
    b2 = ax.bar(x + width / 2, female_vals, width, label="女生",
                color=WARM_COLORS[3], edgecolor="none")
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            if h:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.3,
                        f"{h:.1f}", ha="center", fontsize=8, color=WARM_TEXT)

    ax.set_xticks(x)
    ax.set_xticklabels(class_names, fontsize=9.5)
    ax.set_ylabel("平均分", fontsize=10)
    ax.set_title("男女生平均分对比", fontsize=13, fontweight="bold", pad=12)
    ax.legend(fontsize=10)
    ax.tick_params(labelsize=9)
    fig.tight_layout()
    return _save_and_close(fig, output_dir, "chart_gender")


def subject_detailed_chart(subject_rows: list[dict], output_dir: Path) -> str:
    """各科优良率对比分组条形图"""
    if not subject_rows:
        return ""
    class_names = sorted(set(r["班级"] for r in subject_rows))
    subjects = list(dict.fromkeys(r["学科"] for r in subject_rows))

    fig, ax = plt.subplots(figsize=(max(8, len(subjects) * 1.1), 4.5))
    x = np.arange(len(subjects))
    width = 0.8 / len(class_names) if class_names else 0.2

    for i, cn in enumerate(class_names):
        vals = []
        for subj in subjects:
            for r in subject_rows:
                if r["班级"] == cn and r["学科"] == subj:
                    vals.append(_num(r["优良率"]))
                    break
            else:
                vals.append(0)
        ax.bar(x + i * width, vals, width, label=cn,
               color=WARM_COLORS[i % len(WARM_COLORS)], edgecolor="none")

    ax.set_xticks(x + width * (len(class_names) - 1) / 2)
    ax.set_xticklabels(subjects, fontsize=9, rotation=25, ha="right")
    ax.set_ylabel("优良率（%）", fontsize=10)
    ax.set_title("各科优良率对比", fontsize=13, fontweight="bold", pad=12)
    ax.legend(fontsize=9)
    ax.tick_params(labelsize=9)
    ax.set_ylim(0, 105)
    fig.tight_layout()
    return _save_and_close(fig, output_dir, "chart_subject_quality")


def distribution_chart(all_data: pd.DataFrame, primary_item: str,
                       class_names: list[str], output_dir: Path) -> str:
    """分数分布直方图"""
    if all_data is None or all_data.empty:
        return ""
    subset = all_data[all_data["分析项"] == primary_item]
    if subset.empty:
        return ""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for i, cn in enumerate(class_names):
        scores = pd.to_numeric(
            subset.loc[subset["班级"] == cn, "成绩"], errors="coerce"
        ).dropna()
        if scores.empty:
            continue
        ax.hist(scores, bins=12, alpha=0.55, label=cn,
                color=WARM_COLORS[i % len(WARM_COLORS)], edgecolor="white", linewidth=0.5)

    ax.set_xlabel("分数", fontsize=10)
    ax.set_ylabel("人数", fontsize=10)
    ax.set_title(f"分数分布图（{primary_item}）", fontsize=13, fontweight="bold", pad=12)
    ax.legend(fontsize=9)
    ax.tick_params(labelsize=9)
    fig.tight_layout()
    return _save_and_close(fig, output_dir, "chart_distribution")


# ─── Main chart generation ──────────────────────────────────────────────

def build_all_charts(result: dict[str, Any], output_dir: Path) -> dict[str, str]:
    """Generate all applicable charts and return path mapping."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    charts: dict[str, str] = {}

    overall = result.get("overall_rows", [])
    primary = result.get("primary_item", "")
    class_names = result.get("class_names", [])
    all_data = result.get("_all_data")

    # 1. Average bar chart
    path = average_bar_chart(overall, primary, output_dir)
    if path:
        charts["average"] = path

    # 2. Quality rate chart
    path = quality_rate_chart(overall, output_dir)
    if path:
        charts["quality"] = path

    # 3. Subject heatmap
    path = subject_heatmap(result.get("subject_rows", []), output_dir)
    if path:
        charts["subject_heatmap"] = path

    # 4. Subject quality comparison
    path = subject_detailed_chart(result.get("subject_rows", []), output_dir)
    if path:
        charts["subject_quality"] = path

    # 5. Segment structure
    path = segment_chart(result.get("segment_rows", []), output_dir)
    if path:
        charts["segment"] = path

    # 6. Distribution
    path = distribution_chart(all_data, primary, class_names, output_dir)
    if path:
        charts["distribution"] = path

    # 7. Stability boxplot
    path = stability_chart(all_data, primary, class_names, output_dir)
    if path:
        charts["stability"] = path

    # 8. Core subjects
    path = core_subject_chart(overall, all_data, output_dir)
    if path:
        charts["core_subjects"] = path

    # 9. Grade competitiveness
    path = grade_percentile_chart(result.get("rank_rows", []), output_dir)
    if path:
        charts["grade_competitiveness"] = path

    # 10. Layering
    path = layering_chart(result.get("layering_rows", []), output_dir)
    if path:
        charts["layering"] = path

    # 11. Balance
    path = balance_chart(result.get("balance_rows", []), output_dir)
    if path:
        charts["balance"] = path

    # 12. Gender comparison
    path = gender_chart(result.get("gender_rows", []), output_dir)
    if path:
        charts["gender"] = path

    return charts
