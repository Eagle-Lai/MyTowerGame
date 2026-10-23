"""Finite player policy comparisons against frozen formal exports, not config tuning."""
from formal_tools import *
import sys
sys.path.insert(0,str(ROOT/'.workbuddy/tools'))
import predictor as sim
level=int(sys.argv[1]);out=REPORT/f'L{level:02}/search-expanded-r1';out.mkdir(parents=True,exist_ok=False);runs=[];results=[];plan=formal_plan()
policies=[
 ('dense-mixed',dict(targetCount=56,upgradeAfter=30,types=[1,1,1,4,7,1,4,1,4,1],airWeight=8,upgradeAirWeight=3,slowUpgradeWeight=100)),
 ('air-line',dict(targetCount=44,upgradeAfter=22,types=[1,1,1,7,1,4,1,1,4,1],airWeight=14,upgradeAirWeight=5,slowUpgradeWeight=80,preferUpgrade=True)),
 ('blast-lanes',dict(targetCount=50,upgradeAfter=26,types=[1,1,1,4,7,4,1,4,1,1],airWeight=5,upgradeAirWeight=2,slowUpgradeWeight=120)),
 ('wide-coverage',dict(targetCount=64,upgradeAfter=38,types=[1,1,1,4,7,1,4,1,1,4],airWeight=10,upgradeAirWeight=4,slowUpgradeWeight=100))]
for name,policy in policies:
    sim.POLICY.clear();sim.POLICY.update(policy,earlyNormalCount=3,cheapFallback=True,midwaveUpgrades=False,maxWallSeconds=180)
    r=sim.simulate_level(plan,level,'mixed',40,out)
    (out/f'{name}-prediction.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    path=out/f'{name}-operations.json';path.write_text(json.dumps(r['operations'],ensure_ascii=False,indent=2),encoding='utf-8')
    results.append(dict(name=name,result=r['result'],leaked=r['leaked'],waves=r['metrics']['completedWaveCount'],seconds=r['metrics']['combatElapsedSeconds']))
    runs.append(dict(profileId='D04',levelId=level,strategy='expanded-r1-'+name,speed=1,operationsPath=str(path),waitForFunds=True,screenshots=True))
(out/'request.json').write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/expanded-r1-L{level:02}'),stepSeconds=.02,stepsPerUpdate=1200,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
(out/'index.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print(level,json.dumps(results),flush=True)
