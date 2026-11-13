# -*- coding: utf-8 -*-
"""L02 W10 空中怪（Bat, EnemyData.id=6000095）血量 -10% —— XML 级定点替换。

openpyxl 整体保存会把所有浮点按 15 位有效数字重写（79 格末位漂移），
不符合“白名单外零改动”。此脚本直接改 xlsx 内部 sheet1.xml 的唯一单元格，
其余 zip 条目逐字节原样搬运。
"""
import os
import shutil
import zipfile
from pathlib import Path

import openpyxl

ROOT = Path(r"D:\FreedomTower_1")
SRC = ROOT / "Luban/Config/Datas/Levels/L02/EnemyData.xlsx"
BAK = SRC.with_name("EnemyData.xlsx.bak_20261110_before_w10air-10")
SHEET = "xl/worksheets/sheet1.xml"

OLD_CELL = '<x:c r="D33" s="1"><x:v>779.690759</x:v></x:c>'
NEW_CELL = '<x:c r="D33" s="1"><x:v>701.721683</x:v></x:c>'


def snapshot(path):
    ws = openpyxl.load_workbook(path).active
    return {(r, c): ws.cell(row=r, column=c).value
            for r in range(1, ws.max_row + 1)
            for c in range(1, ws.max_column + 1)}, (ws.max_row, ws.max_column)


def main():
    ws = openpyxl.load_workbook(SRC).active
    assert ws["B33"].value == 6000095, ws["B33"].value
    assert ws["E33"].value == "Bat", ws["E33"].value
    assert ws["N33"].value == 1, ws["N33"].value
    assert abs(float(ws["D33"].value) - 779.690759) < 1e-9, ws["D33"].value
    print(f"[pre-check] B33={ws['B33'].value} E33={ws['E33'].value} "
          f"N33={ws['N33'].value} D33={ws['D33'].value}")

    before, shape_before = snapshot(SRC)

    tmp = SRC.with_name("EnemyData.__tmp.xlsx")
    replaced = 0
    with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(tmp, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == SHEET:
                txt = data.decode("utf-8")
                n = txt.count(OLD_CELL)
                if n != 1:
                    raise SystemExit(f"[abort] 目标单元格在 XML 中出现 {n} 次，预期 1 次")
                txt = txt.replace(OLD_CELL, NEW_CELL)
                data = txt.encode("utf-8")
                replaced += 1
            zout.writestr(info, data)
    if replaced != 1:
        raise SystemExit("[abort] 未替换到目标条目")

    # 目标文件可能被 WPS/Excel mmap 占用，无法 rename 覆盖 → 原地写字节
    payload = tmp.read_bytes()
    with open(SRC, "wb") as f:
        f.write(payload)
    os.remove(tmp)
    print(f"[write] D33 779.690759 -> 701.721683（{len(payload)} bytes）")

    ws2 = openpyxl.load_workbook(SRC).active
    got = ws2["D33"].value
    print(f"[readback] row33 id={ws2['B33'].value} name={ws2['E33'].value} hp={got!r}")
    if abs(float(got) - 701.721683) > 1e-9:
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

    print("[ok] 定点修改完成，白名单外零改动（D33 唯一变化）")


if __name__ == "__main__":
    main()
