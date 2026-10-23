"""Finish the observed last flying enemy using real late refund funds."""
from formal_tools import *
actual=json.loads((ROOT/'Library/BalanceWorkbench/manual-r5-L02/unity-results.json').read_text(encoding='utf-8'))[1]
base=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in actual['operations']if not(o['waveOrdinal']==25 and o['row']==3 and o['col']==15 and o['towerId']==3)]
out=REPORT/'L02/search-r6';out.mkdir(parents=True,exist_ok=False);runs=[]
for timing in [28000,30000,32000]:
    ops=list(base)
    for action,r,c,t in [('sell',3,7,3),('build',3,7,4),('build',5,15,1),('upgrade',5,15,2)]:ops.append(dict(waveOrdinal=25,timeMs=timing,action=action,row=r,col=c,towerId=t))
    ops.sort(key=lambda x:(x['waveOrdinal'],x['timeMs']))
    path=out/f'late-refund-{timing}.json';path.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
    runs.append(dict(profileId='D04',levelId=2,strategy=f'r6-late-refund-{timing}',speed=1,operationsPath=str(path),waitForFunds=True,screenshots=True))
(out/'request.json').write_text(json.dumps(dict(output=str(ROOT/'Library/BalanceWorkbench/manual-r6-L02'),stepSeconds=.02,stepsPerUpdate=600,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
print(out/'request.json')
