# -*- coding: utf-8 -*-
"""
_manual_l02_ground_w75.py —— L02 第 5~25 波「地面怪」血量改为当前值的 75%（一次性人工调表）

================================ 授权与边界 ================================
用户 2026-11-02 明确授权，**单次、单列、单关卡**：
  · 只写 Luban/Config/Datas/Levels/L02/EnemyData.xlsx 的 `hp` 一列；
  · 只作用于 desc 里 wave=5..25（含两端）且 isFlying=0 的记录（共 147 条）；
  · 不改 speed / armor / reward / damageToPlayer / scale / bodyRadius /
    isFlying / animController / desc / levelId；
  · 不改 EnemyList / RoundData / WaveTuning / SceneInfo / 其他关卡任何文件。
与 AGENTS.md「禁止脚本批量改写关卡配置表」的关系：
  禁令针对的是 balance_pipeline 那类**面向全库的批量改写**。本脚本是用户点名范围的
  一次性人工调表工具，**不构成对其他列/其他关卡/后续批次的授权**；
  再跑一次前必须重新取得用户确认。
===========================================================================

基线固定（避免"越跑越高"）：
  · 首次 --apply 时先把当前表复制为 `EnemyData.xlsx.bak_20261102_ground75`；
  · 之后每次 --apply 都以**该 .bak 的 hp 原值**为基线计算 75%，因此重复执行幂等；
  · .bak 一旦存在就不再覆盖，回滚直接复制回来即可。

用法：
    python Tools/_manual_l02_ground_w75.py --dry-run   # 只打印报告，不写盘
    python Tools/_manual_l02_ground_w75.py --apply     # 写入（首次自动备份）
    python Tools/_manual_l02_ground_w75.py --verify    # 对比基线，确认只改了目标格
"""

import argparse
import re
import shutil
import sys
from collections import defaultdict

import openpyxl

LEVEL_DIR = "Luban/Config/Datas/Levels/L02"
ENEMY_DATA = f"{LEVEL_DIR}/EnemyData.xlsx"
ENEMY_LIST = f"{LEVEL_DIR}/EnemyList.xlsx"
ROUND_DATA = f"{LEVEL_DIR}/RoundData.xlsx"
BASELINE = f"{ENEMY_DATA}.bak_20261102_ground75"

WAVE_MIN, WAVE_MAX = 5, 25
FACTOR = 0.75
DECIMALS = 6
LEVEL_ID = 2

WAVE_RE = re.compile(r"\bwave=(\d+)\b")
ROUND_NAME_RE = re.compile(r"第\s*(\d+)\s*/")


def load_grid(path):
    # 用文件对象读取：openpyxl 只按扩展名校验，读不了 .bak_* 备份
    with open(path, "rb") as fh:
        wb = openpyxl.load_workbook(fh, data_only=True)
    ws = wb["Sheet1"]
    rows = list(ws.iter_rows(values_only=True))
    header = [-1 if h is None else h for h in rows[0]]
    idx = {}
    for i, h in enumerate(header):
        if isinstance(h, str) and not h.startswith("##"):
            idx[h.strip()] = i
    return rows, idx


def wave_of(desc):
    m = WAVE_RE.search(desc or "")
    return int(m.group(1)) if m else None


def target_rows(rows, idx):
    """返回 [(excel_row_no, id, name, hp, wave)]，excel_row_no 为 1-based 真实行号。"""
    out = []
    for n, r in enumerate(rows[3:], start=4):
        if r is None or r[idx["id"]] is None:
            continue
        wave = wave_of(r[idx["desc"]])
        if wave is None or not (WAVE_MIN <= wave <= WAVE_MAX):
            continue
        if int(r[idx["isFlying"]] or 0) != 0:
            continue
        if int(r[idx["levelId"]] or 0) != LEVEL_ID:
            raise SystemExit(f"[abort] 行 {n} levelId != {LEVEL_ID}: {r[idx['levelId']]}")
        out.append((n, int(r[idx["id"]]), r[idx["name"]], float(r[idx["hp"]]), wave))
    return out


