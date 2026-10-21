#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阶段 A：把 6 张聚合关卡表物理拆成「每关一个目录、目录内每张表一个文件」。数值零变化。

结构（拆分后）：
    Luban/Config/Datas/
      Levels/L01/SceneInfo.xlsx  RoundData.xlsx  EnemyList.xlsx  LevelMap.xlsx  LevelRating.xlsx  EnemyData.xlsx
      ... L02..L30
      EnemyData.xlsx          <- 只留 132 行原型（id < 100000）
      TowerInfo.xlsx ...      <- 不动
      __tables__.xlsx         <- 6 张关卡表的 input 改成 30 个相对路径

设计要点
--------
1) **不用 openpyxl 重建工作簿，而是复制原文件后 delete_rows**：
   openpyxl 的 _style 是「样式表下标」，跨工作簿复制下标会指错样式；
   同一个工作簿内删行则样式对象跟着走，表头/列宽/冻结全部原样保留。
2) **归属判据一律走引用链**，不用 id 数值范围猜关卡：
   RoundList → RoundData → EnemyList；EnemyData 用 desc 里的 level=。
3) 脚本只做迁移，不碰任何数值；跑完直接调 Luban 与基线逐字段比对。
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / 'Luban/Config/Datas'
LEVELS = DATA / 'Levels'
DESIGN = ROOT / 'Luban/BalanceDesign'
VERSIONS = DESIGN / 'Versions'
EVIDENCE = ROOT / 'Docs/BalanceEvidence'
HEADER_ROWS = 3
FIRST_DATA_ROW = 4

# 表 -> (文件名, 归属方式)
LEVEL_TABLES = {
    'TBRoundData': 'RoundData',
    'TBEnemyList': 'EnemyList',
    'TBSceneInfo': 'SceneInfo',
    'TBLevelMap': 'LevelMap',
    'TBLevelRating': 'LevelRating',
    'TBEnemyData': 'EnemyData',
}


def level_dir(L: int) -> pathlib.Path:
    return LEVELS / f'L{L:02d}'


def rel_level_path(L: int, name: str) -> str:
    return f'Levels/L{L:02d}/{name}.xlsx'


def sheet_of(wb):
    return wb[wb.sheetnames[0]]


def headers_of(ws):
    return {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}


def read_rows(path: pathlib.Path):
    """返回 (header_rows_values, column_count, [(excel_row, {field: value}), ...])。"""
    import openpyxl
    wb = openpyxl.load_workbook(path)
    ws = sheet_of(wb)
    heads = headers_of(ws)
    header = [[ws.cell(r, c).value for c in range(1, ws.max_column + 1)] for r in range(1, HEADER_ROWS + 1)]
    rows = []
    for r in range(FIRST_DATA_ROW, ws.max_row + 1):
        if ws.cell(r, heads['id']).value is None:
            continue
        rows.append((r, {f: ws.cell(r, c).value for f, c in heads.items()}))
    cols = ws.max_column
    wb.close()
    return header, cols, rows


def parse_list(text) -> list[int]:
    if text is None:
        return []
    if isinstance(text, (list, tuple)):
        return [int(x) for x in text]
    raw = str(text).strip()
    if not raw:
        return []
    return [int(x) for x in raw.split(',') if str(x).strip()]


def split_rows(text) -> list[str]:
    if isinstance(text, (list, tuple)):
        return [str(x) for x in text]
    return [x for x in str(text).split('|')]


def as_cell_text(value, field):
    """把 python 列表还原成 xlsx 里实际存储的文本（cells 用 |，其余用 ,）。"""
    if isinstance(value, (list, tuple)):
        return ('|' if field == 'cells' else ',').join(map(str, value))
    return value


def dump(rows) -> dict:
    return {row['id']: row for _, row in rows}


