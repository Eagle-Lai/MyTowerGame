"""
生成塔防波次数据到 Luban/Config/Datas 下的三张表。

背景：这三张表在早期迁移时是**占位数据**——15 个波次编组的内容完全一样
      （都引用怪物 1..5）、时间参数为空，12 个回合也引用同一批编组。
      为了让"一波波怪物"真正有难度递进与种类变化，这里重新生成。

改动内容：
  1. EnemyData.xlsx
     · id 1..9：保持原有的梯度数值（hp/speed/armor/reward 不变，它们是设计好的档位），
       只把 resName 指向 **9 个体型/风格各异的怪物**，于是现有波次立刻有 9 种外观
     · id 10..128：为 MonsterCatalog 里的**全部 119 个怪物**各生成一行，
       数值按"体型档位 + 名称哈希抖动"自动推导（可复现）
  2. EnemyList.xlsx：15 个波次编组，数量 6→20 递增，种类随波次扩大，
     并补齐 interval（波次间隔）/ enemyInterval（波内间隔）
  3. RoundData.xlsx：12 个回合，引用 2→14 个波次（递进），并给出通关奖励

生成后需要重跑 Luban/gen_code_json.bat 让改动生效。
"""
import io, os, json, hashlib, collections
import openpyxl

ASSETS = r'D:\FreedomTower\Assets'
DATAS = r'D:\FreedomTower\Luban\Config\Datas'
SRC_ROOT = os.path.join(ASSETS, '_UIAssets', 'Monsters')


# ---------------------------------------------------------------------------
# 1. 扫描怪物（与 gen_monster_catalog.py 同一套规则）
# ---------------------------------------------------------------------------
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


# 体型档位（决定自动推导的数值），按家族归类
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
SIZE_STATS = {
    'tiny':   (60,  3.60, 0.00,  4, 1, 0.30),
    'small':  (110, 2.40, 0.00,  6, 1, 0.40),
    'medium': (220, 1.50, 0.10, 11, 1, 0.50),
    'large':  (400, 1.00, 0.20, 20, 2, 0.62),
    'huge':   (700, 0.70, 0.30, 35, 3, 0.78),
}

# id 1..9 的梯度怪：只改 resName，保留原有数值档位
TIER_MONSTERS = ['Rat', 'Bat', 'Pig', 'Chicken', 'Wasp', 'Bear', 'Boar', 'MosquitoParasite', 'Monkey']

# 后期波次里加入的"外观差异大"的具体怪物
SPECIFIC = ['Cerberus', 'Lion', 'Tiger', 'Troll', 'Zombie', 'Ogre', 'Scarab',
            'BugQueen', 'Mimic', 'Horse', 'Bull', 'Turkey']


def jitter(name, lo=0.90, hi=1.10):
    """按名字生成稳定的伪随机系数（同一份数据每次生成结果一致）"""
    h = int(hashlib.md5(name.encode('utf-8')).hexdigest()[:8], 16)
    return lo + (hi - lo) * ((h % 1000) / 999.0)


def derive(family, name):
    size = FAMILY_SIZE.get(family, 'medium')
    hp, spd, armor, reward, dmg, radius = SIZE_STATS[size]
    hp = int(round(hp * jitter(name)))
    spd = round(spd * jitter('spd' + name, 0.92, 1.08), 3)
    reward = int(round(reward * jitter('rw' + name)))
    etype = 2 if spd >= 3.0 else (3 if armor >= 0.2 else 1)
    is_flying = 1 if family == 'Bats' else 0
    return dict(speed=spd, hp=hp, type=etype, armor=armor, reward=reward,
                damageToPlayer=dmg, scale=0.5, bodyRadius=radius,
                isFlying=is_flying,
                desc='自动生成：%s / %s 档' % (family, size))


