import importlib.util
import json
import shutil
import struct
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path('D:/FreedomTower_1')
spec = importlib.util.spec_from_file_location('precise_hp', ROOT / '.workbuddy/tools/_l02_w20_air_hp_plateau_20261112.py')
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
OUT = ROOT / 'Library/BalanceStage/l02-w20-w25-ground-plus50-20261112'
P.OUT = OUT
REPORT = ROOT / 'Artifacts/L02_W20_W25_Ground_HP_Plus50_20261112.md'
MULTIPLIER = Decimal('1.50')
LABEL = '上调 50%'
FIRST_WAVE = 20
CELL_COUNT = 25
if len(sys.argv) > 2 and sys.argv[2] == 'minus20':
    OUT = ROOT / 'Library/BalanceStage/l02-w20-w25-ground-minus20-20261112'
    P.OUT = OUT
    REPORT = ROOT / 'Artifacts/L02_W20_W25_Ground_HP_Minus20_20261112.md'
    MULTIPLIER = Decimal('0.80')
    LABEL = '下调 20%'
elif len(sys.argv) > 2 and sys.argv[2] == 'w23minus5':
    OUT = ROOT / 'Library/BalanceStage/l02-w23-w25-ground-minus5-20261112'
    P.OUT = OUT
    REPORT = ROOT / 'Artifacts/L02_W23_W25_Ground_HP_Minus5_20261112.md'
    MULTIPLIER = Decimal('0.95')
    LABEL = '下调 5%'
    FIRST_WAVE = 23
    CELL_COUNT = 13
elif len(sys.argv) > 2 and sys.argv[2] in ('w24plus3', 'w24plus3r2'):
    OUT = ROOT / 'Library/BalanceStage/l02-w24-w25-ground-plus3-20261112'
    P.OUT = OUT
    REPORT = ROOT / 'Artifacts/L02_W24_W25_Ground_HP_Plus3_20261112.md'
    MULTIPLIER = Decimal('1.03')
    LABEL = '上调 3%'
    FIRST_WAVE = 24
    CELL_COUNT = 9
    if sys.argv[2] == 'w24plus3r2':
        OUT = ROOT / 'Library/BalanceStage/l02-w24-w25-ground-plus3-r2-20261112'
        P.OUT = OUT
        REPORT = ROOT / 'Artifacts/L02_W24_W25_Ground_HP_Plus3_R2_20261112.md'
        LABEL = '再次上调 3%'
elif len(sys.argv) > 2 and sys.argv[2] == 'w24plus5':
    OUT = ROOT / 'Library/BalanceStage/l02-w24-w25-ground-plus5-20261112'
    P.OUT = OUT
    REPORT = ROOT / 'Artifacts/L02_W24_W25_Ground_HP_Plus5_20261112.md'
    MULTIPLIER = Decimal('1.05')
    LABEL = '上调 5%'
    FIRST_WAVE = 24
    CELL_COUNT = 9