def build_ownership(tables_root: pathlib.Path):
    """按引用链算出每张表每一行属于哪一关。返回 {表名: {id: level}} 与断言信息。"""
    _, _, scene_rows = read_rows(tables_root / 'SceneInfo.xlsx')
    _, _, round_rows = read_rows(tables_root / 'RoundData.xlsx')
    _, _, list_rows = read_rows(tables_root / 'EnemyList.xlsx')
    _, _, map_rows = read_rows(tables_root / 'LevelMap.xlsx')
    _, _, rating_rows = read_rows(tables_root / 'LevelRating.xlsx')
    _, _, enemy_rows = read_rows(tables_root / 'EnemyData.xlsx')

    scenes = dump(scene_rows)
    rounds = dump(round_rows)
    lists = dump(list_rows)

    scene_owner = {L: L for L in scenes}
    round_owner, list_owner = {}, {}
    for L, row in scenes.items():
        rids = parse_list(row['RoundList'])
        assert len(rids) == len(set(rids)), f'L{L} RoundList 有重复 id'
        for rid in rids:
            assert rid in rounds, f'L{L} RoundList 引用了不存在的 round {rid}'
            assert rid not in round_owner, f'round {rid} 被多关引用：{round_owner[rid]} / {L}'
            round_owner[rid] = L
            children = parse_list(rounds[rid]['EnemyIndexs'])
            assert len(children) == 1, f'round {rid} 必须且只能引用 1 个 enemyList'
            lid = children[0]
            assert lid in lists, f'round {rid} 引用了不存在的 enemyList {lid}'
            assert lid not in list_owner, f'enemyList {lid} 被多关引用：{list_owner[lid]} / {L}'
            list_owner[lid] = L

    assert set(round_owner) == set(rounds), f'RoundData 有行无人引用：{sorted(set(rounds) - set(round_owner))[:10]}'
    assert set(list_owner) == set(lists), f'EnemyList 有行无人引用：{sorted(set(lists) - set(list_owner))[:10]}'

    map_owner = {}
    for _, row in map_rows:
        assert int(row['levelId']) == int(row['id']), f'LevelMap id/levelId 不一致：{row["id"]}'
        map_owner[int(row['id'])] = int(row['levelId'])
    rating_owner = {int(row['id']): int(row['id']) for _, row in rating_rows}

    # EnemyData：原型进主表；变体按 desc 的 level= 归属
    enemy_owner, protos = {}, []
    for _, row in enemy_rows:
        eid = int(row['id'])
        if eid < 100000:
            protos.append(row)
            continue
        desc = str(row.get('desc') or '')
        m = re.search(r'(?:^|[;\s])level=(\d+)', desc)
        assert m, f'变体 {eid} 的 desc 里没有 level=：{desc!r}'
        L = int(m.group(1))
        assert 1 <= L <= 30, f'变体 {eid} 的 level={L} 越界'
        assert eid not in enemy_owner, f'变体 {eid} 重复'
        enemy_owner[eid] = L

    # 每关每波引用的变体必须落在本关（跨关引用会让拆表直接崩）
    by_id = {int(row['id']): row for _, row in enemy_rows}
    for lid, L in list_owner.items():
        for eid in parse_list(lists[lid]['EnemyIndexs']):
            assert eid in by_id, f'enemyList {lid} 引用了不存在的 enemy {eid}'
            owner = enemy_owner.get(eid)
            assert owner is None or owner == L, f'enemy {eid} 属于 L{owner} 却被 L{L} 的 enemyList {lid} 使用'

    owners = {
        'TBSceneInfo': scene_owner,
        'TBRoundData': round_owner,
        'TBEnemyList': list_owner,
        'TBLevelMap': map_owner,
        'TBLevelRating': rating_owner,
        'TBEnemyData': enemy_owner,
    }
    return owners, protos


