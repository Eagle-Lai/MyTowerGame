# -*- coding: utf-8 -*-
"""终局容量探针：满配 42×L3 迷宫（内存中临时 initialGold=99999，不落盘）能否零漏清完
强化后的 W5-25。输出每波结果与容量结论。"""
import json, pathlib, sys
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r'D:/FishTestGame/Docs/BalanceEvidence/L01-DiagramRedesign-20261028/tools')
sys.path.insert(0, r'D:/FishTestGame/.workbuddy/tools')

import l01_verify as V
import balance_simulator as bs

# 与 l01_verify 相同的蓝图，但全部在 W1 边界一次性建成并升满
def full_maze_ops():
    ops = []
    for cell in V.blueprint_flat():
        ops.append({'waveOrdinal': 1, 'timeMs': 0, 'action': 'build',
                    'row': cell[1] - 1, 'col': cell[0] - 1, 'towerId': V.TOWER_L1[V.cell_type(cell)]})
    for cell in V.blueprint_flat():
        t = V.cell_type(cell)
        ops.append({'waveOrdinal': 1, 'timeMs': 0, 'action': 'upgrade',
                    'row': cell[1] - 1, 'col': cell[0] - 1, 'towerId': V.TOWER_L2[t]})
        ops.append({'waveOrdinal': 1, 'timeMs': 0, 'action': 'upgrade',
                    'row': cell[1] - 1, 'col': cell[0] - 1, 'towerId': V.TOWER_L3[t]})
    return ops

def main():
    plan = V.l01_design.build_plan_from_disk()
    plan['tables']['tbsceneinfo'][0]['initialGold'] = 99999   # 仅内存探针
    plan['tables']['tbsceneinfo'][0]['initialHp'] = 99        # 探针允许少量漏怪以观察每波余量
    bs.POLICY.clear()
    bs.POLICY['scriptedOperations'] = full_maze_ops()
    bs.POLICY['maxWallSeconds'] = 900
    out = HERE.parent / 'reports'
    out.mkdir(parents=True, exist_ok=True)
    r = V.simulate_level_tracked(plan, 1, 100, out)
    print(f"victory={r['victory']} leaked={r['leaked']} hp={r['hp']}/{99} completed={r['completedWaveCount']}/25")
    print('波 | 敌数 | 杀 | 漏 | 耗时s | 峰值alive | 末杀距终点')
    for wr, wv in zip(r['reports'], sorted(plan['waves'], key=lambda w: w['waveOrdinal'])):
        w25k = [k for k in r['kill_log'] if k['wave'] == wr['waveOrdinal']]
        last = w25k[-1]['cellsFromEnd'] if w25k else None
        print(f"W{wr['waveOrdinal']:02d} | {wv['count']:4d} | {wr['killed']:4d} | {wr['leaked']:3d} | "
              f"{wr['combatElapsedMs']/1000:6.1f} | {wr['alivePeak']:4d} | {last}")
    (out / 'probe_full_maze.json').write_text(json.dumps(
        {k: r[k] for k in ('victory', 'leaked', 'hp', 'completedWaveCount', 'combatElapsedMs')},
        ensure_ascii=False), encoding='utf-8')

if __name__ == '__main__':
    main()
