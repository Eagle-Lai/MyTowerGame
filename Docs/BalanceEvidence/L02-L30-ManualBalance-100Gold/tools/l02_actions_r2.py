"""Finite player-action variants derived from actual r1 failures, no config edits."""
from formal_tools import *
source=ROOT/'Library/BalanceWorkbench/manual-r1-L02/unity-results.json'
trials=json.loads(source.read_text(encoding='utf-8'))
base=next(r for r in trials if r['strategy']=='r1-folded-maze')['operations']
out=REPORT/'L02/search-r2';out.mkdir(parents=True,exist_ok=False)
def op(wave,row,col,tid,action='upgrade'):return dict(waveOrdinal=wave,timeMs=0,action=action,row=row,col=col,towerId=tid)
runs=[]
# Remove inefficient off-flight slow upgrades. Preserve every blocking base tower.
drop={(6,3),(2,1),(2,13)}
core=[{k:o[k] for k in ['waveOrdinal','timeMs','action','row','col','towerId']} for o in base if not(o['action']=='upgrade' and (o['row'],o['col']) in drop)]
variants=[
('front-air',core+[op(16,3,1,2),op(17,3,1,3),op(19,5,1,2),op(20,5,1,3),op(22,4,5,3)]),
('mid-air',core+[op(16,4,5,3),op(18,5,3,2),op(19,5,3,3),op(21,3,1,2),op(22,3,1,3)]),
('end-air',core+[op(16,4,5,3),op(18,5,3,2),op(19,5,3,3),op(21,4,13,3),op(24,3,11,3)]),
('slow-lane',core+[op(16,4,5,3),op(18,5,3,2),op(19,5,3,3),op(20,4,12,7,'build'),op(21,4,12,8),op(24,4,12,9)])]
for name,ops in variants:
    ops.sort(key=lambda x:(x['waveOrdinal'],x['timeMs']))
    path=out/f'{name}.json';path.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
    runs.append(dict(profileId='D04',levelId=2,strategy='r2-'+name,speed=1,operationsPath=str(path),waitForFunds=True,screenshots=True))
request=dict(output=str(ROOT/'Library/BalanceWorkbench/manual-r2-L02'),stepSeconds=.02,stepsPerUpdate=200,runs=runs)
(out/'request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8')
print(out/'request.json')
