#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性手工改表（L02 专用，2026-11-03 用户口径）。

需求：第二关「第 5 波(不含) → 第 25 波」的**地面怪物**血量，改成当前值的 134%（×1.34）。
  - 波次范围：W6..W25（含 W25），W1-W5 不动。
  - 只动地面单位（EnemyData.isFlying = 0）；飞行单位（Bat）一律不动。
  - 只动 hp 字段；speed / armor / reward / 数量 / 间隔 / 波次奖励全部不动。
  - 只动 L02 目录，其余 29 关一个字节不动。

★ 关键坑（沿用 _l01_gold_ground_hp_20261101.py 的教训）：
  1) RoundData.xlsx 的物理行顺序不是波次顺序（本例物理顺序 2001..2012、2401..2405、2013..2020），
     真实波次由 SceneInfo.RoundList 决定：1..20 → 2001..2020，21..25 → 2401..2405。
  2) 地面/空中看 EnemyData.isFlying，不看名字（Rat 是地面 BOSS）。
  3) 先按「波次→roundId→EnemyList→敌人 id」解析出真正上场的 id 集合，
     再回 EnemyData 校验每行 desc 里的 wave=N 与解析出的波次一致，避免跨波复用被漏改/多改。

用法：
  python _l02_groundhp134_20261103.py values   # 干跑，只打印目标值（只读）
  python _l02_groundhp134_20261103.py apply    # 备份 + 写盘
  python _l02_groundhp134_20261103.py verify   # 只读校验（对照 .bak 基线）

