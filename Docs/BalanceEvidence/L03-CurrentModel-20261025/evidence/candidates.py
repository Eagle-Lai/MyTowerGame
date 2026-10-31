from search import *
import collections,random,math
sys.path.insert(0,str(ROOT/'.workbuddy/tools'))
from balance_campaign import runtime_path_for as path_for
plan=json.loads((OUT/'live-plan.json').read_text(encoding='utf-8'))
cells=next(x['cells'] for x in plan['tables']['tblevelmap'] if x['id']==3)
table={t['id']:t for t in plan['tables']['tbtowerinfo']}
enemytable={e['id']:e for e in plan['tables']['tbenemydata']}
old=json.loads((ROOT/'Docs/BalanceEvidence/L02-L30-ManualBalance-100Gold/L03/best-operations.json').read_text(encoding='utf-8'))
baseline=json.loads((OUT/'baseline/unity-results.json').read_text())[0]
for op in old:
    actual=next((a for a in baseline['operations'] if all(a[k]==op[k] for k in ['waveOrdinal','action','row','col','towerId'])),None)
    if actual:op['timeMs']=actual['timeMs']
def summarize():
    for p in OUT.glob('*/unity-results.json'):
        for i,r in enumerate(json.loads(p.read_text())):
            m=r.get('metrics',{});print(p.parent.name,i,r.get('state'),r.get('stars'),r.get('operationError'),{k:m.get(k) for k in ['completedWaveCount','successfulSpawned','killed','leaked','hp','combatElapsedMs']},'gold',r.get('finalGold'))
            print('LEAKS',dict(collections.Counter((e['waveOrdinal'],e['isFlying']) for e in r.get('enemyOutcomes',[]) if e['leaked'])))
def income_boundary(wave):
    raw=sum(sum(enemytable[eid]['reward'] for eid in w['enemyIds']) for w in plan['waves'][:wave-1])
    return 100+raw*4//5+sum(w['rewardGold'] for w in plan['waves'][:wave-1])
def cov(cell,path,r):return sum((cell[0]-p[0])**2+(cell[1]-p[1])**2<=r*r for p in path)
def enrich(seed,airweight,slowwave,extraStart=6):
    rng=random.Random(seed);built={};ops=[];spent=0;extraSpent=0
    seedWalls={(o['col'],o['row']) for o in old if o['action']=='build'}
    for wave in range(1,26):
        gold=income_boundary(wave)-spent
        for op in old:
            if op['waveOrdinal']!=wave:continue
            cell=(op['col'],op['row']);tid=op['towerId']
            if op['action']=='upgrade' and table[built.get(cell,tid)]['upgradeTo']!=tid:continue
            cost=table[tid]['prices']
            if gold<cost and wave>=6:raise ValueError(('seed insolvent',wave,gold,cost))
            if op['action']=='build' and cell in built:continue
            built[cell]=tid;gold-=cost;spent+=cost;ops.append({k:op[k] for k in ['waveOrdinal','timeMs','action','row','col','towerId']})
        if wave<extraStart:continue
        # Preserve the full original operation sequence's future liquidity.
        seedFutureMargins=[income_boundary(w)-sum(table[o['towerId']]['prices'] for o in old if o['waveOrdinal']<=w) for w in range(wave,26)]
        gold=min(gold,max(0,min(seedFutureMargins)-extraSpent))
        for _ in range(200):
            path=path_for(cells,built)
            options=[]
            for cell,tid in built.items():
                nxt=table[tid]['upgradeTo']
                if not nxt or table[nxt]['prices']>gold:continue
                t,n=table[tid],table[nxt]
                air=sum((cell[0]-8)**2+(cell[1]-y)**2<=n['radius']**2 for y in range(9))
                ground=cov(cell,path,n['radius'])
                if t['type']==3:score=(n['effectValue']-t['effectValue'])*air*airweight*200+ground*2
                else: score=(n['power']*1000/n['CD']-t['power']*1000/t['CD'])*(air*airweight+ground*(3 if t['type']==2 else .25))
                score/=n['prices'];score*=rng.uniform(.9,1.1)
                options.append((score,cell,nxt,'upgrade'))
            for y in range(9):
                for x in range(5,12):
                    cell=(x,y)
                    if cell in built or cells[y][x]!='.' or any((o['col'],o['row'])==cell for o in old if o['action']=='build'):continue
                    p=path_for(cells,list(built)+[cell])
                    if not p:continue
                    if not path_for(cells,set(built)|seedWalls|{cell}):continue
                    air=sum((x-8)**2+(y-yy)**2<=4 for yy in range(9))
                    ground=cov(cell,p,2)
                    tid=1
                    # two supplementary air slow zones, chosen across the lane
                    if wave>=slowwave and not any(table[t]['type']==3 and abs(c[1]-y)<2 and abs(c[0]-8)<2 for c,t in built.items()) and abs(x-8)<=1 and 1<=y<=7:tid=7
                    t=table[tid]
                    if t['prices']>gold:continue
                    score=(13.33*(air*airweight+ground*.25) if tid==1 else air*airweight*5+ground)/t['prices']
                    if tid==7:score*=2
                    score*=rng.uniform(.8,1.2)
                    options.append((score,cell,tid,'build'))
            if not options:break
            _,cell,tid,act=max(options)
            cost=table[tid]['prices'];gold-=cost;spent+=cost;extraSpent+=cost;built[cell]=tid
            ops.append({'waveOrdinal':wave,'timeMs':0,'action':act,'row':cell[1],'col':cell[0],'towerId':tid})
    return ops
if __name__=='__main__':
    if sys.argv[1]=='summary':summarize()
    elif sys.argv[1]=='enrich':
        paths=[]
        for i,aw in enumerate([2,5,10,20]):
            p=OUT/'candidates'/('enrich-v2-'+str(i)+'.json');dump(p,enrich(40+i,aw,7));paths.append(p)
        p=request('enrich-batch-v2',paths,True,step=.05);print(start(p))
