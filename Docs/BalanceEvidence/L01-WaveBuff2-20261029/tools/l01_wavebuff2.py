# -*- coding: utf-8 -*-
"""L01 第二轮波次强化（2026-10-29 用户确认按字面落地，已知不可通关，作极限基准）：

- 在第一轮强化后的当前状态上：W5-25 序列再 ×2（W25 达 700 只）、地面 hp 再 ×1.5（累计 ×2.25）、
  空中 hp 再 ×2.0（累计 ×4.0）。
- 整关经济减半：总收入 6517 → 3258。初始金币/波奖不变 → 击杀金预算 2333，
  摊到 9660 只怪 = 每只约 0.24 金 → 约 76% 怪物 reward=0（C# AddGold(0) 已确认安全）。
- W1-4 不动；RoundData/SceneInfo/LevelMap/TowerInfo 不动；W25 间隔保持 215ms。
- 防重入护栏：基线必须是第一轮强化态（W5 N=110 且 desc 含 wavebuff-20261029）。

用法：python l01_wavebuff2.py [--write]
"""
import json, math, pathlib, sys, collections
import openpyxl

ROOT = pathlib.Path(r'D:/FishTestGame')
DATA = ROOT / 'Luban/Config/Datas'
L01 = DATA / 'Levels/L01'
G2, A2 = 1.5, 2.0
INCOME_TARGET = 3259          # 6517 的一半（3258.5 取整到偶数邻域 3259，-49.99%；击杀预算 2334 需为偶数）
BUFF2_TAG = 'wavebuff2-20261029'
REVISION2 = 'wavebuff2-20261029-v1'

