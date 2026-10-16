# -*- coding: utf-8 -*-
"""多语言审计修复（2026-10-16）：补怪物名词条 + 修正塔名数据。

用法：
    C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe \
        E:/MyTowerGame/.workbuddy/tools/add_monster_names_20261016.py

做什么：
  1. 从 tbsceneinfo/tbrounddata/tbenemylist/tbenemydata.json 算出**被 8 个关卡实际引用**
     的怪物名集合，校验 MONSTER_NAMES 全覆盖（防漏）。
  2. 把 MONSTER_NAMES 幂等追加到 Localization.xlsx（怪物名=内容数据，之前完全未本地化；
     关卡详情的"本关出现怪物"列表会直接显示这些名字）。
  3. 修正 TowerInfo.xlsx 的 name 列：
       NormalTower  → Normal Tower   （词条 "Normal Tower" → 普通塔 现成）
       PowerTower   → Blast Tower    （对外名 Blast）
       RetardTower  → Frost Tower    （对外名 Frost）
     改后显示处（TowerConfig.DisplayName）即可命中多语言表。

跑完后必须在 Unity 里执行「Tools ▸ 塔防 ▸ 3. 导出配置表（Luban）」让词条与塔名生效。
"""
import json
import re
import shutil
import zipfile

ROOT = r'E:/MyTowerGame'
LOCALIZATION = ROOT + '/Luban/Config/Datas/Localization.xlsx'
TOWERINFO = ROOT + '/Luban/Config/Datas/TowerInfo.xlsx'

HEAD = ['id', 'en', 'zhHans', 'zhHant', 'comment']

