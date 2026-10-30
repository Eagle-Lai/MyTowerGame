# -*- coding: utf-8 -*-
"""L01 示意图迷宫重设计 —— 设计规格 / 表写入器 / plan 构建器。

依据（2026-10-28 用户任务）：
  1) 第 25 波最后一怪距终点 >=2 格被消灭；2) 初始金钱 100；3) 空军从 W5 起且逐波递增、
  关卡越靠后种类越丰富（L01 只用 1 种空军 Bat）；4) 三塔三级数值沿用现行（复核通过）；
  5) 终局前示意图全部可建造格(42)满三级；6) 难度循序渐进；7) 零漏怪（initialHp=1 强制）。

本模块只写 L01 五张表（EnemyData/EnemyList/SceneInfo/LevelRating；RoundData 复用不改），
遵守 AGENTS.md 手工链路：改表 → Luban 导出 → 重封 runtimeContentHash。
变体 ID 使用 5000001.. 全新区间，写入前断言与 30 关全部现存 ID 无冲突。
"""
import json, math, pathlib, sys
import openpyxl

ROOT = pathlib.Path(r'D:/FishTestGame')
DATA = ROOT / 'Luban/Config/Datas'
L01 = DATA / 'Levels/L01'
TOOLS = ROOT / '.workbuddy/tools'
sys.path.insert(0, str(TOOLS))

# ---------------------------------------------------------------- 设计规格
# 波次 EHP 目标 = 现行值（保持既有难度节奏：W5/10/15/20 压力波、W25 终末 x2）
EHP_TARGET = [256, 320, 442, 582, 1057, 1076, 1257, 1634, 2094, 3872,
              3946, 4088, 4985, 6021, 10511, 10723, 10933, 11688, 13539, 22733,
              23192, 23661, 24138, 25838, 51579]
WAVE_REWARD = [26, 26, 26, 26, 39, 28, 28, 28, 28, 42,
               30, 30, 30, 30, 45, 32, 32, 32, 32, 48,
               34, 34, 34, 34, 51]          # 与现行 RoundData 完全一致（不改该表）
ENEMY_INTERVAL = [280 - 7 * (w - 1) if w <= 23 else 128 for w in range(1, 26)]
ROUND_IDS = list(range(1, 21)) + [401, 402, 403, 404, 405]   # SceneInfo.RoundList 现行顺序
INITIAL_GOLD = 100
INITIAL_HP = 1                # 零漏怪铁律：任意一漏即败
VID_BASE = 5000000            # 新变体 ID 区间 5000001..

# 角色参数 = 现行 L01 变体的实测参数（保持手感连续）
ROLES = {
    'normal': dict(canons=[17, 18], weight=1.0, armor=0.0, speed=1.10, reward=2, dmg=1),
    'swarm':  dict(canons=[84],     weight=0.65, armor=0.0, speed=1.05, reward=1, dmg=1),
    'medium': dict(canons=[83],     weight=2.0, armor=0.08, speed=1.00, reward=2, dmg=1),
    'heavy':  dict(canons=[88],     weight=4.0, armor=0.15, speed=0.80, reward=3, dmg=2),
    'elite':  dict(canons=[123],    weight=7.0, armor=0.22, speed=0.75, reward=5, dmg=2),
    'air':    dict(canons=[11],     weight=1.2, armor=0.0, speed=1.00, reward=1, dmg=1),
}
# canonical 身份（name/type/resName/scale/bodyRadius/isFlying/animController），取自现行变体
CANON = {
    17:   ('Chick', 1, 'Enemy_Chick', 0.5, 0.4, 0, None),
    18:   ('Chicken', 1, 'Enemy_Chicken', 0.5, 0.4, 0, None),
    84:   ('Larva', 1, 'Enemy_Larva', 0.5, 0.4, 0, None),
    83:   ('Crawler', 1, 'Enemy_Crawler', 0.5, 0.4, 0, None),
    88:   ('Scarab', 3, 'Enemy_Scarab', 0.5, 0.4, 0, None),
    123:  ('Rat', 3, 'Enemy_Rat', 0.5, 0.4, 0, None),
    11:   ('Bat', 4, 'Enemy_Bat', 0.5, 0.4, 1, None),
}

