"""
生成"有挑战难度"的怪物与波次数据。

设计目标（用户反馈：怪物很快被消灭，很多功能看不到）：
  1. 怪物要能站得住 —— 血量/护甲整体上调，让战斗持续而不是秒杀
  2. 波次要更密更大 —— 出怪间隔缩短、每波数量增加，制造"漏怪"压力
  3. 回合要有递进 —— 前几轮练手，后面出坦克+群怪，逼玩家布防/卖塔/换位
  4. 掉落要有意义 —— 击杀奖励跟着血量走，让"攒钱建塔"成为策略

平衡基准（按当前塔的输出算）：
  塔 L1：伤害 10 / 冷却 0.3s = 33 DPS；L3：15 / 0.1s = 150 DPS
  玩家开局 100 金 = 5 座 L1 ≈ 165 DPS；后期最多 ~60 座（棋盘格数限制）≈ 2000 DPS
  护甲按 real = damage × (1 - armor) 生效，所以高护甲对低伤害塔特别有效
  ⇒ 怪物血量按 3~6 倍上调、护甲 0~0.45，即可让战斗从"秒杀"变成"持续交火"

  每档的"有效血量"= hp / (1 - armor)：
    tiny   200/(0.95) ≈  210      large  1400/0.7  ≈ 2000
    small  380/0.9   ≈  420      huge   2600/0.6  ≈ 4300
    medium 750/0.8   ≈  940
"""
import io, os, json, hashlib, collections
import openpyxl

ASSETS = r'D:\FreedomTower\Assets'
DATAS = r'D:\FreedomTower\Luban\Config\Datas'
SRC_ROOT = os.path.join(ASSETS, '_UIAssets', 'Monsters')


def scan_monsters():
    out = []
    for fam in sorted(os.listdir(SRC_ROOT)):
        fd = os.path.join(SRC_ROOT, fam)
        if not os.path.isdir(fd) or fam.startswith('_'):
            continue
        for sub in sorted(os.listdir(fd)):
            sd = os.path.join(fd, sub)
            if not os.path.isdir(sd):
                continue
            for fn in os.listdir(sd):
                if fn.endswith('.prefab'):
                    out.append((fam, os.path.splitext(fn)[0]))
    out.sort(key=lambda t: (t[0], t[1]))
    return out


# 体型档位（决定自动推导的数值）
FAMILY_SIZE = {
    'Parasites': 'tiny', 'Insects': 'tiny',
    'Bats': 'small', 'Birds': 'small', 'Bunnies': 'small',
    'Scorpions': 'small', 'Inanimate': 'small', 'Rats': 'small',
    'Felines': 'medium', 'Pigs': 'medium', 'Dogs': 'medium',
    'Apes': 'medium', 'Mounts': 'medium',
    'Cattle': 'large', 'Horses': 'large',
    'Giants': 'huge',
}

# hp, speed, armor, reward, damageToPlayer, bodyRadius
# （血量整体 ×3~6，护甲上调 —— 目的：战斗有来有回，而不是秒杀）
SIZE_STATS = {
    'tiny':   (200,  3.40, 0.05,  8, 1, 0.30),
    'small':  (380,  2.20, 0.10, 12, 1, 0.40),
    'medium': (750,  1.40, 0.20, 20, 2, 0.52),
    'large':  (1400, 0.95, 0.30, 34, 2, 0.62),
    'huge':   (2600, 0.65, 0.40, 55, 3, 0.78),
}

