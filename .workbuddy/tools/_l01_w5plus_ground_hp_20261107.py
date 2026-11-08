#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性定点改表（2026-11-07 用户口径，仅 L01）：

    W5  地面怪 hp ×1.2（**叠加**在 2026-11-06 的 ×1.5 之上 → 相对原始配置共 ×1.8）
    W6–W25 地面怪 hp ×1.5（以现值 ×1.5）

基线 = 改动前的现值（乘性改动，重复执行会复利，带幂等护栏：desc 含 TAG 即拒绝重跑）。
范围：只 L01；只动 SceneInfo.RoundList 展开的第 5–25 波所引用的地面变体（isFlying=0）；
      空中（Bat 5000045 等）一律不动，数量/间隔/奖励/护甲/速度/波型不动。
备注：EnemyData.desc 追加 tag；EnemyList.desc 更新 EHP 汇总（W6–W24 原记录值是陈旧值，本次按实算更正）。

用法：
  python _l01_w5plus_ground_hp_20261107.py values | apply | verify
"""
import pathlib
import re
import shutil
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L01 = ROOT / 'Luban/Config/Datas/Levels/L01'

TAG = 'groundhp2-20261107'
FIRST_WAVE = 5
FACTOR_W5 = 1.2
FACTOR_REST = 1.5
BAK_ED = L01 / 'EnemyData.xlsx.bak_20261107_groundhp2'
BAK_EL = L01 / 'EnemyList.xlsx.bak_20261107_groundhp2'


def heads(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def load_copy(path, alias):
    """openpyxl 只认 .xlsx 扩展名，.bak 先复制成临时副本再读。"""
    if path.suffix == '.xlsx':
        return path
    tmp = ROOT / '.workbuddy/tools/__pycache__/bakcheck'
    tmp.mkdir(parents=True, exist_ok=True)
    dst = tmp / f'{alias}.xlsx'
    shutil.copy2(path, dst)
    return dst


def read_scene():
    ws = openpyxl.load_workbook(L01 / 'SceneInfo.xlsx', data_only=True)['Sheet1']
    h = heads(ws)
    return [int(x) for x in str(ws.cell(4, h['RoundList']).value).split(',') if str(x).strip()]


def read_enemy(path):
    wb = openpyxl.load_workbook(load_copy(path, 'EnemyData_' + path.name.replace('.', '_')), data_only=True)
    ws = wb[wb.sheetnames[0]]
    h = heads(ws)
    out = {}
    for r in range(4, ws.max_row + 1):
        eid = ws.cell(r, h['id']).value
        if eid is None:
            continue
        out[int(eid)] = dict(row=r, name=ws.cell(r, h['name']).value,
                             hp=float(ws.cell(r, h['hp']).value),
                             armor=float(ws.cell(r, h['armor']).value or 0),
                             fly=int(ws.cell(r, h['isFlying']).value or 0))
    wb.close()
    return out


def read_groups(path):
    wb = openpyxl.load_workbook(load_copy(path, 'EnemyList_' + path.name.replace('.', '_')), data_only=True)
    ws = wb['Sheet1']
    h = heads(ws)
    out = {}
    for r in range(4, ws.max_row + 1):
        lid = ws.cell(r, h['id']).value
        if lid is None:
            continue
        out[int(lid)] = dict(row=r,
                             seq=[int(x) for x in str(ws.cell(r, h['EnemyIndexs']).value).split(',') if str(x).strip()],
                             desc=str(ws.cell(r, h['desc']).value or ''))
    wb.close()
    return out


def ehp_of(seq, enemy):
    return sum(enemy[i]['hp'] / (1 - enemy[i]['armor']) for i in seq)


def build_plan(order, groups, enemy):
    """[(wave, roundId, el_row, factor, ground_ids, old_ehp, new_ehp, desc)]"""
    plan = []
    for w, rid in enumerate(order, 1):
        if w < FIRST_WAVE:
            continue
        g = groups[rid]
        ground = sorted({i for i in g['seq'] if not enemy[i]['fly']})
        factor = FACTOR_W5 if w == FIRST_WAVE else FACTOR_REST
        old = ehp_of(g['seq'], enemy)
        patched = {**enemy, **{i: dict(enemy[i], hp=round(enemy[i]['hp'] * factor, 6)) for i in ground}}
        new = ehp_of(g['seq'], patched)
        plan.append((w, rid, g['row'], factor, ground, old, new, g['desc']))
    return plan


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'values'

    order = read_scene()
    cur = read_enemy(L01 / 'EnemyData.xlsx')
    groups = read_groups(L01 / 'EnemyList.xlsx')
    plan = build_plan(order, groups, cur)

    if mode in ('values', 'verify'):
        base = cur
        if mode == 'verify':
            if not BAK_ED.exists():
                print('❌ 缺少改前基准，无法校验')
                return 1
            base = read_enemy(BAK_ED)
            plan = build_plan(order, groups, base)

        print('波 | roundId | 地面变体 | 倍率 | 现 EHP | 改后 EHP')
        for w, rid, row, f, ground, old, new, _ in plan:
            print(f'W{w:<3}{rid:<9}{len(ground)} 个   x{f:<5}{old:>13,.2f} -> {new:>13,.2f}')
        tot0 = sum(p[5] for p in plan)
        tot1 = sum(p[6] for p in plan)
        rows = sum(len(p[4]) for p in plan)
        print(f'\nW{FIRST_WAVE}–W{len(order)} 合计 EHP {tot0:,.2f} -> {tot1:,.2f} '
              f'({100 * (tot1 / tot0 - 1):+.2f}%)，写入行数 {rows}')

        w5 = next(p for p in plan if p[0] == FIRST_WAVE)
        print(f'\nW{FIRST_WAVE} 地面（现值 ×{FACTOR_W5}）：')
        for i in w5[4]:
            print(f"  {i} {base[i]['name']:<8} {base[i]['hp']:.6f} -> {round(base[i]['hp'] * FACTOR_W5, 6):.6f}")

        if mode == 'verify':
            bad = []
            for w, rid, row, f, ground, old, new, _ in plan:
                for i in ground:
                    want = round(base[i]['hp'] * f, 6)
                    if abs(cur[i]['hp'] - want) > 1e-6:
                        bad.append(f'W{w} id={i} 期望 {want} 实为 {cur[i]["hp"]}')
                for i in {i for i in groups[rid]['seq'] if cur[i]['fly']}:
                    if abs(cur[i]['hp'] - base[i]['hp']) > 1e-9:
                        bad.append(f'W{w} 空中 id={i} 不应改动 实为 {cur[i]["hp"]}')
            if bad:
                print('❌ 校验失败：')
                for b in bad[:20]:
                    print('  ' + b)
                return 1
            print(f'✅ 校验通过：W{FIRST_WAVE} ×{FACTOR_W5}，W{FIRST_WAVE + 1}–W{len(order)} ×{FACTOR_REST}；空中一律未变')
        return 0

    assert mode == 'apply', f'未知模式 {mode}'

    if any(TAG in p[7] for p in plan):
        print(f'⏭ 已带标记 {TAG}，拒绝重复叠加（乘性改动不可重跑）')
        return 0

    for src, dst in ((L01 / 'EnemyData.xlsx', BAK_ED), (L01 / 'EnemyList.xlsx', BAK_EL)):
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f'备份 -> {dst.name}')

    # 1) EnemyData.hp + 行内备注
    wb = openpyxl.load_workbook(L01 / 'EnemyData.xlsx')
    ws = wb[wb.sheetnames[0]]
    h = heads(ws)
    for w, rid, row, f, ground, old, new, _ in plan:
        for i in ground:
            r = cur[i]['row']
            ws.cell(r, h['hp']).value = round(cur[i]['hp'] * f, 6)
            d = str(ws.cell(r, h['desc']).value or '')
            note = f'ground x{f}' + (' (cumulative x1.8 vs original)' if w == FIRST_WAVE else '')
            ws.cell(r, h['desc']).value = f'{d} | {TAG}: {note}'
    wb.save(L01 / 'EnemyData.xlsx')

    # 2) EnemyList 备注：EHP 汇总更正为本波实算值 + 追加 tag
    wb = openpyxl.load_workbook(L01 / 'EnemyList.xlsx')
    ws = wb['Sheet1']
    h = heads(ws)
    for w, rid, row, f, ground, old, new, desc in plan:
        parts = desc.split(' | ')
        if re.search(r'EHP=[\d.]+', parts[0]):
            parts[0] = re.sub(r'EHP=[\d.]+', f'EHP={new:.6f}', parts[0], count=1)
        ws.cell(row, h['desc']).value = ' | '.join(parts) + f' | {TAG}: ground x{f} (EHP={new:.6f})'
    wb.save(L01 / 'EnemyList.xlsx')

    tbl = {}
    for w, rid, row, f, ground, old, new, _ in plan:
        tbl[w] = (len(ground), old, new, f)
    print('已写入（波: 地面变体数, 旧EHP -> 新EHP, 倍率）：')
    for w in sorted(tbl):
        n, old, new, f = tbl[w]
        print(f'  W{w:<3}{n} 个  {old:>13,.2f} -> {new:>13,.2f}  x{f}')
    print(f"备注已追加 {TAG}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
