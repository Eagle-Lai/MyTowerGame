# -*- coding: utf-8 -*-
"""
为 AdvancedHen 合成"正面(朝下)/背面(朝上)"两张方向图集。

输出（与主图集 AdvancedHen.png 完全同规格：960x800、PPU=100、SpriteMode=Multiple）：
    Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen_Down.png
    Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen_Up.png

切图 rect / pivot 与主图集逐字一致（见 ATLAS_Layout），
这样派生预制体只需替换图集 guid，动画（只驱动骨骼 Transform）可原样复用。
"""
import os
import glob
import numpy as np
from PIL import Image, ImageDraw

RAW = r"D:/FreedomTower_1/.workbuddy/cache/hen_dir/raw"
OUT_DIR = r"D:/FreedomTower_1/Assets/_UIAssets/Monsters/Birds/AdvancedHen"
PREVIEW = r"D:/FreedomTower_1/.workbuddy/cache/hen_dir/preview_atlas.png"

ATLAS_W, ATLAS_H = 960, 800

# (name, x, y_bottom_up, w, h) —— 与 AdvancedHen.png.meta 的 spriteSheet 完全一致
ATLAS_LAYOUT = [
    ("HeadNormal", 0,   480, 320, 320),
    ("HeadAngry",  320, 480, 320, 320),
    ("HeadDead",   640, 480, 320, 320),
    ("Body",       0,   0,   640, 480),
    ("Wing",       640, 320, 160, 160),
    ("Leg",        800, 320, 160, 160),
]


def load_cut(path):
    """读图 → 白底转透明 → 返回 RGBA ndarray。"""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    # 从四角泛洪，把与边框连通的白色背景抹成哨兵色
    sentinel = (1, 2, 3)
    px = im.load()
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        if sum(px[seed]) > 700:          # 只在确实是白的时候泛洪
            ImageDraw.floodfill(im, seed, sentinel, thresh=48)
    arr = np.array(im).astype(np.int16)
    is_bg = (arr[:, :, 0] == 1) & (arr[:, :, 1] == 2) & (arr[:, :, 2] == 3)
    # 残留的纯白像素也当背景（泛洪到不了、但明显是纸白的）
    lum = arr.sum(axis=2)
    is_bg |= lum > 738          # 246*3
    rgba = np.dstack([np.array(im).astype(np.uint8), np.full((h, w), 255, np.uint8)])
    rgba[is_bg, 3] = 0
    return rgba


def split_objects(rgba, min_ratio=0.004):
    """按 alpha 的列投影找出横向分离的若干物体，返回 [(x0,y0,x1,y1), ...]（按 x 排序）。"""
    a = rgba[:, :, 3]
    cols = (a > 16).sum(axis=0)
    total = a.shape[0] * a.shape[1]
    min_area = total * min_ratio

    runs, start = [], None
    for x in range(len(cols)):
        if cols[x] > 0 and start is None:
            start = x
        elif cols[x] == 0 and start is not None:
            runs.append((start, x))
            start = None
    if start is not None:
        runs.append((start, len(cols)))

    boxes = []
    for x0, x1 in runs:
        sub = a[:, x0:x1]
        rows = np.where((sub > 16).any(axis=1))[0]
        if rows.size == 0:
            continue
        area = int((sub > 16).sum())
        if area < min_area:
            continue                       # 过滤噪点（例如原图右上角那粒杂色点）
        boxes.append((x0, int(rows[0]), x1, int(rows[-1]) + 1))
    boxes.sort(key=lambda b: b[0])
    return boxes


def crop(rgba, box):
    x0, y0, x1, y1 = box
    return rgba[y0:y1, x0:x1]