改完必须手动跑一次 Luban 导出才生效（Assets/ConfigJson + Assets/Gen 是导出产物，不许手改）。
"""
from __future__ import annotations

import pathlib
import re
import shutil
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L02 = ROOT / 'Luban/Config/Datas/Levels/L02'
TAG = 'l02groundhp-20261103'
FACTOR = 1.34
WAVE_FROM = 6          # 「第 5 波(不含)」
WAVE_TO = 25


def heads(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def wave_order(ws):
    """SceneInfo.RoundList 的 roundId 顺序 = 真实波次顺序（1..25）。"""
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
        ids = [int(x) for x in str(ws.cell(r, h['EnemyIndexs']).value).split(',') if str(x).strip()]
        out[int(rid)] = dict(row=r, list_ids=ids,
                             name=ws.cell(r, h['name']).value if 'name' in h else '')
    return h, out


def read_enemylist(ws):
    h = heads(ws)
    out = {}
    for r in range(4, ws.max_row + 1):
        lid = ws.cell(r, h['id']).value
        if lid is None:
            continue
        ids = [int(x) for x in str(ws.cell(r, h['EnemyIndexs']).value).split(',') if str(x).strip()]
        out[int(lid)] = dict(row=r, ids=ids, desc=str(ws.cell(r, h['desc']).value or ''))
    return h, out


def read_enemy(ws):
    h = heads(ws)
    out = {}
    for r in range(4, ws.max_row + 1):
        eid = ws.cell(r, h['id']).value
        if eid is None:
            continue
        out[int(eid)] = dict(
            row=r,
            name=ws.cell(r, h['name']).value,
            hp=float(ws.cell(r, h['hp']).value),
            armor=float(ws.cell(r, h['armor']).value or 0),
            fly=int(ws.cell(r, h['isFlying']).value or 0),
            desc=str(ws.cell(r, h['desc']).value or ''),
        )
    return h, out


def ehp_of(ids, enemy, override=None):
    """按上场 id 序列（含重复）累加 EHP；override={eid: new_hp} 用于试算改动后。"""
    override = override or {}
    return sum(override.get(i, enemy[i]['hp']) / (1 - enemy[i]['armor']) for i in ids)


def build_plan(enemy, waves):
    """{(wave): dict(list_id, ids, ground_ids, ehp_before)} + 待改行列表"""
    plan, rows, problems = {}, [], []
    for w in range(WAVE_FROM, WAVE_TO + 1):
        rec = waves[w]
        ids = rec['ids']
        for eid in set(ids):
            e = enemy[eid]
            m = re.search(r'wave=(\d+)', e['desc'])
            if m and int(m.group(1)) != w:
                problems.append(f'W{w} 引用 id={eid}，但该行 desc 写的是 wave={m.group(1)}')
        ground = sorted({i for i in ids if not enemy[i]['fly']})
        plan[w] = dict(row=rec['row'], ids=ids, ground=ground, ehp=ehp_of(ids, enemy))
        for eid in ground:
            e = enemy[eid]
            rows.append(dict(w=w, eid=eid, name=e['name'], row=e['row'],
                             old=e['hp'], new=round(e['hp'] * FACTOR, 6)))
    return plan, rows, problems


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'

    wb_si = openpyxl.load_workbook(L02 / 'SceneInfo.xlsx', data_only=True)
    ws_si = wb_si[wb_si.sheetnames[0]]
    order = [rid for rid in wave_order(ws_si)]
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

    # 波次 -> EnemyList 记录（roundId -> RoundData.EnemyIndexs[0] -> EnemyList 行）
    waves = {}
    for w, rid in enumerate(order, 1):
        lid = rounds[rid]['list_ids'][0]
        rec = dict(lid=lid, row=elists[lid]['row'], ids=elists[lid]['ids'],
                   desc=elists[lid]['desc'], rid=rid)
        waves[w] = rec

    plan, rows, problems = build_plan(enemy, waves)

    if mode == 'values':
        print(f'L02 地面单位 ×{FACTOR}：W{WAVE_FROM}..W{WAVE_TO}（{len(rows)} 行），'
              f'W1-W5 与飞行单位不动\n')
        print('波  roundId   EnemyList  地面行  旧 EHP           新 EHP')
        tot_o = tot_n = 0.0
        for w in range(WAVE_FROM, WAVE_TO + 1):
            p = plan[w]
            newhp = {r['eid']: r['new'] for r in rows if r['w'] == w}
            ehp_new = ehp_of(p['ids'], enemy, newhp)
            tot_o += p['ehp']
            tot_n += ehp_new
            print(f'W{w:<3}{waves[w]["rid"]:<9}{waves[w]["lid"]:<11}{len(p["ground"]):<8}'
                  f'{p["ehp"]:>15.4f} {ehp_new:>15.4f}')
        print(f'\n合计 EHP：{tot_o:.4f} -> {tot_n:.4f}  (×{tot_n / tot_o:.6f})')
        print(f'\n改动明细（{len(rows)} 行，id/名称/旧 → 新）：')
        for r in rows:
            print(f'  W{r["w"]:<3}{r["name"]:<10}{r["eid"]:<9}{r["old"]:>14.6f} -> {r["new"]:.6f}')
        if problems:
            print('\n⚠ 波次/desc 不一致（需人工确认）：')
            for p in problems:
                print('  ' + p)
        return 0

    bak_ed = L02 / 'EnemyData.xlsx.bak_20261103_before_groundhp134'
    bak_el = L02 / 'EnemyList.xlsx.bak_20261103_before_groundhp134'

    if mode == 'verify':
        assert bak_ed.exists(), '缺少 .bak 基线'
        tmp = ROOT / '.workbuddy/tools/__pycache__/bakcheck_l02'
        tmp.mkdir(parents=True, exist_ok=True)
        t = tmp / 'EnemyData.xlsx'
        shutil.copy2(bak_ed, t)
        wb = openpyxl.load_workbook(t, data_only=True)
        _, base = read_enemy(wb[wb.sheetnames[0]])
        bad = []
        for r in rows:
            cur = float(ws_ed.cell(r['row'], h_ed['hp']).value)
            if abs(cur - round(base[r['eid']]['hp'] * FACTOR, 6)) > 1e-6:
                bad.append(f'id={r["eid"]} W{r["w"]} 期望 {round(base[r["eid"]]["hp"]*FACTOR,6)} 实为 {cur}')
        # 未在计划内的行必须与基线一致
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
        print(f'✅ 校验通过：{len(rows)} 行 = 基线×{FACTOR}；其余 {len(enemy)-len(rows)} 行未改动')
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
    print(f'已写入 EnemyData {len(rows)} 行 hp')

    # EnemyList 备注：给 W6-W25 追加 EHP 标记（沿用历史 tag 习惯）
    _, enemy_now = read_enemy(openpyxl.load_workbook(L02 / 'EnemyData.xlsx', data_only=True)['Sheet'])
    for w in range(WAVE_FROM, WAVE_TO + 1):
        rec = waves[w]
        ehp = ehp_of(rec['ids'], enemy_now)
        desc = rec['desc']
        desc = re.sub(rf'\s*\|\s*{TAG}:[^|]*$', '', desc).rstrip()
        ws_el.cell(rec['row'], h_el['desc']).value = f'{desc} | {TAG}: ground x{FACTOR} (EHP={ehp:.6f})'
    wb_el.save(L02 / 'EnemyList.xlsx')
    print(f'已写入 EnemyList {WAVE_TO - WAVE_FROM + 1} 条备注')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
