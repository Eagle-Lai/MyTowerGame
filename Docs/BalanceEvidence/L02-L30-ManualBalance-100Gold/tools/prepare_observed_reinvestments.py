"""Bounded legal player purchases from real observed cash; no configuration writes."""
from formal_tools import *
import sys, math

tag=sys.argv[1]
source=ROOT/'Library/BalanceWorkbench/followups-r2-h/unity-results.json'
actual=json.loads(source.read_text(encoding='utf-8'))
t=tables();tc={x['id']:x for x in t['tbtowerinfo']};runs=[];notes=[]
# Each chosen failed candidate has already reached W25 with full health.
# Earlier successful defenses and its route are preserved.
for index in (list(map(int,sys.argv[2:]))if len(sys.argv)>2 else[87,97,98,101,102,103,105]):
    r=actual[index];level=r['levelId'];assert r['metrics']['completedWaveCount']==24
    original=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']]
    assert not r['pendingOperations']
    scene=next(x for x in t['tbsceneinfo']if x['id']==level)
    mp=next(x for x in t['tblevelmap']if x['id']==scene['mapId'])
    boundary=r['waveBoundaries'][-1];assert boundary['beforeWave']==25
    route=[tuple(p)for p in r['finalPathCells']]
    reserved={tuple(p)for p in boundary['pathCells']}|set(route)
    used={(o['col'],o['row'])for o in original}
    free=[(c,row)for row,line in enumerate(mp['cells'])for c,ch in enumerate(line)if ch=='.'and(c,row)not in used and(c,row)not in reserved]
    start=round(r['metrics']['waves'][-1]['combatStartSeconds']*1000)
    last_air=max([e['combatMs']-start for e in r['enemyOutcomes']if e['waveOrdinal']==25 and e['isFlying']]or[0])
    late=math.ceil((max(last_air,max([o['timeMs']for o in original if o['waveOrdinal']==25]or[0]))+1000)/1000)*1000
    for name,at,mixed in [('prepare-group',0,False),('prepare-group-slow',0,True),('earned-group-slow',late,True)]:
        board={}
        for o in original:
            if o['waveOrdinal']==25 and o['timeMs']>at:continue
            p=o['col'],o['row']
            if o['action']=='sell':board.pop(p)
            else:board[p]=o['towerId']
        cash=boundary['cash']+sum(e['rewardOrDamage']for e in r['enemyOutcomes']if e['waveOrdinal']==25 and not e['leaked']and e['combatMs']-start<=at)-sum(o['cost']for o in r['operations']if o['waveOrdinal']==25 and 0<o['timeMs']<=at)
        original_cash=cash;extra=[];strengthened=[]
        for _ in range(18):
            def ground(p,radius):return [(j,q)for j,q in enumerate(route)if(q[0]-p[0])**2+(q[1]-p[1])**2<=radius**2]
            options=[]
            for p in free:
                if p in board:continue
                for tid in ([4,7]if mixed else[4]):
                    cfg=tc[tid]
                    if cfg['prices']>cash:continue
                    hit=ground(p,cfg['radius'])
                    if not hit:continue
                    if tid==7:
                        benefit=0
                        for j,q in hit:
                            old=max([tc[v]['effectValue']for z,v in board.items()if tc[v]['type']==3 and(q[0]-z[0])**2+(q[1]-z[1])**2<=tc[v]['radius']**2]or[0])
                            benefit+=max(0,.16-old)*90*(.3+j/max(1,len(route)-1))
                    else:benefit=sum(.3+j/max(1,len(route)-1)for j,q in hit)*cfg['power']/(cfg['CD']/1000)
                    options.append((benefit/cfg['prices'],p,tid,'build'))
            for p,old in board.items():
                cfg=tc[old];new=tc.get(cfg['upgradeTo'])
                if not new or new['prices']>cash or cfg['type']not in([2,3]if mixed else[2]):continue
                if any((o['col'],o['row'])==p and(o['waveOrdinal'],o['timeMs'])>(25,at)for o in original):continue
                if cfg['type']==2:
                    gain=new['power']/(new['CD']/1000)-cfg['power']/(cfg['CD']/1000)
                    benefit=sum(.3+j/max(1,len(route)-1)for j,q in ground(p,new['radius']))*gain
                else:
                    benefit=0
                    for j,q in ground(p,new['radius']):
                        best=max([tc[v]['effectValue']for z,v in board.items()if tc[v]['type']==3 and(q[0]-z[0])**2+(q[1]-z[1])**2<=tc[v]['radius']**2]or[0])
                        benefit+=max(0,new['effectValue']-best)*90*(.3+j/max(1,len(route)-1))
                options.append((benefit/new['prices'],p,new['id'],'upgrade'))
            if not options:break
            score,p,tid,action=max(options)
            if score<=0:break
            cash-=tc[tid]['prices'];board[p]=tid
            extra.append(dict(waveOrdinal=25,timeMs=at,action=action,row=p[1],col=p[0],towerId=tid))
        if not extra:continue
        out=REPORT/f'L{level:02}/search-{tag}';out.mkdir(parents=True,exist_ok=True)
        variant=f'from-{index}-{name}';path=out/f'{variant}.json';assert not path.exists()
        operations=original+extra;operations.sort(key=lambda o:(o['waveOrdinal'],o['timeMs']))
        path.write_text(json.dumps(operations,ensure_ascii=False,indent=2),encoding='utf-8')
        runs.append(dict(profileId='D04',levelId=level,strategy=f'{tag}-{variant}',speed=1,operationsPath=str(path),waitForFunds=True,screenshots=True,captureStages=True))
        notes.append(dict(level=level,sourceIndex=index,sourceRunId=r['metrics']['runId'],variant=variant,observedCashAtTime=original_cash,investmentTimeMs=at,observedLastAirMs=last_air,remainingPredictedCash=cash,extra=extra,sourceLeakCount=r['metrics']['leaked'],predictionOnly=True,scope='Available funds are conservative observations from the original run. Purchases keep all observed routes open; actual Unity placement, cash and outcome must be measured.'))
(REPORT/f'requests/{tag}.json').write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/f'audit/{tag}-bounds.json').write_text(json.dumps(dict(maxRuns=len(runs),maxAdditionalTransactions=18,decisions=notes,termination='One actual replay for each listed legal purchase plan; no global optimum assertion'),ensure_ascii=False,indent=2),encoding='utf-8')
print(len(runs),'unexecuted player reinvestments')
