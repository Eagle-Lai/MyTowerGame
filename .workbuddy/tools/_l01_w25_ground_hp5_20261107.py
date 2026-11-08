#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性定点改表（2026-11-07 21:5x 用户口径，仅 L01 W25 地面第五轮）：

    第一关 W25（第 25 波）的地面怪血量 = 现值 ×0.95；空中怪不动。

范围与基线：
  - 目标 = W25 编组（roundId=405，编组行 28）引用的地面变体；空中 Bat 不动。
  - 基线 = 改动前现值（乘性），带幂等护栏：desc 含 TAG 即拒绝重跑。
  - 不动：数量（EnemyIndexs）、enemyInterval/interval、reward、armor、speed、isFlying、
    击杀奖励、波次奖励、其它 24 个波次、其它 29 关。

用法：
  python _l01_w25_ground_hp5_20261107.py values | apply | verify
"""
import pathlib
import re
import shutil
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L01 = ROOT / 'Luban/Config/Datas/Levels/L01'

WAVE = 25
FACTOR = 0.95
TAG = 'w25groundhp5-20261107'
BAK_ED = L01 / 'EnemyData.xlsx.bak_groundhpL-20261107'
BAK_EL = L01 / 'EnemyList.xlsx.bak_groundhpL-20261107'


def heads(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def wave_order():
    ws = openpyxl.load_workbook(L01 / 'SceneInfo.xlsx', data_only=True)['Sheet1']
    h = heads(ws)
    return [int(x) for x in str(ws.cell(4, h['RoundList']).value).split(',') if str(x).strip()]


def read_enemy(path):
    src = path
    if path.suffix != '.xlsx':
        tmp = ROOT / '.workbuddy/tools/__pycache__/bakcheck'
        tmp.mkdir(parents=True, exist_ok=True)
        src = tmp / ('EnemyData_' + path.name.replace('.', '_') + '.xlsx')
        shutil.copy2(path, src)
    wb = openpyxl.load_workbook(src, data_only=True)
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


def w_group():
    """返回 (EnemyList 行号, 编组 id, 出怪序列, desc)"""
    order = wave_order()
    rid = order[WAVE - 1]
    wb = openpyxl.load_workbook(L01 / 'EnemyList.xlsx', data_only=True)
    ws = wb['Sheet1']
    h = heads(ws)
    for r in range(4, ws.max_row + 1):
        lid = ws.cell(r, h['id']).value
        if lid is None or int(lid) != rid:
            continue
        seq = [int(x) for x in str(ws.cell(r, h['EnemyIndexs']).value).split(',') if str(x).strip()]
        desc = str(ws.cell(r, h['desc']).value or '')
        wb.close()
        return r, rid, seq, desc
    wb.close()
    raise SystemExit(f'找不到 W{WAVE}（roundId={rid}）编组')


def ehp_of(seq, enemy):
    return sum(enemy[i]['hp'] / (1 - enemy[i]['armor']) for i in seq)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'

    el_row, rid, seq, desc = w_group()
    cur = read_enemy(L01 / 'EnemyData.xlsx')
    base = read_enemy(BAK_ED) if (BAK_ED.exists() and mode == 'verify') else cur

    ground = sorted({i for i in seq if not cur[i]['fly']})
    plan = {i: (base[i]['hp'], round(base[i]['hp'] * FACTOR, 6)) for i in ground}

    old_ehp = ehp_of(seq, base)
    new_enemy = {**base, **{i: dict(base[i], hp=plan[i][1]) for i in ground}}
    new_ehp = ehp_of(seq, new_enemy)

    if mode in ('values', 'verify'):
        print(f'关卡 L01  W{WAVE}  roundId={rid}  编组行={el_row}  出怪 {len(seq)} 只')
        print('id | 怪 | 定位 | 旧 hp | 新 hp')
        for i in ground:
            print(f"{i} | {base[i]['name']:<8} | 地面 | {plan[i][0]:.6f} | {plan[i][1]:.6f}")
        air = sorted({i for i in seq if cur[i]['fly']})
        for i in air:
            print(f"{i} | {cur[i]['name']:<8} | 空中 | {cur[i]['hp']:.6f} | 不动")
        print(f'EHP: {old_ehp:,.6f} -> {new_ehp:,.6f} ({100 * (new_ehp / old_ehp - 1):+.3f}%)')
        if mode == 'verify':
            bad = [f"{i} 期望 {plan[i][1]} 实为 {cur[i]['hp']}" for i in ground
                   if abs(cur[i]['hp'] - plan[i][1]) > 1e-6]
            bad += [f"{i} 空中不应改动 实为 {cur[i]['hp']}" for i in air
                    if abs(cur[i]['hp'] - base[i]['hp']) > 1e-9]
            if bad:
                print('❌ 校验失败：')
                for b in bad:
                    print('  ' + b)
                return 1
            print(f'✅ 校验通过：W{WAVE} 地面 {len(ground)} 行 = 基线×{FACTOR}；空中 {len(air)} 行未变')
        return 0

    assert mode == 'apply', f'未知模式 {mode}'
    if TAG in desc:
        print(f'⏭ W{WAVE} 已带标记 {TAG}，拒绝重复叠加（乘性改动不可重跑）')
        return 0

    for src, dst in ((L01 / 'EnemyData.xlsx', BAK_ED), (L01 / 'EnemyList.xlsx', BAK_EL)):
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f'备份 -> {dst.name}')

    # 1) EnemyData.hp + 行内备注
    wb = openpyxl.load_workbook(L01 / 'EnemyData.xlsx')
    ws = wb[wb.sheetnames[0]]
    h = heads(ws)
    for i in ground:
        r = cur[i]['row']
        ws.cell(r, h['hp']).value = plan[i][1]
        d = str(ws.cell(r, h['desc']).value or '')
        ws.cell(r, h['desc']).value = f'{d} | {TAG}: ground x{FACTOR}'
    wb.save(L01 / 'EnemyData.xlsx')

    # 2) EnemyList 备注：只更新本波 EHP 汇总 + 追加 tag
    wb = openpyxl.load_workbook(L01 / 'EnemyList.xlsx')
    ws = wb['Sheet1']
    h = heads(ws)
    parts = desc.split(' | ')
    parts[0] = re.sub(r'EHP=[\d.]+', f'EHP={new_ehp:.6f}', parts[0], count=1)
    new_desc = ' | '.join(parts) + f' | {TAG}: ground x{FACTOR} (EHP={new_ehp:.6f})'
    ws.cell(el_row, h['desc']).value = new_desc
    wb.save(L01 / 'EnemyList.xlsx')

    print('已写入：')
    for i in ground:
        print(f"  {i} {base[i]['name']:<8} 地面  {plan[i][0]:.6f} -> {plan[i][1]:.6f}")
    print(f'EHP {old_ehp:,.6f} -> {new_ehp:,.6f} ({100 * (new_ehp / old_ehp - 1):+.3f}%)')
    print(f'备注已追加 {TAG}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
