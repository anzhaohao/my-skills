# -*- coding: utf-8 -*-
"""交付后处理：加演讲备注 → 拆分组 → 加柔化边缘 → 自检。

用法：
    python finalize.py --pptx <导出.pptx> --notes notes.json --out <交付.pptx>
    python finalize.py --pptx <导出.pptx> --out <交付.pptx> --soft-edge "1:285750,2:850900"

notes.json 形如 {"1": "第一页讲稿", "2": "第二页讲稿", ...}（键是页码，从 1 起）。

为什么需要"拆分组"：svg 里的 <g data-pptx-bounds> 会被写成 PowerPoint 组合，
文本框要双击进组才能改。这里把恒等变换的组合原地拆平，每个文本框回到顶层。

为什么柔化边缘放在 PPTX 里做：SVG 滤镜 ppt-master 不落成原生效果；
直接往图片的 spPr 里写 <a:softEdge rad="..."/>，PowerPoint 里就是可调的"柔化边缘"。
"""
import argparse
import json
import re
import sys
import zipfile
from lxml import etree
from pptx import Presentation

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"p": P, "a": A}


def add_notes(path, notes):
    prs = Presentation(path)
    n = len(prs.slides)
    missing = [k for k in notes if not (1 <= int(k) <= n)]
    if missing:
        sys.exit("notes 里的页码超出范围：%s（共 %d 页）" % (missing, n))
    for k, v in notes.items():
        prs.slides[int(k) - 1].notes_slide.notes_text_frame.text = v
    prs.save(path)
    empty = [i + 1 for i, s in enumerate(prs.slides) if not s.notes_slide.notes_text_frame.text.strip()]
    print("notes: %d/%d（缺：%s）" % (n - len(empty), n, empty or "无"))


def flatten_groups(src, dst):
    zin = zipfile.ZipFile(src, "r")
    items = zin.infolist()
    data, flat, skipped = {}, 0, 0
    for it in items:
        raw = zin.read(it.filename)
        if re.match(r"ppt/slides/slide\d+\.xml$", it.filename):
            root = etree.fromstring(raw)
            tree = root.find(".//p:cSld/p:spTree", NS)
            changed = False
            for grp in list(tree.findall("p:grpSp", NS)):
                xfrm = grp.find("p:grpSpPr/a:xfrm", NS)
                ok = False
                if xfrm is not None:
                    off, choff = xfrm.find("a:off", NS), xfrm.find("a:chOff", NS)
                    ext, chext = xfrm.find("a:ext", NS), xfrm.find("a:chExt", NS)
                    if None not in (off, choff, ext, chext):
                        ok = (off.get("x") == choff.get("x") and off.get("y") == choff.get("y")
                              and ext.get("cx") == chext.get("cx") and ext.get("cy") == chext.get("cy"))
                if not ok:            # 有真实变换的组合不能硬拆
                    skipped += 1
                    continue
                idx = list(tree).index(grp)
                kids = [c for c in grp if c.tag.split("}")[-1] in ("sp", "pic", "grpSp", "graphicFrame", "cxnSp")]
                for c in kids:
                    tree.insert(idx, c)
                    idx += 1
                tree.remove(grp)
                flat += 1
                changed = True
            if changed:
                raw = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        data[it.filename] = raw
    zin.close()
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in items:
            zout.writestr(it, data[it.filename])
    print("groups flattened: %d（有变换跳过：%d）" % (flat, skipped))


def soft_edges(path, spec):
    """spec: {slide_no: rad_emu}"""
    zin = zipfile.ZipFile(path, "r")
    items = zin.infolist()
    data, n = {}, 0
    for it in items:
        raw = zin.read(it.filename)
        m = re.match(r"ppt/slides/slide(\d+)\.xml$", it.filename)
        if m and int(m.group(1)) in spec:
            root = etree.fromstring(raw)
            for pic in root.iter("{%s}pic" % P):
                spPr = pic.find("{%s}spPr" % P)
                if spPr is None:
                    continue
                old = spPr.find("{%s}effectLst" % A)
                if old is not None:
                    spPr.remove(old)
                eff = etree.SubElement(spPr, "{%s}effectLst" % A)
                etree.SubElement(eff, "{%s}softEdge" % A).set("rad", str(spec[int(m.group(1))]))
                n += 1
            raw = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        data[it.filename] = raw
    zin.close()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in items:
            zout.writestr(it, data[it.filename])
    print("soft edges: %d picture(s)" % n)


def verify(path):
    prs = Presentation(path)
    pics = sum(1 for s in prs.slides for sh in s.shapes if sh.shape_type == 13)
    notes = sum(1 for s in prs.slides if s.notes_slide.notes_text_frame.text.strip())
    print("verify: %d pages, %.3f x %.3f in, %d pictures, %d notes" % (
        len(prs.slides), prs.slide_width / 914400, prs.slide_height / 914400, pics, notes))
    if abs(prs.slide_width / prs.slide_height - 16 / 9.0) > 0.01:
        print("!! 不是 16:9")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--notes")
    ap.add_argument("--soft-edge", default="")
    ap.add_argument("--keep-groups", action="store_true")
    a = ap.parse_args()

    import shutil
    shutil.copy2(a.pptx, a.out)
    if a.notes:
        add_notes(a.out, json.load(open(a.notes, encoding="utf-8")))
    if a.soft_edge:
        spec = {}
        for part in a.soft_edge.split(","):
            k, v = part.split(":")
            spec[int(k)] = int(v)
        soft_edges(a.out, spec)
    if not a.keep_groups:
        tmp = a.out + ".tmp"
        flatten_groups(a.out, tmp)
        os.replace(tmp, a.out)
    verify(a.out)


if __name__ == "__main__":
    import os
    main()
