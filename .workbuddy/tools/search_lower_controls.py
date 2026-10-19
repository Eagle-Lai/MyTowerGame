"""Find affordable legal lower-star control trajectories without changing rating rules."""
import pathlib,copy
import balance_pipeline as core
import balance_simulator as sim

def main():
    root=core.ROOT/'Luban/BalanceDesign/Evidence30x25';plan=core.generate(core.read_json(core.DEFAULT_RECIPE),'D04');index=[]
    rated=core.read_json(root/'Simulation/rated-matrix.json')['results']
    for L in range(1,31):
        existing=[]
        for row in rated:
            if row['profileId']!='D04' or row['levelId']!=L or not row['valid'] or not 0<row['stars']<5:continue
            path=pathlib.Path(row['path']);r=core.read_json(path)
            if r['metrics']['victory']:existing.append((row['stars'],path))
        if existing:
            stars,path=min(existing);index.append({'levelId':L,'source':str(path),'predictionStars':stars,'coverage':'C# rated offline legal clear control'});continue
        trials=[];selected=None
        for count in [3,4,5,6,8,10,12,14,16,20,24,30]:
            policy={'maxTowers':count,'targetCount':count,'upgradeAfter':min(count,4),'preferUpgrade':True,'cheapFallback':True,'midwaveUpgrades':True,'types':[1,1,4,7]}
            sim.POLICY=copy.deepcopy(policy)
            r=sim.simulate_level(plan,L,'mixed',100,root/'Controls'/f'L{L:02}'/str(count))
            path=root/'Controls'/f'L{L:02}'/str(count)/f'L{L:02}-mixed/result.json'
            trials.append({'maxTowers':count,'victory':r['metrics']['victory'],'leaked':r['leaked'],'combatToPar':r['combatToParRatio'],'path':str(path)})
            if r['metrics']['victory'] and (r['leaked']>0 or r['combatToParRatio']>1):selected=path;break
        core.write_json(root/'Controls'/f'L{L:02}'/'search.json',{'trials':trials,'finiteSearch':True})
        index.append({'levelId':L,'source':str(selected) if selected else None,'coverage':'offline legal lower-star candidate; sole C# evaluator pending'})
    core.write_json(root/'Controls'/'lower-index.json',index);print('controls',len(index),'missing',[r['levelId'] for r in index if not r['source']])
if __name__=='__main__':main()