def plan_split(owners):
    levels = sorted({L for table in owners.values() for L in table.values()})
    assert levels == list(range(1, 31)), f'关卡号不是 1..30：{levels}'
    plan = collections.OrderedDict()
    for L in levels:
        plan[L] = {name: sorted(i for i, owner in owners[tbl].items() if owner == L)
                   for tbl, name in LEVEL_TABLES.items()}
    return plan


def contiguous(runs):
    """[1,2,3,7,8] -> [(1,3),(7,2)]，把逐行删除合并成区间删除（10773 行逐行删要几分钟）。"""
    out = []
    for r in runs:
        if out and r == out[-1][0] + out[-1][1]:
            out[-1] = (out[-1][0], out[-1][1] + 1)
        else:
            out.append((r, 1))
    return out


def extract(src: pathlib.Path, dst: pathlib.Path, keep_ids, name: str, id_field='id'):
    """复制 src 后删除不属于 keep_ids 的数据行（同工作簿内删行，样式/列宽原样保留）。"""
    import openpyxl
    dst.parent.mkdir(parents=True, exist_ok=True)
    same = src.resolve() == dst.resolve()
    if not same:
        shutil.copy2(src, dst)
    wb = openpyxl.load_workbook(dst)
    ws = sheet_of(wb)
    heads = headers_of(ws)
    columns = ws.max_column
    header_before = [[ws.cell(r, c).value for c in range(1, columns + 1)] for r in range(1, HEADER_ROWS + 1)]
    keep = set(int(x) for x in keep_ids)
    drop = []
    for r in range(FIRST_DATA_ROW, ws.max_row + 1):
        v = ws.cell(r, heads[id_field]).value
        if v is None or int(v) not in keep:
            drop.append(r)
    for start, count in reversed(contiguous(drop)):
        ws.delete_rows(start, count)
    header_after = [[ws.cell(r, c).value for c in range(1, columns + 1)] for r in range(1, HEADER_ROWS + 1)]
    assert header_after == header_before, f'{name} 表头被 delete_rows 破坏'
    wb.save(dst)
    wb.close()
    return len(keep)


def rewrite_tables_input(dry: bool):
    import openpyxl
    path = DATA / '__tables__.xlsx'
    wb = openpyxl.load_workbook(path)
    ws = sheet_of(wb)
    heads = headers_of(ws)
    col_input, col_name = heads['input'], heads['full_name']
    wanted = {}
    for tbl, name in LEVEL_TABLES.items():
        paths = [rel_level_path(L, name) for L in range(1, 31)]
        if tbl == 'TBEnemyData':
            paths = ['EnemyData.xlsx'] + paths
        wanted[tbl] = ','.join(paths)
    changed = []
    for r in range(FIRST_DATA_ROW, ws.max_row + 1):
        tbl = ws.cell(r, col_name).value
        if tbl in wanted:
            before = ws.cell(r, col_input).value
            if before != wanted[tbl]:
                changed.append({'table': tbl, 'before': before, 'after': wanted[tbl]})
                if not dry:
                    ws.cell(r, col_input).value = wanted[tbl]
    if changed and not dry:
        wb.save(path)
    wb.close()
    return changed


def run_luban(out_dir: pathlib.Path, cache: pathlib.Path):
    exe = ROOT / 'Luban/Tools/Luban.ClientServer/Luban.ClientServer.exe'
    args = [str(exe), '-j', 'cfg', '-c', str(cache), '--',
            '-d', str(ROOT / 'Luban/Config/Defines/__root__.xml'),
            '--input_data_dir', str(DATA),
            '--output_code_dir', str(out_dir / 'Gen'),
            '--output_data_dir', str(out_dir / 'ConfigJson'),
            '--gen_types', 'code_cs_unity_json,data_json', '-s', 'all']
    env = os.environ.copy()
    env['DOTNET_ROLL_FORWARD'] = 'LatestMajor'
    result = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=300)
    (out_dir / 'luban.log').write_text(result.stdout + '\n' + result.stderr, encoding='utf-8')
    if result.returncode:
        raise RuntimeError('Luban 失败，见 ' + str(out_dir / 'luban.log') + '\n' + result.stdout[-4000:])
    return out_dir / 'ConfigJson'


