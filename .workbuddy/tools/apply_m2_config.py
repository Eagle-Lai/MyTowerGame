# -*- coding: utf-8 -*-
"""
M2 配置表补齐脚本（多塔型 5 类 + 子弹特性 + 全局表现常数）。

【为什么用脚本而不是手改 Excel】
  1. 可复现、可 review、可回滚 —— 表结构变更最容易出"改漏一行"的问题；
  2. 备份是脚本的一部分，不依赖人的自觉；
  3. 与本工程既有约定一致（见 .workbuddy/tools/ 下的 gen_*.py / append_tower_rows.py）。

【改动清单】
  TowerInfo.xlsx
    - 追加 T 列 canAttackAir（是否可打飞行单位）
    - 修正 effectType 图例：0无 / 1减速 / 2持续伤害 / 3范围伤害 / 4激光
    - id 4~6（type=2 强力塔）→ 改为真正的 AOE 塔：bulletId 1→2，effectType 2→3
    - id 7~9（type=3 减速塔）→ bulletId 1→4（减速弹），effectType 保持 1
    - 新增 id 10~15：type=4 穿透塔 L1~L3、type=5 激光塔 L1~L3
  BulletData.xlsx
    - 修正 effectType 图例（同上）
    - 新增 id 2~5：爆炸弹 / 穿透弹 / 减速弹 / 腐蚀弹
  Global.xlsx
    - 追加 showDamageText / damageTextThrottleMs / shakeAmplitude / shakeDurationMs

【幂等性】重复执行结果一致（按 id 与列名定位，不按行号盲写）。
"""
import os
import shutil
import sys
import datetime

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")

ROOT = "D:/FreedomTower_1"
DATAS = os.path.join(ROOT, "Luban/Config/Datas")
BACKUP_ROOT = os.path.join(ROOT, ".workbuddy/backup")

TOWER_COLS = ["id", "type", "name", "resName", "level", "radius", "power", "CD",
              "prices", "bulletId", "targetMode", "searchIntervalMs", "rotateSpeed",
              "upgradeTo", "sellPrice", "effectType", "effectValue", "desc"]
BULLET_COLS = ["id", "name", "resName", "speed", "hitRadius", "lifeTimeMs", "pierce",
               "aoeRadius", "effectType", "effectValue", "scale", "desc"]
GLOBAL_COLS = ["id", "cellSize", "boardOriginPadding", "enemyPoolSize", "bulletPoolSize",
               "maxEnemyAlive", "defaultReward", "defaultDamageToPlayer", "defaultBodyRadius",
               "defaultSearchIntervalMs", "targetFrameRate", "deathRecycleDelayMs",
               "checkOfflinePerFrame", "showDebugLog", "autoNextRoundDelayMs",
               "autoStartRoundDelayMs", "sellRefundRate", "artFaceLeft"]

# effectType 统一图例（塔与子弹共用一套编号，避免两处各写一份解释）
EFFECT_LEGEND = "0无/1减速/2持续伤害/3范围伤害/4激光"


def backup():
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_ROOT, stamp, "Config", "Datas")
    os.makedirs(dst, exist_ok=True)
    for name in ("TowerInfo.xlsx", "BulletData.xlsx", "Global.xlsx"):
        src = os.path.join(DATAS, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dst, name))
    return dst


def open_wb(name):
    return openpyxl.load_workbook(os.path.join(DATAS, name))


def header_index(ws, col_name, header_row=1):
    """按列名定位列号（1 基）。比写死列号安全：以后插列不会错位。"""
    for c in range(1, ws.max_column + 2):
        v = ws.cell(row=header_row, column=c).value
        if v is not None and str(v).strip() == col_name:
            return c
    return None


def ensure_column(ws, col_name, type_text, comment):
    """确保某个字段列存在；不存在则追加到最后一列之后（同步写 ##/##type/说明 三行表头）。"""
    idx = header_index(ws, col_name)
    if idx is not None:
        ws.cell(row=3, column=idx).value = comment
        return idx
    idx = ws.max_column + 1
    ws.cell(row=1, column=idx).value = col_name
    ws.cell(row=2, column=idx).value = type_text
    ws.cell(row=3, column=idx).value = comment
    return idx


def row_by_id(ws, id_col, target):
    for r in range(4, ws.max_row + 1):
        v = ws.cell(row=r, column=id_col).value
        if v is not None and str(v).strip() == str(target):
            return r
    return None


