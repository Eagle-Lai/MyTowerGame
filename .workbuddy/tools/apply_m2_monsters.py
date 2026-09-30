# -*- coding: utf-8 -*-
"""
M2 怪物扩展（W4-1）：补 Boss 与高护甲精英，并编入后期波次。

【为什么补这几行】
  设计文档 §8 M2「怪物扩展」要求接入更多 TBEnemy 行：护甲、飞行(isFlying)、Boss。
  · 护甲：表里现有最高 0.40，缺"高护甲精英"这一档；
  · Boss：128 行里 type 全是 1/2/3，**没有一行 type=5**，Boss 玩法等于不存在；
  · 飞行：isFlying 已有 5 行为 1（无需改数据），代码侧在 W4-2 才接上。

【为什么编入第 10/11/12 波，而不是第 13/14/15 波】
  实测：RoundData 的 12 个回合只引用波次 1~12，
  波次 13/14/15 是**没有任何关卡会用到**的孤儿数据。把 Boss 放进那里等于没放。

【幂等性】按 id 定位，重复执行结果一致。
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

ENEMY_COLS = ["id", "speed", "hp", "name", "type", "interval", "resName", "armor",
              "reward", "damageToPlayer", "scale", "bodyRadius", "isFlying",
              "animController", "desc"]

# 新增怪物。type：1普通 / 2快速 / 3重甲 / 4飞行 / 5 Boss
NEW_ENEMIES = [
    dict(id=129, speed=1.2, hp=2500, name="RatKing", type=5, interval=100,
         resName="Enemy_RatKing", armor=0.35, reward=90, damageToPlayer=5,
         scale=1.4, bodyRadius=0.6, isFlying=0, animController="",
         desc="Boss 1：鼠王。首个真正的 Boss 行（type=5），血厚、带护甲、漏了扣 5 点生命"),
    dict(id=130, speed=1.0, hp=3800, name="BugQueen", type=5, interval=100,
         resName="Enemy_BugQueen", armor=0.45, reward=140, damageToPlayer=8,
         scale=1.5, bodyRadius=0.7, isFlying=0, animController="",
         desc="Boss 2：虫后。护甲 0.45，必须靠高单发伤害（强力塔/激光塔）才打得动"),
    dict(id=131, speed=0.9, hp=5200, name="MossQueen", type=5, interval=100,
         resName="Enemy_MossQueen", armor=0.5, reward=200, damageToPlayer=10,
         scale=1.6, bodyRadius=0.75, isFlying=0, animController="",
         desc="Boss 3：苔藓女王。终盘 Boss，护甲 0.5 使纯靠数量的小塔几乎无效"),
    dict(id=132, speed=0.9, hp=1500, name="Ironclad", type=3, interval=100,
         resName="Enemy_Dreadnought", armor=0.65, reward=40, damageToPlayer=3,
         scale=0.9, bodyRadius=0.5, isFlying=0, animController="",
         desc="高护甲精英：护甲 0.65 是当前全表最高档，专门用来验证护甲减伤链路"),
]

# 波次 → 追加的怪物 id（必须落在 RoundData 真正引用到的波次 1~12 上）
WAVE_APPEND = {
    10: [129],
    11: [129, 130],
    12: [129, 130, 131, 132],
}


def backup(files):
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_ROOT, stamp, "Config", "Datas")
    os.makedirs(dst, exist_ok=True)
    for name in files:
        src = os.path.join(DATAS, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dst, name))
    return dst


def header_index(ws, col_name, header_row=1):
    for c in range(1, ws.max_column + 2):
        v = ws.cell(row=header_row, column=c).value
        if v is not None and str(v).strip() == col_name:
            return c
    return None


def row_by_id(ws, id_col, target):
    for r in range(4, ws.max_row + 1):
        v = ws.cell(row=r, column=id_col).value
        if v is not None and str(v).strip() == str(target):
            return r
    return None


def patch_enemy():
    wb = openpyxl.load_workbook(os.path.join(DATAS, "EnemyData.xlsx"))
    ws = wb.active
    id_c = header_index(ws, "id")

    added = 0
    for spec in NEW_ENEMIES:
        r = row_by_id(ws, id_c, spec["id"])
        if r is None:
            r = ws.max_row + 1
        for name, val in spec.items():
            ws.cell(row=r, column=header_index(ws, name)).value = val
        added += 1

    wb.save(os.path.join(DATAS, "EnemyData.xlsx"))
    return "EnemyData.xlsx：新增 %d 行（3 Boss + 1 高护甲精英）" % added


def patch_waves():
    wb = openpyxl.load_workbook(os.path.join(DATAS, "EnemyList.xlsx"))
    ws = wb.active
    id_c = header_index(ws, "id")
    idx_c = header_index(ws, "EnemyIndexs")
    # 【易错点】不能用写死的列号：本表列序是 ##/id/EnemyIndexs/interval/enemyInterval/desc，
    # 之前误把第 3 列（EnemyIndexs）当成 interval，直接把整串敌人 id 拿去转 float。
    in_c = header_index(ws, "interval")
    ei_c = header_index(ws, "enemyInterval")
    desc_c = header_index(ws, "desc")

    msgs = []
    for wave_id, extra in WAVE_APPEND.items():
        r = row_by_id(ws, id_c, wave_id)
        if r is None:
            msgs.append("波次 %d 不存在，跳过" % wave_id)
            continue
        cur = str(ws.cell(row=r, column=idx_c).value or "").strip()
        ids = [x for x in cur.split(",") if x.strip()] if cur else []
        for e in extra:
            if str(e) not in ids:          # 幂等：已经加过就不重复加
                ids.append(str(e))
        ws.cell(row=r, column=idx_c).value = ",".join(ids)

        interval = ws.cell(row=r, column=in_c).value or 0
        enemy_interval = ws.cell(row=r, column=ei_c).value or 0
        kinds = len(set(ids))
        ws.cell(row=r, column=desc_c).value = (
            "第 %d 波：%d 只 / %d 种（间隔 %.1fs / %.2fs）★含 Boss"
            % (wave_id, len(ids), kinds, float(interval) / 1000.0, float(enemy_interval) / 1000.0))
        msgs.append("波次 %d：%d 只（含 Boss %s）" % (wave_id, len(ids), extra))

    wb.save(os.path.join(DATAS, "EnemyList.xlsx"))
    return "EnemyList.xlsx：" + "；".join(msgs)


if __name__ == "__main__":
    print("已备份到:", backup(["EnemyData.xlsx", "EnemyList.xlsx"]))
    print(patch_enemy())
    print(patch_waves())
    print("OK")
