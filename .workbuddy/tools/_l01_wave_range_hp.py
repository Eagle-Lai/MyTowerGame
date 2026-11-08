#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L01 敌人血量「按波次区间 × 倍率 × 地面/空中」定点改表工具（参数化）。

★ 使用前提（不可绕过）：必须先按 AGENTS.md「关卡数值改动的范围与确认」取得**当次授权**——
   哪几关、哪几波、地面/空中、倍率口径（叠加在现值 / 换原始基准）。历史口径不延续。
   本工具只作用于 L01，只改 EnemyData.hp + 两处备注（EnemyData.desc / EnemyList.desc 的 EHP 汇总）。

用法：
  python _l01_wave_range_hp.py values --waves 11-14 --factor 1.3
  python _l01_wave_range_hp.py values --waves 15 --factor 0.9 --target air
  python _l01_wave_range_hp.py apply  --waves 15 --factor 0.9 --target air --tag airhp1-20261107 --yes
  python _l01_wave_range_hp.py verify --waves 15 --factor 0.9 --target air --tag airhp1-20261107

  --target ground（默认）| air | both：按 EnemyData.isFlying 判定，不按名称猜。
  --factor 支持小于 1（削弱），如 0.9 = 减少 10%。

安全设计：
  - 默认 values（干跑，不写盘）；apply 必须显式 --yes；
  - 乘性改动带幂等护栏：EnemyList.desc 命中 tag 即拒绝重跑，避免复利叠加；
  - 改前自动留 `.bak_<tag>` 基准；「白名单外零改动」靠外部逐格 diff 复核。
