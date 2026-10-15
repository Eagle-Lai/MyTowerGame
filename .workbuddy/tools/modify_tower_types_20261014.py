# -*- coding: utf-8 -*-
"""2026-10-14 防御塔三塔型收敛：修改 Luban 配置表。

- TowerInfo.xlsx：删 type=4(穿透)/5(激光) 全部行；type=2(火力) 行 canAttackAir 1→0；
  表头图例同步更新。
- BulletData.xlsx：删穿透弹(id=3)行；删 pierce 列；effectType 图例去"4激光"。
- AudioData.xlsx：删 sfx_tower_fire_pierce / sfx_tower_fire_laser 两行。

幂等：重复执行无副作用。执行前自动备份到 .workbuddy/backup/tower3types_20261014/。
"""
import openpyxl, os, shutil, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATAS = r'D:/FreedomTower_1/Luban/Config/Datas'
BACKUP = r'D:/FreedomTower_1/.workbuddy/backup/tower3types_20261014'

FILES = ['TowerInfo.xlsx', 'BulletData.xlsx', 'AudioData.xlsx', 'Localization.xlsx']
os.makedirs(BACKUP, exist_ok=True)
for f in FILES:
    src = os.path.join(DATAS, f)
    dst = os.path.join(BACKUP, f)
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
        print('[backup]', f, '->', dst)


def header_map(ws):
    """row1 表头名 -> 列号（1-based）。"""
    m = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(row=1, column=c).value
        if v is not None:
            m[str(v).strip()] = c
    return m


def s(v):
    return '' if v is None else str(v).strip()


# ---------------------------------------------------------------- TowerInfo
p = os.path.join(DATAS, 'TowerInfo.xlsx')
wb = openpyxl.load_workbook(p)
ws = wb.worksheets[0]
hm = header_map(ws)
type_col, id_col, air_col, eff_col = hm['type'], hm['id'], hm['canAttackAir'], hm['effectType']

del_rows = []
power_rows = []
for r in range(4, ws.max_row + 1):
    t = s(ws.cell(row=r, column=type_col).value)
    if t in ('4', '5'):
        del_rows.append(r)
    elif t == '2':
        power_rows.append(r)

for r in reversed(del_rows):
    ws.delete_rows(r, 1)
print('[TowerInfo] 删除 type=4/5 行数:', len(del_rows))

changed = 0
for r in power_rows:
    if s(ws.cell(row=r, column=air_col).value) == '1':
        ws.cell(row=r, column=air_col).value = 0
        changed += 1
print('[TowerInfo] 火力塔(type=2) canAttackAir 1->0 行数:', changed)

ws.cell(row=3, column=type_col).value = '类型 1普通/2火力(AOE)/3减速光环'
ws.cell(row=3, column=eff_col).value = '特殊效果类型 0无/1减速(光环)/2持续伤害/3范围伤害'
ws.cell(row=3, column=air_col).value = '是否可攻击飞行单位 0否/1是（留空视为 0。三塔型定案：普通1/火力0/减速1）'

left = {}
for r in range(4, ws.max_row + 1):
    t = s(ws.cell(row=r, column=type_col).value)
    if t:
        left[t] = left.get(t, 0) + 1
print('[TowerInfo] 收敛后按 type 行数:', left)
wb.save(p)

# --------------------------------------------------------------- BulletData
p = os.path.join(DATAS, 'BulletData.xlsx')
wb = openpyxl.load_workbook(p)
ws = wb.worksheets[0]
hm = header_map(ws)
id_col, pierce_col, eff_col = hm['id'], hm['pierce'], hm['effectType']

del_rows = [r for r in range(4, ws.max_row + 1) if s(ws.cell(row=r, column=id_col).value) == '3']
for r in reversed(del_rows):
    ws.delete_rows(r, 1)
print('[BulletData] 删除穿透弹行数:', len(del_rows))

if pierce_col:
    ws.delete_cols(pierce_col, 1)
    print('[BulletData] 已删除 pierce 列(第%d列)' % pierce_col)
hm = header_map(ws)
ws.cell(row=3, column=hm['effectType']).value = '效果类型 0无/1减速/2持续伤害/3范围伤害（命中时施加）'

left = [s(ws.cell(row=r, column=hm['id']).value) for r in range(4, ws.max_row + 1) if s(ws.cell(row=r, column=hm['id']).value)]
print('[BulletData] 收敛后子弹 id:', left, '| 表头字段:', [k for k in hm if k != '##'])
wb.save(p)

# ---------------------------------------------------------------- AudioData
p = os.path.join(DATAS, 'AudioData.xlsx')
wb = openpyxl.load_workbook(p)
ws = wb.worksheets[0]
hm = header_map(ws)
name_col = hm.get('logicalName')
if name_col is None:   # 兜底：找不到表头名就在所有列里找
    name_col = None
    for c in range(1, ws.max_column + 1):
        for r in range(1, 4):
            if s(ws.cell(row=r, column=c).value) == 'logicalName':
                name_col = c
                break
KILL = {'sfx_tower_fire_pierce', 'sfx_tower_fire_laser'}
del_rows = [r for r in range(2, ws.max_row + 1) if s(ws.cell(row=r, column=name_col).value) in KILL]
for r in reversed(del_rows):
    ws.delete_rows(r, 1)
print('[AudioData] 删除穿透/激光音效行数:', len(del_rows))
wb.save(p)

print('DONE')
