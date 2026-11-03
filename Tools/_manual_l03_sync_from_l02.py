# -*- coding: utf-8 -*-
"""
_manual_l03_sync_from_l02.py —— 把 L02 的数值方案按波次映射到 L03（一次性人工调表）

================================ 授权与边界 ================================
用户 2026-11-03 明确指令：「把关卡2的数值修改内容同步到关卡三」，并在追问中确认：
  · 整套 L02 方案；照抄 L02 绝对值（不是按 L03 现值乘倍率）；
  · 只改数值，不碰 SceneInfo；
  · 只改 L03；
  · 波次一一对应，按「同波次 + 同怪种 + 同地空」映射；L02 没有的 8 种怪
    （Chick / EvilEye / MohawkBat / QuickEnemy / DreadEye / Pig / LittleBunny /
    GreenParasite）保留 L03 原有设计，不动。

具体写入范围（只此三张表、只此几列）：
  1) L03/EnemyData.xlsx   `hp` 一列：能对上的行取 L02 同波同怪种绝对 hp；
  2) L03/EnemyList.xlsx   `EnemyIndexs`（每波出怪总数改为 L02 同波总数，构成沿用
                         L03 原有序列）+ `enemyInterval`（取 L02 同波值）；
  3) L03/RoundData.xlsx   `rewardGold`（取 L02 同波值）。
不改：SceneInfo / levelId / EnemyData 的 speed/armor/reward/damageToPlayer/scale/
      bodyRadius/isFlying/animController、RoundData 的 id/EnemyIndexs/name/waveType、
      LevelMap / LevelRules / TowerInfo / BulletData / WaveTuning / Global。

与 AGENTS.md「禁止脚本批量改写关卡配置表」的关系：
  禁令针对 balance_pipeline 那类面向全库的批量改写。本脚本是用户点名单关、单次、
  列明字段的人工调表工具，**不构成对其他列 / 其他关卡 / 后续批次的授权**；
  再跑一次前必须重新取得用户确认。

基线固定：首次 --apply 先把三张表复制为 `*.bak_20261103_before_l2sync`，
之后不再覆盖；回滚 = 三个 .bak 覆盖回去 + 重跑 Luban 导出。

用法：
    python Tools/_manual_l03_sync_from_l02.py --dry-run
    python Tools/_manual_l03_sync_from_l02.py --apply
    python Tools/_manual_l03_sync_from_l02.py --verify
"""

import argparse
import math
import re
import shutil
import sys
from collections import Counter, defaultdict

import openpyxl

BASE = "Luban/Config/Datas/Levels"
SRC = f"{BASE}/L02"
DST = f"{BASE}/L03"
BAK_SUFFIX = ".bak_20261103_before_l2sync"

WAVE_RE = re.compile(r"\bwave=(\d+)\b")
ROUND_RE = re.compile(r"第\s*(\d+)\s*/\s*(\d+)\s*波")
DATA_START = 4  # 1=## 2=##type 3=##desc 4=数据首行


# ----------------------------------------------------------------------------- io
def load(path):
    """返回 (workbook, sheet, header list, [(row_index, dict)])；用文件对象读，兼容 .bak_*。"""
    with open(path, "rb") as fh:
        wb = openpyxl.load_workbook(fh)
    ws = wb.worksheets[0]
    header = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    rows = []
    for r in range(DATA_START, ws.max_row + 1):
        rec = {}
        for c, h in enumerate(header, start=1):
            if h is not None:
                rec[h] = ws.cell(r, c).value
        if rec.get("id") is None:
            continue
        rows.append((r, rec))
    return wb, ws, header, rows


def wave_of(desc):
    m = WAVE_RE.search(str(desc or ""))
    return int(m.group(1)) if m else None


def round_no(name):
    m = ROUND_RE.search(str(name or ""))
    return int(m.group(1)) if m else None


def col_of(header, name):
    return header.index(name) + 1


# ------------------------------------------------------------------ 源表（L02）
def read_l02():
    _, _, ed_hdr, ed_rows = load(f"{SRC}/EnemyData.xlsx")
    hp = {}
    for _, rec in ed_rows:
        w = wave_of(rec.get("desc"))
        if w is None:
            continue
        hp[(w, rec["name"], int(rec["isFlying"]))] = float(rec["hp"])

    _, _, _, el_rows = load(f"{SRC}/EnemyList.xlsx")
    el = {int(rec["id"]): rec for _, rec in el_rows}

    _, _, _, rd_rows = load(f"{SRC}/RoundData.xlsx")
    waves = {}
    for _, rec in rd_rows:
        n = round_no(rec["name"])
        if n is None:
            continue
        list_id = int(str(rec["EnemyIndexs"]).split(",")[0])
        src_list = el[list_id]
        waves[n] = {
            "reward": int(rec["rewardGold"]),
            "count": len(str(src_list["EnemyIndexs"]).split(",")),
            "interval": float(src_list["enemyInterval"]),
        }
    assert len(waves) == 25, f"L02 波次不足 25：{sorted(waves)}"
    return hp, waves


