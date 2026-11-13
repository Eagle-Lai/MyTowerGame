"""Read-only W8 design: trusted sources, accepted W7, wallet, marginal portfolios.

No workbook or Unity export writes. Tower coordinates are deliberately absent.
Portfolio results are a nonspatial design sensitivity, never a gameplay test.
"""
from pathlib import Path
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import hashlib, json, math, statistics
import openpyxl
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'Library/BalanceStage/w8-economy-design-20261110'
BASE = json.loads((OUT/'scope-before.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in BASE['sources'].items())

def read(p):
    book=openpyxl.load_workbook(p,read_only=True,data_only=False)
    rr=list(book.worksheets[0].values);heads=rr[0]
    result=[{h:r[i] for i,h in enumerate(heads) if h and h!='##'}
            for r in rr[3:] if len(r)>1 and isinstance(r[1],int)]
    book.close();return result

data={f'L{lv:02}':{t:read(ROOT/f'Luban/Config/Datas/Levels/L{lv:02}/{t}.xlsx')
       for t in ('EnemyData','EnemyList','RoundData','TowerInfo','BulletData','LevelMap','SceneInfo','LevelRules')}
      for lv in (1,2)}
data['WaveTuning']=read(ROOT/'Luban/Config/Datas/WaveTuning.xlsx')
(OUT/'current-source-inputs.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def index(lv,t):return {r['id']:r for r in data[f'L{lv:02}'][t]}
def ids(s):return [int(i) for i in str(s).split(',')]
def wave(lv,n):
    r=index(lv,'RoundData')[ids(data[f'L{lv:02}']['SceneInfo'][0]['RoundList'])[n-1]]
    groups=index(lv,'EnemyList')
    seq=[i for g in ids(r['EnemyIndexs']) for i in ids(groups[g]['EnemyIndexs'])]
    intervals=[groups[g]['enemyInterval'] for g in ids(r['EnemyIndexs'])]
    assert len(set(intervals))==1
    return r,seq,Counter(seq),intervals[0]/1000

es={lv:index(lv,'EnemyData') for lv in (1,2)}
r17,s17,c17,d17=wave(1,7);r18,s18,c18,d18=wave(1,8)
r27,s27,c27,d27=wave(2,7);r28,s28,c28,d28=wave(2,8)
approved={6000060:(373.371334,297),6000061:(242.691359,174),6000062:(687.003288,110),6000065:(311.548419,31)}
assert all(es[2][i]['hp']==h and c27[i]==n for i,(h,n) in approved.items())
assert r28['id']==2008 and ids(r28['EnemyIndexs'])==[2008] and d28==.231
assert r17['waveType']==r18['waveType']==r27['waveType']==r28['waveType']==1
for t in data['WaveTuning']:
    if t['levelId'] in (1,2):
        for field in ('groundHpScale','airHpScale','groundSpeedScale','airSpeedScale','killGoldScale'):assert t[field]==1
        for field in ('groundArmorBonus','airArmorBonus','waveGoldBonus'):assert t[field]==0
key=lambda e:(e['resName'],e['isFlying']!=0)
maps=[{key(es[lv][i]):i for i in c} for lv,c in ((1,c17),(1,c18),(2,c27),(2,c28))]
assert all(set(m)==set(maps[0]) for m in maps)
D=lambda x:Decimal(str(x))
round6=lambda x:float(x.quantize(D('.000001'),rounding=ROUND_HALF_UP))
roundn=lambda x:int(x.quantize(D(1),rounding=ROUND_HALF_UP))
hps={};counts={};rows=[];map18={}
for k,i8 in maps[3].items():
    i7=maps[2][k];a7=maps[0][k];a8=maps[1][k];map18[a8]=i8
    hps[i8]=round6(D(es[2][i7]['hp'])*D(es[1][a8]['hp'])/D(es[1][a7]['hp']))
    counts[i8]=roundn(D(c27[i7])*D(c18[a8])/D(c17[a7]))
    rows.append({'id':i8,'name':es[2][i8]['name'],'isFlying':es[2][i8]['isFlying'],
                 'acceptedW7Hp':es[2][i7]['hp'],'acceptedW7Count':c27[i7],
                 'oldW8Hp':es[2][i8]['hp'],'oldW8Count':c28[i8],
                 'newHp':hps[i8],'newCount':counts[i8],
                 'referenceHpRatio':es[1][a8]['hp']/es[1][a7]['hp']})

tw={(t['type'],t['level']):t for t in data['L01']['TowerInfo']}
for t in data['L02']['TowerInfo']:
    for field in ('power','CD','prices','radius','effectValue','canAttackAir','airDamageScale'):
        assert t[field]==tw[t['type'],t['level']][field]
bs=index(1,'BulletData');bs2=index(2,'BulletData')
for t in data['L02']['TowerInfo']:
    if t['bulletId']!=0:assert bs2[t['bulletId']]['aoeRadius']==bs[tw[t['type'],t['level']]['bulletId']]['aoeRadius']
cost={(typ,lv):sum(tw[typ,l]['prices'] for l in range(1,lv+1)) for typ,lv in tw}
dps=lambda typ,lv:tw[typ,lv]['power']/(tw[typ,lv]['CD']/1000)
wallet=218
# Inventory is only an aggregate economic check, not a mandatory layout.
stock={1:(4,0,2),2:(5,0,5),3:(0,0,1)}
deployed=sum(stock[t][l-1]*cost[t,l] for t in stock for l in (1,2,3))
assert deployed==1373
income=D(100)
for n in range(1,8):
    r,s,c,dt=wave(2,n)
    income+=sum((D(es[2][i]['reward']) for i in s),D(0))+D(r['rewardGold'])
assert int(income)==deployed+wallet,(income,deployed,wallet)

def portfolios(typ):
    """All affordable new builds/upgrades from aggregate stock; no sells or positions."""
    initial=stock[typ]
    assert initial[1]==0
    result={}
    for up2 in range(initial[0]+1):
      for up3 in range(initial[0]-up2+1):
        upgrade=up2*tw[typ,2]['prices']+up3*(tw[typ,2]['prices']+tw[typ,3]['prices'])
        if upgrade>wallet:continue
        for new1 in range((wallet-upgrade)//cost[typ,1]+1):
          for new2 in range((wallet-upgrade-new1*cost[typ,1])//cost[typ,2]+1):
            for new3 in range((wallet-upgrade-new1*cost[typ,1]-new2*cost[typ,2])//cost[typ,3]+1):
                spent=upgrade+new1*cost[typ,1]+new2*cost[typ,2]+new3*cost[typ,3]
                final=(initial[0]-up2-up3+new1,up2+new2,initial[2]+up3+new3)
                k=(spent,final)
                result.setdefault(k,{'spent':spent,'levels':final,'upgrade1to2':up2,'upgrade1to3':up3,'new':(new1,new2,new3)})
    return list(result.values())
normal=portfolios(1);power=portfolios(2)
# One newly covered slow region only. Existing F3 is already in the accepted baseline.
# No double application to both AOE multiplicity and global opportunity.
frost=[{'spent':0,'level':0}]+[{'spent':cost[3,lv],'level':lv} for lv in (1,2,3)]
packages=[]
for ni,n in enumerate(normal):
  for pi,p in enumerate(power):
    for fi,f in enumerate(frost):
      total=n['spent']+p['spent']+f['spent']
      if wallet-30<=total<=wallet:packages.append((ni,pi,fi,total))
pk=np.array(packages,dtype=int);nc=np.array([n['levels'] for n in normal]);pc=np.array([p['levels'] for p in power])
ng=nc@np.array([dps(1,l) for l in (1,2,3)])
na=nc@np.array([dps(1,l)*tw[1,l]['airDamageScale'] for l in (1,2,3)])
ng0=sum(stock[1][l-1]*dps(1,l) for l in (1,2,3));na0=sum(stock[1][l-1]*dps(1,l)*tw[1,l]['airDamageScale'] for l in (1,2,3))

def load(lv,c,h,dt):
    span=(sum(c.values())-1)*dt
    ground=[i for i in c if es[lv][i]['isFlying']==0]
    return {'span':span,'ground':sum(c[i]*h.get(i,es[lv][i]['hp'])/(1-es[lv][i]['armor']) for i in ground)/span,
            'air':sum(c[i]*h.get(i,es[lv][i]['hp'])/(1-es[lv][i]['armor']) for i in c if i not in ground)/span,
            'groundRate':sum(c[i] for i in ground)/span,
            'speed':sum(c[i] for i in ground)/sum(c[i]/es[lv][i]['speed'] for i in ground)}
l7=load(2,c27,{},d27);l8=load(2,counts,hps,d28)

def required_utilization(l,ng,na,p,opportunity=1):
    # A normal tower's firing time is shared. It cannot supply both full DPS figures.
    return np.maximum(l['air']/na,(l['ground']+l['air']*ng/na)/(p+ng))/opportunity

scenarios=[]
for density in (.5,1.):
  for existing_dwell in (1.,1.4,2.):
    m=lambda l:np.array([1+density*2*bs[tw[2,lv]['bulletId']]['aoeRadius']*l['groundRate']/l['speed']*existing_dwell for lv in (1,2,3)])
    p7=sum(stock[2][lv-1]*dps(2,lv)*m(l7)[lv-1] for lv in (1,2,3))
    p8=pc@(np.array([dps(2,lv) for lv in (1,2,3)])*m(l8))
    u7=float(required_utilization(l7,ng0,na0,p7))
    for newly_covered in (0.,.1,.2):
        fs=np.array([1 if f['level']==0 else 1+newly_covered*tw[3,f['level']]['effectValue']/(1-tw[3,f['level']]['effectValue']) for f in frost])
        ratios=required_utilization(l8,ng[pk[:,0]],na[pk[:,0]],p8[pk[:,1]],fs[pk[:,2]])/u7
        nspent=np.array([normal[i]['spent'] for i in pk[:,0]])
        pspent=np.array([power[i]['spent'] for i in pk[:,1]])
        fspent=np.array([frost[i]['spent'] for i in pk[:,2]])
        styles={'mixed':(nspent>=64)&(pspent>=80)&(fspent==0),
                'normal_emphasis':(nspent>=100)&(pspent>=40)&(fspent==0),
                'AOE_emphasis':(nspent>=32)&(pspent>=130)&(fspent==0),
                'support_mixed':(nspent>=32)&(pspent>=44)&(fspent>=30)}
        best={}
        for name,mask in styles.items():
            ii=np.where(mask)[0];chosen=int(ii[np.argmin(ratios[ii])]);ni,pi,fi,spent=map(int,pk[chosen])
            best[name]={'relativeUtilization':float(ratios[chosen]),'cost':spent,'normal':normal[ni],'power':power[pi],'frost':frost[fi]}
        scenarios.append({'densityFraction':density,'existingSlowDensityMultiplier':existing_dwell,
                          'newSlowCoverageOpportunityFraction':newly_covered,
                          'baselineUtilizationInSimplifiedModel':u7,
                          'baselineAOEMultiplicity':m(l7).tolist(),'candidateAOEMultiplicity':m(l8).tolist(),'bestByStyle':best})

styles_summary={style:{'min':min(s['bestByStyle'][style]['relativeUtilization'] for s in scenarios),
                       'median':statistics.median(s['bestByStyle'][style]['relativeUtilization'] for s in scenarios),
                       'max':max(s['bestByStyle'][style]['relativeUtilization'] for s in scenarios)}
                for style in scenarios[0]['bestByStyle']}
income8=sum((D(counts[i])*D(es[2][i]['reward']) for i in counts),D(0))+D(r28['rewardGold'])
income8old=sum((D(c28[i])*D(es[2][i]['reward']) for i in c28),D(0))+D(r28['rewardGold'])
report={'calculationOnly':True,'sourceWrites':0,'rows':rows,'walletAlreadyAfterW7Settlement':wallet,
        'aggregateScreenshotStock':stock,'deployedCost':deployed,'cumulativeSourceIncomeThroughW7':str(income),
        'normalPortfolioCount':len(normal),'powerPortfolioCount':len(power),'purchasePortfolioCount':len(pk),
        'load':{'W7':l7,'W8':l8,'groundRatio':l8['ground']/l7['ground'],'airRatio':l8['air']/l7['air']},
        'styleSummary':styles_summary,'sensitivityCases':scenarios,
        'economy':{'oldW8KillAndRound':float(income8old),'newW8KillAndRound':float(income8),'extraW8KillIncome':float(income8-income8old)},
        'method':'W8 uses accepted W7 HP/counts multiplied by trusted L01 W7-to-W8 species growth. The observed wallet is used once for an independent joint ground-air portfolio-capacity check, not to multiply the intrinsic L01 HP spike by wallet/43.',
        'limitations':['No coordinates or mandatory purchase route. Aggregate inventory constrains eligible upgrades only.',
                       'Density, slow coverage and common targeting utilization are design sensitivities, not measured telemetry.',
                       'Model estimates average nonspatial throughput, not terminal pressure or actual zero leaks.',
                       'Best within each spending style does not prove every purchase in that style clears W8.',
                       'Shared normal firing time is counted once using aggregate grade ratio. Grade-specific target scheduling is approximated.',
                       'New Frost opportunity is applied once only; overlapping equal/stronger slow can produce zero additional benefit.']}
# Preserve L01's type-order skeleton, expand ground occurrences proportionally,
# and insert additional air at well-separated non-air gaps.
mapped=[map18[i] for i in s18];seed_counts=Counter(mapped);seen=Counter();seq=[]
for i in mapped:
    if es[2][i]['isFlying']!=0:seq.append(i);continue
    before=seen[i]*counts[i]//seed_counts[i];seen[i]+=1
    after=seen[i]*counts[i]//seed_counts[i]
    assert after>before
    seq.extend([i]*(after-before))
air_ids=[i for i in counts if es[2][i]['isFlying']!=0];assert len(air_ids)==1
air=air_ids[0];extra=counts[air]-seed_counts[air];assert extra>=0
gaps=[j for j in range(len(seq)-1) if es[2][seq[j]]['isFlying']==0 and es[2][seq[j+1]]['isFlying']==0]
positions=[float(j) for j,i in enumerate(seq) if es[2][i]['isFlying']!=0];selected=set()
for _ in range(extra):
    j=max((j for j in gaps if j not in selected),key=lambda j:(min(abs(j+.5-p) for p in positions),-j))
    selected.add(j);positions.append(j+.5)
proposed=[]
for j,i in enumerate(seq):
    proposed.append(i)
    if j in selected:proposed.append(air)
assert Counter(proposed)==Counter(counts)
full=[]
for n in range(1,26):
    _,s,_,_=wave(2,n)
    if n!=8:assert not set(counts).intersection(s),'W8 IDs used outside W8'
    full.extend(proposed if n==8 else s)
assert not any(es[2][a]['isFlying']!=0 and es[2][b]['isFlying']!=0 for a,b in zip(full,full[1:]))
exports=BASE['exports']
ed={r['id']:r for r in exports['tbenemydata.json']['rows']}
eg={r['id']:r for r in exports['tbenemylist.json']['rows']}
import struct
for i in counts:assert struct.pack('f',ed[i]['hp'])==struct.pack('f',es[2][i]['hp'])
assert eg[2008]['EnemyIndexs']==s28
assert all(r['initialGold']==100 for r in exports['tbsceneinfo.json']['rows'])
manifest={'sourceHashes':{t:BASE['sources'][f'Luban/Config/Datas/Levels/L02/{t}.xlsx'] for t in ('EnemyData','EnemyList')},
          'edits':[{'table':'EnemyData','id':i,'field':'hp','old':es[2][i]['hp'],'value':hps[i]} for i in counts]
                  +[{'table':'EnemyList','id':2008,'field':'EnemyIndexs','old':s28,'value':proposed}]}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
report['proposedListAirSeparationAcrossAllL02Waves']=True
report['W8EnemyIdsExclusive']=True
report['sourceAndExportBaselineMatched']=True
report['noPurchaseRatios']=[]
for s in scenarios:
    m=np.array(s['candidateAOEMultiplicity'])
    p=sum(stock[2][lv-1]*dps(2,lv)*m[lv-1] for lv in (1,2,3))
    score=float(required_utilization(l8,ng0,na0,p))/s['baselineUtilizationInSimplifiedModel']
    report['noPurchaseRatios'].append(score)
report['scoreInterpretation']='Relative average-load/capacity design index, not measured utilization or terminal pressure. Values above one in the baseline are not claimed physically realized utilization; they expose uncertainty in this static model.'
(OUT/'calculation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in BASE['sources'].items())
print(json.dumps({k:report[k] for k in ('sourceWrites','rows','load','styleSummary','normalPortfolioCount','powerPortfolioCount','purchasePortfolioCount','economy')},ensure_ascii=False,indent=2))
