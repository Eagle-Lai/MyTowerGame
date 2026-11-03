# -*- coding: utf-8 -*-
"""
_manual_l03_scale_unique.py —— L03 独有 8 种怪按「同波同地空基准」等比缩放（一次性人工调表）

================================ 授权与边界 ================================
用户 2026-11-03 12:43 明确同意「修改 L03 的 8 种怪物的数值」，承接上一轮
「L03 ← L02 数值同步」：共享怪种已照抄 L02 绝对值，本轮把 L02 没有的怪种
（Chick / EvilEye / MohawkBat / QuickEnemy / DreadEye / Pig / LittleBunny /
GreenParasite，以及 W25 重复行里保留原值的次行 Rat）拉到同一基准。

缩放口径（几何均值）：
  factor(wave, isFlying) = geomean( L02_hp / L03原hp )，样本只取「上一轮真正
  同步过的行」（即同波同怪种、且已取 L02 值的行）。该波该地空没有样本时，
  取最近有样本的波次（先向前、再向后），避免出现 W3/W4 空中留在 7.7、
  W5 突然 97.64 的断档。
  新 hp = 原 hp × factor，保留 3 位小数；desc 末尾追加来源标记。

不改：EnemyList / RoundData / SceneInfo / levelId / 及 EnemyData 其他列。
与 AGENTS.md 的关系：单次、单关、点名怪种的授权；不构成后续批次授权。

基线：`L03/EnemyData.xlsx.bak_20261103_before_scaleunique`（首跑自动生成）。

用法：
    python Tools/_manual_l03_scale_unique.py --dry-run
    python Tools/_manual_l03_scale_unique.py --apply
    python Tools/_manual_l03_scale_unique.py --verify
"""

import argparse
import math
import os
import re
import shutil
import sys
from collections import defaultdict

import openpyxl

BASE = "Luban/Config/Datas/Levels"
DST = f"{BASE}/L03"
SRC = f"{BASE}/L02"
PREV_BAK = f"{DST}/EnemyData.xlsx.bak_20261103_before_l2sync"
BAK = f"{DST}/EnemyData.xlsx.bak_20261103_before_scaleunique"
DATA_START = 4
WAVE_RE = re.compile(r"\bwave=(\d+)\b")
MARK = "l03-scale-20261103"


def load(path):
    with open(path, "rb") as fh:
        wb = openpyxl.load_workbook(fh)
    ws = wb.worksheets[0]
    hdr = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    rows = []
    for r in range(DATA_START, ws.max_row + 1):
        rec = {h: ws.cell(r, c).value for c, h in enumerate(hdr, start=1) if h}
        if rec.get("id") is None:
            continue
        rows.append((r, rec))
    return wb, ws, hdr, rows


def wave_of(rec):
    m = WAVE_RE.search(str(rec.get("desc") or ""))
    return int(m.group(1)) if m else None


def compute():
    _, _, _, cur_rows = load(f"{DST}/EnemyData.xlsx")
    _, _, _, bak_rows = load(PREV_BAK)
    _, _, _, l2_rows = load(f"{SRC}/EnemyData.xlsx")
    bak = {r: rec for r, rec in bak_rows}
    l2 = {(wave_of(x), x["name"], int(x["isFlying"])): float(x["hp"]) for _, x in l2_rows}

    cur = dict(cur_rows)
    pre = bak                                     # 同步前基线（.bak_..before_l2sync，不变）
    base = dict(load(BAK)[3]) if os.path.exists(BAK) else pre   # 缩放前基线，首跑时=pre
    changed, untouched = [], []
    for r in base:
        if abs(float(base[r]["hp"]) - float(pre[r]["hp"])) > 1e-9:
            changed.append(r)                     # 上一轮已取 L02 绝对值的行
        else:
            untouched.append(r)                   # 本轮要缩放的行

    samples = defaultdict(list)
    for r in changed:
        o = pre[r]
        k = (wave_of(o), o["name"], int(o["isFlying"]))
        samples[(k[0], k[2])].append(l2[k] / float(o["hp"]))

    factor = {}
    for w in range(1, 26):
        for f in (0, 1):
            rs = samples.get((w, f))
            factor[(w, f)] = math.exp(sum(math.log(x) for x in rs) / len(rs)) if rs else None
    # 缺样本的波次：先向前借、再向后借
    for w in range(1, 26):
        for f in (0, 1):
            if factor[(w, f)] is None:
                for d in range(1, 26):
                    for cand in (w - d, w + d):
                        if 1 <= cand <= 25 and factor.get((cand, f)) is not None:
                            factor[(w, f)] = factor[(cand, f)]
                            break
                    if factor[(w, f)] is not None:
                        break

    plan = {}
    for r in untouched:
        rec = base[r]
        k = (wave_of(rec), int(rec["isFlying"]))
        old = float(rec["hp"])
        plan[r] = {
            "old": old,
            "new": round(old * factor[k], 3),
            "factor": factor[k],
            "wave": k[0],
            "fly": k[1],
            "name": rec["name"],
            "desc": rec.get("desc") or "",
        }
    return plan, factor, len(cur_rows), len(changed)


