"""Complete legacy candidate index fields from their preserved actual results."""
from formal_tools import *
import csv
cache={};count=0
fields=['runId','batch','index','strategy','state','victory','stars','valid','waves','spawned','killed','leaked','hp','initialGold','finalGold','combatSeconds','operations','pending','versionKey','runtimeContentHash','source']
for level in range(2,31):
    directory=REPORT/f'L{level:02}';p=directory/'trial-index.json'
    if not p.exists():continue
    rows=json.loads(p.read_text(encoding='utf-8'));rows=rows.get('trials',[])if isinstance(rows,dict)else rows
    for row in rows:
        path=(directory/row['source']).resolve();assert path.is_relative_to(REPORT.resolve())and path.exists(),path
        if path not in cache:
            data=json.loads(path.read_text(encoding='utf-8'));cache[path]={r['metrics']['runId']:(i,r)for i,r in enumerate(data)}
        i,r=cache[path][row['runId']];m=r['metrics']
        row.update(index=i,strategy=r['strategy'],state=r['state'],victory=r['victory'],stars=r['stars'],valid=r['valid'],waves=m['completedWaveCount'],spawned=m['successfulSpawned'],killed=m['killed'],leaked=m['leaked'],hp=m['hp'],initialGold=r.get('initialGold'),finalGold=r['finalGold'],combatSeconds=m['combatElapsedSeconds'],operations=len(r['operations']),pending=len(r['pendingOperations']),versionKey=r['versionKey'],runtimeContentHash=r['profile']['runtimeContentHash']);count+=1
    p.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    with p.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='')as f:
        writer=csv.DictWriter(f,fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
print(count,'actual indexed trials normalized; absent historical initialGold observations remain null')
