"""Read-only W6 proposal, with W5 floors and explicit source/export activation status."""
from pathlib import Path
from decimal import Decimal,ROUND_HALF_UP
from collections import Counter
import hashlib,json,sys,math,struct

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/(sys.argv[1] if len(sys.argv)>1 else 'Library/BalanceStage/w6-algorithm-correction-20261109')
inputs=json.loads((OUT/'current-source-inputs.json').read_text(encoding='utf-8'))
snapshot=json.loads((OUT/'scope-before.json').read_text(encoding='utf-8'))
D=lambda x:Decimal(str(x))
def ids(value):return [int(i) for i in str(value).split(',') if i.strip()]
def index(t,name):return {r['id']:r for r in t[name]['records']}
def wave(t,n):
    r=index(t,'RoundData')[ids(t['SceneInfo']['records'][0]['RoundList'])[n-1]]
    groups=index(t,'EnemyList')
    sequence=[i for g in ids(r['EnemyIndexs']) for i in ids(groups[g]['EnemyIndexs'])]
    return r,sequence,Counter(sequence)
def budget(t,w):
    es=index(t,'EnemyData');total=D(t['SceneInfo']['records'][0]['initialGold'])
    for n in range(1,w):
        r,seq,_=wave(t,n)
        total+=D(r['rewardGold'])+sum((D(es[i]['reward']) for i in seq),D(0))
    return total
def hp6(v):return float(v.quantize(D('0.000001'),rounding=ROUND_HALF_UP))
def same_float(a,b):return struct.pack('f',a)==struct.pack('f',b)

l1,l2=inputs['L01'],inputs['L02'];e1,e2=index(l1,'EnemyData'),index(l2,'EnemyData')
r15,s15,c15=wave(l1,5);r16,s16,c16=wave(l1,6)
r25,s25,c25=wave(l2,5);r26,s26,c26=wave(l2,6)
assert r26['id']==2006 and ids(r26['EnemyIndexs'])==[2006]
approved_hp={6000040:220.625693,6000041:143.406707,6000042:405.951258,6000045:213.888300}
approved_count={6000040:236,6000041:126,6000042:84,6000045:12}
assert all(e2[i]['hp']==hp for i,hp in approved_hp.items()) and dict(c25)==approved_count

export_e={r['id']:r for r in snapshot['exports']['tbenemydata.json']['rows']}
export_g={r['id']:r for r in snapshot['exports']['tbenemylist.json']['rows']}
for i in set(s25+s26):
    for key in ('hp','speed','armor','reward'):assert same_float(e2[i][key],export_e[i][key]),(i,key)
assert export_g[2005]['EnemyIndexs']==s25 and export_g[2006]['EnemyIndexs']==s26
normal3=next(r for r in l2['TowerInfo']['records'] if r['type']==1 and r['level']==3)
strong3=next(r for r in l2['TowerInfo']['records'] if r['type']==2 and r['level']==3)
assert normal3['power']==13 and normal3['airDamageScale']==1.1 and strong3['power']==33
def tower_cost(family,level):
    return sum(r['prices'] for r in l2['TowerInfo']['records'] if r['type']==family and 1<=r['level']<=level)
