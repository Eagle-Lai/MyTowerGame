"""Bounded player investment search from a real observed opening. No config writes."""
from formal_tools import *
import sys
sys.path.insert(0,str(ROOT/'.workbuddy/tools'))
import predictor as sim

level=int(sys.argv[1]);tag=sys.argv[2] if len(sys.argv)>2 else 'adaptive-r4'
actual=json.loads((ROOT/'Library/BalanceWorkbench/campaign-r1-L13-L30-and-refinements/unity-results.json').read_text(encoding='utf-8'))
sources=[r for r in actual if r['levelId']==level and r['strategy']=='campaign-r1-folded-maze']
assert sources
source=sources[0];first_leak=min([x['waveOrdinal']for x in source['enemyOutcomes']if x['leaked']] or [26])
start=max(5,first_leak-3)
opening=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in source['operations']if o['waveOrdinal']<start]
assert not any(o['timeMs'] for o in opening)
layout=json.loads((REPORT/f'L{level:02}/search-campaign-r1/maze.json').read_text(encoding='utf-8'))
out=REPORT/f'L{level:02}/search-{tag}';out.mkdir(parents=True,exist_ok=False)
policies=[
 ('air-core',dict(targetCount=48,upgradeAfter=18,preferUpgrade=True,types=[1,1,1,7,1,4,1,1,7,1],airWeight=20,upgradeAirWeight=15,slowUpgradeWeight=300)),
 ('air-spread',dict(targetCount=60,upgradeAfter=40,upgradeShare=.15,types=[1,1,7,1,1,4,1,1,7,1],airWeight=24,upgradeAirWeight=12,slowUpgradeWeight=250)),
 ('balanced-core',dict(targetCount=48,upgradeAfter=24,preferUpgrade=True,types=[1,1,7,1,4,1,1,4,1,1],airWeight=16,upgradeAirWeight=5,slowUpgradeWeight=220)),
 ('maze-air-core',dict(targetCount=48,upgradeAfter=24,preferUpgrade=True,types=[1,1,1,7,1,4,1,1,7,1],airWeight=20,upgradeAirWeight=12,slowUpgradeWeight=260,blueprintCells=[[p['col'],p['row']]for p in layout['layout']],blueprintPath=layout['reservedPath'],reservedPath=layout['reservedPath'])),
 ('maze-air-spread',dict(targetCount=60,upgradeAfter=40,upgradeShare=.15,types=[1,1,7,1,1,4,1,1,7,1],airWeight=20,upgradeAirWeight=10,slowUpgradeWeight=220,blueprintCells=[[p['col'],p['row']]for p in layout['layout']],blueprintPath=layout['reservedPath'],reservedPath=layout['reservedPath'])),
 ('mixed-dense',dict(targetCount=72,upgradeAfter=56,upgradeShare=.1,types=[1,1,1,4,7,1,4,1,1,4],airWeight=10,upgradeAirWeight=5,slowUpgradeWeight=180))]
plan=formal_plan();rows=[];runs=[]
for name,policy in policies:
 sim.POLICY.clear();sim.POLICY.update(policy,scriptedOperations=opening,adaptiveFromWave=start,cheapFallback=True,midwaveUpgrades=False,maxWallSeconds=150)
 try: result=sim.simulate_level(plan,level,'mixed',40,out)
 except ValueError as e:
  rows.append(dict(name=name,error=str(e),predictionOnly=True));continue
 opfile=out/f'{name}-operations.json';opfile.write_text(json.dumps(result['operations'],ensure_ascii=False,indent=2),encoding='utf-8')
 (out/f'{name}-prediction.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 rows.append(dict(name=name,waves=result['metrics']['completedWaveCount'],leaked=result['leaked'],result=result['result'],operationCount=len(result['operations']),predictionOnly=True,realOpeningRunId=source['metrics']['runId'],adaptiveFromWave=start))
 runs.append(dict(profileId='D04',levelId=level,strategy=tag+'-'+name,speed=1,operationsPath=str(opfile),waitForFunds=True,screenshots=True))
(out/'index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'request.json').write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}-L{level:02}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
print(level,rows,flush=True)
