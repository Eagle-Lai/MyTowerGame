# -*- coding: utf-8 -*-
"""L01 击杀掉落改为「小数 + 累加进位」（2026-10-29 用户需求）。

需求原文：
  「按照当前关卡的金币基准，金币掉落可以是 float 值，累计到了 1 以上后，再增加。」

落地口径：
- 经济总量不动：W5-25 击杀金仍为 2448（W1-4 的 294 不动），整关总收入维持 3667。
- 每个变体按角色给不同小数单价，且**每只都 > 0**（不再有 93% 零掉落）。
- 取消 W24 一次性 1932 金的怪现象（那是局部搜索把预算全塞给一波的副产物）。
- 单价：normal 0.20 / swarm 0.16 / medium 0.32 / air 0.36 / heavy 0.52 / elite 1.40，
  按 W5-25 实际出场次数加权后合计 = 2448.00（精确相等，脚本内断言）。
- 表结构：`Luban/Config/Datas/EnemyData.xlsx` 的 reward 列类型 int → float
  （TBEnemyData 的定义取自该基表，其余 30 个分表头保持 int 也能正常解析，已实测）。

用法：
  python l01_flat_drop.py values     # 改 L01 数值 + 基表类型 + planHash（Luban 导出前）
  python l01_flat_drop.py reseal     # 按导出后 JSON 重算 runtimeContentHash 写回 30 关（导出后）
  python l01_flat_drop.py verify     # 只读复核（不改任何文件）
"""
import collections
import hashlib
import json
import pathlib
import re
import sys

import openpyxl

ROOT = pathlib.Path(r'D:/FishTestGame')
DATAS = ROOT / 'Luban/Config/Datas'
L01 = DATAS / 'Levels/L01'
JSON_DIR = ROOT / 'Assets/ConfigJson'
TAG = 'flatdrop-20261029'
REVISION = 'wavebuff2-flatdrop-20261029-v1'
TARGET_W525 = 2448.0
WEIGHTS = {'normal': 0.20, 'swarm': 0.16, 'medium': 0.32, 'air': 0.36, 'heavy': 0.52, 'elite': 1.40}


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
    variants = {int(v['id']): (r, v) for r, v in var_rows}
    return order, rounds, lists, variants


def wave_sequences(order, rounds, lists):
    seqs = []
    for i, rid in enumerate(order, 1):
        lid = int(str(rounds[rid]['EnemyIndexs']).split(',')[0])
        seq = [int(x) for x in str(lists[lid]['EnemyIndexs']).split(',')]
        seqs.append((i, rid, seq))
    return seqs


def role_of(desc):
    m = re.search(r'role=(\w+)', str(desc or ''))
    return m.group(1) if m and m.group(1) in WEIGHTS else 'normal'