def write_row(ws, cols, r, values):
    for name, val in values.items():
        c = header_index(ws, name)
        if c is None:
            raise RuntimeError("字段不存在：" + name)
        ws.cell(row=r, column=c).value = val


# ---------------------------------------------------------------- TowerInfo
def patch_tower():
    wb = open_wb("TowerInfo.xlsx")
    ws = wb.active

    id_c = header_index(ws, "id")
    eff_c = header_index(ws, "effectType")
    ws.cell(row=3, column=eff_c).value = "特殊效果类型 " + EFFECT_LEGEND
    air_c = ensure_column(ws, "canAttackAir", "int",
                          "是否可攻击飞行单位 0否/1是（缺省视为 1，兼容旧表）")

    # ① 现有 9 行：补 canAttackAir，并修正 AOE / 减速塔的子弹指向
    for r in range(4, 13):
        if ws.cell(row=r, column=id_c).value is None:
            continue
        ws.cell(row=r, column=air_c).value = 1

    # 强力塔（type=2）定位为 AOE：换成爆炸弹，效果类型标为「范围伤害」
    for tid in (4, 5, 6):
        r = row_by_id(ws, id_c, tid)
        write_row(ws, TOWER_COLS, r, {"bulletId": 2, "effectType": 3})

    # 减速塔（type=3）：换减速弹（子弹负责"做什么"，塔的 effectValue 负责"多强"）
    for tid in (7, 8, 9):
        r = row_by_id(ws, id_c, tid)
        write_row(ws, TOWER_COLS, r, {"bulletId": 4})

    # ② 新增穿透塔（type=4, id 10~12）与激光塔（type=5, id 13~15）
    #    resName 暂指向 Tower_Normal：美术未到位，行为完全由配置驱动，
    #    等美术补齐后只改这一格 + ResTable 两行，零代码。
    new_rows = [
        # id, type, name, level, radius, power, CD, prices, bulletId, upgradeTo, sellPrice, effectType
        (10, 4, "PierceTower", 1, 4, 6, 200, 30, 3, 11, 21, 0),
        (11, 4, "PierceTower", 2, 5, 8, 170, 45, 3, 12, 52, 0),
        (12, 4, "PierceTower", 3, 6, 11, 140, 65, 3, 0, 98, 0),
        (13, 5, "LaserTower", 1, 4, 14, 500, 40, 0, 14, 28, 4),
        (14, 5, "LaserTower", 2, 5, 18, 450, 60, 15, 70, 4, 4),
        (15, 5, "LaserTower", 3, 6, 24, 400, 80, 0, 0, 126, 4),
    ]
    # 上面的元组顺序易错，改为显式字典，避免"列错位"这类最难查的错
    new_rows = [
        dict(id=10, type=4, name="PierceTower", level=1, radius=4, power=6, CD=200,
             prices=30, bulletId=3, targetMode=0, searchIntervalMs=100, rotateSpeed=360,
             upgradeTo=11, sellPrice=21, effectType=0, effectValue=0,
             desc="穿透塔 L1：低伤高频，子弹可连续穿透多个敌人"),
        dict(id=11, type=4, name="PierceTower", level=2, radius=5, power=8, CD=170,
             prices=45, bulletId=3, targetMode=0, searchIntervalMs=100, rotateSpeed=360,
             upgradeTo=12, sellPrice=52, effectType=0, effectValue=0,
             desc="穿透塔 L2"),
        dict(id=12, type=4, name="PierceTower", level=3, radius=6, power=11, CD=140,
             prices=65, bulletId=3, targetMode=0, searchIntervalMs=100, rotateSpeed=360,
             upgradeTo=0, sellPrice=98, effectType=0, effectValue=0,
             desc="穿透塔 L3"),
        dict(id=13, type=5, name="LaserTower", level=1, radius=4, power=14, CD=500,
             prices=40, bulletId=0, targetMode=0, searchIntervalMs=100, rotateSpeed=360,
             upgradeTo=14, sellPrice=28, effectType=4, effectValue=0,
             desc="激光塔 L1：瞬发命中（hitscan），不发射弹体；bulletId=0 表示无子弹"),
        dict(id=14, type=5, name="LaserTower", level=2, radius=5, power=18, CD=450,
             prices=60, bulletId=0, targetMode=0, searchIntervalMs=100, rotateSpeed=360,
             upgradeTo=15, sellPrice=70, effectType=4, effectValue=0,
             desc="激光塔 L2"),
        dict(id=15, type=5, name="LaserTower", level=3, radius=6, power=24, CD=400,
             prices=80, bulletId=0, targetMode=0, searchIntervalMs=100, rotateSpeed=360,
             upgradeTo=0, sellPrice=126, effectType=4, effectValue=0,
             desc="激光塔 L3"),
    ]
    for spec in new_rows:
        r = row_by_id(ws, id_c, spec["id"])
        if r is None:
            r = ws.max_row + 1
            if ws.cell(row=r - 1, column=id_c).value is None and r > 4:
                r = r - 1
        values = dict(spec)
        values["resName"] = "Tower_Normal"   # 占位：美术到位后只改这一格
        values["canAttackAir"] = 1
        write_row(ws, TOWER_COLS, r, values)

    wb.save(os.path.join(DATAS, "TowerInfo.xlsx"))
    return "TowerInfo.xlsx：canAttackAir 列 + 6 行新塔 + AOE/减速子弹指向"