def plan():
    assert not OUT.exists(), OUT
    db = P.S.read_db()
    waves, refs = P.S.wave_inputs(db)
    changes = []
    for w in waves[FIRST_WAVE - 1:25]:
        for eid, count in w['counts'].items():
            r = db['EnemyData'][eid]
            if int(r.values['isFlying']) != 0:
                continue
            assert refs[eid] == [w['wave']], (eid, refs[eid])
            old = float(r.values['hp'])
            new = float((Decimal(str(old)) * MULTIPLIER).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
            changes.append({'wave': w['wave'], 'roundId': w['roundId'], 'id': eid,
                            'name': r.values['name'], 'cell': r.source['columns']['hp'] + str(r.source['row']),
                            'old': old, 'new': new, 'count': count})
    assert len(changes) == CELL_COUNT, len(changes)
    p = {'source': str(P.SOURCE), 'sourceSha256': P.sha(P.SOURCE), 'multiplier': float(MULTIPLIER),
         'scope': f'L02 W{FIRST_WAVE}-W25 ground HP only, including W25 Rat, current source * {MULTIPLIER}', 'changes': changes}
    OUT.mkdir(parents=True)
    shutil.copy2(P.SOURCE, OUT / 'EnemyData.before.xlsx')
    shutil.copy2(ROOT / 'Assets/ConfigJson/tbenemydata.json', OUT / 'tbenemydata.before.json')
    (OUT / 'baseline.json').write_text(json.dumps(P.S.state(), indent=2), encoding='utf-8')
    (OUT / 'plan.json').write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding='utf-8')
    manifest = {'edits': [{'table': 'EnemyData', 'id': c['id'], 'field': 'hp', 'old': c['old'], 'value': c['new']} for c in changes]}
    (OUT / 'author-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(p, ensure_ascii=False, indent=2))


def apply():
    p = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    authored = {int(r.values['id']): r for r in P.S.S.read_xlsx(OUT / 'source-authoring/EnemyData.xlsx')}
    for c in p['changes']:
        assert float(authored[c['id']].values['hp']) == c['new'], c
    P.apply()


def verify_export():
    p = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    before = json.loads((OUT / 'baseline.json').read_text(encoding='utf-8'))
    now = P.S.state()
    assert set(now) == set(before), 'Source/export file set changed'
    changed = [k for k in before if before[k] != now[k]]
    assert set(changed) == {'Luban/Config/Datas/Levels/L02/EnemyData.xlsx', 'Assets/ConfigJson/tbenemydata.json'}, changed
    old_rows = {int(r['id']): r for r in json.loads((OUT / 'tbenemydata.before.json').read_text(encoding='utf-8-sig'))}
    new_rows = {int(r['id']): r for r in json.loads((ROOT / 'Assets/ConfigJson/tbenemydata.json').read_text(encoding='utf-8-sig'))}
    assert old_rows.keys() == new_rows.keys()
    expected = {(c['id'], 'hp'): c for c in p['changes']}
    actual = set()
    for eid, row in old_rows.items():
        assert row.keys() == new_rows[eid].keys()
        for field, value in row.items():
            value_new = new_rows[eid][field]
            if value == value_new:
                continue
            key = (eid, field)
            assert key in expected, key
            c = expected[key]
            assert struct.pack('f', float(value)) == struct.pack('f', c['old'])
            assert struct.pack('f', float(value_new)) == struct.pack('f', c['new'])
            actual.add(key)
    assert actual == set(expected)
    mtime_updated = (ROOT / 'Assets/ConfigJson/tbenemydata.json').stat().st_mtime_ns > (OUT / 'tbenemydata.before.json').stat().st_mtime_ns
    assert mtime_updated
    scenes = json.loads((ROOT / 'Assets/ConfigJson/tbsceneinfo.json').read_text(encoding='utf-8-sig'))
    assert len(scenes) == 30 and all(s['initialGold'] == 100 for s in scenes)
    result = {'sourceHpCells': CELL_COUNT, 'exportedHpFields': len(actual), 'outsideWhitelist': 0,
              'otherLevelsChanged': 0, 'otherConfigJsonChanged': 0, 'initialGoldAll30Equal100': True,
              'tbenemydataMtimeUpdated': mtime_updated, 'changedFiles': changed}
    (OUT / 'export-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    lines = [f'# L02 W{FIRST_WAVE}–W25 地面怪物 HP {LABEL}（2026-11-12）', '',
             f'以本轮修改前源表 HP × {MULTIPLIER}，保留六位小数。仅地面怪物，含 W25 Rat，共 {CELL_COUNT} 格。',
             '空中 HP、其他波次、其余关卡和其他字段保持本轮改前值。', '',
             '| 波次 | ID | 怪物 | 单元格 | 旧 HP | 新 HP |', '|---:|---:|---|---|---:|---:|']
    for c in p['changes']:
        lines.append(f"| W{c['wave']} | {c['id']} | {c['name']} | {c['cell']} | {c['old']:.6f} | {c['new']:.6f} |")
    lines += ['', f'源表 {CELL_COUNT}/{CELL_COUNT} 格回读通过，工作簿白名单外 XML、格式与结构零变化。',
              f'导出 JSON 仅 {CELL_COUNT} 个对应 HP 字段变化；其他源表、其他导出文件与改前哈希相同。',
              'tbenemydata.json 修改时间已更新；30 关 initialGold 全部为 100。']
    assert not REPORT.exists(), REPORT
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    {'plan': plan, 'apply': apply, 'verify_export': verify_export}[sys.argv[1]]()
