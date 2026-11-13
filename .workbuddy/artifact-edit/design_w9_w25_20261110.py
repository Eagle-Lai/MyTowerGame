"""Read-only L02 W9-W25 design inputs. Never authors source XLSX or exports."""
from pathlib import Path
from collections import Counter
import json, hashlib, math, statistics
from decimal import Decimal, ROUND_HALF_UP
import openpyxl

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Library/BalanceStage/w9-w25-design-20261110'
OUT.mkdir(parents=True, exist_ok=True)

def table(level, name):
    path = ROOT / f'Luban/Config/Datas/Levels/L{level:02}/{name}.xlsx'
    wb = openpyxl.load_workbook(path, read_only=True, data_only=False)
    rows = list(wb.worksheets[0].values)
    headers = rows[0]
    result = [{h: r[k] for k, h in enumerate(headers) if h and h != '##'}
              for r in rows[3:] if len(r) > 1 and isinstance(r[1], int)]
    wb.close()
    return result

def parse(value):
    return [int(s) for s in str(value).split(',')]

def collect():
    inputs = {str(lv): {t: table(lv, t) for t in ('EnemyData','EnemyList','RoundData','SceneInfo','TowerInfo','BulletData','LevelMap','LevelRules')} for lv in (1,2)}
    wb = openpyxl.load_workbook(ROOT / 'Luban/Config/Datas/WaveTuning.xlsx', read_only=True, data_only=False)
    rr=list(wb.worksheets[0].values)
    inputs['WaveTuning']=[dict(zip(rr[0],r)) for r in rr[3:] if isinstance(r[1],int)]
    wb.close()
    summary={}
    for lv in (1,2):
        d=inputs[str(lv)]
        es={e['id']:e for e in d['EnemyData']}
        rs={r['id']:r for r in d['RoundData']}
        gs={g['id']:g for g in d['EnemyList']}
        waves=[]
        cumulative=100.
        for n,rid in enumerate(parse(d['SceneInfo'][0]['RoundList']),1):
            r=rs[rid]
            groups=[gs[g] for g in parse(r['EnemyIndexs'])]
            seq=[e for g in groups for e in parse(g['EnemyIndexs'])]
            counts=Counter(seq)
            kills=sum(es[e]['reward'] for e in seq)
            waves.append({'wave':n,'round':r,'intervals':[g['enemyInterval'] for g in groups], 'preWaveCumulativeEarned':cumulative,
                          'killIncome':kills, 'total':len(seq), 'roster':[{**es[e], 'count':counts[e]} for e in counts]})
            cumulative+=kills+r['rewardGold']
        summary[str(lv)]={'waves':waves,'totalEarned':cumulative,'towers':d['TowerInfo'],'bullets':d['BulletData']}
    snapshots={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'Luban/Config/Datas').rglob('*.xlsx')}
    (OUT/'inputs.json').write_text(json.dumps(inputs,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'source-hashes.json').write_text(json.dumps(snapshots,indent=2),encoding='utf-8')
    for lv in ('1','2'):
        print('L'+lv, 'totalEarned',round(summary[lv]['totalEarned'],6))
        for w in summary[lv]['waves']:
            print(w['wave'], 'type',w['round']['waveType'],'dt',w['intervals'],'reward',w['round']['rewardGold'],'earned',round(w['preWaveCumulativeEarned'],3),
                  [(e['id'],e['resName'],e['count'],round(e['hp'],6),e['speed'],e['armor'],e['isFlying'],round(e['reward'],6)) for e in w['roster']])
    print('TOWERS',json.dumps(summary['1']['towers'],ensure_ascii=False))
    print('BULLETS',json.dumps(summary['1']['bullets'],ensure_ascii=False))
    print('TUNING',json.dumps(inputs['WaveTuning'],ensure_ascii=False))

def design():
    inputs=json.loads((OUT/'inputs.json').read_text(encoding='utf-8'))
    summary=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
    hashes=json.loads((OUT/'source-hashes.json').read_text(encoding='utf-8'))
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    for row in inputs['WaveTuning']:
        if row['levelId'] in (1,2):
            assert all(row[k]==1 for k in ('groundHpScale','airHpScale','groundSpeedScale','airSpeedScale','killGoldScale'))
            assert all(row[k]==0 for k in ('groundArmorBonus','airArmorBonus','waveGoldBonus'))
    species=lambda e:(e['resName'],bool(e['isFlying']))
    waves={lv:{w['wave']:w for w in summary[str(lv)]['waves']} for lv in (1,2)}
    roster=lambda lv,w:{species(e):e for e in waves[lv][w]['roster']}
    a1,a2=roster(1,8),roster(2,8)
    assert {(e['hp'],e['count']) for e in a2.values()}=={(445.918103,314),(289.846731,192),(820.489343,121),(372.082872,39)}
    base1=waves[1][8]['preWaveCumulativeEarned']
    base2=waves[2][8]['preWaveCumulativeEarned']
    ground_ratio=sum(e['count'] for e in a2.values() if not e['isFlying'])/sum(e['count'] for e in a1.values() if not e['isFlying'])
    count_ratios={s:a2[s]['count']/e['count'] for s,e in a1.items()}
    roundn=lambda v:int(Decimal(str(v)).quantize(Decimal(1),rounding=ROUND_HALF_UP))
    roundhp=lambda v:float(Decimal(str(v)).quantize(Decimal('.000001'),rounding=ROUND_HALF_UP))
    cases=[{'radius':r,'density':d,'dwell':u,'normalShare':q} for r in (.75,.9,1.05) for d in (.5,1.) for u in (1.,1.4,2.) for q in (0.,.25,.5)]
    def burden(rows,dt,case):
        span=(sum(e['count'] for e in rows)-1)*dt
        gr=[e for e in rows if not e['isFlying']]
        ar=[e for e in rows if e['isFlying']]
        ng=sum(e['count'] for e in gr)
        speed=ng/sum(e['count']/e['speed'] for e in gr)
        mult=1+case['density']*2*case['radius']*ng/span/speed*case['dwell']
        q=case['normalShare']
        g=sum(e['count']*e['hp']/(1-e['armor']) for e in gr)/span
        a=sum(e['count']*e['hp']/(1-e['armor']) for e in ar)/span
        return {'ground':g*(q+(1-q)/mult),'air':a,'multiplicity':mult,'rawGround':g,'span':span}
    anchor1=[burden(list(a1.values()),waves[1][8]['intervals'][0]/1000,c) for c in cases]
    anchor2=[burden(list(a2.values()),waves[2][8]['intervals'][0]/1000,c) for c in cases]
    cumulative=base2+waves[2][8]['killIncome']+waves[2][8]['round']['rewardGold']
    proposed_waves=[]
    previous_ground={s:e['hp'] for s,e in a2.items() if not e['isFlying']}
    previous_normal_air={s:e['hp'] for s,e in a2.items() if e['isFlying']}
    rows_out=[]
    lists={}
    es2={e['id']:e for e in inputs['2']['EnemyData']}
    es1={e['id']:e for e in inputs['1']['EnemyData']}
    g1={g['id']:g for g in inputs['1']['EnemyList']}
    g2={g['id']:g for g in inputs['2']['EnemyList']}
    edits=[]
    for n in range(9,26):
        ref,old=roster(1,n),roster(2,n)
        assert set(ref)==set(old)
        assert len(waves[1][n]['intervals'])==len(waves[2][n]['intervals'])==1
        assert waves[1][n]['round']['waveType']==waves[2][n]['round']['waveType']
        dt1=waves[1][n]['intervals'][0]/1000
        dt2=waves[2][n]['intervals'][0]/1000
        economic_factor=(cumulative/base2)/(waves[1][n]['preWaveCumulativeEarned']/base1)
        proposed=[]
        for s,e in ref.items():
            assert e['armor']==old[s]['armor']
            ratio=count_ratios.get(s,ground_ratio)
            proposed.append({**old[s],'hp':e['hp'],'count':roundn(e['count']*ratio)})
        ref_load=[burden(list(ref.values()),dt1,c) for c in cases]
        unit_load=[burden(proposed,dt2,c) for c in cases]
        scales={x:[anchor2[k][x]/unit_load[k][x]*(ref_load[k][x]/anchor1[k][x])*economic_factor for k in range(len(cases))] for x in ('ground','air')}
        unfloored={x:statistics.median(v) for x,v in scales.items()}
        common=dict(unfloored)
        ground_floor=max(previous_ground.get(s,0)/e['hp'] for s,e in ref.items() if not e['isFlying'])
        common['ground']=max(common['ground'],ground_floor)
        # A hard-wave air spike is not carried forward as the floor of a normal wave.
        air_floor=max(previous_normal_air.get(s,0)/e['hp'] for s,e in ref.items() if e['isFlying'])
        common['air']=max(common['air'],air_floor)
        for p in proposed:
            x='air' if p['isFlying'] else 'ground'
            p['hp']=roundhp(p['hp']*common[x])
            s=species(p)
            assert p['hp']>old[s]['hp'] and p['count']>old[s]['count']
            rows_out.append({'wave':n,'roundId':waves[2][n]['round']['id'],'id':p['id'],'enemy':p['resName'],'isFlying':p['isFlying'],
                             'oldHp':old[s]['hp'],'newHp':p['hp'],'oldCount':old[s]['count'],'newCount':p['count'],
                             'hpChangePct':100*(p['hp']/old[s]['hp']-1),'countChangePct':100*(p['count']/old[s]['count']-1),
                             'trustedL01Hp':ref[s]['hp'],'trustedL01Count':ref[s]['count']})
            edits.append({'table':'EnemyData','id':p['id'],'field':'hp','old':old[s]['hp'],'value':p['hp']})
            if not p['isFlying']:previous_ground[s]=p['hp']
            elif waves[2][n]['round']['waveType']==1:previous_normal_air[s]=p['hp']
        # Keep L01 relative ground-type order, expand ground occurrences and spread air into ground gaps.
        mapping={e['id']:old[s]['id'] for s,e in ref.items()}
        seq1=[i for gid in parse(waves[1][n]['round']['EnemyIndexs']) for i in parse(g1[gid]['EnemyIndexs'])]
        seed=[mapping[i] for i in seq1]
        counts={p['id']:p['count'] for p in proposed}
        seed_counts=Counter(seed);seq=[]
        # Keep every reference birth in relative order; spread added ground births
        # across gaps instead of duplicating high-EHP blocks into long bursts.
        extras={i:counts[i]-seed_counts[i] for i in seed_counts if not es2[i]['isFlying']}
        assert min(extras.values())>=0
        added=Counter();extra_ground=sum(extras.values())
        for pos,i in enumerate(seed):
            seq.append(i)
            number=(pos+1)*extra_ground//len(seed)-pos*extra_ground//len(seed)
            for _ in range(number):
                j=min((j for j,nextra in extras.items() if added[j]<nextra),key=lambda j:((added[j]+.5)/extras[j],j))
                seq.append(j);added[j]+=1
        assert added==Counter(extras)
        air=[p['id'] for p in proposed if p['isFlying']]
        assert len(air)==1
        air=air[0]
        extra=counts[air]-seed_counts[air]
        positions=[float(k) for k,i in enumerate(seq) if es2[i]['isFlying']]
        gaps=[k for k in range(len(seq)-1) if not es2[seq[k]]['isFlying'] and not es2[seq[k+1]]['isFlying']]
        chosen=set()
        for _ in range(extra):
            k=max((k for k in gaps if k not in chosen),key=lambda k:(min(abs(k+.5-p) for p in positions),-k))
            chosen.add(k);positions.append(k+.5)
        final=[]
        for k,i in enumerate(seq):
            final.append(i)
            if k in chosen:final.append(air)
        assert Counter(final)==Counter(counts)
        gid=parse(waves[2][n]['round']['EnemyIndexs'])
        assert gid==[waves[2][n]['round']['id']]
        lists[n]=final
        edits.append({'table':'EnemyList','id':gid[0],'field':'EnemyIndexs','old':parse(g2[gid[0]]['EnemyIndexs']),'value':final})
        load=[burden(proposed,dt2,c) for c in cases]
        deviations={x:[(load[k][x]/anchor2[k][x])/(ref_load[k][x]/anchor1[k][x])/economic_factor-1 for k in range(len(cases))] for x in ('ground','air')}
        kills=sum(p['count']*p['reward'] for p in proposed)
        current=waves[2][n]
        w={'wave':n,'roundId':current['round']['id'],'waveType':current['round']['waveType'],'intervalMs':dt2*1000,
           'roundReward':current['round']['rewardGold'],'preWaveCumulativeEarned':cumulative,'preWaveReferenceEarned':waves[1][n]['preWaveCumulativeEarned'],
           'economyCorrection':economic_factor,'groundHpScale':common['ground'],'airHpScale':common['air'],
           'unflooredGroundScale':unfloored['ground'],'unflooredAirScale':unfloored['air'],
           'groundHpFloorScale':ground_floor,'airHpFloorScale':air_floor,
           'floorExtraPressure':{x:common[x]/unfloored[x]-1 for x in common},
           'groundScaleRange':[min(scales['ground']),max(scales['ground'])],
           'stylePressureDeviationRange':{x:[min(v),max(v)] for x,v in deviations.items()},
           'oldKillIncome':current['killIncome'],'newKillIncome':kills,'newWaveTotalIncome':kills+current['round']['rewardGold'],
           'groundCount':sum(p['count'] for p in proposed if not p['isFlying']), 'airCount':sum(p['count'] for p in proposed if p['isFlying']),
           'total':len(final),'roster':proposed,'burdenCentral':load[len(cases)//2]}
        proposed_waves.append(w)
        cumulative+=kills+current['round']['rewardGold']
    full=[]
    ids_by_wave={n:set(lists[n]) for n in lists}
    for n in range(1,26):
        oldseq=[i for gid in parse(waves[2][n]['round']['EnemyIndexs']) for i in parse(g2[gid]['EnemyIndexs'])]
        full.extend(lists[n] if n in lists else oldseq)
        for other,iset in ids_by_wave.items():
            if n!=other:assert not iset.intersection(oldseq),'IDs reused outside target wave'
    assert not any(es2[a]['isFlying'] and es2[b]['isFlying'] for a,b in zip(full,full[1:]))
    # Read-only rolling arrivals diagnostics. These are NOT combat or terminal-pressure simulations.
    proposed_hp={r['id']:r['newHp'] for r in rows_out}
    def peak(seq,dt,es,hps,window=10.):
        result={}
        for flying in (False,True):
            values=[hps.get(i,es[i]['hp'])/(1-es[i]['armor']) if bool(es[i]['isFlying'])==flying else 0. for i in seq]
            width=math.ceil(window/dt-1e-10)
            running=sum(values[:width]);largest=running
            for k in range(width,len(values)):
                running+=values[k]-values[k-width];largest=max(largest,running)
            average=sum(values)/((len(seq)-1)*dt)
            result['air' if flying else 'ground']={'peakEHPPerSecond':largest/window,'averageEHPPerSecond':average,'peakToMean':largest/window/average}
        return result
    for w in proposed_waves:
        n=w['wave'];w['rolling10sArrival']=peak(lists[n],w['intervalMs']/1000,es2,proposed_hp)
        seq1=[i for gid in parse(waves[1][n]['round']['EnemyIndexs']) for i in parse(g1[gid]['EnemyIndexs'])]
        w['referenceRolling10sArrival']=peak(seq1,waves[1][n]['intervals'][0]/1000,es1,{})
    action_rows=[]
    towers={(t['type'],t['level']):t for t in inputs['1']['TowerInfo']}
    bullets={b['id']:b for b in inputs['1']['BulletData']}
    for t in inputs['2']['TowerInfo']:
        ref=towers[t['type'],t['level']]
        assert all(t[k]==ref[k] for k in ('power','CD','prices','radius','canAttackAir','airDamageScale','effectValue'))
    for (typ,lv),t in towers.items():
        if typ==3:continue
        old=towers.get((typ,lv-1));newd=t['power']/(t['CD']/1000);oldd=old['power']/(old['CD']/1000) if old else 0
        action_rows.append({'type':typ,'level':lv,'price':t['prices'],'DPS':newd,'deltaDPS':newd-oldd,'deltaDPSPerGold':(newd-oldd)/t['prices'],
                            'radius':bullets[t['bulletId']]['aoeRadius'],
                            'deltaAirDPS':newd*t['airDamageScale']-oldd*(old['airDamageScale'] if old else 0) if t['canAttackAir'] else 0})
    result={'calculationOnly':True,'sourceWrites':0,'exportWrites':0,'basis':'W5-W7 explicitly playtested; W8 confirmed/applied but no supplied W8 combat result.',
            'scope':'Only L02 W9-W25 HP and counts/order; all other fields held at current values.',
            'anchor':{'wave':8,'preWaveEarnedL01':base1,'preWaveEarnedL02':base2,'earnedAfterW8':base2+waves[2][8]['killIncome']+waves[2][8]['round']['rewardGold'],
                      'countRatios':{str(s):v for s,v in count_ratios.items()},'newGroundSpeciesCountRatio':ground_ratio},
            'assumption':'Same tower-system effective capacity per cumulative invested gold as the anchor; compare matched style scenarios, not arbitrary purchases. This is a conditional planning relation, not measured terminal pressure.',
            'cases':cases,'towerMarginalActions':action_rows,'waves':proposed_waves,'rows':rows_out,
            'oldTotalEconomy':summary['2']['totalEarned'],'newTotalEconomy':cumulative,'extraTotalEconomy':cumulative-summary['2']['totalEarned'],
            'airOrderAllL02WavesPassed':True,'sourceCount':len(hashes),'sourceUnchanged':True}
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    (OUT/'calculation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'manifest.json').write_text(json.dumps({'status':'proposal-only','edits':edits,'sourceHashes':hashes},ensure_ascii=False,indent=2),encoding='utf-8')
    for w in proposed_waves:
        print(w['wave'],round(w['economyCorrection'],6),round(w['preWaveCumulativeEarned'],3),[(e['resName'].replace('Enemy_',''),e['hp'],e['count']) for e in w['roster']], 'income',round(w['newWaveTotalIncome'],3))
    print('Economy',result['oldTotalEconomy'],result['newTotalEconomy'],result['extraTotalEconomy'])
    print('Max style deviation',max(abs(v) for w in proposed_waves for vals in w['stylePressureDeviationRange'].values() for v in vals))

if __name__=='__main__':
    import sys
    if '--design' in sys.argv:design()
    else:collect()
