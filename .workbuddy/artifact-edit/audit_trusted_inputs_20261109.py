"""Read current source workbooks only; never read historical gameplay evidence."""
from pathlib import Path
import hashlib
import json
import openpyxl
import math
import struct

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Library/BalanceStage/trusted-input-audit-20261109'
DATA = ROOT / 'Luban/Config/Datas'

def read_source(path):
    book = openpyxl.load_workbook(path, read_only=True, data_only=False)
    sheets = []
    for sheet in book:
        values = list(sheet.values)
        if not values:
            sheets.append({'sheet': sheet.title, 'rows': []})
            continue
        headers = values[0]
        rows = []
        for index, row in enumerate(values[3:], 4):
            if len(row) < 2 or row[1] is None:
                continue
            record = {str(h): v for h, v in zip(headers, row) if h and h != '##'}
            for name, value in record.items():
                if isinstance(value, str) and value.startswith('='):
                    raise ValueError(f'Formula needs review: {path} {sheet.title} row {index} {name}')
            rows.append({'excelRow': index, 'values': record})
        sheets.append({'sheet': sheet.title, 'rows': rows})
    book.close()
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'sheets': sheets}

def main():
    names = ['SceneInfo', 'LevelMap', 'EnemyData', 'EnemyList', 'RoundData', 'TowerInfo', 'BulletData', 'LevelRules']
    sources = {name: read_source(DATA / 'Levels/L01' / (name + '.xlsx')) for name in names}
    sources['L02Map'] = read_source(DATA / 'Levels/L02/LevelMap.xlsx')
    protected_l02 = {name: read_source(DATA / 'Levels/L02' / (name + '.xlsx')) for name in names if name != 'LevelMap'}
    tuning = read_source(DATA / 'WaveTuning.xlsx')
    exported_matches = {}
    # Exports are checked against source cells, never promoted to trusted inputs.
    # Check every populated source field; Luban may omit optional empty fields.
    for name, source in sources.items():
        export_name = 'tblevelmap' if name == 'L02Map' else 'tb' + name.lower()
        exported = json.loads((ROOT / 'Assets/ConfigJson' / (export_name + '.json')).read_text(encoding='utf-8-sig'))
        by_id = {row['id']: row for row in exported}
        mismatches = []
        checked = 0
        for sheet in source['sheets']:
            for entry in sheet['rows']:
                row = entry['values']
                target = by_id.get(row['id'])
                if target is None:
                    mismatches.append({'id': row['id'], 'error': 'Missing exported row'})
                    continue
                for field, value in row.items():
                    if value is None or field not in target:
                        continue
                    expected = target[field]
                    actual = value
                    if isinstance(expected, dict) and isinstance(value, str):
                        actual = dict(zip(('x', 'y', 'z'), map(float, value.split(','))))
                    if isinstance(expected, list) and isinstance(value, str):
                        actual = value.split(',') if field != 'cells' else value.split('|')
                        if expected and isinstance(expected[0], int):
                            actual = [int(x) for x in actual]
                    checked += 1
                    equal = actual == expected
                    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
                        # Luban serializes System.Single values to their shortest decimal form.
                        equal = struct.pack('f', actual) == struct.pack('f', expected)
                    if not equal:
                        mismatches.append({'id': row['id'], 'field': field, 'source': actual, 'export': expected})
        exported_matches[name] = {'checkedFields': checked, 'mismatches': mismatches}
    towers = [r['values'] for s in sources['TowerInfo']['sheets'] for r in s['rows']]
    cumulative = {}
    for tower_type in (1, 2, 3):
        levels = sorted([r for r in towers if r['type'] == tower_type], key=lambda r: r['level'])
        running = 0
        for row in levels:
            running += row['prices']
            cumulative[f'{tower_type}:{row["level"]}'] = running
    # Transcribed from the user-provided original screenshot, never from final-towers.csv.
    # All positions, types and levels explicitly confirmed by the user this session.
    l01 = []
    for y, cols, typ, level in [
        (0, [1, 5, 9], 2, 1), (1, [1, 3, 5, 7, 9], 2, 3),
        (2, [0, 1, 3, 5, 7, 9, 10], 1, 3),
        (3, [1, 5, 9, 11], 1, 3), (3, [3, 7, 10], 3, 3),
        (4, [1, 3, 5, 7, 9, 10], 1, 3), (4, [11], 1, 1),
        (5, [1, 3, 5, 7, 9, 10, 11], 2, 3), (6, [3, 7], 2, 1),
    ]:
        for x in cols:
            l01.append({'row': y, 'col': x, 'type': typ, 'levelHypothesis': level,
                        'cumulativeCost': cumulative[f'{typ}:{level}']})
    l02_counts = [{'type': 3, 'level': 1, 'count': 8}, {'type': 3, 'level': 3, 'count': 31},
                  {'type': 1, 'level': 3, 'count': 22}, {'type': 2, 'level': 3, 'count': 3}]
    for row in l02_counts:
        row['unitCumulativeCost'] = cumulative[f'{row["type"]}:{row["level"]}']
        row['subtotal'] = row['count'] * row['unitCumulativeCost']
    report = {'trustedSources': sources, 'protectedCurrentL02NotDesignInput': protected_l02,
              'currentWaveTuningForRuntimeAudit': tuning,
              'exportSourceChecks': exported_matches, 'towerCumulativePrices': cumulative,
              'L01ConfirmedLayout': l01, 'L01Count': len(l01),
              'L01Cost': sum(r['cumulativeCost'] for r in l01),
              'L02Counts': l02_counts, 'L02FinalCost': sum(r['subtotal'] for r in l02_counts),
              'L02Economy': sum(r['subtotal'] for r in l02_counts) + 219,
              'excluded': ['Historical gameplay metrics', 'Historical operations', 'Historical runtime snapshots',
                           'Historical final-towers.csv', 'Previous L02 designs', 'Previous candidate simulations']}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'trusted-inputs.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ['trustedSources', 'L01ConfirmedLayout', 'protectedCurrentL02NotDesignInput', 'currentWaveTuningForRuntimeAudit']}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
