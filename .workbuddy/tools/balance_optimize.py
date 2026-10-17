"""Search legal offline policy candidates. Never changes recipe, tables, or formal saves."""
import argparse,copy,math,pathlib,random,time
import balance_simulator as sim
from balance_pipeline import ROOT,DEFAULT_RECIPE,read_json,generate,write_json,path_for,progress,check_cancel

def score(r):
    m=r['metrics']
    if m['victory'] and not m['leaked']:
        return 1e9+1e6*(r['combatToParRatio']<=1)-r['combatToParRatio']*10000
    return m['completedWaveCount']*100000+m['killed']*50-m['leaked']*1000-r['combatToParRatio']*10

def candidates(plan,L,seed,iterations):
    rng=random.Random(seed);level=next(l for l in plan['tables']['tbsceneinfo'] if l['id']==L)
    cells=next(m['cells'] for m in plan['tables']['tblevelmap'] if m['id']==level['mapId']);p=path_for(cells);air=sim.straight(p[0],p[-1])
    free=[(x,y) for y,row in enumerate(cells) for x,c in enumerate(row) if c=='.' and
          any(sim.d2((x,y),p1)<=9 for p1 in p) and any(sim.d2((x,y),a)<=16 for a in air)]
    # Include existing three deterministic templates as comparison baselines.
    yield {}
    for _ in range(iterations):
        count=rng.choice([4,5,6,7,8,9,10,12]);coords=rng.sample(free,min(len(free),rng.choice([3,4,5,7,10])))
        # Same initial investment, spending priorities vary without borrowing any income.
        types=rng.choice([[1],[1,1,4,7],[1,4,1,7,1],[1,1,1,4,7],[4,1,1,7],[1,4,4,7,1],[1,1,7,4,1],[1,1,1,1,4,7]])
        yield {'preferredCells':coords,'types':types,'targetCount':count,'upgradeAfter':rng.choice([3,4,5,6]),
          'preferUpgrade':rng.choice([False,True]),'cheapFallback':True,'midwaveUpgrades':True,'midwaveAfter':rng.choice([2,3,4,5])}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--profile',default='D08');ap.add_argument('--level-min',type=int,default=1);ap.add_argument('--level-max',type=int,default=20)
    ap.add_argument('--iterations',type=int,default=100);ap.add_argument('--seed',type=int,default=42);ap.add_argument('--step-ms',type=int,default=100);ap.add_argument('--out',default=str(ROOT/'Library/BalanceWorkbench/optimization'))
    ap.add_argument('--recipe',default=str(DEFAULT_RECIPE))
    args=ap.parse_args();plan=generate(read_json(args.recipe),args.profile);out=pathlib.Path(args.out);results=[]
    for L in range(args.level_min,args.level_max+1):
        best=None;seen=0;started=time.perf_counter()
        for i,policy in enumerate(candidates(plan,L,args.seed+L,args.iterations)):
            check_cancel(out);sim.POLICY=policy
            r=sim.simulate_level(plan,L,'mixed',args.step_ms,out/'scratch');seen+=1
            if best is None or score(r)>score(best):
                best=copy.deepcopy(r);write_json(out/f'L{L:02}-best'/'result.json',best);write_json(out/f'L{L:02}-best'/'operations.json',best['operations'])
                progress('optimized_candidate',profileId=args.profile,levelId=L,iteration=i,completedWaves=r['metrics']['completedWaveCount'],leaked=r['leaked'],combatToParRatio=r['combatToParRatio'])
            if r['metrics']['victory'] and r['leaked']==0 and r['combatToParRatio']<=1:break
        best['searchIterations']=seen;best['searchElapsedSec']=time.perf_counter()-started;results.append(best)
    sim.POLICY={};write_json(out/'matrix.json',[{k:v for k,v in r.items() if k not in ['operations','waves']} for r in results])

if __name__=='__main__':main()
