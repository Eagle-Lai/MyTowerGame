# -*- coding: utf-8 -*-
"""L01 波次强化（2026-10-29 用户需求，仅第一关）：

- 第 5 波起（含）：地面怪生成数量 ×2、血量 ×1.5；空中怪生成数量 ×2、血量 ×2.0。
- 第 1-4 波完全不动；RoundData / SceneInfo / LevelMap 不动；三塔数值不动。
- 强化后整关经济总产出 = 原值 ×1.2（6517）：初始金币与波奖不变，全部通过
  压低 W5-25 变体击杀奖励实现（数量翻倍补偿后每只约降至 63%，≥1 截断 + 精确和校正）。
- LevelRating：expectedEnemyCount 同步翻倍（W5-25 部分）、parCombatTimeMs 按仿真
  战斗时长比值缩放、balanceRevision 升级、planHash 重算。runtimeContentHash 由
  reseal_hash.py 在导出后统一重封。

用法：
  python l01_wavebuff.py             # dry-run：计算并打印前后对比，不写表
  python l01_wavebuff.py --write     # 写表（写前会做全套断言）
"""
import json, math, pathlib, sys, collections
import openpyxl

ROOT = pathlib.Path(r'D:/FishTestGame')
DATA = ROOT / 'Luban/Config/Datas'
L01 = DATA / 'Levels/L01'
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r'D:/FishTestGame/.workbuddy/tools')

ECONOMY_FACTOR = 1.2          # 约束③：强化后整关经济 = 原值 ×1.2
GROUND_HP = 1.5               # 约束①：地面血量 +50%
AIR_HP = 2.0                  # 约束②：空中血量 +100%
W25_SPAWN_MS = 215            # 容量微调：W25 出怪间隔 128→215ms（单波扫描：170ms 漏16、185ms 漏4、200ms 恰好0漏、215ms 稳定0漏）
BUFF_TAG = 'wavebuff-20261029'
REVISION = 'wavebuff-20261029-v1'
# 击杀奖励波次预算：总击杀金固定，可腾挪余量 468 金全部前倾给早期波（后期波贴近 1 金/只下限）
HEADROOM = {5: 90, 6: 80, 7: 70, 8: 60, 9: 50, 10: 40, 11: 30, 12: 20, 13: 15, 14: 8, 15: 5}

