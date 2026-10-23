"""Bounded legal end-wave reallocation search; all costs paid by real economy."""
from formal_tools import *
actual=json.loads((ROOT/'Library/BalanceWorkbench/manual-r2-L02/unity-results.json').read_text(encoding='utf-8'))[0]
base=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in actual['operations']]
out=REPORT/'L02/search-r4';out.mkdir(parents=True,exist_ok=False);runs=[]
for timing in [22000,24000,26000,28000]:
    ops=list(base)
    def add(action,r,c,t):ops.append(dict(waveOrdinal=25,timeMs=timing,action=action,row=r,col=c,towerId=t))
    for r,c,t,new in [(3,1,3,4),(5,1,3,4),(4,3,9,7)]:add('sell',r,c,t);add('build',r,c,new)
    add('upgrade',4,13,3);add('upgrade',3,11,3)
    add('build',3,15,1);add('upgrade',3,15,2);add('upgrade',3,15,3)
    ops.sort(key=lambda x:(x['waveOrdinal'],x['timeMs']))
    path=out/f'reallocate-{timing}.json';path.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
    runs.append(dict(profileId='D04',levelId=2,strategy=f'r4-reallocate-{timing}',speed=1,operationsPath=str(path),waitForFunds=True,screenshots=True))
(out/'request.json').write_text(json.dumps(dict(output=str(ROOT/'Library/BalanceWorkbench/manual-r4-L02'),stepSeconds=.02,stepsPerUpdate=200,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
print(out/'request.json')
