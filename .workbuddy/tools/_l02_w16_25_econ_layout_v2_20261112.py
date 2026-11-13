import json
import math
import os
import re
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile

import numpy as np

ROOT = Path('D:/FreedomTower_1')
OUT = ROOT / 'Library/BalanceStage/l02-w16-w25-econ-layout-v2-20261112'
sys.path.insert(0, str(ROOT / '.workbuddy/tools'))
spec = __import__('importlib.util').util.spec_from_file_location(
    'source_trend', ROOT / 'Library/BalanceStage/l02-w16-w25-source-trend-20261111/tune.py'
)
S = __import__('importlib.util').util.module_from_spec(spec)
spec.loader.exec_module(S)
SOURCE = S.SOURCE
TOWER_DPS = 13 / 0.410
TOWER_L3_COST = 100
AIR_LAYOUT_SLOTS = 72
GROUND_LAYOUT_SLOTS = 128


def read_db():
    return {name: S.records(name) for name in ('SceneInfo', 'RoundData', 'EnemyList', 'EnemyData')}


def state():
    paths = list((ROOT / 'Luban/Config/Datas').rglob('*.xlsx'))
    paths += [p for d in ('Assets/ConfigJson', 'Assets/Gen') for p in (ROOT / d).rglob('*') if p.is_file()]
    return {p.relative_to(ROOT).as_posix(): S.sha(p) for p in paths}


def wave_inputs(db):
    scene = db['SceneInfo'][2].values
    enemies = db['EnemyData']
    gold = float(scene['initialGold'])
    waves = []
    enemy_waves = {}
    for wave, rid in enumerate(S.seq(scene['RoundList']), 1):
        rd = db['RoundData'][rid].values
        counts = {}
        events = []
        offset = float(rd['interval'])
        for group_id in S.seq(rd['EnemyIndexs']):
            group = db['EnemyList'][group_id].values
            ids = S.seq(group['EnemyIndexs'])
            start = offset + float(group['interval'])
            gap = float(group['enemyInterval'])
            for i, enemy_id in enumerate(ids):
                counts[enemy_id] = counts.get(enemy_id, 0) + 1
                events.append((start + i * gap, enemy_id))
            offset = max(offset, start + gap * max(1, len(ids)))
        ehp = {'ground': 0.0, 'air': 0.0}
        class_counts = {'ground': 0, 'air': 0}
        speeds = {'ground': [], 'air': []}
        for enemy_id, count in counts.items():
            values = enemies[enemy_id].values
            kind = 'air' if int(values['isFlying']) != 0 else 'ground'
            class_counts[kind] += count
            ehp[kind] += count * float(values['hp']) / (1 - float(values['armor']))
            speeds[kind].extend([float(values['speed'])] * count)
            enemy_waves.setdefault(enemy_id, []).append(wave)
        exposure = {}
        for kind in ('ground', 'air'):
            times = [t for t, enemy_id in events
                     if ('air' if int(enemies[enemy_id].values['isFlying']) != 0 else 'ground') == kind]
            avg_speed = float(np.mean(speeds[kind])) if speeds[kind] else 0
            exposure[kind] = ((max(times) - min(times)) / 1000 + 15 / avg_speed
                              if times and avg_speed > 0 else 0)
        kill_gold = sum(count * float(enemies[eid].values['reward']) for eid, count in counts.items())
        start_gold = gold
        gold += kill_gold + float(rd['rewardGold'])
        air_slots = min(AIR_LAYOUT_SLOTS, start_gold / TOWER_L3_COST)
        air_capacity_dps = air_slots * TOWER_DPS
        ground_slots = min(GROUND_LAYOUT_SLOTS, start_gold / TOWER_L3_COST)
        waves.append({
            'wave': wave, 'roundId': rid, 'goldStart': start_gold, 'goldEnd': gold,
            'counts': counts, 'groundCount': class_counts['ground'], 'airCount': class_counts['air'],
            'groundEHP': ehp['ground'], 'airEHP': ehp['air'],
            'groundExposureSec': exposure['ground'], 'airExposureSec': exposure['air'],
            'groundAffordableL3Slots': ground_slots, 'groundLayoutSlots': GROUND_LAYOUT_SLOTS,
            'airAffordableL3Slots': air_slots, 'airCoverageSlots': AIR_LAYOUT_SLOTS,
            'airCapacityDPS': air_capacity_dps,
            'airUtilization': (ehp['air'] / exposure['air'] / air_capacity_dps
                               if exposure['air'] and air_capacity_dps else 0),
            'killGold': kill_gold, 'clearGold': float(rd['rewardGold']),
        })
    return waves, enemy_waves


