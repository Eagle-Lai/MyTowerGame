# -*- coding: utf-8 -*-
"""L02 W16-W25 按 W5-W15 的 Λ（每金币承受 EHP）规律续写 —— 2026-11-11 第五轮

依据：Docs/L02_Rebalance_20261108/L02_重设计规格.md
      W5-W15 的难度是按 Λ 标尺设定的（Λ = 波次 EHP / (塔阵产能 × 波内时长)），
      折算到经济口径就是「每 1 金币累计经济可承受多少地面 EHP」：
        73.4, 107.9, 110.0, 126.3, 144.0, 179.1, 176.6, 164.7, 182.1, 201.0, 246.6
      这是一条线性递增的难度曲线（越往后越吃操作），不是固定倍率。

本轮：用 W5/W15 两点定标这条直线，逐波 ratio(W) = a + b·W，
      target_gndEHP(W) = ratio(W) × cumE(W)，cumE 含击杀金币（实际配置）。

范围：仅 L02 EnemyData W16..W25 地面怪 hp；空中不动；数量/速度/护甲/金币全不动。
"""
import sys
import json
import shutil
import collections
import openpyxl

XLSX = r"D:/FreedomTower_1/Luban/Config/Datas/Levels/L02/EnemyData.xlsx"
CFG = r"D:/FreedomTower_1/Assets/ConfigJson"
BAK = XLSX + ".bak_20261111_before_l02_w16_25_lambda_curve"
ID_COL, HP_COL, NAME_COL = 2, 4, 5

# 文档记载的 W5-W15 Λ 经济比（旧口径 EHP / 旧累计经济），用于定标趋势线
LAM5, LAM15 = 85460.0 / 1164.0, 878317.0 / 3562.0

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


def load(name):
    d = json.load(open(CFG + "/" + name + ".json", encoding="utf-8"))
    return d if isinstance(d, list) else (d.get("data") or list(d.values())[0])


def build():
    sc = {s["id"]: s for s in load("tbsceneinfo")}
    rd = {x["id"]: x for x in load("tbrounddata")}
    el = {x["id"]: x for x in load("tbenemylist")}
    ed = {x["id"]: x for x in load("tbenemydata")}
    l2 = sc[2]
    cum = float(l2["initialGold"])
    cumE, gcount = {}, {}
    for w, rid in enumerate(l2["RoundList"], 1):
        r = rd[rid]
        ids = []
        for lid in r["EnemyIndexs"]:
            ids += el[lid]["EnemyIndexs"]
        c = collections.Counter(ids)
        kill = sum(ed[eid]["reward"] * n for eid, n in c.items())
        cum += r["rewardGold"] + kill
        cumE[w] = cum
        gcount[w] = {eid: n for eid, n in c.items() if not ed[eid]["isFlying"]}
    return cumE, gcount


def snap(ws):
    return {(r, c): ws.cell(r, c).value
            for r in range(1, ws.max_row + 1) for c in range(1, ws.max_column + 1)}


def main():
    cumE, gcount = build()
    slope = (LAM15 - LAM5) / 10.0
    icpt = LAM5 - slope * 5.0
    print("Λ 经济比趋势线: ratio(W) = %.2f + %.2f x W   (W5=%.1f, W15=%.1f)" % (icpt, slope, LAM5, LAM15))

    wb = openpyxl.load_workbook(XLSX)
    ws = wb["Sheet"]
    before = snap(ws)
    id2row = {}
    for r in range(4, ws.max_row + 1):
        v = ws.cell(r, ID_COL).value
        if isinstance(v, int):
            id2row[v] = r

    plan, errors = [], []
    for w in range(16, 26):
        ratio = icpt + slope * w
        target = ratio * cumE[w]
        cur = sum(gcount[w][eid] * float(ws.cell(id2row[eid], HP_COL).value) for eid in gcount[w])
        k = target / cur
        for eid, name in WAVES[w].items():
            if eid in AIR_IDS:
                continue
            row = id2row.get(eid)
            if row is None or ws.cell(row, NAME_COL).value != name:
                errors.append("W%d id=%d 定位失败" % (w, eid))
                continue
            old = float(ws.cell(row, HP_COL).value)
            plan.append((row, eid, name, old, round(old * k, 6), w))
        print("W%-2d ratio=%6.1f cumE=%8.1f 目标EHP=%9.0f 当前=%9.0f k=%.4f" % (w, ratio, cumE[w], target, cur, k))

    if errors:
        print("ABORT：", *errors, sep="\n  ")
        return 2

    shutil.copy2(XLSX, BAK)
    print("backup ->", BAK)
    for row, eid, name, old, new, w in plan:
        ws.cell(row, HP_COL).value = new
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
    print("回读校验：%d/%d 通过" % (len(plan) - bad, len(plan)))
    for w in range(16, 26):
        rows = [p for p in plan if p[5] == w]
        print("W%-2d %s" % (w, " | ".join("%s %.1f->%.1f" % (n, o, nv) for _, _, n, o, nv, _ in rows)))
    print("DONE")
    return 0 if bad == 0 else 4


if __name__ == "__main__":
    sys.exit(main())
