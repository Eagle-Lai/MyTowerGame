"""Reproducible candidate trials; mutations are restricted to explicit recipe acceptance."""
import argparse,copy,pathlib
import balance_pipeline as core
import balance_simulator as sim
from balance_campaign import capacity


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--level',type=int,default=1)
    parser.add_argument('--profile',default='D04');parser.add_argument('--out',required=True)
    args=parser.parse_args();original=core.read_json(core.DEFAULT_RECIPE);out=pathlib.Path(args.out)
    for index,ehp in enumerate([18,22,26]):
        recipe=copy.deepcopy(original);recipe['formula']['baseEhpPerUnit']=ehp
        recipe['formula'].update(waveLinear=.10,waveQuadratic=.010)
        for tower in recipe['towerValues']:
            if tower['id']<=3:
                tower['power']=[6,11,16][tower['id']-1];tower['CD']=[400,450,450][tower['id']-1]
            elif tower['id']<=6:
                tower['power']=[14,22,32][tower['id']-4]
        plan=core.generate(recipe,args.profile)
        for policy_index,policy in enumerate([{'upgradeShare':.25},{'upgradeShare':.45},{'upgradeShare':.2,'reservedPath':'minimum'}]):
            policy=copy.deepcopy(policy)
            if policy.get('reservedPath')=='minimum':
                level=next(l for l in plan['tables']['tbsceneinfo'] if l['id']==args.level)
                cells=next(m['cells'] for m in plan['tables']['tblevelmap'] if m['id']==level['mapId'])
                policy['reservedPath']=capacity(cells)['reservedPath']
            sim.POLICY=policy
            trial=out/f'ehp-{ehp}-policy-{policy_index}'
            result=sim.simulate_level(plan,args.level,'mixed',100,trial)
            core.write_json(trial/'recipe.json',recipe)
            core.progress('trial',ehp=ehp,policy=policy_index,victory=result['metrics']['victory'],
                completed=result['metrics']['completedWaveCount'],leaks=result['leaked'],
                ratio=result['combatToParRatio'],towers=result['waves'][-1]['towerCount'])
    sim.POLICY={}


if __name__=='__main__':main()