def cross_check(targets):
    """用 RoundData + EnemyList 交叉校验「波次 → 敌人 id 集合」是否与 desc 一致。"""
    rd_rows, rd_idx = load_grid(ROUND_DATA)
    el_rows, el_idx = load_grid(ENEMY_LIST)

    el_map = {}
    for r in el_rows[3:]:
        if r is None or r[el_idx["id"]] is None:
            continue
        el_map[int(r[el_idx["id"]])] = {int(x) for x in str(r[el_idx["EnemyIndexs"]]).split(",") if x.strip()}

    round_to_wave = {}
    for r in rd_rows[3:]:
        if r is None or r[rd_idx["id"]] is None:
            continue
        m = ROUND_NAME_RE.search(str(r[rd_idx["name"]] or ""))
        if not m:
            continue
        rid = int(r[rd_idx["id"]])
        wave = int(m.group(1))
        if wave in round_to_wave:
            raise SystemExit(f"[abort] RoundData 波次重名: {wave}")
        round_to_wave[wave] = rid

    # 判据（L02 现状）：
    #   · 出怪列表 list ⊆ 本波 desc 定义集合；
    #   · 所有地面定义必须都被 list 引用（地面怪不允许有未使用的孤儿定义）；
    #   · W5~W8 允许存在少量**未被引用**的空中定义（历史遗留），不算错误。
    ground_ids = defaultdict(set)
    all_ids = defaultdict(set)
    for _, eid, _, _, wave in targets:
        ground_ids[wave].add(eid)
    ed_rows, ed_idx = load_grid(ENEMY_DATA)
    for r in ed_rows[3:]:
        if r is None or r[ed_idx["id"]] is None:
            continue
        m = WAVE_RE.search(r[ed_idx["desc"]] or "")
        if m:
            all_ids[int(m.group(1))].add(int(r[ed_idx["id"]]))

    problems = []
    for wave in range(WAVE_MIN, WAVE_MAX + 1):
        rid = round_to_wave.get(wave)
        if rid is None:
            problems.append(f"W{wave}: RoundData 找不到该波")
            continue
        listed = el_map.get(rid)
        if listed is None:
            problems.append(f"W{wave}: EnemyList 缺 id={rid}")
            continue
        if not listed <= all_ids[wave]:
            problems.append(f"W{wave}: 出怪列表引用了不存在的定义 {sorted(listed - all_ids[wave])[:6]}")
        if not ground_ids[wave] <= listed:
            problems.append(f"W{wave}: 地面定义未被出怪列表引用 {sorted(ground_ids[wave] - listed)[:6]}")
    return problems


def report(targets):
    per = defaultdict(list)
    for _, _, name, hp, wave in targets:
        per[wave].append((name, hp))
    print(f"{'波次':<6}{'地面怪定义数':<14}{'原 hp（去重）':<46}{'改后 hp'}")
    for wave in sorted(per):
        vals = sorted({hp for _, hp in per[wave]})
        before = "/".join(f"{v:g}" for v in vals)
        after = "/".join(f"{round(v * FACTOR, DECIMALS):g}" for v in vals)
        print(f"W{wave:<5}{len(per[wave]):<14}{before:<46}{after}")
    total_before = sum(hp for _, _, _, hp, _ in targets)
    total_after = sum(round(hp * FACTOR, DECIMALS) for _, _, _, hp, _ in targets)
    print(f"\n合计 {len(targets)} 条地面怪定义；hp 总和 {total_before:,.3f} → {total_after:,.3f}（{total_after / total_before:.4f}）")


def read_baseline_hp(path=ENEMY_DATA):
    rows, idx = load_grid(path)
    return {int(r[idx["id"]]): float(r[idx["hp"]]) for r in rows[3:] if r is not None and r[idx["id"]] is not None}