def semantic_diff(a_dir: pathlib.Path, b_dir: pathlib.Path):
    """按 id 排序逐字段比对，忽略行序与键序。返回 (报告, 是否一致)。"""
    report = collections.OrderedDict()
    ok = True
    for path in sorted(a_dir.glob('tb*.json')):
        table = path.stem
        other = b_dir / path.name
        if not other.is_file():
            report[table] = {'status': 'missing_in_after'}
            ok = False
            continue
        left = json.loads(path.read_text(encoding='utf-8-sig'))
        right = json.loads(other.read_text(encoding='utf-8-sig'))
        left = sorted(left, key=lambda r: r['id'])
        right = sorted(right, key=lambda r: r['id'])
        diffs = []
        if len(left) != len(right):
            diffs.append({'kind': 'rowCount', 'before': len(left), 'after': len(right)})
        for x, y in zip(left, right):
            if x['id'] != y['id']:
                diffs.append({'kind': 'idOrder', 'before': x['id'], 'after': y['id']})
                continue
            for field in sorted(set(x) | set(y)):
                if x.get(field) != y.get(field):
                    diffs.append({'kind': 'field', 'id': x['id'], 'field': field,
                                  'before': x.get(field), 'after': y.get(field)})
                    if len(diffs) > 40:
                        break
            if len(diffs) > 40:
                break
        report[table] = {'status': 'equal' if not diffs else 'differs',
                         'rowsBefore': len(left), 'rowsAfter': len(right),
                         'differenceCount': len(diffs), 'differences': diffs[:40]}
        ok = ok and not diffs
    return report, ok


