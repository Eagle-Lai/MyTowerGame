"""One-time, audited migration; does not apply Excel or production JSON."""
import copy
from balance_pipeline import DEFAULT_RECIPE, DESIGN, read_json, write_json


def migrate():
    old = read_json(DEFAULT_RECIPE)
    if old.get('campaignLevelCount') == 30 and old.get('wavesPerLevel') == 25:
        raise SystemExit('30x25 recipe already exists; never overwrite calibration edits')
    history = DESIGN/'Versions'/old['balanceRevision']
    write_json(history/'balance_design.json',old)
    for name in ['variant_manifest.json','applied_state.json']:
        write_json(history/name,read_json(DESIGN/name))
    recipe = copy.deepcopy(old)
    recipe.update(schemaVersion=2,campaignLevelCount=30,wavesPerLevel=25,levelsPerTier=6,
        balanceRevision='balance-30x25-economy-v2',selectedProfileId='D04',
        overrides=[],calibrationEvidence=[],bulletValues=[{'id':2,'aoeRadius':.75}])
    recipe['formula'].update(countLevelCoefficient=1,countWaveCoefficient=2,countOffset=15,
        baseEhpPerUnit=32,levelEhpGrowth=.018,waveLinear=.13,waveQuadratic=.021,
        minBudgetGrowth=1.025,pressureMultiplier=1.10,finalMultiplier=1.18,
        spawnBaseMs=650,spawnWaveReductionMs=8,spawnLevelReductionMs=2,minSpawnMs=360,maxSpawnMs=650,
        speedLevelGrowth=.001,speedWaveGrowth=.001,initialGold=140,goldPerLevel=6,
        rewardBase=12,rewardBlockIncrement=3,tailBaseMs=18000,tailTierGrowthMs=1500)
    for profile in recipe['profiles']:
        profile['revision']='2'
    rewards=dict(normal=3,swarm=2,fast=3,air=4,medium=4,heavy=6,elite=10,boss=30)
    for role,reward in rewards.items():
        recipe['roles'][role]['reward']=reward
    for unlock in recipe['unlockSchedule']:
        if unlock['role']=='boss':unlock['wave']=25
    seed=[(5,500,2,25,0),(9,500,2,45,0),(14,500,2,70,0),
          (12,1000,2,40,0),(20,1000,2,65,0),(30,1000,2,95,0),
          (0,250,2,30,.15),(0,250,2,45,.22),(0,250,2,65,.28)]
    for tower,values in zip(recipe['towerValues'],seed):
        tower.update(dict(zip(['power','CD','radius','prices','effectValue'],values)))
    starts=[1,7,2,6,3,5,1,7,4,2];ends=[2,6,3,4,5,6,3,1,6,5]
    obstacles=[[(1,4),(8,4),(15,7),(2,8),(14,0)],[(2,2),(8,7),(14,2),(15,8)],
        [(3,7),(8,1),(14,7),(1,0)],[(1,3),(7,6),(15,7),(10,8),(0,0)],
        [(2,1),(9,1),(15,2),(2,8)],[(4,1),(7,7),(13,2),(15,8),(0,0)],
        [(2,7),(9,1),(14,7),(15,0)],[(2,4),(9,8),(15,4),(0,0)],
        [(1,7),(7,7),(14,2),(15,8)],[(2,6),(11,2),(15,8),(1,0)]]
    recipe['mapDefinitions']=[]
    for i in range(10):
        grid=[list('.'*17) for _ in range(9)]
        for x,y in obstacles[i]:grid[y][x]='#'
        grid[starts[i]][0]='S';grid[ends[i]][16]='E'
        recipe['mapDefinitions'].append({'id':i+21,'levelId':i+21,'cells':[''.join(row) for row in grid],
            'desc':f'L{i+21}: offset entrance/exit, sparse obstacles, open space for several firing zones'})
    write_json(DESIGN/'Versions'/'migration-30x25.json',{
        'from':old['balanceRevision'],'to':recipe['balanceRevision'],
        'removedOverrideCount':len(old.get('overrides',[])),
        'reason':'20-wave calibration is archived; regenerate from unscaled baseline and recalibrate all 25 waves',
        'retainedStableKeys':'levels 1-20; rounds/lists L1-20 W1-20; existing variant manifest; prototypes 1-132',
        'newIdAllocation':'persistent explicit manifest, monotonic globally unused IDs',
        'sourceHistory':str(history.relative_to(DESIGN)).replace('\\','/')})
    write_json(DEFAULT_RECIPE,recipe)
    print('Migrated recipe; numerical values are iteration seeds, not certified final balance')


if __name__=='__main__':migrate()
