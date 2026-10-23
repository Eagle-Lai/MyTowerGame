"""Two legal L09 ground investments from actual per-wave tower contribution."""
from formal_tools import *
tag='l09-heavy-r2-i';source=ROOT/'Library/BalanceWorkbench/references-r2-a/unity-results.json';r=json.loads(source.read_text(encoding='utf-8'))[13]
assert r['levelId']==9 and r['metrics']['leaked']==1
ops=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']]
before={(x['row'],x['col']):x for x in r['waveBoundaries'][-1]['layout']};after={(x['row'],x['col']):x for x in r['towerContributions']}
assert after[(3,2)]['towerId']==3 and after[(3,2)]['airHits']-before[(3,2)]['airHits']==0
delta=after[(3,2)]['damage']-before[(3,2)]['damage'];assert delta<31
base=ops+[dict(waveOrdinal=25,timeMs=16000,action='sell',row=3,col=2,towerId=3),dict(waveOrdinal=25,timeMs=16000,action='build',row=3,col=2,towerId=1)]
t=tables();tower={x['id']:x for x in t['tbtowerinfo']};scene=next(x for x in t['tbsceneinfo']if x['id']==9);mp=next(x for x in t['tblevelmap']if x['id']==scene['mapId'])
out=REPORT/'L09'/f'search-{tag}';out.mkdir(exist_ok=False);runs=[];decisions=[]
extra=[dict(waveOrdinal=25,timeMs=16000,action='upgrade',row=row,col=col,towerId=6)for row,col in [(3,1),(4,1),(4,2)]]
variants=[('three-terminal-group3',extra)]
occupied={(x['col'],x['row'])for x in r['towerContributions']};reserved={tuple(p)for p in r['finalPathCells']};free=[(c,row)for row,line in enumerate(mp['cells'])for c,ch in enumerate(line)if ch=='.'and(c,row)not in occupied and(c,row)not in reserved]
def score(p):return sum((.2+j/max(1,len(r['finalPathCells'])-1))for j,(c,row)in enumerate(r['finalPathCells'])if(c-p[0])**2+(row-p[1])**2<=tower[5]['radius']**2)
points=sorted(free,key=score,reverse=True)[:3];assert len(points)==3
extra=[]
for col,row in points:
    extra.append(dict(waveOrdinal=25,timeMs=16000,action='build',row=row,col=col,towerId=4));extra.append(dict(waveOrdinal=25,timeMs=16000,action='upgrade',row=row,col=col,towerId=5))
variants.append(('three-new-group2',extra))
for name,extra in variants:
    f=out/f'{name}.json';f.write_text(json.dumps(base+extra,ensure_ascii=False,indent=2),encoding='utf-8')
    runs.append(dict(profileId='D04',levelId=9,strategy=tag+'-'+name,speed=1,operationsPath=str(f),waitForFunds=True,screenshots=True,captureStages=True))
    decisions.append(dict(name=name,sourceRunId=r['metrics']['runId'],observedRedundantNormalWave25Damage=delta,observedRedundantNormalAirHits=0,downgrade=dict(row=3,col=2,fromId=3,toId=1,observedRefundGrade3=211,buildCost=32),actualCashAfterOriginal15sConversions=395,conservativeCashAfterDowngrade=574,newInvestments=extra,newCellsOutsideObservedRoute=points if name.endswith('group2')else[],tested=False))
(REPORT/f'requests/{tag}.json').write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/f'audit/{tag}-bounds.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2),encoding='utf-8')
print('2 unexecuted L09 heavy-specific allocations')