def cmd_values():
    order, rounds, lists, variants = read_level()
    seqs = wave_sequences(order, rounds, lists)
    if seqs[4][2].__len__() != 220:
        raise RuntimeError('基线不符：W5 敌数 %d != 220（应为第二轮强化态）' % len(seqs[4][2]))
    if any(TAG in str(v['desc'] or '') for _, v in variants.values()):
        raise RuntimeError('已应用 flatdrop 调整，拒绝重复执行')

    # 1) 基表 reward 列类型 int -> float（TBEnemyData 的定义来自这张表）
    wb, ws, heads, _ = load_rows(DATAS / 'EnemyData.xlsx')
    col = heads['reward']
    cur = ws.cell(2, col).value
    if cur == 'int':
        ws.cell(2, col, 'float')
        wb.save(DATAS / 'EnemyData.xlsx')
        print('基表 EnemyData.xlsx: reward 类型 int -> float')
    elif cur != 'float':
        raise RuntimeError('基表 reward 类型异常：%r' % cur)
    else:
        print('基表 EnemyData.xlsx: reward 已是 float，跳过')
    wb.close()

    # 2) 统计 W5-25 每个变体的出场次数
    counts = collections.Counter()
    for wave, _, seq in seqs:
        if wave < 5:
            continue
        for v in seq:
            counts[v] += 1
    plan = {}
    for v, c in counts.items():
        plan[v] = WEIGHTS[role_of(variants[v][1]['desc'])]
    total = sum(plan[v] * counts[v] for v in counts)
    if abs(total - TARGET_W525) > 0.005:
        # 用 elite 收口（出场次数最少，影响面最小）
        elite = [v for v in counts if role_of(variants[v][1]['desc']) == 'elite']
        if not elite:
            raise RuntimeError('合计 %.4f 与目标 %.2f 不符，且无 elite 可收口' % (total, TARGET_W525))
        v = elite[0]
        delta = (TARGET_W525 - total) / counts[v]
        plan[v] = round(plan[v] + delta, 4)
        total = sum(plan[v] * counts[v] for v in counts)
    if abs(total - TARGET_W525) > 0.005:
        raise RuntimeError('合计 %.4f 无法收敛到 %.2f' % (total, TARGET_W525))

    # 3) 写 L01 变体 reward + desc 标注
    wb, ws, heads, rows = load_rows(L01 / 'EnemyData.xlsx')
    n_rw = 0
    for r, v in rows:
        vid = int(v['id'])
        if vid not in plan:
            continue
        new = plan[vid]
        if abs(float(v['reward'] or 0) - new) > 1e-9:
            ws.cell(r, heads['reward'], new)
            n_rw += 1
        d = str(ws.cell(r, heads['desc']).value or '')
        base = d.split(' | ' + TAG)[0]
        ws.cell(r, heads['desc'], base + ' | %s: %.2f/只(角色=%s)' % (TAG, new, role_of(v['desc'])))
    wb.save(L01 / 'EnemyData.xlsx')
    wb.close()
    print('L01 EnemyData.xlsx: %d 个变体 reward 改写（小数单价），%d 个变体 desc 标注' % (n_rw, len(plan)))

    # 4) LevelRating: planHash / balanceRevision
    spec = json.dumps({'mode': 'flat-drop', 'targetW525': TARGET_W525,
                       'weights': WEIGHTS, 'plan': {str(k): plan[k] for k in sorted(plan)}},
                      ensure_ascii=False, sort_keys=True)
    plan_hash = hashlib.sha256(spec.encode('utf-8')).hexdigest()
    wb, ws, heads, rows = load_rows(L01 / 'LevelRating.xlsx')
    for r, v in rows:
        ws.cell(r, heads['planHash'], plan_hash)
        ws.cell(r, heads['balanceRevision'], REVISION)
    wb.save(L01 / 'LevelRating.xlsx')
    wb.close()
    print('L01 LevelRating.xlsx: planHash=%s…, revision=%s' % (plan_hash[:12], REVISION))

    # 5) 前后对比
    print('\n波次  敌数  击杀金(旧)  击杀金(新)')
    old_total = new_total = 0.0
    for wave, _, seq in seqs:
        old = sum(float(variants[v][1]['reward'] or 0) for v in seq)
        new = sum(plan.get(v, float(variants[v][1]['reward'] or 0)) for v in seq)
        old_total += old
        new_total += new
        if wave <= 6 or wave in (10, 15, 20, 24, 25):
            print('W%02d   %4d  %8.0f  %10.2f' % (wave, len(seq), old, new))
    print('合计：击杀金 %.0f -> %.2f（目标 %.0f）' % (old_total, new_total, old_total))
    zero = sum(1 for wave, _, seq in seqs if wave >= 5 for v in seq if plan.get(v, 0) <= 0)
    print('W5-25 零掉落出场次数：%d（应为 0）' % zero)


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
    print('重算哈希: %s' % h)
    print('表中哈希: %s' % stored)
    print('一致: %s' % (stored == [h]))
    enemy = {x['id']: x for x in json.loads((JSON_DIR / 'tbenemydata.json').read_text(encoding='utf-8-sig'))}
    order, rounds, lists, _ = read_level()
    seqs = wave_sequences(order, rounds, lists)
    zero = total = 0
    for wave, _, seq in seqs:
        if wave < 5:
            continue
        for v in seq:
            r = float(enemy[v]['reward'])
            total += r
            if r <= 0:
                zero += 1
    print('W5-25 击杀金合计 %.2f，零掉落 %d 次' % (total, zero))
    print('W1-4 击杀金 %.0f' % sum(float(enemy[v]['reward']) for wave, _, seq in seqs if wave < 5 for v in seq))


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'verify'
    {'values': cmd_values, 'reseal': cmd_reseal, 'verify': cmd_verify}[mode]()
