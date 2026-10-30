"""带偏移的梳子构造：路径列与塔列交替，可枚举间距/偏移/方向。"""
import sys
sys.path.insert(0, 'E:/MyTowerGame/.workbuddy/tools')
from balance_campaign import runtime_path_for


def _tr(cells):
    return [''.join(r[i] for r in cells) for i in range(len(cells[0]))]


def comb_walls(cells, sp, off, trans=False):
    """在 (可能转置的) 地图上生成梳子墙体，返回 blocked 列表。"""
    c = _tr(cells) if trans else cells
    H, W = len(c), len(c[0])
    S = next(((x, y) for y in range(H) for x in range(W) if c[y][x] == 'S'), None)
    E = next(((x, y) for y in range(H) for x in range(W) if c[y][x] == 'E'), None)
    if not S or not E:
        return None
    cand, flip = [], 0
    for x in range(off, W, sp):
        if x == S[0] or x == E[0]:
            flip ^= 1
            continue
        rng = range(0, H - 1) if flip == 0 else range(1, H)
        for y in rng:
            if c[y][x] != '#':
                cand.append((x, y))
        flip ^= 1
    walls = []
    for cell in cand:
        if runtime_path_for(c, walls + [cell]):
            walls.append(cell)
    return walls


def build(cells, sp, off, trans=False):
    """返回 (路径, 塔位集合)，坐标已转回原图。"""
    c = _tr(cells) if trans else cells
    w = comb_walls(cells, sp, off, trans)
    if w is None:
        return None
    p = runtime_path_for(c, w)
    if not p:
        return None
    if trans:
        return [(q[1], q[0]) for q in p], {(q[1], q[0]) for q in w}
    return [tuple(q) for q in p], {tuple(q) for q in w}
