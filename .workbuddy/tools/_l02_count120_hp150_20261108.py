#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L02 W5–W25（含第 5 波）怪物数量 ×1.2 + 血量 ×1.5（2026-11-08）。

用户口径（本轮当次确认）：
  · 范围：L02 第 5 波次（含）到第 25 波次，共 21 波
  · 数量：每波总数 = round(现值 × 1.2)，按各怪种当前占比用最大余数法分配
  · 血量：涉及行 hp = round(原值 × 1.5, 6)
  · 出怪间隔 enemyInterval / 单怪 reward / RoundData.rewardGold 一律不动
  · 新增怪物必须满足「空中怪不相邻」（AGENTS.md 铁律）：空中等距重排，地面按占比重采样

基线：.bak_20261108_before_count120 / .bak_20261108_before_hp150（固定为改动前原值 → 幂等）

用法：python _l02_count120_hp150_20261108.py values|apply|verify
"""
from __future__ import annotations

import math
import pathlib
import shutil
import sys
from collections import Counter, defaultdict

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L02 = ROOT / 'Luban/Config/Datas/Levels/L02'
LIST_BAK = L02 / 'EnemyList.xlsx.bak_20261108_before_count120'
ENEMY_BAK = L02 / 'EnemyData.xlsx.bak_20261108_before_hp150'
WAVE_FROM, WAVE_TO = 5, 25
COUNT_FACTOR = 1.2
HP_FACTOR = 1.5


def heads(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def open_book(path):
    """用二进制句柄打开，绕开 openpyxl 对 .bak_xxx 扩展名的拒绝。"""
    with open(path, 'rb') as fh:
        return openpyxl.load_workbook(fh, data_only=True)


def load_enemy(path):
    ws = open_book(path).worksheets[0]
    h = heads(ws)
    out = {}
    for r in range(4, ws.max_row + 1):
        eid = ws.cell(r, h['id']).value
        if eid is None:
            continue
        out[int(eid)] = dict(row=r, hp=float(ws.cell(r, h['hp']).value),
                             fly=int(ws.cell(r, h['isFlying']).value or 0),
                             name=ws.cell(r, h['name']).value)
    return out


def load_lists(path):
    ws = open_book(path).worksheets[0]
    out = {}
    for r in range(4, ws.max_row + 1):
        lid = ws.cell(r, 2).value
        if lid is None:
            continue
        out[int(lid)] = dict(row=r, ids=[int(x) for x in str(ws.cell(r, 3).value).split(',') if x.strip()],
                             enemy_interval=ws.cell(r, 5).value)
    return out


def load_round_list():
    ws = open_book(L02 / 'SceneInfo.xlsx').worksheets[0]
    h = heads(ws)
    val = str(ws.cell(4, h['RoundList']).value)
    return [int(x) for x in val.split(',') if x.strip()]


def largest_remainder(counts: dict[int, int], total: int) -> dict[int, int]:
    """按 counts 占比把 total 分配到各 id；余数用最大余数法补齐，和精确等于 total。"""
    src_total = sum(counts.values())
    exact = {k: v * total / src_total for k, v in counts.items()}
    base = {k: int(math.floor(v)) for k, v in exact.items()}
    left = total - sum(base.values())
    order = sorted(exact, key=lambda k: (-(exact[k] - base[k]), -counts[k], k))
    for k in order[:left]:
        base[k] += 1
    return base


def resample(seq: list[int], targets: dict[int, int]) -> list[int]:
    """保持 seq 相对顺序，把每种 id 扩到 targets[id] 个（超额副本均匀分布到该 id 的各个原位置）。"""
    pos = defaultdict(list)
    for i, x in enumerate(seq):
        pos[x].append(i)
    emit = {i: 0 for i in range(len(seq))}
    for eid, t in targets.items():
        plist = pos[eid]
        c = len(plist)
        assert c > 0 and t >= 0
        for k in range(1, t + 1):
            occ = min(c, max(1, math.ceil(k * c / t)))
            emit[plist[occ - 1]] += 1
    out = []
    for i, x in enumerate(seq):
        out.extend([x] * emit[i])
    assert len(out) == sum(targets.values()), (len(out), sum(targets.values()))
    return out


def build_wave(seq: list[int], enemy: dict):
    n = len(seq)
    target_total = int(round(n * COUNT_FACTOR))
    cur = Counter(seq)
    air_ids = [e for e in cur if enemy[e]['fly'] != 0]
    ground_ids = [e for e in cur if enemy[e]['fly'] == 0]

    air_total = int(round(sum(cur[e] for e in air_ids) * target_total / n))
    air_targets = largest_remainder({e: cur[e] for e in air_ids}, air_total) if air_ids else {}
    ground_targets = largest_remainder({e: cur[e] for e in ground_ids},
                                       target_total - air_total) if ground_ids else {}

    # 空中：在目标长度上等距铺开（间距 ≥ 2，天然满足不相邻）
    air_seq_orig = [x for x in seq if enemy[x]['fly'] != 0]
    air_slots = resample(air_seq_orig, air_targets) if air_ids else []
    assert len(air_slots) == air_total
    air_pos = {int(math.floor((k - 0.5) * target_total / air_total)) for k in range(1, air_total + 1)}
    assert len(air_pos) == air_total, '空中等距槽位冲突（间距应 ≥ 2）'
    assert all(0 <= p < target_total for p in air_pos)

    # 地面：按原顺序重采样后依次填入非空中槽位
    ground_slots = resample([x for x in seq if enemy[x]['fly'] == 0], ground_targets) if ground_ids else []
    assert len(ground_slots) == target_total - air_total
    it = iter(ground_slots)
    air_it = iter(air_slots)
    out = [next(air_it) if i in air_pos else next(it) for i in range(target_total)]
    assert Counter(out) == Counter({**air_targets, **ground_targets})
    assert not any(enemy[out[i]]['fly'] and enemy[out[i - 1]]['fly'] for i in range(1, len(out)))
    return out


def plan():
    round_list = load_round_list()
    base_lists = load_lists(LIST_BAK if LIST_BAK.exists() else (L02 / 'EnemyList.xlsx'))
    base_enemy = load_enemy(ENEMY_BAK if ENEMY_BAK.exists() else (L02 / 'EnemyData.xlsx'))
    waves = []
    for wave in range(WAVE_FROM, WAVE_TO + 1):
        lid = round_list[wave - 1]
        seq = base_lists[lid]['ids']
        waves.append(dict(wave=wave, lid=lid, row=base_lists[lid]['row'],
                          enemy_interval=base_lists[lid]['enemy_interval'],
                          old=seq, new=build_wave(seq, base_enemy)))
    ids = sorted({e for w in waves for e in w['old']})
    hp_plan = {e: round(base_enemy[e]['hp'] * HP_FACTOR, 6) for e in ids}
    return waves, hp_plan, base_enemy


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'
    waves, hp_plan, base_enemy = plan()
    all_ids = sorted(hp_plan)
    untouched_lists = [k for k in load_lists(L02 / 'EnemyList.xlsx') if k not in {w['lid'] for w in waves}]

    if mode == 'values':
        print(f'L02 W{WAVE_FROM}–W{WAVE_TO}｜数量 ×{COUNT_FACTOR}（每波 round）+ 血量 ×{HP_FACTOR}\n')
        print(f"{'波':<4}{'list':>6}{'N现':>6}{'N新':>6}{'增':>5}{'空现':>5}{'空新':>5}{'EHP现':>12}{'EHP新':>12}{'出怪间隔':>10}")
        tn = tno = tair = tairo = 0
        for w in waves:
            n0, n1 = len(w['old']), len(w['new'])
            a0 = sum(1 for x in w['old'] if base_enemy[x]['fly'])
            a1 = sum(1 for x in w['new'] if base_enemy[x]['fly'])
            e0 = sum(base_enemy[x]['hp'] for x in w['old'])
            e1 = sum(base_enemy[x]['hp'] * HP_FACTOR for x in w['old'])
            tn += n1; tno += n0; tair += a1; tairo += a0
            print(f"W{w['wave']:<3}{w['lid']:>6}{n0:>6}{n1:>6}{n1 - n0:>+5}{a0:>5}{a1:>5}"
                  f"{e0:>12,.0f}{e1:>12,.0f}{w['enemy_interval']:>10}")
        print(f"\n合计：{tno:,} -> {tn:,}（+{tn - tno:,}）｜空中 {tairo:,} -> {tair:,}")
        print(f'血量行数：{len(all_ids)} 行（{all_ids[0]}–{all_ids[-1]}）')
        hp0 = sum(base_enemy[e]['hp'] for e in all_ids)
        print(f'100 行 hp 合计：{hp0:,.2f} -> {hp0 * HP_FACTOR:,.2f}')
        print(f'不动的波次组：{untouched_lists}')
        gaps = []
        for w in waves:
            pos = [i for i, x in enumerate(w['new']) if base_enemy[x]['fly']]
            gaps += [b - a for a, b in zip(pos, pos[1:])]
        print(f'空中最小间距：{min(gaps)}（必须 ≥2 才算不相邻）')
        return 0

    if mode == 'verify':
        cur_lists = load_lists(L02 / 'EnemyList.xlsx')
        cur_enemy = load_enemy(L02 / 'EnemyData.xlsx')
        bad = []
        for w in waves:
            got = cur_lists[w['lid']]['ids']
            if Counter(got) != Counter(w['new']):
                bad.append(f"list={w['lid']} 多重集合不符（{len(got)} vs {len(w['new'])}）")
            if any(cur_enemy[got[i]]['fly'] and cur_enemy[got[i - 1]]['fly'] for i in range(1, len(got))):
                bad.append(f"list={w['lid']} 出现空中相邻")
            if cur_lists[w['lid']]['enemy_interval'] != w['enemy_interval']:
                bad.append(f"list={w['lid']} enemyInterval 被改动")
        for e in all_ids:
            if abs(cur_enemy[e]['hp'] - hp_plan[e]) > 1e-6:
                bad.append(f'id={e} hp 期望 {hp_plan[e]} 实为 {cur_enemy[e]["hp"]}')
        for e in cur_enemy:
            if e not in hp_plan and abs(cur_enemy[e]['hp'] - base_enemy[e]['hp']) > 1e-9:
                bad.append(f'id={e} 非目标行 hp 被改动 {base_enemy[e]["hp"]} -> {cur_enemy[e]["hp"]}')
        for lid in untouched_lists:
            if load_lists(L02 / 'EnemyList.xlsx')[lid]['ids'] != load_lists(LIST_BAK)[lid]['ids']:
                bad.append(f'list={lid} 不在范围却被改动')
        if bad:
            print('❌ 校验失败：')
            for b in bad[:20]:
                print('  ' + b)
            return 1
        print(f'✅ 校验通过：21 波数量 = 基线×1.2（{sum(len(w["new"]) for w in waves):,} 只）、'
              f'{len(all_ids)} 行 hp = 基线×{HP_FACTOR}、空中无相邻；'
              f'{len(untouched_lists)} 个 W1–W4 组与 {len(cur_enemy) - len(all_ids)} 行 hp 未改动')
        return 0

    assert mode == 'apply', f'未知模式 {mode}'
    cur_lists = load_lists(L02 / 'EnemyList.xlsx')
    if all(cur_lists[w['lid']]['ids'] == w['new'] for w in waves):
        print('⏭ EnemyList 已是目标值，未重复写入')
    else:
        if not LIST_BAK.exists():
            shutil.copy2(L02 / 'EnemyList.xlsx', LIST_BAK)
            print('备份 ->', LIST_BAK.name)
        wb = openpyxl.load_workbook(L02 / 'EnemyList.xlsx')
        ws = wb[wb.sheetnames[0]]
        h = heads(ws)
        for w in waves:
            ws.cell(w['row'], h['EnemyIndexs']).value = ','.join(str(x) for x in w['new'])
        wb.save(L02 / 'EnemyList.xlsx')
        print(f'已写入 EnemyList：{len(waves)} 组')

    cur_enemy = load_enemy(L02 / 'EnemyData.xlsx')
    if all(abs(cur_enemy[e]['hp'] - hp_plan[e]) < 1e-6 for e in all_ids):
        print('⏭ EnemyData.hp 已是目标值，未重复写入')
    else:
        if not ENEMY_BAK.exists():
            shutil.copy2(L02 / 'EnemyData.xlsx', ENEMY_BAK)
            print('备份 ->', ENEMY_BAK.name)
        wb = openpyxl.load_workbook(L02 / 'EnemyData.xlsx')
        ws = wb[wb.sheetnames[0]]
        h = heads(ws)
        for e in all_ids:
            ws.cell(cur_enemy[e]['row'], h['hp']).value = hp_plan[e]
        wb.save(L02 / 'EnemyData.xlsx')
        print(f'已写入 EnemyData：{len(all_ids)} 行 hp ×{HP_FACTOR}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
