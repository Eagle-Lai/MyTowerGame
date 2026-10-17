"""Retain several legal, distinct offline operations for real Unity replay."""
import argparse,copy,pathlib,random
import balance_pipeline as core
import balance_simulator as sim
from balance_optimize import candidates,score


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--recipe',default=str(core.DEFAULT_RECIPE));ap.add_argument('--profile',default='D04')
    ap.add_argument('--levels',required=True);ap.add_argument('--iterations',type=int,default=40);ap.add_argument('--out',required=True)
    args=ap.parse_args();plan=core.generate(core.read_json(args.recipe),args.profile);out=pathlib.Path(args.out);index=[]
    for L in map(int,args.levels.split(',')):
        level=next(x for x in plan['tables']['tbsceneinfo'] if x['id']==L);cells=next(m['cells'] for m in plan['tables']['tblevelmap'] if m['id']==level['mapId'])
        rows=len(cells);cols=len(cells[0]);wall=[]
        for x in [cols//3,cols//2,cols*2//3]:
            first=[(x,y) for y in [rows//2-1,rows//2,rows//2+1] if cells[y][x]=='.']
            for count in [7,9]:
                wall.append({'preferredCells':first,'types':[1,1,1,4,4,7],'targetCount':count,'upgradeAfter':3,
                    'preferUpgrade':True,'cheapFallback':True,'midwaveUpgrades':True,'midwaveAfter':3})
        policies=wall+list(candidates(plan,L,52017+L,args.iterations));best=[]
        for i,policy in enumerate(policies):
            core.check_cancel(out);sim.POLICY=policy;r=sim.simulate_level(plan,L,'mixed',100,out/'scratch')
            best.append(copy.deepcopy(r));best.sort(key=score,reverse=True);best=best[:3]
        sim.POLICY={}
        for rank,result in enumerate(best,1):
            path=out/f'L{L:02}-candidate-{rank}'/'result.json';core.write_json(path,result);core.write_json(path.with_name('operations.json'),result['operations'])
            index.append({'profileId':args.profile,'levelId':L,'candidate':rank,'planHash':result['planHash'],'leaked':result['leaked'],
              'combatToParRatio':result['combatToParRatio'],'resultPath':str(path),'operationsPath':str(path.with_name('operations.json'))})
        core.write_json(out/'reference_index.json',index);core.progress('level_candidates',levelId=L,leaked=[r['leaked'] for r in best])


if __name__=='__main__':main()
