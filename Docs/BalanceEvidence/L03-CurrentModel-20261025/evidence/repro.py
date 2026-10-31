from finalize import *
selected=json.loads((DOC/'selected-result.json').read_text());p=OUT/'strict-final/unity-results.json'
if not p.exists():raise SystemExit('Strict replay still running')
rs=json.loads(p.read_text());comparisons=[]
def clean(x):
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items() if k not in ['runId','spawnSerial','sourceIndex','requestedTimeMs','screenshot','screenshotTiming','repeatEffectEnemies','repeatEffectDefinition']}
    if isinstance(x,list):return [clean(i) for i in x]
    return x
def same(a,b,path=''):
    errors=[]
    if isinstance(a,dict) and isinstance(b,dict):
        if set(a)!=set(b):errors.append(path+':keys')
        for k in set(a)&set(b):errors+=same(a[k],b[k],path+'/'+k)
    elif isinstance(a,list) and isinstance(b,list):
        if len(a)!=len(b):errors.append(path+':length')
        for i,(aa,bb) in enumerate(zip(a,b)):errors+=same(aa,bb,path+'/'+str(i))
    elif isinstance(a,(int,float)) and isinstance(b,(int,float)):
        if abs(a-b)>.00001:errors.append(path)
    elif a!=b:errors.append(path)
    return errors
for i,r in enumerate(rs):
    fields=['metrics','operations','finalGold','initialGold','initialHp','finalPathCells','waveBoundaries','towerContributions','enemyOutcomes']
    differences=[]
    if i<2:
        for field in fields:differences+=same(clean(selected[field]),clean(r[field]),field)
    comparisons.append({'index':i,'runId':r['metrics']['runId'],'exactTimingReplay':i<2,'valid':r['valid'],'victory':r['metrics']['victory'],'hp':r['metrics']['hp'],'killed':r['metrics']['killed'],'leaked':r['metrics']['leaked'],'stars':r['stars'],'combatSeconds':r['metrics']['combatElapsedSeconds'],'operations':len(r['operations']),'equalToSelected':not differences if i<2 else None,'differences':differences[:30]})
dump(DOC/'reproducibility.json',{'selectedRunId':selected['metrics']['runId'],'stepSeconds':.02,'strictFunding':True,'description':'Exact scheduled operation affordability. Compare all wave metrics, outcomes, transactions, cash, routes and tower contributions, excluding run identity and observation metadata; tolerance 0.00001. Third run delays every midwave action by 500ms.','runs':comparisons})
dump(DOC/'three-strict-replays.json',rs)
print(json.dumps(comparisons,ensure_ascii=False,indent=2))
