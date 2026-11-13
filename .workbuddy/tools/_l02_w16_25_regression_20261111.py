# -*- coding: utf-8 -*-
"""L02 W16-W25 血量按 W5-W15 规律平滑外推 —— 2026-11-11

规律（对数线性拟合 W5..W15 的「单只加权平均 hp」）：
  · 地面 g = 1.0832 / 波（R²=0.814）
  · 空中 g = 1.1311 / 波（R²=0.923）
数量保持现状（本就线性延续 +46/波 地面、+7.6/波 空中），只缩放 hp。

做法：每波取目标「加权平均 hp」→ k = 目标 / 当前 → 该波所有同阵营怪 hp × k，
      从而保持波内怪种比例不变。
范围：仅 L02 EnemyData 中 W16..W25（rid 2016..2020 / 2401..2405）的 hp 单元格。
      W1..W15 一律不动；quantity / speed / armor / reward / isFlying 全不动。
"""
import sys
import shutil
import collections
import openpyxl

XLSX = r"D:/FreedomTower_1/Luban/Config/Datas/Levels/L02/EnemyData.xlsx"
BAK = XLSX + ".bak_20261111_before_l02_w16_25_regression"
G = 1.0832     # 地面每波
A = 1.1311     # 空中每波
W_FROM, W_TO = 16, 25

ID_COL, HP_COL, NAME_COL = 2, 4, 5   # B / D / E

# (wave, {eid: (name, isFlying)}) —— 由配置展开得到，保留顺序稳定
WAVES = {
    16: {6000150: ("Chicken", 0), 6000151: ("Larva", 0), 6000152: ("Crawler", 0), 6000153: ("Scarab", 0), 6000155: ("Bat", 1)},
    17: {6000160: ("Chicken", 0), 6000161: ("Larva", 0), 6000162: ("Crawler", 0), 6000163: ("Scarab", 0), 6000165: ("Bat", 1)},
    18: {6000170: ("Chicken", 0), 6000171: ("Larva", 0), 6000172: ("Crawler", 0), 6000173: ("Scarab", 0), 6000175: ("Bat", 1)},
    19: {6000180: ("Chicken", 0), 6000181: ("Larva", 0), 6000182: ("Crawler", 0), 6000183: ("Scarab", 0), 6000185: ("Bat", 1)},
    20: {6000190: ("Chicken", 0), 6000191: ("Larva", 0), 6000192: ("Crawler", 0), 6000193: ("Scarab", 0), 6000195: ("Bat", 1)},
    21: {6000200: ("Chicken", 0), 6000201: ("Larva", 0), 6000202: ("Crawler", 0), 6000203: ("Scarab", 0), 6000205: ("Bat", 1)},
    22: {6000210: ("Chicken", 0), 6000211: ("Larva", 0), 6000212: ("Crawler", 0), 6000213: ("Scarab", 0), 6000215: ("Bat", 1)},
    23: {6000220: ("Chicken", 0), 6000221: ("Larva", 0), 6000222: ("Crawler", 0), 6000223: ("Scarab", 0), 6000225: ("Bat", 1)},
    24: {6000230: ("Chicken", 0), 6000231: ("Larva", 0), 6000232: ("Crawler", 0), 6000233: ("Scarab", 0), 6000235: ("Bat", 1)},
    25: {6000240: ("Chicken", 0), 6000241: ("Larva", 0), 6000242: ("Crawler", 0), 6000243: ("Scarab", 0),
         6000244: ("Rat", 0), 6000245: ("Bat", 1)},
}

# 每波各阵营数量（来自 tbrounddata/tbenemylist 展开，仅用于算加权平均）
COUNTS = {
    16: (996, 101), 17: (1042, 109), 18: (1086, 117), 19: (1134, 125), 20: (1180, 133),
    21: (1226, 131), 22: (1272, 138), 23: (1319, 146), 24: (1363, 154), 25: (1411, 162),
}
# W15 实测加权平均单只 hp（654176/949、65801/94）
AVG15_GND, AVG15_AIR = 654176.0 / 949.0, 65800.65 / 94.0

# 每波地面的「数量加权」分布：按各自数量占比，需与 COUNTS 一致
SPLIT = {
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


def snapshot(ws):
    return {(r, c): ws.cell(r, c).value
            for r in range(1, ws.max_row + 1) for c in range(1, ws.max_column + 1)}


def main():
    wb = openpyxl.load_workbook(XLSX)
    ws = wb["Sheet"]
    before = snapshot(ws)

    id2row = {}
    for r in range(4, ws.max_row + 1):
        v = ws.cell(r, ID_COL).value
        if isinstance(v, int):
            id2row[v] = r

    # 1) 定位并核对
    plan = []   # (row, eid, name, old, new, wave, air)
    errors = []
    tg, ta = AVG15_GND, AVG15_AIR
    for w in range(W_FROM, W_TO + 1):
        tg *= G
        ta *= A
        gc, ac = COUNTS[w]
        # 当前加权平均
        cur_g = sum(SPLIT[w][eid] * float(ws.cell(id2row[eid], HP_COL).value) for eid in SPLIT[w]) / gc
        air_ids = [e for e, (n, f) in WAVES[w].items() if f]
        cur_a = float(ws.cell(id2row[air_ids[0]], HP_COL).value)
        kg, ka = tg / cur_g, ta / cur_a
        for eid, (name, fly) in WAVES[w].items():
            row = id2row.get(eid)
            if row is None:
                errors.append(f"W{w} id={eid} 在表中找不到")
                continue
            got_name = ws.cell(row, NAME_COL).value
            if got_name != name:
                errors.append(f"W{w} id={eid} 名字不符：期望 {name} 实际 {got_name}")
                continue
            old = float(ws.cell(row, HP_COL).value)
            k = ka if fly else kg
            plan.append((row, eid, name, old, round(old * k, 6), w, fly))
        print("W%-2d 目标 地面avg=%.1f 空中avg=%.1f | k=%.4f / %.4f" % (w, tg, ta, kg, ka))

    if errors:
        print("ABORT：")
        for e in errors:
            print("  " + e)
        return 2

    shutil.copy2(XLSX, BAK)
    print("backup ->", BAK)

    # 2) 写入
    for row, eid, name, old, new, w, fly in plan:
        ws.cell(row, HP_COL).value = new
        print("W%-2d D%-3d %-8s(%d) %10.3f -> %10.3f %s" % (w, row, name, eid, old, new, "AIR" if fly else ""))
    wb.save(XLSX)

    # 3) 回读 + 全表比对（容差 1e-9）
    ws2 = openpyxl.load_workbook(XLSX)["Sheet"]
    after = snapshot(ws2)

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
    for row, eid, name, old, new, w, fly in plan:
        got = float(ws2.cell(row, HP_COL).value)
        if abs(got - new) > 1e-9:
            bad += 1
            print("  VERIFY FAIL W%d %s 期望 %.6f 实际 %.6f" % (w, name, new, got))
    print("回读校验：%d/%d 通过" % (len(plan) - bad, len(plan)))
    print("DONE")
    return 0 if bad == 0 else 4


if __name__ == "__main__":
    sys.exit(main())
