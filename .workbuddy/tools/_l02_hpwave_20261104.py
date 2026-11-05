#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性手工改表（L02 专用，2026-11-04 口径）。

需求（用户在 2026-11-04 明确）：
  · W6 – W20：按波型加成 —— 普通波(waveType=1) 全部怪物 hp ×1.20；困难波(waveType=2) 全部怪物 hp ×1.10
  · W21 – W25：只加地面怪物 hp ×1.10（空中 Bat 不动，不区分波型）
  · W1 – W5：完全不动（含困难波 W5）
  · 只动 EnemyData.hp；speed / armor / reward / 数量 / 间隔 / 波次奖励 / 波型 一律不动
  · 基线 = 当前表值（在现值上乘），不回溯历史基线

用法：
  python _l02_hpwave_20261104.py values   # 干跑，只打印（只读）
  python _l02_hpwave_20261104.py apply    # 备份 + 写盘
  python _l02_hpwave_20261104.py verify   # 只读校验
"""
from __future__ import annotations

import pathlib
import re
import shutil
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L02 = ROOT / 'Luban/Config/Datas/Levels/L02'
TAG = 'l02hpwave-20261104'
BAK_ED = L02 / 'EnemyData.xlsx.bak_20261104_before_hpwave'
BAK_EL = L02 / 'EnemyList.xlsx.bak_20261104_before_hpwave'

NORMAL_FACTOR = 1.20      # 普通波：所有怪物
HARD_FACTOR = 1.10        # 困难波：所有怪物
LATE_GROUND_FACTOR = 1.10  # W21+：仅地面怪物
TYPE_RANGE = (6, 20)      # 按波型加成的波次区间
LATE_FROM = 21            # 从这一波起改「只加地面」


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
        out[int(rid)] = dict(ids=[int(x) for x in str(ws.cell(r, h['EnemyIndexs']).value).split(',')
                                  if str(x).strip()],
                             wave_type=int(ws.cell(r, h['waveType']).value or 0),
                             name=str(ws.cell(r, h['name']).value or ''))
    return out


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
                             fly=int(ws.cell(r, h['isFlying']).value or 0))
    return h, out


def factor_of(wave: int, wave_type: int, fly: int) -> float:
    if TYPE_RANGE[0] <= wave <= TYPE_RANGE[1]:
        return HARD_FACTOR if wave_type == 2 else NORMAL_FACTOR
    if wave >= LATE_FROM:
        return 1.0 if fly else LATE_GROUND_FACTOR
    return 1.0


def load_all():
    wb_si = openpyxl.load_workbook(L02 / 'SceneInfo.xlsx', data_only=True)
    order = wave_order(wb_si[wb_si.sheetnames[0]])
    assert len(order) == 25, f'RoundList 应 25 波，实为 {len(order)}'

    wb_rd = openpyxl.load_workbook(L02 / 'RoundData.xlsx', data_only=True)
    rounds = read_rounds(wb_rd[wb_rd.sheetnames[0]])

    wb_el = openpyxl.load_workbook(L02 / 'EnemyList.xlsx', data_only=True)
    _, elists = read_enemylist(wb_el[wb_el.sheetnames[0]])

    wb_ed = openpyxl.load_workbook(L02 / 'EnemyData.xlsx', data_only=True)
    _, enemy = read_enemy(wb_ed[wb_ed.sheetnames[0]])

    waves = {}
    for w, rid in enumerate(order, 1):
        rd = rounds[rid]
        lid = rd['ids'][0]
        waves[w] = dict(rid=rid, lid=lid, wt=rd['wave_type'],
                        row=elists[lid]['row'], ids=elists[lid]['ids'], desc=elists[lid]['desc'])
    return waves, enemy


def build_plan(waves, enemy):
    rows, problems = [], []
    owner = {}
    for w, rec in waves.items():
        for eid in rec['ids']:
            owner.setdefault(eid, set()).add(w)
    for eid, ws_ in owner.items():
        if len(ws_) > 1:
            problems.append(f'id={eid} 被多波共用：{sorted(ws_)}')

    for w in sorted(waves):
        rec = waves[w]
        for eid in sorted(set(rec['ids'])):
            e = enemy[eid]
            f = factor_of(w, rec['wt'], e['fly'])
            if f == 1.0:
                continue
            rows.append(dict(w=w, wt=rec['wt'], eid=eid, name=e['name'], row=e['row'],
                             fly=e['fly'], f=f, old=e['hp'], new=round(e['hp'] * f, 6)))
    return rows, problems


def ehp(ids, enemy, override=None):
    override = override or {}
    return sum(override.get(i, enemy[i]['hp']) / (1 - enemy[i]['armor']) for i in ids)


def report(waves, enemy, rows):
    by_wave = {}
    for r in rows:
        by_wave.setdefault(r['w'], {})[r['eid']] = r['new']
    print('波  型  倍率  改行  地面hp 基线->目标        空中hp 基线->目标         EHP 基线->目标')
    t = [0.0] * 6
    for w in sorted(waves):
        rec = waves[w]
        ov = by_wave.get(w, {})
        g0 = sum(enemy[i]['hp'] for i in rec['ids'] if not enemy[i]['fly'])
        g1 = sum(ov.get(i, enemy[i]['hp']) for i in rec['ids'] if not enemy[i]['fly'])
        a0 = sum(enemy[i]['hp'] for i in rec['ids'] if enemy[i]['fly'])
        a1 = sum(ov.get(i, enemy[i]['hp']) for i in rec['ids'] if enemy[i]['fly'])
        e0 = ehp(rec['ids'], enemy)
        e1 = ehp(rec['ids'], enemy, ov)
        for k, v in enumerate((g0, g1, a0, a1, e0, e1)):
            t[k] += v
        factors = sorted({r['f'] for r in rows if r['w'] == w}) or [1.0]
        print(f'W{w:<3}{rec["wt"]:<3}{str(factors):<8}{len(ov):<5}'
              f'{g0:>10.1f} -> {g1:>10.1f}   {a0:>10.1f} -> {a1:>10.1f}   {e0:>10.1f} -> {e1:>10.1f}')
    print(f'\n合计：地面 {t[0]:.1f} -> {t[1]:.1f} (×{t[1]/t[0]:.4f})；'
          f'空中 {t[2]:.1f} -> {t[3]:.1f} (×{t[3]/t[2]:.4f})；'
          f'EHP {t[4]:.1f} -> {t[5]:.1f} (×{t[5]/t[4]:.4f})')
    print(f'改动行数：{len(rows)}（地面 {sum(1 for r in rows if not r["fly"])} / '
          f'空中 {sum(1 for r in rows if r["fly"])}）')


def load_base_enemy():
    """基线固定为「改动前原值」：优先读本次 .bak，避免重复 apply 时越乘越高。"""
    src = BAK_ED if BAK_ED.exists() else (L02 / 'EnemyData.xlsx')
    with open(src, 'rb') as fh:          # .bak_* 后缀 openpyxl 不认，走文件句柄
        _, base = read_enemy(openpyxl.load_workbook(fh, data_only=True)['Sheet'])
    return base, src


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'
    waves, enemy_cur = load_all()
    enemy, src = load_base_enemy()
    assert len(enemy) == len(enemy_cur), '基线与当前表行数不一致，先人工核对'
    if src == BAK_ED:
        print(f'基线：{BAK_ED.name}（幂等；重复 apply 不会叠加）')
    rows, problems = build_plan(waves, enemy)

    if mode == 'values':
        report(waves, enemy, rows)
        if problems:
            print('\n⚠ 结构异常：')
            for p in problems:
                print('  ' + p)
        print('\n改动明细：')
        for r in rows:
            print(f'  W{r["w"]:<3}{"空" if r["fly"] else "地"} {r["name"]:<9}{r["eid"]:<9}'
                  f'×{r["f"]:<5}{r["old"]:>14.6f} -> {r["new"]:.6f}')
        return 0

    if mode == 'verify':
        assert BAK_ED.exists(), '缺少 .bak 基线'
        tmp = ROOT / '.workbuddy/tools/__pycache__/verify_l02_20261104.xlsx'
        tmp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BAK_ED, tmp)
        wb0 = openpyxl.load_workbook(tmp, data_only=True)
        _, base = read_enemy(wb0[wb0.sheetnames[0]])
        bad = []
        for r in rows:
            exp = round(base[r['eid']]['hp'] * r['f'], 6)
            cur = float(enemy_cur[r['eid']]['hp'])
            if abs(cur - exp) > 1e-6:
                bad.append(f'id={r["eid"]} W{r["w"]} 期望 {exp} 实为 {cur}')
        planned = {r['eid'] for r in rows}
        for eid, e in enemy_cur.items():
            if eid not in planned and abs(e['hp'] - base[eid]['hp']) > 1e-9:
                bad.append(f'id={eid} 未列入计划却被改动：{base[eid]["hp"]} -> {e["hp"]}')
        # 其它列(非 hp) 必须零变化
        wb_cur = openpyxl.load_workbook(L02 / 'EnemyData.xlsx', data_only=True)
        wb_old = openpyxl.load_workbook(tmp, data_only=True)
        s0, s1 = wb_old[wb_old.sheetnames[0]], wb_cur[wb_cur.sheetnames[0]]
        h = heads(s1)
        hp_col = h['hp']
        for rr in range(4, s1.max_row + 1):
            for cc in range(1, s1.max_column + 1):
                if cc == hp_col:
                    continue
                if s0.cell(rr, cc).value != s1.cell(rr, cc).value:
                    bad.append(f'第{rr}行 第{cc}列 非 hp 字段被改动：'
                               f'{s0.cell(rr, cc).value!r} -> {s1.cell(rr, cc).value!r}')
        if bad:
            print('❌ 校验失败：')
            for b in bad[:20]:
                print('  ' + b)
            return 1
        print(f'✅ 校验通过：{len(rows)} 行按波型倍率改动（地面 '
              f'{sum(1 for r in rows if not r["fly"])} / 空中 {sum(1 for r in rows if r["fly"])}）；'
              f'其余 {len(enemy) - len(rows)} 行 hp 未动；非 hp 列零改动')
        return 0

    assert mode == 'apply', f'未知模式 {mode}'
    if all(abs(float(enemy_cur[r['eid']]['hp']) - r['new']) < 1e-6 for r in rows):
        print('⏭ 已是目标值，未重复写入')
        return 0

    for src, dst in ((L02 / 'EnemyData.xlsx', BAK_ED), (L02 / 'EnemyList.xlsx', BAK_EL)):
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f'备份 -> {dst.name}')

    wb_ed = openpyxl.load_workbook(L02 / 'EnemyData.xlsx')
    ws_ed = wb_ed[wb_ed.sheetnames[0]]
    h_ed = heads(ws_ed)
    for r in rows:
        ws_ed.cell(r['row'], h_ed['hp']).value = r['new']
    wb_ed.save(L02 / 'EnemyData.xlsx')
    print(f'已写入 EnemyData {len(rows)} 行 hp（地面 '
          f'{sum(1 for r in rows if not r["fly"])} / 空中 {sum(1 for r in rows if r["fly"])}）')

    # 备注打标（仅 W6-W25，便于回溯；不影响玩法）
    _, enemy_now = read_enemy(openpyxl.load_workbook(L02 / 'EnemyData.xlsx', data_only=True)['Sheet'])
    wb_el = openpyxl.load_workbook(L02 / 'EnemyList.xlsx')
    ws_el = wb_el[wb_el.sheetnames[0]]
    h_el, _ = read_enemylist(ws_el)
    n = 0
    for w in sorted(waves):
        if w < TYPE_RANGE[0]:
            continue
        rec = waves[w]
        e_ = ehp(rec['ids'], enemy_now)
        desc = re.sub(rf'\s*\|\s*{TAG}:[^|]*$', '', rec['desc']).rstrip()
        note = ('all x1.20 (normal wave)' if rec['wt'] != 2 else 'all x1.10 (hard wave)') \
            if w <= TYPE_RANGE[1] else 'ground x1.10 (air untouched)'
        ws_el.cell(rec['row'], h_el['desc']).value = f'{desc} | {TAG}: {note}; EHP={e_:.6f}'
        n += 1
    wb_el.save(L02 / 'EnemyList.xlsx')
    print(f'已写入 EnemyList {n} 条备注')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
