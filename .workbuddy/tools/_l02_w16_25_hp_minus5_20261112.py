import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path('D:/FreedomTower_1')
OUT = ROOT / 'Library/BalanceStage/l02-w16-w25-current-minus5-20261112'
sys.path.insert(0, str(ROOT / '.workbuddy/tools'))
spec = __import__('importlib.util').util.spec_from_file_location(
    'econ_layout', ROOT / '.workbuddy/tools/_l02_w16_25_econ_layout_v2_20261112.py')
S = __import__('importlib.util').util.module_from_spec(spec)
spec.loader.exec_module(S)
SOURCE = S.SOURCE
MULTIPLIER = 0.95


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan():
    assert not OUT.exists(), f'Audit folder already exists: {OUT}'
    db = S.read_db()
    waves, enemy_waves = S.wave_inputs(db)
    changes = []
    for wave in waves[15:25]:
        for enemy_id, count in wave['counts'].items():
            row = db['EnemyData'][enemy_id]
            old = float(row.values['hp'])
            new = round(old * MULTIPLIER, 6)
            changes.append({
                'wave': wave['wave'], 'roundId': wave['roundId'], 'id': enemy_id,
                'name': row.values['name'],
                'kind': 'air' if int(row.values['isFlying']) != 0 else 'ground',
                'cell': row.source['columns']['hp'] + str(row.source['row']),
                'old': old, 'new': new, 'count': count,
            })
            assert enemy_waves[enemy_id] == [wave['wave']], f'Shared enemy id {enemy_id}'
    assert len(changes) == 51, len(changes)
    plan_data = {
        'source': str(SOURCE), 'sourceSha256': sha(SOURCE),
        'multiplier': MULTIPLIER, 'scope': 'L02 W16-W25 hp, all ground and airborne enemies',
        'changes': changes,
    }
    OUT.mkdir(parents=True)
    shutil.copy2(SOURCE, OUT / 'EnemyData.before.xlsx')
    shutil.copy2(ROOT / 'Assets/ConfigJson/tbenemydata.json', OUT / 'tbenemydata.before.json')
    (OUT / 'baseline.json').write_text(json.dumps(S.state(), indent=2), encoding='utf-8')
    (OUT / 'plan.json').write_text(json.dumps(plan_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'sourceSha256': plan_data['sourceSha256'], 'changes': len(changes),
                      'first': changes[:2], 'last': changes[-3:]}, ensure_ascii=False, indent=2))


def patch_cell(xml, cell, value):
    pattern = rb'(<c\b[^>]*\br="' + cell.encode() + rb'"[^>]*>.*?<v>)([^<]*)(</v>.*?</c>)'
    matches = list(re.finditer(pattern, xml, re.S))
    assert len(matches) == 1, (cell, len(matches))
    match = matches[0]
    old = float(match.group(2))
    return xml[:match.start(2)] + str(value).encode() + xml[match.end(2):], old


def apply():
    p = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    assert sha(SOURCE) == p['sourceSha256'], 'Source changed after plan; stop and re-read.'
    with ZipFile(SOURCE) as z:
        members = {info.filename: (info, z.read(info.filename)) for info in z.infolist()}
    sheet = 'xl/worksheets/sheet1.xml'
    original = members[sheet][1]
    patched = original
    for change in p['changes']:
        patched, old = patch_cell(patched, change['cell'], change['new'])
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
        restored = z.read(sheet)
        for change in p['changes']:
            pattern = (rb'(<c\b[^>]*\br="' + change['cell'].encode()
                       + rb'"[^>]*>.*?<v>)([^<]*)(</v>.*?</c>)')
            old_token = re.search(pattern, original, re.S).group(2)
            restored = re.sub(pattern, lambda m: m.group(1) + old_token + m.group(3),
                              restored, count=1, flags=re.S)
        assert restored == original, 'Package sheet changed outside hp whitelist.'
    assert sha(SOURCE) == p['sourceSha256']
    shutil.copy2(SOURCE, OUT / 'EnemyData.backup.xlsx')
    os.replace(temp, SOURCE)
    verify_source()