rows=[];targets={};edits=[]
for i in c16:
    trusted=e1[i]
    def matching(es,counts):
        found=[es[j] for j in counts if es[j]['resName']==trusted['resName'] and es[j]['isFlying']==trusted['isFlying']]
        assert len(found)==1
        return found[0]
    a1,a2,current=matching(e1,c15),matching(e2,c25),matching(e2,c26)
    assert a2['armor']==current['armor']==trusted['armor'],'Different armor requires a separately reviewed EHP floor'
    raw_hp=D(a2['hp'])*D(trusted['hp'])/D(a1['hp'])
    # Monotonic HP/count is a design constraint for this request, not a difficulty theorem.
    new_hp=hp6(max(D(a2['hp']),raw_hp))
    raw_count=int((D(c25[a2['id']])*D(c16[i])/D(c15[a1['id']])).quantize(D(1),rounding=ROUND_HALF_UP))
    new_count=max(c25[a2['id']],raw_count)
    assert new_hp>=a2['hp'] and new_count>=c25[a2['id']]
    damage=D('14.3')*(1-D(current['armor'])) if current['isFlying']!=0 else D(33)*(1-D(current['armor']))
    k5=math.ceil(D(a2['hp'])/damage);k_current=math.ceil(D(current['hp'])/damage);k6=math.ceil(D(new_hp)/damage)
    assert k6>=k5
    targets[current['id']]={'newCount':new_count,'oldCount':c26[current['id']],'seen':0}
    edits.append({'table':'EnemyData','id':current['id'],'field':'hp','old':current['hp'],'value':new_hp})
    rows.append({'id':current['id'],'name':current['name'],'isFlying':current['isFlying'],
        'acceptedW5Hp':a2['hp'],'currentW6SourceHp':current['hp'],'currentW6ExportHp':export_e[current['id']]['hp'],
        'currentW6HpRatioVsW5':float(D(current['hp'])/D(a2['hp'])),
        'L01GrowthHp':hp6(raw_hp),'correctedCandidateHp':new_hp,'W5FloorApplied':raw_hp<D(a2['hp']),
        'acceptedW5Count':c25[a2['id']],'currentW6Count':c26[current['id']],'candidateW6Count':new_count,
        'referenceDamagePerHit':float(damage),'W5ReferenceHits':k5,'currentW6ReferenceHits':k_current,'candidateW6ReferenceHits':k6,
        'speedHeld':current['speed'],'armorHeld':current['armor'],'perKillRewardHeld':current['reward']})

proposed=[]
for i in s26:
    t=targets[i];before=t['seen']*t['newCount']//t['oldCount'];t['seen']+=1
    after=t['seen']*t['newCount']//t['oldCount'];assert after-before>=1
    proposed.extend([i]*(after-before))
assert all(proposed.count(i)==t['newCount'] for i,t in targets.items())
assert [i for i in s26 if e2[i]['isFlying']!=0]==[i for i in proposed if e2[i]['isFlying']!=0]
full=[]
for n in range(1,26):
    _,seq,_=wave(l2,n)
    if n!=6:assert not(set(c26)&set(seq)),f'W6 IDs referenced by W{n}'
    full.extend(proposed if n==6 else seq)
assert not any(e2[a]['isFlying']!=0 and e2[b]['isFlying']!=0 for a,b in zip(full,full[1:]))
edits.append({'table':'EnemyList','id':2006,'field':'EnemyIndexs','old':s26,'value':proposed})

gap5=D(index(l2,'EnemyList')[2005]['enemyInterval'])/1000
gap6=D(index(l2,'EnemyList')[2006]['enemyInterval'])/1000
def air_reference_metrics(seq,gap,hit_by_id):
    items=[(float(D(j)*gap),hit_by_id[i]) for j,i in enumerate(seq) if e2[i]['isFlying']!=0]
    span=float(D(len(seq)-1)*gap)
    peak={}
    for seconds in (5,10,20):
        maximum=0
        for start,_ in items:maximum=max(maximum,sum(h for at,h in items if start<=at<start+seconds))
        peak[str(seconds)]={'maxReferenceHitsForAirBornInWindow':maximum,'referenceHitsPerSecond':maximum/seconds}
    return {'spawnSpanSeconds':span,'totalReferenceHits':sum(h for _,h in items),
            'meanReferenceHitsPerSpawnSecond':sum(h for _,h in items)/span,'windowsSeconds':peak}
h5={i:math.ceil(D(e2[i]['hp'])/D('14.3')) for i in c25 if e2[i]['isFlying']!=0}
h6={r['id']:r['candidateW6ReferenceHits'] for r in rows if r['isFlying']!=0}
air5=air_reference_metrics(s25,gap5,h5);air6=air_reference_metrics(proposed,gap6,h6)
assert air6['meanReferenceHitsPerSpawnSecond']>=air5['meanReferenceHitsPerSpawnSecond']

