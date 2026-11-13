"""Prepare authorized W5 HP/count promotion and subsequent W6 growth, without writing sources."""
from pathlib import Path
from decimal import Decimal,ROUND_HALF_UP
from collections import Counter
import hashlib,json,sys,math,struct

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/sys.argv[1]
data=json.loads((OUT/'current-source-inputs.json').read_text(encoding='utf-8'))
before=json.loads((OUT/'scope-before.json').read_text(encoding='utf-8'))
D=lambda v:Decimal(str(v))
def ids(v):return [int(x) for x in str(v).split(',') if x.strip()]
def index(t,name):return {r['id']:r for r in t[name]['records']}
def wave(t,n):
    rid=ids(t['SceneInfo']['records'][0]['RoundList'])[n-1]
    r=index(t,'RoundData')[rid];groups=index(t,'EnemyList')
    seq=[i for g in ids(r['EnemyIndexs']) for i in ids(groups[g]['EnemyIndexs'])]
    return r,seq,Counter(seq)
def round_hp(v):return float(v.quantize(D('0.000001'),rounding=ROUND_HALF_UP))
def float_same(a,b):return struct.pack('f',a)==struct.pack('f',b)
def key(e):return e['resName'],e['isFlying']!=0

l1,l2=data['L01'],data['L02'];e1,e2=index(l1,'EnemyData'),index(l2,'EnemyData')
r15,s15,c15=wave(l1,5);r16,s16,c16=wave(l1,6)
r25,s25,c25=wave(l2,5);r26,s26,c26=wave(l2,6)
assert r25['id']==2005 and r26['id']==2006
assert ids(r25['EnemyIndexs'])==[2005] and ids(r26['EnemyIndexs'])==[2006]
expected6={6000050:(245.928559,252),6000051:(159.853552,144),6000052:(452.508546,92),6000055:(213.8883,18)}
assert all(e2[i]['hp']==h and c26[i]==n for i,(h,n) in expected6.items())
export_e={e['id']:e for e in before['exports']['tbenemydata.json']['rows']}
export_g={e['id']:e for e in before['exports']['tbenemylist.json']['rows']}
for i in set(s25+s26):
    for field in ('hp','speed','armor','reward'):assert float_same(e2[i][field],export_e[i][field]),(i,field)
assert export_g[2005]['EnemyIndexs']==s25 and export_g[2006]['EnemyIndexs']==s26
maps=[{key(es[i]):i for i in cc} for es,cc in ((e1,c15),(e1,c16),(e2,c25),(e2,c26))]
assert all(len(m)==4 for m in maps) and all(set(m)==set(maps[0]) for m in maps)
edits=[];rows=[];target5={};target6={};hp_after={}
for k,i5 in maps[2].items():
    i6=maps[3][k];a1=e1[maps[0][k]];b1=e1[maps[1][k]]
    assert e2[i5]['armor']==e2[i6]['armor']==a1['armor']==b1['armor']
    hp5=e2[i6]['hp'];n5=c26[i6]
    hp6=round_hp(max(D(hp5),D(hp5)*D(b1['hp'])/D(a1['hp'])))
    n6=max(n5,int((D(n5)*D(c16[b1['id']])/D(c15[a1['id']])).quantize(D(1),rounding=ROUND_HALF_UP)))
    assert hp6>=hp5 and n6>n5
    for i,old,new in ((i5,e2[i5]['hp'],hp5),(i6,e2[i6]['hp'],hp6)):
        hp_after[i]=new
        if old!=new:edits.append({'table':'EnemyData','id':i,'field':'hp','old':old,'value':new})
    target5[i5]=n5;target6[i6]=n6
    damage=D('14.3')*(1-D(e2[i6]['armor'])) if k[1] else D(33)*(1-D(e2[i6]['armor']))
    rows.append({'name':e2[i5]['name'],'W5Id':i5,'W6Id':i6,'isFlying':e2[i5]['isFlying'],
        'oldW5Hp':e2[i5]['hp'],'oldW5Count':c25[i5],'oldW6Hp':e2[i6]['hp'],'oldW6Count':c26[i6],
        'newW5Hp':hp5,'newW5Count':n5,'newW6Hp':hp6,'newW6Count':n6,
        'trustedL01HpGrowth':float(D(b1['hp'])/D(a1['hp'])),
        'airHpHeldAtPromotedW5Floor':k[1] and hp6==hp5,
        'referenceDamagePerHit':float(damage),'newW5ReferenceHits':math.ceil(D(hp5)/damage),'newW6ReferenceHits':math.ceil(D(hp6)/damage)})

def subsequence(old,new):
    it=iter(new)
    return all(any(x==wanted for x in it) for wanted in old)
def extend_sequence(old,target):
    counts=Counter(old);seen=Counter();seq=[]
    # Spread extra ground copies through existing occurrences, preserving all old entries.
    for i in old:
        if e2[i]['isFlying']!=0:seq.append(i);continue
        a=seen[i]*target[i]//counts[i];seen[i]+=1;b=seen[i]*target[i]//counts[i]
        assert b-a>=1
        seq.extend([i]*(b-a))
    flying=[i for i in counts if e2[i]['isFlying']!=0]
    assert len(flying)==1,'Different air types require explicit distribution review'
    air_id=flying[0];extra=target[air_id]-counts[air_id];assert extra>=0
    # Insert new air only between ground entries. Choose largest remaining gaps to avoid new clumps.
    candidates=[j for j in range(len(seq)-1) if e2[seq[j]]['isFlying']==0 and e2[seq[j+1]]['isFlying']==0]
    air_positions=[float(j) for j,i in enumerate(seq) if e2[i]['isFlying']!=0]
    selected=set()
    for _ in range(extra):
        j=max((j for j in candidates if j not in selected),key=lambda j:(min(abs(j+0.5-p) for p in air_positions),-j))
        selected.add(j);air_positions.append(j+0.5)
    result=[]
    for j,i in enumerate(seq):
        result.append(i)
        if j in selected:result.append(air_id)
    assert Counter(result)==Counter(target) and subsequence(old,result)
    assert not any(e2[a]['isFlying']!=0 and e2[b]['isFlying']!=0 for a,b in zip(result,result[1:]))
    return result

