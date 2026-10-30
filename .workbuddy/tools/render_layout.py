"""把布局渲染成 PNG：路径、塔位、死角、起终点、统计。"""
import json, io, math, pathlib
from PIL import Image, ImageDraw, ImageFont

FONT = 'C:/Windows/Fonts/msyh.ttc'
MONO = 'C:/Windows/Fonts/consola.ttf'
C_PATH = (255, 245, 238)
C_TOWER = (63, 80, 101)
C_DEAD = (203, 208, 216)
C_S = (126, 211, 33)
C_E = (208, 2, 27)
C_GRID = (222, 222, 226)
C_TXT = (44, 44, 42)
C_SUB = (110, 110, 105)


def font(size, mono=False):
    try:
        return ImageFont.truetype(MONO if mono else FONT, size)
    except Exception:
        return ImageFont.load_default()


def render(item, out_dir):
    L = item['L']
    cells = item['cells']
    H, W = len(cells), len(cells[0])
    path = [tuple(p) for p in item['path']]
    Ps = set(path)
    towers = [tuple(t) for t in item['towers']]
    dead = [tuple(d) for d in item['dead']]
    obs = set(tuple(o) for o in item.get('obstacles', []))

    CS = 40
    PADL, PADT = 70, 96
    PADR, PADB = 40, 150
    iw, ih = W * CS, H * CS
    img = Image.new('RGB', (PADL + iw + PADR, PADT + ih + PADB), 'white')
    d = ImageDraw.Draw(img)

    d.text((PADL, 28), 'L%02d  最长路径布局' % L, font=font(24), fill=C_TXT)
    d.text((PADL, 62), '路径 %d 步 · 塔位 %d · 死角 %d · 覆盖 %.0f%%'
           % (item['n'], len(towers), len(dead), 100.0 * len(towers) / max(1, len(towers) + len(dead))),
           font=font(15), fill=C_SUB)

    for i in range(W + 1):
        d.line([(PADL + i * CS, PADT), (PADL + i * CS, PADT + ih)], fill=C_GRID, width=1)
    for j in range(H + 1):
        d.line([(PADL, PADT + j * CS), (PADL + iw, PADT + j * CS)], fill=C_GRID, width=1)

    for j in range(H):
        for i in range(W):
            ch = cells[j][i]
            x0, y0 = PADL + i * CS, PADT + j * CS
            c = (i, j)
            if c in obs:
                d.rectangle([x0 + 2, y0 + 2, x0 + CS - 2, y0 + CS - 2], fill=(232, 226, 214))
            elif ch in 'SE':
                col = C_S if ch == 'S' else C_E
                d.rectangle([x0 + 2, y0 + 2, x0 + CS - 2, y0 + CS - 2], fill=col)
                d.text((x0 + CS / 2, y0 + CS / 2), ch, font=font(20), fill='white', anchor='mm')
            elif c in Ps:
                d.rectangle([x0 + 2, y0 + 2, x0 + CS - 2, y0 + CS - 2], fill=C_PATH)
            elif c in dead:
                d.rectangle([x0 + 2, y0 + 2, x0 + CS - 2, y0 + CS - 2], fill=C_DEAD)
            else:
                d.rectangle([x0 + 1, y0 + 1, x0 + CS - 1, y0 + CS - 1], fill=C_TOWER)
                d.line([(x0 + 9, y0 + 9), (x0 + CS - 9, y0 + CS - 9)], fill=(90, 108, 128), width=2)
                d.line([(x0 + CS - 9, y0 + 9), (x0 + 9, y0 + CS - 9)], fill=(90, 108, 128), width=2)

    for (ox, oy) in obs:
        x0, y0 = PADL + ox * CS, PADT + oy * CS
        d.rectangle([x0 + 1, y0 + 1, x0 + CS - 1, y0 + CS - 1], outline=(60, 40, 20), width=3)
        d.line([(x0 + 7, y0 + 7), (x0 + CS - 7, y0 + CS - 7)], fill=(120, 78, 40), width=3)
        d.line([(x0 + CS - 7, y0 + 7), (x0 + 7, y0 + CS - 7)], fill=(120, 78, 40), width=3)

    # 路径顺序细线
    if len(path) > 1:
        pts = [(PADL + p[0] * CS + CS / 2, PADT + p[1] * CS + CS / 2) for p in path]
        d.line(pts, fill=(221, 73, 57), width=3, joint='curve')
        for k in range(6, len(pts) - 4, 7):
            ax, ay = pts[k]; bx, by = pts[k + 1]
            d.line([(ax, ay), (bx, by)], fill=(221, 73, 57), width=4)

    # 塔位编号
    for k, (x, y) in enumerate(towers[:99], 1):
        d.text((PADL + x * CS + CS / 2, PADT + y * CS + CS / 2), str(k),
               font=font(9, True), fill=(230, 235, 242), anchor='mm')

    # 坐标
    for i in range(W):
        d.text((PADL + i * CS + CS / 2, PADT - 18), str(i), font=font(12), fill=C_SUB, anchor='mm')
    for j in range(H):
        d.text((PADL - 18, PADT + j * CS + CS / 2), str(j), font=font(12), fill=C_SUB, anchor='mm')

    # 图例
    ly = PADT + ih + 34
    lg = [('路径', C_PATH), ('塔位', C_TOWER), ('死角', C_DEAD), ('障碍', (110, 72, 36)), ('起/终', C_S)]
    x = PADL
    for name, col in lg:
        d.rectangle([x, ly, x + 18, ly + 18], fill=col, outline=(200, 200, 205))
        d.text((x + 26, ly + 9), name, font=font(14), fill=C_TXT, anchor='lm')
        x += 92
    d.text((PADL, ly + 34), '障碍＝地图配置表中的不可走格（路径已避让）·  死角＝距路径 >2 格，塔打不到',
           font=font(13), fill=C_SUB)

    out = out_dir / ('L%02d_longest_path_towers.png' % L)
    img.save(out)
    return out


def main(data_path, out_dir):
    data = json.load(io.open(data_path, encoding='utf-8'))
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outs = []
    for it in data:
        outs.append(render(it, out_dir))
    return outs


if __name__ == '__main__':
    import sys
    outs = main(sys.argv[1], sys.argv[2])
    print('生成', len(outs), '张')
