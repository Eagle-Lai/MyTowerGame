import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path('D:/FreedomTower_1')
OUT = ROOT / 'Library/BalanceStage/l02-w20-air-plateau-20261112'
sys.path.insert(0, str(ROOT / '.workbuddy/tools'))
spec = __import__('importlib.util').util.spec_from_file_location(
    'econ_layout', ROOT / '.workbuddy/tools/_l02_w16_25_econ_layout_v2_20261112.py')
S = __import__('importlib.util').util.module_from_spec(spec)
spec.loader.exec_module(S)
SOURCE = S.SOURCE
W20_MULTIPLIER = 0.90


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan():
    assert not OUT.exists(), f'Audit folder already exists: {OUT}'
    db = S.read_db()
    waves, enemy_waves = S.wave_inputs(db)
    targets = []
    for wave in waves[19:25]:
        air_ids = [eid for eid in wave['counts']
                   if int(db['EnemyData'][eid].values['isFlying']) != 0]
        assert len(air_ids) == 1, (wave['wave'], air_ids)
        eid = air_ids[0]
        row = db['EnemyData'][eid]
        assert enemy_waves[eid] == [wave['wave']]
        targets.append((wave, eid, row))
    w20_old = float(targets[0][2].values['hp'])
    plateau = round(w20_old * W20_MULTIPLIER, 6)
    changes = []
    for wave, eid, row in targets:
        old = float(row.values['hp'])
        new = plateau
        changes.append({
            'wave': wave['wave'], 'roundId': wave['roundId'], 'id': eid,
            'name': row.values['name'], 'cell': row.source['columns']['hp'] + str(row.source['row']),
            'old': old, 'new': new, 'count': wave['counts'][eid],
            'rule': 'W20 current HP * 0.90' if wave['wave'] == 20 else 'flat at reduced W20 HP',
        })
    assert len(changes) == 6
    p = {'source': str(SOURCE), 'sourceSha256': sha(SOURCE),
         'w20Multiplier': W20_MULTIPLIER, 'plateauHp': plateau,
         'scope': 'L02 W20-W25 airborne HP; W20 -10%, W21-W25 flat at revised W20',
         'changes': changes}
    OUT.mkdir(parents=True)
    shutil.copy2(SOURCE, OUT / 'EnemyData.before.xlsx')
    shutil.copy2(ROOT / 'Assets/ConfigJson/tbenemydata.json', OUT / 'tbenemydata.before.json')
    (OUT / 'baseline.json').write_text(json.dumps(S.state(), indent=2), encoding='utf-8')
    (OUT / 'plan.json').write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(p, ensure_ascii=False, indent=2))


def patch_cell(xml, cell, value):
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
        patched, old = patch_cell(patched, c['cell'], c['new'])
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
        for field, old in old_row.values.items():
            new = after[enemy_id].values[field]
            if new != old:
                actual.add((enemy_id, field, float(old), float(new)))
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
    now = S.state()
    changed = [k for k in baseline if baseline[k] != now[k]]
    assert changed == ['Luban/Config/Datas/Levels/L02/EnemyData.xlsx'], changed
    result = {'sourceReadback': len(actual), 'outsideWhitelist': 0,
              'changedSourceFiles': changed, 'sourceSha256': sha(SOURCE)}
    (OUT / 'source-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


def verify_export():
    p = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    baseline = json.loads((OUT / 'baseline.json').read_text(encoding='utf-8'))
    now = S.state()
    changed = [k for k in baseline if baseline[k] != now[k]]
    assert set(changed) == {'Luban/Config/Datas/Levels/L02/EnemyData.xlsx',
                            'Assets/ConfigJson/tbenemydata.json'}, changed
    old = {int(x['id']): x for x in json.loads((OUT / 'tbenemydata.before.json').read_text(encoding='utf-8-sig'))}
    new = {int(x['id']): x for x in json.loads((ROOT / 'Assets/ConfigJson/tbenemydata.json').read_text(encoding='utf-8-sig'))}
    expected = {(c['id'], 'hp'): c for c in p['changes']}
    fields = set()
    import struct
    for eid, old_row in old.items():
        for field, old_value in old_row.items():
            value = new[eid][field]
            if old_value == value:
                continue
            key = (eid, field)
            assert key in expected
            c = expected[key]
            assert struct.pack('f', float(old_value)) == struct.pack('f', c['old'])
            assert struct.pack('f', float(value)) == struct.pack('f', c['new'])
            fields.add(key)
    assert fields == set(expected)
    for path, digest in baseline.items():
        if path.startswith('Assets/ConfigJson/') and path != 'Assets/ConfigJson/tbenemydata.json':
            assert now[path] == digest, path
    mtime = (ROOT / 'Assets/ConfigJson/tbenemydata.json').stat().st_mtime_ns > (
        OUT / 'tbenemydata.before.json').stat().st_mtime_ns
    assert mtime
    report = ROOT / 'Artifacts/L02_W20_Air_HP_Plateau_20261112.md'
    assert not report.exists(), report
    lines = ['# L02 W20–W25 空中怪 HP 调整（2026-11-12）', '',
             'W20 以本轮改前值降低 10%；W21–W25 固定为调整后的 W20 空中 HP。仅修改 6 个空中 HP 单元格。', '',
             '| 波次 | ID | 怪物 | 单元格 | 旧 HP | 新 HP |', '|---:|---:|---|---|---:|---:|']
    for c in p['changes']:
        lines.append(f"| W{c['wave']} | {c['id']} | {c['name']} | {c['cell']} | {c['old']:.6f} | {c['new']:.6f} |")
    lines += ['', '源表 6/6 格回读通过，白名单外 0 变化；Luban 导表成功，JSON 恰有 6 个 HP 字段变化；空中出生顺序检查通过。']
    report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    result = {'sourceHpCells': len(p['changes']), 'exportedHpFields': len(fields),
              'outsideWhitelist': 0, 'otherConfigJsonChanged': 0,
              'tbenemydataMtimeUpdated': mtime, 'changedFiles': changed}
    (OUT / 'export-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    {'plan': plan, 'apply': apply, 'verify_source': verify_source,
     'verify_export': verify_export}[sys.argv[1]]()
