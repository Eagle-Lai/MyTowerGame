"""Prepare materially different legal investment tests from real zero-leak results."""
from formal_tools import *
import collections,math
t=tables();tc={x['id']:x for x in t['tbtowerinfo']};sc={x['id']:x for x in t['tbsceneinfo']};maps={x['id']:x for x in t['tblevelmap']};runs=[];decisions=[]
for level in [2,3,4,5,6]:
 index=json.loads((REPORT/f'L{level:02}/trial-index.json').read_text(encoding='utf-8'));zero=[x for x in index if x.get('victory')and x.get('leaked')==0]
 best=min(zero,key=lambda x:(x['operations'],x['combatSeconds']));source=REPORT/f'raw-trials/{best["batch"]}/unity-results.json';r=json.loads(source.read_text(encoding='utf-8'))[best['index']]
 original=[{k:o[k]for k in['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']]
 candidates=[i for i,o in enumerate(original)if o['action']=='upgrade'and o['towerId']==3 and o['timeMs']==0 and o['waveOrdinal']>=20 and not any(x['row']==o['row']and x['col']==o['col']for x in original[i+1:])]
 assert candidates,(level,'No independent late upgrade')
 remove=candidates[-1];old=original[remove];wave=old['waveOrdinal'];mp=maps[sc[level]['mapId']];occupied={(o['col'],o['row'])for o in original};reserved={tuple(p)for b in r['waveBoundaries']if b['beforeWave']>=wave for p in b['pathCells']}|{tuple(p)for p in r['finalPathCells']}
 points={ch:(c,row)for row,line in enumerate(mp['cells'])for c,ch in enumerate(line)if ch in'SE'};s=points['S'];e=points['E'];air=[(s[0]+(e[0]-s[0])*k/80,s[1]+(e[1]-s[1])*k/80)for k in range(81)]
 choices=[(c,row)for row,line in enumerate(mp['cells'])for c,ch in enumerate(line)if ch=='.'and(c,row)not in occupied and(c,row)not in reserved]
 out=REPORT/f'L{level:02}/search-alternatives-r2';out.mkdir(exist_ok=False)
 for name,types in [('spread-aoe-air',[4,4,1,1]),('dedicated-aoe',[4,5]),('air-slow',[1,2,7])]:
  selected=[];extra=[];last=None
  for tid in types:
   cfg=tc[tid]
   if tid in[2,5]:cell=last;action='upgrade'
   else:
    remaining=[p for p in choices if p not in selected]
    assert remaining,(level,name)
    def score(p):
     ground=sum((p[0]-c)**2+(p[1]-row)**2<=cfg['radius']**2 for c,row in r['finalPathCells']);a=sum((p[0]-c)**2+(p[1]-row)**2<=cfg['radius']**2 for c,row in air)
     return ground+(a*.8 if cfg['canAttackAir']else 0)
    cell=max(remaining,key=score);selected.append(cell);last=cell;action='build'
   extra.append(dict(waveOrdinal=wave,timeMs=0,action=action,row=cell[1],col=cell[0],towerId=tid))
  assert sum(tc[o['towerId']]['prices']for o in extra)<=180
  ops=original[:remove]+extra+original[remove+1:];f=out/f'{name}.json';f.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
  decisions.append(dict(level=level,name=name,sourceRunId=r['metrics']['runId'],sourceSeal=r['profile']['runtimeContentHash'],removed=old,replacement=extra,predictionOnly=False,notYetTested=True))
  runs.append(dict(profileId='D04',levelId=level,strategy='alternative-r2-'+name,speed=1,operationsPath=str(f),waitForFunds=True,screenshots=True,captureStages=True))
(REPORT/'audit/alternative-investments-r2.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/'requests/alternatives-r2.json').write_text(json.dumps(dict(output=str(ROOT/'Library/BalanceWorkbench/alternatives-r2'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
print(len(runs),'untested alternative investment sequences')
