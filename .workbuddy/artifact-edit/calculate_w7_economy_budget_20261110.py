"""Read-only, layout-independent economy/throughput proposal for L02 W7.

All efficiency and AOE multiplicity cases are design sensitivities, not playtest
measurements. Source XLSX and exported JSON are never authored by this script.
"""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from collections import Counter
import hashlib, json, math, struct, statistics

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'Library/BalanceStage/w7-from-approved-w6-20261110'
OUT=ROOT/'Library/BalanceStage/w7-economy-budget-20261110/reference-calibrated'
OUT.mkdir(parents=True,exist_ok=True)
data=json.loads((BASE/'current-source-inputs.json').read_text(encoding='utf-8'))
baseline=json.loads((BASE/'scope-before.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in baseline['sources'].items())
assert all(hashlib.sha256((ROOT/'Assets/ConfigJson'/p).read_bytes()).hexdigest()==r['sha256'] for p,r in baseline['exports'].items())
for target in ('manifest.json','calculation.json'):
    assert not (OUT/target).exists(),'Preserve earlier proposals'
D=lambda x:Decimal(str(x))
round_hp=lambda x:float(x.quantize(D('.000001'),rounding=ROUND_HALF_UP))
round_count=lambda x:int(x.quantize(D(1),rounding=ROUND_HALF_UP))
def index(l,t):return {r['id']:r for r in data[f'L{l:02}'][t]}
def ids(v):return [int(x) for x in str(v).split(',')]
def wave(l,n):
    r=index(l,'RoundData')[ids(data[f'L{l:02}']['SceneInfo'][0]['RoundList'])[n-1]]
    gs=index(l,'EnemyList');seq=[i for g in ids(r['EnemyIndexs']) for i in ids(gs[g]['EnemyIndexs'])]
    return r,seq,Counter(seq)
e1,e2=index(1,'EnemyData'),index(2,'EnemyData')
r16,s16,c16=wave(1,6);r17,s17,c17=wave(1,7);r26,s26,c26=wave(2,6);r27,s27,c27=wave(2,7)
assert r27['id']==2007 and ids(r27['EnemyIndexs'])==[2007]
assert r26['rewardGold']==74
approved={6000050:(361.855997,269),6000051:(235.206353,165),6000052:(665.815055,101),6000055:(294.096413,27)}
assert all(e2[i]['hp']==h and c26[i]==n for i,(h,n) in approved.items())
key=lambda e:(e['resName'],e['isFlying']!=0)
maps=[{key(es[i]):i for i in cc} for es,cc in ((e1,c16),(e1,c17),(e2,c26),(e2,c27))]
assert all(set(m)==set(maps[0]) for m in maps)
tw={(t['type'],t['level']):t for t in data['L01']['TowerInfo']}
bullets=index(1,'BulletData')
for t in data['L02']['TowerInfo']:
    for field in ('power','CD','prices','radius','effectValue','canAttackAir','airDamageScale'):
        assert t[field]==tw[t['type'],t['level']][field]
    if t['type']==2:
        assert index(2,'BulletData')[t['bulletId']]['aoeRadius']==bullets[tw[t['type'],t['level']]['bulletId']]['aoeRadius']
def dps(t):return t['power']/(t['CD']/1000)
actions=[]
for (typ,lv),t in tw.items():
    if typ==3:continue
    prev=tw.get((typ,lv-1));p0=dps(prev) if prev else 0
    actions.append({'type':typ,'level':lv,'price':t['prices'],'DPS':dps(t),
                    'deltaGroundPerTargetDPS':dps(t)-p0,
                    'deltaAirDPS':dps(t)*t['airDamageScale']-(p0*prev['airDamageScale'] if prev else 0) if t['canAttackAir'] else 0,
                    'aoeRadius':bullets[t['bulletId']]['aoeRadius'],
                    'requiresPriorLevel':lv-1 if prev else 0})
proposed_hp={};proposed_counts={};rows=[];mapping={}
for k,i7 in maps[3].items():
    i6=maps[2][k];a6=maps[0][k];a7=maps[1][k];mapping[a7]=i7
    assert e2[i7]['armor']==e2[i6]['armor']==e1[a7]['armor']==e1[a6]['armor']
    hp=round_hp(D(e2[i6]['hp'])*D(e1[a7]['hp'])/D(e1[a6]['hp']))
    n=round_count(D(c26[i6])*D(c17[a7])/D(c16[a6]))
    proposed_hp[i7]=hp;proposed_counts[i7]=n
    rows.append({'id':i7,'name':e2[i7]['name'],'isFlying':e2[i7]['isFlying'],'acceptedW6Hp':e2[i6]['hp'],
                 'acceptedW6Count':c26[i6],'oldW7Hp':e2[i7]['hp'],'oldW7Count':c27[i7],
                 'newHp':hp,'structureReferenceCount':n,'trustedL01HpRatio':float(D(e1[a7]['hp'])/D(e1[a6]['hp']))})
air_ids=[i for i in proposed_counts if e2[i]['isFlying']!=0]
assert len(air_ids)==1
air_id=air_ids[0];ground_count=sum(n for i,n in proposed_counts.items() if e2[i]['isFlying']==0)
interval=index(2,'EnemyList')[2007]['enemyInterval']/1000
span6=(len(s26)-1)*index(2,'EnemyList')[2006]['enemyInterval']/1000
air_load6=sum(e2[i]['hp']/(1-e2[i]['armor']) for i in s26 if e2[i]['isFlying']!=0)/span6
air_increment=lambda n:n*proposed_hp[air_id]/(1-e2[air_id]['armor'])/((ground_count+n-1)*interval)-air_load6
mixed_cost=tw[1,1]['prices']+tw[2,2]['prices']
assert mixed_cost<=74
# Planning sensitivity band, explicitly NOT a measured utilization distribution.
utilizations=(.65,.75,.85)
air_limits=[]
for eta in utilizations:
    limit=max(n for n in range(c26[maps[2][key(e2[air_id])]],proposed_counts[air_id]+1) if air_increment(n)<=eta*dps(tw[1,1]))
    air_limits.append({'assumedUtilization':eta,'maxAirCount':limit,'availableIncrementAirDPS':eta*dps(tw[1,1])})
def source_workload(es,sequence,span):
    ground=[i for i in sequence if es[i]['isFlying']==0]
    return {'ground':sum(es[i]['hp']/(1-es[i]['armor']) for i in ground)/span,
            'air':sum(es[i]['hp']/(1-es[i]['armor']) for i in sequence if es[i]['isFlying']!=0)/span,
            'groundRate':len(ground)/span,
            'groundHarmonicSpeed':len(ground)/sum(1/es[i]['speed'] for i in ground)}
span16=(len(s16)-1)*index(1,'EnemyList')[6]['enemyInterval']/1000
span17=(len(s17)-1)*index(1,'EnemyList')[7]['enemyInterval']/1000
reference6=source_workload(e1,s16,span16);reference7=source_workload(e1,s17,span17)
anchor6=source_workload(e2,s26,span6)
reference_gold=r16['rewardGold'];assert reference_gold==43
air_per_gold=(reference7['air']-reference6['air'])/reference_gold
assert air_per_gold>0
air_increment_budget=74*air_per_gold
new_air_count=max(n for n in range(c26[maps[2][key(e2[air_id])]],proposed_counts[air_id]+1)
                  if air_increment(n)<=air_increment_budget)
proposed_counts[air_id]=new_air_count
candidate_span=(sum(proposed_counts.values())-1)*interval
candidate_rate=ground_count/candidate_span
candidate_speed=ground_count/sum(n/e2[i]['speed'] for i,n in proposed_counts.items() if e2[i]['isFlying']==0)
seed_ground_load=sum(n*proposed_hp[i]/(1-e2[i]['armor']) for i,n in proposed_counts.items() if e2[i]['isFlying']==0)/candidate_span
ground_cases=[]
def multiplicity(rate,speed,radius,density_fraction,dwell_multiplier):
    return 1+density_fraction*2*radius*rate/speed*dwell_multiplier
for radius in (.75,.90,1.05):
    for density_fraction in (.5,1.):
        for dwell_multiplier in (1.,1.4,2.):
            for normal_ground_share in (0.,.25,.5):
                def unit_cost(rate,speed):
                    mult=multiplicity(rate,speed,radius,density_fraction,dwell_multiplier)
                    return normal_ground_share+(1-normal_ground_share)/mult
                f16=unit_cost(reference6['groundRate'],reference6['groundHarmonicSpeed'])
                f17=unit_cost(reference7['groundRate'],reference7['groundHarmonicSpeed'])
                f26=unit_cost(anchor6['groundRate'],anchor6['groundHarmonicSpeed'])
                f27=unit_cost(candidate_rate,candidate_speed)
                per_gold=(reference7['ground']*f17-reference6['ground']*f16)/reference_gold
                target_load=(anchor6['ground']*f26+74*per_gold)/f27
                ground_cases.append({'radius':radius,'forwardDensityFraction':density_fraction,'dwellMultiplier':dwell_multiplier,
                                     'normalShareOfGroundDamage':normal_ground_share,'referenceGroundBurdenPerGold':per_gold,
                                     'targetGroundEHPPerSecond':target_load,'seedHpScale':target_load/seed_ground_load})
ground_scale=statistics.median(case['seedHpScale'] for case in ground_cases)
for i in proposed_hp:
    if e2[i]['isFlying']==0:proposed_hp[i]=round_hp(D(proposed_hp[i])*D(ground_scale))
for row in rows:
    row['newCount']=proposed_counts[row['id']]
    row['structureReferenceHp']=row['newHp']
    row['newHp']=proposed_hp[row['id']]
    assert row['newHp']>=row['acceptedW6Hp'] and row['newCount']>=row['acceptedW6Count']
# L01 W7 is the sequence skeleton. Increase ground occurrences proportionally,
# retain its original air occurrences, then insert remaining air into ground gaps.
mapped=[mapping[i] for i in s17];old_counts=Counter(mapped);seen=Counter();seq=[]
for i in mapped:
    if e2[i]['isFlying']!=0:seq.append(i);continue
    before=seen[i]*proposed_counts[i]//old_counts[i];seen[i]+=1
    after=seen[i]*proposed_counts[i]//old_counts[i]
    assert after>=before+1
    seq.extend([i]*(after-before))
extra=new_air_count-old_counts[air_id];assert extra>=0
candidates=[j for j in range(len(seq)-1) if e2[seq[j]]['isFlying']==0 and e2[seq[j+1]]['isFlying']==0]
positions=[float(j) for j,i in enumerate(seq) if e2[i]['isFlying']!=0];chosen=set()
for _ in range(extra):
    j=max((j for j in candidates if j not in chosen),key=lambda j:(min(abs(j+.5-p) for p in positions),-j))
    chosen.add(j);positions.append(j+.5)
proposed=[]
for j,i in enumerate(seq):
    proposed.append(i)
    if j in chosen:proposed.append(air_id)
assert Counter(proposed)==Counter(proposed_counts)
full=[]
for n in range(1,26):
    _,current,_=wave(2,n)
    if n!=7:assert not(set(proposed_counts)&set(current))
    full.extend(proposed if n==7 else current)
assert not any(e2[a]['isFlying']!=0 and e2[b]['isFlying']!=0 for a,b in zip(full,full[1:]))
span7=(len(proposed)-1)*interval
def workload(sequence,span,hps):
    return {name:sum(hps.get(i,e2[i]['hp'])/(1-e2[i]['armor']) for i in sequence if (e2[i]['isFlying']!=0)==flying)/span
            for name,flying in (('ground',False),('air',True))}
load6=workload(s26,span6,{});load7=workload(proposed,span7,proposed_hp)
def kills(seq):return sum((D(e2[i]['reward']) for i in seq),D(0))
aoe_cases=[]
for m1 in (2.,4.,6.):
    m2=1+(m1-1)*bullets[tw[2,2]['bulletId']]['aoeRadius']/bullets[tw[2,1]['bulletId']]['aoeRadius']
    aoe_cases.append({'level1MeanHitTargetsAssumption':m1,'level2MeanHitTargetsAssumption':m2,
                      'upgrade1To2GroundDPSIncrementIdeal':dps(tw[2,2])*m2-dps(tw[2,1])*m1,
                      'meaning':'Dense one-dimensional stream sensitivity only; multiplicity is not observed combat data.'})
packages=[{'name':'Two new Normal1','cost':64,'groundOrAirDPS':2*dps(tw[1,1]),'mutuallyExclusiveGroundAirTime':True},
          {'name':'Normal1 to Normal3','cost':68,'deltaGroundDPS':dps(tw[1,3])-dps(tw[1,1]),
           'deltaAirDPS':dps(tw[1,3])*tw[1,3]['airDamageScale']-dps(tw[1,1]),'requires':'An eligible level1 normal tower','mutuallyExclusiveGroundAirTime':True},
          {'name':'New Normal1 plus Power1 to Power2','cost':mixed_cost,'newNormalDPS':dps(tw[1,1]),
           'powerUpgradeDPSCases':aoe_cases,'requires':'An eligible level1 AOE tower; placement is not prescribed'},
          {'name':'New Normal1 plus Frost1','cost':tw[1,1]['prices']+tw[3,1]['prices'],
           'newNormalDPS':dps(tw[1,1]),'slowFraction':tw[3,1]['effectValue'],
           'supportFormula':'Extra expected attack time = unslowedFractionNewlyCovered * s/(1-s). Strongest slow only; existing stronger overlaps add zero.',
           'newlyCoveredFractionSensitivity':[.10,.20,.30]}]
edits=[{'table':'EnemyData','id':i,'field':'hp','old':e2[i]['hp'],'value':proposed_hp[i]} for i in proposed_hp]
edits.append({'table':'EnemyList','id':2007,'field':'EnemyIndexs','old':s27,'value':proposed})
manifest={'sourceHashes':{t:baseline['sources'][f'Luban/Config/Datas/Levels/L02/{t}.xlsx'] for t in ('EnemyData','EnemyList')},'edits':edits}
report={'sourceWrites':0,'calculationOnly':True,'usesSpecificLayout':False,'newBudgetConfirmed':74,'rows':rows,
        'marginalActions':actions,'budgetPackages':packages,'airUtilizationSensitivity':air_limits,
        'referenceCalibration':{'L01W6':reference6,'L01W7':reference7,'L01IncrementalGold':reference_gold,
                                'airIncrementPerGold':air_per_gold,'L02AirIncrementBudget':air_increment_budget,
                                'groundSensitivityCases':ground_cases,'groundSeedScaleMedian':ground_scale,
                                'groundHpScaleSensitivityRange':[min(c['seedHpScale'] for c in ground_cases),max(c['seedHpScale'] for c in ground_cases)]},
        'airIncrementRequired':load7['air']-load6['air'],'birthSpan':{'W6':span6,'W7':span7},
        'workloadEHPPerSpawnSecond':{'W6':load6,'W7':load7,'ratios':{k:load7[k]/load6[k] for k in load6}},
        'wave7Total':len(proposed),'wave7Ground':ground_count,'wave7Air':new_air_count,
        'income':{'oldW7KillAndRound':float(kills(s27)+D(r27['rewardGold'])),
                  'candidateW7KillAndRound':float(kills(proposed)+D(r27['rewardGold'])),
                  'extraKillIncome':float(kills(proposed)-kills(s27)),'roundRewardHeld':r27['rewardGold']},
        'hpMethod':'Start from accepted W6 and trusted L01 species growth, then calibrate incremental equivalent combat burden per gold from L01 W6 to W7. Ground HP uses the median of explicit nonspatial AOE/normal/slow sensitivity cases, not a gold-ratio HP multiplier.',
        'countMethod':'Ground uses trusted L01 species-growth reference. Air takes the largest count within the additional-air-burden budget calibrated from trusted L01 tables and its 43-gold reward, scaled to 74 gold. The utilization band is a cross-check, not a measured efficiency or the decision rule.',
        'airSeparationAcrossAllWaves':True,'actualTowerCoordinatesRequired':False,
        'limitations':['L01 tables are the user-selected design reference; the per-gold growth coefficient is an inferred reference coefficient, not measured player DPS.',
                       'The utilization band, normal ground share, AOE density and slow opportunity cases are design sensitivities, not measured player statistics. Their median is a design choice, not a statistical confidence estimate.',
                       'The mixed package supplies an affordability reference; it does not prescribe the player purchase and is not proof all packages clear the wave.',
                       'Ground and air shot time from a normal tower are shared, never counted simultaneously at full output.',
                       'Ground AOE has density-dependent throughput. Ground HP per second is a workload diagnostic, not a linear difficulty score.',
                       'Slow only adds opportunity to damage towers, is subject to strongest-only overlap, and is never standalone damage.',
                       'Peak windows and actual leaks remain for user validation. No combat simulation or editor test was run.']}
for name,obj in [('manifest.json',manifest),('calculation.json',report)]:
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'scope-before.json').write_bytes((BASE/'scope-before.json').read_bytes())
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in baseline['sources'].items())
print(json.dumps({k:report[k] for k in ('sourceWrites','usesSpecificLayout','rows','airUtilizationSensitivity','airIncrementRequired','workloadEHPPerSpawnSecond','wave7Total','wave7Ground','wave7Air','income')},ensure_ascii=False,indent=2))
