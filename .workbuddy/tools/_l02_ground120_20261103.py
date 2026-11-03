#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性手工改表（L02 专用，2026-11-03 第三轮口径）。

需求：第二关「第 5 波(不含) → 第 25 波」**地面怪物** hp → 当前值的 120%（叠加）。
  · 用户当轮确认：**A 叠加**（当前值 ×1.2），累计 = 今早原始值 ×2.01（1.34×1.25×1.2）。
  · **空中不动**：上一轮已改到 ×1.20，本轮保持（W5 那只 Bat 也不动）。
  · W1-W5 不动；只动 hp，其余字段（speed/armor/reward/数量/间隔/波次奖励）一律不动；只动 L02。

用法：
  python _l02_ground120_20261103.py values   # 干跑（只读）
  python _l02_ground120_20261103.py apply    # 备份 + 写盘
  python _l02_ground120_20261103.py verify   # 只读校验（地面=基线×1.2、空中必须与基线逐字节相同）

导出建议用编辑器菜单 `Tools/塔防/3. 导出配置表（Luban）`（会自动保留 FTProject.Gen.asmdef）；
若改用 exe 导出，导出后必须 `git checkout -- Assets/Gen/FTProject.Gen.asmdef`。
"""
from __future__ import annotations

import pathlib
import re
import shutil
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L02 = ROOT / 'Luban/Config/Datas/Levels/L02'
TAG = 'l02ground120-20261103'
FACTOR = 1.20
WAVE_FROM = 6
WAVE_TO = 25
BAK0 = 'EnemyData.xlsx.bak_20261103_before_groundhp134'   # 今早原始值（仅用于报告累计倍率）


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
        plan[w] = dict(row=rec['row'], ids=ids, g=g, air=sorted({i for i in ids if enemy[i]['fly']}))
        for eid in g:
            e = enemy[eid]
            rows.append(dict(w=w, eid=eid, name=e['name'], row=e['row'], fly=0,
                             old=e['hp'], new=round(e['hp'] * FACTOR, 6)))
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

    if mode == 'values':
        print(f'L02 W{WAVE_FROM}-W{WAVE_TO} 地面 {len(rows)} 行 ×{FACTOR}（空中本轮不动）\n')
        print('波  地面行  地面总hp 当前 -> 之后      空中总hp（不变）     EHP 当前 -> 之后')
        tg0 = tg1 = te0 = te1 = 0.0
        for w in range(WAVE_FROM, WAVE_TO + 1):
            p = plan[w]
            wr = {r['eid']: r['new'] for r in rows if r['w'] == w}
            g0 = sum(enemy[i]['hp'] for i in p['ids'] if not enemy[i]['fly'])
            g1 = sum(wr[i] for i in p['ids'] if not enemy[i]['fly'])
            a0 = sum(enemy[i]['hp'] for i in p['ids'] if enemy[i]['fly'])
            e0, e1 = ehp_of(p['ids'], enemy), ehp_of(p['ids'], enemy, wr)
            tg0 += g0; tg1 += g1; te0 += e0; te1 += e1
            print(f'W{w:<3}{len(p["g"]):<8}{g0:>11.2f} -> {g1:>11.2f}   {a0:>11.2f}          {e0:>13.1f} -> {e1:>13.1f}')
        print(f'\n合计：地面 {tg0:.2f} -> {tg1:.2f}；EHP {te0:.1f} -> {te1:.1f} (×{te1/te0:.6f})')
        if (L02 / BAK0).exists():
            tmp = ROOT / '.workbuddy/tools/__pycache__/base0_l02.xlsx'
            tmp.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(L02 / BAK0, tmp)
            wb0 = openpyxl.load_workbook(tmp, data_only=True)
            _, base = read_enemy(wb0[wb0.sheetnames[0]])
            print('相对今早原始值的累计倍率：',
                  sorted({round(r['new'] / base[r['eid']]['hp'], 4) for r in rows}))
        print('\n改动明细：')
        for r in rows:
            print(f'  W{r["w"]:<3}{r["name"]:<9}{r["eid"]:<9}{r["old"]:>14.6f} -> {r["new"]:.6f}')
        if problems:
            print('\n⚠ 波次/desc 不一致：')
            for p in problems:
                print('  ' + p)
        return 0

    bak_ed = L02 / 'EnemyData.xlsx.bak_20261103_before_ground120'
    bak_el = L02 / 'EnemyList.xlsx.bak_20261103_before_ground120'

    if mode == 'verify':
        assert bak_ed.exists(), '缺少 .bak 基线'
        tmp = ROOT / '.workbuddy/tools/__pycache__/verify2_l02.xlsx'
        tmp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bak_ed, tmp)
        wb0 = openpyxl.load_workbook(tmp, data_only=True)
        _, base = read_enemy(wb0[wb0.sheetnames[0]])
        bad = []
        planned = {r['eid'] for r in rows}
        for r in rows:
            cur = float(ws_ed.cell(r['row'], h_ed['hp']).value)
            exp = round(base[r['eid']]['hp'] * FACTOR, 6)
            if abs(cur - exp) > 1e-6:
                bad.append(f'地面 id={r["eid"]} W{r["w"]} 期望 {exp} 实为 {cur}')
        for eid, e in enemy.items():
            if eid in planned:
                continue
            # 未列入计划的行（空中 + W1-W5）必须与基线逐字节相同
            if abs(e['hp'] - base[eid]['hp']) > 1e-9:
                bad.append(f'非计划行被改动 id={eid} fly={e["fly"]}：{base[eid]["hp"]} -> {e["hp"]}')
        if bad:
            print('❌ 校验失败：')
            for b in bad[:20]:
                print('  ' + b)
            return 1
        print(f'✅ 校验通过：地面 {len(rows)} 行 = 基线×{FACTOR}；'
              f'其余 {len(enemy) - len(rows)} 行（含全部空中 20 行、W1-W5 10 行）与基线完全一致')
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
    print(f'已写入 EnemyData {len(rows)} 行 hp（仅地面）')

    _, enemy_now = read_enemy(openpyxl.load_workbook(L02 / 'EnemyData.xlsx', data_only=True)['Sheet'])
    for w in range(WAVE_FROM, WAVE_TO + 1):
        rec = waves[w]
        ehp = ehp_of(rec['ids'], enemy_now)
        desc = re.sub(rf'\s*\|\s*{TAG}:[^|]*$', '', rec['desc']).rstrip()
        ws_el.cell(rec['row'], h_el['desc']).value = f'{desc} | {TAG}: ground x{FACTOR} (EHP={ehp:.6f})'
    wb_el.save(L02 / 'EnemyList.xlsx')
    print(f'已写入 EnemyList {WAVE_TO - WAVE_FROM + 1} 条备注')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
