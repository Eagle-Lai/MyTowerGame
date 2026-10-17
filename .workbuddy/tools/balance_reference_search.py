"""Build a reproducible per-level reference index from legal simulations and search."""
import argparse,copy,pathlib,time
import balance_pipeline as core
import balance_simulator as sim
from balance_optimize import candidates,score


def good(r):return r['metrics']['victory'] and not r['leaked'] and r['combatToParRatio']<=1


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--recipe',required=True);ap.add_argument('--profiles',default='D05,D06,D07,D08')
    ap.add_argument('--iterations',type=int,default=100);ap.add_argument('--out',required=True);args=ap.parse_args()
    recipe=core.read_json(args.recipe);out=pathlib.Path(args.out);index=[]
    for profile in args.profiles.split(','):
        plan=core.generate(recipe,profile)
        for L in range(1,21):
            sources=[]
            for strategy in ['normal','power','mixed']:
                p=core.ROOT/'Library/BalanceWorkbench'/('gradient-'+strategy+'-matrix')/profile/f'L{L:02}-{strategy}'/'result.json'
                if p.exists():sources.append((core.read_json(p),p))
            for extra in ['gradient-wall-opening-search','gradient-optimize-D08-L20'] if profile=='D08' else []:
                p=core.ROOT/'Library/BalanceWorkbench'/extra/f'L{L:02}-best'/'result.json'
                if p.exists():sources.append((core.read_json(p),p))
            sources=[(r,p) for r,p in sources if r['planHash']==plan['tables']['tblevelrating'][L-1]['planHash']]
            best,path=max(sources,key=lambda item:score(item[0])) if sources else (None,None)
            if best is None or not good(best):
                for i,policy in enumerate(candidates(plan,L,42017+L,args.iterations)):
                    core.check_cancel(out);sim.POLICY=policy
                    r=sim.simulate_level(plan,L,'mixed',100,out/'scratch')
                    if best is None or score(r)>score(best):
                        best=copy.deepcopy(r);path=out/profile/f'L{L:02}-best'/'result.json'
                        core.write_json(path,best);core.write_json(path.with_name('operations.json'),best['operations'])
                        core.progress('better_reference',profileId=profile,levelId=L,iteration=i,leaked=best['leaked'],ratio=best['combatToParRatio'])
                    if good(best):break
            sim.POLICY={}
            index.append({'profileId':profile,'levelId':L,'planHash':best['planHash'],'noLeakUnderParPrediction':good(best),
                'leaked':best['leaked'],'combatToParRatio':best['combatToParRatio'],'resultPath':str(path),
                'operationsPath':str(path.with_name('operations.json'))})
            core.write_json(out/'reference_index.json',index)
            core.progress('reference_complete',profileId=profile,levelId=L,passed=good(best))


if __name__=='__main__':main()