def _rows(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.worksheets[0]
    heads = {c.value: c.column for c in ws[1] if c.value}
    out = []
    for r in range(4, ws.max_row + 1):
        if ws.cell(r, heads['id']).value is not None:
            out.append(({k: ws.cell(r, c).value for k, c in heads.items()},
                        {k: c for k, c in heads.items()}))
    wb.close()
    return out

def load_level():
    """读 L01 全部表，返回可变数据结构（不动盘）。含防重入护栏。"""
    scene_row, scene_heads = _rows(L01 / 'SceneInfo.xlsx')[0]
    rating_row, rating_heads = _rows(L01 / 'LevelRating.xlsx')[0]
    order = [int(x) for x in str(scene_row['RoundList']).split(',')]
    rounds = {}
    for row, _ in _rows(L01 / 'RoundData.xlsx'):
        rounds[int(row['id'])] = dict(list_id=int(str(row['EnemyIndexs']).split(',')[0]),
                                      reward=int(row['rewardGold']), name=row['name'])
    lists = {}
    for row, _ in _rows(L01 / 'EnemyList.xlsx'):
        lists[int(row['id'])] = dict(seq=[int(x) for x in str(row['EnemyIndexs']).split(',')],
                                     interval=int(row['interval']),
                                     enemyInterval=int(row['enemyInterval']), desc=row['desc'])
    variants = {}
    for row, _ in _rows(L01 / 'EnemyData.xlsx'):
        variants[int(row['id'])] = dict(row)
    # ★ 防重入：波次敌数必须等于 25+6W（交付态基线），且 desc 未带本次强化标记
    wmap = wave_ordinal_map(order)
    for rid in order:
        w = wmap[rid]; n = len(lists[rounds[rid]['list_id']]['seq'])
        expect = 25 + 6 * w
        if n != expect:
            raise RuntimeError(f'基线不符：W{w} 敌数 {n} != {expect}——表可能已被强化过，拒绝二次强化')
    for lst in lists.values():
        if BUFF_TAG in str(lst['desc'] or ''):
            raise RuntimeError('EnemyList 已含本次强化标记，拒绝二次强化')
    return dict(order=order, rounds=rounds, lists=lists, variants=variants,
                initialGold=int(scene_row['initialGold']), initialHp=int(scene_row['initialHp']),
                rating=rating_row)

def wave_ordinal_map(order):
    """RoundList 顺序 → 波次序号 1..25。"""
    return {rid: i + 1 for i, rid in enumerate(order)}

def compute(lv):
    """纯函数：计算强化后的全部新值与前后对比，不改入参。"""
    wmap = wave_ordinal_map(lv['order'])
    # ---- 每波旧统计
    waves_old = []
    for rid in lv['order']:
        w = wmap[rid]; lst = lv['lists'][lv['rounds'][rid]['list_id']]
        seq = lst['seq']
        fly = sum(1 for v in seq if lv['variants'][v]['isFlying'] == 1)
        ehp = sum(lv['variants'][v]['hp'] / (1 - (lv['variants'][v]['armor'] or 0)) for v in seq)
        ehp_g = sum(lv['variants'][v]['hp'] / (1 - (lv['variants'][v]['armor'] or 0))
                    for v in seq if lv['variants'][v]['isFlying'] != 1)
        ehp_a = ehp - ehp_g
        kill = sum(int(lv['variants'][v]['reward'] or 0) for v in seq)
        waves_old.append(dict(wave=w, rid=rid, n=len(seq), fly=fly, ehp=ehp, ehp_g=ehp_g,
                              ehp_a=ehp_a, kill=kill, reward=lv['rounds'][rid]['reward']))
    income_old = lv['initialGold'] + sum(x['kill'] for x in waves_old) + sum(x['reward'] for x in waves_old)
    income_target = round(income_old * ECONOMY_FACTOR)
    kill_total_target = income_target - lv['initialGold'] - sum(x['reward'] for x in waves_old)
    kill_w14_old = sum(x['kill'] for x in waves_old if x['wave'] <= 4)
    w525 = [x for x in waves_old if x['wave'] >= 5]
    w525_kill_old = sum(x['kill'] for x in w525)
    w525_kill_target = kill_total_target - kill_w14_old
    factor = w525_kill_target / (2 * w525_kill_old)     # 数量×2，每只奖励 ×factor

    # ---- W5-25 变体集合（仅这些变体改数值；W1-4 变体不动）
    buff_ids = set()
    for x in w525:
        buff_ids |= set(lv['lists'][lv['rounds'][x['rid']]['list_id']]['seq'])

    # ---- 逐变体新血量/新奖励：按波预算分配（总击杀金固定，前倾 468 金给 W5-15）
    spawn_cnt = collections.Counter()
    for x in w525:
        for v in lv['lists'][lv['rounds'][x['rid']]['list_id']]['seq']:
            spawn_cnt[v] += 2                                   # ★ 翻倍后序列中的出场次数（原序列 ×2）
    new_hp = {}
    for vid in buff_ids:
        v = lv['variants'][vid]
        mult = AIR_HP if v['isFlying'] == 1 else GROUND_HP
        new_hp[vid] = round(float(v['hp']) * mult, 6)
    # 每波：spawns 只怪，预算 target_w = 2*N_old + headroom；每只基础 1 金，
    # 余量按旧奖励加权分配（重型/精英多分），舍入残差按出场数贪心校正。
    new_reward = {}
    budget_report = []
    for x in w525:
        w = x['wave']
        seq = lv['lists'][lv['rounds'][x['rid']]['list_id']]['seq']
        cnt2 = collections.Counter()
        for v in seq: cnt2[v] += 2                            # 翻倍后的出场次数
        spawns2 = sum(cnt2.values())
        target_w = spawns2 + HEADROOM.get(w, 0)
        need = target_w - spawns2                             # 通过 +1 奖励凑出（每 +1 值 cnt2 金，每变体上限 8）
        extra = {v: 0 for v in cnt2}
        if need > 0:
            best = {0: tuple()}
            for v in cnt2:
                for _ in range(8):
                    nxt = dict(best)
                    for amt, path in best.items():
                        na = amt + cnt2[v]
                        if na <= need and na not in nxt:
                            nxt[na] = path + (v,)
                    best = nxt
            amt = max(a for a in best)                        # 可达的最大值（≤ need，通常精确等于）
            for v in best[amt]:
                extra[v] += 1
        for v in cnt2:
            new_reward[v] = 1 + extra[v]
        budget_report.append((w, spawns2, target_w))
    def kill_sum(): return sum(new_reward[v] * spawn_cnt[v] for v in buff_ids)
    diff = w525_kill_target - kill_sum()
    # ---- 全局局部搜索：±1 奖励移动，严格减小 |diff|（每变体奖励上限 9、下限 1）
    guard = 0
    while diff != 0 and guard < 300:
        guard += 1
        best_move = None
        for v in buff_ids:
            if new_reward[v] < 9:
                nd = abs(diff - spawn_cnt[v])
                if best_move is None or nd < best_move[0]: best_move = (nd, v, +1)
            if new_reward[v] > 1:
                nd = abs(diff + spawn_cnt[v])
                if nd < best_move[0]: best_move = (nd, v, -1)
        if best_move is None or best_move[0] >= abs(diff): break
        _, v, step = best_move
        new_reward[v] += step; diff -= step * spawn_cnt[v]
    assert abs(diff) <= 10, f'奖励预算残差过大：{diff}'

    # ---- 新波次序列（整段翻倍）与新统计
    waves_new = []
    for x in waves_old:
        rid = x['rid']; lst = lv['lists'][lv['rounds'][rid]['list_id']]
        if x['wave'] <= 4:
            seq_new = list(lst['seq'])
        else:
            seq_new = list(lst['seq']) + list(lst['seq'])
        fly = sum(1 for v in seq_new if lv['variants'][v]['isFlying'] == 1)
        ehp = sum((new_hp.get(v, lv['variants'][v]['hp']) / (1 - (lv['variants'][v]['armor'] or 0))) for v in seq_new)
        ehp_g = sum((new_hp.get(v, lv['variants'][v]['hp']) / (1 - (lv['variants'][v]['armor'] or 0)))
                    for v in seq_new if lv['variants'][v]['isFlying'] != 1)
        kill = sum((new_reward.get(v, int(lv['variants'][v]['reward'] or 0))) for v in seq_new)
        waves_new.append(dict(wave=x['wave'], rid=rid, n=len(seq_new), fly=fly, ehp=ehp,
                              ehp_g=ehp - (ehp - ehp_g) if False else ehp - sum(
                                  (new_hp.get(v, lv['variants'][v]['hp']) / (1 - (lv['variants'][v]['armor'] or 0)))
                                  for v in seq_new if lv['variants'][v]['isFlying'] == 1),
                              ehp_a=ehp - sum((new_hp.get(v, lv['variants'][v]['hp']) / (1 - (lv['variants'][v]['armor'] or 0)))
                                              for v in seq_new if lv['variants'][v]['isFlying'] != 1),
                              kill=kill, reward=x['reward'], seq=seq_new))
    income_new = lv['initialGold'] + sum(x['kill'] for x in waves_new) + sum(x['reward'] for x in waves_new)
    assert income_new == income_target, f'经济目标未命中：{income_new} != {income_target}'
    assert sum(x['n'] for x in waves_new[:4]) == sum(x['n'] for x in waves_old[:4]), 'W1-4 被改动'
    return dict(waves_old=waves_old, waves_new=waves_new, buff_ids=buff_ids, new_hp=new_hp,
                new_reward=new_reward, spawn_cnt=spawn_cnt, factor=factor,
                budget_report=budget_report,
                income_old=income_old, income_target=income_target,
                kill_total_target=kill_total_target, w525_kill_old=w525_kill_old,
                w525_kill_target=w525_kill_target, kill_w14_old=kill_w14_old)

def write_tables(lv, res, dry=True):
    """把 res 中的新值写回三张表。返回审计行。"""
    audit = []
    # ---- EnemyData：仅 W5-25 变体的 hp/reward/desc
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
            base = d.split(' | ' + BUFF_TAG)[0]
            mult = AIR_HP if lv['variants'][vid]['isFlying'] == 1 else GROUND_HP
            ws.cell(r, heads['desc'], base + f' | {BUFF_TAG}: hp x{mult}, reward per-wave budget')
    audit.append(('EnemyData.xlsx', f'{n_hp} 个 W5-25 变体 hp 更新（{n_rw} 个 reward 变化），W1-4 变体未触碰'))
    if not dry: wb.save(p)
    wb.close()
    # ---- EnemyList：W5-25 序列翻倍 + desc
    p = L01 / 'EnemyList.xlsx'
    wb = openpyxl.load_workbook(p); ws = wb.worksheets[0]
    heads = {c.value: c.column for c in ws[1] if c.value}
    for x in res['waves_new']:
        r_idx = None
        for r in range(4, ws.max_row + 1):
            if ws.cell(r, heads['id']).value == x['rid']: r_idx = r; break
        assert r_idx, f'EnemyList 缺 id={x["rid"]}'
        old_seq = str(ws.cell(r_idx, heads['EnemyIndexs']).value).split(',')
        if x['wave'] <= 4: continue
        ws.cell(r_idx, heads['EnemyIndexs'], ','.join(str(v) for v in x['seq']))
        if x['wave'] == 25:
            ws.cell(r_idx, heads['enemyInterval'], W25_SPAWN_MS)
        comps = collections.Counter()
        var_names = {}
        for v in x['seq']: comps[v] += 1
        ws.cell(r_idx, heads['desc'],
                f'L1 W{x["wave"]}/25; N={x["n"]}; EHP={x["ehp"]:.6f}; '
                f'variants:{len(comps)} (counts doubled, hp x{GROUND_HP}/x{AIR_HP}) | {BUFF_TAG}')
    audit.append(('EnemyList.xlsx', 'W5-25 共 21 行 EnemyIndexs 翻倍 + desc 更新；W1-4 四行未动'))
    if not dry: wb.save(p)
    wb.close()
    # ---- LevelRating：expectedEnemyCount / planHash / balanceRevision（par 留待仿真后二段更新）
    import hashlib
    p = L01 / 'LevelRating.xlsx'
    wb = openpyxl.load_workbook(p); ws = wb.worksheets[0]
    heads = {c.value: c.column for c in ws[1] if c.value}
    expected = sum(x['n'] for x in res['waves_new'])
    spec = json.dumps({'waves': [{k: x[k] for k in ('wave', 'n', 'seq', 'kill')} for x in res['waves_new']],
                       'hp': res['new_hp'], 'reward': res['new_reward'],
                       'initialGold': lv['initialGold'], 'initialHp': lv['initialHp']},
                      ensure_ascii=False, sort_keys=True)
    plan_hash = hashlib.sha256(spec.encode('utf-8')).hexdigest()
    for r in range(4, ws.max_row + 1):
        if ws.cell(r, heads['id']).value == 1:
            old_cnt = ws.cell(r, heads['expectedEnemyCount']).value
            ws.cell(r, heads['expectedEnemyCount'], expected)
            ws.cell(r, heads['planHash'], plan_hash)
            ws.cell(r, heads['balanceRevision'], REVISION)
            ws.cell(r, heads['calibrationStatus'], 'pending_unity_reference')
            audit.append(('LevelRating.xlsx',
                          f'expectedEnemyCount {old_cnt}->{expected}, planHash={plan_hash[:12]}…, '
                          f'balanceRevision={REVISION}（parCombatTimeMs 与 runtimeContentHash 留待仿真/导出阶段）'))
    if not dry: wb.save(p)
    wb.close()
    return audit

def print_compare(res):
    print(f'经济系数={ECONOMY_FACTOR}  地面血量×{GROUND_HP}  空中血量×{AIR_HP}  '
          f'W5-25 奖励系数 f={res["factor"]:.4f}（数量×2 补偿后每只约 {res["factor"]:.0%}）')
    print(f'收入：{res["income_old"]} -> {res["income_target"]}（W1-4 击杀金 {res["kill_w14_old"]} 不变；'
          f'W5-25 击杀金 {res["w525_kill_old"]} -> {res["w525_kill_target"]}，目标击杀总额 {res["kill_total_target"]}）')
    print('\n波 | 敌数       | 空军       | EHP(地面)            | EHP(空中)          | 击杀金     | 波奖')
    print('   | 旧 -> 新   | 旧 -> 新   | 旧 -> 新             | 旧 -> 新           | 旧 -> 新   | 不变')
    for o, n in zip(res['waves_old'], res['waves_new']):
        print(f'W{o["wave"]:02d} | {o["n"]:4d}->{n["n"]:4d} | {o["fly"]:3d}->{n["fly"]:3d} | '
              f'{o["ehp_g"]:9.0f}->{n["ehp_g"]:9.0f} | {o["ehp_a"]:8.0f}->{n["ehp_a"]:8.0f} | '
              f'{o["kill"]:4d}->{n["kill"]:4d} | {o["reward"]:3d}')
    t_old = [sum(x['n'] for x in res['waves_old']), sum(x['fly'] for x in res['waves_old']),
             sum(x['ehp_g'] for x in res['waves_old']), sum(x['ehp_a'] for x in res['waves_old']),
             sum(x['kill'] for x in res['waves_old'])]
    t_new = [sum(x['n'] for x in res['waves_new']), sum(x['fly'] for x in res['waves_new']),
             sum(x['ehp_g'] for x in res['waves_new']), sum(x['ehp_a'] for x in res['waves_new']),
             sum(x['kill'] for x in res['waves_new'])]
    print(f'合计 | {t_old[0]:5d}->{t_new[0]:5d} | {t_old[1]:4d}->{t_new[1]:4d} | '
          f'{t_old[2]:.0f}->{t_new[2]:.0f} (x{t_new[2]/t_old[2]:.2f}) | '
          f'{t_old[3]:.0f}->{t_new[3]:.0f} (x{t_new[3]/t_old[3]:.2f}) | {t_old[4]}->{t_new[4]}')

if __name__ == '__main__':
    dry = '--write' not in sys.argv
    lv = load_level()
    res = compute(lv)
    print_compare(res)
    print()
    for a in write_tables(lv, res, dry=dry):
        print(('（dry-run）' if dry else '已写入 '), a[0], ':', a[1])
