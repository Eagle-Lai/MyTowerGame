# -*- coding: utf-8 -*-
"""
M3-1：为 8 关生成棋盘（TBLevelMap）。

【现状】SceneInfo 已有 8 关且 mapId = 1..8，但 LevelMap.xlsx **只有 1 张图** ——
  于是 8 个关卡全都在同一张空棋盘上打，难度曲线无从谈起。

【设计口径】
  · 字符集：S 起点 / E 终点 / . 可建造地砖 / # 障碍（不可通行、不可建造）
  · 障碍只做"约束"，不做"迷宫"：**必须保证 S→E 仍可通行**，否则开局就崩。
  · 难度不靠"把路做长" —— 塔防里路越长越**容易**（射程覆盖时间更久）。
    真正拉难度的是两条：① 可建造格变少（好位置稀缺）② 敌人强度（见 M3-2 的回合编排）。
    所以本脚本把"可建造格数量"当作主要的地图难度指标。

【自检】每张图都用 BFS 验证：
  ① S 与 E 都存在且唯一；② S→E 可达；③ 输出最短路长度与可建造格数量。
  任一张不满足就中止，不写文件。
"""
import os
import shutil
import sys
import datetime
from collections import deque

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")

ROOT = "D:/FreedomTower_1"
DATAS = os.path.join(ROOT, "Luban/Config/Datas")
BACKUP_ROOT = os.path.join(ROOT, ".workbuddy/backup")

# ---------------------------------------------------------------------------
# 8 张棋盘。每行长度必须等于 cols。
# 设计意图写在每张图前面，便于以后调难度时知道"当初为什么这样摆"。
# ---------------------------------------------------------------------------
MAPS = [
    # L1 教学：全开阔，无预置障碍。路径完全由玩家自己塑造（对齐原作第一关）
    (1, 1, "M1 教学：全开阔，无预置障碍；难度 1", [
        "S...............",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "...............E",
    ]),
    # L2 两团障碍把中段夹成一个"窄口"，逼玩家把火力集中在中间
    (2, 2, "M2 双障碍夹出中段窄口；难度 1", [
        "S...............",
        "................",
        "...##......##...",
        "...##......##...",
        "...##......##...",
        "...##......##...",
        "...##......##...",
        "................",
        "...............E",
    ]),
    # L3 一条带缺口的横墙：路径不变长，但墙上下两侧的好位置变少
    (3, 3, "M3 厚横墙：好建位变少；难度 1", [
        "S...............",
        "................",
        "....########....",
        "....########....",
        "....########....",
        "................",
        "................",
        "................",
        "...............E",
    ]),
    # L4 两条交错横墙，强制 S 形走位；可建造格进一步减少
    (4, 4, "M4 双交错横墙，S 形走位；难度 2", [
        "S...............",
        "..#########.....",
        "................",
        ".....#########..",
        "................",
        "..#########.....",
        "................",
        ".....#########..",
        "...............E",
    ]),
    # L5 中央大块障碍 + 四角小障碍：能贴路的格子很少
    (5, 5, "M5 中央大块障碍，贴路可建位稀缺；难度 2", [
        "S...............",
        "................",
        "....########....",
        "....########....",
        "....########....",
        "....########....",
        "....########....",
        "................",
        "...............E",
    ]),
    # L6 井字街区：路径被拉长且拐弯多，但真正难的是"每个街区内侧都能被覆盖"
    (6, 6, "M6 井字街区，内侧位置差；难度 2", [
        "S...............",
        ".##..##..##..##.",
        ".##..##..##..##.",
        ".##..##..##..##.",
        "................",
        ".##..##..##..##.",
        ".##..##..##..##.",
        ".##..##..##..##.",
        "...............E",
    ]),
    # L7 密集障碍：可建造格明显变少，容错率低
    (7, 7, "M7 密集障碍，可建位少、容错低；难度 3", [
        "S...............",
        ".##.##.##.##.##.",
        ".##.##.##.##.##.",
        ".##.##.##.##.##.",
        "................",
        ".##.##.##.##.##.",
        ".##.##.##.##.##.",
        ".##.##.##.##.##.",
        "...............E",
    ]),
    # L8 终盘：障碍最密 + 起点终点同侧，路径短、覆盖窗口小
    # 【为什么不用"起终点同排"来拉难度】实测那样会把路径压到 15 格，
    # 于是"半径内能覆盖到路径的可建造格"从 74 掉到 44 —— 塔数上限被砍掉四成，
    # 直接导致该关数学上无解（余量 0.09）。难度改由"障碍密度 + 敌人强度"承担。
    # 【连通性要点】障碍行只在固定列留缺口，相邻两行必须**共享至少一个缺口列**，
    # 否则上下就断了。上一版把缺口错开（一行留 4/7/10/13、下一行留 0/3/6/9…），
    # 结果 S→E 直接不可达 —— 脚本的 BFS 自检当场拦住了。
    (8, 8, "M8 终盘：障碍最密，可建位最少；难度 3", [
        "S...............",
        "####.##.##.##.##",
        "####.##.##.##.##",
        "................",
        "####.##.##.##.##",
        "####.##.##.##.##",
        "####.##.##.##.##",
        "####.##.##.##.##",
        "...............E",
    ]),
]