# --------------------------------------------------------------- 编写目标表（L03）
def plan_enemy_hp(hp_src):
    """返回 {row_index: (old, new, key)}，同波同怪重复行只改 hp 最大的那条。"""
    _, _, _, rows = load(f"{DST}/EnemyData.xlsx")
    by_key = defaultdict(list)
    for r, rec in rows:
        w = wave_of(rec.get("desc"))
        if w is None:
            continue
        by_key[(w, rec["name"], int(rec["isFlying"]))].append((r, float(rec["hp"])))

    plan, skipped = {}, []
    for key, items in by_key.items():
        if key not in hp_src:
            continue
        items.sort(key=lambda t: t[1])
        for r, old in items[:-1]:          # 重复行里的非主行：保留 L03 原值
            skipped.append((key, r, old))
        r, old = items[-1]
        plan[r] = (old, hp_src[key], key)
    return plan, skipped, rows


def resample(seq, target):
    """按原序列等比取样/重复，保持顺序与构成比例，长度精确等于 target。"""
    n = len(seq)
    if target == n:
        return list(seq)
    if target > n:
        return [seq[i % n] for i in range(target)]
    return [seq[int(i * n / target)] for i in range(target)]


def plan_spawns(waves_src):
    """返回 {row_index: dict(...)}，按 RoundData.name 定位波次，经 EnemyIndexs 找列表行。"""
    _, _, _, rd_rows = load(f"{DST}/RoundData.xlsx")
    _, _, el_hdr, el_rows = load(f"{DST}/EnemyList.xlsx")
    el_by_id = {int(rec["id"]): (r, rec) for r, rec in el_rows}

    plan = {}
    for _, rec in rd_rows:
        n = round_no(rec["name"])
        if n is None or n not in waves_src:
            continue
        list_id = int(str(rec["EnemyIndexs"]).split(",")[0])
        r, el = el_by_id[list_id]
        seq = [int(x) for x in str(el["EnemyIndexs"]).split(",")]
        target = waves_src[n]["count"]
        new_seq = resample(seq, target)
        plan[r] = {
            "wave": n,
            "list_id": list_id,
            "old_count": len(seq),
            "new_count": target,
            "new_text": ",".join(str(x) for x in new_seq),
            "old_interval": float(el["enemyInterval"]),
            "new_interval": waves_src[n]["interval"],
            "old_desc": el["desc"],
        }
    return plan


def plan_rewards(waves_src):
    _, _, _, rd_rows = load(f"{DST}/RoundData.xlsx")
    plan = {}
    for r, rec in rd_rows:
        n = round_no(rec["name"])
        if n in waves_src:
            plan[r] = (n, int(rec["rewardGold"]), waves_src[n]["reward"])
    return plan


# ------------------------------------------------------------------------- 主流程
def report(hp_plan, skipped, hp_rows, spawn_plan, reward_plan):
    print("=" * 78)
    print("L03 ← L02 数值同步（预演）")
    print("=" * 78)
    print(f"\n[1] EnemyData.hp：改 {len(hp_plan)} 行 / 共 {len(hp_rows)} 行")
    by_wave = Counter(k[0] for _, _, k in hp_plan.values())
    print("    每波改动行数:", [by_wave.get(w, 0) for w in range(1, 26)])
    if skipped:
        print("    同波同怪重复行（保留 L03 原值）:")
        for key, r, old in skipped:
            print(f"      wave={key[0]} {key[1]} flying={key[2]} row{r} hp={old}")
    old_sum = sum(v[0] for v in hp_plan.values())
    new_sum = sum(v[1] for v in hp_plan.values())
    print(f"    这 {len(hp_plan)} 行 hp 合计 {old_sum:,.2f} → {new_sum:,.2f}")

    print(f"\n[2] EnemyList：改 {len(spawn_plan)} 波")
    total_old = sum(v["old_count"] for v in spawn_plan.values())
    total_new = sum(v["new_count"] for v in spawn_plan.values())
    print(f"    出怪总数 {total_old:,} → {total_new:,}")
    print("    逐波 旧→新:", [f'{spawn_plan[r]["old_count"]}→{spawn_plan[r]["new_count"]}'
                             for r in sorted(spawn_plan, key=lambda r: spawn_plan[r]["wave"])])
    print("    逐波 interval 旧→新:", [f'{spawn_plan[r]["old_interval"]:.0f}→{spawn_plan[r]["new_interval"]:.0f}'
                                      for r in sorted(spawn_plan, key=lambda r: spawn_plan[r]["wave"])])

    print(f"\n[3] RoundData.rewardGold：改 {len(reward_plan)} 波")
    old_r = sum(v[1] for v in reward_plan.values())
    new_r = sum(v[2] for v in reward_plan.values())
    print(f"    合计 {old_r:,} → {new_r:,}")
    print("    逐波 旧→新:", [f"{v[1]}→{v[2]}" for _, v in sorted(reward_plan.items())])