def report(plan, factor, total, changed):
    print("=" * 78)
    print("L03 独有怪等比缩放（预演）")
    print("=" * 78)
    print(f"总行 {total}｜上一轮已同步 {changed} 行｜本轮缩放 {len(plan)} 行")
    print("逐波系数 地面:", [round(factor[(w, 0)], 2) for w in range(1, 26)])
    print("逐波系数 空中:", [round(factor[(w, 1)], 2) for w in range(1, 26)])
    by_name = defaultdict(list)
    for v in plan.values():
        by_name[v["name"]].append(v)
    print("\n按怪种：")
    for name in sorted(by_name):
        vs = by_name[name]
        olds = sorted({round(v["old"], 2) for v in vs})
        news = sorted({v["new"] for v in vs})
        print(f"  {name:14s} {len(vs):>3} 行  旧 {olds[0]}~{olds[-1]} → 新 {news[0]}~{news[-1]}")
    print("\nW5 / W25 明细：")
    for v in plan.values():
        if v["wave"] in (5, 25):
            print(f"  W{v['wave']:>2} {v['name']:14s} {'空' if v['fly'] else '地'} "
                  f"{v['old']:>10.2f} → {v['new']:>10.2f}  (×{v['factor']:.2f})")


def apply(plan):
    if not os.path.exists(BAK):
        shutil.copy2(f"{DST}/EnemyData.xlsx", BAK)
        print(f"  备份 {BAK}")
    wb, ws, hdr, rows = load(f"{DST}/EnemyData.xlsx")
    c_hp = hdr.index("hp") + 1
    c_desc = hdr.index("desc") + 1
    for r, v in plan.items():
        ws.cell(r, c_hp).value = v["new"]
        desc = v["desc"]
        if MARK not in desc:
            ws.cell(r, c_desc).value = desc + f" | {MARK} x{v['factor']:.2f}"
    wb.save(f"{DST}/EnemyData.xlsx")
    print("  已写入 EnemyData.xlsx")


def verify(plan):
    _, _, _, rows = load(f"{DST}/EnemyData.xlsx")
    cur = {r: rec for r, rec in rows}
    bad = 0
    for r, v in plan.items():
        if abs(float(cur[r]["hp"]) - v["new"]) > 1e-6:
            bad += 1
            print(f"  [FAIL] row{r} {v['name']} hp={cur[r]['hp']} 期望 {v['new']}")
    print(f"  [{'OK' if not bad else 'FAIL'}] {len(plan)} 行校验，异常 {bad} 行")
    return bad == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if not any((a.dry_run, a.apply, a.verify)):
        ap.print_help()
        return 1
    plan, factor, total, changed = compute()
    report(plan, factor, total, changed)
    if a.dry_run:
        print("\n[dry-run] 未写盘")
        return 0
    if a.apply:
        print("\n[apply] 写盘")
        apply(plan)
    if a.verify:
        print("\n[verify]")
        return 0 if verify(plan) else 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