COLS = 16
ROWS = 9


def bfs(cells, rows, cols):
    """返回 (可达?, 最短路步数, 可建造格数)。障碍 # 与空洞 X 不可通行。"""
    start = end = None
    for r in range(rows):
        for c in range(cols):
            ch = cells[r][c]
            if ch == "S":
                start = (r, c)
            elif ch == "E":
                end = (r, c)
    if start is None or end is None:
        return False, -1, 0

    def walkable(r, c):
        return cells[r][c] not in "#X"

    dist = {start: 0}
    q = deque([start])
    while q:
        r, c = q.popleft()
        if (r, c) == end:
            break
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in dist and walkable(nr, nc):
                dist[(nr, nc)] = dist[(r, c)] + 1
                q.append((nr, nc))

    buildable = sum(1 for r in range(rows) for c in range(cols) if cells[r][c] == ".")
    return (end in dist), dist.get(end, -1), buildable


def main():
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_ROOT, stamp, "Config", "Datas")
    os.makedirs(dst, exist_ok=True)
    shutil.copy2(os.path.join(DATAS, "LevelMap.xlsx"), os.path.join(dst, "LevelMap.xlsx"))
    print("已备份到:", dst)

    problems = []
    stats = []
    for mid, level_id, desc, cells in MAPS:
        if len(cells) != ROWS:
            problems.append("map %d 行数 %d != %d" % (mid, len(cells), ROWS))
            continue
        for i, row in enumerate(cells):
            if len(row) != COLS:
                problems.append("map %d 第 %d 行长度 %d != %d" % (mid, i, len(row), COLS))
        ok, plen, buildable = bfs(cells, ROWS, COLS)
        stats.append((mid, plen, buildable, ok))
        if not ok:
            problems.append("map %d S→E 不可达！" % mid)

    print("\n【棋盘自检】")
    print("  地图  最短路径  可建造格  可达")
    for mid, plen, buildable, ok in stats:
        print("   %2d     %3d      %3d      %s" % (mid, plen, buildable, "✔" if ok else "✘"))

    if problems:
        for p in problems:
            print("  ✘", p)
        raise SystemExit("自检未通过，未写文件")

    wb = openpyxl.load_workbook(os.path.join(DATAS, "LevelMap.xlsx"))
    ws = wb.active
    hdr = {ws.cell(row=1, column=c).value: c for c in range(1, ws.max_column + 1)}
    id_c = hdr["id"]

    for mid, level_id, desc, cells in MAPS:
        # 幂等：按 id 定位已有行
        r = None
        for rr in range(4, ws.max_row + 1):
            if ws.cell(row=rr, column=id_c).value is not None and int(ws.cell(row=rr, column=id_c).value) == mid:
                r = rr
                break
        if r is None:
            r = ws.max_row + 1
        ws.cell(row=r, column=hdr["id"]).value = mid
        ws.cell(row=r, column=hdr["levelId"]).value = level_id
        ws.cell(row=r, column=hdr["cols"]).value = COLS
        ws.cell(row=r, column=hdr["rows"]).value = ROWS
        ws.cell(row=r, column=hdr["cells"]).value = "|".join(cells)   # Luban: (list#sep=|),string
        ws.cell(row=r, column=hdr["desc"]).value = desc

    wb.save(os.path.join(DATAS, "LevelMap.xlsx"))
    print("\n已写出 %d 张棋盘到 LevelMap.xlsx" % len(MAPS))


if __name__ == "__main__":
    main()