# 怪物名 → (简中, 繁中)。id=en=英文原名（显示处 Localization.Get(name) 直接命中）。
MONSTER_NAMES = {
    'AdvancedHen': ('高阶母鸡', '高階母雞'),
    'Bat': ('蝙蝠', '蝙蝠'),
    'BattlePanther': ('战豹', '戰豹'),
    'Bear': ('大熊', '大熊'),
    'BearMounted': ('骑熊', '騎熊'),
    'BlackBear': ('黑熊', '黑熊'),
    'BlackBoar': ('黑野猪', '黑野豬'),
    'BlackWolf': ('黑狼', '黑狼'),
    'BlueScorpion': ('蓝蝎', '藍蠍'),
    'Boar': ('野猪', '野豬'),
    'BoarMounted': ('骑猪', '騎豬'),
    'BugQueen': ('虫后', '蟲后'),
    'Bull': ('公牛', '公牛'),
    'BullMounted': ('骑牛', '騎牛'),
    'BullyRooster': ('恶霸公鸡', '惡霸公雞'),
    'Bunny': ('小兔', '小兔'),
    'Burro': ('小毛驴', '小毛驢'),
    'Butcher': ('屠夫', '屠夫'),
    'Cannibal': ('食人族', '食人族'),
    'Caterpillar': ('毛毛虫', '毛毛蟲'),
    'CaveCaterpillar': ('洞穴毛虫', '洞穴毛蟲'),
    'CaveRat': ('洞穴鼠', '洞穴鼠'),
    'Cerberus': ('地狱犬', '地獄犬'),
    'Chick': ('雏鸡', '雛雞'),
    'Chicken': ('鸡', '雞'),
    'Cow': ('奶牛', '奶牛'),
    'Crawler': ('爬行者', '爬行者'),
    'CrystalLizard': ('水晶蜥蜴', '水晶蜥蜴'),
    'DarkBunny': ('暗黑兔', '暗黑兔'),
    'Donkey': ('驴', '驢'),
    'Drake': ('幼龙', '幼龍'),
    'DreadEye': ('恐惧之眼', '恐懼之眼'),
    'Dreadnought': ('恐惧巨兽', '恐懼巨獸'),
    'Duck': ('鸭子', '鴨子'),
    'EvilEye': ('邪眼', '邪眼'),
    'FancyParasite': ('华丽寄生体', '華麗寄生體'),
    'FlyingDemon': ('飞行恶魔', '飛行惡魔'),
    'ForestTurkey': ('森林火鸡', '森林火雞'),
    'Ghost': ('幽灵', '幽靈'),
    'Goat': ('山羊', '山羊'),
    'Gobbler': ('贪食火鸡', '貪食火雞'),
    'Goose': ('大鹅', '大鵝'),
    'GreenParasite': ('绿色寄生体', '綠色寄生體'),
    'GreenScorpion': ('绿蝎', '綠蠍'),
    'Hen': ('母鸡', '母雞'),
    'Hog': ('大肥猪', '大肥豬'),
    'Horse': ('骏马', '駿馬'),
    'Husky': ('哈士奇', '哈士奇'),
    'IceParasite': ('寒冰寄生体', '寒冰寄生體'),
    'InfectedRat': ('感染鼠', '感染鼠'),
    'Ironclad': ('铁甲兽', '鐵甲獸'),
    'Juggernaut': ('碾压巨兽', '碾壓巨獸'),
    'Larva': ('幼虫', '幼蟲'),
    'Lion': ('狮子', '獅子'),
    'LittleBunny': ('迷你兔', '迷你兔'),
    'Maneater': ('食人兽', '食人獸'),
    'MeatBug': ('肉虫', '肉蟲'),
    'MechanicalParasiteTypeA': ('机械寄生体·甲', '機械寄生體·甲'),
    'MechanicalParasiteTypeB': ('机械寄生体·乙', '機械寄生體·乙'),
    'Mimic': ('拟态怪', '擬態怪'),
    'MimicChest': ('宝箱怪', '寶箱怪'),
    'MinerBoar': ('矿工野猪', '礦工野豬'),
    'MohawkBat': ('莫西干蝙蝠', '莫西干蝙蝠'),
    'Monkey': ('猴子', '猴子'),
    'MosquitoParasite': ('蚊型寄生体', '蚊型寄生體'),
    'MossQueen': ('苔藓女王', '苔蘚女王'),
    'MossQueenMounted': ('骑乘苔藓女王', '騎乘苔蘚女王'),
    'Nightmare': ('梦魇', '夢魘'),
    'NormalEnemy': ('普通怪', '普通怪'),
    'Ogre': ('食人魔', '食人魔'),
    'Ox': ('壮牛', '壯牛'),
    'Panther': ('美洲豹', '美洲豹'),
    'Pig': ('猪', '豬'),
    'Piggy': ('小猪', '小豬'),
    'PirateBoar': ('海盗野猪', '海盜野豬'),
    'Pony': ('矮脚马', '矮腳馬'),
    'Porcupine': ('豪猪', '豪豬'),
    'Porky': ('胖猪', '胖豬'),
    'PossessedBlackBear': ('夺魂黑熊', '奪魂黑熊'),
    'PossessedBlackBoar': ('夺魂黑野猪', '奪魂黑野豬'),
    'PossessedRat': ('夺魂鼠', '奪魂鼠'),
    'PossessedWarg': ('夺魂座狼', '奪魂座狼'),
    'PossessedWatchdog': ('夺魂看门犬', '奪魂看門犬'),
    'PossessedWolf': ('夺魂狼', '奪魂狼'),
    'Pug': ('巴哥犬', '巴哥犬'),
    'Punisher': ('惩戒者', '懲戒者'),
    'PurpleScarab': ('紫圣甲虫', '紫聖甲蟲'),
    'QuickEnemy': ('快速怪', '快速怪'),
    'Ram': ('公羊', '公羊'),
    'Rat': ('老鼠', '老鼠'),
    'RatKing': ('鼠王', '鼠王'),
    'RedScorpion': ('红蝎', '紅蠍'),
    'Rooster': ('公鸡', '公雞'),
    'RoyalBoar': ('皇家野猪', '皇家野豬'),
    'SabretoothTiger': ('剑齿虎', '劍齒虎'),
    'Scarab': ('圣甲虫', '聖甲蟲'),
    'ScarabMounted': ('骑乘圣甲虫', '騎乘聖甲蟲'),
    'ShardLizard': ('碎片蜥蜴', '碎片蜥蜴'),
    'Sheep': ('绵羊', '綿羊'),
    'SlugQueen': ('蛞蝓女王', '蛞蝓女王'),
    'StrongEnemy': ('强敌', '強敵'),
    'Swine': ('壮猪', '壯豬'),
    'Tiger': ('老虎', '老虎'),
    'TreasureChest': ('宝箱', '寶箱'),
    'Troll': ('巨魔', '巨魔'),
    'Turkey': ('火鸡', '火雞'),
    'VolcanoParasite': ('熔岩寄生体', '熔岩寄生體'),
    'Warg': ('座狼', '座狼'),
    'Wasp': ('黄蜂', '黃蜂'),
    'Watchdog': ('看门犬', '看門犬'),
    'WhiteWolf': ('白狼', '白狼'),
    'WildGoat': ('野山羊', '野山羊'),
    'WildRooster': ('野公鸡', '野公雞'),
    'WinterBear': ('冬熊', '冬熊'),
    'WinterBoar': ('冬野猪', '冬野豬'),
    'WinterOgre': ('冬食人魔', '冬食人魔'),
    'WinterWarg': ('冬座狼', '冬座狼'),
    'WinterWolfTypeA': ('冬狼·甲', '冬狼·甲'),
    'WinterWolfTypeB': ('冬狼·乙', '冬狼·乙'),
    'Wolf': ('狼', '狼'),
    'WolfHound': ('狼犬', '狼犬'),
    'WolfMounfed': ('狼骑', '狼騎'),
    'Zombie': ('丧尸', '喪屍'),
}


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def col_letter(i):
    s = ''
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def cell(ref, val):
    return '<c r="%s" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, esc(val))


def rows_of(path):
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    return d if isinstance(d, list) else d.get('data', [])


