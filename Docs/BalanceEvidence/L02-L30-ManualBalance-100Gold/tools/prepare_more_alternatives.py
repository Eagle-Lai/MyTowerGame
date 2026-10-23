"""Prepare explicitly bounded alternative real investments for later successes."""
from formal_tools import *
import math
selected=json.loads((REPORT/'audit/development-reference-selections.json').read_text(encoding='utf-8'))['levels'];runs=[];decisions=[];t=tables();tc={x['id']:x for x in t['tbtowerinfo']}
for entry in selected:
    level=entry['level']
    if level not in [7,11,12,17,26,30]:continue
    r=json.loads((REPORT/entry['source']).read_text(encoding='utf-8'))[entry['sourceIndex']];ops=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']]
    independent=[i for i,o in enumerate(ops)if o['action']=='upgrade'and o['towerId']==3 and 18<=o['waveOrdinal']<=24 and o['timeMs']==0 and not any(q['row']==o['row']and q['col']==o['col']for q in ops[i+1:])]
    assert independent,level
    remove=independent[-1];old=ops[remove];wave=old['waveOrdinal'];s=next(x for x in t['tbsceneinfo']if x['id']==level);mp=next(x for x in t['tblevelmap']if x['id']==s['mapId']);reserved={tuple(p)for b in r['waveBoundaries']if b['beforeWave']>=wave for p in b['pathCells']}|{tuple(p)for p in r['finalPathCells']};occupied={(o['col'],o['row'])for o in ops};choices=[(c,row)for row,line in enumerate(mp['cells'])for c,ch in enumerate(line)if ch=='.'and(c,row)not in reserved and(c,row)not in occupied]
    out=REPORT/f'L{level:02}/search-alternatives-r2-more';out.mkdir(exist_ok=True)
    ends={ch:(c,row)for row,line in enumerate(mp['cells'])for c,ch in enumerate(line)if ch in'SE'};a,b=ends['S'],ends['E'];air=[(a[0]+(b[0]-a[0])*j/80,a[1]+(b[1]-a[1])*j/80)for j in range(81)]
    for name,ids in [('dedicated-aoe',[4,5]),('air-slow',[1,2,7])]:
        if sum(tid not in[2,5]for tid in ids)>len(choices):continue
        extra=[];picked=[];last=None
        for tid in ids:
            cfg=tc[tid]
            if tid in[2,5]:point=last;action='upgrade'
            else:
                assert choices,level
                def score(point):
                    ground=sum((point[0]-c)**2+(point[1]-row)**2<=cfg['radius']**2 for c,row in r['finalPathCells']);ac=sum((point[0]-c)**2+(point[1]-row)**2<=cfg['radius']**2 for c,row in air)
                    return ground+(ac*.8 if cfg['canAttackAir']else 0)
                point=max([p for p in choices if p not in picked],key=score);last=point;picked.append(point);action='build'
            extra.append(dict(waveOrdinal=wave,timeMs=0,action=action,row=point[1],col=point[0],towerId=tid))
        f=out/f'{name}.json';f.write_text(json.dumps(ops[:remove]+extra+ops[remove+1:],ensure_ascii=False,indent=2),encoding='utf-8')
        runs.append(dict(profileId='D04',levelId=level,strategy='alternative-r2-more-'+name,speed=1,operationsPath=str(f),waitForFunds=True,screenshots=True,captureStages=True))
        decisions.append(dict(level=level,sourceRunId=r['metrics']['runId'],sourceHash=r['profile']['runtimeContentHash'],removed=old,replacement=extra,routingReason='New points lie outside every relevant observed ground route and all original transaction coordinates; same primary route remains legal',spend=sum(tc[x['towerId']]['prices']for x in extra),tested=False))
(REPORT/'requests/alternatives-r2-more.json').write_text(json.dumps(dict(output=str(ROOT/'Library/BalanceWorkbench/alternatives-r2-more'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/'audit/alternative-investments-r2-more.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2),encoding='utf-8');print(len(runs),'unexecuted alternative allocations')
