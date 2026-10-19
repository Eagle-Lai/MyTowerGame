"""Versioned, resumable evidence jobs. No source tables or production saves are modified."""
import argparse, concurrent.futures, copy, math, pathlib, time
import balance_pipeline as core
import balance_simulator as sim
from balance_campaign import capacity


def job(payload):
    recipe_path, profile, strategy, levels, mode, out, maze_root = payload
    recipe = core.read_json(recipe_path); plan = core.generate(recipe, profile)
    results = []
    for level in levels:
        board = next(m for m in plan['tables']['tblevelmap'] if m['id'] == level)
        audit = capacity(board['cells']); cap = audit['capacity']
        policy = {'capacity':cap,'upgradeShare':recipe.get('referencePolicy',{}).get('upgradeShare',.25)}
        if mode == 'high':policy.update(reservedPath=audit['reservedPath'],targetCount=cap,upgradeReserve=40,
            airWeight=recipe.get('referencePolicy',{}).get('airWeight',2),upgradeAirWeight=1,
            types=[1,4,1,7,4,1,1,4,7,1])
        if mode == 'maze':
            maze=core.read_json(pathlib.Path(maze_root)/f'L{level:02}.json')
            if not maze:raise ValueError('Missing maze blueprint for level '+str(level))
            blocked=[(r['col'],r['row']) for r in maze['layout']]
            if core.path_for(board['cells'],blocked)!=[tuple(c) for c in maze['reservedPath']]:
                raise ValueError('Maze blueprint differs from the candidate map: '+str(level))
            policy.update(blueprintCells=blocked,blueprintPath=maze['reservedPath'],targetCount=len(blocked),
                maxTowers=len(blocked),upgradeReserve=25,airWeight=12,upgradeAirWeight=6,
                types=[1,1,4,1,7,1,4,1,7,4],towerTypeHints=maze.get('towerTypeHints',[]),trackReentry=True)
        if mode in ['small','low']:
            limit = max(6,math.ceil(cap*.15)) if mode=='small' else max(max(6,math.ceil(cap*.15))+1,math.ceil(cap*.30))
            policy.update(maxTowers=limit,targetCount=limit,upgradeAfter=4,preferUpgrade=True,midwaveUpgrades=True,cheapFallback=True)
        destination = pathlib.Path(out)/mode/profile/strategy
        existing = destination/f'L{level:02}-{strategy}'/'result.json'
        result = core.read_json(existing)
        rating = next(r for r in plan['tables']['tblevelrating'] if r['id']==level)
        # JSON round-tripping normalizes coordinate tuples before resume checks.
        policy=__import__('json').loads(__import__('json').dumps(policy))
        if not result or result['planHash'] != rating['planHash'] or result.get('policy')!=policy or result.get('strategyRevision')!=sim.VERSION:
            sim.POLICY = policy
            result = sim.simulate_level(plan,level,strategy,100,destination)
        results.append({'profileId':profile,'levelId':level,'strategy':strategy,'mode':mode,
            'completed':result['metrics']['completedWaveCount'],'leaked':result['leaked'],
            'ratio':result['combatToParRatio'],'towers':result['waves'][-1]['towerCount'],
            'path':str(existing),'elapsedSec':result['elapsedSec']})
        core.progress('evidence_level',**results[-1])
    return results


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--recipe',default=str(core.DEFAULT_RECIPE));ap.add_argument('--out',required=True)
    ap.add_argument('--profiles',default='D04');ap.add_argument('--strategies',default='mixed');ap.add_argument('--levels',default='1,10,20,30')
    ap.add_argument('--modes',default='high');ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--maze-root',default='Luban/BalanceDesign/Evidence30x25/Mazes')
    args=ap.parse_args();recipe=core.read_json(args.recipe)
    levels=list(range(1,recipe['campaignLevelCount']+1)) if args.levels=='all' else list(map(int,args.levels.split(',')))
    profiles=[p['id'] for p in recipe['profiles']] if args.profiles=='all' else args.profiles.split(',')
    tasks=[(args.recipe,p,s,levels,m,args.out,args.maze_root) for p in profiles for s in args.strategies.split(',') for m in args.modes.split(',')]
    if len(tasks)<args.workers:
        size=max(1,math.ceil(len(levels)*len(tasks)/args.workers))
        tasks=[(r,p,s,ls[i:i+size],m,o,mr) for r,p,s,ls,m,o,mr in tasks for i in range(0,len(ls),size)]
    rows=[];started=time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        for result in executor.map(job,tasks):rows.extend(result)
    core.write_json(pathlib.Path(args.out)/'job-summary.json',{'elapsedSec':time.perf_counter()-started,'runs':rows,
        'coverage':'offline prediction; stars require sole C# evaluator; finite policy search is not a proof'})


if __name__=='__main__':main()
