"""Search legal spatial tower roles against frozen formal data, never write tables."""
from formal_tools import *
import sys,math
sys.path.insert(0,str(ROOT/'.workbuddy/tools'))
import predictor as sim
level=int(sys.argv[1]);plan=formal_plan()
raw=json.loads((REPORT/'raw-trials/campaign-r1-L13-L30-and-refinements/unity-results.json').read_text(encoding='utf-8'))
if level<13:
 raw+=json.loads((REPORT/'raw-trials/campaign-r1-L05-L12/unity-results.json').read_text(encoding='utf-8'))
choices=[r for r in raw if r['levelId']==level and r['metrics']['completedWaveCount']>=1 and r['metrics']['waves'][0]['leaked']==0]
assert choices
source=max(choices,key=lambda r:(r['metrics']['completedWaveCount'],-r['metrics']['leaked']))
opening=[o for o in source['operations']if o['waveOrdinal']==1 and o['timeMs']==0]
assert opening and all(o['action']=='build'for o in opening)
layout=json.loads((REPORT/f'L{level:02}/search-campaign-r1/maze.json').read_text(encoding='utf-8'))
scene=next(s for s in plan['tables']['tbsceneinfo']if s['id']==level);mp=next(m for m in plan['tables']['tblevelmap']if m['id']==scene['mapId'])
points={ch:(c,r)for r,line in enumerate(mp['cells'])for c,ch in enumerate(line)if ch in'SE'};s=points['S'];e=points['E'];dx=e[0]-s[0];dy=e[1]-s[1];length=math.hypot(dx,dy)
cells=[(p['col'],p['row'])for p in layout['layout']];initial={(o['col'],o['row'])for o in opening}
def distance(p):return abs((p[0]-s[0])*dy-(p[1]-s[1])*dx)/length
out=REPORT/f'L{level:02}/search-role-r5';out.mkdir(parents=True,exist_ok=False);runs=[];rows=[]
for name,band,slow_count,up_after,prefer in [('wide-core',2.5,3,26,True),('wide-spread',2.5,3,44,False),('narrow-core',1.5,2,28,True),('wide-four-slow',2.5,4,36,False)]:
 slow=[]
 for i in range(slow_count):
  fraction=(i+.5)/slow_count;point=(s[0]+dx*fraction,s[1]+dy*fraction)
  options=[p for p in cells if p not in slow and p not in initial and distance(p)<=2.1]
  if options:slow.append(min(options,key=lambda p:sim.d2(p,point)))
 hints=[dict(col=p[0],row=p[1],towerId=7 if p in slow else 1 if distance(p)<=band else 4)for p in cells if p not in initial]+[{k:o[k]for k in['row','col','towerId']}for o in opening]
 sim.POLICY.clear();sim.POLICY.update(targetCount=60,upgradeAfter=up_after,preferUpgrade=prefer,upgradeShare=.2,cheapFallback=True,blueprintCells=[list(p)for p in cells],blueprintPath=layout['reservedPath'],reservedPath=layout['reservedPath'],towerTypeHints=hints,preferredCells=[[o['col'],o['row']]for o in opening],airWeight=18,upgradeAirWeight=8,slowUpgradeWeight=220,maxWallSeconds=90,midwaveUpgrades=False)
 result=sim.simulate_level(plan,level,'mixed',40,out)
 path=out/f'{name}-operations.json';path.write_text(json.dumps(result['operations'],ensure_ascii=False,indent=2),encoding='utf-8')
 (out/f'{name}-prediction.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 rows.append(dict(name=name,result=result['result'],waves=result['metrics']['completedWaveCount'],leaked=result['leaked'],predictionOnly=True,openingRunId=source['metrics']['runId']))
 runs.append(dict(profileId='D04',levelId=level,strategy='role-r5-'+name,speed=1,operationsPath=str(path),waitForFunds=True,screenshots=True))
(out/'index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'request.json').write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/role-r5-L{level:02}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
print(level,rows,flush=True)
