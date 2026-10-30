# -*- coding: utf-8 -*-
"""L01：地面怪 +5% 之后把经济拉回原值（2026-10-30 用户追加要求）。

需求原文：
  「我只是说增加地面怪物 5%，不希望经济也增加 5%，你要重新计算。」

背景：`l01_ground_plus5.py` 只加了数量（W5-25 地面 +441 只），怪物单价没动，
于是击杀金从 2,733.00 涨到 2,839.16（+106.16）。本脚本把这 106 金收回去：
**只改 W5-25 地面变体的单只奖励**，空军与 W1-4 一律不动。

口径：
- 目标击杀金：W1-4 294.00 + 空军 353.88 + **W5-25 地面 2,085.12** = 2,733.00（与 +5% 之前完全一致）
- 缩放系数 k = 2,085.12 / 2,191.28 ≈ 0.951553，套到 W5-25 的地面变体上
- 每个变体保留 4 位小数；四舍五入残差由**出场次数最多**的那个变体收口，
  保证 Σ(单价 × 数量) 精确等于 2,085.12

用法：
  python l01_ground_econ_neutral.py values | reseal | verify
"""
import hashlib
import json
import pathlib
import sys

import openpyxl

ROOT = pathlib.Path(r'D:/FishTestGame')
DATAS = ROOT / 'Luban/Config/Datas'
L01 = DATAS / 'Levels/L01'
JSON_DIR = ROOT / 'Assets/ConfigJson'
TAG = 'econneutral-20261030'
REVISION = 'ground-plus5-econ-neutral-20261030-v1'
TARGET_GROUND = 2085.12   # = 2733.00 总击杀金 − 294.00(W1-4) − 353.88(空军)
TOL = 0.011


def load_rows(path):
    wb = openpyxl.load_workbook(path)
    ws = wb.worksheets[0]
    heads = {c.value: c.column for c in ws[1] if c.value}
    rows = []
    for r in range(4, ws.max_row + 1):
        if ws.cell(r, heads['id']).value is not None:
            rows.append((r, {k: ws.cell(r, c).value for k, c in heads.items()}))
    return wb, ws, heads, rows


def read_level():
    _, _, _, scene = load_rows(L01 / 'SceneInfo.xlsx')
    order = [int(x) for x in str(scene[0][1]['RoundList']).split(',')]
    _, _, _, rounds_rows = load_rows(L01 / 'RoundData.xlsx')
    rounds = {int(v['id']): v for _, v in rounds_rows}
    _, _, _, list_rows = load_rows(L01 / 'EnemyList.xlsx')
    lists = {int(v['id']): v for _, v in list_rows}
    _, _, _, var_rows = load_rows(L01 / 'EnemyData.xlsx')
    variants = {int(v['id']): v for _, v in var_rows}
    return order, rounds, lists, variants


def cmd_values():
    order, rounds, lists, variants = read_level()
    if any(TAG in str(v.get('desc') or '') for v in variants.values()):
        raise RuntimeError('已应用经济中性修正，拒绝重复执行')

    counts = {}
    for w, rid in enumerate(order, 1):
        if w <= 4:
            continue
        lid = int(str(rounds[rid]['EnemyIndexs']).split(',')[0])
        seq = [int(x) for x in str(lists[lid]['EnemyIndexs']).split(',')]
        for v in seq:
            if int(variants[v]['isFlying'] or 0) == 0:
                counts[v] = counts.get(v, 0) + 1
    current = sum(float(variants[v]['reward'] or 0) * c for v, c in counts.items())
    k = TARGET_GROUND / current
    print('W5-25 地面：%d 个变体 / %d 只出场 / 当前击杀金 %.2f → 目标 %.2f（k=%.6f）'
          % (len(counts), sum(counts.values()), current, TARGET_GROUND, k))

    plan = {v: round(float(variants[v]['reward'] or 0) * k, 4) for v in counts}
    total = sum(plan[v] * counts[v] for v in counts)
    residual = TARGET_GROUND - total
    if abs(residual) > TOL:
        v = max(counts, key=lambda x: counts[x])
        plan[v] = round(plan[v] + residual / counts[v], 6)
        total = sum(plan[v] * counts[v] for v in counts)
    if abs(total - TARGET_GROUND) > TOL:
        raise RuntimeError('残差无法收敛：%.4f' % (total - TARGET_GROUND))
    print('缩放后合计 %.4f（残差 %+.4f）' % (total, total - TARGET_GROUND))

    wb, ws, heads, rows = load_rows(L01 / 'EnemyData.xlsx')
    n = 0
    for r, v in rows:
        vid = int(v['id'])
        if vid not in plan:
            continue
        old = float(v['reward'] or 0)
        ws.cell(r, heads['reward'], plan[vid])
        d = str(v['desc'] or '').split(' | ' + TAG)[0]
        ws.cell(r, heads['desc'], d + ' | %s: %.4f (was %.2f)' % (TAG, plan[vid], old))
        n += 1
    wb.save(L01 / 'EnemyData.xlsx')
    wb.close()
    print('已改写 %d 个地面变体的 reward' % n)

    spec = json.dumps({'mode': 'ground-econ-neutral', 'target': TARGET_GROUND, 'k': round(k, 9)}, sort_keys=True)
    plan_hash = hashlib.sha256(spec.encode('utf-8')).hexdigest()
    wb, ws, heads, rows = load_rows(L01 / 'LevelRating.xlsx')
    for r, v in rows:
        ws.cell(r, heads['planHash'], plan_hash)
        ws.cell(r, heads['balanceRevision'], REVISION)
    wb.save(L01 / 'LevelRating.xlsx')
    wb.close()
    print('LevelRating: planHash=%s…, revision=%s' % (plan_hash[:12], REVISION))

    # 复核总额
    _, _, _, var2 = read_level()
    air = w14 = ground = 0.0
    for w, rid in enumerate(order, 1):
        lid = int(str(rounds[rid]['EnemyIndexs']).split(',')[0])
        seq = [int(x) for x in str(lists[lid]['EnemyIndexs']).split(',')]
        for v in seq:
            g = float(var2[v]['reward'] or 0)
            if int(var2[v]['isFlying'] or 0) == 1:
                air += g
            elif w <= 4:
                w14 += g
            else:
                ground += g
    print('\n击杀金：W1-4 %.2f｜空军 %.2f｜W5-25 地面 %.2f｜合计 %.2f（改动前 2733.00）'
          % (w14, air, ground, w14 + air + ground))


