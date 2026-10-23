"""Search player actions against formal exported tables. Never authors config."""
from formal_tools import *
import sys,time
sys.path.insert(0,str(ROOT/'.workbuddy/tools'))
import balance_simulator as sim
import balance_maze as maze

level=int(sys.argv[1]);tag=sys.argv[2];out=REPORT/f'L{level:02}/search-{tag}';out.mkdir(parents=True,exist_ok=False)
plan=formal_plan();cells=next(x['cells'] for x in plan['tables']['tblevelmap'] if x['id']==next(l['mapId'] for l in plan['tables']['tbsceneinfo'] if l['id']==level))
layout=maze.search(cells,42+level,300);maze.add_air_service(cells,layout)
(out/'maze.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf-8')
policies=[
 ('greedy-mixed',dict(targetCount=38,upgradeAfter=24,cheapFallback=True,types=[1,1,1,4,7,1,4,1,1,4],earlyNormalCount=3,airWeight=6,midwaveUpgrades=False)),
 ('air-upgrades',dict(targetCount=30,upgradeAfter=18,cheapFallback=True,types=[1,1,1,7,1,4,1,1,4,1],earlyNormalCount=3,airWeight=14,upgradeAirWeight=3,preferUpgrade=True,midwaveUpgrades=False)),
 ('folded-maze',dict(targetCount=48,upgradeAfter=30,cheapFallback=True,blueprintCells=[[p['col'],p['row']] for p in layout['layout']],blueprintPath=layout['reservedPath'],reservedPath=layout['reservedPath'],types=[1,1,1,4,7,1,4,1,4,1],earlyNormalCount=3,airWeight=8,midwaveUpgrades=False))]
index=[];runs=[]
for name,policy in policies:
    sim.POLICY.clear();sim.POLICY.update(policy,maxWallSeconds=180)
    result=sim.simulate_level(plan,level,'mixed',40,out)
    (out/f'{name}-prediction.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    operations=result['operations'];opfile=out/f'{name}-operations.json';opfile.write_text(json.dumps(operations,ensure_ascii=False,indent=2),encoding='utf-8')
    index.append(dict(name=name,result=result.get('result'),leaked=result.get('leaked'),operations=len(operations)))
    runs.append(dict(profileId='D04',levelId=level,strategy=f'{tag}-{name}',speed=1,operationsPath=str(opfile),waitForFunds=True,screenshots=True))
request=dict(output=str(ROOT/f'Library/BalanceWorkbench/manual-{tag}-L{level:02}'),stepSeconds=.02,stepsPerUpdate=200,runs=runs)
(out/'request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(index,ensure_ascii=False));print(out/'request.json')
