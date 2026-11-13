# -*- coding: utf-8 -*-
"""L02 W10 空中怪（Bat, EnemyData.id=6000095）血量通用定点修改器。

用法：
  python _l02_w10_air_hp_set.py --old 599.972039 --new 569.973437 --bak _r4

做法：XML 级定点替换，只改 sheet1.xml 中 D33 的 <v>，其余 zip 条目逐字节搬运，
避免 openpyxl 整体保存造成的浮点末位漂移。写前核对 id/name/isFlying/旧值，
写后回读 + 全表逐格比对，白名单外有任何改动即中止。
"""
import argparse
import os
import shutil
import zipfile
from pathlib import Path

import openpyxl

ROOT = Path(r"D:\FreedomTower_1")
SRC = ROOT / "Luban/Config/Datas/Levels/L02/EnemyData.xlsx"
SHEET = "xl/worksheets/sheet1.xml"
TARGET_ID, TARGET_NAME, TARGET_FLY = 6000095, "Bat", 1
CELL_ROW, CELL_COL = 33, 4          # D33 = Bat 的 hp


def snapshot(path):
    ws = openpyxl.load_workbook(path).active
    return ({(r, c): ws.cell(row=r, column=c).value
             for r in range(1, ws.max_row + 1)
             for c in range(1, ws.max_column + 1)},
            (ws.max_row, ws.max_column))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True, type=float)
    ap.add_argument("--new", required=True, type=float)
    ap.add_argument("--bak", required=True, help="备份后缀，如 _r4")
    ap.add_argument("--decimals", type=int, default=6)
    a = ap.parse_args()

    old_s = f"{round(a.old, a.decimals):.{a.decimals}f}".rstrip("0").rstrip(".")
    new_s = f"{round(a.new, a.decimals):.{a.decimals}f}".rstrip("0").rstrip(".")
    old_cell = f'<x:c r="D{CELL_ROW}" s="1"><x:v>{old_s}</x:v></x:c>'
    new_cell = f'<x:c r="D{CELL_ROW}" s="1"><x:v>{new_s}</x:v></x:c>'
    print(f"[plan] D{CELL_ROW}: {old_s} -> {new_s}")

    ws = openpyxl.load_workbook(SRC).active
    assert ws["B33"].value == TARGET_ID, ws["B33"].value
    assert ws["E33"].value == TARGET_NAME, ws["E33"].value
    assert ws["N33"].value == TARGET_FLY, ws["N33"].value
    assert abs(float(ws["D33"].value) - a.old) < 1e-9, ws["D33"].value
    print(f"[pre-check] id={ws['B33'].value} name={ws['E33'].value} "
          f"isFlying={ws['N33'].value} hp={ws['D33'].value!r}")

    bak = SRC.with_name(f"EnemyData.xlsx.bak_20261110_before_w10air{a.bak}")
    if not bak.exists():
        shutil.copy2(SRC, bak)
        print(f"[backup] {bak.name}")
    else:
        print(f"[backup] 已存在，保留原备份：{bak.name}")

    before, shape_before = snapshot(SRC)

    tmp = SRC.with_name(f"EnemyData.__tmp{a.bak}.xlsx")
    with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(tmp, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == SHEET:
                txt = data.decode("utf-8")
                n = txt.count(old_cell)
                if n != 1:
                    raise SystemExit(f"[abort] 目标单元格在 XML 中出现 {n} 次，预期 1 次")
                data = txt.replace(old_cell, new_cell).encode("utf-8")
            zout.writestr(info, data)

    payload = tmp.read_bytes()
    with open(SRC, "wb") as f:
        f.write(payload)
    os.remove(tmp)
    print(f"[write] {old_s} -> {new_s}（{len(payload)} bytes）")

    ws2 = openpyxl.load_workbook(SRC).active
    got = ws2["D33"].value
    print(f"[readback] row33 id={ws2['B33'].value} name={ws2['E33'].value} hp={got!r}")
    if abs(float(got) - a.new) > 1e-9:
        raise SystemExit("[abort] 回读值与写入值不一致")

    after, shape_after = snapshot(SRC)
    assert shape_before == shape_after, (shape_before, shape_after)
    diffs = [(k, before.get(k), after.get(k)) for k in sorted(set(before) | set(after))
             if before.get(k) != after.get(k)]
    print(f"[diff] 变化单元格 {len(diffs)} 个 / 全表 {shape_after[0]}x{shape_after[1]}")
    for (r, c), o, n in diffs:
        print(f"   R{r}C{c}: {o!r} -> {n!r}")
    if len(diffs) != 1 or diffs[0][0] != (CELL_ROW, CELL_COL):
        raise SystemExit("[abort] 白名单外出现改动")

    print("[ok] 定点修改完成，白名单外零改动")


if __name__ == "__main__":
    main()