def n_per_wave(w):      return 25 + 6 * w                 # 31..175，总 2575（同现行）
def air_per_wave(w):    return 0 if w < 5 else w - 3      # W5:2 → W25:22，严格递增，总 242

def ground_mix(w, ground_n):
    """地面角色数量分配（解锁节奏同现行：W3 虫群、W5 中型、W11 重型、W25 精英）。"""
    if w <= 2:   shares = [('normal', 1.0)]
    elif w <= 4: shares = [('normal', 0.70), ('swarm', 0.30)]
    elif w <= 10: shares = [('normal', 0.50), ('swarm', 0.30), ('medium', 0.20)]
    elif w <= 24: shares = [('normal', 0.45), ('swarm', 0.27), ('medium', 0.16), ('heavy', 0.12)]
    else:         shares = [('normal', 0.42), ('swarm', 0.26), ('medium', 0.16), ('heavy', 0.14), ('elite', 0.02)]
    counts = {r: math.floor(s * ground_n) for r, s in shares}
    rem = ground_n - sum(counts.values())
    counts[shares[0][0]] += rem
    return counts

def round_up_half(x): return math.floor(x + 0.5)

def build_design():
    """生成完整设计：每波组成、变体数值、经济汇总。确定性纯函数。"""
    design = {'initialGold': INITIAL_GOLD, 'initialHp': INITIAL_HP, 'waves': [], 'variants': {}}
    for w in range(1, 26):
        n = n_per_wave(w); air_n = air_per_wave(w); ground_n = n - air_n
        gmix = ground_mix(w, ground_n)
        # normal 再对半拆成 Chick(17)/Chicken(18)（奇偶波侧重不同，纯观感）
        nn = gmix['normal']
        c17 = (nn + (1 if w % 2 else 0)) // 2
        c18 = nn - c17
        role_counts = [('normal', 17, c17), ('normal', 18, c18)]
        for r in ('swarm', 'medium', 'heavy', 'elite'):
            if gmix.get(r): role_counts.append((r, ROLES[r]['canons'][0], gmix[r]))
        if air_n: role_counts.append(('air', 11, air_n))
        q = sum(cnt * ROLES[r]['weight'] for r, c, cnt in role_counts)
        comps = []
        for r, cid, cnt in role_counts:
            if cnt <= 0: continue
            rp = ROLES[r]
            vid = VID_BASE + (w - 1) * 10 + {'normal': 0, 'swarm': 1, 'medium': 2, 'heavy': 3, 'elite': 4, 'air': 5}[r]
            # normal 双形态：17/18 共享同一变体（同角色同数值），EnemyIndexs 里按比例混排
            hp = EHP_TARGET[w - 1] * rp['weight'] / q * (1 - rp['armor'])
            speed = rp['speed'] * (1.0015 ** (w - 1))
            name, typ, res, scale, body, fly, anim = CANON[cid]
            design['variants'][vid] = dict(id=vid, speed=round(speed, 6), hp=round(hp, 6),
                name=name, type=typ, interval=100, resName=res, armor=rp['armor'],
                reward=rp['reward'], damageToPlayer=rp['dmg'], scale=scale, bodyRadius=body,
                isFlying=fly, animController=anim,
                desc=f'Balance variant; canonical={cid}; role={r}; profile=D04; level=1; wave={w}')
            comps.append(dict(variantId=vid, role=r, canonical=cid, count=cnt,
                              canonCount=None))
        # 组内序列：轮转混排（均匀铺开重型/空军，避免扎堆）
        pools = []
        for r, cid, cnt in role_counts:
            rp = ROLES[r]
            vid = VID_BASE + (w - 1) * 10 + {'normal': 0, 'swarm': 1, 'medium': 2, 'heavy': 3, 'elite': 4, 'air': 5}[r]
            if cnt <= 0: continue
            if r == 'normal':   # 17/18 混排
                seq = []
                for i in range(cnt):
                    cc = 17 if (i % 2 == 0 and i < c17 * 2) or (i >= c17 + c18 - min(c17, c18)) else 18
                    seq.append(17 if i < c17 or (i - c17) % 2 == 0 and False else 17)
                pools.append([17 if i < c17 else 18 for i in range(cnt)])
            else:
                pools.append([cid] * cnt)
        seq = []
        idx = 0
        while any(pools):
            for pi in range(len(pools)):
                if pools[pi]:
                    cid = pools[pi].pop(0)
                    r = next(r for r, c, cnt in role_counts if c == cid) if cid != 17 and cid != 18 else 'normal'
                    vid = VID_BASE + (w - 1) * 10 + {'normal': 0, 'swarm': 1, 'medium': 2, 'heavy': 3, 'elite': 4, 'air': 5}[r]
                    seq.append(vid)
            idx += 1
        ehp = sum(design['variants'][v]['hp'] / (1 - design['variants'][v]['armor']) for v in seq)
        kill = sum(design['variants'][v]['reward'] for v in seq)
        design['waves'].append(dict(waveOrdinal=w, roundId=ROUND_IDS[w - 1],
            listId=ROUND_IDS[w - 1], count=n, air=air_n,
            composition=[dict(variantId=c['variantId'], role=c['role'], count=c['count'],
                              canonical=c['canonical']) for c in comps if c['count'] > 0],
            enemyIds=seq, enemyInterval=ENEMY_INTERVAL[w - 1],
            rewardGold=WAVE_REWARD[w - 1], actualEhp=round(ehp, 6), killGold=kill))
    design['expectedEnemyCount'] = sum(x['count'] for x in design['waves'])
    design['totalKillGold'] = sum(x['killGold'] for x in design['waves'])
    design['totalWaveGold'] = sum(x['rewardGold'] for x in design['waves'])
    design['totalIncome'] = INITIAL_GOLD + design['totalKillGold'] + design['totalWaveGold']
    return design

