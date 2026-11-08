#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L02 W5–W25 金币产出持平（2026-11-08，配合数量 ×1.2 / 血量 ×1.5）。

用户口径（本轮当次确认）：
  · 数量已 +20%，击杀金币不能跟着涨 → 压缩每只怪的 `reward`，把每波金币总量拉回改前值
  · 配平精度：**每波击杀金币总额精确等于改前值**（每波一个系数，怪种间相对报酬比例不变）
  · `RoundData.rewardGold`（波次通关奖励）**不动**；`hp` / `speed` / `armor` / 数量 / 顺序 一并不动

基线：EnemyData.xlsx.bak_20261108_before_hp150（改前 reward）+ EnemyList.xlsx.bak_20261108_before_count120（改前数量）
幂等：已在目标值则跳过写入。

用法：python _l02_gold_hold_20261108.py values|apply|verify
"""
from __future__ import annotations

import pathlib
import shutil
import sys
from collections import Counter

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L02 = ROOT / 'Luban/Config/Datas/Levels/L02'
LIST_BAK = L02 / 'EnemyList.xlsx.bak_20261108_before_count120'
ENEMY_BAK = L02 / 'EnemyData.xlsx.bak_20261108_before_hp150'
ENEMY_BAK2 = L02 / 'EnemyData.xlsx.bak_20261108_before_gold_hold'
WAVE_FROM, WAVE_TO = 5, 25
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
        out[int(eid)] = dict(row=r, reward=float(ws.cell(r, h['reward']).value),
                             hp=float(ws.cell(r, h['hp']).value),
                             name=ws.cell(r, h['name']).value)
    return out


def load_lists(path):
    ws = open_book(path).worksheets[0]
    out = {}
    for r in range(4, ws.max_row + 1):
        lid = ws.cell(r, 2).value
        if lid is None:
            continue
        out[int(lid)] = [int(x) for x in str(ws.cell(r, 3).value).split(',') if x.strip()]
    return out


def round_ids():
    ws = open_book(L02 / 'SceneInfo.xlsx').worksheets[0]
    h = heads(ws)
    return [int(x) for x in str(ws.cell(4, h['RoundList']).value).split(',') if x.strip()]


def plan():
    rl = round_ids()
    old_lists = load_lists(LIST_BAK)
    new_lists = load_lists(L02 / 'EnemyList.xlsx')
    base = load_enemy(ENEMY_BAK)
    waves = []
    for wave in range(WAVE_FROM, WAVE_TO + 1):
        lid = rl[wave - 1]
        old_ids, new_ids = old_lists[lid], new_lists[lid]
        gold_old = sum(base[e]['reward'] for e in old_ids)
        gold_raw = sum(base[e]['reward'] for e in new_ids)     # 数量 ×1.2 后的金币（未压缩）
        factor = gold_old / gold_raw
        targets = {e: round(base[e]['reward'] * factor, DIGITS) for e in Counter(new_ids)}
        waves.append(dict(wave=wave, lid=lid, factor=factor, gold_old=gold_old,
                          gold_raw=gold_raw, targets=targets,
                          gold_new=sum(targets[e] * n for e, n in Counter(new_ids).items()),
                          ids=sorted(targets)))
    hp_rows = {e for w in waves for e in w['ids']}
    return waves, hp_rows, base


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'
    waves, ids, base = plan()

    if mode == 'values':
        print(f'L02 W{WAVE_FROM}–W{WAVE_TO}｜击杀金币拉回改前值（每波精确配平）\n')
        print(f"{'波':<4}{'系数':>9}{'金币(现在)':>12}{'改前目标':>10}{'配平后':>9}{'单只系数后样例':>22}")
        t0 = t1 = t2 = 0.0
        for w in waves:
            e = w['ids'][0]
            print(f"W{w['wave']:<3}{w['factor']:>9.5f}{w['gold_raw']:>12,.2f}{w['gold_old']:>10,.2f}"
                  f"{w['gold_new']:>9,.2f}   {e}: {base[e]['reward']:.6f}->{w['targets'][e]:.6f}")
            t0 += w['gold_old']; t1 += w['gold_raw']; t2 += w['gold_new']
        print(f"\n合计：改前 {t0:,.1f}｜现在 {t1:,.1f}（{t1 / t0 - 1:+.1%}）｜配平后 {t2:,.2f}"
              f"（{(t2 / t0 - 1) * 100:+.3f}%）")
        print(f'涉及 {len(ids)} 行 reward；RoundData.rewardGold 不动')
        return 0

    if mode == 'verify':
        cur = load_enemy(L02 / 'EnemyData.xlsx')
        bad = []
        worst = 0.0
        for w in waves:
            for e, v in w['targets'].items():
                if abs(cur[e]['reward'] - v) > 1e-9:
                    bad.append(f'id={e}（W{w["wave"]}）期望 {v} 实为 {cur[e]["reward"]}')
            new_counts = Counter(load_lists(L02 / 'EnemyList.xlsx')[w['lid']])
            got = sum(cur[e]['reward'] * n for e, n in new_counts.items())
            worst = max(worst, abs(got - w['gold_old']))
            if abs(got - w['gold_old']) > 0.01:
                bad.append(f'W{w["wave"]} 金币 {got:.4f} != 改前 {w["gold_old"]:.4f}')
        for e in cur:
            if e not in ids and abs(cur[e]['reward'] - base[e]['reward']) > 1e-9:
                bad.append(f'id={e} 非目标行 reward 被改动')
        if bad:
            print('❌ 校验失败：')
            for b in bad[:20]:
                print('  ' + b)
            return 1
        print(f'✅ 校验通过：{len(ids)} 行 reward 已按每波系数压缩；'
              f'21 波金币与改前最大偏差 {worst:.6f}；其余 {len(cur) - len(ids)} 行未改动')
        return 0

    assert mode == 'apply', f'未知模式 {mode}'
    cur = load_enemy(L02 / 'EnemyData.xlsx')
    if all(abs(cur[e]['reward'] - v) < 1e-9 for w in waves for e, v in w['targets'].items()):
        print('⏭ 已是目标值，未重复写入')
        return 0
    if not ENEMY_BAK2.exists():
        shutil.copy2(L02 / 'EnemyData.xlsx', ENEMY_BAK2)
        print('备份 ->', ENEMY_BAK2.name)
    wb = openpyxl.load_workbook(L02 / 'EnemyData.xlsx')
    ws = wb[wb.sheetnames[0]]
    h = heads(ws)
    n = 0
    for w in waves:
        for e, v in w['targets'].items():
            ws.cell(cur[e]['row'], h['reward']).value = v
            n += 1
    wb.save(L02 / 'EnemyData.xlsx')
    print(f'已写入 EnemyData.reward：{n} 行')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
