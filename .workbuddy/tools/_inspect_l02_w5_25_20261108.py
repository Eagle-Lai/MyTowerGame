#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读：打印 L02 的 SceneInfo/RoundData/EnemyList/EnemyData 结构（W5–W25）。

不写任何文件。
"""
from __future__ import annotations

import pathlib
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L02 = ROOT / 'Luban/Config/Datas/Levels/L02'


def dump(name, max_rows=40):
    p = L02 / f'{name}.xlsx'
    wb = openpyxl.load_workbook(p, data_only=True)
    for ws in wb.worksheets:
        print(f'--- {name} / sheet={ws.title} rows={ws.max_row} cols={ws.max_column}')
        for r in range(1, min(ws.max_row, max_rows) + 1):
            vals = [ws.cell(r, c).value for c in range(1, ws.max_column + 1)]
            print(f'  r{r}: {vals}')
    print()


if __name__ == '__main__':
    which = sys.argv[1:] or ['SceneInfo', 'RoundData']
    for w in which:
        dump(w, int(sys.argv[-1]) if sys.argv[-1].isdigit() else 40)
