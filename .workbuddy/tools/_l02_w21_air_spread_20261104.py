#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L02 W21–W25 空中怪「拆对、均匀单发」重排（2026-11-04）。

问题（用户实测 + 数据核对）：
  各波 EnemyList 里蝙蝠是 **成对刷出**（★★ 背靠背，相差 1 个出怪位 = 一帧内两只），
  W21 33 对 / W22 42 对 / W23 40 对 / W24 47 对 / W25 48 对。
  → 塔打死一只时第二只已经贴身，必然漏怪。用户明确：要解决「多只同时出现」，
    不是改 enemyInterval、也不是削血量。

改法（只动顺序，不动数量/血量/其余列）：
  · 把每波的蝙蝠从序列里取出，按 N/蝙蝠数 的间距**均匀单发**插回；
  · 地面怪相对顺序原样保留（只是被"推开"）；
  · 每波总只数、蝙蝠只数、各地面怪只数全部不变。

用法：
  python _l02_w21_air_spread_20261104.py values   # 干跑（只读）
  python _l02_w21_air_spread_20261104.py apply    # 备份 + 写盘
  python _l02_w21_air_spread_20261104.py verify   # 只读校验（对照 .bak 基线）
"""
from __future__ import annotations

import pathlib
import re
import shutil
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L02 = ROOT / 'Luban/Config/Datas/Levels/L02'
# W1-W20 = 2001-2020，W21-W25 = 2401-2405；W1-W4 无空中怪，一并纳入不影响结果
LIST_IDS = list(range(2005, 2021)) + [2401, 2402, 2403, 2404, 2405]
TAG = 'airspread-20261104'
BAK_EL = L02 / 'EnemyList.xlsx.bak_20261104_before_airspread'
CROSS_SEC = 15.5          # 16 格 / 速度 ~1.03 格每秒 ≈ 15.5 秒穿场


def heads(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def load_list(ws, h, list_id):
    for r in range(4, ws.max_row + 1):
        v = ws.cell(r, h['id']).value
        if v is None:
            continue
        if int(v) == list_id:
            return r, [int(x) for x in str(ws.cell(r, h['EnemyIndexs']).value).split(',') if str(x).strip()], \
                float(ws.cell(r, h['enemyInterval']).value or 0)
    raise SystemExit(f'EnemyList 里找不到 id={list_id}')


def load_air_flag():
    ws = openpyxl.load_workbook(L02 / 'EnemyData.xlsx', data_only=True).worksheets[0]
    h = heads(ws)
    return {int(ws.cell(r, h['id']).value): int(ws.cell(r, h['isFlying']).value or 0)
            for r in range(4, ws.max_row + 1) if ws.cell(r, h['id']).value is not None}


def reflow(ids, air_flag):
    """地面保序、空中均匀单发。"""
    air = [e for e in ids if air_flag[e] == 1]
    ground = [e for e in ids if air_flag[e] != 1]
    n, m = len(ids), len(air)
    if m == 0:
        return list(ids)
    targets = [min(max(int(round((k + 0.5) * n / m)), 0), n - 1) for k in range(m)]
    used = set()
    for k in range(m):
        t = targets[k]
        while t in used:
            t += 1
        used.add(t)
        targets[k] = t
    air_at = dict(zip(targets, air))
    out, gi = [], 0
    for i in range(n):
        if i in air_at:
            out.append(air_at[i])
        else:
            out.append(ground[gi])
            gi += 1
    assert gi == len(ground)
    return out


def stats(ids, air_flag, interval_ms):
    pos = [i for i, e in enumerate(ids) if air_flag[e] == 1]
    gaps = [pos[i + 1] - pos[i] for i in range(len(pos) - 1)]
    step = (interval_ms or 140.0) / 1000.0
    span = max(1, int(CROSS_SEC / step))
    win = max(1, int(20 / step))
    return dict(n=len(ids), air=len(pos), min_gap=min(gaps) if gaps else 0,
                back_to_back=sum(1 for g in gaps if g == 1),
                within3=sum(1 for g in gaps if g <= 3),
                first20=sum(1 for p in pos if p < win),
                peak_concurrent=max((sum(1 for q in pos if p <= q <= p + span) for p in pos), default=0),
                min_gap_sec=(min(gaps) * step) if gaps else 0.0)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'

    wb = openpyxl.load_workbook(L02 / 'EnemyList.xlsx')
    ws = wb[wb.sheetnames[0]]
    h = heads(ws)
    air_flag = load_air_flag()

    cur = {}
    for lid in LIST_IDS:
        row, ids, iv = load_list(ws, h, lid)
        cur[lid] = dict(row=row, ids=ids, iv=iv, new=reflow(ids, air_flag))

    if mode in ('values', 'verify'):
        base_ids = None
        if mode == 'verify':
            assert BAK_EL.exists(), '缺少 .bak 基线'
            with open(BAK_EL, 'rb') as fh:
                wb0 = openpyxl.load_workbook(fh, data_only=True)
            ws0 = wb0[wb0.sheetnames[0]]
            h0 = heads(ws0)
            base_ids = {lid: load_list(ws0, h0, lid) for lid in LIST_IDS}

        print(f"{'ID':<6}{'波':<4}{'总只':>6}{'空中':>5}{'背靠背':>12}{'≤3位':>10}{'最小间隔':>11}{'前20s空':>10}{'走廊峰值':>10}")
        ok = True
        for lid in LIST_IDS:
            w = lid - 2000 if lid < 2400 else lid - 2400 + 20
            ref = base_ids[lid][1] if base_ids else cur[lid]['ids']   # 改前（verify 用 .bak）
            src = cur[lid]['ids'] if base_ids else cur[lid]['new']     # 现状 / 计划
            a = stats(ref, air_flag, base_ids[lid][2] if base_ids else cur[lid]['iv'])
            b = stats(src, air_flag, cur[lid]['iv'])
            print(f"{lid:<6}W{w:<3}{b['n']:>6}{b['air']:>5}"
                  f"{str(a['back_to_back'])+'->'+str(b['back_to_back']):>12}"
                  f"{str(a['within3'])+'->'+str(b['within3']):>10}"
                  f"{str(a['min_gap'])+'->'+str(b['min_gap']):>11}"
                  f"{str(a['first20'])+'->'+str(b['first20']):>10}"
                  f"{str(a['peak_concurrent'])+'->'+str(b['peak_concurrent']):>10}")
            if base_ids:
                g_old = [e for e in base_ids[lid][1] if air_flag[e] != 1]
                g_new = [e for e in cur[lid]['ids'] if air_flag[e] != 1]
                good = (sorted(cur[lid]['ids']) == sorted(base_ids[lid][1])
                        and b['n'] == a['n'] and b['air'] == a['air']
                        and g_old == g_new and b['back_to_back'] == 0 and b['min_gap'] >= 8)
                if not good:
                    ok = False
                    print(f"   ❌ W{w} 校验失败：{a} -> {b}")
        if mode == 'verify':
            if ok:
                print('\n✅ 全部通过：5 波总只数/空中只数不变、地面顺序不变、背靠背 0 处、最少隔 ≥8 位')
                return 0
            return 1
        if base_ids is None:
            print('\n（以上为「改后」口径；现状见 git diff 前的 .bak）')
        return 0

    assert mode == 'apply', f'未知模式 {mode}'
    todo = [lid for lid in LIST_IDS if cur[lid]['ids'] != cur[lid]['new']]
    if not todo:
        print('⏭ 全部已是目标顺序，未重复写入')
        return 0
    if not BAK_EL.exists():
        shutil.copy2(L02 / 'EnemyList.xlsx', BAK_EL)
        print('备份 ->', BAK_EL.name)

    for lid in todo:
        rec = cur[lid]
        ws.cell(rec['row'], h['EnemyIndexs']).value = ','.join(str(x) for x in rec['new'])
        desc = str(ws.cell(rec['row'], h['desc']).value or '')
        desc = re.sub(rf'\s*\|\s*{TAG}:[^|]*$', '', desc).rstrip()
        b = stats(rec['new'], air_flag, rec['iv'])
        ws.cell(rec['row'], h['desc']).value = (
            f"{desc} | {TAG}: air reflowed single-file "
            f"(air={b['air']}, min gap={b['min_gap']} slots)")
        print(f"  已重排 id={lid}：{b['n']} 只 / 空中 {b['air']} / 背靠背 0 / 最少隔 {b['min_gap']} 位")
    wb.save(L02 / 'EnemyList.xlsx')
    print(f'已写入 {len(todo)} 波')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
