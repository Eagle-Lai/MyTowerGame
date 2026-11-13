"""Read-only coverage and upgrade-budget analysis. This is not a combat simulation."""
from pathlib import Path
from itertools import product
from collections import Counter
import json, math, hashlib, openpyxl
from decimal import Decimal, ROUND_HALF_UP
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Library/BalanceStage/w6-reward145-20261109'
baseline=json.loads((OUT/'scope-before.json').read_text(encoding='utf-8'))
def read(level,table):
    p=ROOT/f'Luban/Config/Datas/Levels/L{level:02}/{table}.xlsx'
    assert hashlib.sha256(p.read_bytes()).hexdigest()==baseline['sources'][p.relative_to(ROOT).as_posix()]
    b=openpyxl.load_workbook(p,read_only=True,data_only=False)
    rows=list(b.worksheets[0].values);headers=rows[0]
    records=[{k:r[i] for i,k in enumerate(headers) if k and k!='##'} for r in rows[3:] if len(r)>1 and isinstance(r[1],int)]
    b.close();return records
data={f'L{l:02}':{t:read(l,t) for t in ('TowerInfo','BulletData','EnemyData','EnemyList','RoundData','SceneInfo','LevelMap')} for l in (1,2)}
tw={(r['type'],r['level']):r for r in data['L01']['TowerInfo']}
bullets={r['id']:r for r in data['L01']['BulletData']}
for r in data['L02']['TowerInfo']:
    for field in ('prices','power','CD','radius','airDamageScale','canAttackAir','effectValue'):
        assert r[field]==tw[r['type'],r['level']][field]
    if r['type']==2:
        b=next(b for b in data['L02']['BulletData'] if b['id']==r['bulletId'])
        assert b['aoeRadius']==bullets[tw[r['type'],r['level']]['bulletId']]['aoeRadius']
layout=[(3,0,1,1),(3,1,1,1),(3,3,1,1),(4,1,1,1),(5,1,1,1),(5,3,1,1),
        (1,3,2,1),(2,3,2,1),(8,3,2,1),(7,3,2,2),(6,1,2,3),(6,3,2,3),(7,1,2,3),(4,3,3,3)]
waypoints=[(0,4),(0,8),(2,8),(2,0),(4,0),(4,4),(15,4)]
occupied={(c,r) for r,c,_,_ in layout}
def sample_path(points,step=.005):
    samples=[]
    for a,b in zip(points,points[1:]):
        length=math.dist(a,b);n=round(length/step)
        for j in range(n):
            f=(j+.5)/n;samples.append((a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f,length/n))
    return np.array(samples)
ground=sample_path(waypoints);air=sample_path([(0,4),(15,4)])
assert all((round(x),round(y)) not in occupied for x,y,_ in ground if abs(x-round(x))<.003 and abs(y-round(y))<.003)
slow=tw[3,3]
def exposure(r,c,t,lv,path,air_only=False):
    cfg=tw[t,lv]
    if t==3 or (air_only and not cfg['canAttackAir']):return 0.
    distance=(path[:,0]-c)**2+(path[:,1]-r)**2
    in_slow=(path[:,0]-3)**2+(path[:,1]-4)**2<=slow['radius']**2
    slow_weight=np.where(in_slow,1/(1-slow['effectValue']),1.)
    # Common speed factor cancels for the same monster before/after upgrades.
    value=float(np.sum(path[:,2]*slow_weight*(distance<=cfg['radius']**2)))*cfg['power']/(cfg['CD']/1000)
    if air_only:value*=cfg['airDamageScale']
    return value
base_air=sum(exposure(r,c,t,lv,air,True) for r,c,t,lv in layout)
base_ground=sum(exposure(r,c,t,lv,ground) for r,c,t,lv in layout)
base_aoe=sum(exposure(r,c,t,lv,ground)*bullets[tw[t,lv]['bulletId']]['aoeRadius'] for r,c,t,lv in layout if t==2)
options=[]
for r,c,t,lv in layout:
    opts=[]
    for new in range(lv,4):
        cost=sum(tw[t,k]['prices'] for k in range(lv+1,new+1))
        dg=exposure(r,c,t,new,ground)-exposure(r,c,t,lv,ground)
        da=exposure(r,c,t,new,air,True)-exposure(r,c,t,lv,air,True)
        dp=0.
        if t==2:
            dp=exposure(r,c,t,new,ground)*bullets[tw[t,new]['bulletId']]['aoeRadius']-exposure(r,c,t,lv,ground)*bullets[tw[t,lv]['bulletId']]['aoeRadius']
        opts.append({'r':r,'c':c,'type':t,'from':lv,'to':new,'cost':cost,'groundDelta':dg,'airDelta':da,'aoeDelta':dp})
    options.append(opts)
plans=[]
for combination in product(*options):
    cost=sum(o['cost'] for o in combination)
    if cost>145:continue
    g=1+sum(o['groundDelta'] for o in combination)/base_ground
    a=1+sum(o['airDelta'] for o in combination)/base_air
    p=1+sum(o['aoeDelta'] for o in combination)/base_aoe
    plans.append({'cost':cost,'groundExposureRatio':g,'airExposureRatio':a,'aoeRadiusWeightedExposureRatio':p,
                  'balancedScore':min(p,a),'upgrades':[o for o in combination if o['cost']]})
