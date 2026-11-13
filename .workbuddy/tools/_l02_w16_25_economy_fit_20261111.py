# -*- coding: utf-8 -*-
"""L02 W16-W25 按「经济折算」重算地面血量 —— 2026-11-11 第四轮

问题：前三轮用固定倍率（1.083 / 1.157 / 1.20 / 1.25）外推，脱离玩家实际购买力。
W5-W15 的实测关系是「地面 EHP ≈ 线性于累计金币」：

    ratio = gndEHP / cumE  = 109.0,148.4,143.7,161.5,184.2,172.6,148.4,142.4,153.5,169.0,156.4

用 W5/W15 两点定标（等价于「每新增 1 金币可承受多少 EHP」）：

    gndEHP(W) = b + c * cumE(W)
    c = (654176-126624)/(4182.8-1161.7) = 174.62  (每 1 金币 → 174.62 EHP)
    b = -76231.2

cumE(W) = initialGold(100) + Σ_{w<=W}(RoundData.rewardGold + Σ数量×EnemyData.reward)

本轮按该式重算 W16..W25 地面 hp：k = 目标EHP / 当前EHP，该波地面怪统一缩放。
空中一律不动（用户已确认空中曲线符合）。
"""
import sys
import json
import shutil
import collections
import openpyxl

XLSX = r"D:/FreedomTower_1/Luban/Config/Datas/Levels/L02/EnemyData.xlsx"
CFG = r"D:/FreedomTower_1/Assets/ConfigJson"
BAK = XLSX + ".bak_20261111_before_l02_w16_25_economy_fit"

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


def load(name):
    d = json.load(open(CFG + "/" + name + ".json", encoding="utf-8"))
    return d if isinstance(d, list) else (d.get("data") or list(d.values())[0])


def build_economy():
    sc = {s["id"]: s for s in load("tbsceneinfo")}
    rd = {x["id"]: x for x in load("tbrounddata")}
    el = {x["id"]: x for x in load("tbenemylist")}
    ed = {x["id"]: x for x in load("tbenemydata")}
    l2 = sc[2]
    cum = float(l2["initialGold"])
    cumE, gcount, acount, gids = {}, {}, {}, {}
    for w, rid in enumerate(l2["RoundList"], 1):
        r = rd[rid]
        ids = []
        for lid in r["EnemyIndexs"]:
            ids += el[lid]["EnemyIndexs"]
        c = collections.Counter(ids)
        kill = 0.0
        for eid, n in c.items():
            kill += ed[eid]["reward"] * n
        cum += r["rewardGold"] + kill
        cumE[w] = cum
        gids[w] = [eid for eid in c if not ed[eid]["isFlying"]]
        gcount[w] = {eid: c[eid] for eid in gids[w]}
        acount[w] = sum(c[eid] for eid in c if ed[eid]["isFlying"])
    return cumE, gcount, acount


def snap(ws):
    return {(r, c): ws.cell(r, c).value
            for r in range(1, ws.max_row + 1) for c in range(1, ws.max_column + 1)}


def main():
    cumE, gcount, _ = build_economy()
    wb = openpyxl.load_workbook(XLSX)
    ws = wb["Sheet"]
    before = snap(ws)
    id2row = {}
    for r in range(4, ws.max_row + 1):
        v = ws.cell(r, ID_COL).value
        if isinstance(v, int):
            id2row[v] = r

    # 以当前配置的 W5/W15 地面 EHP 定标（W1-W15 本轮不动）
    def gnd_ehp(w):
        return sum(gcount[w][eid] * float(ws.cell(id2row[eid], HP_COL).value) for eid in gcount[w])

    e5, e15 = gnd_ehp(5), gnd_ehp(15)
    c = (e15 - e5) / (cumE[15] - cumE[5])
    b = e5 - c * cumE[5]
    print("定标: W5 EHP=%.0f cumE=%.1f | W15 EHP=%.0f cumE=%.1f" % (e5, cumE[5], e15, cumE[15]))
    print("gndEHP = %.1f + %.2f x cumE   (每 1 金币 = %.2f EHP)" % (b, c, c))

    plan, errors = [], []
    for w in range(16, 26):
        target = b + c * cumE[w]
        cur = gnd_ehp(w)
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
        print("W%-2d cumE=%8.1f 目标EHP=%9.0f 当前=%9.0f k=%.4f" % (w, cumE[w], target, cur, k))

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
        got = float(ws2.cell(row, HP_COL).value)
        if abs(got - new) > 1e-9:
            bad += 1
            print("  VERIFY FAIL W%d %s" % (w, name))
    print("回读校验：%d/%d 通过" % (len(plan) - bad, len(plan)))
    for w in range(16, 26):
        rows = [p for p in plan if p[5] == w]
        print("W%-2d 地面 hp: %s" % (w, " | ".join("%s %.1f->%.1f" % (n, o, nv) for _, _, n, o, nv, _ in rows)))
    print("DONE")
    return 0 if bad == 0 else 4


if __name__ == "__main__":
    sys.exit(main())