def used_monster_names():
    """被 8 个关卡实际引用的怪物名集合（SceneInfo → Round → EnemyList → EnemyData）。"""
    rounds = {r.get('id'): r for r in rows_of(ROOT + '/Assets/ConfigJson/tbrounddata.json')}
    elists = {r.get('id'): r for r in rows_of(ROOT + '/Assets/ConfigJson/tbenemylist.json')}
    enemies = {r.get('id'): r.get('name', '') for r in rows_of(ROOT + '/Assets/ConfigJson/tbenemydata.json')}
    used_ids = set()
    for sc in rows_of(ROOT + '/Assets/ConfigJson/tbsceneinfo.json'):
        for rid in sc.get('RoundList', []) or []:
            r = rounds.get(rid)
            if not r:
                continue
            for elid in r.get('EnemyIndexs', []) or []:
                e = elists.get(elid)
                if not e:
                    continue
                for eid in e.get('EnemyIndexs', []) or []:
                    used_ids.add(eid)
    return {enemies.get(i, '?%d' % i) for i in used_ids}


def append_localization():
    with zipfile.ZipFile(LOCALIZATION, 'r') as z:
        names = z.namelist()
        data = {n: z.read(n) for n in names}
    sheet_name = 'xl/worksheets/sheet1.xml'
    sheet = data[sheet_name].decode('utf-8')

    have = set()
    for row_m in re.finditer(r'<row r="(\d+)"[^>]*>(.*?)</row>', sheet, re.S):
        m = re.search(r'<c r="B\d+"[^>]*><is><t[^>]*>(.*?)</t></is></c>', row_m.group(2), re.S)
        if m:
            have.add(m.group(1).replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>'))

    todo = [k for k in sorted(MONSTER_NAMES) if k not in have]
    if not todo:
        print('[loc] 怪物名词条均已存在，无需追加')
        return

    max_row = 0
    for m in re.finditer(r'<row r="(\d+)"', sheet):
        max_row = max(max_row, int(m.group(1)))
    print('[loc] 现有词条 %d，待追加怪物名 %d 条（行 %d 起）' % (len(have), len(todo), max_row + 1))

    rows_xml = []
    ri = max_row
    for key in todo:
        zh_hans, zh_hant = MONSTER_NAMES[key]
        ri += 1
        full = (key, key, zh_hans, zh_hant, '怪物名（关卡详情的"本关出现怪物"列表）')
        rows_xml.append('<row r="%d">' % ri + ''.join(
            cell(col_letter(ci + 1) + str(ri), v) for ci, v in enumerate(full)) + '</row>')

    sheet_new = sheet.replace('</sheetData>', ''.join(rows_xml) + '</sheetData>')
    if sheet_new == sheet:
        raise SystemExit('[loc] 未找到 </sheetData>，表格式不符，中止')

    shutil.copyfile(LOCALIZATION, LOCALIZATION + '.bak_20261016_monsters')
    data[sheet_name] = sheet_new.encode('utf-8')
    with zipfile.ZipFile(LOCALIZATION, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.writestr(n, data[n])
    print('[loc] 已写入', LOCALIZATION, '（新增 %d 条）' % len(todo))


def patch_tower_names():
    RENAME = {
        'NormalTower': 'Normal Tower',
        'PowerTower': 'Blast Tower',
        'RetardTower': 'Frost Tower',
    }
    with zipfile.ZipFile(TOWERINFO, 'r') as z:
        names = z.namelist()
        data = {n: z.read(n) for n in names}
    sheet_name = 'xl/worksheets/sheet1.xml'
    sheet = data[sheet_name].decode('utf-8')

    changed = 0
    for old, new in RENAME.items():
        # 仅替换 D 列（name）单元格内的值，防误伤其它列
        pattern = r'(<c r="D\d+"[^>]*><is><t[^>]*>)' + old + r'(</t></is></c>)'
        sheet, n = re.subn(pattern, r'\g<1>' + new + r'\g<2>', sheet)
        changed += n

    if changed == 0:
        print('[tower] name 列无需修改（可能已改过）')
        return
    shutil.copyfile(TOWERINFO, TOWERINFO + '.bak_20261016_names')
    data[sheet_name] = sheet.encode('utf-8')
    with zipfile.ZipFile(TOWERINFO, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.writestr(n, data[n])
    print('[tower] 已修正 name 列 %d 处：%s' % (changed, RENAME))


def main():
    used = used_monster_names()
    missing = sorted(used - set(MONSTER_NAMES))
    print('关卡实际引用怪物名 %d 个；词条表覆盖 %d 个' % (len(used), len(set(used) & set(MONSTER_NAMES))))
    if missing:
        print('!! 以下被引用怪物缺翻译（需补进 MONSTER_NAMES）：')
        for m in missing:
            print('   ', m)
        raise SystemExit('覆盖率校验未通过，中止（防漏翻）')
    print('覆盖率校验通过（无遗漏）')

    append_localization()
    patch_tower_names()
    print()
    print('完成。下一步：Unity 菜单「Tools ▸ 塔防 ▸ 3. 导出配置表（Luban）」重导。')


if __name__ == '__main__':
    main()