kill=lambda seq:sum((D(e2[i]['reward']) for i in seq),D(0))
b25,b26=budget(l2,5),budget(l2,6)
old_w5=json.loads((ROOT/'Artifacts/L02_W5_Ground_20261109_cell_changes.json').read_text(encoding='utf-8'))
old_seq=next(e['old'] for e in old_w5['edits'] if e['table']=='EnemyList' and e['id']==2005)
additional_w5=kill(s25)-kill(old_seq)
source_active=all(e2[e['id']]['hp']==e['value'] for e in edits if e['table']=='EnemyData') and s26==proposed
export_active=all(same_float(export_e[e['id']]['hp'],e['value']) for e in edits if e['table']=='EnemyData') and export_g[2006]['EnemyIndexs']==proposed
report={'algorithmRevision':'W6-v2: W5 floors, no gold-to-HP multiplier, activation gate, per-target hit and air arrival workload diagnostics',
    'calculationOnly':True,'sourceWorkbooksWritten':0,'candidateStatus':'ACTIVE' if source_active and export_active else 'NOT_APPLIED',
    'candidateInSource':source_active,'candidateInExport':export_active,'unityInMemoryChecked':False,
    'doNotAttributeCurrentPlaytestToUnappliedCandidate':True,'rows':rows,
    'designRule':'For this requested W6 continuation, carry trusted L01 growth but floor each HP and count at approved W5. These are non-regression constraints, not proof of equal terminal pressure.',
    'economy':{'W5EntryCumulativeReceivedGold':float(b25),'W6EntryCumulativeReceivedGold':float(b26),
        'W5TotalIncome':float(b26-b25),'recentW5AdditionalKillGold':float(additional_w5),
        'additionalW5GoldAlreadyIncluded':True,'goldToHpMultiplierApplied':False,
        'conversionStatus':'Effective firepower increase is unknown without a purchasable tower-state/path/coverage calculation; do not invent a percentage from gold ratios.',
        'conditionalPurchaseExamples':[{'bundle':'One new level-3 strong tower and one new level-3 normal tower','cost':tower_cost(2,3)+tower_cost(1,3),'conditions':'Requires available permitted cells and effective coverage; does not identify the actual optimal build.'},
            {'bundle':'Two new level-3 normal towers and one level-1 slow tower','cost':2*tower_cost(1,3)+tower_cost(3,1),'conditions':'Requires available permitted cells and non-redundant slowing/coverage; not a measured damage increment.'}],
        'W6RoundRewardHeld':r26['rewardGold'],'currentW6KillGold':float(kill(s26)),'candidateW6KillGold':float(kill(proposed)),
        'candidateW6AdditionalKillGold':float(kill(proposed)-kill(s26))},
    'spawn':{'W5Ground':sum(n for i,n in c25.items() if e2[i]['isFlying']==0),
        'currentW6Ground':sum(n for i,n in c26.items() if e2[i]['isFlying']==0),
        'candidateW6Ground':sum(n for i,n in Counter(proposed).items() if e2[i]['isFlying']==0),
        'W5Total':len(s25),'currentW6Total':len(s26),'candidateW6Total':len(proposed),
        'enemyIntervalMsHeld':float(gap6*1000),'airOrderAndCountPreserved':True,'crossWaveAirAdjacencyPassed':True},
    'airSingleTargetWorkloadDiagnostics':{'W5':air5,'candidateW6':air6,
        'meaning':'Reference projectile demand from births at fixed 14.3 damage per hit. This excludes coverage, retargeting, shared ground fire, and cannot predict actual leaks.'},
    'limitations':['No combat simulation or editor playtest performed.',
        'Ground AOE is checked per target; monster count times HP is not treated as linear AOE difficulty.',
        'Tower upgrades, path changes, overlap and gold spending can still change actual terminal pressure.',
        'The previously optional 1.028741 gold multiplier is removed; old W6 proposal is superseded.'],
    'heldFields':['speed','armor','enemyInterval','per-kill reward','round reward']}
source_hashes={name:snapshot['sources'][f'Luban/Config/Datas/Levels/L02/{name}.xlsx'] for name in ('EnemyData','EnemyList')}
for name,obj in [('calculation.json',report),('candidate-corrected-manifest.json',{'sourceHashes':source_hashes,'edits':edits})]:
    target=OUT/name;assert not target.exists(),'Preserve existing output'
    target.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in snapshot['sources'].items())
assert all(hashlib.sha256((ROOT/'Assets/ConfigJson'/p).read_bytes()).hexdigest()==v['sha256'] for p,v in snapshot['exports'].items())
print(json.dumps(report,ensure_ascii=False,indent=2))
