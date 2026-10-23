"""Use an already observed zero-leak opening, then search later player investments."""
from formal_tools import *
import sys
sys.path.insert(0,str(ROOT/'.workbuddy/tools'))
import predictor as sim
level=int(sys.argv[1]);source=ROOT/'Library/BalanceWorkbench/campaign-r1-L13-L30-and-refinements/unity-results.json';actual=json.loads(source.read_text(encoding='utf-8'))
openings=[r for r in actual if r['levelId']==level and r['strategy']in['normal','power']and r['metrics']['waves'][0]['leaked']==0 and r['metrics']['completedWaveCount']>=1]
campaign=[r for r in actual if r['levelId']==level and r['strategy'].startswith('campaign-r1')and r['metrics']['waves'][0]['leaked']==0 and r['metrics']['completedWaveCount']>=1]
if campaign:openings.append(max(campaign,key=lambda r:(r['metrics']['completedWaveCount'],-r['metrics']['leaked'])))
unique={}
for opening in openings:
    key=tuple((o['row'],o['col'],o['towerId'])for o in opening['operations']if o['waveOrdinal']==1 and o['timeMs']==0)
    unique.setdefault(key,opening)
openings=list(unique.values())
assert openings,'No observed opening; wait for the real controls'
out=REPORT/f'L{level:02}/search-seeded-r3';out.mkdir(parents=True,exist_ok=False);plan=formal_plan();runs=[];summary=[]
policies=[('mixed38',dict(targetCount=38,upgradeAfter=24,types=[1,1,1,4,7,1,4,1,1,4],airWeight=6)),('coverage72',dict(targetCount=72,upgradeAfter=64,upgradeShare=.1,types=[1,1,1,4,7,1,4,1,1,4],airWeight=8,upgradeAirWeight=4,slowUpgradeWeight=70)),('air44',dict(targetCount=44,upgradeAfter=28,types=[1,1,1,7,1,4,1,1,4,1],airWeight=14,upgradeAirWeight=4,slowUpgradeWeight=90))]
for opening in openings:
    initial=[o for o in opening['operations']if o['waveOrdinal']==1 and o['timeMs']==0];assert all(o['action']=='build'for o in initial)
    for name,policy in policies:
        key=opening['strategy']+'-'+name;sim.POLICY.clear();sim.POLICY.update(policy,earlyNormalCount=3,cheapFallback=True,midwaveUpgrades=False,maxWallSeconds=120,preferredCells=[[o['col'],o['row']]for o in initial],towerTypeHints=initial)
        result=sim.simulate_level(plan,level,'mixed',40,out)
        # The replayable prefix must match the actually observed opening, including type/order.
        got=[(o['row'],o['col'],o['towerId'])for o in result['operations']if o['waveOrdinal']==1]
        expected=[(o['row'],o['col'],o['towerId'])for o in initial];assert got==expected,(got,expected)
        (out/f'{key}-prediction.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');path=out/f'{key}-operations.json';path.write_text(json.dumps(result['operations'],ensure_ascii=False,indent=2),encoding='utf-8')
        summary.append(dict(name=key,observedOpeningRunId=opening['metrics']['runId'],predictionOnly=True,result=result['result'],waves=result['metrics']['completedWaveCount'],leaked=result['leaked']))
        runs.append(dict(profileId='D04',levelId=level,strategy='seeded-r3-'+key,speed=1,operationsPath=str(path),waitForFunds=True,screenshots=True))
(out/'index.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');(out/'request.json').write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/seeded-r3-L{level:02}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8');print(level,summary,flush=True)
