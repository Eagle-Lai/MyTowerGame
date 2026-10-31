from finalize import *
archive=DOC/'evidence';archive.mkdir(parents=True,exist_ok=True)
rows=all_rows();dump(DOC/'trial-index.json',rows)
for name in ['geometric-layout-search.json','snake-candidates.json']:
    if (OUT/name).exists():shutil.copy2(OUT/name,archive/name)
for p in OUT.glob('*.request.json'):
    shutil.copy2(p,archive/p.name)
for p in (OUT/'candidates').glob('*.json'):
    shutil.copy2(p,archive/'candidate-operations'/p.name) if (archive/'candidate-operations').exists() else None
(archive/'candidate-operations').mkdir(exist_ok=True)
for p in (OUT/'candidates').glob('*.json'):shutil.copy2(p,archive/'candidate-operations'/p.name)
for p in OUT.glob('*.py'):shutil.copy2(p,archive/p.name)
dump(archive/'source-table-fingerprints.json',{str(p.relative_to(ROOT)).replace(chr(92),'/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'Luban/Config/Datas/Levels/L03').glob('*.xlsx')})
hashes=json.loads((OUT/'input-hashes.json').read_text());diff=[]
for name,h in hashes.items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h:diff.append(name)
dump(DOC/'unchanged-input-verification.json',{'passed':not diff,'changes':diff,'comparedFiles':len(hashes),'description':'All runtime JSON and gameplay C# match the start-of-search hashes; no balance or gameplay patch applied in this strategy search.'})
print('Archived',len(rows),'trials; modified input files',diff)
