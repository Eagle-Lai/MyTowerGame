"""Bounded search over legal player transactions before fast ground enemies escape."""
from formal_tools import *
import sys,math,argparse
p=argparse.ArgumentParser();p.add_argument('levels',nargs='+',type=int);p.add_argument('--tag',default='early-ground-r2');a=p.parse_args()
t=tables();tower={r['id']:r for r in t['tbtowerinfo']};scenes={r['id']:r for r in t['tbsceneinfo']};maps={r['id']:r for r in t['tblevelmap']};runs=[];decisions=[]
for level in a.levels:
    source=ROOT/'Library/BalanceWorkbench'/('manual-campaign-r1-L04'if level==4 else 'campaign-r1-L05-L12')/'unity-results.json'
    choices=[r for r in json.loads(source.read_text(encoding='utf-8'))if r['levelId']==level and r['metrics']['completedWaveCount']>=24 and not r['pendingOperations']]
    if not choices:continue
    result=min(choices,key=lambda r:(r['metrics']['leaked'],-r['metrics']['killed']))
    base=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in result['operations']]
    board=result['waveBoundaries'][-1]['layout'];path=result['finalPathCells'];cells=maps[scenes[level]['mapId']]['cells'];points={ch:(c,r)for r,row in enumerate(cells)for c,ch in enumerate(row)if ch in 'SE'}
    def airscore(row,col,radius):
        s=points['S'];e=points['E'];return sum((s[0]+(e[0]-s[0])*k/100-col)**2+(s[1]+(e[1]-s[1])*k/100-row)**2<=radius**2 for k in range(101))
    available=[]
    for x in board:
        cfg=tower[x['towerId']]
        if cfg['type']!=1 or cfg['level']<2:continue
        ground=sum((.2+i/max(1,len(path)-1)) for i,(c,r)in enumerate(path)if(c-x['col'])**2+(r-x['row'])**2<=2.1**2)
        if not ground:continue
        # Prior-wave actual air contribution estimates opportunity cost; geometry breaks ties.
        air=airscore(x['row'],x['col'],cfg['radius'])
        available.append((ground/(1+x['airHits']/30+air/20),x['row'],x['col'],x['towerId']))
    available.sort(reverse=True);out=REPORT/f'L{level:02}/search-{a.tag}';out.mkdir(parents=True,exist_ok=False)
    variants=[(3,0),(6,0),(9,0),(6,15000)]
    if level==4:variants=[(2,0),(2,0),(2,0),(3,0)]
    for v,(count,time)in enumerate(variants):
        selected=available[:count]
        if level==4:selected=[(1,6,1,3),(1,5,1,3)] + ([(1,1,3,2)]if v==3 else [])
        new=list(base);extra=[]
        for _,row,col,tid in selected:extra.append(dict(waveOrdinal=25,timeMs=time,action='sell',row=row,col=col,towerId=tid))
        for _,row,col,tid in selected:extra.append(dict(waveOrdinal=25,timeMs=time,action='build',row=row,col=col,towerId=4))
        if level==4:
            upgrades=[[(4,13,3),(5,13,3)],[(4,13,3),(4,5,3)],[(3,3,2),(3,3,3)],[(4,13,3),(4,5,3)]][v]
            for row,col,tid in upgrades:extra.append(dict(waveOrdinal=25,timeMs=time,action='upgrade',row=row,col=col,towerId=tid))
            # One finite later reallocation from remaining upgraded normals, after the original air window.
            later=[(1,3,2),(3,1,3),(4,7,3),(5,9,3)];sold={(r,c)for _,r,c,_ in selected}
            for row,col,tid in later:
                if(row,col)not in sold:extra.append(dict(waveOrdinal=25,timeMs=40000,action='sell',row=row,col=col,towerId=tid))
            for row,col,tid in later:
                if(row,col)not in sold:extra.append(dict(waveOrdinal=25,timeMs=40000,action='build',row=row,col=col,towerId=4))
            for row,col,tid in later:
                if(row,col)not in sold and tid==3:extra.append(dict(waveOrdinal=25,timeMs=40000,action='upgrade',row=row,col=col,towerId=5))
        else:
            for _,row,col,tid in selected:
                if tid==3:extra.append(dict(waveOrdinal=25,timeMs=time,action='upgrade',row=row,col=col,towerId=5))
        new+=extra;new.sort(key=lambda o:(o['waveOrdinal'],o['timeMs']))
        opfile=out/f'candidate-{v}.json';opfile.write_text(json.dumps(new,ensure_ascii=False,indent=2),encoding='utf-8')
        runs.append(dict(profileId='D04',levelId=level,strategy=f'{a.tag}-{v}-count{count}-at{time}',speed=1,operationsPath=str(opfile),waitForFunds=True,screenshots=True,captureStages=True))
        decisions.append(dict(level=level,candidate=v,sourceRunId=result['metrics']['runId'],ranking=available,selected=selected,transactions=extra))
(REPORT/f'requests/{a.tag}.json').write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/{a.tag}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/f'audit/{a.tag}-decisions.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2),encoding='utf-8');print(len(runs),'bounded early reallocation trials prepared')