best={k:max(plans,key=lambda p:p[k]) for k in ('groundExposureRatio','airExposureRatio','aoeRadiusWeightedExposureRatio','balancedScore')}
enemies={r['id']:r for r in data['L02']['EnemyData']}
groups={r['id']:r for r in data['L02']['EnemyList']}
rounds={r['id']:r for r in data['L02']['RoundData']}
seqs={rid:[int(i) for gid in str(rounds[rid]['EnemyIndexs']).split(',') for i in str(groups[int(gid)]['EnemyIndexs']).split(',')] for rid in (2005,2006)}
assert rounds[2005]['rewardGold']==145
actual={6000050:(274.133331,269),6000051:(178.186631,165),6000052:(504.405345,101),6000055:(213.8883,27)}
assert all(enemies[i]['hp']==h and seqs[2006].count(i)==n for i,(h,n) in actual.items())
def metrics(rid):
    seq=seqs[rid];span=(len(seq)-1)*groups[rid]['enemyInterval']/1000
    return {'span':span,'groundPerSecond':sum(enemies[i]['isFlying']==0 for i in seq)/span,
            'airPerSecond':sum(enemies[i]['isFlying']!=0 for i in seq)/span}
report={'layoutZeroBased':layout,'layoutConfirmedCompleteByUser':True,'noBuildW6PassedByUser':True,
        'baseInvestment':sum(sum(tw[t,k]['prices'] for k in range(1,lv+1)) for r,c,t,lv in layout),
        'rewardBudget':145,'groundWaypointsZeroBased':waypoints,'groundLength':float(ground[:,2].sum()),
        'airLength':float(air[:,2].sum()),'feasibleUpgradePlans':len(plans),'bestPlans':best,
        'metrics':{str(rid):metrics(rid) for rid in seqs},
        'method':'Static path integral of DPS * range indicator / speed-with-slow. Ground AOE proxy also weights by explosion radius, appropriate only as a dense 1D stream sensitivity approximation. Not measured damage, kill capacity, leakage or a combat simulation.',
        'limitations':['Single-target exposure is shared among concurrent enemies.','AOE target selection, turning geometry, overkill and slow linger are not simulated.','No-build pass is only an inequality; actual unused damage margin is unknown.','Upgrade optimization uses the 14 confirmed occupied cells only, and holds the route fixed.','A unique balanced HP cannot be inferred from the pass/fail observation alone.']}
(OUT/'current-source-inputs.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'coverage-analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
# Round the mixed-upgrade static sensitivity to a usable 5 percentage-point
# trial increment. This is a design choice, not a fitted lethal threshold.
D=lambda x:Decimal(str(x))
def trial_ratio(ratio):
    return D(1)+((D(ratio)-1)/D('.05')).quantize(D(1),rounding=ROUND_HALF_UP)*D('.05')
mixed=best['balancedScore']
ground_ratio=trial_ratio(mixed['aoeRadiusWeightedExposureRatio'])
air_ratio=trial_ratio(mixed['airExposureRatio'])
assert ground_ratio==D('1.20') and air_ratio==D('1.25')
edits=[];candidate=[]
for eid,(oldhp,count) in actual.items():
    e=enemies[eid];ratio=air_ratio if e['isFlying']!=0 else ground_ratio
    hp=float((D(oldhp)*ratio).quantize(D('.000001'),rounding=ROUND_HALF_UP))
    i5=next(i for i in set(seqs[2005]) if enemies[i]['resName']==e['resName'])
    projectile=D('6') if e['isFlying']!=0 else D('33')*(1-D(e['armor']))
    ceil=lambda value:int((D(value)/projectile).to_integral_value(rounding='ROUND_CEILING'))
    candidate.append({'id':eid,'name':e['name'],'countHeld':count,'W5Hp':enemies[i5]['hp'],'oldHp':oldhp,'newHp':hp,
                      'hpMultiplier':float(ratio),'oldReferenceShots':ceil(oldhp),'newReferenceShots':ceil(hp),
                      'referenceDamage':float(projectile),'isFlying':e['isFlying']})
    edits.append({'table':'EnemyData','id':eid,'field':'hp','old':oldhp,'value':hp})
assert all(not set(actual).intersection(int(i) for gid in str(r['EnemyIndexs']).split(',') for i in str(groups[int(gid)]['EnemyIndexs']).split(',')) for r in data['L02']['RoundData'] if r['id']!=2006)
exported={r['id']:r for r in baseline['exports']['tbenemydata.json']['rows']}
import struct
for eid in actual:
    for field in ('hp','speed','armor','reward'):
        assert struct.pack('f',enemies[eid][field])==struct.pack('f',exported[eid][field]),(eid,field)
assert seqs[2006]==next(r for r in baseline['exports']['tbenemylist.json']['rows'] if r['id']==2006)['EnemyIndexs']
manifest={'sourceHashes':{'EnemyData':baseline['sources']['Luban/Config/Datas/Levels/L02/EnemyData.xlsx']},'edits':edits}
calculation={'candidate':candidate,'groundMultiplier':float(ground_ratio),'airMultiplier':float(air_ratio),
             'designBasis':'Use the user-confirmed no-upgrade pass of the CURRENT W6 as the empirical anchor. Transfer the mixed affordable upgrade exposure ratios into trial HP increments, rounded to 5 percentage points. This does not estimate or prove the actual leakage threshold.',
             'mixedUpgradePlan':mixed,'battleSimulationPerformed':False,'sourceCellsToChange':4,
             'held':['all spawn IDs, counts and order','speed','armor','enemyInterval','kill reward','round reward','W5','other waves and levels'],
             'extraKillIncome':0,'fullClearW6IncomeHeld':float(sum((D(enemies[i]['reward']) for i in seqs[2006]),D(0))+D(rounds[2006]['rewardGold'])),
             'calibrationLimit':'Cannot guarantee old formation fails and upgraded formation passes without another user playtest; no measured survival or clearance margin was supplied.'}
for name,obj in [('manifest.json',manifest),('calculation.json',calculation)]:
    target=OUT/name
    assert not target.exists(),'Preserve existing candidate'
    target.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in baseline['sources'].items())
print(json.dumps(calculation,ensure_ascii=False,indent=2))
