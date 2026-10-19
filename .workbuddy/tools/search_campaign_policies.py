"""Finite, reproducible legal policy comparisons, including paid sparse relocations."""
import argparse,concurrent.futures,copy,json,math,pathlib,random,time
import balance_pipeline as core
import balance_simulator as sim
from balance_campaign import capacity
from balance_optimize import candidates,score

def run(payload):
    recipe_path,profile,level,mode,budget,out=payload
    recipe=core.read_json(recipe_path);plan=core.generate(recipe,profile)
    root=pathlib.Path(out)/mode/profile/f'L{level:02}';rng=random.Random(20261019+level)
    if mode in ['small','low']:policies=list(candidates(plan,level,20261019+level,budget,mode))
    else:
        maze=core.read_json(core.ROOT/recipe['referencePolicy']['mazeDirectory']/f'L{level:02}.json')
        base={'capacity':maze['capacity'],'blueprintCells':[(r['col'],r['row']) for r in maze['layout']],
            'blueprintPath':maze['reservedPath'],'towerTypeHints':maze.get('towerTypeHints',[]),
            'targetCount':maze['towerCount'],'maxTowers':maze['towerCount'],'upgradeReserve':25,
            'airWeight':12,'upgradeAirWeight':6,'upgradeShare':.55,'types':[1,1,4,1,7,1,4,1,7,4]}
        policies=[base]
        for i in range(budget):
            p=copy.deepcopy(base)
            p.update(upgradeShare=rng.choice([0,.15,.3,.45,.7]),airWeight=rng.choice([4,8,12,20]),
                upgradeAirWeight=rng.choice([2,6,12]),earlyNormalCount=rng.choice([0,3,4,5]),
                reserveAirCells=rng.choice([0,6,12]),pathGainWeight=rng.choice([8,16,32]),
                futureCoverageWeight=rng.choice([.6,1.2,2.4]),upgradeAfter=rng.choice([6,8,12]),
                types=rng.choice([[1,1,4,1,7],[1,1,4,4,7],[1,1,1,4,7],[1,1,4,1,7,1,4,1,7,4]]))
            policies.append(p)
    best=None;trials=[];start=time.perf_counter()
    for i,policy in enumerate(policies):
        sim.POLICY=copy.deepcopy(policy)
        try:r=sim.simulate_level(plan,level,'mixed',100,root/'trials'/str(i),20261019+level)
        except ValueError as ex:trials.append({'index':i,'policy':policy,'error':str(ex)});continue
        trials.append({'index':i,'policy':policy,'completed':r['metrics']['completedWaveCount'],'leaked':r['leaked'],
            'combatMs':r['metrics']['combatElapsedMs'],'source':str(root/'trials'/str(i)/f'L{level:02}-mixed/result.json')})
        if best is None or score(r)>score(best):best=r;core.write_json(root/'best/result.json',r);core.write_json(root/'best/operations.json',r['operations'])
        # Reference search can stop at an affordable full legal route. Sparse
        # comparisons use the full declared budget, including all counterexamples.
        if mode=='maze' and r['metrics']['victory'] and r['leaked']==0 and len(r['waves'][-1]['layout'])==policy['targetCount']:break
    report={'profileId':profile,'levelId':level,'mode':mode,'seed':20261019+level,'requestedBudget':budget+1,
        'evaluated':len(trials),'elapsedSec':time.perf_counter()-start,'trials':trials,
        'bestLeaks':best['leaked'] if best else None,'bestCompleted':best['metrics']['completedWaveCount'] if best else None,
        'coverage':'Finite legal policy search; no global optimality or impossibility claim. Real Unity replay and sole evaluator required.'}
    core.write_json(root/'search.json',report);return {k:v for k,v in report.items() if k!='trials'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--recipe',default=str(core.DEFAULT_RECIPE));ap.add_argument('--profiles',default='D04')
    ap.add_argument('--levels',default='1,7,10,20,30');ap.add_argument('--modes',default='small,low');ap.add_argument('--iterations',type=int,default=12)
    ap.add_argument('--workers',type=int,default=4);ap.add_argument('--out',required=True);a=ap.parse_args();rows=[]
    jobs=[(a.recipe,p,int(l),m,a.iterations,a.out) for p in a.profiles.split(',') for l in a.levels.split(',') for m in a.modes.split(',')]
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as ex:
        for r in ex.map(run,jobs):rows.append(r);print(json.dumps(r),flush=True)
    core.write_json(pathlib.Path(a.out)/'search-index.json',rows)
if __name__=='__main__':main()
