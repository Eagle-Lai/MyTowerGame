"""完全复刻《怪物行进路径》版式：米色路径 + 深蓝障碍 + 红色箭头。"""
import json, io, math, pathlib
from PIL import Image, ImageDraw, ImageFont

F = 'C:/Windows/Fonts/msyh.ttc'
FM = 'C:/Windows/Fonts/consola.ttf'
BG = (246, 248, 251)
PATH = (255, 245, 238)
WALL = (63, 80, 101)
XCOL = (96, 116, 138)
RED = (221, 73, 57)
GREEN = (76, 175, 80)
TXT = (44, 44, 42)
SUB = (110, 116, 124)
GRID = (232, 237, 244)
WHITE = (255, 255, 255)


def f(sz, mono=False):
    try:
        return ImageFont.truetype(FM if mono else F, sz)
    except Exception:
        return ImageFont.load_default()


def arrow(d, p, q, size=13, color=RED):
    ang = math.atan2(q[1] - p[1], q[0] - p[0])
    for s in (2.6, -2.6):
        d.line([q, (q[0] - size * math.cos(ang + s / 1.0), q[1] - size * math.sin(ang + s / 1.0))],
               fill=color, width=3)


def render(item, out_dir, idx, total):
    L = item['L']
    cells = item['cells']
    H, W = len(cells), len(cells[0])
    P = [tuple(p) for p in item['path']]
    Ps = set(P)

    CS = 86 if W <= 14 else (80 if W <= 16 else 74)
    GX, GY = 200, 168
    iw, ih = W * CS, H * CS
    Wd, Ht = iw + 400, ih + 330
    img = Image.new('RGB', (Wd, Ht), BG)
    d = ImageDraw.Draw(img)

    d.text((56, 44), '第 %02d 关 · 怪物行进路径' % L, font=f(30), fill=TXT)
    d.text((58, 92), '%d 列 × %d 行   /   按箭头方向从 S 到 E' % (W, H), font=f(16), fill=SUB)

    tag = '%d 列 × %d 行' % (W, H)
    tw = d.textlength(tag, font=f(16))
    d.rounded_rectangle([Wd - tw - 96, 46, Wd - 56, 88], radius=8, fill=(232, 237, 244))
    d.text((Wd - tw - 76, 58), tag, font=f(16), fill=SUB)
    t2 = '路径布局 %02d / %d' % (idx, total)
    tw2 = d.textlength(t2, font=f(15))
    d.text((Wd - tw2 - 56, 108), t2, font=f(15), fill=SUB)

    for i in range(W + 1):
        d.line([(GX + i * CS, GY), (GX + i * CS, GY + ih)], fill=GRID, width=1)
    for j in range(H + 1):
        d.line([(GX, GY + j * CS), (GX + iw, GY + j * CS)], fill=GRID, width=1)

    for j in range(H):
        for i in range(W):
            ch = cells[j][i]
            x0, y0 = GX + i * CS, GY + j * CS
            if ch in 'SE':
                continue
            if (i, j) in Ps:
                d.rectangle([x0 + 1, y0 + 1, x0 + CS - 2, y0 + CS - 2], fill=PATH)
            else:
                d.rectangle([x0 + 1, y0 + 1, x0 + CS - 2, y0 + CS - 2], fill=WALL)
                k = CS * 0.26
                d.line([(x0 + k, y0 + k), (x0 + CS - k, y0 + CS - k)], fill=XCOL, width=3)
                d.line([(x0 + CS - k, y0 + k), (x0 + k, y0 + CS - k)], fill=XCOL, width=3)

    if len(P) > 1:
        pts = [(GX + p[0] * CS + CS / 2, GY + p[1] * CS + CS / 2) for p in P]
        d.line(pts, fill=RED, width=4, joint='curve')
        run = 1
        for k in range(1, len(pts) - 1):
            v1 = (pts[k][0] - pts[k-1][0], pts[k][1] - pts[k-1][1])
            v2 = (pts[k+1][0] - pts[k][0], pts[k+1][1] - pts[k][1])
            if v1 != v2:
                if run >= 2:
                    mp = ((pts[k][0] + pts[k+1][0]) / 2, (pts[k][1] + pts[k+1][1]) / 2)
                    arrow(d, pts[k], mp)
                run = 1
            else:
                run += 1
        if run >= 2:
            mp = ((pts[-2][0] + pts[-1][0]) / 2, (pts[-2][1] + pts[-1][1]) / 2)
            arrow(d, pts[-2], mp)

    S = next(((x, y) for y in range(H) for x in range(W) if cells[y][x] == 'S'), None)
    E = next(((x, y) for y in range(H) for x in range(W) if cells[y][x] == 'E'), None)
    if S:
        x0, y0 = GX + S[0] * CS, GY + S[1] * CS
        d.rounded_rectangle([x0 + 5, y0 + 5, x0 + CS - 6, y0 + CS - 6], radius=10, fill=GREEN)
        d.text((x0 + CS / 2, y0 + CS / 2 - 6), 'S', font=f(24), fill=WHITE, anchor='mm')
        d.text((x0 + CS / 2, y0 + CS / 2 + 17), '起点', font=f(10), fill=WHITE, anchor='mm')
    if E:
        x0, y0 = GX + E[0] * CS, GY + E[1] * CS
        d.rounded_rectangle([x0 + 5, y0 + 5, x0 + CS - 6, y0 + CS - 6], radius=10, fill=(211, 47, 47))
        d.text((x0 + CS / 2, y0 + CS / 2 - 6), 'E', font=f(24), fill=WHITE, anchor='mm')
        d.text((x0 + CS / 2, y0 + CS / 2 + 17), '终点', font=f(10), fill=WHITE, anchor='mm')

    for i in range(W):
        d.text((GX + i * CS + CS / 2, GY - 22), str(i + 1), font=f(15), fill=SUB, anchor='mm')
    for j in range(H):
        d.text((GX - 22, GY + j * CS + CS / 2), str(j + 1), font=f(15), fill=SUB, anchor='mm')

    ly = GY + ih + 56
    lx = GX
    items = [('S', GREEN, '起点'), ('E', (211, 47, 47), '终点'), (None, RED, '行进方向'),
             (None, WALL, '障碍区'), ('#', WALL, '原图 # 障碍')]
    for key, col, label in items:
        if key in ('S', 'E'):
            d.rounded_rectangle([lx, ly - 15, lx + 30, ly + 15], radius=6, fill=col)
            d.text((lx + 15, ly), key, font=f(17), fill=WHITE, anchor='mm')
        elif key == '#':
            d.rectangle([lx, ly - 15, lx + 30, ly + 15], fill=col)
            d.text((lx + 15, ly), '#', font=f(16), fill=WHITE, anchor='mm')
        elif label == '行进方向':
            d.line([(lx, ly), (lx + 26, ly)], fill=col, width=4)
            arrow(d, (lx + 10, ly), (lx + 28, ly))
        else:
            d.rectangle([lx, ly - 15, lx + 30, ly + 15], fill=col)
        d.text((lx + 40, ly), label, font=f(15), fill=TXT, anchor='lm')
        lx += 40 + d.textlength(label, font=f(15)) + 46

    d.text((Wd - 300, ly), '路线外格子为障碍区', font=f(14), fill=SUB)

    out = pathlib.Path(out_dir) / ('L%02d_怪物行进路径.png' % L)
    img.save(out)
    return out


def main(data_path, out_dir):
    data = json.load(io.open(data_path, encoding='utf-8'))
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for it in data:
        render(it, out_dir, it['L'], len(data))
    return len(data)


if __name__ == '__main__':
    import sys
    print('生成', main(sys.argv[1], sys.argv[2]), '张')