def fit_paste(atlas, rgba_obj, box, pad_ratio=0.06):
    """把单件等比缩放到目标 box 内（留边距）后居中贴入 atlas。box 用左上原点像素坐标。"""
    bx0, by0, bx1, by1 = box
    bw, bh = bx1 - bx0, by1 - by0
    ow, oh = rgba_obj.shape[1], rgba_obj.shape[0]
    inner_w, inner_h = bw * (1 - pad_ratio), bh * (1 - pad_ratio)
    s = min(inner_w / ow, inner_h / oh)
    nw, nh = max(1, int(round(ow * s))), max(1, int(round(oh * s)))
    obj = Image.fromarray(rgba_obj, "RGBA").resize((nw, nh), Image.LANCZOS)
    ox = bx0 + (bw - nw) // 2
    oy = by0 + (bh - nh) // 2
    atlas.alpha_composite(obj, (ox, oy))


def rect_to_pixel_box(x, y_bottom, w, h):
    """Unity rect（y 自下往上）→ 图像像素 box（y 自上往下）。"""
    top = ATLAS_H - y_bottom - h
    return (x, top, x + w, top + h)


def build(name):
    return Image.new("RGBA", (ATLAS_W, ATLAS_H), (0, 0, 0, 0))


def main():
    by_stamp = {}
    for f in glob.glob(os.path.join(RAW, "*.png")):
        stamp = os.path.basename(f).split("_")[-1][:-4]
        by_stamp[stamp[-8:]] = f
    print("素材时间戳 → 文件：")
    for k in sorted(by_stamp):
        print("  ", k, os.path.basename(by_stamp[k]))

    A = load_cut(by_stamp["11-52-53"])   # 正面 3 个头部
    B = load_cut(by_stamp["11-52-52"])   # 正面 整鸡 / 翅膀 / 爪
    C = load_cut(by_stamp["11-53-35"])   # 正面 无头身体
    D = load_cut(by_stamp["11-53-37"])   # 背面 爪 / 翅膀 / 身体 / 翅膀 / 爪
    E = load_cut(by_stamp["11-54-16"])   # 背面 3 个头部

    aobjs = [crop(A, b) for b in split_objects(A)]
    bobj = [crop(B, b) for b in split_objects(B)]
    cobj = [crop(C, b) for b in split_objects(C)]
    dobj = [crop(D, b) for b in split_objects(D)]
    eobj = [crop(E, b) for b in split_objects(E)]
    print("切出件数：A=%d B=%d C=%d D=%d E=%d" % (len(aobjs), len(bobj), len(cobj), len(dobj), len(eobj)))

    plan = {
        "AdvancedHen_Down.png": {
            "HeadNormal": aobjs[0], "HeadAngry": aobjs[1], "HeadDead": aobjs[2],
            "Body": cobj[0], "Wing": bobj[1], "Leg": bobj[2],
        },
        "AdvancedHen_Up.png": {
            "HeadNormal": eobj[0], "HeadAngry": eobj[1], "HeadDead": eobj[2],
            "Body": dobj[2], "Wing": dobj[1], "Leg": dobj[0],
        },
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    previews = []
    for fname, parts in plan.items():
        atlas = build(fname)
        for sname, x, y, w, h in ATLAS_LAYOUT:
            fit_paste(atlas, parts[sname], rect_to_pixel_box(x, y, w, h))
        out = os.path.join(OUT_DIR, fname)
        atlas.save(out)
        print("写出：", out, Image.open(out).size)
        previews.append((fname, atlas))

    # 预览（棋盘底，便于看透明区）
    cell = 16
    pv = Image.new("RGBA", (ATLAS_W, ATLAS_H * 2 + 20), (60, 60, 60, 255))
    for i, (fname, atlas) in enumerate(previews):
        y0 = i * (ATLAS_H + 20)
        for yy in range(0, ATLAS_H, cell):
            for xx in range(0, ATLAS_W, cell):
                c = (110, 110, 110, 255) if ((xx // cell + yy // cell) % 2 == 0) else (150, 150, 150, 255)
                pv.paste(c, (xx, y0 + yy, min(xx + cell, ATLAS_W), min(y0 + yy + cell, y0 + ATLAS_H)))
        pv.alpha_composite(atlas, (0, y0))
    pv.save(PREVIEW)
    print("预览：", PREVIEW)


if __name__ == "__main__":
    main()