def fit_line(xs, ys):
    slope, intercept = np.polyfit(np.asarray(xs, dtype=float), np.asarray(ys, dtype=float), 1)
    return float(slope), float(intercept)


def backtest(waves):
    ground_errors, air_errors = [], []
    # Rolling origin: fit through W9..W14 and forecast 1..5 waves, stopping at W15.
    for train_end in range(8, 14):
        train = waves[4:train_end + 1]
        gs, gi = fit_line([x['wave'] for x in train],
                          [x['groundEHP'] / x['groundAffordableL3Slots'] for x in train])
        aas, aai = fit_line([x['wave'] for x in train], [x['airUtilization'] for x in train])
        for actual in waves[train_end + 1:min(train_end + 6, 15)]:
            ground_pred = (gi + gs * actual['wave']) * actual['groundAffordableL3Slots']
            air_use = max(0, min(1, aai + aas * actual['wave']))
            air_pred = air_use * actual['airCapacityDPS'] * actual['airExposureSec']
            ground_errors.append(abs(ground_pred / actual['groundEHP'] - 1))
            air_errors.append(abs(air_pred / actual['airEHP'] - 1))
    return {
        'rollingOrigins': 6, 'predictionCount': len(ground_errors),
        'groundMAPE': float(np.mean(ground_errors)), 'groundMaxAPE': float(max(ground_errors)),
        'airMAPE': float(np.mean(air_errors)), 'airMaxAPE': float(max(air_errors)),
    }


def plan():
    assert not OUT.exists(), f'Audit directory already exists: {OUT}'
    db = read_db()
    waves, enemy_waves = wave_inputs(db)
    ref = waves[4:15]
    ground_slope, ground_intercept = fit_line(
        [x['wave'] for x in ref], [x['groundEHP'] / x['groundAffordableL3Slots'] for x in ref])
    air_slope, air_intercept = fit_line(
        [x['wave'] for x in ref], [x['airUtilization'] for x in ref])
    changes = []
    for wave in waves[15:25]:
        target_ground = max(0, ground_intercept + ground_slope * wave['wave']) * wave['groundAffordableL3Slots']
        target_air_util = max(0, min(1, air_intercept + air_slope * wave['wave']))
        target_air = target_air_util * wave['airCapacityDPS'] * wave['airExposureSec']
        wave['targetGroundEHP'] = target_ground
        wave['targetAirUtilization'] = target_air_util
        wave['targetAirEHP'] = target_air
        wave['groundScale'] = target_ground / wave['groundEHP']
        wave['airScale'] = target_air / wave['airEHP']
        for enemy_id, count in wave['counts'].items():
            rec = db['EnemyData'][enemy_id]
            values = rec.values
            kind = 'air' if int(values['isFlying']) != 0 else 'ground'
            assert enemy_waves[enemy_id] == [wave['wave']], f'Shared enemy id {enemy_id}'
            old_hp = float(values['hp'])
            scale = wave['airScale'] if kind == 'air' else wave['groundScale']
            new_hp = round(old_hp * scale, 6)
            changes.append({
                'wave': wave['wave'], 'roundId': wave['roundId'], 'id': enemy_id,
                'name': values['name'], 'kind': kind,
                'cell': rec.source['columns']['hp'] + str(rec.source['row']),
                'old': old_hp, 'new': new_hp, 'count': count,
                'armor': float(values['armor']), 'scale': scale,
            })
    assert len(changes) == 51, len(changes)
    baseline = state()
    OUT.mkdir(parents=True)
    shutil.copy2(SOURCE, OUT / 'EnemyData.before.xlsx')
    shutil.copy2(ROOT / 'Assets/ConfigJson/tbenemydata.json', OUT / 'tbenemydata.before.json')
    (OUT / 'baseline.json').write_text(json.dumps(baseline, indent=2), encoding='utf-8')
    plan_data = {
        'source': str(SOURCE), 'sourceSha256': S.sha(SOURCE),
        'method': 'Ground target = OLS(W5-W15, ground EHP/affordable L3 tower equivalents vs wave) '
                  '× min(128 legal ground slots, start gold/100); '
                  'air target = OLS(W5-W15, measured air DPS utilization vs wave) × '
                  'min(72 effective air-cover slots, start gold/100) × L3 normal tower DPS × '
                  'actual air exposure window. EHP is Σ(count×hp/(1-armor)); class HP is scaled '
                  'uniformly within each wave.',
        'groundFit': {'slopeEHPPerAffordableSlotPerWave': ground_slope,
                      'interceptEHPPerAffordableSlot': ground_intercept},
        'airUtilizationFit': {'slope': air_slope, 'intercept': air_intercept,
                              'towerDPS': TOWER_DPS, 'towerL3Cost': TOWER_L3_COST,
                              'effectiveAirSlots': AIR_LAYOUT_SLOTS,
                              'groundLegalLayoutSlots': GROUND_LAYOUT_SLOTS},
        'backtest': backtest(waves), 'waves': waves, 'changes': changes,
    }
    (OUT / 'plan.json').write_text(json.dumps(plan_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'groundFit': plan_data['groundFit'], 'airFit': plan_data['airUtilizationFit'],
                      'backtest': plan_data['backtest'],
                      'waves': [{k: x[k] for k in ('wave', 'goldStart', 'groundEHP', 'targetGroundEHP',
                                                    'airEHP', 'targetAirEHP', 'targetAirUtilization',
                                                    'groundScale', 'airScale')} for x in waves[15:25]],
                      'changeCount': len(changes)}, ensure_ascii=False, indent=2))


