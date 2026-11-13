# -*- coding: utf-8 -*-
"""L02 W15（roundId 2015）地面怪 hp ×1.05 —— 2026-11-11

口径：只改 L02 EnemyData 中 W15 实际引用的 4 种地面怪 hp 单元格（D54:D57），
      按当前值 ×1.05（与上一轮 ×1.15 同一口径，不叠加历史基准）。
      D58 空中 Bat 不动；数量 / speed / armor / reward / isFlying 全不动。
定位：Luban/Config/Datas/Levels/L02/EnemyData.xlsx，sheet 'Sheet'，hp 在 D 列。
"""
import sys
import shutil
import openpyxl

XLSX = r"D:/FreedomTower_1/Luban/Config/Datas/Levels/L02/EnemyData.xlsx"
BAK = XLSX + ".bak_20261111_before_l02w15_ground_hp105"
SCALE = 1.05

# (row, id, name, 预期旧值)
TARGETS = [
    (54, 6000140, "Chicken", 500.36925),
    (55, 6000141, "Larva", 325.240016),
    (56, 6000142, "Crawler", 920.679417),
    (57, 6000143, "Scarab", 1701.255435),
]
HP_COL = 4   # D


def snapshot(ws):
    data = {}
    for r in range(1, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            data[(r, c)] = ws.cell(r, c).value
    return data


def main():
    wb = openpyxl.load_workbook(XLSX)
    ws = wb["Sheet"]
    before = snapshot(ws)

    # 1) 严格核对旧值
    errors = []
    for row, eid, name, expect in TARGETS:
        got_id = ws.cell(row, 2).value
        got_name = ws.cell(row, 5).value
        got_hp = ws.cell(row, HP_COL).value
        if got_id != eid or got_name != name:
            errors.append(f"row {row}: 期望 id={eid}/{name}，实际 id={got_id}/{got_name}")
            continue
        if abs(float(got_hp) - expect) > 1e-9:
            errors.append(f"row {row}: 期望 hp={expect}，实际 {got_hp}")
    if errors:
        print("ABORT 旧值不符：")
        for e in errors:
            print("  " + e)
        return 2

    shutil.copy2(XLSX, BAK)
    print("backup ->", BAK)

    # 2) 写入
    changes = []
    for row, eid, name, expect in TARGETS:
        new = round(expect * SCALE, 6)
        ws.cell(row, HP_COL).value = new
        changes.append((row, eid, name, expect, new))
        print(f"D{row} {name}({eid})  {expect} -> {new}")

    wb.save(XLSX)

    # 3) 回读 + 全表比对
    wb2 = openpyxl.load_workbook(XLSX)
    ws2 = wb2["Sheet"]
    after = snapshot(ws2)
    diff = [k for k in before if before[k] != after.get(k)]
    allow = {(row, HP_COL) for row, _, _, _ in TARGETS}
    unexpected = [k for k in diff if k not in allow]
    print(f"changed cells = {len(diff)}, unexpected = {len(unexpected)}")
    if unexpected:
        for k in unexpected[:20]:
            print("  UNEXPECTED", k, before[k], "->", after.get(k))
        return 3

    for row, eid, name, expect, new in changes:
        got = ws2.cell(row, HP_COL).value
        ok = abs(float(got) - new) < 1e-9
        print(f"verify D{row} {name} = {got} {'OK' if ok else 'FAIL'}")
        if not ok:
            return 4
    print("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