def apply(hp_plan, spawn_plan, reward_plan):
    paths = [f"{DST}/EnemyData.xlsx", f"{DST}/EnemyList.xlsx", f"{DST}/RoundData.xlsx"]
    for p in paths:
        bak = p + BAK_SUFFIX
        if not __import__("os").path.exists(bak):
            shutil.copy2(p, bak)
            print(f"  备份 {bak}")

    # EnemyData.hp
    wb, ws, hdr, _ = load(f"{DST}/EnemyData.xlsx")
    c = col_of(hdr, "hp")
    for r, (old, new, _k) in hp_plan.items():
        ws.cell(r, c).value = new
    wb.save(paths[0])

    # EnemyList
    wb, ws, hdr, _ = load(f"{DST}/EnemyList.xlsx")
    c_ids = col_of(hdr, "EnemyIndexs")
    c_iv = col_of(hdr, "enemyInterval")
    c_desc = col_of(hdr, "desc")
    for r, v in spawn_plan.items():
        ws.cell(r, c_ids).value = v["new_text"]
        ws.cell(r, c_iv).value = v["new_interval"]
        desc = str(v["old_desc"] or "")
        if "l02-sync-20261103" not in desc:
            ws.cell(r, c_desc).value = desc + " | l02-sync-20261103"
    wb.save(paths[1])

    # RoundData
    wb, ws, hdr, _ = load(f"{DST}/RoundData.xlsx")
    c_rw = col_of(hdr, "rewardGold")
    for r, (_n, _old, new) in reward_plan.items():
        ws.cell(r, c_rw).value = new
    wb.save(paths[2])
    print("  已写入三张表")


def verify(hp_plan, spawn_plan, reward_plan):
    ok = True
    # hp
    _, _, _, rows = load(f"{DST}/EnemyData.xlsx")
    cur = {r: rec for r, rec in rows}
    for r, (_old, new, key) in hp_plan.items():
        if abs(float(cur[r]["hp"]) - new) > 1e-9:
            ok = False
            print(f"  [FAIL] EnemyData row{r} {key} hp={cur[r]['hp']} 期望 {new}")
    # spawn
    _, _, _, rows = load(f"{DST}/EnemyList.xlsx")
    cur = {r: rec for r, rec in rows}
    for r, v in spawn_plan.items():
        n = len(str(cur[r]["EnemyIndexs"]).split(","))
        if n != v["new_count"]:
            ok = False
            print(f"  [FAIL] EnemyList row{r} 数量 {n} 期望 {v['new_count']}")
        if abs(float(cur[r]["enemyInterval"]) - v["new_interval"]) > 1e-9:
            ok = False
            print(f"  [FAIL] EnemyList row{r} interval {cur[r]['enemyInterval']}")
    # reward
    _, _, _, rows = load(f"{DST}/RoundData.xlsx")
    cur = {r: rec for r, rec in rows}
    for r, (_n, _old, new) in reward_plan.items():
        if int(cur[r]["rewardGold"]) != new:
            ok = False
            print(f"  [FAIL] RoundData row{r} reward {cur[r]['rewardGold']} 期望 {new}")
    print("  [OK] 目标格全部符合预期" if ok else "  [FAIL] 存在不符合项")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if not any((a.dry_run, a.apply, a.verify)):
        ap.print_help()
        return 1

    hp_src, waves_src = read_l02()
    hp_plan, skipped, hp_rows = plan_enemy_hp(hp_src)
    spawn_plan = plan_spawns(waves_src)
    reward_plan = plan_rewards(waves_src)

    report(hp_plan, skipped, hp_rows, spawn_plan, reward_plan)
    if a.dry_run:
        print("\n[dry-run] 未写盘")
        return 0
    if a.apply:
        print("\n[apply] 开始写盘")
        apply(hp_plan, spawn_plan, reward_plan)
    if a.verify:
        print("\n[verify]")
        return 0 if verify(hp_plan, spawn_plan, reward_plan) else 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