def replace_cell(xml, cell, value):
    pattern = rb'(<c\b[^>]*\br="' + cell.encode() + rb'"[^>]*>.*?<v>)([^<]*)(</v>.*?</c>)'
    matches = list(re.finditer(pattern, xml, re.S))
    assert len(matches) == 1, (cell, len(matches))
    match = matches[0]
    old = float(match.group(2))
    return xml[:match.start(2)] + str(value).encode() + xml[match.end(2):], old


def apply():
    p = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    assert S.sha(SOURCE) == p['sourceSha256'], 'Source changed after planning; stop and re-read.'
    with ZipFile(SOURCE) as z:
        members = {info.filename: (info, z.read(info.filename)) for info in z.infolist()}
    sheet = 'xl/worksheets/sheet1.xml'
    original = members[sheet][1]
    patched = original
    for change in p['changes']:
        patched, old = replace_cell(patched, change['cell'], change['new'])
        assert old == change['old'], change
    temp = OUT / 'EnemyData.patched.xlsx'
    with ZipFile(temp, 'w') as z:
        for name, (info, data) in members.items():
            z.writestr(info, patched if name == sheet else data)
    with ZipFile(temp) as z:
        assert set(z.namelist()) == set(members)
        for name, (_, data) in members.items():
            if name != sheet:
                assert z.read(name) == data, name
        reverted = z.read(sheet)
        for change in p['changes']:
            pattern = (rb'(<c\b[^>]*\br="' + change['cell'].encode()
                       + rb'"[^>]*>.*?<v>)([^<]*)(</v>.*?</c>)')
            token = re.search(pattern, original, re.S).group(2)
            reverted = re.sub(pattern, lambda m: m.group(1) + token + m.group(3),
                               reverted, count=1, flags=re.S)
        assert reverted == original, 'XLSX sheet changed outside the hp whitelist.'
    assert S.sha(SOURCE) == p['sourceSha256'], 'Source changed before commit.'
    shutil.copy2(SOURCE, OUT / 'EnemyData.backup.xlsx')
    os.replace(temp, SOURCE)
    verify()


