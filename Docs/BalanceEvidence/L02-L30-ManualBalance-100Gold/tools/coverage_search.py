"""Finite placement/upgrade policies against frozen formal tables; no table edits."""
from formal_tools import *
import sys
sys.path.insert(0,str(ROOT/'.workbuddy/tools'))
import predictor as sim
level=int(sys.argv[1]);tag='coverage-r3';out=REPORT/f'L{level:02}/search-{tag}';out.mkdir(parents=True,exist_ok=False);plan=formal_plan();runs=[];summary=[]
policies=[
 ('coverage72',dict(targetCount=72,upgradeAfter=64,upgradeShare=.1,types=[1,1,1,4,7,1,4,1,1,4],airWeight=8,upgradeAirWeight=4,slowUpgradeWeight=70)),
 ('air84',dict(targetCount=84,upgradeAfter=72,upgradeShare=.08,types=[1,1,1,7,1,4,1,1,4,1],airWeight=14,upgradeAirWeight=5,slowUpgradeWeight=80)),
 ('group72',dict(targetCount=72,upgradeAfter=60,upgradeShare=.1,types=[1,1,1,4,7,4,1,4,1,1],airWeight=6,upgradeAirWeight=3,slowUpgradeWeight=100)),
 ('basic96-control',dict(targetCount=96,upgradeAfter=96,forbidUpgrades=True,types=[1,1,1,4,7,1,4,1,1,4],airWeight=10))]
for name,policy in policies:
    sim.POLICY.clear();sim.POLICY.update(policy,earlyNormalCount=3,cheapFallback=True,midwaveUpgrades=False,maxWallSeconds=120)
    r=sim.simulate_level(plan,level,'mixed',40,out)
    (out/f'{name}-prediction.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    ops=out/f'{name}-operations.json';ops.write_text(json.dumps(r['operations'],ensure_ascii=False,indent=2),encoding='utf-8')
    summary.append(dict(name=name,result=r['result'],waves=r['metrics']['completedWaveCount'],leaked=r['leaked'],operationCount=len(r['operations'])))
    runs.append(dict(profileId='D04',levelId=level,strategy=f'{tag}-{name}',speed=1,operationsPath=str(ops),waitForFunds=True,screenshots=True))
(out/'request.json').write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}-L{level:02}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
(out/'index.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(level,summary,flush=True)