def _rows(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.worksheets[0]
    heads = {c.value: c.column for c in ws[1] if c.value}
    out = []
    for r in range(4, ws.max_row + 1):
        if ws.cell(r, heads['id']).value is not None:
            out.append({k: ws.cell(r, c).value for k, c in heads.items()})
    wb.close()
    return out

def load_level():
    scene = _rows(L01 / 'SceneInfo.xlsx')[0]
    rating = _rows(L01 / 'LevelRating.xlsx')[0]
    order = [int(x) for x in str(scene['RoundList']).split(',')]
    rounds = {int(r['id']): dict(list_id=int(str(r['EnemyIndexs']).split(',')[0]),
                                 reward=int(r['rewardGold'])) for r in _rows(L01 / 'RoundData.xlsx')}
    lists = {int(r['id']): dict(seq=[int(x) for x in str(r['EnemyIndexs']).split(',')],
                                enemyInterval=int(r['enemyInterval']), desc=r['desc'])
             for r in _rows(L01 / 'EnemyList.xlsx')}
    variants = {int(r['id']): r for r in _rows(L01 / 'EnemyData.xlsx')}
    # 防重入：基线必须是第一轮强化态
    wmap = {rid: i + 1 for i, rid in enumerate(order)}
    for rid in order:
        w = wmap[rid]
        n = len(lists[rounds[rid]['list_id']]['seq'])
        expect = 2 * (25 + 6 * w) if w >= 5 else 25 + 6 * w
        if n != expect:
            raise RuntimeError(f'基线不符：W{w} 敌数 {n} != {expect}（应为第一轮强化态）')
    if not any('wavebuff-20261029' in str(l['desc'] or '') for l in lists.values()):
        raise RuntimeError('未检测到第一轮强化标记，拒绝执行')
    if any('wavebuff2-20261029' in str(l['desc'] or '') for l in lists.values()):
        raise RuntimeError('已是第二轮强化态，拒绝重复执行')
    return dict(order=order, rounds=rounds, lists=lists, variants=variants,
                initialGold=int(scene['initialGold']), rating=rating)

def compute(lv):
    wmap = {rid: i + 1 for i, rid in enumerate(lv['order'])}
    income_old = lv['initialGold'] + sum(
        int(lv['variants'][v]['reward'] or 0) * collections.Counter(
            lv['lists'][lv['rounds'][rid]['list_id']]['seq'])[v]
        for rid in lv['order'] for v in set(lv['lists'][lv['rounds'][rid]['list_id']]['seq']))
    income_old += sum(lv['rounds'][rid]['reward'] for rid in lv['order'])
    assert income_old == 6517, f'基线收入 {income_old} != 6517'
    waves_old, waves_new = [], []
    buff_ids = set()
    for rid in lv['order']:
        w = wmap[rid]; seq = lv['lists'][lv['rounds'][rid]['list_id']]['seq']
        fly = sum(1 for v in seq if lv['variants'][v]['isFlying'] == 1)
        ehp = sum(lv['variants'][v]['hp'] / (1 - (lv['variants'][v]['armor'] or 0)) for v in seq)
        kill = sum(int(lv['variants'][v]['reward'] or 0) for v in seq)
        waves_old.append(dict(wave=w, rid=rid, n=len(seq), fly=fly, ehp=ehp, kill=kill,
                              reward=lv['rounds'][rid]['reward']))
        if w >= 5:
            buff_ids |= set(seq)
    # 击杀金预算：3258 - 100 - 825 = 2333（W1-4 的 294 不变）
    kill_w14 = next(x['kill'] for x in waves_old if x['wave'] == 1) + \
               sum(x['kill'] for x in waves_old if 2 <= x['wave'] <= 4)
    kill_target = INCOME_TARGET - lv['initialGold'] - sum(x['reward'] for x in waves_old)
    w525_target = kill_target - kill_w14
    # 第二轮翻倍后的出场次数
    cnt2 = collections.Counter()
    for x in waves_old:
        if x['wave'] >= 5:
            for v in lv['lists'][lv['rounds'][x['rid']]['list_id']]['seq']:
                cnt2[v] += 2
    spawns2 = sum(cnt2.values())
    per_spawn = w525_target / spawns2
    # 新奖励：round(old × (per_spawn/old_per_spawn))，下限 0；全局 ±1 局部搜索精确命中
    f = per_spawn / (sum(int(lv['variants'][v]['reward'] or 0) * (cnt2[v] // 2) for v in cnt2) / (spawns2 / 2))
    new_reward = {v: min(9, max(0, round(int(lv['variants'][v]['reward'] or 0) * f))) for v in cnt2}
    diff = w525_target - sum(new_reward[v] * cnt2[v] for v in cnt2)
    guard = 0
    while diff != 0 and guard < 500:
        guard += 1
        best = None
        for v in cnt2:
            if new_reward[v] < 9:
                nd = abs(diff - cnt2[v])
                if best is None or nd < best[0]: best = (nd, v, +1)
            if new_reward[v] > 0:
                nd = abs(diff + cnt2[v])
                if nd < best[0]: best = (nd, v, -1)
        if best is None or best[0] >= abs(diff): break
        _, v, step = best
        new_reward[v] += step; diff -= step * cnt2[v]
    assert diff == 0, f'奖励精确和未命中：残差 {diff}'
    # 新血量/新序列
    new_hp = {v: round(float(lv['variants'][v]['hp']) * (A2 if lv['variants'][v]['isFlying'] == 1 else G2), 6)
              for v in cnt2}
    waves_new = []
    for x in waves_old:
        if x['wave'] <= 4:
            seq2 = lv['lists'][lv['rounds'][x['rid']]['list_id']]['seq']
        else:
            base_seq = lv['lists'][lv['rounds'][x['rid']]['list_id']]['seq']
            seq2 = base_seq + base_seq
        fly = sum(1 for v in seq2 if lv['variants'][v]['isFlying'] == 1)
        ehp = sum((new_hp.get(v, lv['variants'][v]['hp']) / (1 - (lv['variants'][v]['armor'] or 0))) for v in seq2)
        kill = sum(new_reward.get(v, int(lv['variants'][v]['reward'] or 0)) for v in seq2)
        waves_new.append(dict(wave=x['wave'], rid=x['rid'], n=len(seq2), fly=fly, ehp=ehp,
                              kill=kill, reward=x['reward'], seq=seq2))
    income_new = lv['initialGold'] + sum(x['kill'] for x in waves_new) + sum(x['reward'] for x in waves_new)
    assert income_new == INCOME_TARGET, f'经济目标未命中：{income_new} != {INCOME_TARGET}'
    zero_spawns = sum(cnt2[v] for v in cnt2 if new_reward[v] == 0)
    return dict(waves_old=waves_old, waves_new=waves_new, buff_ids=set(cnt2), new_hp=new_hp,
                new_reward=new_reward, cnt2=cnt2, factor=f, income_old=income_old,
                income_new=income_new, kill_target=kill_target, w525_target=w525_target,
                spawns2=spawns2, per_spawn=round(per_spawn, 3),
                zero_ratio=round(zero_spawns / spawns2, 3))

def write_tables(lv, res, dry=True):
    audit = []
    p = L01 / 'EnemyData.xlsx'
    wb = openpyxl.load_workbook(p); ws = wb.worksheets[0]
    heads = {c.value: c.column for c in ws[1] if c.value}
    n_hp = n_rw = 0
    for r in range(4, ws.max_row + 1):
        vid = ws.cell(r, heads['id']).value
        if vid in res['buff_ids']:
            ws.cell(r, heads['hp'], res['new_hp'][vid]); n_hp += 1
            if ws.cell(r, heads['reward']).value != res['new_reward'][vid]:
                ws.cell(r, heads['reward'], res['new_reward'][vid]); n_rw += 1
            d = str(ws.cell(r, heads['desc']).value or '')
            base = d.split(' | ' + BUFF2_TAG)[0]
            mult = A2 if lv['variants'][vid]['isFlying'] == 1 else G2
            ws.cell(r, heads['desc'], base + f' | {BUFF2_TAG}: hp x{mult} again, counts x2 again, reward halved-budget')
    audit.append(('EnemyData.xlsx', f'{n_hp} 个变体 hp 再乘（{n_rw} 个 reward 变化，允许 0）'))
    if not dry: wb.save(p)
    wb.close()
    p = L01 / 'EnemyList.xlsx'
    wb = openpyxl.load_workbook(p); ws = wb.worksheets[0]
    heads = {c.value: c.column for c in ws[1] if c.value}
    for x in res['waves_new']:
        if x['wave'] <= 4: continue
        r_idx = None
        for r in range(4, ws.max_row + 1):
            if ws.cell(r, heads['id']).value == x['rid']: r_idx = r; break
        ws.cell(r_idx, heads['EnemyIndexs'], ','.join(str(v) for v in x['seq']))
        ws.cell(r_idx, heads['desc'],
                f'L1 W{x["wave"]}/25; N={x["n"]}; EHP={x["ehp"]:.6f} | {BUFF2_TAG} (counts x2 again, hp stacked)')
    audit.append(('EnemyList.xlsx', 'W5-25 共 21 行 EnemyIndexs 再翻倍 + desc 更新'))
    if not dry: wb.save(p)
    wb.close()
    import hashlib
    p = L01 / 'LevelRating.xlsx'
    wb = openpyxl.load_workbook(p); ws = wb.worksheets[0]
    heads = {c.value: c.column for c in ws[1] if c.value}
    expected = sum(x['n'] for x in res['waves_new'])
    spec = json.dumps({'waves': [{k: x[k] for k in ('wave', 'n', 'seq', 'kill')} for x in res['waves_new']],
                       'hp': res['new_hp'], 'reward': res['new_reward']}, ensure_ascii=False, sort_keys=True)
    plan_hash = hashlib.sha256(spec.encode('utf-8')).hexdigest()
    for r in range(4, ws.max_row + 1):
        if ws.cell(r, heads['id']).value == 1:
            ws.cell(r, heads['expectedEnemyCount'], expected)
            ws.cell(r, heads['planHash'], plan_hash)
            ws.cell(r, heads['balanceRevision'], REVISION2)
            ws.cell(r, heads['calibrationStatus'], 'pending_unity_reference')
    audit.append(('LevelRating.xlsx', f'expectedEnemyCount->{expected}, planHash={plan_hash[:12]}…, revision={REVISION2}'))
    if not dry: wb.save(p)
    wb.close()
    return audit

def print_compare(res):
    print(f"收入：{res['income_old']} -> {res['income_new']}（{INCOME_TARGET if False else res['income_new']}，"
          f"{res['income_new']/res['income_old']-1:+.1%}）  击杀金预算 {res['w525_target']} ÷ {res['spawns2']} 只 = "
          f"{res['per_spawn']} 金/只，0 掉落占比 {res['zero_ratio']:.0%}")
    print('波 | 敌数 旧→新 | 空军 旧→新 | EHP 旧→新 | 击杀金 旧→新')
    for o, n in zip(res['waves_old'], res['waves_new']):
        print(f"W{o['wave']:02d} | {o['n']:4d}->{n['n']:4d} | {o['fly']:3d}->{n['fly']:3d} | "
              f"{o['ehp']:9.0f}->{n['ehp']:9.0f} | {o['kill']:4d}->{n['kill']:4d}")

if __name__ == '__main__':
    dry = '--write' not in sys.argv
    lv = load_level()
    res = compute(lv)
    print_compare(res)
    for a in write_tables(lv, res, dry=dry):
        print(('（dry-run）' if dry else '已写入 '), a[0], ':', a[1])
