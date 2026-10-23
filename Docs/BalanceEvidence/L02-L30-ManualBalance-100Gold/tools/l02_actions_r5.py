"""Correct the prerequisite order after inspecting actual funding-delayed times."""
from formal_tools import *
out=REPORT/'L02/search-r5';out.mkdir(parents=True,exist_ok=False);runs=[]
for timing in [22000,24000,26000,28000]:
    old=REPORT/f'L02/search-r4/reallocate-{timing}.json'
    ops=json.loads(old.read_text(encoding='utf-8'))
    ops=[o for o in ops if not(o['waveOrdinal']==25 and o['row']==3 and o['col']==11 and o['towerId']==2)]
    index=next(i for i,o in enumerate(ops)if o['waveOrdinal']==25 and o['row']==3 and o['col']==11 and o['towerId']==3)
    ops.insert(index,dict(waveOrdinal=25,timeMs=timing,action='upgrade',row=3,col=11,towerId=2))
    path=out/f'reallocate-{timing}.json';path.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
    runs.append(dict(profileId='D04',levelId=2,strategy=f'r5-reallocate-{timing}',speed=1,operationsPath=str(path),waitForFunds=True,screenshots=True))
(out/'request.json').write_text(json.dumps(dict(output=str(ROOT/'Library/BalanceWorkbench/manual-r5-L02'),stepSeconds=.02,stepsPerUpdate=200,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
print(out/'request.json')