# ---------------------------------------------------------------- 表写入
def _sheet(path):
    wb = openpyxl.load_workbook(path)
    ws = wb.worksheets[0]
    heads = {c.value: c.column for c in ws[1] if c.value}
    return wb, ws, heads

def _clear_data_rows(ws, heads, id_col='id'):
    """清掉第 4 行起全部数据行（置 None），返回可复用行号队列。"""
    free = []
    for r in range(4, ws.max_row + 1):
        if ws.cell(r, heads[id_col]).value is not None or any(
                ws.cell(r, c).value is not None for c in range(1, ws.max_column + 1)):
            for c in range(1, ws.max_column + 1):
                ws.cell(r, c).value = None
            free.append(r)
        else:
            free.append(r)
    return free

def _assert_no_id_collision(new_ids):
    seen = {}
    for L in range(1, 31):
        p = DATA / 'Levels' / f'L{L:02d}' / 'EnemyData.xlsx'
        wb = openpyxl.load_workbook(p, read_only=True)
        ws = wb.worksheets[0]
        for row in ws.iter_rows(min_row=4, values_only=True):
            if row[1] is not None and isinstance(row[1], int):
                if row[1] in new_ids and L != 1:   # L01 是重写目标，跳过自身
                    raise RuntimeError(f'变体 ID {row[1]} 与 L{L:02d} 冲突')
        wb.close()

