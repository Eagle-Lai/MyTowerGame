#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性手工改表（L02 专用，2026-11-03 第二轮口径）。

需求：第二关「第 5 波(不含) → 第 25 波」
  · 地面怪物 hp → **当前值的 125%**（叠加：今天早上的 ×1.34 仍保留，累计 = 原始 ×1.675）
  · 空中怪物 hp → **当前值的 120%**（空中此前未动过，累计 = 原始 ×1.20）
W1-W5 全部不动；只动 hp，其余字段（speed/armor/reward/数量/间隔/波次奖励）一律不动；
只动 L02 目录。

用法：
  python _l02_hp125air120_20261103.py values   # 干跑，只打印目标值（只读）
  python _l02_hp125air120_20261103.py apply    # 备份 + 写盘
  python _l02_hp125air120_20261103.py verify   # 只读校验（对照本次 .bak 基线）

改完必须跑 Luban 导出；导出后会删 Assets/Gen/FTProject.Gen.asmdef，记得 git checkout 恢复。
"""
from __future__ import annotations

import pathlib
import re
import shutil
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L02 = ROOT / 'Luban/Config/Datas/Levels/L02'
TAG = 'l02hp125-20261103'
G_FACTOR = 1.25      # 地面：当前值 ×1.25（叠加）
A_FACTOR = 1.20      # 空中：当前值 ×1.20
WAVE_FROM = 6
WAVE_TO = 25
BAK_SRC = 'EnemyData.xlsx.bak_20261103_before_groundhp134'   # 今天早上的原始基线（仅用于报告累计倍率）


def heads(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def wave_order(ws):
    h = heads(ws)
    return [int(x) for x in str(ws.cell(4, h['RoundList']).value).replace('，', ',').split(',')
            if str(x).strip()]


def read_rounds(ws):
    h = heads(ws)
    out = {}
    for r in range(4, ws.max_row + 1):
        rid = ws.cell(r, h['id']).value
        if rid is None:
            continue
        out[int(rid)] = [int(x) for x in str(ws.cell(r, h['EnemyIndexs']).value).split(',')
                         if str(x).strip()]
    return h, out


def read_enemylist(ws):
    h = heads(ws)
    out = {}
    for r in range(4, ws.max_row + 1):
        lid = ws.cell(r, h['id']).value
        if lid is None:
            continue
        out[int(lid)] = dict(row=r,
                             ids=[int(x) for x in str(ws.cell(r, h['EnemyIndexs']).value).split(',')
                                  if str(x).strip()],
                             desc=str(ws.cell(r, h['desc']).value or ''))
    return h, out


def read_enemy(ws):
    h = heads(ws)
    out = {}
    for r in range(4, ws.max_row + 1):
        eid = ws.cell(r, h['id']).value
        if eid is None:
            continue
        out[int(eid)] = dict(row=r,
                             name=ws.cell(r, h['name']).value,
                             hp=float(ws.cell(r, h['hp']).value),
                             armor=float(ws.cell(r, h['armor']).value or 0),
                             fly=int(ws.cell(r, h['isFlying']).value or 0),
                             desc=str(ws.cell(r, h['desc']).value or ''))
    return h, out


def ehp_of(ids, enemy, override=None):
    override = override or {}
    return sum(override.get(i, enemy[i]['hp']) / (1 - enemy[i]['armor']) for i in ids)


def build_plan(enemy, waves):
    plan, rows, problems = {}, [], []
    for w in range(WAVE_FROM, WAVE_TO + 1):
        rec = waves[w]
        ids = rec['ids']
        for eid in set(ids):
            m = re.search(r'wave=(\d+)', enemy[eid]['desc'])
            if m and int(m.group(1)) != w:
                problems.append(f'W{w} 引用 id={eid}，但该行 desc 写的是 wave={m.group(1)}')
        g = sorted({i for i in ids if not enemy[i]['fly']})
        a = sorted({i for i in ids if enemy[i]['fly']})
        plan[w] = dict(row=rec['row'], ids=ids, g=g, a=a)
        for eid in g + a:
            e = enemy[eid]
            f = A_FACTOR if e['fly'] else G_FACTOR
            rows.append(dict(w=w, eid=eid, name=e['name'], row=e['row'], fly=e['fly'],
                             old=e['hp'], new=round(e['hp'] * f, 6)))
    return plan, rows, problems


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'

    wb_si = openpyxl.load_workbook(L02 / 'SceneInfo.xlsx', data_only=True)
    ws_si = wb_si[wb_si.sheetnames[0]]
    order = wave_order(ws_si)
    assert len(order) == 25, f'RoundList 应 25 波，实为 {len(order)}'

    wb_rd = openpyxl.load_workbook(L02 / 'RoundData.xlsx')
    ws_rd = wb_rd[wb_rd.sheetnames[0]]
    h_rd, rounds = read_rounds(ws_rd)

    wb_el = openpyxl.load_workbook(L02 / 'EnemyList.xlsx')
    ws_el = wb_el[wb_el.sheetnames[0]]
    h_el, elists = read_enemylist(ws_el)

    wb_ed = openpyxl.load_workbook(L02 / 'EnemyData.xlsx')
    ws_ed = wb_ed[wb_ed.sheetnames[0]]
    h_ed, enemy = read_enemy(ws_ed)

    waves = {}
    for w, rid in enumerate(order, 1):
        lid = rounds[rid][0]
        waves[w] = dict(lid=lid, rid=rid, row=elists[lid]['row'],
                        ids=elists[lid]['ids'], desc=elists[lid]['desc'])

    plan, rows, problems = build_plan(enemy, waves)
    g_rows = [r for r in rows if not r['fly']]
    a_rows = [r for r in rows if r['fly']]

    if mode == 'values':
        print(f'L02 W{WAVE_FROM}-W{WAVE_TO}：地面 {len(g_rows)} 行 ×{G_FACTOR}，'
              f'空中 {len(a_rows)} 行 ×{A_FACTOR}（W1-W5 不动）\n')
        print('波  地面行 空中行  地面总hp 当前 -> 之后     空中总hp 当前 -> 之后     EHP 当前 -> 之后')
        tg0 = tg1 = ta0 = ta1 = te0 = te1 = 0.0
        for w in range(WAVE_FROM, WAVE_TO + 1):
            p = plan[w]
            wr = {r['eid']: r['new'] for r in rows if r['w'] == w}
            g0 = sum(enemy[i]['hp'] for i in p['ids'] if not enemy[i]['fly'])
            g1 = sum(wr[i] for i in p['ids'] if not enemy[i]['fly'])
            a0 = sum(enemy[i]['hp'] for i in p['ids'] if enemy[i]['fly'])
            a1 = sum(wr[i] for i in p['ids'] if enemy[i]['fly'])
            e0 = ehp_of(p['ids'], enemy)
            e1 = ehp_of(p['ids'], enemy, wr)
            tg0 += g0; tg1 += g1; ta0 += a0; ta1 += a1; te0 += e0; te1 += e1
            print(f'W{w:<3}{len(p["g"]):<7}{len(p["a"]):<7}{g0:>11.2f} -> {g1:>11.2f}  '
                  f'{a0:>11.2f} -> {a1:>11.2f}  {e0:>13.1f} -> {e1:>13.1f}')
        print(f'\n合计：地面 {tg0:.2f} -> {tg1:.2f}；空中 {ta0:.2f} -> {ta1:.2f}；'
              f'EHP {te0:.1f} -> {te1:.1f} (×{te1 / te0:.6f})')

        # 相对「今天早上改动前」的累计倍率
        tmp = ROOT / '.workbuddy/tools/__pycache__/base_l02.xlsx'
        if (L02 / BAK_SRC).exists():
            tmp.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(L02 / BAK_SRC, tmp)
            wb0 = openpyxl.load_workbook(tmp, data_only=True)
            _, base = read_enemy(wb0[wb0.sheetnames[0]])
            ratios = sorted({round(r['new'] / base[r['eid']]['hp'], 4) for r in rows})
            print(f'相对 {BAK_SRC} 的累计倍率：{ratios}')
        print('\n改动明细：')
        for r in rows:
            print(f'  W{r["w"]:<3}{"地" if not r["fly"] else "空"} {r["name"]:<9}{r["eid"]:<9}'
                  f'{r["old"]:>14.6f} -> {r["new"]:.6f}')
        if problems:
            print('\n⚠ 波次/desc 不一致：')
            for p in problems:
                print('  ' + p)
        return 0

    bak_ed = L02 / 'EnemyData.xlsx.bak_20261103_before_hp125air120'
    bak_el = L02 / 'EnemyList.xlsx.bak_20261103_before_hp125air120'

    if mode == 'verify':
        assert bak_ed.exists(), '缺少 .bak 基线'
        tmp = ROOT / '.workbuddy/tools/__pycache__/verify_l02.xlsx'
        tmp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bak_ed, tmp)
        wb0 = openpyxl.load_workbook(tmp, data_only=True)
        _, base = read_enemy(wb0[wb0.sheetnames[0]])
        bad = []
        for r in rows:
            exp = round(base[r['eid']]['hp'] * (A_FACTOR if r['fly'] else G_FACTOR), 6)
            cur = float(ws_ed.cell(r['row'], h_ed['hp']).value)
            if abs(cur - exp) > 1e-6:
                bad.append(f'id={r["eid"]} W{r["w"]} 期望 {exp} 实为 {cur}')
        planned = {r['eid'] for r in rows}
        for eid, e in enemy.items():
            if eid in planned:
                continue
            if abs(e['hp'] - base[eid]['hp']) > 1e-9:
                bad.append(f'id={eid} 未列入计划却被改动：{base[eid]["hp"]} -> {e["hp"]}')
        if bad:
            print('❌ 校验失败：')
            for b in bad[:20]:
                print('  ' + b)
            return 1
        print(f'✅ 校验通过：地面 {len(g_rows)} 行 = 基线×{G_FACTOR}、空中 {len(a_rows)} 行 = 基线×{A_FACTOR}；'
              f'其余 {len(enemy) - len(rows)} 行未改动')
        return 0

    assert mode == 'apply', f'未知模式 {mode}'
    if all(abs(float(ws_ed.cell(r['row'], h_ed['hp']).value) - r['new']) < 1e-6 for r in rows):
        print('⏭ 已是目标值，未重复写入')
        return 0

    for src, dst in ((L02 / 'EnemyData.xlsx', bak_ed), (L02 / 'EnemyList.xlsx', bak_el)):
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f'备份 -> {dst.name}')

    for r in rows:
        ws_ed.cell(r['row'], h_ed['hp']).value = r['new']
    wb_ed.save(L02 / 'EnemyData.xlsx')
    print(f'已写入 EnemyData {len(rows)} 行 hp（地面 {len(g_rows)} / 空中 {len(a_rows)}）')

    _, enemy_now = read_enemy(openpyxl.load_workbook(L02 / 'EnemyData.xlsx', data_only=True)['Sheet'])
    for w in range(WAVE_FROM, WAVE_TO + 1):
        rec = waves[w]
        ehp = ehp_of(rec['ids'], enemy_now)
        desc = re.sub(rf'\s*\|\s*{TAG}:[^|]*$', '', rec['desc']).rstrip()
        ws_el.cell(rec['row'], h_el['desc']).value = (
            f'{desc} | {TAG}: ground x{G_FACTOR}, air x{A_FACTOR} (EHP={ehp:.6f})')
    wb_el.save(L02 / 'EnemyList.xlsx')
    print(f'已写入 EnemyList {WAVE_TO - WAVE_FROM + 1} 条备注')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
