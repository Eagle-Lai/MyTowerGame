import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path('D:/FreedomTower_1')
OUT = ROOT / 'Library/BalanceStage/l02-w17-w25-air-minus10-20261112'
sys.path.insert(0, str(ROOT / '.workbuddy/tools'))
spec = __import__('importlib.util').util.spec_from_file_location(
    'econ_layout', ROOT / '.workbuddy/tools/_l02_w16_25_econ_layout_v2_20261112.py')
S = __import__('importlib.util').util.module_from_spec(spec)
spec.loader.exec_module(S)
SOURCE = S.SOURCE
MULTIPLIER = 0.90


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan():
    assert not OUT.exists(), f'Audit folder already exists: {OUT}'
    db = S.read_db()
    waves, enemy_waves = S.wave_inputs(db)
    changes = []
    for wave in waves[16:25]:
        for enemy_id, count in wave['counts'].items():
            row = db['EnemyData'][enemy_id]
            if int(row.values['isFlying']) == 0:
                continue
            old = float(row.values['hp'])
            changes.append({
                'wave': wave['wave'], 'roundId': wave['roundId'], 'id': enemy_id,
                'name': row.values['name'], 'cell': row.source['columns']['hp'] + str(row.source['row']),
                'old': old, 'new': round(old * MULTIPLIER, 6), 'count': count,
            })
            assert enemy_waves[enemy_id] == [wave['wave']], f'Shared enemy id {enemy_id}'
    assert len(changes) == 9, len(changes)
    p = {'source': str(SOURCE), 'sourceSha256': sha(SOURCE), 'multiplier': MULTIPLIER,
         'scope': 'L02 W17-W25 airborne enemy hp only', 'changes': changes}
    OUT.mkdir(parents=True)
    shutil.copy2(SOURCE, OUT / 'EnemyData.before.xlsx')
    shutil.copy2(ROOT / 'Assets/ConfigJson/tbenemydata.json', OUT / 'tbenemydata.before.json')
    (OUT / 'baseline.json').write_text(json.dumps(S.state(), indent=2), encoding='utf-8')
    (OUT / 'plan.json').write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(p, ensure_ascii=False, indent=2))


def replace_cell(xml, cell, value):
    pattern = rb'(<c\b[^>]*\br="' + cell.encode() + rb'"[^>]*>.*?<v>)([^<]*)(</v>.*?</c>)'
    matches = list(re.finditer(pattern, xml, re.S))
    assert len(matches) == 1, (cell, len(matches))
    m = matches[0]
    return xml[:m.start(2)] + str(value).encode() + xml[m.end(2):], float(m.group(2))


def apply():
    p = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    assert sha(SOURCE) == p['sourceSha256'], 'Source changed after plan.'
    with ZipFile(SOURCE) as z:
        members = {i.filename: (i, z.read(i.filename)) for i in z.infolist()}
    sheet = 'xl/worksheets/sheet1.xml'
    original = members[sheet][1]
    patched = original
    for c in p['changes']:
        patched, old = replace_cell(patched, c['cell'], c['new'])
        assert old == c['old'], c
    temp = OUT / 'EnemyData.patched.xlsx'
    with ZipFile(temp, 'w') as z:
        for name, (info, data) in members.items():
            z.writestr(info, patched if name == sheet else data)
    with ZipFile(temp) as z:
        assert set(z.namelist()) == set(members)
        for name, (_, data) in members.items():
            if name != sheet:
                assert z.read(name) == data
        restored = z.read(sheet)
        for c in p['changes']:
            pattern = (rb'(<c\b[^>]*\br="' + c['cell'].encode()
                       + rb'"[^>]*>.*?<v>)([^<]*)(</v>.*?</c>)')
            token = re.search(pattern, original, re.S).group(2)
            restored = re.sub(pattern, lambda m: m.group(1) + token + m.group(3),
                              restored, count=1, flags=re.S)
        assert restored == original
    assert sha(SOURCE) == p['sourceSha256']
    shutil.copy2(SOURCE, OUT / 'EnemyData.backup.xlsx')
    os.replace(temp, SOURCE)
    verify_source()