def compute_hash():
    keys = ['tbenemydata', 'tbenemylist', 'tbrounddata', 'tbsceneinfo',
            'tblevelmap', 'tbtowerinfo', 'tbbulletdata', 'tbglobal']
    text = []
    for k in keys:
        p = JSON_DIR / (k + '.json')
        s = p.read_text(encoding='utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
        text.append('%s\n%s\n' % (k, s))
    rows = json.loads((JSON_DIR / 'tblevelrating.json').read_text(encoding='utf-8-sig'))
    rows.sort(key=lambda r: r['id'])
    for r in rows:
        def joined(v):
            return ','.join(str(x) for x in v) if isinstance(v, list) else ''
        fields = [r['id'], r['difficultyTier'], r['profileId'], r['profileRevision'],
                  r['expectedWaveCount'], r['expectedEnemyCount'], r['twoStarHpPermille'],
                  r['threeStarHpPermille'], r['fourStarHpPermille'], r['maxFourStarLeaks'],
                  r['fourStarTimePermille'], r['parCombatTimeMs'],
                  joined(r.get('bossVariantIds')), joined(r.get('criticalVariantIds')),
                  r['balanceRevision'], r['ratingRevision'], r['planHash']]
        text.append('|'.join(str(x) for x in fields) + '\n')
    return hashlib.sha256(''.join(text).encode('utf-8')).hexdigest()


def cmd_reseal():
    h = compute_hash()
    print('按导出 JSON 计算 runtimeContentHash = %s' % h)
    for i in range(1, 31):
        p = DATAS / ('Levels/L%02d/LevelRating.xlsx' % i)
        wb, ws, heads, rows = load_rows(p)
        for r, v in rows:
            ws.cell(r, heads['runtimeContentHash'], h)
        wb.save(p)
        wb.close()
    print('已写入 30 关 LevelRating.xlsx（runtimeContentHash）')


def cmd_verify():
    h = compute_hash()
    rows = json.loads((JSON_DIR / 'tblevelrating.json').read_text(encoding='utf-8-sig'))
    stored = sorted({r['runtimeContentHash'] for r in rows})
    print('重算哈希: %s 一致=%s' % (h, stored == [h]))
    enemy = {x['id']: x for x in json.loads((JSON_DIR / 'tbenemydata.json').read_text(encoding='utf-8-sig'))}
    lists = {x['id']: x for x in json.loads((JSON_DIR / 'tbenemylist.json').read_text(encoding='utf-8-sig'))}
    rounds = {x['id']: x for x in json.loads((JSON_DIR / 'tbrounddata.json').read_text(encoding='utf-8-sig'))}
    lv = [x for x in json.loads((JSON_DIR / 'tbsceneinfo.json').read_text(encoding='utf-8-sig')) if x['id'] == 1][0]
    kill = 0.0
    n = 0
    for rid in lv['RoundList']:
        seq = lists[rounds[rid]['EnemyIndexs'][0]]['EnemyIndexs']
        n += len(seq)
        kill += sum(float(enemy[v]['reward']) for v in seq)
    wave = sum(rounds[r]['rewardGold'] for r in lv['RoundList'])
    print('运行时 JSON：敌数 %d｜击杀金 %.2f｜波奖 %d｜初始 100 → 总收入 %.2f'
          % (n, kill, wave, 100 + kill + wave))


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'verify'
    {'values': cmd_values, 'reseal': cmd_reseal, 'verify': cmd_verify}[mode]()
