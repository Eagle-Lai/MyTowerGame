#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性手工改表（不入库）：第一关 血量×2、空军数量×2、空军改成 W5 起。

直接改 xlsx（不走配方），改完必须手动跑一次 Luban 导出才生效；
下一次 `balance_pipeline.py apply` 会把这两张表整体覆盖回配方值。
"""
import collections
import pathlib
import re

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L01 = ROOT / 'Luban/Config/Datas/Levels/L01'
# 2026-10-21 第二次调：地面 ×1.5、空军 ×2（空军在 1.5 的基础上再翻倍）
HP_FACTOR = 1.5
AIR_HP_FACTOR = 2.0
AIR_FIRST_WAVE = 5
AIR_FACTOR = 2


def load(path):
    wb = openpyxl.load_workbook(path)
    ws = wb[wb.sheetnames[0]]
    heads = {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}
    return wb, ws, heads


def main():
    # ---------- 1. EnemyData：全部血量 ×2 ----------
    wb, ws, h = load(L01 / 'EnemyData.xlsx')
    rows = {}
    changed = 0
    for r in range(4, ws.max_row + 1):
        eid = ws.cell(r, h['id']).value
        if eid is None:
            continue
        assert int(eid) >= 100000, f'L01 里出现原型行 {eid}，不该在这里'
        hp = float(ws.cell(r, h['hp']).value)
        flying = int(ws.cell(r, h['isFlying']).value or 0)
        factor = AIR_HP_FACTOR if flying else HP_FACTOR
        ws.cell(r, h['hp']).value = round(hp * factor, 6)
        rows[int(eid)] = {'hp': hp * factor, 'armor': float(ws.cell(r, h['armor']).value or 0),
                          'flying': flying}
        changed += 1
    wb.save(L01 / 'EnemyData.xlsx')
    print(f'EnemyData: {changed} 行 地面 hp x{HP_FACTOR} / 空军 hp x{AIR_HP_FACTOR}')

    # ---------- 2. EnemyList：空军 W5 起、数量 ×2（总数不变，用地面换） ----------
    wb, ws, h = load(L01 / 'EnemyList.xlsx')
    stats = []
    for r in range(4, ws.max_row + 1):
        lid = ws.cell(r, h['id']).value
        if lid is None:
            continue
        desc = str(ws.cell(r, h['desc']).value or '')
        m = re.match(r'L(\d+) W(\d+)/(\d+)', desc)
        wave = int(m.group(2))
        ids = [int(x) for x in str(ws.cell(r, h['EnemyIndexs']).value).split(',') if str(x).strip()]
        air_ids = [i for i in ids if rows[i]['flying']]
        ground_ids = [i for i in ids if not rows[i]['flying']]
        assert ground_ids, f'W{wave} 没有地面单位'
        ground = collections.Counter(ground_ids).most_common(1)[0][0]

        if wave < AIR_FIRST_WAVE:
            new_ids = [i for i in ids if not rows[i]['flying']] + [ground] * len(air_ids)
            target_air = 0
        else:
            target_air = len(air_ids) * AIR_FACTOR
            pool = air_ids or [i for i in ids if rows[i]['flying']]
            if not pool:
                raise SystemExit(f'W{wave} 列表里没有任何空军变体，无法凭空造出空军')
            new_ids = list(ids)
            # 只换"最便宜的地面位"：按变体 hp 升序挑替身，别把精英/重甲换成小飞机
            need = target_air - len(air_ids)
            if need > 0:
                candidates = sorted((idx for idx, i in enumerate(new_ids) if not rows[i]['flying']),
                                    key=lambda idx: rows[new_ids[idx]]['hp'])
                for k, idx in enumerate(candidates[:need]):
                    new_ids[idx] = pool[k % len(pool)]
            elif need < 0:
                extra = -need
                for idx, i in enumerate(new_ids):
                    if extra == 0:
                        break
                    if rows[i]['flying']:
                        new_ids[idx] = ground
                        extra -= 1
        assert len(new_ids) == len(ids), f'W{wave} 数量被改动了'
        ws.cell(r, h['EnemyIndexs']).value = ','.join(str(x) for x in new_ids)

        # 重算 EHP 并回写 desc（原来那串只改 EHP 数字，其余保持）
        ehp = sum(rows[i]['hp'] / (1 - rows[i]['armor']) for i in new_ids)
        air_after = sum(1 for i in new_ids if rows[i]['flying'])
        desc = re.sub(r'EHP=[\d.]+', f'EHP={ehp:.6f}', desc)
        if 'manual:' not in desc:
            desc = desc.rstrip() + f' | manual: hp x{HP_FACTOR} (air x{AIR_HP_FACTOR}), air x{AIR_FACTOR} from W{AIR_FIRST_WAVE}'
        ws.cell(r, h['desc']).value = desc
        stats.append((wave, len(ids), len(air_ids), air_after, ehp))
    wb.save(L01 / 'EnemyList.xlsx')

    print('wave  N   空军(改前->改后)   EHP')
    for w, n, before, after, ehp in stats:
        print(f'  {w:>2}  {n:>3}   {before:>2} -> {after:<3}      {ehp:.1f}')


if __name__ == '__main__':
    main()
