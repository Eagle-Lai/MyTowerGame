"""Bounded r2 player-action predictions using the current formal exports only."""
from formal_tools import *
import sys
sys.path.insert(0,str(ROOT/'.workbuddy/tools'))
import predictor as sim
level=int(sys.argv[1]);mode=sys.argv[2]if len(sys.argv)>2 else'r2';assert mode in ['r2','r2b'];plan=formal_plan();actual=[]
for tag in ['campaign-r1-L13-L30-and-refinements','campaign-r1-L05-L12','targeted-r3-r4']:
 actual+=json.loads((REPORT/f'raw-trials/{tag}/unity-results.json').read_text(encoding='utf-8'))
candidates=[r for r in actual if r['levelId']==level and r['metrics']['completedWaveCount']>=5 and r['metrics']['waves'][0]['leaked']==0 and (r['state']=='finished'or mode=='r2b'and r['state']=='operation_incomplete')]
assert candidates
source=max(candidates,key=lambda r:(r['metrics']['completedWaveCount'],-r['metrics']['leaked']))
first=min([o['waveOrdinal']for o in source['enemyOutcomes']if o['leaked']]or[26]);start=max(5,first-3)
opening=[{k:o[k]for k in['waveOrdinal','timeMs','action','row','col','towerId']}for o in source['operations']if o['waveOrdinal']<start]
assert not any(o['timeMs']for o in opening)
maze=json.loads((REPORT/f'L{level:02}/search-campaign-r1/maze.json').read_text(encoding='utf-8'))
out=REPORT/f'L{level:02}/search-refined-{mode}';out.mkdir(exist_ok=False);rows=[];runs=[]
policies=[
 ('mixed38',dict(targetCount=38,upgradeAfter=24,types=[1,1,1,4,7,1,4,1,1,4],airWeight=6)),
 ('coverage72',dict(targetCount=72,upgradeAfter=64,upgradeShare=.1,types=[1,1,1,4,7,1,4,1,1,4],airWeight=8,upgradeAirWeight=4,slowUpgradeWeight=70)),
 ('group72',dict(targetCount=72,upgradeAfter=56,upgradeShare=.1,types=[1,4,1,4,7,1,4,1,4,1],airWeight=5,upgradeAirWeight=3,slowUpgradeWeight=70)),
 ('maze-spread',dict(targetCount=60,upgradeAfter=40,upgradeShare=.15,types=[1,1,7,1,1,4,1,1,7,1],airWeight=20,upgradeAirWeight=10,slowUpgradeWeight=220,blueprintCells=[[p['col'],p['row']]for p in maze['layout']],blueprintPath=maze['reservedPath'],reservedPath=maze['reservedPath'])),
 ('balanced-core',dict(targetCount=48,upgradeAfter=24,preferUpgrade=True,types=[1,1,7,1,4,1,1,4,1,1],airWeight=16,upgradeAirWeight=5,slowUpgradeWeight=220)),
 ('dense-group',dict(targetCount=86,upgradeAfter=76,upgradeShare=.05,types=[1,4,1,4,7,1,4,1,4,1],airWeight=8,upgradeAirWeight=4,slowUpgradeWeight=100))]
for name,policy in policies:
 sim.POLICY.clear();sim.POLICY.update(policy,scriptedOperations=opening,adaptiveFromWave=start,cheapFallback=True,maxWallSeconds=120,midwaveUpgrades=False)
 result=sim.simulate_level(plan,level,'mixed',40,out)
 f=out/f'{name}-operations.json';f.write_text(json.dumps(result['operations'],ensure_ascii=False,indent=2),encoding='utf-8')
 (out/f'{name}-prediction.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 rows.append(dict(name=name,waves=result['metrics']['completedWaveCount'],leaked=result['leaked'],predictionOnly=True,result=result['result'],openingSourceRunId=source['metrics']['runId'],openingSourceSeal=source['profile']['runtimeContentHash'],currentFormalSeal=runtime_hash(),adaptiveFromWave=start))
 runs.append(dict(profileId='D04',levelId=level,strategy=f'refined-{mode}-'+name,speed=1,operationsPath=str(f),waitForFunds=True,screenshots=True))
(out/'index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'request.json').write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/refined-{mode}-L{level:02}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
print(level,rows,flush=True)
