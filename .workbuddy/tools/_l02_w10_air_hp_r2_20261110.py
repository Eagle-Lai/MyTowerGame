# -*- coding: utf-8 -*-
"""L02 W10 空中怪（Bat, EnemyData.id=6000095）血量第二轮 -10%（叠加）。

XML 级定点替换：只改 sheet1.xml 中 D33 的 <v>，其余 zip 条目逐字节搬运，
避免 openpyxl 整体保存造成的浮点末位漂移。
"""
import os
import shutil
import zipfile
from pathlib import Path

import openpyxl

ROOT = Path(r"D:\FreedomTower_1")
SRC = ROOT / "Luban/Config/Datas/Levels/L02/EnemyData.xlsx"
BAK = SRC.with_name("EnemyData.xlsx.bak_20261110_before_w10air-10_r2")
SHEET = "xl/worksheets/sheet1.xml"

EXPECT_OLD = 701.721683
NEW_VALUE = 631.549515          # 701.721683 * 0.9 = 631.5495147
OLD_CELL = f'<x:c r="D33" s="1"><x:v>{EXPECT_OLD!r}</x:v></x:c>'
NEW_CELL = f'<x:c r="D33" s="1"><x:v>{NEW_VALUE!r}</x:v></x:c>'


def snapshot(path):
    ws = openpyxl.load_workbook(path).active
    return ({(r, c): ws.cell(row=r, column=c).value
             for r in range(1, ws.max_row + 1)
             for c in range(1, ws.max_column + 1)},
            (ws.max_row, ws.max_column))


def main():
    ws = openpyxl.load_workbook(SRC).active
    assert ws["B33"].value == 6000095, ws["B33"].value
    assert ws["E33"].value == "Bat", ws["E33"].value
    assert ws["N33"].value == 1, ws["N33"].value
    assert abs(float(ws["D33"].value) - EXPECT_OLD) < 1e-9, ws["D33"].value
    print(f"[pre-check] B33={ws['B33'].value} E33={ws['E33'].value} "
          f"N33={ws['N33'].value} D33={ws['D33'].value}")

    if not BAK.exists():
        shutil.copy2(SRC, BAK)
        print(f"[backup] {BAK.name}")
    else:
        print(f"[backup] 已存在，保留原备份：{BAK.name}")

    before, shape_before = snapshot(SRC)

    tmp = SRC.with_name("EnemyData.__tmp2.xlsx")
    with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(tmp, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == SHEET:
                txt = data.decode("utf-8")
                n = txt.count(OLD_CELL)
                if n != 1:
                    raise SystemExit(f"[abort] 目标单元格在 XML 中出现 {n} 次，预期 1 次")
                data = txt.replace(OLD_CELL, NEW_CELL).encode("utf-8")
            zout.writestr(info, data)

    payload = tmp.read_bytes()
    with open(SRC, "wb") as f:
        f.write(payload)
    os.remove(tmp)
    print(f"[write] D33 {EXPECT_OLD} -> {NEW_VALUE}（{len(payload)} bytes）")

    ws2 = openpyxl.load_workbook(SRC).active
    got = ws2["D33"].value
    print(f"[readback] row33 id={ws2['B33'].value} name={ws2['E33'].value} hp={got!r}")
    if abs(float(got) - NEW_VALUE) > 1e-9:
        raise SystemExit("[abort] 回读值与写入值不一致")

    after, shape_after = snapshot(SRC)
    assert shape_before == shape_after, (shape_before, shape_after)
    keys = set(before) | set(after)
    diffs = [(k, before.get(k), after.get(k)) for k in sorted(keys)
             if before.get(k) != after.get(k)]
    print(f"[diff] 变化单元格 {len(diffs)} 个 / 全表 {shape_after[0]}x{shape_after[1]}")
    for (r, c), o, n in diffs:
        print(f"   R{r}C{c}: {o!r} -> {n!r}")
    if len(diffs) != 1 or diffs[0][0] != (33, 4):
        raise SystemExit("[abort] 白名单外出现改动")

    print("[ok] 第二轮定点修改完成，白名单外零改动（D33 唯一变化）")


if __name__ == "__main__":
    main()