def sha(path: pathlib.Path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main(argv=None):
    parser = argparse.ArgumentParser(description='阶段 A：把聚合关卡表拆成每关一目录')
    parser.add_argument('--dry-run', action='store_true', help='只打印将生成的文件与行数，不落盘')
    parser.add_argument('--skip-luban', action='store_true')
    parser.add_argument('--stamp', default=datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    args = parser.parse_args(argv)
    dry = args.dry_run

    owners, protos = build_ownership(DATA)
    plan = plan_split(owners)
    print(json.dumps({'stage': 'ownership', 'levels': len(plan),
                      'protoRows': len(protos),
                      'variantRows': len(owners['TBEnemyData'])},
                     ensure_ascii=False))

    if dry:
        for L in (1, 15, 30):
            print(json.dumps({'level': L, 'rows': {k: len(v) for k, v in plan[L].items()},
                              'firstRoundIds': plan[L]['RoundData'][:5],
                              'firstVariantIds': plan[L]['EnemyData'][:3]}, ensure_ascii=False))
        total = sum(len(v) for L in plan for v in plan[L].values())
        print(json.dumps({'stage': 'dry-run', 'files': 30 * 6, 'dataRows': total}, ensure_ascii=False))
        return

    # 1) 备份
    backup = VERSIONS / f'split-{args.stamp}'
    if backup.exists():
        raise RuntimeError('备份目录已存在，换一个 --stamp：' + str(backup))
    (backup / 'Datas').parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(DATA, backup / 'Datas', ignore=shutil.ignore_patterns('Levels'))
    shutil.copy2(DESIGN / 'balance_design.json', backup / 'balance_design.json')
    shutil.copy2(DESIGN / 'applied_state.json', backup / 'applied_state.json')
    print(json.dumps({'stage': 'backup', 'path': str(backup.relative_to(ROOT))}, ensure_ascii=False))

    # 2) 拆 6 张表
    written = []
    for L in plan:
        for tbl, name in LEVEL_TABLES.items():
            src = DATA / f'{name}.xlsx'
            dst = level_dir(L) / f'{name}.xlsx'
            kept = extract(src, dst, plan[L][name], name)
            written.append({'table': name, 'level': L, 'rows': kept,
                            'path': str(dst.relative_to(ROOT)).replace('\\', '/')})
    print(json.dumps({'stage': 'split', 'files': len(written)}, ensure_ascii=False))

    # 3) 主表 EnemyData 只留原型
    proto_ids = [int(r['id']) for r in protos]
    extract(DATA / 'EnemyData.xlsx', DATA / 'EnemyData.xlsx', proto_ids, 'EnemyData')
    print(json.dumps({'stage': 'prototypes', 'rows': len(proto_ids)}, ensure_ascii=False))

    # 4) 删旧聚合文件（EnemyData 保留）
    removed = []
    for name in ['SceneInfo', 'RoundData', 'EnemyList', 'LevelMap', 'LevelRating']:
        p = DATA / f'{name}.xlsx'
        if p.exists():
            p.unlink()
            removed.append(str(p.relative_to(ROOT)).replace('\\', '/'))
    print(json.dumps({'stage': 'remove_aggregates', 'files': removed}, ensure_ascii=False))

    # 5) 重写 __tables__ 的 input
    changed = rewrite_tables_input(dry=False)
    print(json.dumps({'stage': 'tables_input', 'changed': [c['table'] for c in changed]}, ensure_ascii=False))

    # 6) 校验磁盘结构
    problems = []
    for L in plan:
        for tbl, name in LEVEL_TABLES.items():
            p = level_dir(L) / f'{name}.xlsx'
            if not p.is_file():
                problems.append(f'missing {p}')
                continue
            _, _, rows = read_rows(p)
            if len(rows) != len(plan[L][name]):
                problems.append(f'{p} rows {len(rows)} != {len(plan[L][name])}')
    _, _, proto_rows = read_rows(DATA / 'EnemyData.xlsx')
    if len(proto_rows) != len(protos):
        problems.append(f'EnemyData prototypes {len(proto_rows)} != {len(protos)}')
    if problems:
        raise RuntimeError('结构校验失败：\n' + '\n'.join(problems[:30]))

    if args.skip_luban:
        print(json.dumps({'stage': 'complete', 'luban': 'skipped'}, ensure_ascii=False))
        return

    # 7) Luban 导出并与基线比对
    out = ROOT / 'Library/SplitWork' / f'after-{args.stamp}'
    cfg = run_luban(out, ROOT / 'Library/SplitWork' / f'after-{args.stamp}.cache.meta')
    baseline = ROOT / 'Library/SplitWork/baseline/ConfigJson'
    if not baseline.is_dir():
        raise RuntimeError('缺少基线导出：先跑一次 Luban 到 Library/SplitWork/baseline/ConfigJson')
    report, ok = semantic_diff(baseline, cfg)

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    payload = {
        'stage': 'A-split-level-tables',
        'stamp': args.stamp,
        'backup': str(backup.relative_to(ROOT)).replace('\\', '/'),
        'levelFiles': len(written),
        'prototypeRows': len(protos),
        'variantRows': len(owners['TBEnemyData']),
        'aggregateRemoved': removed,
        'tablesInputChanged': [c['table'] for c in changed],
        'rowCounts': {name: {str(L): len(plan[L][name]) for L in plan} for tbl, name in LEVEL_TABLES.items()},
        'semanticEqual': ok,
        'tables': report,
        'hashes': {t: {'before': sha(baseline / f'{t}.json'), 'after': sha(cfg / f'{t}.json')} for t in report},
    }
    (EVIDENCE / 'split-migration.json').write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'stage': 'complete', 'semanticEqual': ok,
                      'tables': {t: v['status'] for t, v in report.items()},
                      'evidence': 'Docs/BalanceEvidence/split-migration.json'}, ensure_ascii=False))
    if not ok:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
