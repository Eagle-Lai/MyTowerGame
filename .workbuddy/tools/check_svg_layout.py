# -*- coding: utf-8 -*-
"""
check_svg_layout.py — 效果图（SVG）几何布局校验器  v2

目标：像"按钮压住卡片/怪物展示"这类**真实排版事故**才报警，不报警装饰性叠放。

判定思路（三分类）：
  元素按语义分成三类：
    - NAV   导航/操作按钮：<polygon> 芯片、以及组内名为 返回/取消/确定/上一页/下一页 的矩形
    - BODY  内容实体：卡片内框（fill #252F40/#1E2939/#22303F 的 rect）、大面板 rect
    - NOTE  注解层：y >= NOTE_Y0 的 text，或 fill 为 #080B12 的整页底 —— 视为 overlay，不报警
  只检查 **NAV × BODY** 与 **NAV × NAV**：
    这两类是用户实际会点到的东西，压住就是事故。
  BODY × BODY 的"层叠"（面板上放卡片）是正常设计 → 只在**没有包含关系**时，且重叠率
    极高（>=0.55）时才报告，作为可疑提示。

同时报告"越界"：元素超出画布 0..1920 / 0..1080。
"""
import re
import sys
import os
import xml.etree.ElementTree as ET

SVG_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "Docs", "ui_mockups"))
NS = "{http://www.w3.org/2000/svg}"

NOTE_Y0 = 1000.0                 # 注解带起始 y
PAGE_FILLS = {"#080b12", "#0b0e14"}          # 整页底
BODY_CARD_FILLS = {"#252f40", "#1e2939", "#22303f", "#2a3444", "#131a26"}
NAV_HINT = ("返回", "取消", "确定", "关闭", "上一步", "下一步", "开始",
            "继续", "重试", "购买", "升级", "出售", "是", "否")


def parse_pts(s):
    nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", s)]
    return list(zip(nums[0::2], nums[1::2]))


def bbox_of(el, tag):
    try:
        if tag == "rect":
            x = float(el.get("x", 0)); y = float(el.get("y", 0))
            w = float(el.get("width", 0)); h = float(el.get("height", 0))
            if w <= 0 or h <= 0:
                return None
            return (x, y, x + w, y + h)
        if tag == "polygon":
            pts = parse_pts(el.get("points", ""))
            if not pts:
                return None
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            return (min(xs), min(ys), max(xs), max(ys))
        if tag == "text":
            x = float(el.get("x", 0)); y = float(el.get("y", 0))
            fs = float(el.get("font-size", 24))
            body = "".join(el.itertext())
            n = max(1, len(body.strip()))
            anchor = el.get("text-anchor", "start")
            cjk = sum(1 for c in body if ord(c) > 0x2E80)
            w = cjk * fs + (n - cjk) * fs * 0.62
            x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
            return (x0, y - fs * 0.82, x0 + w, y + fs * 0.28)
    except Exception:
        return None
    return None


def inter(a, b):
    x0 = max(a[0], b[0]); y0 = max(a[1], b[1])
    x1 = min(a[2], b[2]); y1 = min(a[3], b[3])
    return 0.0 if (x1 <= x0 or y1 <= y0) else (x1 - x0) * (y1 - y0)


def area(a):
    return max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])


def inside(o, i):
    return o[0] <= i[0] and o[1] <= i[1] and o[2] >= i[2] and o[3] >= i[3]


def collect(root):
    nav, body, notes, over = [], [], [], []

    def walk(node, dimmed):
        """dimmed=True 表示处于 '战场示意/压暗' 组内 → 其中的元素不是可点控件，跳过冲突检查。"""
        for el in node:
            tag = el.tag.replace(NS, "")
            if tag == "g":
                op = el.get("opacity")
                is_dim = dimmed or (op is not None and float(op) <= 0.5)
                walk(el, is_dim)
                continue
            if tag not in ("rect", "polygon", "text"):
                continue
            bb = bbox_of(el, tag)
            if bb is None:
                continue
            txt = "".join(el.itertext()).strip()
            fill = (el.get("fill") or "").lower()

            # 越界检查（压暗组内也检查，避免注释出屏）
            if bb[0] < -1 or bb[1] < -1 or bb[2] > 1921 or bb[3] > 1081:
                over.append((txt[:16] or tag, tuple(round(v) for v in bb)))

            if dimmed:
                notes.append(("dimmed:" + (txt[:12] or tag), bb))
                continue

            if tag == "text":
                if bb[1] >= NOTE_Y0:
                    notes.append((txt[:16], bb))
                elif any(k in txt for k in NAV_HINT) and len(txt) <= 8:
                    nav.append(("btn:" + txt, bb))
                continue

            if tag == "polygon":
                if area(bb) > 150000:
                    body.append(("polyPanel", bb))
                else:
                    nav.append(("poly", bb))
                continue

            # rect
            if fill in PAGE_FILLS or area(bb) >= 1900 * 1040:
                notes.append(("page", bb))
                continue
            if (bb[2] - bb[0]) >= 1400 and (bb[3] - bb[1]) >= 700:
                notes.append(("backdrop", bb))
                continue
            if fill in BODY_CARD_FILLS:
                body.append(("card", bb))
                continue
            if fill in ("none", "") and area(bb) > 250000:
                body.append(("panel", bb))

    walk(root, False)
    return nav, body, notes, over


def check(path):
    root = ET.parse(path).getroot()
    nav, body, notes, over = collect(root)
    probs = []

    def scan(A, B, kinds):
        for la, a in A:
            for lb, b in B:
                ov = inter(a, b)
                if ov <= 0:
                    continue
                s = min(area(a), area(b))
                if s <= 0:
                    continue
                r = ov / s
                if kinds == "body-body":
                    if inside(a, b) or inside(b, a):
                        continue
                    if r >= 0.55:
                        probs.append((r, la, a, lb, b, kinds))
                else:
                    if inside(a, b) or inside(b, a):
                        continue
                    if r >= 0.15:
                        probs.append((r, la, a, lb, b, kinds))

    scan(nav, body, "nav-body")
    scan(nav, nav, "nav-nav")
    scan(body, body, "body-body")
    probs.sort(key=lambda t: -t[0])
    return probs, over, (len(nav), len(body))


def main():
    args = sys.argv[1:]
    files = sorted(f for f in os.listdir(SVG_DIR) if f.endswith(".svg"))
    if args:
        files = [f for f in files if any(a in f for a in args)]
    bad = 0
    for f in files:
        p = os.path.join(SVG_DIR, f)
        try:
            probs, over, cnt = check(p)
        except Exception as e:
            print("[XML ERROR] %-34s %s" % (f, e)); bad += 1; continue
        tag = "OK" if (not probs and not over) else "问题"
        if not probs and not over:
            print("[  OK   ] %-30s nav=%d body=%d" % (f, cnt[0], cnt[1]))
            continue
        bad += 1
        print("[ %-4s ] %-30s nav=%d body=%d" % (tag, f, cnt[0], cnt[1]))
        for r, la, a, lb, b, k in probs[:10]:
            print("    %5.1f%%  [%s] %s %s ∪ %s %s"
                  % (r * 100, k, la, tuple(round(v) for v in a), lb, tuple(round(v) for v in b)))
        for name, bb in over[:6]:
            print("    越界   %s %s" % (name, bb))
    print("\n合计 %d 个文件，%d 个需处理" % (len(files), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
