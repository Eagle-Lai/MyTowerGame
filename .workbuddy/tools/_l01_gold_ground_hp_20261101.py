#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性手工改表（L01 专用，2026-11-01 用户口径）。

两项改动，**只作用于第一关**：
  1) 波次通关奖励 RoundData.rewardGold：25 波各 +5；W5/W10/W15/W20 在此基础上再 +15（即 +20）。
  2) 地面单位血量 EnemyData.hp：W6-W24 中**除 W10/W15/W20** 的 16 个波次，地面变体（isFlying=0）各 ×1.12。
其余数值一律不动（含 W1-W5、W10/W15/W20/W25 的血量、全部空军、击杀奖励、数量、出怪间隔）。

★ 关键坑：RoundData.xlsx 的**物理行顺序不是波次顺序**（id 排列为 1..12、401-405、13..20），
   真实波次由 SceneInfo.RoundList 决定（1..20, 401-405 → W21-25 是 401-405）。
   本脚本一律以 RoundList 的顺序为准。

用法：
  python _l01_gold_ground_hp_20261101.py values   # 干跑，只打印目标值
  python _l01_gold_ground_hp_20261101.py apply    # 备份 + 写盘
  python _l01_gold_ground_hp_20261101.py verify   # 只读校验（对照 .bak 基线）

