# -*- coding: utf-8 -*-
"""svg_kit —— 组会 PPT（ppt-master SVG → PPTX）的绘图工具箱。

坐标约定：1280 x 720 px（= 13.333 x 7.5 in = 16:9）；1 px = 0.75 pt = 9525 EMU。
所有函数只产出 SVG 片段字符串，不依赖 ppt-master 内部实现。\n注意返回值：slab() / grid() / trace_cells() 返回【列表】，其余返回单个字符串；\n拼页面时列表项与字符串项不要直接相加，用 [...] + [...] 或 .extend()。

用法：
    from svg_kit import *
    d = Deck(r"D:\\...\\ppt-master-xxx")      # 含 svg_output/ 与 images/
    d.add("01_cover.svg", shell([...]))
    d.write()                                  # 写盘并清掉旧页
"""
import math
import os

FONT = "Arial, Microsoft YaHei"

# --- 配色（取自作者旧稿实测值） -------------------------------------------
TITLE_GREY = "#767171"
INK = "#111111"
KEY_BLUE = "#4472C4"
KEY_RED = "#E23B2E"
NAVY = "#2F5597"
DARKNAVY = "#1F3864"
CREAM = "#FFF7EE"
CREAM_LINE = "#E9DABB"
TINT = "#F3F6FB"       # 浅蓝块
TINT_BLUE = "#E7EEF9"  # 稍深蓝块（主干/特征图）
TINT_RED = "#FBE7E4"   # 对照/测试集块
GREY = "#8C8C8C"
SOFT = "#B9B9B9"

# --- 版面骨架（px） --------------------------------------------------------
HEAD_Y = 14          # 标题带顶
HEAD_BASE = 60       # 标题基线
HEAD_SIZE = 44       # 页面标题字号
BODY_TOP = 92        # 主图带上沿
BODY_BOTTOM = 620    # 主图带下沿（有结论条时）
BAR_Y = 648          # 结论条上沿
BAR_H = 64
BAR_TEXT = 30        # 结论条字号


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(lines, x, y, size=BODY_TOP, weight=700, color=INK, line_h=None, anchor=None):
    """多行文本。lines 的每一项可以是 str，或 [(片段, 颜色), ...] 的列表（行内强调）。"""
    a = 'x="%g" y="%g" font-size="%g" font-weight="%d" fill="%s"' % (x, y, size, weight, color)
    if anchor:
        a += ' text-anchor="%s"' % anchor
    spans = []
    for i, ln in enumerate(lines):
        if isinstance(ln, str):
            ln = [(ln, None)]
        inner = ""
        for t, c in ln:
            inner += ('<tspan fill="%s">%s</tspan>' % (c, esc(t))) if c and c != color else esc(t)
        dy = 0 if i == 0 else (line_h or round(size * 1.45, 1))
        spans.append('<tspan x="%g" dy="%g">%s</tspan>' % (x, dy, inner))
    return "<text %s>%s</text>" % (a, "".join(spans))


def band(gid, x, y, w, h, body):
    """顶层模块。同一页的顶层模块【不能重叠】（检查器硬门槛），浏览器不需要也不允许嵌套变换。"""
    return '<g id="%s" data-pptx-bounds="%g %g %g %g">\n%s\n</g>' % (gid, x, y, w, h, "\n".join(body))


def rect(x, y, w, h, fill, rx=None):
    """纯填充矩形；默认无描边（作者偏好：能不用框就不用框）。"""
    a = '<rect x="%g" y="%g" width="%g" height="%g"' % (x, y, w, h)
    if rx:
        a += ' rx="%g" ry="%g"' % (rx, rx)
    return a + ' fill="%s"/>' % fill


