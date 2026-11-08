#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性定点改表（2026-11-07 用户口径，仅 L01）：

    W6–W9 地面怪 hp ×1.3（**叠加**在现值之上；W6–W9 已历 11-06 ×1.5 与今早 ×1.5，累计约 ×1.95）

基线 = 改动前的现值（乘性改动，重复执行会复利，带幂等护栏：desc 含 TAG 即拒绝重跑）。
范围：只 L01、只第 6–9 波（按 SceneInfo.RoundList 展开）、只地面变体（isFlying=0）；
      空中一律不动，数量/间隔/奖励/护甲/速度/波型不动。

用法：
  python _l01_w6_9_ground_hp_20261107.py values | apply | verify
"""
import pathlib
import re
import shutil
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L01 = ROOT / 'Luban/Config/Datas/Levels/L01'

TAG = 'groundhp3-20261107'
WAVE_FROM, WAVE_TO = 6, 9
FACTOR = 1.3
BAK_ED = L01 / 'EnemyData.xlsx.bak_20261107_groundhp3'
BAK_EL = L01 / 'EnemyList.xlsx.bak_20261107_groundhp3'


def heads(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def load_copy(path, alias):
    if path.suffix == '.xlsx':
        return path
    tmp = ROOT / '.workbuddy/tools/__pycache__/bakcheck'
    tmp.mkdir(parents=True, exist_ok=True)
    dst = tmp / f'{alias}.xlsx'
    shutil.copy2(path, dst)
    return dst


def read_scene():
    ws = openpyxl.load_workbook(L01 / 'SceneInfo.xlsx', data_only=True)['Sheet1']
    h = heads(ws)
    return [int(x) for x in str(ws.cell(4, h['RoundList']).value).split(',') if str(x).strip()]


def read_enemy(path):
    wb = openpyxl.load_workbook(load_copy(path, 'EnemyData_' + path.name.replace('.', '_')), data_only=True)
    ws = wb[wb.sheetnames[0]]
    h = heads(ws)
    out = {}
    for r in range(4, ws.max_row + 1):
        eid = ws.cell(r, h['id']).value
        if eid is None:
            continue
        out[int(eid)] = dict(row=r, name=ws.cell(r, h['name']).value,
                             hp=float(ws.cell(r, h['hp']).value),
                             armor=float(ws.cell(r, h['armor']).value or 0),
                             fly=int(ws.cell(r, h['isFlying']).value or 0))
    wb.close()
    return out


def read_groups(path):
    wb = openpyxl.load_workbook(load_copy(path, 'EnemyList_' + path.name.replace('.', '_')), data_only=True)
    ws = wb['Sheet1']
    h = heads(ws)
    out = {}
    for r in range(4, ws.max_row + 1):
        lid = ws.cell(r, h['id']).value
        if lid is None:
            continue
        out[int(lid)] = dict(row=r,
                             seq=[int(x) for x in str(ws.cell(r, h['EnemyIndexs']).value).split(',') if str(x).strip()],
                             desc=str(ws.cell(r, h['desc']).value or ''))
    wb.close()
    return out


def ehp_of(seq, enemy):
    return sum(enemy[i]['hp'] / (1 - enemy[i]['armor']) for i in seq)


def build_plan(order, groups, enemy):
    """[(wave, roundId, el_row, ground_ids, air_ids, old_ehp, new_ehp, desc)]"""
    plan = []
    for w, rid in enumerate(order, 1):
        if not (WAVE_FROM <= w <= WAVE_TO):
            continue
        g = groups[rid]
        ground = sorted({i for i in g['seq'] if not enemy[i]['fly']})
        air = sorted({i for i in g['seq'] if enemy[i]['fly']})
        old = ehp_of(g['seq'], enemy)
        patched = {**enemy, **{i: dict(enemy[i], hp=round(enemy[i]['hp'] * FACTOR, 6)) for i in ground}}
        plan.append((w, rid, g['row'], ground, air, old, ehp_of(g['seq'], patched), g['desc']))
    if not plan:
        raise SystemExit(f'没有匹配到 W{WAVE_FROM}–W{WAVE_TO}')
    return plan


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'

    order = read_scene()
    cur = read_enemy(L01 / 'EnemyData.xlsx')
    groups = read_groups(L01 / 'EnemyList.xlsx')

    if mode in ('values', 'verify'):
        base = cur
        if mode == 'verify':
            if not BAK_ED.exists():
                print('❌ 缺少改前基准，无法校验')
                return 1
            base = read_enemy(BAK_ED)
        plan = build_plan(order, groups, base)
        print(f'L01 W{WAVE_FROM}–W{WAVE_TO} 地面怪 ×{FACTOR}（基线 = 现值）')
        for w, rid, row, ground, air, old, new, _ in plan:
            print(f'-- W{w} (roundId={rid}, 编组行={row})  EHP {old:,.2f} -> {new:,.2f} '
                  f'({100 * (new / old - 1):+.2f}%)  空中 {len(air)} 种不动')
            for i in ground:
                print(f"   {i} {base[i]['name']:<8} {base[i]['hp']:.6f} -> {round(base[i]['hp'] * FACTOR, 6):.6f}")
        tot0 = sum(p[5] for p in plan)
        tot1 = sum(p[6] for p in plan)
        print(f'\n合计 EHP {tot0:,.2f} -> {tot1:,.2f} ({100 * (tot1 / tot0 - 1):+.2f}%)，'
              f'写入 {sum(len(p[3]) for p in plan)} 行')

        if mode == 'verify':
            bad = []
            for w, rid, row, ground, air, old, new, _ in plan:
                for i in ground:
                    want = round(base[i]['hp'] * FACTOR, 6)
                    if abs(cur[i]['hp'] - want) > 1e-6:
                        bad.append(f'W{w} id={i} 期望 {want} 实为 {cur[i]["hp"]}')
                for i in air:
                    if abs(cur[i]['hp'] - base[i]['hp']) > 1e-9:
                        bad.append(f'W{w} 空中 id={i} 不应改动 实为 {cur[i]["hp"]}')
            if bad:
                print('❌ 校验失败：')
                for b in bad[:20]:
                    print('  ' + b)
                return 1
            print(f'✅ 校验通过：W{WAVE_FROM}–W{WAVE_TO} 地面 = 基线×{FACTOR}；空中未变')
        return 0

    assert mode == 'apply', f'未知模式 {mode}'
    plan = build_plan(order, groups, cur)

    if any(TAG in p[7] for p in plan):
        print(f'⏭ 已带标记 {TAG}，拒绝重复叠加（乘性改动不可重跑）')
        return 0

    for src, dst in ((L01 / 'EnemyData.xlsx', BAK_ED), (L01 / 'EnemyList.xlsx', BAK_EL)):
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f'备份 -> {dst.name}')

    wb = openpyxl.load_workbook(L01 / 'EnemyData.xlsx')
    ws = wb[wb.sheetnames[0]]
    h = heads(ws)
    for w, rid, row, ground, air, old, new, _ in plan:
        for i in ground:
            r = cur[i]['row']
            ws.cell(r, h['hp']).value = round(cur[i]['hp'] * FACTOR, 6)
            d = str(ws.cell(r, h['desc']).value or '')
            ws.cell(r, h['desc']).value = f'{d} | {TAG}: ground x{FACTOR} (W{w})'
    wb.save(L01 / 'EnemyData.xlsx')

    wb = openpyxl.load_workbook(L01 / 'EnemyList.xlsx')
    ws = wb['Sheet1']
    h = heads(ws)
    for w, rid, row, ground, air, old, new, desc in plan:
        parts = desc.split(' | ')
        if re.search(r'EHP=[\d.]+', parts[0]):
            parts[0] = re.sub(r'EHP=[\d.]+', f'EHP={new:.6f}', parts[0], count=1)
        ws.cell(row, h['desc']).value = ' | '.join(parts) + f' | {TAG}: ground x{FACTOR} (EHP={new:.6f})'
    wb.save(L01 / 'EnemyList.xlsx')

    print('已写入：')
    for w, rid, row, ground, air, old, new, _ in plan:
        print(f'  W{w}: {len(ground)} 个地面变体  EHP {old:,.2f} -> {new:,.2f}')
    print(f'备注已追加 {TAG}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