改完必须手动跑一次 Luban 导出（Luban/gen_code_json.bat）才生效。
"""
import pathlib
import re
import shutil
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L01 = ROOT / 'Luban/Config/Datas/Levels/L01'
TAG = 'goldhp-20261101'

GOLD_FLAT = 5                      # 每波固定增量
GOLD_BONUS = 15                    # W5/W10/W15/W20 额外增量
GOLD_BONUS_WAVES = {5, 10, 15, 20}
HP_FACTOR = 1.12
HP_WAVES = [6, 7, 8, 9, 11, 12, 13, 14, 16, 17, 18, 19, 21, 22, 23, 24]   # 不含 10/15/20/25


def heads(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def wave_order(ws):
    """SceneInfo.RoundList 的 roundId 顺序 = 真实波次顺序。"""
    h = heads(ws)
    return [int(x) for x in str(ws.cell(4, h['RoundList']).value).split(',') if str(x).strip()]


def read_enemy(ws):
    h = heads(ws)
    out = {}
    for r in range(4, ws.max_row + 1):
        eid = ws.cell(r, h['id']).value
        if eid is None:
            continue
        out[int(eid)] = dict(
            row=r,
            name=ws.cell(r, h['name']).value,
            hp=float(ws.cell(r, h['hp']).value),
            armor=float(ws.cell(r, h['armor']).value or 0),
            fly=int(ws.cell(r, h['isFlying']).value or 0),
        )
    return h, out


def read_waves(ws):
    """EnemyList：desc 里的 'L1 W<n>/25' 才是波次号（id 本身也是 1..25，但不依赖它）。"""
    h = heads(ws)
    out = {}
    for r in range(4, ws.max_row + 1):
        lid = ws.cell(r, h['id']).value
        if lid is None:
            continue
        desc = str(ws.cell(r, h['desc']).value or '')
        m = re.match(r'L(\d+) W(\d+)/(\d+)', desc)
        ids = [int(x) for x in str(ws.cell(r, h['EnemyIndexs']).value).split(',') if str(x).strip()]
        out[int(m.group(2))] = dict(row=r, lid=int(lid), ids=ids, desc=desc)
    return h, out


def ehp_of(ids, enemy):
    return sum(enemy[i]['hp'] / (1 - enemy[i]['armor']) for i in ids)


def planned_gold(base_gold_by_rid, order):
    """{roundId: (old, new)}"""
    out = {}
    for w, rid in enumerate(order, 1):
        add = GOLD_FLAT + (GOLD_BONUS if w in GOLD_BONUS_WAVES else 0)
        out[rid] = (base_gold_by_rid[rid], base_gold_by_rid[rid] + add)
    return out


def planned_hp(enemy, waves):
    """[(row, name, old, new, wave)]"""
    rows = []
    for w in HP_WAVES:
        for eid in sorted({i for i in waves[w]['ids'] if not enemy[i]['fly']}):
            e = enemy[eid]
            rows.append((e['row'], e['name'], eid, e['hp'], round(e['hp'] * HP_FACTOR, 6), w))
    return rows


def dump_gold(plan, order):
    print('波  roundId  旧奖  新奖  增量')
    o = n = 0
    for w, rid in enumerate(order, 1):
        old, new = plan[rid]
        o += old
        n += new
        print(f'W{w:<3}{rid:<8}{old:>5}{new:>6}   +{new - old}')
    print(f'合计 {o} -> {n}  (Δ+{n - o})')


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'

    ws_si = openpyxl.load_workbook(L01 / 'SceneInfo.xlsx', data_only=True)['Sheet1']
    order = wave_order(ws_si)

    wb_rd = openpyxl.load_workbook(L01 / 'RoundData.xlsx')
    ws_rd = wb_rd[wb_rd.sheetnames[0]]
    h_rd = heads(ws_rd)
    base_gold, row_of_rid = {}, {}
    for r in range(4, ws_rd.max_row + 1):
        rid = ws_rd.cell(r, h_rd['id']).value
        if rid is None:
            continue
        base_gold[int(rid)] = int(ws_rd.cell(r, h_rd['rewardGold']).value)
        row_of_rid[int(rid)] = r

    wb_ed = openpyxl.load_workbook(L01 / 'EnemyData.xlsx')
    ws_ed = wb_ed[wb_ed.sheetnames[0]]
    h_ed, enemy = read_enemy(ws_ed)

    wb_el = openpyxl.load_workbook(L01 / 'EnemyList.xlsx')
    ws_el = wb_el[wb_el.sheetnames[0]]
    h_el, waves = read_waves(ws_el)

    # ---- 基线来源：未改时用表现值；已改过则用 .bak ----
    bak_rd = L01 / 'RoundData.xlsx.bak_20261101_goldhp'
    bak_ed = L01 / 'EnemyData.xlsx.bak_20261101_goldhp'
    if mode == 'verify':
        assert bak_rd.exists() and bak_ed.exists(), '缺少 .bak 基线，无法校验'
        # openpyxl 只认 .xlsx 扩展名，.bak 需先复制成临时副本再读
        tmpdir = ROOT / '.workbuddy/tools/__pycache__/bakcheck'
        tmpdir.mkdir(parents=True, exist_ok=True)
        t_rd, t_ed = tmpdir / 'RoundData.xlsx', tmpdir / 'EnemyData.xlsx'
        shutil.copy2(bak_rd, t_rd)
        shutil.copy2(bak_ed, t_ed)
        wb = openpyxl.load_workbook(t_rd, data_only=True)
        ws = wb[wb.sheetnames[0]]
        h = heads(ws)
        base_gold = {int(ws.cell(r, h['id']).value): int(ws.cell(r, h['rewardGold']).value)
                     for r in range(4, ws.max_row + 1) if ws.cell(r, h['id']).value is not None}
        wb = openpyxl.load_workbook(t_ed, data_only=True)
        ws = wb[wb.sheetnames[0]]
        _, enemy = read_enemy(ws)

    gold_plan = planned_gold(base_gold, order)
    hp_plan = planned_hp(enemy, waves)

    if mode == 'values':
        dump_gold(gold_plan, order)
        print(f'\n血量：{len(hp_plan)} 个地面变体行 ×{HP_FACTOR}（W{HP_WAVES[0]}-W{HP_WAVES[-1]}，跳过 10/15/20）')
        for row, name, eid, old, new, w in hp_plan:
            print(f'  W{w:<3}{name:<10}{eid:<9}{old:>12.6f} -> {new:.6f}')
        print('\n未改动：W1-W5、W10/W15/W20、W25 的血量；全部飞行单位；数量/间隔/击杀奖励')
        return 0

    if mode == 'verify':
        bad = []
        for rid, (old, new) in gold_plan.items():
            cur = int(ws_rd.cell(row_of_rid[rid], h_rd['rewardGold']).value)
            if cur != new:
                bad.append(f'RoundData id={rid} 期望 {new} 实为 {cur}')
        for row, name, eid, old, new, w in hp_plan:
            cur = float(ws_ed.cell(row, h_ed['hp']).value)
            if abs(cur - new) > 1e-6:
                bad.append(f'EnemyData id={eid} W{w} 期望 {new} 实为 {cur}')
        if bad:
            print('❌ 校验失败：')
            for b in bad[:20]:
                print('  ' + b)
            return 1
        print(f'✅ 校验通过：rewardGold 25 行 = 目标；地面血量 {len(hp_plan)} 行 = 基线×{HP_FACTOR}')
        return 0

    assert mode == 'apply', f'未知模式 {mode}'

    # 幂等：若已是目标值则拒绝重跑
    if all(int(ws_rd.cell(row_of_rid[rid], h_rd['rewardGold']).value) == new
           for rid, (_, new) in gold_plan.items()):
        print('⏭ 已是目标值，未重复写入')
        return 0

    for src, dst in ((L01 / 'RoundData.xlsx', bak_rd), (L01 / 'EnemyData.xlsx', bak_ed),
                     (L01 / 'EnemyList.xlsx', L01 / 'EnemyList.xlsx.bak_20261101_goldhp')):
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f'备份 -> {dst.name}')

    # 1) 波次奖励
    for rid, (old, new) in gold_plan.items():
        ws_rd.cell(row_of_rid[rid], h_rd['rewardGold']).value = new
    wb_rd.save(L01 / 'RoundData.xlsx')

    # 2) 地面血量
    for row, name, eid, old, new, w in hp_plan:
        ws_ed.cell(row, h_ed['hp']).value = new
    wb_ed.save(L01 / 'EnemyData.xlsx')

    # 3) 备注：只给血量动过的波次追加 EHP 标记（沿用历史 tag 习惯）
    wb_ed2 = openpyxl.load_workbook(L01 / 'EnemyData.xlsx', data_only=True)
    _, enemy_now = read_enemy(wb_ed2[wb_ed2.sheetnames[0]])
    for w in HP_WAVES:
        rec = waves[w]
        ehp = ehp_of(rec['ids'], enemy_now)
        desc = rec['desc']
        if TAG in desc:
            desc = re.sub(rf'\| {TAG}:.*$', '', desc).rstrip()
        desc = f"{desc} | {TAG}: ground x{HP_FACTOR} (EHP={ehp:.6f})"
        ws_el.cell(rec['row'], h_el['desc']).value = desc
    wb_el.save(L01 / 'EnemyList.xlsx')

    dump_gold(gold_plan, order)
    print(f'\n已写入：RoundData 25 行、EnemyData {len(hp_plan)} 行、EnemyList {len(HP_WAVES)} 条备注')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