# 梯度档（id 1..9）：数值直接写死为设计值
# id, name, monster, speed, hp, armor, reward, dmg, type
TIERS = [
    (1, 'NormalEnemy', 'Rat',              1.40,  220, 0.05,  6, 1, 1),
    (2, 'QuickEnemy',  'Bat',              3.20,  130, 0.00,  8, 1, 2),
    (3, 'StrongEnemy', 'Pig',              0.80,  700, 0.35, 18, 2, 3),
    (4, 'NormalEnemy', 'Chicken',          1.70,  320, 0.10,  7, 1, 1),
    (5, 'QuickEnemy',  'Wasp',             4.00,  220, 0.00, 10, 1, 2),
    (6, 'StrongEnemy', 'Bear',             1.10, 1100, 0.40, 22, 2, 3),
    (7, 'NormalEnemy', 'Boar',             2.00,  500, 0.15,  9, 1, 1),
    (8, 'QuickEnemy',  'MosquitoParasite', 4.50,  350, 0.00, 12, 1, 2),
    (9, 'StrongEnemy', 'Monkey',           1.50, 1600, 0.45, 30, 3, 3),
]

# 后期波次加入的"外观/机制差异大"的怪
SPECIFIC = ['Cerberus', 'Lion', 'Tiger', 'Troll', 'Zombie', 'Ogre', 'Scarab',
            'BugQueen', 'Mimic', 'Horse', 'Bull', 'Turkey']


def jitter(name, lo=0.90, hi=1.10):
    h = int(hashlib.md5(name.encode('utf-8')).hexdigest()[:8], 16)
    return lo + (hi - lo) * ((h % 1000) / 999.0)


def derive(family, name):
    size = FAMILY_SIZE.get(family, 'medium')
    hp, spd, armor, reward, dmg, radius = SIZE_STATS[size]
    hp = int(round(hp * jitter(name)))
    spd = round(spd * jitter('spd' + name, 0.92, 1.08), 3)
    reward = int(round(reward * jitter('rw' + name)))
    etype = 2 if spd >= 3.0 else (3 if armor >= 0.25 else 1)
    is_flying = 1 if family == 'Bats' else 0
    return dict(speed=spd, hp=hp, type=etype, armor=armor, reward=reward,
                damageToPlayer=dmg, scale=0.5, bodyRadius=radius,
                isFlying=is_flying, desc='挑战档：%s / %s' % (family, size))