def do_apply():
    rows, idx = load_grid(ENEMY_DATA)
    targets = target_rows(rows, idx)
    problems = cross_check(targets)
    if problems:
        for p in problems:
            print("[交叉校验] " + p)
        raise SystemExit("[abort] 波次与出怪表不一致，未写盘")

    import os

    if not os.path.exists(BASELINE):
        shutil.copy2(ENEMY_DATA, BASELINE)
        print(f"[baseline] 已生成固定基线 {BASELINE}")
    base_hp = read_baseline_hp(BASELINE)

    wb = openpyxl.load_workbook(ENEMY_DATA)
    ws = wb["Sheet1"]
    changed = 0
    for row_no, eid, name, cur_hp, wave in targets:
        if eid not in base_hp:
            raise SystemExit(f"[abort] 基线缺 id={eid}")
        new_hp = round(base_hp[eid] * FACTOR, DECIMALS)
        cell = ws.cell(row=row_no, column=idx["hp"] + 1)
        if cell.value != new_hp:
            cell.value = new_hp
            changed += 1
    wb.save(ENEMY_DATA)
    print(f"[apply] 目标 {len(targets)} 条，实际写入 {changed} 格 → {ENEMY_DATA}")


def do_verify():
    cur_rows, cur_idx = load_grid(ENEMY_DATA)
    base_rows, base_idx = load_grid(BASELINE)

    if len(cur_rows) != len(base_rows):
        raise SystemExit(f"[fail] 行数变化 {len(base_rows)} → {len(cur_rows)}")

    header = [h for h in base_rows[0]]
    cur_hp_col = cur_idx["hp"]
    base_hp_col = base_idx["hp"]

    changed_cells = []
    for n, (c, b) in enumerate(zip(cur_rows, base_rows), start=1):
        for col, (cv, bv) in enumerate(zip(c, b), start=1):
            if cv != bv:
                name = header[col - 1] if col - 1 < len(header) else f"col{col}"
                changed_cells.append((n, col, name, bv, cv))

    bad = [x for x in changed_cells if x[2] != "hp"]
    if bad:
        for x in bad[:10]:
            print(f"[越界改动] 行{x[0]} 列{x[2]}: {x[3]!r} → {x[4]!r}")
        raise SystemExit(f"[fail] 出现 {len(bad)} 个非 hp 列的改动")

    # 逐条校验：目标行必须正好是基线 × 0.75，非目标行必须原样
    targets = {eid: (row_no, wave) for row_no, eid, _, _, wave in target_rows(cur_rows, cur_idx)}
    target_rows_no = {row_no for row_no, _ in targets.values()}
    ok, wrong = 0, []
    for row_no, col, name, bv, cv in changed_cells:
        if row_no not in target_rows_no:
            wrong.append((row_no, bv, cv))
            continue
        if abs(cv - round(bv * FACTOR, DECIMALS)) > 1e-9:
            wrong.append((row_no, bv, cv))
        else:
            ok += 1
    if wrong:
        for w in wrong[:10]:
            print(f"[异常] 行{w[0]}: {w[1]} → {w[2]}")
        raise SystemExit(f"[fail] {len(wrong)} 个改动不符合 75% 口径")

    print(f"[verify] 仅 hp 列变化；{ok} 个目标格全部等于基线 × 0.75（{len(targets)} 条目标 id）")
    print(f"[verify] 非目标行 0 改动；总改动格数 {len(changed_cells)}")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--verify", action="store_true")
    a = ap.parse_args()

    if a.verify:
        do_verify()
        return

    rows, idx = load_grid(ENEMY_DATA)
    targets = target_rows(rows, idx)
    print(f"范围：L02 第 {WAVE_MIN}~{WAVE_MAX} 波（含两端），isFlying=0，共 {len(targets)} 条地面怪定义\n")
    report(targets)
    problems = cross_check(targets)
    print("\n交叉校验（RoundData + EnemyList）:", "通过" if not problems else "发现问题")
    for p in problems:
        print("  - " + p)
    if problems:
        raise SystemExit("[abort] 未写盘")

    if a.dry_run:
        print("\n[dry-run] 未写盘。")
    else:
        do_apply()
        print()
        do_verify()


if __name__ == "__main__":
    sys.exit(main())
