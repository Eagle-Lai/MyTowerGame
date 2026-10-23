"""Player actions responding to observed W25 flying leaks; unchanged formal config."""
from formal_tools import *
base=json.loads((ROOT/'Library/BalanceWorkbench/manual-r1-L02/unity-results.json').read_text(encoding='utf-8'))[-1]['operations']
core=[{k:o[k] for k in ['waveOrdinal','timeMs','action','row','col','towerId']} for o in base if not(o['action']=='upgrade' and (o['row'],o['col']) in {(6,3),(2,1),(2,13)})]
def op(w,r,c,t,action='upgrade'):return dict(waveOrdinal=w,timeMs=0,action=action,row=r,col=c,towerId=t)
out=REPORT/'L02/search-r3';out.mkdir(parents=True,exist_ok=False)
slow=[op(19,5,13,1,'sell'),op(19,5,13,7,'build'),op(19,5,13,8),op(21,5,13,9)]
end=[op(22,3,15,1,'build'),op(22,5,15,1,'build'),op(23,3,15,2),op(24,3,15,3)]
variants=[('slow-end',core+slow+end+[op(18,4,5,3)]),
('both-end',core+end+[op(18,4,5,3),op(22,5,15,2),op(25,5,15,3)]),
('back-upgrade',core+slow+[op(18,4,5,3),op(22,4,13,3),op(24,5,13,9)]),
('slow-only',core+slow+[op(18,4,5,3),op(22,4,13,3),op(23,3,15,1,'build'),op(24,3,15,2)])]
# Avoid a duplicate terminal slow upgrade in the authored comparison.
variants[2]=(variants[2][0],[o for i,o in enumerate(variants[2][1]) if not(o['waveOrdinal']==24 and o['row']==5 and o['col']==13)])
runs=[]
for name,ops in variants:
    ops.sort(key=lambda x:(x['waveOrdinal'],x['timeMs']))
    path=out/f'{name}.json';path.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
    runs.append(dict(profileId='D04',levelId=2,strategy='r3-'+name,speed=1,operationsPath=str(path),waitForFunds=True,screenshots=True))
(out/'request.json').write_text(json.dumps(dict(output=str(ROOT/'Library/BalanceWorkbench/manual-r3-L02'),stepSeconds=.02,stepsPerUpdate=200,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
print(out/'request.json')
