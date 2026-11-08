#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L02 W5–W25 血量在当前值上 ×0.8（2026-11-08 第三轮，累计相对 11-07 原值 ×1.8）。

用户口径（本轮当次确认）：
  · 范围：L02 第 5 波次（含）–第 25 波次，全部怪物（含空中）
  · 基准：**当前配置值** ×0.8（在第二轮 ×2.25 的基础上回撤，不是替换）
  · 精度：round(值, 6)
  · 其余一律不动：`reward` 金币（上一轮已压到持平）、数量、出怪顺序、`enemyInterval`、
    `speed`、`armor`、`RoundData.rewardGold`

基线：EnemyData.xlsx.bak_20261108_before_hp_r3（本轮写前快照 → 幂等）

用法：python _l02_hp_r3_080_20261108.py values|apply|verify
"""
from __future__ import annotations

import pathlib
import shutil
import sys

import openpyxl
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
L02 = ROOT / 'Luban/Config/Datas/Levels/L02'
ENEMY = L02 / 'EnemyData.xlsx'
BAK = L02 / 'EnemyData.xlsx.bak_20261108_before_hp_r3'
ORIG = L02 / 'EnemyData.xlsx.bak_20261108_before_hp150'
FACTOR = 0.8
DIGITS = 6
WAVE_FROM, WAVE_TO = 5, 25


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


def wave_ids(path):
    ws = open_book(path).worksheets[0]
    out = {}
    for r in range(4, ws.max_row + 1):
        lid = ws.cell(r, 2).value
        if lid is None:
            continue
        out[int(lid)] = [int(x) for x in str(ws.cell(r, 3).value).split(',') if x.strip()]
    return out


def plan():
    ws = open_book(L02 / 'SceneInfo.xlsx').worksheets[0]
    h = heads(ws)
    rl = [int(x) for x in str(ws.cell(4, h['RoundList']).value).split(',') if x.strip()]
    lists = wave_ids(ENEMY.parent / 'EnemyList.xlsx')
    base = load_enemy(BAK if BAK.exists() else ENEMY)
    waves = []
    for wave in range(WAVE_FROM, WAVE_TO + 1):
        lid = rl[wave - 1]
        seq = lists[lid]
        ids = sorted(set(seq))
        ehp0 = sum(base[e]['hp'] for e in seq)
        waves.append(dict(wave=wave, lid=lid, ids=ids, counts=Counter(seq),
                          ehp0=ehp0, ehp1=ehp0 * FACTOR))
    targets = {e: round(base[e]['hp'] * FACTOR, DIGITS) for w in waves for e in w['ids']}
    return waves, targets, base


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'
    waves, targets, base = plan()
    cur = load_enemy(ENEMY)

    if mode == 'values':
        orig = load_enemy(ORIG)
        print(f'L02 W{WAVE_FROM}–W{WAVE_TO}｜血量在当前值上再 ×{FACTOR}\n')
        print(f"{'波':<4}{'EHP 现':>12}{'EHP 改后':>12}{'累计/原值':>10}")
        t0 = t1 = 0.0
        for w in waves:
            t0 += w['ehp0']; t1 += w['ehp1']
            print(f"W{w['wave']:<3}{w['ehp0']:>12,.0f}{w['ehp1']:>12,.0f}"
                  f"{w['ehp1'] / sum(orig[e]['hp'] * n for e, n in w['counts'].items()):>9.2f}x")
        print(f"\n合计 EHP：{t0:,.0f} -> {t1:,.0f}")
        hp0 = sum(cur[e]['hp'] for e in targets)
        print(f'{len(targets)} 行 hp 合计：{hp0:,.2f} -> {sum(targets.values()):,.2f}')
        print(f'累计相对 11-07 原值：×{FACTOR * 2.25}｜reward / 数量 / 间隔 均不动')
        return 0

    if mode == 'verify':
        bad = []
        for e, v in targets.items():
            if abs(cur[e]['hp'] - v) > 1e-6:
                bad.append(f'id={e} hp 期望 {v} 实为 {cur[e]["hp"]}')
        for e in cur:
            if e not in targets:
                if abs(cur[e]['hp'] - base[e]['hp']) > 1e-9:
                    bad.append(f'id={e} 非目标行 hp 被改动')
        for e in cur:
            if abs(cur[e]['reward'] - base[e]['reward']) > 1e-9:
                bad.append(f'id={e} reward 被改动（本轮不允许）')
        if bad:
            print('❌ 校验失败：')
            for b in bad[:20]:
                print('  ' + b)
            return 1
        print(f'✅ 校验通过：{len(targets)} 行 hp = 上轮值 ×{FACTOR}（累计原值 ×{FACTOR * 2.25}）；'
              f'其余 {len(cur) - len(targets)} 行 hp 未动；reward 全表未改动')
        return 0

    assert mode == 'apply', f'未知模式 {mode}'
    if all(abs(cur[e]['hp'] - v) < 1e-6 for e, v in targets.items()):
        print('⏭ 已是目标值，未重复写入')
        return 0
    if not BAK.exists():
        shutil.copy2(ENEMY, BAK)
        print('备份 ->', BAK.name)
    wb = openpyxl.load_workbook(ENEMY)
    ws = wb[wb.sheetnames[0]]
    h = heads(ws)
    for e, v in targets.items():
        ws.cell(cur[e]['row'], h['hp']).value = v
    wb.save(ENEMY)
    print(f'已写入 EnemyData.hp：{len(targets)} 行 ×{FACTOR}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
