#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""反向对齐：把 balance_design.json 调到「能复现当前手改表」。

方向说明（用户 2026-10-22 明确）：**配方 ← 表**，不是表 ← 配方。
表是人工维护的真值，配方只作为「可离线复算 / 可给 fill-gate 用」的影子。

对齐手段（只用现有 schema，不新增公式）：
  1. roles.air.weight 0.45 → 0.60      —— 让空中单位血量是地面的 2.0/1.5 倍
  2. roles.air.share  0.12 → 0.24      —— 空军数量翻倍
  3. air 解锁波全部推到 ≥5              —— W1~W4 不出空军
  4. formula.goldPerEhp                 —— 击杀金币按「单位 EHP × 系数」发，天然随关卡缩放
  5. 每关 3 条 override（targetEhp / rewardGold / parCombatTimeMs）
     —— 吸收「每波空军占比不同」带来的形状误差，把每关总量钉到表上
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import balance_pipeline as bp

CFG = bp.ROOT / 'Assets/ConfigJson'
AIR_UNLOCK = [(13, 5), (11, 6), (14, 8), (12, 13), (2, 18)]


def table_profile():
    scene = {r['id']: r for r in bp.read_json(CFG / 'tbsceneinfo.json')}
    rounds = {r['id']: r for r in bp.read_json(CFG / 'tbrounddata.json')}
    lists = {r['id']: r for r in bp.read_json(CFG / 'tbenemylist.json')}
    enemy = {r['id']: r for r in bp.read_json(CFG / 'tbenemydata.json')}
    rating = {r['id']: r for r in bp.read_json(CFG / 'tblevelrating.json')}
    out = {}
    for L, scene_row in scene.items():
        ids, wave_gold = [], 0
        per_wave = []
        for rid in scene_row['RoundList']:
            lid = rounds[rid]['EnemyIndexs'][0]
            wave_ids = lists[lid]['EnemyIndexs']
            ids += wave_ids
            wave_gold += rounds[rid]['rewardGold']
            per_wave.append(sum(enemy[i]['hp'] / (1 - enemy[i]['armor']) for i in wave_ids))
        ehp = sum(enemy[i]['hp'] / (1 - enemy[i]['armor']) for i in ids)
        kill = sum(enemy[i]['reward'] for i in ids)
        out[L] = {'ehp': ehp, 'kill': kill, 'wave': wave_gold, 'gold': kill + wave_gold,
                  'count': len(ids), 'perWave': per_wave,
                  'air': sum(1 for i in ids if enemy[i].get('isFlying')),
                  'par': rating[L]['parCombatTimeMs'], 'initialGold': scene_row['initialGold']}
    return out


def plan_profile(plan):
    out = {}
    for L in range(1, plan['levelCount'] + 1):
        waves = [w for w in plan['waves'] if w['levelId'] == L]
        out[L] = {'ehp': sum(w['actualEhp'] for w in waves), 'kill': sum(w['killGold'] for w in waves),
                  'wave': sum(w['rewardGold'] for w in waves), 'count': sum(w['count'] for w in waves),
                  'air': sum(w['flyingCount'] for w in waves),
                  'perWave': [w['actualEhp'] for w in waves]}
        out[L]['gold'] = out[L]['kill'] + out[L]['wave']
    return out


def apply(recipe):
    f = recipe['formula']
    f['goldPerEhp'] = GPE
    recipe['roles']['air']['weight'] = 0.60
    recipe['roles']['air']['share'] = 0.24
    for u in recipe['unlockSchedule']:
        if u['role'] == 'air':
            u['wave'] = dict(AIR_UNLOCK)[u['canonicalId']]
    return recipe


GPE = 0.0


def main():
    global GPE
    tbl = table_profile()
    recipe = bp.read_json(bp.DEFAULT_RECIPE)
    recipe['overrides'] = []
    recipe['parCalibration'] = {}

    # 击杀金币：让「单位 EHP × gpe」近似表里的击杀收入
    GPE = round(tbl[1]['kill'] / tbl[1]['ehp'], 6)
    print(f'goldPerEhp = {GPE}（L1 击杀金 {tbl[1]["kill"]} / EHP {tbl[1]["ehp"]:.0f}）')
    apply(recipe)

    for attempt in range(1, 4):
        plan = bp.generate(recipe, 'D04')
        cur = plan_profile(plan)
        new_overrides = []
        worst_e = worst_g = 0.0
        for L in range(1, 31):
            r_e = tbl[L]['ehp'] / cur[L]['ehp']
            # 累积倍率（上一轮已经乘过，这里按残差再修一次）
            prev_e = next((o['value'] for o in recipe['overrides']
                           if o['id'] == f'align-ehp-L{L}'), 1.0)
            new_overrides += [
                {'id': f'align-ehp-L{L}', 'scope': 'level', 'levelId': L, 'target': 'wave',
                 'field': 'targetEhp', 'mode': 'multiply', 'value': round(prev_e * r_e, 6)},
                {'id': f'align-wave-L{L}', 'scope': 'level', 'levelId': L, 'target': 'wave',
                 'field': 'rewardGold', 'mode': 'replace',
                 # 波奖励吃掉「击杀四舍五入」的残差，让每关总金币也钉到表上
                 'value': max(1, round((tbl[L]['gold'] - cur[L]['kill']) / len(tbl[L]['perWave'])))},
                {'id': f'align-par-L{L}', 'scope': 'level', 'levelId': L, 'target': 'rating',
                 'field': 'parCombatTimeMs', 'mode': 'replace', 'value': tbl[L]['par']},
            ]
            worst_e = max(worst_e, abs(r_e - 1))
        recipe['overrides'] = new_overrides
        print(f'  第 {attempt} 轮：EHP 最大残差 {worst_e*100:.2f}%')

    plan = bp.generate(recipe, 'D04')
    cur = plan_profile(plan)
    print('\n L   表EHP      配方EHP    Δ%     表金   配方金   Δ%   表空军 配方空军')
    for L in range(1, 31):
        de = (cur[L]['ehp'] / tbl[L]['ehp'] - 1) * 100
        dg = (cur[L]['gold'] / tbl[L]['gold'] - 1) * 100
        print(f'{L:>2}  {tbl[L]["ehp"]:>10.0f} {cur[L]["ehp"]:>10.0f} {de:>6.2f}  '
              f'{tbl[L]["gold"]:>6} {cur[L]["gold"]:>6} {dg:>6.2f}  {tbl[L]["air"]:>4} {cur[L]["air"]:>4}')

    result = bp.validate(plan)
    print('\nvalidate:', result['passed'], result['errors'][:3])
    recipe['balanceRevision'] = 'balance-30x25-l1anchor-v8'
    bp.write_json(bp.DEFAULT_RECIPE, recipe)
    print('written', bp.DEFAULT_RECIPE)


if __name__ == '__main__':
    main()
