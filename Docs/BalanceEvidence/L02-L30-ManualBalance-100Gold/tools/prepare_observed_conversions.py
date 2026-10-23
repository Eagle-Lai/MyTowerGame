"""One-time late air-to-ground reallocations from recorded failed runs."""
from formal_tools import *
import sys,math
tag=sys.argv[1];actual=json.loads((ROOT/'Library/BalanceWorkbench/followups-r2-h/unity-results.json').read_text(encoding='utf-8'))
t=tables();tc={x['id']:x for x in t['tbtowerinfo']};runs=[];notes=[]
for index in [87,97,101,103,105,108,109,111,112,113,114]:
    r=actual[index];assert not r['pendingOperations'];level=r['levelId']
    original=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']]
    path=r['finalPathCells'];start=round(r['metrics']['waves'][-1]['combatStartSeconds']*1000)
    air=[e['combatMs']-start for e in r['enemyOutcomes']if e['waveOrdinal']==25 and e['isFlying']]
    at=math.ceil((max(max(air or[0]),max([o['timeMs']for o in original if o['waveOrdinal']==25]or[0]))+1000)/1000)*1000
    board={(x['row'],x['col']):x['towerId']for x in r['towerContributions']}
    def score(item):
        (row,col),tid=item
        return sum(.3+j/max(1,len(path)-1)for j,(c,rr)in enumerate(path)if(c-col)**2+(rr-row)**2<=tc[5]['radius']**2)
    possible=sorted([(p,tid)for p,tid in board.items()if tc[tid]['type']==1 and tc[tid]['level']>=2],key=score,reverse=True)
    for count in [6,9]:
        chosen=possible[:count]
        if len(chosen)<count:continue
        extra=[]
        for (row,col),tid in chosen:extra.append(dict(waveOrdinal=25,timeMs=at,action='sell',row=row,col=col,towerId=tid))
        for (row,col),tid in chosen:extra.append(dict(waveOrdinal=25,timeMs=at,action='build',row=row,col=col,towerId=4))
        for (row,col),tid in chosen:
            if tc[tid]['level']==3:extra.append(dict(waveOrdinal=25,timeMs=at,action='upgrade',row=row,col=col,towerId=5))
        out=REPORT/f'L{level:02}/search-{tag}';out.mkdir(parents=True,exist_ok=True)
        name=f'from-{index}-convert{count}';f=out/f'{name}.json';assert not f.exists()
        f.write_text(json.dumps(original+extra,ensure_ascii=False,indent=2),encoding='utf-8')
        runs.append(dict(profileId='D04',levelId=level,strategy=tag+'-'+name,speed=1,operationsPath=str(f),waitForFunds=True,screenshots=True,captureStages=True))
        notes.append(dict(level=level,sourceIndex=index,sourceRunId=r['metrics']['runId'],name=name,observedLastAirMs=max(air or[0]),timeMs=at,extra=extra,scope='One conversion per cell after the last RECORDED air outcome in the failed source run; future planned air may be unobserved if defeat stopped spawning. Identical occupied cells afterwards. Actual Unity outcome, including any air failure, must be measured.'))
(REPORT/f'requests/{tag}.json').write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/f'audit/{tag}-bounds.json').write_text(json.dumps(dict(maxRuns=len(runs),decisions=notes,termination='One replay per listed plan; no repeated stalling or free transactions'),ensure_ascii=False,indent=2),encoding='utf-8')
print(len(runs),'unexecuted one-time conversions')