def write_tables(design, dry_run=False):
    audit = []
    new_ids = set(design['variants'])
    _assert_no_id_collision(new_ids)
    # ---- EnemyData：全量重写变体行
    p = L01 / 'EnemyData.xlsx'
    wb, ws, heads = _sheet(p)
    free = _clear_data_rows(ws, heads)
    cols = ['id', 'speed', 'hp', 'name', 'type', 'interval', 'resName', 'armor', 'reward',
            'damageToPlayer', 'scale', 'bodyRadius', 'isFlying', 'animController', 'desc']
    for i, vid in enumerate(sorted(design['variants'])):
        v = design['variants'][vid]
        r = free[i] if i < len(free) else ws.max_row + 1
        for k, col in enumerate(cols):
            ws.cell(r, heads[col], v[col])
    audit.append(('EnemyData.xlsx', len(design['variants']), '变体行全量重写（旧 217 行清除）'))
    if not dry_run: wb.save(p); wb.close()
    # ---- EnemyList：同 25 个 listId，重写 EnemyIndexs/interval/enemyInterval/desc
    p = L01 / 'EnemyList.xlsx'
    wb, ws, heads = _sheet(p)
    free = _clear_data_rows(ws, heads)
    for i, wv in enumerate(design['waves']):
        r = free[i]
        comps = ','.join(f"{c['role']}:{c['canonical']}x{c['count']}" for c in wv['composition'])
        desc = f"L1 W{wv['waveOrdinal']}/25; N={wv['count']}; EHP={wv['actualEhp']:.6f}; {comps} | diagram-maze-20261028: air from W5 (Bat only), strictly increasing"
        ws.cell(r, heads['id'], wv['listId'])
        ws.cell(r, heads['EnemyIndexs'], ','.join(map(str, wv['enemyIds'])))
        ws.cell(r, heads['interval'], 0)
        ws.cell(r, heads['enemyInterval'], wv['enemyInterval'])
        ws.cell(r, heads['desc'], desc)
    audit.append(('EnemyList.xlsx', 25, '25 行重写（id 1-20,401-405 不变）'))
    if not dry_run: wb.save(p); wb.close()
    # ---- SceneInfo：initialHp=1 + desc
    p = L01 / 'SceneInfo.xlsx'
    wb, ws, heads = _sheet(p)
    for r in range(4, ws.max_row + 1):
        if ws.cell(r, heads['id']).value == 1:
            old_hp = ws.cell(r, heads['initialHp']).value
            ws.cell(r, heads['initialHp'], INITIAL_HP)
            ws.cell(r, heads['initialGold'], INITIAL_GOLD)
            ws.cell(r, heads['desc'],
                    'M1 13x7; obstacles=0; no-build=0; open-route building; stage=1; preset=中等; '
                    '25 clearable waves; diagram-maze-20261028; zero-leak (initialHp=1)')
            audit.append(('SceneInfo.xlsx', 1, f'initialHp {old_hp}->1, initialGold=100, desc 更新'))
    if not dry_run: wb.save(p); wb.close()
    # ---- LevelRating：期望数/关键变体/修订号/planHash（runtimeContentHash 由导出后重封）
    p = L01 / 'LevelRating.xlsx'
    wb, ws, heads = _sheet(p)
    import hashlib
    spec = json.dumps({k: design[k] for k in ('waves', 'variants', 'initialGold', 'initialHp')},
                      ensure_ascii=False, sort_keys=True)
    plan_hash = hashlib.sha256(spec.encode('utf-8')).hexdigest()
    elite_ids = [c['variantId'] for wv in design['waves'] if wv['waveOrdinal'] == 25
                 for c in wv['composition'] if c['role'] == 'elite']
    for r in range(4, ws.max_row + 1):
        if ws.cell(r, heads['id']).value == 1:
            ws.cell(r, heads['expectedEnemyCount'], design['expectedEnemyCount'])
            ws.cell(r, heads['criticalVariantIds'], ','.join(map(str, elite_ids)) or None)
            ws.cell(r, heads['balanceRevision'], 'diagram-maze-20261028-v1')
            ws.cell(r, heads['planHash'], plan_hash)
            ws.cell(r, heads['calibrationStatus'], 'pending_unity_reference')
            audit.append(('LevelRating.xlsx', 1,
                          f"expectedEnemyCount={design['expectedEnemyCount']}, criticalVariantIds={elite_ids}, "
                          f"balanceRevision=diagram-maze-20261028-v1, planHash={plan_hash[:12]}..., "
                          'runtimeContentHash 留待导出后重封'))
    if not dry_run: wb.save(p); wb.close()
    return audit