def verify_source():
    p = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    before = {int(r.values['id']): r for r in S.S.read_xlsx(OUT / 'EnemyData.before.xlsx')}
    after = {int(r.values['id']): r for r in S.S.read_xlsx(SOURCE)}
    expected = {(c['id'], 'hp', c['old'], c['new']) for c in p['changes']}
    actual = set()
    for enemy_id, old_row in before.items():
        new_row = after[enemy_id]
        for field, old in old_row.values.items():
            value = new_row.values[field]
            if value != old:
                actual.add((enemy_id, field, float(old), float(value)))
    assert actual == expected
    with ZipFile(OUT / 'EnemyData.before.xlsx') as a, ZipFile(SOURCE) as b:
        for name in a.namelist():
            if name != 'xl/worksheets/sheet1.xml':
                assert a.read(name) == b.read(name), name
        x, y = a.read('xl/worksheets/sheet1.xml'), b.read('xl/worksheets/sheet1.xml')
        for c in p['changes']:
            pattern = (rb'(<c\b[^>]*\br="' + c['cell'].encode()
                       + rb'"[^>]*>.*?<v>)([^<]*)(</v>.*?</c>)')
            token = re.search(pattern, x, re.S).group(2)
            y = re.sub(pattern, lambda m: m.group(1) + token + m.group(3), y,
                       count=1, flags=re.S)
        assert x == y
    baseline = json.loads((OUT / 'baseline.json').read_text(encoding='utf-8'))
    current = S.state()
    changed = [k for k in baseline if baseline[k] != current[k]]
    assert changed == ['Luban/Config/Datas/Levels/L02/EnemyData.xlsx'], changed
    result = {'sourceReadback': len(actual), 'outsideWhitelist': 0,
              'changedSourceFiles': changed, 'sourceSha256': sha(SOURCE)}
    (OUT / 'source-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


def verify_export():
    p = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    baseline = json.loads((OUT / 'baseline.json').read_text(encoding='utf-8'))
    current = S.state()
    changed = [k for k in baseline if baseline[k] != current[k]]
    assert set(changed) == {'Luban/Config/Datas/Levels/L02/EnemyData.xlsx',
                            'Assets/ConfigJson/tbenemydata.json'}, changed
    old_rows = {int(x['id']): x for x in json.loads((OUT / 'tbenemydata.before.json').read_text(encoding='utf-8-sig'))}
    new_rows = {int(x['id']): x for x in json.loads((ROOT / 'Assets/ConfigJson/tbenemydata.json').read_text(encoding='utf-8-sig'))}
    expected = {(c['id'], 'hp'): c for c in p['changes']}
    fields = set()
    import struct
    for enemy_id, old_row in old_rows.items():
        for field, old in old_row.items():
            new = new_rows[enemy_id][field]
            if old != new:
                assert (enemy_id, field) in expected
                c = expected[(enemy_id, field)]
                assert struct.pack('f', float(old)) == struct.pack('f', c['old'])
                assert struct.pack('f', float(new)) == struct.pack('f', c['new'])
                fields.add((enemy_id, field))
    assert fields == set(expected)
    for path, digest in baseline.items():
        if path.startswith('Assets/ConfigJson/') and path != 'Assets/ConfigJson/tbenemydata.json':
            assert current[path] == digest, path
    updated = (ROOT / 'Assets/ConfigJson/tbenemydata.json').stat().st_mtime_ns > (
        OUT / 'tbenemydata.before.json').stat().st_mtime_ns
    assert updated
    result = {'sourceHpCells': len(p['changes']), 'exportedHpFields': len(fields),
              'outsideWhitelist': 0, 'otherConfigJsonChanged': 0,
              'tbenemydataMtimeUpdated': updated, 'changedFiles': changed}
    (OUT / 'export-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    lines = ['# L02 W17–W25 空中怪 HP 降低 10%（2026-11-12）', '',
             '基准为本轮开始时当前源表值。仅修改 L02 W17–W25 空中敌人 hp，共 9 格；地面敌人、W16、其他关卡和其他字段不变。', '',
             '| 波次 | ID | 怪物 | 单元格 | 旧 HP | 新 HP |', '|---:|---:|---|---|---:|---:|']
    for c in p['changes']:
        lines.append(f"| W{c['wave']} | {c['id']} | {c['name']} | {c['cell']} | {c['old']:.6f} | {c['new']:.6f} |")
    lines += ['', '校验：源表 9 格回读通过，白名单外 0 变化；Luban 导出成功；导出 JSON 恰有 9 个 HP 字段变化，其他配置 JSON 不变。']
    report = ROOT / 'Artifacts/L02_W17_W25_Air_HP_Minus10_20261112.md'
    assert not report.exists(), report
    report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    {'plan': plan, 'apply': apply, 'verify_source': verify_source,
     'verify_export': verify_export}[sys.argv[1]]()