# ---------------------------------------------------------------------------
# 2. EnemyData
# ---------------------------------------------------------------------------
def write_enemy_data(mons):
    p = os.path.join(DATAS, 'EnemyData.xlsx')
    wb = openpyxl.load_workbook(p)
    ws = wb['Sheet1']

    idx = {}
    for _, name in mons:
        idx[name] = True
    for t in TIER_MONSTERS:
        if t not in idx:
            raise SystemExit('梯度怪不存在: ' + t)
    for t in SPECIFIC:
        if t not in idx:
            raise SystemExit('特定怪不存在: ' + t)

    # 清掉旧数据行（4 行起）
    for r in range(4, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            ws.cell(r, c).value = None

    row = 4
    # --- id 1..9：梯度档 ---
    kept = []
    for i, mname in enumerate(TIER_MONSTERS):
        eid = i + 1
        ws.cell(row, 2).value = eid
        ws.cell(row, 5).value = mname
        ws.cell(row, 8).value = 'Enemy_' + mname
        ws.cell(row, 16).value = '梯度档 %d（%s）' % (eid, mname)
        kept.append(eid)
        row += 1

    # 保留原有 1..9 行的数值列，从旧文件里读回来（旧数据已被清空，所以从备份 json 读）
    old = json.load(io.open(os.path.join(ASSETS, 'ConfigJson', 'tbenemydata.json'), encoding='utf-8'))
    oldmap = {r['id']: r for r in old}
    for i in range(len(TIER_MONSTERS)):
        r = 4 + i
        o = oldmap.get(i + 1)
        if not o:
            raise SystemExit('旧 EnemyData 缺少 id=%d' % (i + 1))
        ws.cell(r, 3).value = o['speed']
        ws.cell(r, 4).value = o['hp']
        ws.cell(r, 6).value = o['type']
        ws.cell(r, 7).value = o.get('interval', 100)
        ws.cell(r, 9).value = o['armor']
        ws.cell(r, 10).value = o['reward']
        ws.cell(r, 11).value = o['damageToPlayer']
        ws.cell(r, 12).value = 0.5
        ws.cell(r, 13).value = o['bodyRadius']
        ws.cell(r, 14).value = o.get('isFlying', 0)
        ws.cell(r, 15).value = ''    # 留空：沿用 prefab 自带 Animator，不覆盖

    # --- id 10..：全部怪物 ---
    next_id = 10
    id_of = {}
    for fam, name in mons:
        s = derive(fam, name)
        ws.cell(row, 2).value = next_id
        ws.cell(row, 3).value = s['speed']
        ws.cell(row, 4).value = s['hp']
        ws.cell(row, 5).value = name
        ws.cell(row, 6).value = s['type']
        ws.cell(row, 7).value = 100
        ws.cell(row, 8).value = 'Enemy_' + name
        ws.cell(row, 9).value = s['armor']
        ws.cell(row, 10).value = s['reward']
        ws.cell(row, 11).value = s['damageToPlayer']
        ws.cell(row, 12).value = s['scale']
        ws.cell(row, 13).value = s['bodyRadius']
        ws.cell(row, 14).value = s['isFlying']
        ws.cell(row, 15).value = ''
        ws.cell(row, 16).value = s['desc']
        id_of[name] = next_id
        next_id += 1
        row += 1

    wb.save(p)
    print('EnemyData: 梯度档 %d 行 + 具体怪 %d 行，共 %d 行（id 1..%d）'
          % (len(kept), len(mons), row - 4, next_id - 1))
    return id_of


# ---------------------------------------------------------------------------
# 3. EnemyList（波次编组）
# ---------------------------------------------------------------------------
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
    for k in range(1, 16):
        # 波次间隔：让 WaveManager 展开出的时间轴有明确节奏
        interval = (k - 1) * 2500
        enemy_interval = max(250, 700 - (k - 1) * 30)
        count = 5 + k

        # 越往后：参与的种类越多、数量越多
        pool = tier_ids[:max(2, min(9, 2 + (k - 1) // 2))]
        if k >= 5:
            pool = pool + specific_ids[:min(len(specific_ids), k - 4)]

        # 用 (i + k) % len 轮转：一定能覆盖到池里所有种类。
        # 曾用 (i*3+k)%len，当池长为 3 时步长与长度成倍数 → 整波全是同一种
        monsters = [pool[(i + k) % len(pool)] for i in range(count)]

        ws.cell(row, 2).value = k
        ws.cell(row, 3).value = ','.join(str(m) for m in monsters)
        ws.cell(row, 4).value = interval
        ws.cell(row, 5).value = enemy_interval
        ws.cell(row, 6).value = '第 %d 波：%d 只，%d 种怪' % (k, count, len(set(monsters)))
        row += 1

    wb.save(p)
    print('EnemyList: 生成 15 个波次编组（6~20 只，间隔 0~35s，波内 %d~%d ms）'
          % (max(250, 700 - 14 * 30), 700))


# ---------------------------------------------------------------------------
# 4. RoundData（回合）
# ---------------------------------------------------------------------------
def write_round_data():
    p = os.path.join(DATAS, 'RoundData.xlsx')
    wb = openpyxl.load_workbook(p)
    ws = wb['Sheet1']

    row = 4
    for r in range(1, 13):
        ws.cell(row, 2).value = r
        ws.cell(row, 3).value = ','.join(str(g) for g in range(1, min(15, 1 + r) + 1))
        ws.cell(row, 4).value = 2000          # 回合开始前的准备时间（ms）
        if not ws.cell(row, 5).value:
            ws.cell(row, 5).value = '第 %d 回合' % r
        ws.cell(row, 6).value = 10 + r * 5    # 通关奖励
        row += 1
    # 清掉多余行
    for r in range(row, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            ws.cell(r, c).value = None

    wb.save(p)
    print('RoundData: 12 个回合，波次数 2~14，准备时间 2s，通关奖励 15~70')


if __name__ == '__main__':
    mons = scan_monsters()
    print('扫描到 %d 个怪物 / %d 个家族' % (len(mons), len(set(f for f, _ in mons))))
    print()
    id_of = write_enemy_data(mons)
    write_enemy_list(id_of)
    write_round_data()
    print()
    print('完成。请重跑 Luban/gen_code_json.bat 让改动生效。')
