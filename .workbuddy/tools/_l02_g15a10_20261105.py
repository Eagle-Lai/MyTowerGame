#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L02 W6–W25 地面 ×1.15、空中 ×1.10（2026-11-05，叠加在当前值上）。

用户口径：「从第六波次开始，地面怪物都继续增加 15% 的血量，空中怪物增加 10% 的血量」。
  · 地面：W6–W25 全部 isFlying=0 的行（76 行）
  · 空中：W6–W25 全部 isFlying=1 的行（20 行；**W5 的 13 只 Bat 不在「第六波起」范围内，未动**）
基线：`.bak_20261105_before_g15a10`（固定为本次改动前原值 → 幂等，重复 apply 不叠加）
只动 hp；speed / armor / reward / 数量 / 出怪顺序 / 波型 一律不动。

用法：python _l02_g15a10_20261105.py values|apply|verify
"""
from __future__ import annotations

import pathlib
import shutil
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L02 = ROOT / 'Luban/Config/Datas/Levels/L02'
BAK = L02 / 'EnemyData.xlsx.bak_20261105_before_g15a10'
G_FACTOR = 1.15
A_FACTOR = 1.10
WAVE_FROM = 6
LIST_IDS = list(range(2006, 2021)) + [2401, 2402, 2403, 2404, 2405]   # W6–W25


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


def wave_lists():
    ws = openpyxl.load_workbook(L02 / 'EnemyList.xlsx', data_only=True).worksheets[0]
    return {int(r[1]): [int(x) for x in str(r[2]).split(',') if str(x).strip()]
            for r in ws.iter_rows(min_row=4, values_only=True) if r[1] is not None}


def targets(en, wl):
    t = {}
    for w, lid in enumerate(LIST_IDS, start=WAVE_FROM):
        for eid in wl[lid]:
            t.setdefault(eid, w)
    return t


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'
    base = enemy(BAK if BAK.exists() else (L02 / 'EnemyData.xlsx'))
    cur = enemy(L02 / 'EnemyData.xlsx')
    wl = wave_lists()
    tgt = targets(base, wl)
    plan = {i: round(base[i]['hp'] * (A_FACTOR if base[i]['fly'] else G_FACTOR), 6) for i in tgt}
    g = [i for i in tgt if base[i]['fly'] == 0]
    a = [i for i in tgt if base[i]['fly'] == 1]

    if mode == 'values':
        print(f'基线：{BAK.name if BAK.exists() else "当前表"}｜W{WAVE_FROM}–W25｜'
              f'地面 ×{G_FACTOR}（{len(g)} 行）/ 空中 ×{A_FACTOR}（{len(a)} 行）\n')
        byw = {}
        for eid, w in tgt.items():
            byw.setdefault(w, []).append(eid)
        print(f"{'波':<5}{'地行':>5}{'空行':>5}{'地面hp 现值':>13}{'改后':>12}{'空中hp 现值':>13}{'改后':>12}")
        for w in sorted(byw):
            ids = byw[w]
            gs = [i for i in ids if base[i]['fly'] == 0]
            as_ = [i for i in ids if base[i]['fly'] == 1]
            g0 = sum(base[i]['hp'] for i in gs)
            a0 = sum(base[i]['hp'] for i in as_)
            print(f"W{w:<4}{len(gs):>5}{len(as_):>5}{g0:>13.1f}{g0 * G_FACTOR:>12.1f}"
                  f"{a0:>13.1f}{a0 * A_FACTOR:>12.1f}")
        G0 = sum(base[i]['hp'] for i in g); A0 = sum(base[i]['hp'] for i in a)
        print(f"\n合计：地面 {G0:,.0f} -> {G0 * G_FACTOR:,.0f}（×{G_FACTOR}）｜"
              f"空中 {A0:,.0f} -> {A0 * A_FACTOR:,.0f}（×{A_FACTOR}）")
        print('注：W5 的空中（id=6000045）属「第六波之前」，本轮未纳入。')
        return 0

    if mode == 'verify':
        assert BAK.exists(), '缺少 .bak 基线'
        bad = []
        for i in tgt:
            if abs(cur[i]['hp'] - plan[i]) > 1e-6:
                bad.append(f'id={i}（W{tgt[i]}）期望 {plan[i]} 实为 {cur[i]["hp"]}')
        for i in cur:
            if i not in plan and abs(cur[i]['hp'] - base[i]['hp']) > 1e-9:
                bad.append(f'id={i} 非目标行却被改动：{base[i]["hp"]} -> {cur[i]["hp"]}')
        if bad:
            print('❌ 校验失败：')
            for b in bad[:20]:
                print('  ' + b)
            return 1
        print(f'✅ 校验通过：地面 {len(g)} 行 = 基线×{G_FACTOR}、空中 {len(a)} 行 = 基线×{A_FACTOR}；'
              f'其余 {len(cur) - len(tgt)} 行（W1–W5 全部 + W5 空中）未改动')
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
    print(f'已写入：地面 {len(g)} 行 ×{G_FACTOR}、空中 {len(a)} 行 ×{A_FACTOR}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
