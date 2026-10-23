"""Search legal one-time ground reallocation after observed last-air outcome."""
from formal_tools import *
import sys,math,argparse
parser=argparse.ArgumentParser();parser.add_argument('levels',nargs='+',type=int);parser.add_argument('--tag',default='ground-r1');args=parser.parse_args()
levels=args.levels;tag=args.tag;runs=[];tower={x['id']:x for x in tables()['tbtowerinfo']}
for level in levels:
    if level==4:source=ROOT/'Library/BalanceWorkbench/manual-campaign-r1-L04/unity-results.json'
    else:source=ROOT/'Library/BalanceWorkbench/campaign-r1-L05-L12/unity-results.json'
    candidates=[r for r in json.loads(source.read_text(encoding='utf-8'))if r['levelId']==level and r['metrics']['completedWaveCount']>=24 and not r['pendingOperations']]
    if not candidates:continue
    result=min(candidates,key=lambda r:(r['metrics']['leaked'],-r['metrics']['killed']))
    ops=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in result['operations']]
    if any(o['waveOrdinal']==25 and o['timeMs']>0 for o in ops):continue
    path=result['finalPathCells'];w=result['metrics']['waves'][-1]
    lastair=[e['combatMs']-round(w['combatStartSeconds']*1000)for e in result['enemyOutcomes']if e['waveOrdinal']==25 and e['isFlying']]
    if any(e['leaked'] and e['isFlying']for e in result['enemyOutcomes']):continue
    timing=math.ceil((max(lastair)+1000)/1000)*1000 if lastair else 40000
    available=[]
    for t in result['towerContributions']:
        cfg=tower[t['towerId']]
        if cfg['type']!=1 or cfg['level']<2:continue
        score=sum((.2+i/max(1,len(path)-1)) for i,(c,r)in enumerate(path)if (c-t['col'])**2+(r-t['row'])**2<=2.1**2)
        if score:available.append((score,cfg['level'],t['row'],t['col'],t['towerId']))
    available.sort(reverse=True);out=REPORT/f'L{level:02}/search-{tag}';out.mkdir(parents=True,exist_ok=False)
    for count,delay in [(3,0),(6,0),(9,0),(6,3000)]:
        selected=available[:count];new=list(ops);time=timing+delay
        # Complete refunds before spending; replacement uses the same legal cells.
        for score,grade,row,col,tid in selected:new.append(dict(waveOrdinal=25,timeMs=time,action='sell',row=row,col=col,towerId=tid))
        for score,grade,row,col,tid in selected:new.append(dict(waveOrdinal=25,timeMs=time,action='build',row=row,col=col,towerId=4))
        for score,grade,row,col,tid in selected:
            if grade==3:new.append(dict(waveOrdinal=25,timeMs=time,action='upgrade',row=row,col=col,towerId=5))
        pathfile=out/f'convert-{count}-at-{time}.json';pathfile.write_text(json.dumps(new,ensure_ascii=False,indent=2),encoding='utf-8')
        runs.append(dict(profileId='D04',levelId=level,strategy=f'{tag}-{count}-at-{time}',speed=1,operationsPath=str(pathfile),waitForFunds=True,screenshots=True,captureStages=True))
out=REPORT/f'requests/{tag}.json';out.write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=1200,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8');print(out,len(runs))
