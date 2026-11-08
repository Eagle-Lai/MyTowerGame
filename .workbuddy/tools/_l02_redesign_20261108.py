#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L02 按《L02_重设计规格》整体改表（2026-11-08，第五轮）。

依据：Docs/L02_Rebalance_20261108/L02_重设计规格.md
  · 难度基准 = L01 零漏怪通关版 Λ 曲线（α=1.0）
  · 数量 = L01 同波同类 × 1.5（四舍五入）
  · 血量 = L01 同类型 hp × m_w（地面）/ × m_a（空中）
  · 单只 reward = L01 同类型 reward × 1.16
  · speed = L01 同类型 speed（两关统一）
  · 出怪间隔 = L01 同波间隔 ÷ 1.5；RoundData.rewardGold = L01 × 1.74；initialGold = 174
  · 地图 / 塔表 / 全局规则不动

出生序列重建：空中等距铺槽 + 地面按占比重采样（保证空中不相邻）

用法：python _l02_redesign_20261108.py values|apply|verify
"""
from __future__ import annotations

import json
import math
import pathlib
import shutil
import sys
from collections import Counter, defaultdict

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L02 = ROOT / 'Luban/Config/Datas/Levels/L02'
ART = ROOT / 'Artifacts/L01_ZeroLeak_20261103_1823/runtime-config.json'
DESIGN = ROOT / '.workbuddy/tools/_l02_design_rows.json'
BAK_TAG = 'bak_20261108_before_redesign'
DIGITS = 6


def open_book(p):
    with open(p, 'rb') as fh:
        return openpyxl.load_workbook(fh, data_only=True)


def heads(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def load_enemy(path):
    ws = open_book(path).worksheets[0]
    h = heads(ws)
    out = {}
    for r in range(4, ws.max_row + 1):
        eid = ws.cell(r, h['id']).value
        if eid is None:
            continue
        out[int(eid)] = dict(row=r, name=ws.cell(r, h['name']).value,
                             fly=int(ws.cell(r, h['isFlying']).value or 0))
    return out


def load_lists(path):
    ws = open_book(path).worksheets[0]
    out = {}
    for r in range(4, ws.max_row + 1):
        lid = ws.cell(r, 2).value
        if lid is None:
            continue
        out[int(lid)] = dict(row=r, ids=[int(x) for x in str(ws.cell(r, 3).value).split(',') if x.strip()],
                             interval=ws.cell(r, 5).value)
    return out


def round_ids():
    ws = open_book(L02 / 'SceneInfo.xlsx').worksheets[0]
    h = heads(ws)
    return [int(x) for x in str(ws.cell(4, h['RoundList']).value).split(',') if x.strip()]


def largest_remainder(counts: dict[int, int], total: int) -> dict[int, int]:
    src = sum(counts.values())
    exact = {k: v * total / src for k, v in counts.items()}
    base = {k: int(math.floor(v)) for k, v in exact.items()}
    left = total - sum(base.values())
    for k in sorted(exact, key=lambda k: (-(exact[k] - base[k]), -counts[k], k))[:left]:
        base[k] += 1
    return base


def resample(seq, targets):
    pos = defaultdict(list)
    for i, x in enumerate(seq):
        pos[x].append(i)
    emit = {i: 0 for i in range(len(seq))}
    for eid, t in targets.items():
        plist = pos[eid]
        c = len(plist)
        for k in range(1, t + 1):
            occ = min(c, max(1, math.ceil(k * c / t)))
            emit[plist[occ - 1]] += 1
    out = []
    for i, x in enumerate(seq):
        out.extend([x] * emit[i])
    assert len(out) == sum(targets.values())
    return out


def build_sequence(template, targets_g, targets_a, enemy):
    """template: 当前出生序列（只用于地面顺序）；targets_*: id → 新数量"""
    ground_tpl = [x for x in template if not enemy[x]['fly']]
    ground = resample(ground_tpl, targets_g) if targets_g else []
    na = sum(targets_a.values())
    total = len(ground) + na
    if na == 0:
        return ground
    assert total / na >= 2, '空中槽位间距 <2'
    slots = [int(math.floor((k - 0.5) * total / na)) for k in range(1, na + 1)]
    assert len(set(slots)) == na
    air_seq = []
    for eid, c in targets_a.items():
        air_seq += [eid] * c
    # 空中按原顺序循环铺，保持种类占比
    air_seq = sorted(air_seq, key=lambda e: e)
    out, gi, ai = [], 0, 0
    sset = set(slots)
    for p in range(total):
        if p in sset:
            out.append(air_seq[ai]); ai += 1
        else:
            out.append(ground[gi]); gi += 1
    assert gi == len(ground) and ai == len(air_seq)
    assert not any(enemy[out[i]]['fly'] and enemy[out[i - 1]]['fly'] for i in range(1, len(out)))
    return out


def l01_ref():
    import csv
    d = json.load(open(ART, encoding='utf-8'))
    out = []
    for rd in d['rounds']:
        eps = []
        for g in rd['groups']:
            for e in g['enemies']:
                eps.append(dict(name=e['Name'], count=e['count'], hp=e['Hp'], speed=e['Speed'],
                                reward=e['Reward'], fly=bool(e['IsFlying'])))
        N = sum(e['count'] for e in eps)
        ivl = rd['groups'][0]['SpawnIntervalMs'] / 1000.0
        vg = [e['speed'] for e in eps if not e['fly']]
        va = [e['speed'] for e in eps if e['fly']]
        out.append(dict(eps=eps, N=N, ivl=ivl,
                        VG=(sum(vg)/len(vg) if vg else 1.0),
                        VA=(sum(va)/len(va) if va else 1.0),
                        ehp=sum(e['count']*e['hp'] for e in eps),
                        bonus=rd['RewardGold'], wt=rd['WaveType']))
    return out


def plan():
    ref = l01_ref()
    rl = round_ids()
    enemy = load_enemy(L02 / 'EnemyData.xlsx')
    lists = load_lists(L02 / 'EnemyList.xlsx')
    Sg1, Da1, L1 = 1437.0, 2997.0, 41
    Sg2, Da2, L2 = 2603.0, 3520.0, 70
    waves = []
    for i, rid in enumerate(rl):
        r = ref[i]
        cur = lists[rid]['ids']
        name2id = {}
        for e in cur:
            name2id.setdefault(enemy[e]['name'], e)
        # 目标数量（按类型 ×1.5）
        tg, ta = {}, {}
        hpL01, spdL01, rwL01 = {}, {}, {}
        for e in r['eps']:
            eid = name2id[e['name']]
            c = round(e['count'] * 1.5)
            if c <= 0:
                continue
            (ta if enemy[eid]['fly'] else tg)[eid] = c
            hpL01[eid], spdL01[eid], rwL01[eid] = e['hp'], e['speed'], e['reward']
        N2 = sum(tg.values()) + sum(ta.values())
        Tw = N2 * (r['ivl'] / 1.5) + L2 / r['VG']
        # L01 基准 Λ
        lam_w = Sg1 * (r['N'] * r['ivl'] + L1 / r['VG']) / r['ehp']
        ehp_target = Sg2 * Tw / lam_w
        # 空中单独定标
        air_hp = None
        if ta:
            h_air_l01 = max(e['hp'] for e in r['eps'] if e['fly'])
            lam_a = (Da1 / r['VA']) / h_air_l01
            air_hp = (Da2 / r['VA']) / lam_a
        air_ehp = sum(ta.values()) * (air_hp or 0)
        ground_ehp = ehp_target - air_ehp
        base_ground = sum(tg[e] * hpL01[e] for e in tg)
        m = ground_ehp / base_ground
        hp_plan, rw_plan, spd_plan = {}, {}, {}
        for e in tg:
            hp_plan[e] = round(hpL01[e] * m, DIGITS)
        for e in ta:
            hp_plan[e] = round(air_hp, DIGITS)
        for e in list(tg) + list(ta):
            rw_plan[e] = round(rwL01[e] * 1.16, DIGITS)
            spd_plan[e] = round(spdL01[e], DIGITS)
        seq = build_sequence(cur, tg, ta, enemy)
        waves.append(dict(w=i + 1, rid=rid, row=lists[rid]['row'], new=seq, old=cur,
                          hp=hp_plan, rw=rw_plan, spd=spd_plan,
                          interval=round(r['ivl'] / 1.5 * 1000, 3),
                          bonus=round(r['bonus'] * 1.74, 3),
                          ng=sum(tg.values()), na=sum(ta.values()), m=m, air_hp=air_hp,
                          ehp_target=ehp_target, Tw=Tw))
    return waves, enemy


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'
    waves, enemy = plan()
    total = sum(len(w['new']) for w in waves)
    gold = 174 + sum(w['bonus'] for w in waves) + sum(
        sum(c * enemy[e]['fly'] for e, c in Counter(w['new']).items()) * 0 for w in waves)

    if mode == 'values':
        print(f'{"波":<4}{"地":>6}{"空":>5}{"合计":>6}{"间隔ms":>8}{"EHP目标":>11}{"地血倍":>7}{"空血":>8}{"奖励":>7}')
        for w in waves:
            print(f"W{w['w']:<3}{w['ng']:>6}{w['na']:>5}{len(w['new']):>6}{w['interval']:>8.1f}"
                  f"{w['ehp_target']:>11,.0f}{w['m']:>7.2f}{(w['air_hp'] or 0):>8.0f}{w['bonus']:>7.0f}")
        print(f"\n合计 {total:,} 只（现 {sum(len(w['old']) for w in waves):,}）｜EHP {sum(w['ehp_target'] for w in waves):,.0f}")
        return 0

    if mode == 'verify':
        cur = load_lists(L02 / 'EnemyList.xlsx')
        en = load_enemy(L02 / 'EnemyData.xlsx')
        bad = []
        for w in waves:
            got = cur[w['rid']]['ids']
            if Counter(got) != Counter(w['new']):
                bad.append(f"list={w['rid']} 多重集合不符")
            if abs(float(cur[w['rid']]['interval']) - w['interval']) > 1e-6:
                bad.append(f"list={w['rid']} 间隔 {cur[w['rid']]['interval']} != {w['interval']}")
            if any(en[got[i]]['fly'] and en[got[i - 1]]['fly'] for i in range(1, len(got))):
                bad.append(f"list={w['rid']} 空中相邻")
        ws = open_book(L02 / 'EnemyData.xlsx').worksheets[0]
        h = heads(ws)
        for r in range(4, ws.max_row + 1):
            eid = ws.cell(r, h['id']).value
            if eid is None:
                continue
            eid = int(eid)
            for w in waves:
                if eid in w['hp']:
                    if abs(float(ws.cell(r, h['hp']).value) - w['hp'][eid]) > 1e-6:
                        bad.append(f'id={eid} hp 不符')
                    if abs(float(ws.cell(r, h['reward']).value) - w['rw'][eid]) > 1e-9:
                        bad.append(f'id={eid} reward 不符')
                    if abs(float(ws.cell(r, h['speed']).value) - w['spd'][eid]) > 1e-6:
                        bad.append(f'id={eid} speed 不符')
        if bad:
            print('❌ 校验失败：')
            for b in bad[:20]:
                print('  ' + b)
            return 1
        print(f'✅ 校验通过：25 波数量/间隔、全部 hp/reward/speed 与规格一致，空中无相邻')
        return 0

    assert mode == 'apply', f'未知模式 {mode}'
    # 备份
    for f in ('EnemyData.xlsx', 'EnemyList.xlsx', 'RoundData.xlsx', 'SceneInfo.xlsx'):
        b = L02 / f'{f}.{BAK_TAG}'
        if not b.exists():
            shutil.copy2(L02 / f, b)
            print('备份 ->', b.name)
    # EnemyData
    wb = openpyxl.load_workbook(L02 / 'EnemyData.xlsx')
    ws = wb[wb.sheetnames[0]]
    h = heads(ws)
    idx = {int(ws.cell(r, h['id']).value): r for r in range(4, ws.max_row + 1)
           if ws.cell(r, h['id']).value is not None}
    for w in waves:
        for eid, hp in w['hp'].items():
            ws.cell(idx[eid], h['hp']).value = hp
            ws.cell(idx[eid], h['reward']).value = w['rw'][eid]
            ws.cell(idx[eid], h['speed']).value = w['spd'][eid]
    wb.save(L02 / 'EnemyData.xlsx')
    print(f'EnemyData：{len(idx)} 行（hp/reward/speed）')

    # EnemyList
    wb = openpyxl.load_workbook(L02 / 'EnemyList.xlsx')
    ws = wb[wb.sheetnames[0]]
    h = heads(ws)
    for w in waves:
        ws.cell(w['row'], h['EnemyIndexs']).value = ','.join(str(x) for x in w['new'])
        ws.cell(w['row'], h['enemyInterval']).value = w['interval']
    wb.save(L02 / 'EnemyList.xlsx')
    print(f'EnemyList：{len(waves)} 组')

    # RoundData
    wb = openpyxl.load_workbook(L02 / 'RoundData.xlsx')
    ws = wb[wb.sheetnames[0]]
    h = heads(ws)
    row_of = {}
    for r in range(4, ws.max_row + 1):
        if ws.cell(r, h['id']).value is not None:
            row_of[int(ws.cell(r, h['id']).value)] = r
    for w in waves:
        ws.cell(row_of[w['rid']], h['rewardGold']).value = int(round(w['bonus']))
    wb.save(L02 / 'RoundData.xlsx')
    print(f'RoundData：{len(waves)} 行 rewardGold')

    # SceneInfo
    wb = openpyxl.load_workbook(L02 / 'SceneInfo.xlsx')
    ws = wb[wb.sheetnames[0]]
    h = heads(ws)
    ws.cell(4, h['initialGold']).value = 174
    wb.save(L02 / 'SceneInfo.xlsx')
    print('SceneInfo：initialGold=174')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
