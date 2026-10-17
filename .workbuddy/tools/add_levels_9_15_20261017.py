# -*- coding: utf-8 -*-
"""
新增关卡 9~15 的完整配置（EnemyList / RoundData / SceneInfo），配合已有 LevelMap 9~15。

【为什么单独写一个脚本，而不是重跑 gen_m3_waves_rounds.py】
  那个脚本是"重排 1~40 波"的战役生成器，且 ROOT 写死了家用机路径 D:/FreedomTower_1。
  本次只**追加** 41~75 波 / 41~75 回合 / 9~15 关，绝不动 1~40 的既有平衡数据。

【难度口径】不重新造曲线，接着第 40 波（≈5.97 万有效血量）往后**低斜率**延伸：
    target(w) = 59681 * 1.008 ** (w - 40)
  这样第 75 波约 7.9 万，比第 8 关末波高约 30%，用 2600~3500 的初始金币承接，
  不会像"继续 1.101"那样在 75 波冲到 170 万（数学上必无解）。

【每关 5 回合，一回合 = 一波】L9=41~45, L10=46~50, … L15=71~75。
【地图事实】LevelMap 9~13 是全开阔直线图（0 障碍），14/15 各 3 格障碍 —— 描述按实际棋盘写。
"""
import datetime
import os
import shutil
import sys

import openpyxl

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_HERE = os.path.dirname(os.path.abspath(__file__))          # <根>/.workbuddy/tools
ROOT = os.path.dirname(os.path.dirname(_HERE))              # <根>
DATAS = os.path.join(ROOT, "Luban", "Config", "Datas")
BACKUP_ROOT = os.path.join(ROOT, ".workbuddy", "backup")

FIRST_DATA_ROW = 4

FIRST_WAVE = 41
LAST_WAVE = 75
WAVE_EHP_AT_40 = 59681.0     # 第 40 波的实际目标（与既有 desc 一致）
WAVE_GROWTH = 1.008
MAX_COUNT = 46
BOSSES = [129, 130, 131]
ELITE = 132

# 关卡号 -> (初始金币, 初始生命, 难度, 备注)  —— 备注按 LevelMap 里的真实棋盘写
NEW_LEVELS = {
    9:  (2600, 12, 3, "M9 新图：16×9 全开阔，S 右下 → E 中部偏上"),
    10: (2750, 12, 3, "M10 新图：16×9 全开阔，S 左上 → E 中右"),
    11: (2900, 12, 3, "M11 新图：16×9 全开阔，S 左上 → E 左下"),
    12: (3050, 12, 3, "M12 新图：16×9 全开阔，S 左下 → E 左上"),
    13: (3200, 12, 3, "M13 新图：16×9 全开阔，S 右下 → E 右上"),
    14: (3350, 12, 3, "M14 新图：17×9，中央 3 格横墙断开上下路"),
    15: (3500, 12, 3, "M15 新图：16×9，S 与 E 之间隔一格竖墙（3 格）"),
}


def header_map(ws):
    return {ws.cell(row=1, column=c).value: c for c in range(1, ws.max_column + 1)}


def last_data_row(ws, id_col):
    last = FIRST_DATA_ROW - 1
    for r in range(FIRST_DATA_ROW, ws.max_row + 1):
        if ws.cell(row=r, column=id_col).value is not None:
            last = r
    return last


def find_or_append_row(ws, id_col, target_id):
    """按 id 找行；没有就追加一行并写入 id。保证脚本可重复运行（重跑=覆盖，不重复追加）。"""
    last = FIRST_DATA_ROW - 1
    for r in range(FIRST_DATA_ROW, ws.max_row + 1):
        v = ws.cell(row=r, column=id_col).value
        if v is None:
            continue
        last = r
        if int(v) == target_id:
            return r
    r = last + 1
    ws.cell(row=r, column=id_col).value = target_id
    return r


