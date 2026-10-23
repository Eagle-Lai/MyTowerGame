"""Preserve raw own-task trials and indexes, including all failures."""
from formal_tools import *
import sys,shutil,csv,datetime
tag=sys.argv[1];source=ROOT/'Library/BalanceWorkbench'/tag
rows=json.loads((source/'unity-results.json').read_text(encoding='utf-8'))
dest=REPORT/'raw-trials'/tag;dest.parent.mkdir(exist_ok=True)
shutil.copytree(source,dest,dirs_exist_ok=True)
inputs=REPORT/'audit/batch-inputs'/tag
if inputs.exists():shutil.copytree(inputs,dest/'inputs',dirs_exist_ok=True)
for level in sorted({r['levelId'] for r in rows}):
    directory=REPORT/f'L{level:02}';directory.mkdir(exist_ok=True);indexpath=directory/'trial-index.json'
    old=json.loads(indexpath.read_text(encoding='utf-8')) if indexpath.exists() else []
    # Previous indexes may carry metadata around the trial list.
    if isinstance(old,dict):old=old.get('trials',[])
    known={r.get('runId')for r in old};new=[]
    for i,r in enumerate(rows):
        if r['levelId']!=level:continue
        m=r['metrics'];runid=m['runId']
        if runid in known:continue
        new.append(dict(runId=runid,batch=tag,index=i,strategy=r['strategy'],state=r['state'],victory=r['victory'],stars=r['stars'],valid=r['valid'],waves=m['completedWaveCount'],spawned=m['successfulSpawned'],killed=m['killed'],leaked=m['leaked'],hp=m['hp'],initialGold=r['initialGold'],finalGold=r['finalGold'],combatSeconds=m['combatElapsedSeconds'],operations=len(r['operations']),pending=len(r['pendingOperations']),versionKey=r['versionKey'],source=f'../raw-trials/{tag}/unity-results.json'))
    old.extend(new);indexpath.write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf-8')
    fields=['runId','batch','index','strategy','state','victory','stars','valid','waves','spawned','killed','leaked','hp','initialGold','finalGold','combatSeconds','operations','pending','versionKey','source']
    with (directory/'trial-index.csv').open('w',encoding='utf-8-sig',newline='')as f:
        w=csv.DictWriter(f,fields,extrasaction='ignore');w.writeheader();w.writerows(old)
print(tag,len(rows),'archived')
