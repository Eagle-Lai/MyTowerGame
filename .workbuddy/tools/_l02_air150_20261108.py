#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L02 W5–W25 只加空中怪数量 ×1.5（2026-11-08 第四轮），其余数值不变。

用户口径（本轮当次确认）：
  · 范围：L02 第 5 波次（含）–第 25 波次，**仅 `isFlying != 0` 的怪物**
  · 数量：每波 `floor(空中现数 × 1.5)`（**向下取整**）
  · 金币持平：每波空中行 `reward × (旧空中数 / 新空中数)`，使**每波击杀金币精确等于改前值**
  · 其余一律不动：地面怪的数量与相对顺序、`hp`、`enemyInterval`、`RoundData.rewardGold`、
    其它关卡、W1–W4
  · 空中怪不相邻（AGENTS.md 铁律）：空中按等距铺槽重建，地面序列原样填剩余槽位

基线：EnemyList.xlsx.bak_20261108_before_air150 / EnemyData.xlsx.bak_20261108_before_air_gold

用法：python _l02_air150_20261108.py values|apply|verify
"""
from __future__ import annotations

import math
import pathlib
import shutil
import sys
from collections import Counter

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L02 = ROOT / 'Luban/Config/Datas/Levels/L02'
LIST = L02 / 'EnemyList.xlsx'
ENEMY = L02 / 'EnemyData.xlsx'
LIST_BAK = L02 / 'EnemyList.xlsx.bak_20261108_before_air150'
ENEMY_BAK = L02 / 'EnemyData.xlsx.bak_20261108_before_air_gold'
WAVE_FROM, WAVE_TO = 5, 25
AIR_FACTOR = 1.5
DIGITS = 6


def open_book(path):
    with open(path, 'rb') as fh:
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
        out[int(eid)] = dict(row=r, hp=float(ws.cell(r, h['hp']).value),
                             reward=float(ws.cell(r, h['reward']).value),
                             fly=int(ws.cell(r, h['isFlying']).value or 0),
                             name=ws.cell(r, h['name']).value)
    return out


def load_lists(path):
    ws = open_book(path).worksheets[0]
    out = {}
    for r in range(4, ws.max_row + 1):
        lid = ws.cell(r, 2).value
        if lid is None:
            continue
        out[int(lid)] = dict(row=r, ids=[int(x) for x in str(ws.cell(r, 3).value).split(',') if x.strip()],
                             enemy_interval=ws.cell(r, 5).value)
    return out


def round_ids():
    ws = open_book(L02 / 'SceneInfo.xlsx').worksheets[0]
    h = heads(ws)
    return [int(x) for x in str(ws.cell(4, h['RoundList']).value).split(',') if x.strip()]


def build(seq, enemy):
    """空中等距铺槽 + 地面原序填充；地面数量与相对顺序绝对不变。"""
    air = [x for x in seq if enemy[x]['fly']]
    ground = [x for x in seq if not enemy[x]['fly']]
    na_new = int(math.floor(len(air) * AIR_FACTOR))
    total = len(ground) + na_new
    assert na_new >= 1 and total / na_new >= 2, '空中槽位间距不足 2，无法满足不相邻'
    air_pos = [int(math.floor((k - 0.5) * total / na_new)) for k in range(1, na_new + 1)]
    assert len(set(air_pos)) == na_new, '空中槽位冲突'
    # 空中的种类构成按原占比（同种同 id，直接按原顺序循环展开）
    air_new = [air[i % len(air)] for i in range(na_new)]
    out, gi = [], 0
    air_set = set(air_pos)
    for pos in range(total):
        if pos in air_set:
            out.append(air_new.pop(0))
        else:
            out.append(ground[gi]); gi += 1
    assert gi == len(ground) and not air_new
    assert not any(enemy[out[i]]['fly'] and enemy[out[i - 1]]['fly'] for i in range(1, len(out)))
    return out, len(air), na_new


def plan():
    rl = round_ids()
    old = load_lists(LIST_BAK if LIST_BAK.exists() else LIST)
    base_enemy = load_enemy(ENEMY_BAK if ENEMY_BAK.exists() else ENEMY)
    waves, reward_plan = [], {}
    for wave in range(WAVE_FROM, WAVE_TO + 1):
        lid = rl[wave - 1]
        seq = old[lid]['ids']
        new_seq, na_old, na_new = build(seq, base_enemy)
        air_ids = sorted({e for e in seq if base_enemy[e]['fly']})
        # 每波空中行 reward 按 旧数/新数 压缩 → 该波空中金币精确不变
        factor = na_old / na_new
        for e in air_ids:
            reward_plan[e] = round(base_enemy[e]['reward'] * factor, DIGITS)
        waves.append(dict(wave=wave, lid=lid, row=old[lid]['row'], old=seq, new=new_seq,
                          na_old=na_old, na_new=na_new, air_ids=air_ids, factor=factor,
                          enemy_interval=old[lid]['enemy_interval'],
                          gold_before=sum(base_enemy[e]['reward'] for e in seq if base_enemy[e]['fly']),
                          gold_after=sum(reward_plan[e] for e in new_seq if base_enemy[e]['fly'])))
    return waves, reward_plan, base_enemy


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'
    waves, reward_plan, base_enemy = plan()
    all_ids = sorted(reward_plan)   # 空中行 = 每波 1 行

    if mode == 'values':
        print(f'L02 W{WAVE_FROM}–W{WAVE_TO}｜仅空中 ×{AIR_FACTOR}（向下取整）＋空中 reward 压缩保金币持平\n')
        print(f"{'波':<4}{'空中现':>7}{'空中新':>7}{'总怪现':>8}{'总怪新':>8}{'空中占比':>9}{'reward系数':>11}{'空中金币现':>10}{'改后':>8}")
        ta0 = ta1 = 0
        for w in waves:
            ta0 += w['na_old']; ta1 += w['na_new']
            e0 = w['air_ids'][0]
            print(f"W{w['wave']:<3}{w['na_old']:>7}{w['na_new']:>7}{len(w['old']):>8}{len(w['new']):>8}"
                  f"{w['na_new'] / len(w['new']):>8.1%}{w['factor']:>11.4f}"
                  f"{w['gold_before']:>10.4f}{w['gold_after']:>8.4f}")
        print(f'\n空中合计 {ta0:,} -> {ta1:,}（+{ta1 - ta0:,}，×{ta1 / ta0:.4f}）')
        print(f'总怪数 {sum(len(w["old"]) for w in waves):,} -> {sum(len(w["new"]) for w in waves):,}')
        ta = sum(sum(base_enemy[e]['hp'] for e in w['old'] if base_enemy[e]['fly']) for w in waves)
        tb = sum(sum(base_enemy[e]['hp'] for e in w['new'] if base_enemy[e]['fly']) for w in waves)
        print(f'空中 EHP {ta:,.0f} -> {tb:,.0f}（+{tb / ta - 1:.1%}，因空中只数变多，hp 值本身未动）')
        g0 = sum(w['gold_before'] for w in waves); g1 = sum(w['gold_after'] for w in waves)
        print(f'空中金币 {g0:,.4f} -> {g1:,.4f}（{(g1 / g0 - 1) * 100:+.4f}%）')
        print(f'涉及 reward 行数：{len(all_ids)}（{all_ids[0]}–{all_ids[-1]}，每波 1 行空中怪）')
        return 0

    if mode == 'verify':
        cur_lists = load_lists(LIST)
        cur_enemy = load_enemy(ENEMY)
        bad = []
        for w in waves:
            got = cur_lists[w['lid']]['ids']
            if len(got) != len(w['new']) or Counter(got) != Counter(w['new']):
                bad.append(f"list={w['lid']} 序列/数量不符（{len(got)} vs {len(w['new'])}）")
            # 地面子序列必须与原序列完全一致（数量与相对顺序都不许变）
            g_old = [x for x in w['old'] if not base_enemy[x]['fly']]
            g_new = [x for x in got if not base_enemy[x]['fly']]
            if g_old != g_new:
                bad.append(f"list={w['lid']} 地面序列被改动")
            if cur_lists[w['lid']]['enemy_interval'] != w['enemy_interval']:
                bad.append(f"list={w['lid']} enemyInterval 被改动")
            if any(cur_enemy[got[i]]['fly'] and cur_enemy[got[i - 1]]['fly'] for i in range(1, len(got))):
                bad.append(f"list={w['lid']} 出现空中相邻")
            g = sum(cur_enemy[e]['reward'] for e in got if cur_enemy[e]['fly'])
            if abs(g - w['gold_before']) > 0.01:
                bad.append(f"list={w['lid']} 空中金币 {g:.4f} != 改前 {w['gold_before']:.4f}")
        for e, v in reward_plan.items():
            if abs(cur_enemy[e]['reward'] - v) > 1e-9:
                bad.append(f'id={e} reward 期望 {v} 实为 {cur_enemy[e]["reward"]}')
        for e in cur_enemy:
            if abs(cur_enemy[e]['hp'] - base_enemy[e]['hp']) > 1e-9:
                bad.append(f'id={e} hp 被改动（本轮不允许）')
            if e not in reward_plan and abs(cur_enemy[e]['reward'] - base_enemy[e]['reward']) > 1e-9:
                bad.append(f'id={e} 非空中行 reward 被改动')
        untouched = [k for k in cur_lists if k not in {w['lid'] for w in waves}]
        old_lists = load_lists(LIST_BAK)
        for lid in untouched:
            if cur_lists[lid]['ids'] != old_lists[lid]['ids']:
                bad.append(f'list={lid} 不在范围却被改动')
        if bad:
            print('❌ 校验失败：')
            for b in bad[:20]:
                print('  ' + b)
            return 1
        print(f'✅ 校验通过：21 波空中 = floor(原×1.5)（{sum(w["na_new"] for w in waves):,} 只）、'
              f'地面序列与数量零改动、hp 全表未动、每波空中金币与改前一致；'
              f'{len(untouched)} 个非目标组未改动')
        return 0

    assert mode == 'apply', f'未知模式 {mode}'
    need_list = any(load_lists(LIST)[w['lid']]['ids'] != w['new'] for w in waves)
    if need_list:
        if not LIST_BAK.exists():
            shutil.copy2(LIST, LIST_BAK)
            print('备份 ->', LIST_BAK.name)
        wb = openpyxl.load_workbook(LIST)
        ws = wb[wb.sheetnames[0]]
        h = heads(ws)
        for w in waves:
            ws.cell(w['row'], h['EnemyIndexs']).value = ','.join(str(x) for x in w['new'])
        wb.save(LIST)
        print(f'已写入 EnemyList：{len(waves)} 组')
    else:
        print('⏭ EnemyList 已是目标值')

    cur_enemy = load_enemy(ENEMY)
    if any(abs(cur_enemy[e]['reward'] - v) > 1e-9 for e, v in reward_plan.items()):
        if not ENEMY_BAK.exists():
            shutil.copy2(ENEMY, ENEMY_BAK)
            print('备份 ->', ENEMY_BAK.name)
        wb = openpyxl.load_workbook(ENEMY)
        ws = wb[wb.sheetnames[0]]
        h = heads(ws)
        for e, v in reward_plan.items():
            ws.cell(cur_enemy[e]['row'], h['reward']).value = v
        wb.save(ENEMY)
        print(f'已写入 EnemyData.reward：{len(reward_plan)} 行（空中行压缩保金币持平）')
    else:
        print('⏭ reward 已是目标值')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
