"""Apply reviewed literal cell edits. No balancing formulas or config generation.

Input: [{path, sheet, cell, before, after, reason}]. Every target is explicit.
Only level source workbooks are writable; L01 only data!T4 is allowed.
Exports are deliberately inaccessible to this tool.
"""
import argparse, hashlib, json, pathlib, shutil
from collections import defaultdict
import openpyxl

ROOT = pathlib.Path(__file__).resolve().parents[4]
REPORT = ROOT / 'Docs/BalanceEvidence/L02-L30-ManualBalance-100Gold'

def apply(path):
    edits = json.loads(path.read_text(encoding='utf-8'))
    grouped = defaultdict(list)
    seen = set()
    for e in edits:
        p = (ROOT / e['path']).resolve()
        relative = p.relative_to(ROOT).as_posix()
        assert relative.startswith('Luban/Config/Datas/Levels/L') and p.suffix == '.xlsx', relative
        level = int(p.parent.name[1:])
        assert 1 <= level <= 30
        assert level != 1 or (p.name == 'LevelRating.xlsx' and e['sheet'] == 'data' and e['cell'] == 'T4')
        assert e['reason'] and not (isinstance(e['after'], str) and e['after'].startswith('='))
        key = (relative, e['sheet'], e['cell'])
        assert key not in seen, key
        seen.add(key)
        grouped[p].append(e)
    books = {}
    for p, rows in grouped.items():
        wb = openpyxl.load_workbook(p)
        for e in rows:
            actual = wb[e['sheet']][e['cell']].value
            assert actual == e['before'], (p, e['cell'], actual, e['before'])
        books[p] = wb
    backup = REPORT / 'audit/source-backups'
    for p, wb in books.items():
        target = backup / p.relative_to(ROOT / 'Luban/Config/Datas')
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(p, target)
        for e in grouped[p]:
            wb[e['sheet']][e['cell']] = e['after']
        wb.save(p)
    receipt = {'manifest': str(path), 'manifestSha256': hashlib.sha256(path.read_bytes()).hexdigest(),
               'workbooks': len(books), 'edits': len(edits),
               'files': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in books}}
    path.with_suffix('.receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest', type=pathlib.Path)
    apply(parser.parse_args().manifest)
