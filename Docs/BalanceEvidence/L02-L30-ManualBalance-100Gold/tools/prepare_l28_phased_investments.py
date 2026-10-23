"""Continue a recorded L28 defense that stopped investing after W16."""
from formal_tools import *
import sys,math
tag=sys.argv[1];source=ROOT/'Library/BalanceWorkbench/followups-r2-h/unity-results.json'
r=json.loads(source.read_text(encoding='utf-8'))[114];assert r['levelId']==28
original=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']]
assert max(o['waveOrdinal']for o in original)==16
t=tables();tc={x['id']:x for x in t['tbtowerinfo']};scene=next(x for x in t['tbsceneinfo']if x['id']==28);mp=next(x for x in t['tblevelmap']if x['id']==scene['mapId'])
route=[tuple(p)for p in r['finalPathCells']];reserved={tuple(p)for b in r['waveBoundaries']if b['beforeWave']>=17 for p in b['pathCells']}|set(route)
initial={(x['col'],x['row']):x['towerId']for x in r['towerContributions']}
free=[(c,row)for row,line in enumerate(mp['cells'])for c,ch in enumerate(line)if ch=='.'and(c,row)not in initial and(c,row)not in reserved]
ends={ch:(c,row)for row,line in enumerate(mp['cells'])for c,ch in enumerate(line)if ch in'SE'};s,e=ends['S'],ends['E']
air=[(s[0]+(e[0]-s[0])*j/80,s[1]+(e[1]-s[1])*j/80)for j in range(81)]
runs=[];notes=[]
for name,weights in [('air-priority',{1:1.6,2:.7,3:1.0}),('balanced',{1:1,2:1,3:1.2}),('group-priority',{1:.75,2:1.5,3:1.0})]:
    board=dict(initial);extra=[];spent=0;budgets=[]
    for wave in range(17,26):
        cash=next(b['cash']for b in r['waveBoundaries']if b['beforeWave']==wave)-spent
        before=cash
        for _ in range(14):
            def benefit(p,new,old=None):
                def cov(points,cfg):return sum(.4+j/max(1,len(points)-1)for j,q in enumerate(points)if(q[0]-p[0])**2+(q[1]-p[1])**2<=cfg['radius']**2)
                if new['type']==1:
                    return weights[1]*(cov(air,new)*new['power']/(new['CD']/1000)-(cov(air,old)*old['power']/(old['CD']/1000)if old else 0))
                if new['type']==2:
                    return weights[2]*3*(cov(route,new)*new['power']/(new['CD']/1000)-(cov(route,old)*old['power']/(old['CD']/1000)if old else 0))
                value=0
                for points,mult in [(air,24),(route,72)]:
                    for j,q in enumerate(points):
                        if(q[0]-p[0])**2+(q[1]-p[1])**2>new['radius']**2:continue
                        best=max([tc[v]['effectValue']for z,v in board.items()if tc[v]['type']==3 and(q[0]-z[0])**2+(q[1]-z[1])**2<=tc[v]['radius']**2]or[0])
                        value+=mult*max(0,new['effectValue']-best)*(.4+j/max(1,len(points)-1))
                return weights[3]*value
            choices=[]
            for p in free:
                if p in board:continue
                for tid in [1,4,7]:
                    cfg=tc[tid]
                    if cfg['prices']<=cash-12:choices.append((benefit(p,cfg)/cfg['prices'],p,tid,'build'))
            for p,tid in board.items():
                old=tc[tid];cfg=tc.get(old['upgradeTo'])
                if cfg and cfg['prices']<=cash-12:choices.append((benefit(p,cfg,old)/cfg['prices'],p,cfg['id'],'upgrade'))
            if not choices:break
            score,p,tid,action=max(choices)
            if score<=0:break
            cash-=tc[tid]['prices'];spent+=tc[tid]['prices'];board[p]=tid
            extra.append(dict(waveOrdinal=wave,timeMs=0,action=action,row=p[1],col=p[0],towerId=tid))
        budgets.append(dict(wave=wave,observedBaseCash=before+spent-(sum(tc[o['towerId']]['prices']for o in extra if o['waveOrdinal']==wave)),conservativeAvailableBefore=before,conservativeCashAfter=cash))
    out=REPORT/f'L28/search-{tag}';out.mkdir(parents=True,exist_ok=True);f=out/f'{name}.json';assert not f.exists()
    f.write_text(json.dumps(original+extra,ensure_ascii=False,indent=2),encoding='utf-8')
    runs.append(dict(profileId='D04',levelId=28,strategy=tag+'-'+name,speed=1,operationsPath=str(f),waitForFunds=True,screenshots=True,captureStages=True))
    notes.append(dict(name=name,sourceRunId=r['metrics']['runId'],sourceIndex=114,observedUnspentPreparationCashW25=6825,allocationWeights=weights,budgets=budgets,extraTransactions=len(extra),additionalSpend=spent,predictionOnly=True,scope='Continue investing from W17 before original W22/23 failures. All original routes remain open. Recorded future cash is a conservative budget, not a guarantee of timing/outcome.'))
(REPORT/f'requests/{tag}.json').write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/f'audit/{tag}-bounds.json').write_text(json.dumps(dict(maxRuns=3,decisions=notes,termination='One real replay per allocation; no formal table changes'),ensure_ascii=False,indent=2),encoding='utf-8')
print('3 unexecuted phased L28 investments')
