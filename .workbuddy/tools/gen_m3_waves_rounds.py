# -*- coding: utf-8 -*-
"""
M3-2：8 关战役的完整编排（TBEnemyList 40 波 + TBRoundData 40 回合 + TBSceneInfo 8 关）。

【为什么要重排全部 40 波，而不是只补 13~40】
  实测发现两代波次数据在强度上互相穿插（沿用 M1 的 1~12 波与新建的 13~40 波）：
    波 10 = 53586，波 13 = 3281，波 21 = 8326，波 12 = 68830 …
  按这个顺序切关卡，难度曲线怎么切都是非单调的。
  根因是 M1 的 1~12 波当初是为"**累积引用**的回合"设计的（回合 r 重放 1..r 波），
  单看每一波就已经很大；而新波次是"一波一回合"。两套口径混在一起必然打架。

【本版口径：目标血量法】
  先给出一条**几何递增的目标有效血量曲线**，再按目标去"填"每一波的敌人：
      target(w) = BASE * GROWTH ** (w - 1)
  这样曲线是**构造出来**的，而不是"填完再看运气"。
  敌人从与该波档位匹配的池子里轮取，累加到目标为止 —— 于是：
    · 难度单调可控；· 出怪数自然随强度增长（强怪少、弱怪多）。

【关卡划分】每关 5 个回合，共 40 回合：
  L1 = 1~5, L2 = 6~10, …, L8 = 36~40。关卡 N 用棋盘 N。
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

# 【这两个数是怎么定的】先按 1.118 生成，再用 balance_sim 反查：
#   末关最后一波 12.7 万有效血量，而该关摆满也只能提供约 3300 DPS → 余量 0.09，数学上无解。
#   于是把增长率压到 1.101（末波约 6.1 万），并让 initialGold 随关卡增长（见 _LV_META），
#   使"金币够不够"与"位置够不够"两个约束都留出余量。定完必须回跑 balance_sim 复核。
BASE_EHP = 1400.0        # 第 1 波的目标有效血量
GROWTH = 1.101           # 每波目标血量的几何增长率（→ 第 40 波约 6.1 万）
MAX_COUNT = 46           # 单波敌人上限，防止弱怪把屏幕塞满

BOSSES = [129, 130, 131]
ELITE = 132

# 关卡 → (回合区间, 初始金币, 初始生命, 难度标签, 说明)
LEVELS = []
# (初始金币, 初始生命, 难度标签, 说明)
# 【初始金币为什么必须随关卡增长】每关是**独立经济**（从头攒钱，不跨关继承），
# 而敌人强度按几何曲线涨。金币若还是 100 出头，玩家在关卡 5 之后连 4 座塔都买不起，
# 再高的位置上限也没有意义 —— 实测正是这一点让 3~8 关全部无解。
_LV_META = [
    (100, 20, 1, "开阔棋盘：把路让给玩家自己塑造"),
    (220, 20, 1, "双障碍夹出中段窄口"),
    (380, 20, 1, "厚横墙：好建位变少"),
    (600, 18, 2, "双交错横墙，S 形走位"),
    (900, 18, 2, "中央大块障碍，贴路可建位稀缺"),
    (1300, 15, 2, "井字街区，内侧位置差"),
    (1800, 15, 3, "密集障碍，可建位少、容错低"),
    (2400, 12, 3, "终盘：障碍最密，可建位最少"),
]
for i, (gold, hp, diff, note) in enumerate(_LV_META):
    LEVELS.append((i + 1, list(range(i * 5 + 1, i * 5 + 6)), gold, hp, diff, "关卡 %d：%s" % (i + 1, note)))


def load_enemies():
    wb = openpyxl.load_workbook(os.path.join(DATAS, "EnemyData.xlsx"), data_only=True)
    ws = wb.active
    hdr = {ws.cell(row=1, column=c).value: c for c in range(1, ws.max_column + 1)}
    rows = []
    for r in range(4, ws.max_row + 1):
        eid = ws.cell(row=r, column=hdr["id"]).value
        if eid is None:
            continue
        eid = int(eid)
        hp = float(ws.cell(row=r, column=hdr["hp"]).value or 0)
        ar = float(ws.cell(row=r, column=hdr["armor"]).value or 0)
        rows.append((eid, hp / max(0.05, 1.0 - ar)))
    return rows


def tiers_of(rows):
    """把非 Boss / 非精英的敌人按有效血量分 4 档。"""
    normal = [x for x in rows if x[0] not in BOSSES and x[0] != ELITE]
    normal.sort(key=lambda x: x[1])
    n = len(normal)
    return [[e for e, _ in normal[i * n // 4:(i + 1) * n // 4]] for i in range(4)]


def eff_map(rows):
    return {e: v for e, v in rows}


def build_wave(w, tiers, eff):
    """按目标有效血量"填"出一波敌人。"""
    target = BASE_EHP * (GROWTH ** (w - 1))
    tier_idx = min(3, (w - 1) // 5 // 2)      # 每 2 关（10 波）升一档，末尾封顶 3
    pool = tiers[tier_idx]

    ids = []
    acc = 0.0
    i = 0
    while acc < target and len(ids) < MAX_COUNT:
        eid = pool[(i * 7 + w * 3) % len(pool)]
        ids.append(eid)
        acc += eff[eid]
        i += 1

    # 精英：从第 3 关（波 11）起，每波有概率掺一个
    if w >= 11 and w % 2 == 0:
        ids.append(ELITE)
        acc += eff[ELITE]
    # Boss：第 4 关起，每关（5 波）的最后一波登场，且随关卡升级
    if w >= 16 and w % 5 == 0:
        boss = BOSSES[min(2, (w // 5) - 4)]
        ids.append(boss)
        acc += eff[boss]

    enemy_interval = max(170, 560 - 12 * ((w - 1) // 5) * 4 - 8 * ((w - 1) % 5))
    desc = "第 %d 波：%d 只 / 目标血量 %.0f（单怪间隔 %.2fs）" % (w, len(ids), target, enemy_interval / 1000.0)
    return ids, enemy_interval, desc, acc


def main():
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_ROOT, stamp, "Config", "Datas")
    os.makedirs(dst, exist_ok=True)
    for n in ("EnemyList.xlsx", "RoundData.xlsx", "SceneInfo.xlsx"):
        shutil.copy2(os.path.join(DATAS, n), os.path.join(dst, n))
    print("已备份到:", dst)

    rows = load_enemies()
    tiers = tiers_of(rows)
    eff = eff_map(rows)
    print("敌人四档规模:", [len(x) for x in tiers])

    # ---------- EnemyList：重排 1~40 ----------
    wb = openpyxl.load_workbook(os.path.join(DATAS, "EnemyList.xlsx"))
    ws = wb.active
    hdr = {ws.cell(row=1, column=c).value: c for c in range(1, ws.max_column + 1)}
    id_c = hdr["id"]
    got = {}
    for w in range(1, 41):
        ids, ei, desc, acc = build_wave(w, tiers, eff)
        got[w] = (len(ids), acc)
        r = None
        for rr in range(4, ws.max_row + 1):
            v = ws.cell(row=rr, column=id_c).value
            if v is not None and int(v) == w:
                r = rr
                break
        if r is None:
            r = ws.max_row + 1
        ws.cell(row=r, column=hdr["id"]).value = w
        ws.cell(row=r, column=hdr["EnemyIndexs"]).value = ",".join(str(x) for x in ids)
        ws.cell(row=r, column=hdr["interval"]).value = 3000
        ws.cell(row=r, column=hdr["enemyInterval"]).value = ei
        ws.cell(row=r, column=hdr["desc"]).value = desc
    wb.save(os.path.join(DATAS, "EnemyList.xlsx"))
    print("EnemyList：已重排 1~40 波")

    # ---------- RoundData：1~40，一回合引用同号波次 ----------
    wb = openpyxl.load_workbook(os.path.join(DATAS, "RoundData.xlsx"))
    ws = wb.active
    hdr = {ws.cell(row=1, column=c).value: c for c in range(1, ws.max_column + 1)}
    id_c = hdr["id"]
    for rnd in range(1, 41):
        r = None
        for rr in range(4, ws.max_row + 1):
            v = ws.cell(row=rr, column=id_c).value
            if v is not None and int(v) == rnd:
                r = rr
                break
        if r is None:
            r = ws.max_row + 1
        ws.cell(row=r, column=hdr["id"]).value = rnd
        ws.cell(row=r, column=hdr["EnemyIndexs"]).value = str(rnd)
        ws.cell(row=r, column=hdr["interval"]).value = 1500
        ws.cell(row=r, column=hdr["name"]).value = "第 %d 回合" % rnd
        ws.cell(row=r, column=hdr["rewardGold"]).value = 30 + 4 * (rnd - 1)
    wb.save(os.path.join(DATAS, "RoundData.xlsx"))
    print("RoundData：已重排 1~40 回合（一回合 = 一波）")

    # ---------- SceneInfo ----------
    wb = openpyxl.load_workbook(os.path.join(DATAS, "SceneInfo.xlsx"))
    ws = wb.active
    hdr = {ws.cell(row=1, column=c).value: c for c in range(1, ws.max_column + 1)}
    id_c = hdr["id"]
    for lid, rounds, gold, hp, diff, desc in LEVELS:
        r = None
        for rr in range(4, ws.max_row + 1):
            v = ws.cell(row=rr, column=id_c).value
            if v is not None and int(v) == lid:
                r = rr
                break
        if r is None:
            r = ws.max_row + 1
        ws.cell(row=r, column=hdr["id"]).value = lid
        ws.cell(row=r, column=hdr["mapId"]).value = lid
        ws.cell(row=r, column=hdr["RoundList"]).value = ",".join(str(x) for x in rounds)
        ws.cell(row=r, column=hdr["initialGold"]).value = gold
        ws.cell(row=r, column=hdr["initialHp"]).value = hp
        ws.cell(row=r, column=hdr["difficulty"]).value = diff
        ws.cell(row=r, column=hdr["name"]).value = "关卡 %d" % lid
        ws.cell(row=r, column=hdr["desc"]).value = desc
    wb.save(os.path.join(DATAS, "SceneInfo.xlsx"))
    print("SceneInfo：已分配 8 关（每关 5 回合）")

    # ---------- 自检 ----------
    print("\n【难度曲线自检】")
    print("  关卡  回合区间   单回合均量   首/末回合      金币  生命  难度")
    prev = None
    for lid, rounds, gold, hp, diff, _ in LEVELS:
        seg = [got[w][1] for w in rounds]
        per = sum(seg) / len(seg)
        mark = "" if prev is None else ("  ✔" if per > prev else "  ✘ 非单调")
        print("   %d    %2d~%2d    %9.0f   %7.0f/%7.0f  %5d %5d   %d%s"
              % (lid, rounds[0], rounds[-1], per, seg[0], seg[-1], gold, hp, diff, mark))
        prev = per


if __name__ == "__main__":
    main()
