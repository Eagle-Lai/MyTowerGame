# -*- coding: utf-8 -*-
"""第二轮强化可行性探针（只读，不写任何表）。

需求：W5-25 数量再×2、地面血量再×1.5、空中再×2.0；整关经济降至原来的一半（6517→3258）。
本探针回答三个问题：
  A) 经济：3258 的击杀金预算摊到 9660 只怪上，每只平均多少？（奖励 0 值占比）
  B) 容量：满配 42×L3 迷宫在 W25=700 只 / 49.9 万 EHP 下，各出怪间隔漏多少？
  C) 前期：真实经济曲线下 W5-W8 能否站得住？
"""
import collections, json, pathlib, sys
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r'D:/FishTestGame/Docs/BalanceEvidence/L01-DiagramRedesign-20261028/tools')
sys.path.insert(0, r'D:/FishTestGame/.workbuddy/tools')

import l01_verify as V
import l01_design
import balance_simulator as bs

G2, A2 = 1.5, 2.0            # 第二轮血量倍数
INCOME_TARGET = 3258         # 6517 的一半

def build_round2_tables():
    """在内存中从当前盘上表再叠一层强化，返回 (variants2, lists2, waves2 统计)。"""
    base = l01_design.build_plan_from_disk()
    variants = {v['id']: dict(v) for v in base['tables']['tbenemydata']}
    lists = {}
    for w in base['waves']:
        lists[w['waveOrdinal']] = dict(seq=list(w['enemyIds']), spawn=w['spawnIntervalMs'],
                                       reward=w['rewardGold'])
    for w in range(5, 26):
        seq = lists[w]['seq']
        lists[w]['seq'] = seq + seq                       # 再 ×2
        for v in set(seq):
            mult = A2 if variants[v]['isFlying'] == 1 else G2
            variants[v]['hp'] = round(variants[v]['hp'] * mult, 6)
    waves2 = []
    for w in range(1, 26):
        seq = lists[w]['seq']
        fly = sum(1 for v in seq if variants[v]['isFlying'] == 1)
        ehp = sum(variants[v]['hp'] / (1 - (variants[v]['armor'] or 0)) for v in seq)
        waves2.append(dict(wave=w, n=len(seq), fly=fly, ehp=ehp))
    return base, variants, lists, waves2

def economy_solve(base, variants, lists):
    spawns_w525 = sum(len(lists[w]['seq']) for w in range(5, 26))
    wave_reward = sum(lists[w]['reward'] for w in range(1, 26))
    kill_target = INCOME_TARGET - 100 - wave_reward
    per_spawn = kill_target / spawns_w525
    zero_ratio = 1 - per_spawn if per_spawn < 1 else 0
    return dict(spawns_w525=spawns_w525, wave_reward=wave_reward, kill_target=kill_target,
                per_spawn=round(per_spawn, 3), zero_ratio=round(max(0, zero_ratio), 3),
                feasible=0 <= per_spawn)

def make_plan(base, variants, lists, waves_keep, initial_gold, hp, interval_override=None):
    """构造只含 waves_keep 波的 plan（供探针仿真）。"""
    plan = json.loads(json.dumps(base))
    plan['tables']['tbenemydata'] = [variants[v['id']] for v in base['tables']['tbenemydata']]
    plan['waves'] = [w for w in plan['waves'] if w['waveOrdinal'] in waves_keep]
    for w in plan['waves']:
        w['enemyIds'] = lists[w['waveOrdinal']]['seq']
        w['count'] = len(w['enemyIds'])
        if interval_override:
            w['spawnIntervalMs'] = interval_override
        comp = collections.Counter(w['enemyIds'])
        vmap = {v['id']: v for v in plan['tables']['tbenemydata']}
        w['composition'] = [dict(variantId=vid, role=('air' if vmap[vid]['isFlying'] == 1 else 'normal'),
                                 count=c) for vid, c in comp.items()]
        w['actualEhp'] = sum(vmap[v]['hp'] / (1 - (vmap[v]['armor'] or 0)) for v in w['enemyIds'])
    plan['tables']['tbsceneinfo'][0]['initialGold'] = initial_gold
    plan['tables']['tbsceneinfo'][0]['initialHp'] = hp
    plan['tables']['tblevelrating'][0]['expectedWaveCount'] = len(plan['waves'])
    return plan

def full_maze_ops(wave_ord):
    ops = []
    for cell in V.blueprint_flat():
        ops.append({'waveOrdinal': wave_ord, 'timeMs': 0, 'action': 'build', 'row': cell[1]-1,
                    'col': cell[0]-1, 'towerId': V.TOWER_L1[V.cell_type(cell)]})
    for cell in V.blueprint_flat():
        t = V.cell_type(cell)
        ops.append({'waveOrdinal': wave_ord, 'timeMs': 0, 'action': 'upgrade', 'row': cell[1]-1,
                    'col': cell[0]-1, 'towerId': V.TOWER_L2[t]})
        ops.append({'waveOrdinal': wave_ord, 'timeMs': 0, 'action': 'upgrade', 'row': cell[1]-1,
                    'col': cell[0]-1, 'towerId': V.TOWER_L3[t]})
    return ops

def main():
    base, variants, lists, waves2 = build_round2_tables()
    print('=== A) 强化后逐波规模 ===')
    for x in waves2:
        if x['wave'] in (1, 4, 5, 10, 15, 20, 25):
            print(f"W{x['wave']:02d}: N={x['n']} 空军={x['fly']} EHP={x['ehp']:.0f}")
    eco = economy_solve(base, variants, lists)
    print('\n=== B) 经济求解 ===')
    print(json.dumps(eco, ensure_ascii=False))
    out = HERE.parent / 'reports'
    out.mkdir(parents=True, exist_ok=True)
    # ---- C) W25 容量扫描（满配 42×L3，hp=99 允许观察漏怪分布）
    print('\n=== C) W25=700只 容量扫描（满配迷宫）===')
    for ms in [215, 300, 400, 500]:
        plan = make_plan(base, variants, lists, {25}, 99999, 99, interval_override=ms)
        bs.POLICY.clear(); bs.POLICY['scriptedOperations'] = full_maze_ops(25)
        bs.POLICY['maxWallSeconds'] = 1200; bs.POLICY['maxWaveSeconds'] = 900
        r = V.simulate_level_tracked(plan, 1, 200, out)
        print(f"interval={ms}ms: killed={r['killed']}/700 leaked={r['leaked']} "
              f"time={r['combatElapsedMs']/1000:.0f}s error={r['error']}")
    # ---- D) 前期 W5-W8 连打（真实经济：初始100，无满配，策略=现实验证器）
    print('\n=== D) 前期连打 W1-W8（初始100金，普通策略）===')
    plan = make_plan(base, variants, lists, set(range(1, 9)), 100, 1)
    bs.POLICY.clear()
    bs.POLICY['maxWallSeconds'] = 1200; bs.POLICY['maxWaveSeconds'] = 900
    r = V.simulate_level_tracked(plan, 1, 100, out)
    print(f"victory={r['victory']} hp={r['hp']} completed={r['completedWaveCount']}/8 total_leaked={r['leaked']}")
    for wr in r['reports']:
        print(f"  W{wr['waveOrdinal']}: kill={wr['killed']}/{wr['planned']} leak={wr['leaked']} "
              f"towers={wr['towerCount']} t={wr['combatElapsedMs']/1000:.1f}s")
    (out / 'probe_round2.json').write_text(json.dumps({'eco': eco}, ensure_ascii=False), encoding='utf-8')

if __name__ == '__main__':
    main()
