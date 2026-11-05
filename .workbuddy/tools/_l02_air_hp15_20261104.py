#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L02 全部空中怪 hp ×1.15（2026-11-04，用户口径「统一把空中血量都增加 15%」）。

范围：L02 的 EnemyData 里 isFlying=1 的全部行（W5–W25 每波一只 Bat，共 21 行）。
基线：本次 `.bak_20261104_before_air15`（幂等，重复 apply 不会叠加）。
只动 hp；speed / armor / reward / damageToPlayer / 数量 / 波型 一律不动。

用法：
  python _l02_air_hp15_20261104.py values|apply|verify
"""
from __future__ import annotations

import pathlib
import shutil
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L02 = ROOT / 'Luban/Config/Datas/Levels/L02'
BAK = L02 / 'EnemyData.xlsx.bak_20261104_before_air15'
FACTOR = 1.15
TAG = 'airhp15-20261104'


def heads(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def read(path):
    with open(path, 'rb') as fh:
        ws = openpyxl.load_workbook(fh, data_only=True).worksheets[0]
    h = heads(ws)
    out = {}
    for r in range(4, ws.max_row + 1):
        eid = ws.cell(r, h['id']).value
        if eid is None:
            continue
        out[int(eid)] = dict(row=r, hp=float(ws.cell(r, h['hp']).value),
                             fly=int(ws.cell(r, h['isFlying']).value or 0),
                             name=ws.cell(r, h['name']).value)
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'
    base = read(BAK if BAK.exists() else (L02 / 'EnemyData.xlsx'))
    cur = read(L02 / 'EnemyData.xlsx')
    air = [i for i in sorted(base) if base[i]['fly'] == 1]
    plan = {i: round(base[i]['hp'] * FACTOR, 6) for i in air}

    if mode == 'values':
        print(f'基线：{BAK.name if BAK.exists() else "当前表（无 .bak）"}')
        print(f'空中怪行数：{len(air)}（W5–W25 每波 1 只 Bat）\n')
        print(f"{'id':<9}{'怪':<6}{'旧hp':>10}{'新hp':>12}{'变化':>8}")
        for i in air:
            print(f"{i:<9}{base[i]['name']:<6}{base[i]['hp']:>10.3f}{plan[i]:>12.3f}{FACTOR - 1:>8.0%}")
        o = sum(base[i]['hp'] for i in air)
        print(f"\n空中总血量 {o:.1f} -> {sum(plan.values()):.1f}（×{sum(plan.values()) / o:.4f}）")
        return 0

    if mode == 'verify':
        assert BAK.exists(), '缺少 .bak 基线'
        bad = []
        for i in air:
            if abs(cur[i]['hp'] - plan[i]) > 1e-6:
                bad.append(f'id={i} 期望 {plan[i]} 实为 {cur[i]["hp"]}')
        for i in cur:
            if i not in plan and abs(cur[i]['hp'] - base[i]['hp']) > 1e-9:
                bad.append(f'id={i} 非空中行却被改动：{base[i]["hp"]} -> {cur[i]["hp"]}')
        if bad:
            print('❌ 校验失败：')
            for b in bad[:20]:
                print('  ' + b)
            return 1
        print(f'✅ 校验通过：{len(air)} 行空中 hp = 基线×{FACTOR}；'
              f'其余 {len(cur) - len(air)} 行（含地面）未改动')
        return 0

    assert mode == 'apply', f'未知模式 {mode}'
    if all(abs(cur[i]['hp'] - plan[i]) < 1e-6 for i in air):
        print('⏭ 已是目标值，未重复写入')
        return 0
    if not BAK.exists():
        shutil.copy2(L02 / 'EnemyData.xlsx', BAK)
        print('备份 ->', BAK.name)

    wb = openpyxl.load_workbook(L02 / 'EnemyData.xlsx')
    ws = wb[wb.sheetnames[0]]
    h = heads(ws)
    for i in air:
        ws.cell(cur[i]['row'], h['hp']).value = plan[i]
    wb.save(L02 / 'EnemyData.xlsx')
    print(f'已写入 {len(air)} 行空中 hp ×{FACTOR}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