def ln(x1, y1, x2, y2, stroke=SOFT, sw=2.6, dash=None):
    a = '<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="%g"' % (x1, y1, x2, y2, stroke, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    return a + "/>"


def tri(x, y, size, fill=SOFT, up=False, down=False):
    """实心小三角箭头；默认指向右，尖在 (x, y)。"""
    if up:
        pts = (x - size * 0.62, y + size, x, y, x + size * 0.62, y + size)
    elif down:
        pts = (x - size * 0.62, y - size, x, y, x + size * 0.62, y - size)
    else:
        pts = (x - size, y - size * 0.62, x, y, x - size, y + size * 0.62)
    return '<polygon points="%g,%g %g,%g %g,%g" fill="%s"/>' % (pts + (fill,))


def arrow(x1, y1, x2, y2, stroke=SOFT, sw=2.6, head=9):
    return ln(x1, y1, x2, y2, stroke, sw) + tri(x2 + head * 0.8, y2, head, stroke)


def dot(cx, cy, r, fill):
    return '<circle cx="%g" cy="%g" r="%g" fill="%s"/>' % (cx, cy, r, fill)


def blend(hex_color, t):
    """与白色混合；t=0 原色，t=1 纯白。用于做"淡一档"的填充。"""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return "#%02X%02X%02X" % (int(r + (255 - r) * t), int(g + (255 - g) * t), int(b + (255 - b) * t))


def blob(cx, cy, rx, ry, angle=0.0, n=64, fill=TINT, stroke=NAVY, sw=2.0, dash=None):
    """倾斜椭圆（用多边形实现，避免 transform 属性）。画 FROG 轨迹示意用。"""
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        px, py = rx * math.cos(t), ry * math.sin(t)
        pts.append((cx + px * ca - py * sa, cy + px * sa + py * ca))
    a = '<polygon points="%s" fill="%s"' % (" ".join("%.1f,%.1f" % p for p in pts), fill)
    if stroke:
        a += ' stroke="%s" stroke-width="%g"' % (stroke, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    return a + "/>"


def gauss(cx, y0, amp, sigma, x_from, x_to, stroke, sw=3.2, dash=None, n=100):
    """高斯曲线折线；y0 是基线，amp 是峰高（向上）。"""
    pts = []
    for i in range(n + 1):
        x = x_from + (x_to - x_from) * i / n
        y = y0 - amp * math.exp(-((x - cx) ** 2) / (2 * sigma ** 2))
        pts.append("%.1f,%.1f" % (x, y))
    a = '<polyline points="%s" fill="none" stroke="%s" stroke-width="%g"' % (" ".join(pts), stroke, sw)
    if dash:
        a += ' stroke-dasharray="%s"' % dash
    return a + "/>"


def grid(x, y, n, cell, gap, colors):
    """n x n 方格网；colors 是二维颜色表。用于"卷积窗口扫图"、数据集格子。"""
    out = []
    for r in range(n):
        for c in range(n):
            out.append(rect(x + c * (cell + gap), y + r * (cell + gap), cell, cell, colors[r][c], 1.5))
    return out


def trace_cells(n, cx, cy, sigma_u, sigma_v, angle=38.0, dark="#12203A", light="#FFE9A8", floor=0.12):
    """生成 n x n 的"像 FROG 轨迹"的色块表：斜着的亮椭圆。"""
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    rows = []
    for r in range(n):
        row = []
        for c in range(n):
            u = (c - cx) * ca + (r - cy) * sa
            v = -(c - cx) * sa + (r - cy) * ca
            val = math.exp(-((u / sigma_u) ** 2 + (v / sigma_v) ** 2))
            row.append(blend(dark, 1 - val) if val > floor else dark)
        rows.append(row)
    return rows


def slab(x, y, w, h, tint, rx=7, depth=12):
    """三层错位的实心块：读作"一叠特征图"，不需要描边。"""
    return [rect(x + depth, y - depth, w, h, blend(tint, 0.62), rx),
            rect(x + depth / 2, y - depth / 2, w, h, blend(tint, 0.32), rx),
            rect(x, y, w, h, tint, rx)]


def img(x, y, w, h, name, opacity=None, path="../images"):
    """图片；name 为 images/ 下的文件名。透明度和柔化边缘见 finalize.py。"""
    a = '<image href="%s/%s" x="%g" y="%g" width="%g" height="%g" preserveAspectRatio="xMidYMid meet"' % (
        path, name, x, y, w, h)
    if opacity:
        a += ' opacity="%g"' % opacity
    return a + "/>"


def shell(bands, head_band=None, role="content"):
    head = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" lang="zh-CN" '
            'data-pptx-page-role="%s" font-family="%s">' % (role, FONT))
    out = [head,
           '<rect id="bg" x="0" y="0" width="1280" height="720" fill="#FFFFFF" data-pptx-role="background"/>']
    if head_band:
        out.append(head_band)
    out.extend(bands)
    out.append("</svg>")
    return "\n".join(out) + "\n"


def head(title):
    """页面标题：主题——说明。44px，深暖灰，左上 (20, 60)。"""
    return band("head", 26, HEAD_Y, 1228, 74, [text([title], 20, HEAD_BASE, HEAD_SIZE, 700, TITLE_GREY)])


def bar(parts, size=BAR_TEXT):
    """结论条：米黄圆角、无描边、文字居中，关键词上色。

    parts 可以是：一个字符串 / 一行 [(片段, 颜色), ...] / 多行 [[...], [...]]。
    """
    if isinstance(parts, str):
        lines = [parts]
    elif parts and isinstance(parts[0], tuple):
        lines = [parts]
    else:
        lines = parts
    return band("bar", 34, BAR_Y - 6, 1212, 78,
                [rect(44, BAR_Y, 1192, BAR_H, CREAM, 8),
                 text(lines, 640, BAR_Y + 43, size, 700, INK, anchor="middle")])


class Deck(object):
    """管理一个 ppt-master 项目的 svg_output/：按文件名排序即页序，写盘时清掉旧页。"""

    def __init__(self, project_dir):
        self.out = os.path.join(project_dir, "svg_output")
        self.pages = []

    def add(self, name, svg):
        self.pages.append((name, svg))

    def write(self):
        os.makedirs(self.out, exist_ok=True)
        keep = set()
        for name, svg in self.pages:
            with open(os.path.join(self.out, name), "w", encoding="utf-8", newline="\n") as f:
                f.write(svg)
            keep.add(name)
        for fn in os.listdir(self.out):
            if fn.endswith(".svg") and fn not in keep:
                os.remove(os.path.join(self.out, fn))
                print("removed stale", fn)
        print("wrote %d pages -> %s" % (len(keep), self.out))