# ---------------------------------------------------------------- plan 构建（从磁盘读回，保证与表一致）
def build_plan_from_disk():
    def rows(path):
        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb.worksheets[0]
        heads = {c.value: c.column for c in ws[1] if c.value}
        out = []
        for r in range(4, ws.max_row + 1):
            if ws.cell(r, heads['id']).value is not None:
                out.append({k: ws.cell(r, c).value for k, c in heads.items()})
        wb.close()
        return out
    import balance_campaign
    scene = rows(L01 / 'SceneInfo.xlsx')[0]
    rating = rows(L01 / 'LevelRating.xlsx')[0]
    lmap = rows(L01 / 'LevelMap.xlsx')[0]
    rounds = {r['id']: r for r in rows(L01 / 'RoundData.xlsx')}
    lists = {r['id']: r for r in rows(L01 / 'EnemyList.xlsx')}
    variants = {r['id']: r for r in rows(L01 / 'EnemyData.xlsx')}
    towers = rows(L01 / 'TowerInfo.xlsx')
    globs = rows(L01 / 'LevelRules.xlsx')
    bullets = rows(L01 / 'BulletData.xlsx')
    for t in towers:
        t['upgradeTo'] = int(t['upgradeTo']); t['canAttackAir'] = int(t['canAttackAir'] or 0)
    order = [int(x) for x in str(scene['RoundList']).split(',')]
    waves = []
    for i, rid in enumerate(order, 1):
        rd = rounds[rid]; lid = int(str(rd['EnemyIndexs']).split(',')[0]); el = lists[lid]
        ids = [int(x) for x in str(el['EnemyIndexs']).split(',')]
        comp = {}
        for vid in ids:
            comp.setdefault(vid, [variants[vid], 0])
            comp[vid][1] += 1
        composition = []
        for vid, (v, cnt) in comp.items():
            role = 'air' if v['isFlying'] == 1 else ('heavy' if v['type'] == 3 and v['armor'] >= 0.15
                                                     else 'normal' if v['type'] == 1 else 'medium')
            # elite 识别：W25 的 Rat(type3, armor 0.22)
            if v['armor'] and v['armor'] >= 0.22: role = 'elite'
            composition.append({'variantId': vid, 'role': role, 'count': cnt})
        ehp = sum(variants[v]['hp'] / (1 - (variants[v]['armor'] or 0)) for v in ids)
        waves.append({'levelId': 1, 'waveOrdinal': i, 'roundId': rid, 'enemyListId': lid,
            'count': len(ids), 'enemyIds': ids, 'spawnIntervalMs': int(el['enemyInterval']),
            'rewardGold': int(rd['rewardGold']),
            'killGold': sum(variants[v]['reward'] for v in ids),
            'actualEhp': ehp, 'composition': composition,
            'flyingCount': sum(1 for v in ids if variants[v]['isFlying'] == 1),
            'heavyCount': sum(c['count'] for c in composition if c['role'] == 'heavy'),
            'eliteCount': sum(c['count'] for c in composition if c['role'] == 'elite'),
            'bossCount': 0})
    cells = str(lmap['cells']).split('|')
    plan = {'profileId': 'D04', 'tables': {
        'tbsceneinfo': [{'id': 1, 'mapId': int(scene['mapId']), 'initialGold': int(scene['initialGold']),
                         'initialHp': int(scene['initialHp'])}],
        'tblevelrating': [{'id': 1, 'expectedWaveCount': int(rating['expectedWaveCount']),
                           'expectedEnemyCount': int(rating['expectedEnemyCount']),
                           'parCombatTimeMs': int(rating['parCombatTimeMs']),
                           'profileRevision': str(rating['profileRevision']),
                           'balanceRevision': str(rating['balanceRevision']),
                           'ratingRevision': str(rating['ratingRevision']), 'planHash': str(rating['planHash'])}],
        'tblevelmap': [{'id': int(lmap['id']), 'cells': cells}],
        'tbenemydata': list(variants.values()),
        'tbtowerinfo': towers, 'tbglobal': globs, 'tbbulletdata': bullets},
        'waves': waves}
    return plan

if __name__ == '__main__':
    d = build_design()
    print(f"总敌数={d['expectedEnemyCount']} 击杀金={d['totalKillGold']} 波奖={d['totalWaveGold']} 总收入={d['totalIncome']}")
    print(f"变体数={len(d['variants'])} (ID {min(d['variants'])}..{max(d['variants'])})")
    print('波 | N | 空军 | EHP | 击杀金')
    for wv in d['waves']:
        print(f"W{wv['waveOrdinal']:02d} | {wv['count']:3d} | {wv['air']:3d} | {wv['actualEhp']:9.1f} | {wv['killGold']:4d}")
    if '--write' in sys.argv:
        for a in write_tables(d):
            print('写入:', a)
    else:
        print('\n(dry-run：加 --write 才写表)')
