from search import *
tables={p.stem:json.loads(p.read_text(encoding='utf-8-sig')) for p in (ROOT/'Assets/ConfigJson').glob('*.json')}
scene=next(s for s in tables['tbsceneinfo'] if s['id']==3)
rounds={r['id']:r for r in tables['tbrounddata']};lists={r['id']:r for r in tables['tbenemylist']};enemies={r['id']:r for r in tables['tbenemydata']}
print('SCENE',scene)
print('MAP',next(m for m in tables['tblevelmap'] if m['id']==scene['mapId']))
waves=[]
for w,rid in enumerate(scene['RoundList'],1):
    r=rounds[rid];ls=[lists[l] for l in r['EnemyIndexs']];ids=sum([l['EnemyIndexs'] for l in ls],[])
    role=lambda e:'air' if e['isFlying'] else 'boss' if e['type']==5 else 'ground'
    comps=[{'variantId':eid,'role':role(enemies[eid])} for eid in set(ids)]
    row={'levelId':3,'waveOrdinal':w,'enemyIds':ids,'count':len(ids),'spawnIntervalMs':ls[0]['enemyInterval'],'rewardGold':r['rewardGold'],'actualEhp':sum(enemies[e]['hp']/(1-enemies[e]['armor']) for e in ids),'composition':comps,'flyingCount':sum(enemies[e]['isFlying'] for e in ids),'heavyCount':0,'eliteCount':0,'bossCount':0}
    waves.append(row)
    print(w,len(ids),'air',row['flyingCount'],'gap',row['spawnIntervalMs'],'gold',sum(enemies[e]['reward'] for e in ids)*.8,r['rewardGold'],'variants',[(e,enemies[e]['hp'],enemies[e]['speed'],enemies[e]['armor'],enemies[e]['reward']) for e in sorted(set(ids))])
dump(OUT/'live-plan.json',{'tables':tables,'waves':waves,'profileId':'D04'})
for p in OUT.glob('*/unity-results.json'):
    for i,r in enumerate(json.loads(p.read_text())):
        print('RESULT',p.parent.name,i,{k:r.get(k) for k in ['state','stars','victory','leaked','hp','combatElapsedMs','finalGold','operationError']})
        print('KEYS',list(r))
        if 'metrics' in r: print('METRICS',r['metrics'])
