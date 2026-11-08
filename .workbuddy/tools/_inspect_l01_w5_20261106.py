#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读侦察：L01 W5（按 SceneInfo.RoundList 的真实波次顺序）引用了哪些怪、哪些是地面、当前 hp 多少。"""
import pathlib
import re

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L01 = ROOT / 'Luban/Config/Datas/Levels/L01'


def heads(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def main():
    ws = openpyxl.load_workbook(L01 / 'SceneInfo.xlsx', data_only=True)['Sheet1']
    h = heads(ws)
    print('SceneInfo 表头:', list(h.keys()))
    for r in range(4, ws.max_row + 1):
        if ws.cell(r, h['id']).value is None:
            continue
        print(f"  id={ws.cell(r, h['id']).value} name={ws.cell(r, h['name']).value!r}")
        order = [int(x) for x in str(ws.cell(r, h['RoundList']).value).split(',') if str(x).strip()]
        print(f'  RoundList({len(order)}): {order}')
        w5_rid = order[4]
        print(f'  => W5 roundId = {w5_rid}')

    # RoundData
    wb = openpyxl.load_workbook(L01 / 'RoundData.xlsx', data_only=True)
    ws_rd = wb[wb.sheetnames[0]]
    h_rd = heads(ws_rd)
    print('\nRoundData 表头:', list(h_rd.keys()))
    for r in range(4, ws_rd.max_row + 1):
        rid = ws_rd.cell(r, h_rd['id']).value
        if rid is None:
            continue
        vals = {k: ws_rd.cell(r, v).value for k, v in h_rd.items()}
        if int(rid) == w5_rid:
            print(f'  [W5] row={r} ' + ', '.join(f'{k}={v}' for k, v in vals.items()))
    wb.close()

    # EnemyList
    wb = openpyxl.load_workbook(L01 / 'EnemyList.xlsx', data_only=True)
    ws_el = wb[wb.sheetnames[0]]
    h_el = heads(ws_el)
    print('\nEnemyList 表头:', list(h_el.keys()))
    groups = []
    for r in range(4, ws_el.max_row + 1):
        lid = ws_el.cell(r, h_el['id']).value
        if lid is None:
            continue
        desc = str(ws_el.cell(r, h_el['desc']).value or '')
        m = re.match(r'L(\d+) W(\d+)/(\d+)', desc)
        if m and int(m.group(2)) == 5:
            ids = [int(x) for x in str(ws_el.cell(r, h_el['EnemyIndexs']).value).split(',') if str(x).strip()]
            groups.append((r, int(lid), ids, desc))
            print(f'\n  W5 编组 row={r} id={lid}\n    desc={desc}\n    EnemyIndexs({len(ids)})={ids}')
    wb.close()

    # EnemyData
    wb = openpyxl.load_workbook(L01 / 'EnemyData.xlsx', data_only=True)
    ws_ed = wb[wb.sheetnames[0]]
    h_ed = heads(ws_ed)
    print('\nEnemyData 表头:', list(h_ed.keys()))
    ed = {}
    for r in range(4, ws_ed.max_row + 1):
        eid = ws_ed.cell(r, h_ed['id']).value
        if eid is None:
            continue
        ed[int(eid)] = dict(row=r, name=ws_ed.cell(r, h_ed['name']).value,
                            hp=ws_ed.cell(r, h_ed['hp']).value,
                            armor=ws_ed.cell(r, h_ed['armor']).value,
                            fly=ws_ed.cell(r, h_ed['isFlying']).value,
                            desc=ws_ed.cell(r, h_ed['desc']).value)
    wb.close()

    all_ids = sorted({i for _, _, ids, _ in groups for i in ids})
    print('\nW5 涉及怪物（全部去重）：')
    for i in all_ids:
        e = ed[i]
        print(f"  id={i:<4} row={e['row']:<4} {str(e['name']):<14} hp={e['hp']} armor={e['armor']} isFlying={e['fly']}  -> {'空中' if e['fly'] else '地面'}")
        print(f"        desc={e['desc']!r}")
    ground = [i for i in all_ids if not ed[i]['fly']]
    print(f"\n地面怪 {len(ground)} 个: {ground}")


if __name__ == '__main__':
    main()
