# -*- coding: utf-8 -*-
"""L02 W15 地面四怪血量定点整体上调 15%（×1.15，以当前值为基准）。

目标：
  D54 Chicken 6000140  435.103696 -> 500.36925
  D55 Larva   6000141  282.817405 -> 325.240016
  D56 Crawler 6000142  800.590797 -> 920.679417
  D57 Scarab  6000143  1479.352552 -> 1701.255435

用法：
  python _l02_w15_ground_hp115_20261111.py --apply

做法：XML 级定点替换，只改 sheet1.xml 中四个 <v>，其余 zip 条目逐字节搬运，
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
DEC = 6

# (row, id, name, isFlying, old, new)
TARGETS = [
    (54, 6000140, "Chicken", 0, 435.103696, 435.103696 * 1.15),
    (55, 6000141, "Larva", 0, 282.817405, 282.817405 * 1.15),
    (56, 6000142, "Crawler", 0, 800.590797, 800.590797 * 1.15),
    (57, 6000143, "Scarab", 0, 1479.352552, 1479.352552 * 1.15),
]


def fmt(x):
    return f"{round(x, DEC):.{DEC}f}".rstrip("0").rstrip(".")


def snapshot(path):
    ws = openpyxl.load_workbook(path).active
    return ({(r, c): ws.cell(row=r, column=c).value
             for r in range(1, ws.max_row + 1)
             for c in range(1, ws.max_column + 1)},
            (ws.max_row, ws.max_column))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="不加则只预览")
    a = ap.parse_args()

    ws = openpyxl.load_workbook(SRC).active
    plan = []
    for row, tid, name, fly, old, new in TARGETS:
        assert ws.cell(row, 2).value == tid, (row, ws.cell(row, 2).value)
        assert ws.cell(row, 5).value == name, (row, ws.cell(row, 5).value)
        assert ws.cell(row, 14).value == fly, (row, ws.cell(row, 14).value)
        cur = float(ws.cell(row, 4).value)
        assert abs(cur - old) < 1e-9, (row, cur, old)
        plan.append((row, tid, name, fmt(old), fmt(new)))
        print(f"[plan] D{row} {name:8s} {tid}: {fmt(old)} -> {fmt(new)}")

    if not a.apply:
        print("[dry-run] 未写入")
        return

    bak = SRC.with_name("EnemyData.xlsx.bak_20261111_before_l02w15_ground_hp115")
    if not bak.exists():
        shutil.copy2(SRC, bak)
        print(f"[backup] {bak.name}")
    else:
        print(f"[backup] 已存在，保留原备份：{bak.name}")

    before, shape_before = snapshot(SRC)
    tmp = SRC.with_name("EnemyData.__tmp_ground115.xlsx")
    with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(tmp, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == SHEET:
                txt = data.decode("utf-8")
                for row, _tid, _name, old_s, new_s in plan:
                    old_cell = f'<x:c r="D{row}" s="1"><x:v>{old_s}</x:v></x:c>'
                    new_cell = f'<x:c r="D{row}" s="1"><x:v>{new_s}</x:v></x:c>'
                    n = txt.count(old_cell)
                    if n != 1:
                        raise SystemExit(f"[abort] D{row} 在 XML 中出现 {n} 次，预期 1 次")
                    txt = txt.replace(old_cell, new_cell)
                data = txt.encode("utf-8")
            zout.writestr(info, data)

    payload = tmp.read_bytes()
    with open(SRC, "wb") as f:
        f.write(payload)
    os.remove(tmp)
    print(f"[write] 4 格已写入（{len(payload)} bytes）")

    ws2 = openpyxl.load_workbook(SRC).active
    for row, _tid, name, _o, new_s in plan:
        got = ws2.cell(row, 4).value
        print(f"[readback] D{row} {name}: {got!r}")
        if abs(float(got) - float(new_s)) > 1e-9:
            raise SystemExit(f"[abort] D{row} 回读值与写入值不一致")

    after, shape_after = snapshot(SRC)
    assert shape_before == shape_after, (shape_before, shape_after)
    diffs = [(k, before.get(k), after.get(k)) for k in sorted(set(before) | set(after))
             if before.get(k) != after.get(k)]
    print(f"[diff] 变化单元格 {len(diffs)} 个 / 全表 {shape_after[0]}x{shape_after[1]}")
    for (r, c), o, n2 in diffs:
        print(f"   R{r}C{c}: {o!r} -> {n2!r}")
    expect = {(row, 4) for row, *_ in plan}
    if len(diffs) != len(expect) or {k for k, _, _ in diffs} != expect:
        raise SystemExit("[abort] 白名单外出现改动")

    print("[ok] 定点修改完成，白名单外零改动")


if __name__ == "__main__":
    main()