def verify_source():
    p = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    old = {int(r.values['id']): r for r in S.S.read_xlsx(OUT / 'EnemyData.before.xlsx')}
    new = {int(r.values['id']): r for r in S.S.read_xlsx(SOURCE)}
    expected = {(c['id'], 'hp', c['old'], c['new']) for c in p['changes']}
    actual = set()
    for enemy_id, old_row in old.items():
        new_row = new[enemy_id]
        assert {k: v for k, v in old_row.source.items() if k != 'path'} == {
            k: v for k, v in new_row.source.items() if k != 'path'}
        for field, old_value in old_row.values.items():
            new_value = new_row.values[field]
            if new_value != old_value:
                actual.add((enemy_id, field, float(old_value), float(new_value)))
    assert actual == expected
    with ZipFile(OUT / 'EnemyData.before.xlsx') as a, ZipFile(SOURCE) as b:
        for name in a.namelist():
            if name != 'xl/worksheets/sheet1.xml':
                assert a.read(name) == b.read(name), name
        a_xml, b_xml = a.read('xl/worksheets/sheet1.xml'), b.read('xl/worksheets/sheet1.xml')
        for c in p['changes']:
            pattern = (rb'(<c\b[^>]*\br="' + c['cell'].encode()
                       + rb'"[^>]*>.*?<v>)([^<]*)(</v>.*?</c>)')
            token = re.search(pattern, a_xml, re.S).group(2)
            b_xml = re.sub(pattern, lambda m: m.group(1) + token + m.group(3), b_xml,
                           count=1, flags=re.S)
        assert b_xml == a_xml
    baseline = json.loads((OUT / 'baseline.json').read_text(encoding='utf-8'))
    current = S.state()
    changed = [k for k in baseline if baseline[k] != current[k]]
    assert changed == ['Luban/Config/Datas/Levels/L02/EnemyData.xlsx'], changed
    result = {'sourceReadback': len(actual), 'outsideWhitelist': 0,
              'onlyChangedSource': changed, 'packageMembersOutsideCellsUnchanged': True,
              'sourceSha256': sha(SOURCE)}
    (OUT / 'source-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


def verify_export():
    p = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    baseline = json.loads((OUT / 'baseline.json').read_text(encoding='utf-8'))
    current = S.state()
    changed = [k for k in baseline if baseline[k] != current[k]]
    expected_files = ['Assets/ConfigJson/tbenemydata.json', 'Luban/Config/Datas/Levels/L02/EnemyData.xlsx']
    assert set(changed) == set(expected_files), changed
    old_rows = {int(x['id']): x for x in json.loads((OUT / 'tbenemydata.before.json').read_text(encoding='utf-8-sig'))}
    new_rows = {int(x['id']): x for x in json.loads((ROOT / 'Assets/ConfigJson/tbenemydata.json').read_text(encoding='utf-8-sig'))}
    expected = {(c['id'], 'hp'): c for c in p['changes']}
    fields = set()
    for enemy_id, old_row in old_rows.items():
        row = new_rows[enemy_id]
        for field, old_value in old_row.items():
            if old_value == row[field]:
                continue
            key = (enemy_id, field)
            assert key in expected, key
            c = expected[key]
            import struct
            assert struct.pack('f', float(old_value)) == struct.pack('f', c['old'])
            assert struct.pack('f', float(row[field])) == struct.pack('f', c['new'])
            fields.add(key)
    assert fields == set(expected)
    for name, digest in baseline.items():
        if name.startswith('Assets/ConfigJson/') and name != 'Assets/ConfigJson/tbenemydata.json':
            assert current[name] == digest, name
    mtime = (ROOT / 'Assets/ConfigJson/tbenemydata.json').stat().st_mtime_ns > (
        OUT / 'tbenemydata.before.json').stat().st_mtime_ns
    assert mtime
    result = {'sourceHpCells': len(p['changes']), 'exportedHpFields': len(fields),
              'outsideWhitelist': 0, 'otherConfigJsonChanged': 0,
              'tbenemydataMtimeUpdated': mtime, 'changedFiles': changed}
    (OUT / 'export-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    lines = ['# L02 W16–W25 HP 统一降低 5%（2026-11-12）', '',
             '基准为本轮开始时当前源表值。范围仅 L02 W16–W25 所有敌人 hp，共 51 格（地面 41 格，含 W25 Rat；空中 10 格）。其余波次、关卡和字段不变。', '',
             '| 波次 | ID | 怪物 | 类别 | 单元格 | 当前 HP | 新 HP |', '|---:|---:|---|---|---|---:|---:|']
    for c in p['changes']:
        lines.append(f"| W{c['wave']} | {c['id']} | {c['name']} | {c['kind']} | {c['cell']} | {c['old']:.6f} | {c['new']:.6f} |")
    lines += ['', '校验：源表 51 格回读通过，白名单外 0 变化；Luban 导出成功；导出 JSON 恰有 51 个 HP 字段变化，其他配置 JSON 不变。']
    report = ROOT / 'Artifacts/L02_W16_W25_HP_Minus5_20261112.md'
    assert not report.exists(), f'Report already exists: {report}'
    report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    {'plan': plan, 'apply': apply, 'verify_source': verify_source,
     'verify_export': verify_export}[sys.argv[1]]()