# ---------------------------------------------------------------- BulletData
def patch_bullet():
    wb = open_wb("BulletData.xlsx")
    ws = wb.active
    eff_c = header_index(ws, "effectType")
    ws.cell(row=3, column=eff_c).value = "效果类型 " + EFFECT_LEGEND + "（命中时施加）"

    bullets = [
        dict(id=2, name="爆炸弹", resName="Bullet_Normal", speed=12, hitRadius=0.25,
             lifeTimeMs=3000, pierce=0, aoeRadius=1.2, effectType=3, effectValue=0, scale=1.3,
             desc="AOE 塔专用：命中后对 aoeRadius 格内的其他敌人造成同等伤害"),
        dict(id=3, name="穿透弹", resName="Bullet_Normal", speed=18, hitRadius=0.22,
             lifeTimeMs=2500, pierce=3, aoeRadius=0, effectType=0, effectValue=0, scale=0.9,
             desc="穿透：pierce=3 表示命中后还能再穿 3 个敌人（共可打 4 个）"),
        dict(id=4, name="减速弹", resName="Bullet_Normal", speed=12, hitRadius=0.25,
             lifeTimeMs=3000, pierce=0, aoeRadius=0, effectType=1, effectValue=0.5, scale=1,
             desc="减速：effectValue=减速比例(0~1)。塔自身 effectValue>0 时会覆盖此值（减速塔三级各不相同）"),
        dict(id=5, name="腐蚀弹", resName="Bullet_Normal", speed=12, hitRadius=0.25,
             lifeTimeMs=3000, pierce=0, aoeRadius=0, effectType=2, effectValue=6, scale=1,
             desc="持续伤害：effectValue=每秒伤害，持续时长由代码常数 DotDurationSec 决定"),
    ]
    id_c = header_index(ws, "id")
    for b in bullets:
        r = row_by_id(ws, id_c, b["id"])
        if r is None:
            r = ws.max_row + 1
        write_row(ws, BULLET_COLS, r, b)

    wb.save(os.path.join(DATAS, "BulletData.xlsx"))
    return "BulletData.xlsx：新增 4 种子弹（爆炸/穿透/减速/腐蚀）"


# ---------------------------------------------------------------- Global
def patch_global():
    wb = open_wb("Global.xlsx")
    ws = wb.active
    ensure_column(ws, "showDamageText", "int", "是否显示伤害飘字 0否/1是")
    ensure_column(ws, "damageTextThrottleMs", "int",
                  "同一怪物两次伤害飘字的最小间隔（毫秒），防止高频攻击刷屏")
    ensure_column(ws, "shakeAmplitude", "float", "屏幕震动幅度（世界单位）；0=不震")
    ensure_column(ws, "shakeDurationMs", "int", "屏幕震动持续时间（毫秒）")

    r = row_by_id(ws, header_index(ws, "id"), 1)
    if r is None:
        r = 4
    for name, val in (("showDamageText", 1), ("damageTextThrottleMs", 120),
                      ("shakeAmplitude", 0.12), ("shakeDurationMs", 180)):
        ws.cell(row=r, column=header_index(ws, name)).value = val

    wb.save(os.path.join(DATAS, "Global.xlsx"))
    return "Global.xlsx：新增 4 个表现常数（飘字开关/节流、震动幅度/时长）"


if __name__ == "__main__":
    dst = backup()
    print("已备份到:", dst)
    print(patch_tower())
    print(patch_bullet())
    print(patch_global())
    print("OK")
