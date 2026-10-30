# -*- coding: utf-8 -*-
"""组会 PPT 骨架 —— 复制这个文件改内容就能出一套。

改三处：PROJECT（ppt-master 项目目录）、各页的文案、FIG（论文图文件名）。
跑完依次执行（见 SKILL.md）：
    python svg_quality_checker.py <PROJECT> --quick-generate --canonical-authoring --stage final --json
    python svg_to_pptx.py <PROJECT> --quick-generate --no-notes
    python finalize.py --pptx <导出文件> --notes notes.json --out <交付文件>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svg_kit import *  # noqa

PROJECT = r"D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260429-ppt-master\output\20261030-模板示例"
FIG = "fig_example.png"          # 放在 <PROJECT>/images/ 下；不存在则跳过图页

d = Deck(PROJECT)

# ---------------------------------------------------------------- 01 封面
d.add("01_cover.svg", shell([band("shot", 49, 228, 1180, 486, [
    # 论文首页淡化截图：透明度 0.23 + 柔化边缘（见 finalize.py --soft-edge）
    img(55, 232, 1165, 480, "paper_first_page.png", 0.23)])],
    head_band=band("head", 26, 18, 1230, 200, [
        text(["English Title Line One of the Paper",
              "and Line Two Here"], 40, 64, 44, 700, INK, line_h=52),
        text([[("关键词", KEY_BLUE), ("用中文写一句话标题", None)]], 40, 198, 54, 700, INK)])))

# ---------------------------------------------------------------- 02 原理示意图
d.add("02_problem.svg", shell([
    band("fig", 34, 92, 1212, 500, [
        text(["一句话交代测量方式：一次采集 = 数百到数百万发的积分"], 60, 148, 28, 700, "#444444"),
        ] + [blob(150, 300, 74, 54, -18), blob(322, 300, 74, 54, -2), blob(494, 300, 74, 54, 15)] + [
        text(["每一发都不一样"], 322, 420, 26, 700, NAVY, anchor="middle"),
        arrow(596, 300, 668, 300),
        ] + [blob(900, 300, 218, 104, 4, fill=TINT, stroke="#C9C9C9", sw=2.2, dash="9 7")] + [
        text(["积分得到的“平均轨迹”"], 900, 420, 26, 700, GREY, anchor="middle"),
        text([[("≠", KEY_RED), ("  任何一发真实轨迹", KEY_RED)]], 900, 480, 34, 700, KEY_RED, anchor="middle"),
        rect(60, 516, 1176, 52, "#FAFAFA", 6),
        text(["把这一步的物理后果一句话说清 —— 这才是本文的入口。"], 84, 553, 25, 700, "#333333")]),
    bar("结论条：一句话，关键词上色。")],
    head_band=head("研究背景——这里写你的说明")))

# ---------------------------------------------------------------- 03 流程图（方法）
boxes = [("输入", "一张 FROG 轨迹", "多发射积分图", NAVY),
         ("模型", "预训练 CNN", "只吃像素，不看坐标轴", NAVY),
         ("输出", "不稳定度 στ", "5 档分类 / 连续值", KEY_RED)]
flow = []
x = 60
for i, (tag, main, sub, col) in enumerate(boxes):
    flow.append(rect(x, 140, 320, 172, TINT, 12))
    flow.append(text([tag], x + 28, 182, 22, 700, GREY))
    flow.append(text([main], x + 28, 242, 30, 700, col))
    flow.append(text([sub], x + 28, 284, 21, 700, "#555555"))
    if i < 2:
        flow.append(arrow(x + 334, 222, x + 396, 222))
    x += 410
flow += [text(["传统做法"], 60, 424, 24, 700, GREY),
         text(["数分钟"], 60, 512, 64, 700, "#3A3A3A"),
         arrow(360, 476, 530, 476),
         text(["本文"], 590, 424, 24, 700, GREY),
         text(["< 50 ms"], 590, 512, 64, 700, KEY_RED)]
d.add("03_method.svg", shell([band("flow", 34, 96, 1212, 460, flow),
                              bar([[("把“先重建、再评估”变成", None), ("一次读数", KEY_RED), ("。", None)]])],
                             head_band=head("方案架构——一句话说清它怎么工作")))

# ---------------------------------------------------------------- 04 论文图 + 大数字
if os.path.exists(os.path.join(PROJECT, "images", FIG)):
    d.add("04_result.svg", shell([
        band("fig", 44, 94, 1192, 432, [img(50, 100, 1180, 420, FIG)]),
        band("stats", 88, 530, 1180, 116, [
            text(["91%"], 96, 596, 64, 700, KEY_RED), text(["指标说明"], 96, 634, 22, 700, "#555555"),
            text(["100%"], 492, 596, 64, 700, NAVY), text(["指标说明"], 492, 634, 22, 700, "#555555"),
            text(["7.1%"], 888, 596, 64, 700, NAVY), text(["指标说明"], 888, 634, 22, 700, "#555555")])],
        head_band=head("结果 I——把结论放进标题，别只写“结果”")))
else:
    print("skip figure page: images/%s not found" % FIG)

# ---------------------------------------------------------------- 05 结束
d.add("05_thanks.svg", shell([band("end", 120, 230, 1040, 340, [
    text(["我的汇报完了，请大家批评指正"], 640, 320, 64, 700, INK, anchor="middle"),
    text(["Q1  第一个讨论问题？"], 640, 440, 26, 700, "#444444", anchor="middle"),
    text(["Q2  第二个讨论问题？"], 640, 486, 26, 700, "#444444", anchor="middle"),
    text(["Q3  第三个讨论问题？"], 640, 532, 26, 700, "#444444", anchor="middle")])]))

d.write()
