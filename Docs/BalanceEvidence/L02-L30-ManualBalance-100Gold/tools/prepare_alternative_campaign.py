"""Merge existing unexecuted alternatives and add independent late allocations."""
from formal_tools import *
import sys
tag=sys.argv[1]
selected=json.loads((REPORT/'audit/development-reference-selections.json').read_text(encoding='utf-8'))['levels']
t=tables();tc={x['id']:x for x in t['tbtowerinfo']};runs=[];decisions=[]
for old in ['alternatives-r2','alternatives-r2-more']:
    request=json.loads((REPORT/f'requests/{old}.json').read_text(encoding='utf-8'))
    runs.extend(request['runs'])
covered={x['levelId']for x in runs}
for entry in selected:
    level=entry['level']
    if level in covered:continue
    r=json.loads((REPORT/entry['source']).read_text(encoding='utf-8'))[entry['sourceIndex']]
    ops=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']]
    choices=[i for i,o in enumerate(ops)if o['action']=='upgrade'and o['towerId']==3 and o['waveOrdinal']>=18 and o['timeMs']==0 and not any(q['row']==o['row']and q['col']==o['col']for q in ops[i+1:])]
    if not choices:
        decisions.append(dict(level=level,skipped='No independent late normal3 upgrade to reassign; requires a different bounded alternative.'));continue
    remove=choices[-1];old=ops[remove];wave=old['waveOrdinal']
    scene=next(x for x in t['tbsceneinfo']if x['id']==level);mp=next(x for x in t['tblevelmap']if x['id']==scene['mapId'])
    occupied={(o['col'],o['row'])for o in ops};reserved={tuple(p)for b in r['waveBoundaries']if b['beforeWave']>=wave for p in b['pathCells']}|{tuple(p)for p in r['finalPathCells']}
    free=[(c,row)for row,line in enumerate(mp['cells'])for c,ch in enumerate(line)if ch=='.'and(c,row)not in occupied and(c,row)not in reserved]
    ends={ch:(c,row)for row,line in enumerate(mp['cells'])for c,ch in enumerate(line)if ch in'SE'};a,b=ends['S'],ends['E'];air=[(a[0]+(b[0]-a[0])*j/80,a[1]+(b[1]-a[1])*j/80)for j in range(81)]
    for name,ids in [('dedicated-group',[4,5]),('air-slow',[1,2,7])]:
        if len(free)<sum(tid not in[2,5]for tid in ids):continue
        extra=[];used=[];last=None
        for tid in ids:
            cfg=tc[tid]
            if tid in[2,5]:point=last;action='upgrade'
            else:
                def score(p):
                    ground=sum((p[0]-c)**2+(p[1]-row)**2<=cfg['radius']**2 for c,row in r['finalPathCells'])
                    ac=sum((p[0]-c)**2+(p[1]-row)**2<=cfg['radius']**2 for c,row in air)
                    return ground+(.8*ac if cfg['canAttackAir']else 0)
                point=max([p for p in free if p not in used],key=score);used.append(point);last=point;action='build'
            extra.append(dict(waveOrdinal=wave,timeMs=0,action=action,row=point[1],col=point[0],towerId=tid))
        assert sum(tc[x['towerId']]['prices']for x in extra)<=180
        out=REPORT/f'L{level:02}/search-{tag}';out.mkdir(parents=True,exist_ok=True);f=out/f'{name}.json';assert not f.exists()
        f.write_text(json.dumps(ops[:remove]+extra+ops[remove+1:],ensure_ascii=False,indent=2),encoding='utf-8')
        runs.append(dict(profileId='D04',levelId=level,strategy=f'{tag}-{name}',speed=1,operationsPath=str(f),waitForFunds=True,screenshots=True,captureStages=True))
        decisions.append(dict(level=level,source=entry['source'],sourceIndex=entry['sourceIndex'],sourceRunId=r['metrics']['runId'],removed=old,replacement=extra,reason='Materially redirect180-gold normal upgrade into group output or air+slow on previously unused cells outside every relevant observed route; actual outcome pending.'))
request=dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs)
(REPORT/f'requests/{tag}.json').write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/f'audit/{tag}-bounds.json').write_text(json.dumps(dict(candidateCount=len(runs),coveredLevels=sorted({x['levelId']for x in runs}),extraDecisions=decisions,termination='one actual run per listed candidate; failures retained'),ensure_ascii=False,indent=2),encoding='utf-8')
print(len(runs),'unexecuted alternative allocations across',len({x['levelId']for x in runs}),'levels')