def load_enemies():
    wb = openpyxl.load_workbook(os.path.join(DATAS, "EnemyData.xlsx"), data_only=True)
    ws = wb.active
    hdr = header_map(ws)
    rows = []
    for r in range(FIRST_DATA_ROW, ws.max_row + 1):
        eid = ws.cell(row=r, column=hdr["id"]).value
        if eid is None:
            continue
        eid = int(eid)
        hp = float(ws.cell(row=r, column=hdr["hp"]).value or 0)
        ar = float(ws.cell(row=r, column=hdr["armor"]).value or 0)
        rows.append((eid, hp / max(0.05, 1.0 - ar)))
    wb.close()
    return rows


def tiers_of(rows):
    normal = [x for x in rows if x[0] not in BOSSES and x[0] != ELITE]
    normal.sort(key=lambda x: x[1])
    n = len(normal)
    return [[e for e, _ in normal[i * n // 4:(i + 1) * n // 4]] for i in range(4)]


def build_wave(w, tiers, eff):
    """按目标有效血量填一波（末尾两关统一用最强档池子）。"""
    target = WAVE_EHP_AT_40 * (WAVE_GROWTH ** (w - 40))
    pool = tiers[3]

    ids, acc, i = [], 0.0, 0
    while acc < target and len(ids) < MAX_COUNT:
        eid = pool[(i * 7 + w * 3) % len(pool)]
        ids.append(eid)
        acc += eff[eid]
        i += 1

    if w % 2 == 0:
        ids.append(ELITE)
        acc += eff[ELITE]
    if w % 5 == 0:
        boss = BOSSES[(w // 5) % len(BOSSES)]
        ids.append(boss)
        acc += eff[boss]

    enemy_interval = max(170, 560 - 12 * ((w - 1) // 5) * 4 - 8 * ((w - 1) % 5))
    desc = "第 %d 波：%d 只 / 目标血量 %.0f（单怪间隔 %.2fs）" % (w, len(ids), target, enemy_interval / 1000.0)
    return ids, enemy_interval, desc


def main():
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_ROOT, stamp, "Config", "Datas")
    os.makedirs(dst, exist_ok=True)
    for n in ("EnemyList.xlsx", "RoundData.xlsx", "SceneInfo.xlsx"):
        shutil.copy2(os.path.join(DATAS, n), os.path.join(dst, n))
    print("已备份到:", dst)

    enemies = load_enemies()
    tiers = tiers_of(enemies)
    eff = {e: v for e, v in enemies}
    print("敌人四档规模:", [len(t) for t in tiers])

    # ---------- EnemyList：追加 41~75 ----------
    path = os.path.join(DATAS, "EnemyList.xlsx")
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    hdr = header_map(ws)
    for w in range(FIRST_WAVE, LAST_WAVE + 1):
        ids, ei, desc = build_wave(w, tiers, eff)
        row = find_or_append_row(ws, hdr["id"], w)
        ws.cell(row=row, column=hdr["id"]).value = w
        ws.cell(row=row, column=hdr["EnemyIndexs"]).value = ",".join(str(x) for x in ids)
        ws.cell(row=row, column=hdr["interval"]).value = 3000
        ws.cell(row=row, column=hdr["enemyInterval"]).value = ei
        ws.cell(row=row, column=hdr["desc"]).value = desc
    wb.save(path)
    print("EnemyList：已写入 %d~%d 波" % (FIRST_WAVE, LAST_WAVE))

    # ---------- RoundData：追加 41~75（一回合引用同号波次）----------
    path = os.path.join(DATAS, "RoundData.xlsx")
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    hdr = header_map(ws)
    for rnd in range(FIRST_WAVE, LAST_WAVE + 1):
        row = find_or_append_row(ws, hdr["id"], rnd)
        ws.cell(row=row, column=hdr["id"]).value = rnd
        ws.cell(row=row, column=hdr["EnemyIndexs"]).value = str(rnd)
        ws.cell(row=row, column=hdr["interval"]).value = 1500
        ws.cell(row=row, column=hdr["name"]).value = "第 %d 回合" % rnd
        ws.cell(row=row, column=hdr["rewardGold"]).value = 30 + 4 * (rnd - 1)
    wb.save(path)
    print("RoundData：已写入 %d~%d 回合" % (FIRST_WAVE, LAST_WAVE))

    # ---------- SceneInfo：9~15 关 ----------
    path = os.path.join(DATAS, "SceneInfo.xlsx")
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    hdr = header_map(ws)
    id_c = hdr["id"]

    # 第 8 关那一行做模板：D~I 是废弃的 3D 字段（viewport 类型仍在），照抄最省事
    template = None
    for rr in range(FIRST_DATA_ROW, ws.max_row + 1):
        v = ws.cell(row=rr, column=id_c).value
        if v is not None and int(v) == 8:
            template = rr
            break
    if template is None:
        raise SystemExit("SceneInfo.xlsx 里找不到第 8 关，无法取模板行")

    def cell(rid):
        return ws.cell(row=template, column=hdr[rid]).value

    for lid in sorted(NEW_LEVELS):
        gold, hp, diff, desc = NEW_LEVELS[lid]
        rounds = list(range((lid - 9) * 5 + 41, (lid - 9) * 5 + 46))
        r = None
        for rr in range(FIRST_DATA_ROW, ws.max_row + 1):
            v = ws.cell(row=rr, column=id_c).value
            if v is not None and int(v) == lid:
                r = rr
                break
        if r is None:
            r = last_data_row(ws, id_c) + 1
        ws.cell(row=r, column=hdr["id"]).value = lid
        ws.cell(row=r, column=hdr["RoundList"]).value = ",".join(str(x) for x in rounds)
        ws.cell(row=r, column=hdr["CameraPosition"]).value = cell("CameraPosition")
        ws.cell(row=r, column=hdr["CameraRotration"]).value = cell("CameraRotration")
        ws.cell(row=r, column=hdr["MapName"]).value = cell("MapName")
        ws.cell(row=r, column=hdr["EenemyPosition"]).value = cell("EenemyPosition")
        ws.cell(row=r, column=hdr["MapPosition"]).value = cell("MapPosition")
        ws.cell(row=r, column=hdr["PointScale"]).value = cell("PointScale")
        ws.cell(row=r, column=hdr["name"]).value = "关卡 %d" % lid
        ws.cell(row=r, column=hdr["mapId"]).value = lid
        ws.cell(row=r, column=hdr["initialGold"]).value = gold
        ws.cell(row=r, column=hdr["initialHp"]).value = hp
        ws.cell(row=r, column=hdr["waveIntervalMs"]).value = 3000
        ws.cell(row=r, column=hdr["nightSightMs"]).value = 0
        ws.cell(row=r, column=hdr["difficulty"]).value = diff
        ws.cell(row=r, column=hdr["desc"]).value = desc
    wb.save(path)
    print("SceneInfo：已写入 9~15 关（每关 5 回合）")

    # ---------- 自检 ----------
    wb = openpyxl.load_workbook(os.path.join(DATAS, "LevelMap.xlsx"), data_only=True)
    ws = wb.active
    h = header_map(ws)
    map_ids = set()
    for rr in range(FIRST_DATA_ROW, ws.max_row + 1):
        v = ws.cell(row=rr, column=h["id"]).value
        if v is not None:
            map_ids.add(int(v))
    wb.close()

    print("\n【自检】")
    print("  关卡  mapId对齐  回合区间     首/末波目标血量   金币  生命")
    for lid in sorted(NEW_LEVELS):
        gold, hp, diff, _ = NEW_LEVELS[lid]
        rounds = list(range((lid - 9) * 5 + 41, (lid - 9) * 5 + 46))
        first = WAVE_EHP_AT_40 * (WAVE_GROWTH ** (rounds[0] - 40))
        last = WAVE_EHP_AT_40 * (WAVE_GROWTH ** (rounds[-1] - 40))
        ok = "OK" if lid in map_ids else "缺失!"
        print("   %2d    %-6s   %2d~%2d   %8.0f/%-8.0f  %4d  %2d"
              % (lid, ok, rounds[0], rounds[-1], first, last, gold, hp))


if __name__ == "__main__":
    main()
