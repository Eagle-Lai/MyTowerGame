# -*- coding: utf-8 -*-
"""L02 W16-W25 地面血量加强：改按「整波地面 EHP」斜率外推 —— 2026-11-11 第二轮

上一轮（20261111 regression）只按「单只 hp」×1.0832/波外推，漏掉了数量本身的增长，
导致地面整波 EHP 只有 ×1.13/波，低于 W5..W15 实测的 ×1.1568/波（R²=0.920）。
本轮改成直接对齐 EHP 曲线：

    EHP_target(W) = EHP15_gnd * 1.1568^(W-15)         EHP15_gnd = 654,176
    k(W)          = EHP_target / 当前该波地面 EHP
    该波所有地面怪 hp *= k

空中一律不动（用户确认空中曲线已符合）。
范围：仅 L02 EnemyData 的 W16..W25 地面怪 hp。
"""
import sys
import shutil
import openpyxl

XLSX = r"D:/FreedomTower_1/Luban/Config/Datas/Levels/L02/EnemyData.xlsx"
BAK = XLSX + ".bak_20261111_before_l02_w16_25_ground_boost"
G_EHP = 1.1568
EHP15 = 654176.0
W_FROM, W_TO = 16, 25

ID_COL, HP_COL, NAME_COL = 2, 4, 5

AIR_IDS = {6000155, 6000165, 6000175, 6000185, 6000195, 6000205, 6000215, 6000225, 6000235, 6000245}

WAVES = {
    16: {6000150: "Chicken", 6000151: "Larva", 6000152: "Crawler", 6000153: "Scarab", 6000155: "Bat"},
    17: {6000160: "Chicken", 6000161: "Larva", 6000162: "Crawler", 6000163: "Scarab", 6000165: "Bat"},
    18: {6000170: "Chicken", 6000171: "Larva", 6000172: "Crawler", 6000173: "Scarab", 6000175: "Bat"},
    19: {6000180: "Chicken", 6000181: "Larva", 6000182: "Crawler", 6000183: "Scarab", 6000185: "Bat"},
    20: {6000190: "Chicken", 6000191: "Larva", 6000192: "Crawler", 6000193: "Scarab", 6000195: "Bat"},
    21: {6000200: "Chicken", 6000201: "Larva", 6000202: "Crawler", 6000203: "Scarab", 6000205: "Bat"},
    22: {6000210: "Chicken", 6000211: "Larva", 6000212: "Crawler", 6000213: "Scarab", 6000215: "Bat"},
    23: {6000220: "Chicken", 6000221: "Larva", 6000222: "Crawler", 6000223: "Scarab", 6000225: "Bat"},
    24: {6000230: "Chicken", 6000231: "Larva", 6000232: "Crawler", 6000233: "Scarab", 6000235: "Bat"},
    25: {6000240: "Chicken", 6000241: "Larva", 6000242: "Crawler", 6000243: "Scarab", 6000244: "Rat", 6000245: "Bat"},
}

# 各波地面怪数量（tbrounddata → tbenemylist 展开）
GCOUNT = {
    16: {6000150: 449, 6000151: 279, 6000152: 158, 6000153: 110},
    17: {6000160: 466, 6000161: 288, 6000162: 167, 6000163: 121},
    18: {6000170: 493, 6000171: 297, 6000172: 167, 6000173: 129},
    19: {6000180: 511, 6000181: 318, 6000182: 176, 6000183: 129},
    20: {6000190: 530, 6000191: 327, 6000192: 185, 6000193: 138},
    21: {6000200: 558, 6000201: 336, 6000202: 194, 6000203: 138},
    22: {6000210: 566, 6000211: 357, 6000212: 202, 6000213: 147},
    23: {6000220: 592, 6000221: 366, 6000222: 205, 6000223: 156},
    24: {6000230: 619, 6000231: 375, 6000232: 213, 6000233: 156},
    25: {6000240: 592, 6000241: 375, 6000242: 222, 6000243: 193, 6000244: 29},
}


def snap(ws):
    return {(r, c): ws.cell(r, c).value
            for r in range(1, ws.max_row + 1) for c in range(1, ws.max_column + 1)}


def main():
    wb = openpyxl.load_workbook(XLSX)
    ws = wb["Sheet"]
    before = snap(ws)

    id2row = {}
    for r in range(4, ws.max_row + 1):
        v = ws.cell(r, ID_COL).value
        if isinstance(v, int):
            id2row[v] = r

    plan, errors = [], []
    target = EHP15
    for w in range(W_FROM, W_TO + 1):
        target *= G_EHP
        cur = sum(GCOUNT[w][eid] * float(ws.cell(id2row[eid], HP_COL).value) for eid in GCOUNT[w])
        k = target / cur
        for eid, name in WAVES[w].items():
            if eid in AIR_IDS:
                continue
            row = id2row.get(eid)
            if row is None or ws.cell(row, NAME_COL).value != name:
                errors.append(f"W{w} id={eid} 定位失败")
                continue
            old = float(ws.cell(row, HP_COL).value)
            plan.append((row, eid, name, old, round(old * k, 6), w))
        print("W%-2d 目标地面EHP=%9.0f 当前=%9.0f  k=%.4f" % (w, target, cur, k))

    if errors:
        print("ABORT：", *errors, sep="\n  ")
        return 2

    shutil.copy2(XLSX, BAK)
    print("backup ->", BAK)

    for row, eid, name, old, new, w in plan:
        ws.cell(row, HP_COL).value = new
        print("W%-2d D%-3d %-8s(%d) %10.3f -> %10.3f" % (w, row, name, eid, old, new))
    wb.save(XLSX)

    ws2 = openpyxl.load_workbook(XLSX)["Sheet"]
    after = snap(ws2)

    def same(x, y):
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return abs(float(x) - float(y)) <= 1e-9
        return x == y

    changed = [k for k in before if not same(before[k], after.get(k))]
    allow = {(row, HP_COL) for row, *_ in plan}
    unexpected = [k for k in changed if k not in allow]
    print("实质变化格 = %d，白名单 = %d，越界 = %d" % (len(changed), len(allow), len(unexpected)))
    if unexpected:
        for k in unexpected[:20]:
            print("  UNEXPECTED", k, before[k], "->", after.get(k))
        return 3

    bad = 0
    for row, eid, name, old, new, w in plan:
        if abs(float(ws2.cell(row, HP_COL).value) - new) > 1e-9:
            bad += 1
            print("  VERIFY FAIL W%d %s" % (w, name))
    print("回读校验：%d/%d 通过" % (len(plan) - bad, len(plan)))
    print("DONE")
    return 0 if bad == 0 else 4


if __name__ == "__main__":
    sys.exit(main())
