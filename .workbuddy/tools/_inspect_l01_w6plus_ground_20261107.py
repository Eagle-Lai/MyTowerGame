#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读侦察：L01 各波次（按 SceneInfo.RoundList 真实顺序）的地面怪构成、变体是否跨波复用。

用于确认「W5 再 +20% + W6–W25 地面 +50%」的实际影响面。
"""
import collections
import pathlib

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L01 = ROOT / 'Luban/Config/Datas/Levels/L01'


def heads(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def main():
    # 真实波次顺序
    ws = openpyxl.load_workbook(L01 / 'SceneInfo.xlsx', data_only=True)['Sheet1']
    h = heads(ws)
    order = [int(x) for x in str(ws.cell(4, h['RoundList']).value).split(',') if str(x).strip()]
    print(f'RoundList({len(order)}): {order}')

    # EnemyData
    wb = openpyxl.load_workbook(L01 / 'EnemyData.xlsx', data_only=True)
    ws_ed = wb[wb.sheetnames[0]]
    h_ed = heads(ws_ed)
    ed = {}
    for r in range(4, ws_ed.max_row + 1):
        eid = ws_ed.cell(r, h_ed['id']).value
        if eid is None:
            continue
        ed[int(eid)] = dict(row=r, name=ws_ed.cell(r, h_ed['name']).value,
                            hp=float(ws_ed.cell(r, h_ed['hp']).value),
                            armor=float(ws_ed.cell(r, h_ed['armor']).value or 0),
                            fly=int(ws_ed.cell(r, h_ed['isFlying']).value or 0))
    wb.close()

    # EnemyList
    wb = openpyxl.load_workbook(L01 / 'EnemyList.xlsx', data_only=True)
    ws_el = wb['Sheet1']
    h_el = heads(ws_el)
    groups = {}
    for r in range(4, ws_el.max_row + 1):
        lid = ws_el.cell(r, h_el['id']).value
        if lid is None:
            continue
        seq = [int(x) for x in str(ws_el.cell(r, h_el['EnemyIndexs']).value).split(',') if str(x).strip()]
        groups[int(lid)] = dict(row=r, seq=seq, desc=str(ws_el.cell(r, h_el['desc']).value or ''))
    wb.close()

    owner = collections.defaultdict(set)   # enemyId -> {wave}
    print('\n波 | roundId | 编组行 | 出怪 | 地面变体(去重) | 空中变体(去重)')
    wave_ground = {}
    for w, rid in enumerate(order, 1):
        g = groups.get(rid)
        if g is None:
            print(f'W{w:<3}{rid:<8} 缺少编组')
            continue
        gnd = sorted({i for i in g['seq'] if not ed[i]['fly']})
        air = sorted({i for i in g['seq'] if ed[i]['fly']})
        wave_ground[w] = gnd
        for i in gnd:
            owner[i].add(w)
        print(f'W{w:<3}{rid:<8} {g["row"]:<7}{len(g["seq"]):<6}{gnd} | {air}')

    print('\n=== 跨波复用的地面变体 ===')
    shared = {i: sorted(ws_) for i, ws_ in owner.items() if len(ws_) > 1}
    if not shared:
        print('无：每个地面变体只属于自己的那一波')
    for i, ws_ in sorted(shared.items()):
        print(f'  {i} {ed[i]["name"]}: 波次 {ws_}')

    print('\n=== 各波地面变体明细（含变体 desc 里的 wave 标记）===')
    for w in sorted(wave_ground):
        for i in wave_ground[w]:
            e = ed[i]
            print(f'  W{w:<3}id={i:<9}{e["name"]:<12}hp={e["hp"]:<12.6f}armor={e["armor"]}')

    allg = sorted(owner)
    print(f'\n地面变体总数（去重）: {len(allg)}；W5 地面: {wave_ground.get(5)}')
    print(f'W6–W25 地面变体（去重）: {sorted({i for w in range(6, 26) for i in wave_ground.get(w, [])})}')
    nowave = [w for w in range(6, 26) if not wave_ground.get(w)]
    print(f'W6–W25 中没有地面怪的波次: {nowave or "无"}')


if __name__ == '__main__':
    main()
