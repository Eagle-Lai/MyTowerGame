#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L02 W6–W25 地面怪 hp ×1.10（2026-11-04 第 N 轮，用户口径「从第六波次开始地面都 +10%」）。

范围：L02 EnemyData 里 isFlying=0、且属于 W6–W25 的行（W6–W9 各 3 行、W10 3 行、
      W11–W24 各 4 行、W25 5 行，共 76 行）。
基线：当前表值（叠加），`.bak_20261104_before_ground10` 固定为本次改动前原值 → 幂等。
只动 hp；speed / armor / reward / 数量 / 波型 / 出怪顺序 一律不动。

用法：python _l02_ground_hp10_20261104.py values|apply|verify
"""
from __future__ import annotations

import pathlib
import shutil
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L02 = ROOT / 'Luban/Config/Datas/Levels/L02'
BAK = L02 / 'EnemyData.xlsx.bak_20261104_before_ground10'
FACTOR = 1.10
WAVE_FROM = 6
LIST_IDS = list(range(2006, 2021)) + [2401, 2402, 2403, 2404, 2405]


def heads(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def enemy(path):
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


def lists():
    ws = openpyxl.load_workbook(L02 / 'EnemyList.xlsx', data_only=True).worksheets[0]
    out = {}
    for r in ws.iter_rows(min_row=4, values_only=True):
        if r[1] is None:
            continue
        out[int(r[1])] = [int(x) for x in str(r[2]).split(',') if str(x).strip()]
    return out


def target_rows(en, wl):
    """W6 起每波用到的地面怪行（去重）。"""
    rows = {}
    for i, lid in enumerate(LIST_IDS, start=WAVE_FROM):
        for eid in wl[lid]:
            if en[eid]['fly'] == 0:
                rows[eid] = i
    return rows


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'
    base = enemy(BAK if BAK.exists() else (L02 / 'EnemyData.xlsx'))
    cur = enemy(L02 / 'EnemyData.xlsx')
    wl = lists()
    tgt = target_rows(base, wl)
    plan = {i: round(base[i]['hp'] * FACTOR, 6) for i in tgt}

    if mode == 'values':
        print(f'基线：{BAK.name if BAK.exists() else "当前表"}｜倍率 ×{FACTOR}｜范围 W{WAVE_FROM}–W25 地面\n')
        by_wave = {}
        for eid, w in tgt.items():
            by_wave.setdefault(w, []).append(eid)
        print(f"{'波':<5}{'地面行':>6}{'地面hp 现值':>14}{'改后':>13}{'变化':>7}")
        for w in sorted(by_wave):
            ids = by_wave[w]
            o = sum(base[i]['hp'] for i in ids)
            print(f"W{w:<4}{len(ids):>6}{o:>14.1f}{o * FACTOR:>13.1f}{FACTOR - 1:>7.0%}")
        to = sum(base[i]['hp'] for i in tgt)
        print(f"\n合计 {len(tgt)} 行：地面总 hp {to:,.0f} -> {to * FACTOR:,.0f}（×{FACTOR}）")
        return 0

    if mode == 'verify':
        assert BAK.exists(), '缺少 .bak 基线'
        bad = []
        for i in tgt:
            if abs(cur[i]['hp'] - plan[i]) > 1e-6:
                bad.append(f'id={i} 期望 {plan[i]} 实为 {cur[i]["hp"]}')
        for i in cur:
            if i not in plan and abs(cur[i]['hp'] - base[i]['hp']) > 1e-9:
                bad.append(f'id={i} 非目标行却被改动：{base[i]["hp"]} -> {cur[i]["hp"]}')
        if bad:
            print('❌ 校验失败：')
            for b in bad[:20]:
                print('  ' + b)
            return 1
        print(f'✅ 校验通过：{len(tgt)} 行地面 hp = 基线×{FACTOR}；'
              f'其余 {len(cur) - len(tgt)} 行（含全部空中）未改动')
        return 0

    assert mode == 'apply', f'未知模式 {mode}'
    if all(abs(cur[i]['hp'] - plan[i]) < 1e-6 for i in tgt):
        print('⏭ 已是目标值，未重复写入')
        return 0
    if not BAK.exists():
        shutil.copy2(L02 / 'EnemyData.xlsx', BAK)
        print('备份 ->', BAK.name)

    wb = openpyxl.load_workbook(L02 / 'EnemyData.xlsx')
    ws = wb[wb.sheetnames[0]]
    h = heads(ws)
    for i in tgt:
        ws.cell(cur[i]['row'], h['hp']).value = plan[i]
    wb.save(L02 / 'EnemyData.xlsx')
    print(f'已写入 {len(tgt)} 行地面 hp ×{FACTOR}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