# ---------------------------------------------------------------------------
def write_enemy_data(mons):
    p = os.path.join(DATAS, 'EnemyData.xlsx')
    wb = openpyxl.load_workbook(p)
    ws = wb['Sheet1']

    names = set(n for _, n in mons)
    for t in [t[2] for t in TIERS] + SPECIFIC:
        if t not in names:
            raise SystemExit('怪物不存在: ' + t)

    for r in range(4, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            ws.cell(r, c).value = None

    # 旧表里 1..9 的 speed 等已被覆盖，这里全部按 TIERS 写死
    row = 4
    for eid, ename, mon, spd, hp, armor, reward, dmg, etype in TIERS:
        ws.cell(row, 2).value = eid
        ws.cell(row, 3).value = spd
        ws.cell(row, 4).value = hp
        ws.cell(row, 5).value = ename
        ws.cell(row, 6).value = etype
        ws.cell(row, 7).value = 100
        ws.cell(row, 8).value = 'Enemy_' + mon
        ws.cell(row, 9).value = armor
        ws.cell(row, 10).value = reward
        ws.cell(row, 11).value = dmg
        ws.cell(row, 12).value = 0.5
        ws.cell(row, 13).value = 0.4
        ws.cell(row, 14).value = 1 if mon in ('Bat',) else 0
        ws.cell(row, 15).value = ''
        ws.cell(row, 16).value = '梯度档 %d：%s（hp %d / 甲 %.2f）' % (eid, mon, hp, armor)
        row += 1

    next_id = 10
    id_of = {}
    for fam, name in mons:
        st = derive(fam, name)
        ws.cell(row, 2).value = next_id
        ws.cell(row, 3).value = st['speed']
        ws.cell(row, 4).value = st['hp']
        ws.cell(row, 5).value = name
        ws.cell(row, 6).value = st['type']
        ws.cell(row, 7).value = 100
        ws.cell(row, 8).value = 'Enemy_' + name
        ws.cell(row, 9).value = st['armor']
        ws.cell(row, 10).value = st['reward']
        ws.cell(row, 11).value = st['damageToPlayer']
        ws.cell(row, 12).value = st['scale']
        ws.cell(row, 13).value = st['bodyRadius']
        ws.cell(row, 14).value = st['isFlying']
        ws.cell(row, 15).value = ''
        ws.cell(row, 16).value = st['desc']
        id_of[name] = next_id
        next_id += 1
        row += 1

    wb.save(p)
    print('EnemyData: 梯度档 %d 行 + 具体怪 %d 行 = %d 行（id 1..%d）'
          % (len(TIERS), len(mons), row - 4, next_id - 1))
    return id_of


def write_enemy_list(id_of):
    p = os.path.join(DATAS, 'EnemyList.xlsx')
    wb = openpyxl.load_workbook(p)
    ws = wb['Sheet1']
    for r in range(4, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            ws.cell(r, c).value = None

    tier_ids = list(range(1, 10))
    specific_ids = [id_of[n] for n in SPECIFIC]
    row = 4
    total = 0
    for k in range(1, 16):
        interval = (k - 1) * 2000                      # 波次间隔 0~28s
        enemy_interval = max(180, 620 - 25 * (k - 1))  # 波内间隔 620→180ms
        count = 8 + 2 * k                              # 10→38 只
        total += count

        # 前期只用轻档，越往后参与的种类越多、越重
        pool = tier_ids[:max(2, min(9, 2 + (k - 1) // 2))]
        if k >= 4:
            pool = pool + specific_ids[:min(len(specific_ids), k - 3)]

        monsters = [pool[(i + k) % len(pool)] for i in range(count)]

        ws.cell(row, 2).value = k
        ws.cell(row, 3).value = ','.join(str(m) for m in monsters)
        ws.cell(row, 4).value = interval
        ws.cell(row, 5).value = enemy_interval
        ws.cell(row, 6).value = '第 %d 波：%d 只 / %d 种（间隔 %.1fs / %.2fs）' % (
            k, count, len(set(monsters)), interval / 1000.0, enemy_interval / 1000.0)
        row += 1

    wb.save(p)
    print('EnemyList: 15 波，每波 10~38 只（总计 %d），波内间隔 0.18~0.62s' % total)


def write_round_data():
    p = os.path.join(DATAS, 'RoundData.xlsx')
    wb = openpyxl.load_workbook(p)
    ws = wb['Sheet1']
    row = 4
    for r in range(1, 13):
        ws.cell(row, 2).value = r
        ws.cell(row, 3).value = ','.join(str(g) for g in range(1, min(15, r) + 1))
        ws.cell(row, 4).value = 1500
        if not ws.cell(row, 5).value:
            ws.cell(row, 5).value = '第 %d 回合' % r
        ws.cell(row, 6).value = 20 + 10 * r
        row += 1
    for r in range(row, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            ws.cell(r, c).value = None
    wb.save(p)
    print('RoundData: 12 回合，回合 r 含 r 个波次（1→12 递进），通关奖励 30~130')


def bump_global_pool():
    p = os.path.join(DATAS, 'Global.xlsx')
    wb = openpyxl.load_workbook(p)
    ws = wb['Sheet1']
    for c in range(1, ws.max_column + 1):
        if ws.cell(1, c).value == 'enemyPoolSize':
            old = ws.cell(4, c).value
            ws.cell(4, c).value = 256
            print('Global.enemyPoolSize: %s -> 256（波次变密后 64 不够用）' % old)
    wb.save(p)


if __name__ == '__main__':
    mons = scan_monsters()
    print('扫描到 %d 个怪物 / %d 个家族' % (len(mons), len(set(f for f, _ in mons))))
    print()
    id_of = write_enemy_data(mons)
    write_enemy_list(id_of)
    write_round_data()
    bump_global_pool()
    print()
    print('完成。请在 Unity 里执行「Tools ▸ 塔防 ▸ 10. 导出配置表（Luban）」使其生效。')