"""
import argparse
import pathlib
import re
import shutil
import sys

import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[2]
L01 = ROOT / 'Luban/Config/Datas/Levels/L01'
LABEL = {'ground': '地面', 'air': '空中', 'both': '地面+空中'}


def heads(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def load_copy(path, alias):
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


def split_by_target(seq, enemy, target):
    """返回 (要改的变体去重列表, 不动的变体去重列表)；判定只看 isFlying。"""
    def is_air(i):
        return enemy[i]['fly'] != 0

    if target == 'ground':
        sel = [i for i in seq if not is_air(i)]
        other = [i for i in seq if is_air(i)]
    elif target == 'air':
        sel = [i for i in seq if is_air(i)]
        other = [i for i in seq if not is_air(i)]
    else:
        sel = list(seq)
        other = []
    return sorted(set(sel)), sorted(set(other))


def build_plan(order, groups, enemy, wave_from, wave_to, factor, target):
    """[(wave, roundId, el_row, sel_ids, other_ids, old_ehp, new_ehp, desc)]"""
    plan = []
    for w, rid in enumerate(order, 1):
        if not (wave_from <= w <= wave_to):
            continue
        g = groups[rid]
        sel, other = split_by_target(g['seq'], enemy, target)
        old = ehp_of(g['seq'], enemy)
        patched = {**enemy, **{i: dict(enemy[i], hp=round(enemy[i]['hp'] * factor, 6)) for i in sel}}
        plan.append((w, rid, g['row'], sel, other, old, ehp_of(g['seq'], patched), g['desc']))
    if not plan:
        raise SystemExit(f'没有匹配到 W{wave_from}–W{wave_to}')
    return plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['values', 'apply', 'verify'])
    ap.add_argument('--waves', required=True, help='波次区间，如 11-14 或 15')
    ap.add_argument('--factor', type=float, required=True, help='倍率，如 1.3 / 0.9')
    ap.add_argument('--target', choices=['ground', 'air', 'both'], default='ground')
    ap.add_argument('--tag', default=None, help='备注/idempotency 标记（apply/verify 必填）')
    ap.add_argument('--yes', action='store_true', help='apply 的显式确认')
    a = ap.parse_args()

    if '-' in a.waves:
        wave_from, wave_to = (int(x) for x in a.waves.split('-', 1))
    else:
        wave_from = wave_to = int(a.waves)
    if a.factor <= 0:
        raise SystemExit('倍率必须为正')
    if a.mode in ('apply', 'verify') and not a.tag:
        raise SystemExit('apply/verify 必须给 --tag')

    bak_ed = L01 / f'EnemyData.xlsx.bak_{a.tag}' if a.tag else None
    bak_el = L01 / f'EnemyList.xlsx.bak_{a.tag}' if a.tag else None
    label = LABEL[a.target]

    order = read_scene()
    cur = read_enemy(L01 / 'EnemyData.xlsx')
    groups = read_groups(L01 / 'EnemyList.xlsx')

    if a.mode in ('values', 'verify'):
        base = cur
        if a.mode == 'verify':
            if not bak_ed or not bak_ed.exists():
                print(f'❌ 缺少改前基准 {bak_ed.name if bak_ed else "(无 tag)"}，无法校验')
                return 1
            base = read_enemy(bak_ed)
        plan = build_plan(order, groups, base, wave_from, wave_to, a.factor, a.target)
        print(f'L01 W{wave_from}–W{wave_to} {label}怪 ×{a.factor}（基线 = 改前现值）')
        for w, rid, row, sel, other, old, new, _ in plan:
            print(f'-- W{w} (roundId={rid}, 编组行={row})  EHP {old:,.2f} -> {new:,.2f} '
                  f'({100 * (new / old - 1):+.2f}%)  另 {len(other)} 种不动')
            for i in sel:
                print(f"   {i} {base[i]['name']:<8} {base[i]['hp']:.6f} -> {round(base[i]['hp'] * a.factor, 6):.6f}")
            if not sel:
                print('   （本波没有该类型变体，跳过）')
        tot0 = sum(p[5] for p in plan)
        tot1 = sum(p[6] for p in plan)
        print(f'\n合计 EHP {tot0:,.2f} -> {tot1:,.2f} ({100 * (tot1 / tot0 - 1):+.2f}%)，'
              f'写入 {sum(len(p[3]) for p in plan)} 行')

        if a.mode == 'verify':
            bad = []
            for w, rid, row, sel, other, old, new, _ in plan:
                for i in sel:
                    want = round(base[i]['hp'] * a.factor, 6)
                    if abs(cur[i]['hp'] - want) > 1e-6:
                        bad.append(f'W{w} id={i} 期望 {want} 实为 {cur[i]["hp"]}')
                for i in other:
                    if abs(cur[i]['hp'] - base[i]['hp']) > 1e-9:
                        bad.append(f'W{w} 非目标 id={i} 不应改动 实为 {cur[i]["hp"]}')
            if bad:
                print('❌ 校验失败：')
                for b in bad[:20]:
                    print('  ' + b)
                return 1
            print(f'✅ 校验通过：W{wave_from}–W{wave_to} {label} = 基线×{a.factor}；非目标未变')
        return 0

    # apply
    if not a.yes:
        raise SystemExit('apply 需要 --yes 显式确认（先用 values 看计划）')
    plan = build_plan(order, groups, cur, wave_from, wave_to, a.factor, a.target)

    if any(a.tag in p[7] for p in plan):
        print(f'⏭ 已带标记 {a.tag}，拒绝重复叠加（乘性改动不可重跑）')
        return 0

    for src, dst in ((L01 / 'EnemyData.xlsx', bak_ed), (L01 / 'EnemyList.xlsx', bak_el)):
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f'备份 -> {dst.name}')

    wb = openpyxl.load_workbook(L01 / 'EnemyData.xlsx')
    ws = wb[wb.sheetnames[0]]
    h = heads(ws)
    for w, rid, row, sel, other, old, new, _ in plan:
        for i in sel:
            r = cur[i]['row']
            ws.cell(r, h['hp']).value = round(cur[i]['hp'] * a.factor, 6)
            d = str(ws.cell(r, h['desc']).value or '')
            ws.cell(r, h['desc']).value = f'{d} | {a.tag}: {a.target} x{a.factor} (W{w})'
    wb.save(L01 / 'EnemyData.xlsx')

    wb = openpyxl.load_workbook(L01 / 'EnemyList.xlsx')
    ws = wb['Sheet1']
    h = heads(ws)
    for w, rid, row, sel, other, old, new, desc in plan:
        parts = desc.split(' | ')
        if re.search(r'EHP=[\d.]+', parts[0]):
            parts[0] = re.sub(r'EHP=[\d.]+', f'EHP={new:.6f}', parts[0], count=1)
        ws.cell(row, h['desc']).value = ' | '.join(parts) + f' | {a.tag}: {a.target} x{a.factor} (EHP={new:.6f})'
    wb.save(L01 / 'EnemyList.xlsx')

    print('已写入：')
    for w, rid, row, sel, other, old, new, _ in plan:
        print(f'  W{w}: {len(sel)} 个{label}变体  EHP {old:,.2f} -> {new:,.2f}')
    print(f'备注已追加 {a.tag}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