new5=extend_sequence(s25,target5);new6=extend_sequence(s26,target6)
for group,old,new in ((2005,s25,new5),(2006,s26,new6)):
    assert old!=new
    edits.append({'table':'EnemyList','id':group,'field':'EnemyIndexs','old':old,'value':new})
full=[]
for n in range(1,26):
    _,seq,_=wave(l2,n)
    if n not in (5,6):assert not(set(seq)&set(s25+s26)),f'Target enemy ID shared with W{n}'
    full.extend(new5 if n==5 else new6 if n==6 else seq)
assert not any(e2[a]['isFlying']!=0 and e2[b]['isFlying']!=0 for a,b in zip(full,full[1:]))

def kill(seq):return sum((D(e2[i]['reward']) for i in seq),D(0))
def budget(w,new=False):
    total=D(l2['SceneInfo']['records'][0]['initialGold'])
    for n in range(1,w):
        r,seq,_=wave(l2,n)
        if new:seq=new5 if n==5 else new6 if n==6 else seq
        total+=D(r['rewardGold'])+kill(seq)
    return total
g=index(l2,'EnemyList')
def air_metric(seq,group):
    span=D(len(seq)-1)*D(g[group]['enemyInterval'])/1000
    demand=sum((D(math.ceil(D(hp_after[i])/(D('14.3')*(1-D(e2[i]['armor']))))) for i in seq if e2[i]['isFlying']!=0),D(0))
    return {'spawnSpanSeconds':float(span),'referenceNormal3Hits':int(demand),'meanReferenceHitsPerSecond':float(demand/span)}
report={'operation':'Copy current W6 HP/counts by enemy type into W5, then grow W6 from promoted W5',
    'sourceWritesDuringCalculation':0,'rows':rows,'changedCells':len(edits),
    'method':{'W5':'HP and per-type counts exactly equal pre-change W6; IDs and other fields stay in their own wave.',
        'W6Hp':'max(new W5 HP, new W5 HP * trusted L01 W6 HP / trusted L01 W5 HP)',
        'W6Count':'max(new W5 count, round(new W5 count * trusted L01 W6 count / trusted L01 W5 count))',
        'economy':'Recalculate actual income changes; do not multiply HP by a gold ratio or claim economy-to-effective-DPS equivalence.'},
    'waves':[{'wave':w,'roundId':rid,'oldGround':sum(1 for i in old if e2[i]['isFlying']==0),'newGround':sum(1 for i in new if e2[i]['isFlying']==0),
        'oldAir':sum(1 for i in old if e2[i]['isFlying']!=0),'newAir':sum(1 for i in new if e2[i]['isFlying']!=0),
        'oldTotal':len(old),'newTotal':len(new),'enemyIntervalMsHeld':g[rid]['enemyInterval'],
        'oldKillGold':float(kill(old)),'newKillGold':float(kill(new)),'extraKillGold':float(kill(new)-kill(old)),
        'roundRewardHeld':r['rewardGold'],'newTotalWaveIncome':float(kill(new)+D(r['rewardGold'])),
        'oldSpawnEntriesPreservedInOrder':subsequence(old,new)} for w,rid,r,old,new in ((5,2005,r25,s25,new5),(6,2006,r26,s26,new6))],
    'economy':{'W6EntryBefore':float(budget(6)),'W6EntryAfter':float(budget(6,True)),
        'W7EntryBefore':float(budget(7)),'W7EntryAfter':float(budget(7,True)),
        'fullLevelBefore':float(budget(26)),'fullLevelAfter':float(budget(26,True)),
        'totalExtraGold':float(kill(new5)+kill(new6)-kill(s25)-kill(s26)),
        'definition':'Full-clear cumulative received gold including initial 100, not unspent wallet balance.'},
    'airReferenceWorkload':{'newW5':air_metric(new5,2005),'newW6':air_metric(new6,2006),
        'meaning':'Reference projectile demand only, not actual terminal pressure or a combat simulation.'},
    'crossWaveAirAdjacencyPassed':True,'otherWavesChanged':False,'battleSimulationPerformed':False,
    'heldFields':['speed','armor','enemyInterval','per-kill reward','round reward','initialGold'],
    'limitations':['Preserving W5/W6 timings means this copies HP/counts, not every timing/speed aspect of old W6.',
        'New W6 air strengthens through quantity 18 to 27; its individual HP is held at the promoted W5 floor.',
        'Tower spending, AOE/slow coverage and actual terminal pressure are not solved or independently validated.']}
manifest={'sourceHashes':{t:before['sources'][f'Luban/Config/Datas/Levels/L02/{t}.xlsx'] for t in ('EnemyData','EnemyList')},'edits':edits}
assert len(edits)==8
for name,obj in (('manifest.json',manifest),('calculation.json',report)):
    target=OUT/name;assert not target.exists(),'Preserve earlier calculation'
    target.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in before['sources'].items())
print(json.dumps(report,ensure_ascii=False,indent=2))
