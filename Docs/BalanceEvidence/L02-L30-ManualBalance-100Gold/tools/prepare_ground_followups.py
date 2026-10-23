"""Bounded legal player investments from observed r2 late-ground failures."""
from formal_tools import *
import sys,math,collections
source=pathlib.Path(sys.argv[1]);tag=sys.argv[2];rows=json.loads(source.read_text(encoding='utf-8'));h=runtime_hash();by=collections.defaultdict(list);t=tables();tc={x['id']:x for x in t['tbtowerinfo']};runs=[];decisions=[]
for i,r in enumerate(rows):
    if r['profile']['runtimeContentHash']!=h or not r['enemyOutcomes']:continue
    leaks=[e for e in r['enemyOutcomes']if e['leaked']]
    if not leaks or any(e['isFlying']or e['waveOrdinal']!=25 for e in leaks):continue
    if r['metrics']['completedWaveCount']<24:continue
    by[r['levelId']].append((i,r))
for level,options in by.items():
    i,r=min(options,key=lambda x:(x[1]['metrics']['leaked'],sum(o['timeMs']>0 for o in x[1]['operations']),-x[1]['metrics']['killed']))
    out=REPORT/f'L{level:02}/search-{tag}';out.mkdir(exist_ok=False)
    (out/'source-result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    base=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']]
    w=r['metrics']['waves'][-1];start=round(w['combatStartSeconds']*1000);lastair=max([e['combatMs']-start for e in r['enemyOutcomes']if e['waveOrdinal']==25 and e['isFlying']]or[0]);lastop=max([o['timeMs']for o in base if o['waveOrdinal']==25]or[0]);timing=math.ceil(max(lastair+2000,lastop+3000)/1000)*1000
    firstleak=min(e['combatMs']-start for e in r['enemyOutcomes']if e['leaked'])
    path=r['finalPathCells'];inventory=r['towerContributions']
    def cov(x,radius):return sum((.25+j/max(1,len(path)-1))for j,(c,row)in enumerate(path)if(c-x['col'])**2+(row-x['row'])**2<=radius**2)
    upgrades=sorted([x for x in inventory if tc[x['towerId']]['upgradeTo']and tc[x['towerId']]['type']in[1,2]],key=lambda x:cov(x,tc[tc[x['towerId']]['upgradeTo']]['radius'])*(tc[tc[x['towerId']]['upgradeTo']]['power']*1000/tc[tc[x['towerId']]['upgradeTo']]['CD']-tc[x['towerId']]['power']*1000/tc[x['towerId']]['CD'])/tc[tc[x['towerId']]['upgradeTo']]['prices'],reverse=True)
    normals=sorted([x for x in inventory if tc[x['towerId']]['type']==1 and tc[x['towerId']]['level']>=2],key=lambda x:cov(x,tc[5]['radius']),reverse=True)
    if len([e for e in r['enemyOutcomes']if e['leaked']])==1:policies=[('upgrade1',1,'up'),('upgrade3',3,'up'),('convert3',3,'convert')]
    else:policies=[('upgrade3',3,'up'),('convert3',3,'convert'),('convert6',6,'convert')]
    for name,count,action in policies:
        extra=[]
        if action=='up':
            for x in upgrades[:count]:extra.append(dict(waveOrdinal=25,timeMs=timing,action='upgrade',row=x['row'],col=x['col'],towerId=tc[x['towerId']]['upgradeTo']))
        else:
            selected=normals[:count]
            for x in selected:extra.append(dict(waveOrdinal=25,timeMs=timing,action='sell',row=x['row'],col=x['col'],towerId=x['towerId']))
            for x in selected:extra.append(dict(waveOrdinal=25,timeMs=timing,action='build',row=x['row'],col=x['col'],towerId=4))
            for x in selected:
                if tc[x['towerId']]['level']==3:extra.append(dict(waveOrdinal=25,timeMs=timing,action='upgrade',row=x['row'],col=x['col'],towerId=5))
        if not extra:continue
        f=out/f'{name}-at-{timing}.json';f.write_text(json.dumps(base+extra,ensure_ascii=False,indent=2),encoding='utf-8')
        runs.append(dict(profileId='D04',levelId=level,strategy=f'{tag}-{name}-at-{timing}',speed=1,operationsPath=str(f),waitForFunds=True,screenshots=True,captureStages=True))
    decisions.append(dict(level=level,source=str(source),sourceIndex=i,sourceRunId=r['metrics']['runId'],runtimeContentHash=h,lastAirOutcomeMs=lastair,lastPriorTransactionMs=lastop,firstGroundLeakMs=firstleak,proposedTimeMs=timing,lateBeforeObservedLeak=timing<firstleak,policies=[p[0]for p in policies],maxRuns=len(policies),purpose='Spend real funds after air completion; test legal one-time upgrades or same-cell reallocation; no data edits or claims of success'))
request=dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs)
(REPORT/f'requests/{tag}.json').write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/f'audit/{tag}-search-bounds.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2),encoding='utf-8')
print(len(runs),'unexecuted bounded player-action followups across',len(decisions),'levels')