def verify():
    p = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    before = {int(r.values['id']): r for r in S.read_xlsx(OUT / 'EnemyData.before.xlsx')}
    after = {int(r.values['id']): r for r in S.read_xlsx(SOURCE)}
    expected = {(c['id'], 'hp', c['old'], c['new']) for c in p['changes']}
    actual = set()
    for enemy_id, old_row in before.items():
        new_row = after[enemy_id]
        assert {k: v for k, v in old_row.source.items() if k != 'path'} == {
            k: v for k, v in new_row.source.items() if k != 'path'}
        for field, old in old_row.values.items():
            new = new_row.values[field]
            if new != old:
                actual.add((enemy_id, field, float(old), float(new)))
    assert actual == expected, {'actual': sorted(actual), 'expected': sorted(expected)}
    with ZipFile(OUT / 'EnemyData.before.xlsx') as bz, ZipFile(SOURCE) as az:
        assert bz.namelist() == az.namelist()
        for name in bz.namelist():
            if name != 'xl/worksheets/sheet1.xml':
                assert bz.read(name) == az.read(name), name
        old_xml = bz.read('xl/worksheets/sheet1.xml')
        new_xml = az.read('xl/worksheets/sheet1.xml')
        reverted = new_xml
        for change in p['changes']:
            pattern = (rb'(<c\b[^>]*\br="' + change['cell'].encode()
                       + rb'"[^>]*>.*?<v>)([^<]*)(</v>.*?</c>)')
            token = re.search(pattern, old_xml, re.S).group(2)
            reverted = re.sub(pattern, lambda m: m.group(1) + token + m.group(3),
                              reverted, count=1, flags=re.S)
        assert reverted == old_xml
    baseline = json.loads((OUT / 'baseline.json').read_text(encoding='utf-8'))
    current = state()
    changed = [path for path in baseline if baseline[path] != current[path]]
    assert set(changed) == {'Luban/Config/Datas/Levels/L02/EnemyData.xlsx'}, changed
    result = {'sourceReadback': len(actual), 'whitelist': len(expected), 'outsideWhitelist': 0,
              'changedFilesSinceBaseline': changed, 'packageMembersOutsideCellsUnchanged': True,
              'sourceSha256': S.sha(SOURCE)}
    (OUT / 'source-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


def finalize():
    p = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    baseline = json.loads((OUT / 'baseline.json').read_text(encoding='utf-8'))
    current = state()
    changed_files = [path for path in baseline if baseline[path] != current[path]]
    expected_files = {
        'Luban/Config/Datas/Levels/L02/EnemyData.xlsx',
        'Assets/ConfigJson/tbenemydata.json',
    }
    assert set(changed_files) == expected_files, changed_files
    before_json = json.loads((OUT / 'tbenemydata.before.json').read_text(encoding='utf-8-sig'))
    after_json = json.loads((ROOT / 'Assets/ConfigJson/tbenemydata.json').read_text(encoding='utf-8-sig'))
    old_rows = {int(x['id']): x for x in before_json}
    new_rows = {int(x['id']): x for x in after_json}
    expected = {(c['id'], 'hp'): c for c in p['changes']}
    changed_fields = set()
    for enemy_id, old_row in old_rows.items():
        new_row = new_rows[enemy_id]
        for field, old_value in old_row.items():
            new_value = new_row[field]
            if old_value != new_value:
                key = (enemy_id, field)
                assert key in expected, (enemy_id, field)
                change = expected[key]
                assert __import__('struct').pack('f', float(old_value)) == __import__('struct').pack('f', change['old'])
                assert __import__('struct').pack('f', float(new_value)) == __import__('struct').pack('f', change['new'])
                changed_fields.add(key)
    assert changed_fields == set(expected)
    unchanged_json = []
    for path, digest in baseline.items():
        if path.startswith('Assets/ConfigJson/') and path != 'Assets/ConfigJson/tbenemydata.json':
            assert current[path] == digest, path
            unchanged_json.append(path)
    mtime_updated = (ROOT / 'Assets/ConfigJson/tbenemydata.json').stat().st_mtime_ns > (
        (OUT / 'tbenemydata.before.json').stat().st_mtime_ns)
    assert mtime_updated
    scene = json.loads((ROOT / 'Assets/ConfigJson/tbsceneinfo.json').read_text(encoding='utf-8-sig'))
    assert len(scene) == 30 and all(x['initialGold'] == 100 for x in scene)
    result = {
        'changedFiles': changed_files, 'sourceCellsChanged': len(p['changes']),
        'exportedHpFieldsChanged': len(changed_fields), 'outsideWhitelistChanges': 0,
        'unchangedJsonFiles': len(unchanged_json), 'tbenemydataMtimeUpdated': mtime_updated,
        'initialGold100Levels': len(scene), 'backtest': p['backtest'],
    }
    (OUT / 'final-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    lines = [
        '# L02 W16–W25 HP：经济与塔位回归重算（2026-11-12）', '',
        '范围：仅 L02 W16–W25 的敌人 hp 字段，地面、空中均调整，共 51 格（地面 41 格，含 W25 Rat；空中 Bat 10 格）。W1–W15、其他关卡及数量、奖励、速度、护甲、出怪时序均不改。', '',
        '## 计算', '',
        'EHP = Σ(出生数量 × hp / (1 − armor))。波次按 SceneInfo.RoundList → RoundData.EnemyIndexs → EnemyList.EnemyIndexs 展开；空地类型只按 EnemyData.isFlying 判定。', '',
        f"地面：先算 W5–W15 的地面 EHP / 可购买满级普通塔等价数，再对该比值按波次做一次最小二乘回归；目标 EHP = 回归值 × min(128 个合法地面塔位, 开波金币 / 100)。W16–W25 的理论金币均未达到 12,800 金，当前仍由经济可买塔数约束。斜率 {p['groundFit']['slopeEHPPerAffordableSlotPerWave']:.6f} EHP/槽/波，截距 {p['groundFit']['interceptEHPPerAffordableSlot']:.6f}。", '',
        f"空中：W5–W15 的对空利用率 = 空中 EHP / 实际受火窗口 / (可买满级塔等价数 × 31.707317 DPS)，回归利用率随波次一次增长。目标 EHP = 预测利用率 × min(72 个射程内有效空中塔位, 开波金币 / 100) × 31.707317 DPS × 实际受火窗口。有效空中塔位上限取自 L02 spacing-1 合法布阵数据。利用率斜率 {p['airUtilizationFit']['slope']:.8f}/波，截距 {p['airUtilizationFit']['intercept']:.8f}。", '',
        f"回测：W5 起始，训练终点 W9–W14 滚动向前预测最多 5 波、共 {p['backtest']['predictionCount']} 个历史预测；地面 MAPE {p['backtest']['groundMAPE']:.2%}、最大误差 {p['backtest']['groundMaxAPE']:.2%}；空中 MAPE {p['backtest']['airMAPE']:.2%}、最大误差 {p['backtest']['airMaxAPE']:.2%}。这衡量历史外推误差，不等于战斗胜率。", '',
        '同波同类型 HP 统一按目标 EHP / 改前 EHP 缩放，保留该类各怪相对比例。', '',
        '## 波次结果', '',
        '| 波次 | 开波金币 | 地面 EHP 改前→改后 | 地面倍率 | 空中 EHP 改前→改后 | 空中利用率 | 空中倍率 |',
        '|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for w in p['waves'][15:25]:
        lines.append(f"| W{w['wave']} | {w['goldStart']:.2f} | {w['groundEHP']:.2f} → {w['targetGroundEHP']:.2f} | {w['groundScale']:.4f} | {w['airEHP']:.2f} → {w['targetAirEHP']:.2f} | {w['targetAirUtilization']:.2%} | {w['airScale']:.4f} |")
    lines += ['', '## 逐格 HP', '', '| 波次 | ID | 怪物 | 类别 | 单元格 | 旧 HP | 新 HP |', '|---:|---:|---|---|---|---:|---:|']
    for c in p['changes']:
        lines.append(f"| W{c['wave']} | {c['id']} | {c['name']} | {c['kind']} | {c['cell']} | {c['old']:.6f} | {c['new']:.6f} |")
    lines += ['', '## 校验', '',
              f"- 源表 {len(p['changes'])}/{len(p['changes'])} 格回读通过；白名单外单元格 0 变化；XLSX 内除白名单数字外包成员内容完全一致。",
              f"- Luban 菜单实际返回成功，导出 11 张表；{len(changed_fields)} 个 JSON HP 字段与源表白名单一致，其他字段 0 变化；其余 {len(unchanged_json)} 个 ConfigJson 文件内容不变；tbenemydata.json mtime 更新。",
              '- Unity `TBEnemyData` 等 11 张表加载完成，`[Config]` 汇总未列失败表；另有既存交叉引用 Warning（22,103 条），内容为全关卡波次与当前关卡作用域比较，不是本轮 HP 配置加载失败。Play 仅用于配置加载确认，未推进波次。',
              '- 空中出生顺序源表和 JSON 均 PASS：L02 25 波、1,923 只空中怪、相邻空中对 0、引用错误 0。30 关 initialGold 全为 100。',
              '- Unity 未新增 Console error；保留的历史异常为 `Unity Remote requirements check failed`。编辑器已退出 Play，恢复 Boot，ready_for_tools=true。', '',
              '逐格基准与公式数据见同目录 `plan.json`；源表改前副本与白名单回读记录也保留在该目录。']
    report = ROOT / 'Artifacts/L02_W16_W25_Economy_Layout_Recalculated_20261112.md'
    report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    {'plan': plan, 'apply': apply, 'verify': verify, 'finalize': finalize}[sys.argv[1]]()
