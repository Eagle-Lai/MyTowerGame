#!/usr/bin/env python3
"""Authoritative deterministic balance compiler. Preview never writes Assets or Excel.

Luban spreadsheets are machine-owned source tables, so this adapter deliberately uses
the project's established openpyxl writer to preserve Luban header/type/style contracts.
All gameplay formulae live here and in balance_design.json, never in the EditorWindow.
"""
from __future__ import annotations
import argparse, collections, copy, csv, hashlib, json, math, os, pathlib, shutil
import struct, subprocess, sys, time, traceback, uuid
from datetime import datetime,timezone
from contextlib import contextmanager
from decimal import Decimal, ROUND_CEILING
from balance_campaign import dimensions, prepare_manifest, allocate, economy

ROOT = pathlib.Path(__file__).resolve().parents[2]
DESIGN = ROOT / 'Luban/BalanceDesign'
DATA = ROOT / 'Luban/Config/Datas'
DEFAULT_RECIPE = DESIGN / 'balance_design.json'
MANIFEST = DESIGN / 'variant_manifest.json'
STATE = DESIGN / 'applied_state.json'
JOBS = ROOT / 'Library/BalanceWorkbench'
TABLE_FILES = {'tbenemydata':'EnemyData','tbenemylist':'EnemyList','tbrounddata':'RoundData',
 'tbsceneinfo':'SceneInfo','tbtowerinfo':'TowerInfo','tbglobal':'Global','tblevelmap':'LevelMap',
 'tbbulletdata':'BulletData','tblevelrating':'LevelRating'}
OWNED_FIELDS={'tbsceneinfo':{'RoundList','initialGold','initialHp','difficulty','waveIntervalMs','desc'},
 'tbtowerinfo':{'power','CD','radius','prices','effectValue','canAttackAir','searchIntervalMs','sellPrice','desc','bulletId'},
 'tbglobal':{'autoNextRoundDelayMs','autoStartRoundDelayMs','sellRefundRate','defaultSearchIntervalMs'},
 'tblevelmap':{'cols','rows','cells','desc'},'tbbulletdata':{'aoeRadius','name','resName','speed','hitRadius','lifeTimeMs','effectType','effectValue','scale','desc'}}
ROLE_ORDER = ['normal','swarm','fast','air','medium','heavy','elite','boss']
RATING_TYPES = {'id':'int','difficultyTier':'int','profileId':'string','profileRevision':'string',
 'expectedWaveCount':'int','expectedEnemyCount':'int','twoStarHpPermille':'int',
 'threeStarHpPermille':'int','fourStarHpPermille':'int','maxFourStarLeaks':'int',
 'fourStarTimePermille':'int','parCombatTimeMs':'int','bossVariantIds':'(list#sep=,),int',
 'criticalVariantIds':'(list#sep=,),int','balanceRevision':'string','ratingRevision':'string',
 'planHash':'string','calibrationStatus':'string','runtimeContentHash':'string'}
FLOAT_FIELDS={'tbenemydata':{'speed','hp','armor','scale','bodyRadius'},
 'tbtowerinfo':{'CD','rotateSpeed','effectValue','radius'},
 'tbbulletdata':{'speed','hitRadius','aoeRadius','effectValue','scale'}}

def read_json(p, default=None):
    return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig')) if pathlib.Path(p).exists() else copy.deepcopy(default)
def canonical(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',',':'), allow_nan=False)
def digest(x): return hashlib.sha256(canonical(x).encode('utf-8')).hexdigest()
def file_hash(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() if pathlib.Path(p).exists() else None
def write_json(p,x):
    p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def round_up(x): return math.floor(float(x)+0.5)
def positive_int(x,label):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or int(x)!=x or x<=0: raise ValueError(label+' requires a positive integer')
    return int(x)
def progress(stage,**kw): print(json.dumps({'stage':stage,'phase':stage,**kw},ensure_ascii=False),flush=True)
def check_cancel(out):
    p=pathlib.Path(out).resolve()
    while p!=ROOT.parent and p!=p.parent:
        if (p/'cancel.request').exists():raise RuntimeError('Cancelled at a safe boundary; formal data unchanged')
        if p==ROOT:break
        p=p.parent

def default_recipe():
    names=['非常容易','容易','中等偏下','中等','中等偏上','困难','非常困难','极度困难']
    values=[(.50,.90,1.10,1.40),(.65,.94,1.07,1.25),(.82,.97,1.04,1.10),(1,1,1,1),
            (1.18,1.02,.98,.96),(1.40,1.04,.95,.92),(1.65,1.06,.92,.88),(1.95,1.08,.89,.84)]
    roles=[(1,1.1,0,2,1,1),(.65,1.05,0,1,1,1),(.85,1.6,0,2,1,2),(1.2,1.4,0,3,1,4),
           (2,1,.08,3,1,1),(4,.8,.18,5,2,3),(7,.75,.22,8,2,3),(18,.65,.25,25,4,5)]
    return {'schemaVersion':1,'balanceRevision':'balance-20x20-v1','ratingRevision':'five-stars-v1',
      'selectedProfileId':'D04','profiles':[{'id':f'D{i+1:02}','name':names[i],'revision':'1',
        'ehpMultiplier':v[0],'speedMultiplier':v[1],'gapMultiplier':v[2],'goldMultiplier':v[3]} for i,v in enumerate(values)],
      'formula':{'countOffset':6,'baseEhpPerUnit':30,'levelEhpGrowth':.03,'waveLinear':.12,'waveQuadratic':.018,
        'minBudgetGrowth':1.04,'pressureMultiplier':1.12,'finalMultiplier':1.25,'spawnBaseMs':900,
        'spawnWaveReductionMs':15,'spawnLevelReductionMs':5,'minSpawnMs':450,'maxSpawnMs':900,
        'speedLevelGrowth':.002,'speedWaveGrowth':.001,'initialGold':100,'goldPerLevel':18,'initialHp':20,
        'rewardBase':6,'rewardWaveBlock':5,'autoNextRoundDelayMs':5000,'autoStartRoundDelayMs':0,
        'tailBaseMs':10000,'tailTierGrowthMs':2000},
      'roles':{r:dict(zip(['weight','speed','armor','reward','damage','type'],v)) for r,v in zip(ROLE_ORDER,roles)},
      'unlockSchedule':[{'canonicalId':17,'level':1,'wave':1,'role':'normal'},
        {'canonicalId':18,'level':1,'wave':2,'role':'normal'},{'canonicalId':84,'level':1,'wave':3,'role':'swarm'},
        {'canonicalId':83,'level':1,'wave':5,'role':'medium'},{'canonicalId':13,'level':1,'wave':7,'role':'air'},
        {'canonicalId':11,'level':1,'wave':8,'role':'air'},{'canonicalId':14,'level':1,'wave':10,'role':'air'},
        {'canonicalId':88,'level':1,'wave':11,'role':'heavy'},{'canonicalId':123,'level':1,'wave':15,'role':'medium'},
        {'canonicalId':30,'level':2,'wave':11,'role':'fast'},{'canonicalId':108,'level':2,'wave':15,'role':'medium'},
        {'canonicalId':98,'level':3,'wave':11,'role':'fast'},{'canonicalId':80,'level':4,'wave':11,'role':'heavy'},
        {'canonicalId':86,'level':4,'wave':15,'role':'heavy'},{'canonicalId':31,'level':5,'wave':11,'role':'heavy'},
        {'canonicalId':40,'level':6,'wave':11,'role':'heavy'},{'canonicalId':58,'level':7,'wave':11,'role':'fast'},
        {'canonicalId':127,'level':8,'wave':11,'role':'heavy'},{'canonicalId':64,'level':9,'wave':11,'role':'fast'},
        {'canonicalId':70,'level':10,'wave':11,'role':'heavy'},{'canonicalId':67,'level':11,'wave':11,'role':'heavy'},
        {'canonicalId':129,'level':12,'wave':20,'role':'boss'},{'canonicalId':130,'level':13,'wave':20,'role':'boss'},
        {'canonicalId':131,'level':14,'wave':20,'role':'boss'},{'canonicalId':132,'level':15,'wave':20,'role':'boss'}],
      'towerValues':[
        {'id':i+1,'power':v[0],'CD':v[1],'radius':v[2],'prices':v[3],'effectValue':v[4],
         'canAttackAir':0 if 3<=i<6 else 1,'searchIntervalMs':100}
        for i,v in enumerate([(6,400,3,25,0),(14,400,3,40,0),(24,300,4,65,0),
            (14,1000,3,45,0),(28,900,3,60,0),(45,800,4,100,0),
            (0,400,3,35,.25),(0,400,3,50,.35),(0,400,4,80,.45)])],
      'rating':{'twoStarHpPermille':500,'threeStarHpPermille':750,'fourStarHpPermille':900,
        'maxFourStarLeaks':2,'fourStarTimePermille':1250},
      'maps':{'expandTutorial':True,'sparseObstacles':True,'longAirCorridors':True},'overrides':[]}

def source_hashes():
    paths=[DATA/(v+'.xlsx') for v in TABLE_FILES.values()]
    paths += [DATA/'__tables__.xlsx',DATA/'Localization.xlsx',DEFAULT_RECIPE,MANIFEST,STATE]
    paths += [DESIGN/'baseline_data.json',DESIGN/'balance_localization.json',DESIGN/'monster_measurements.json']
    paths += list((ROOT/'Luban/Config/Defines').glob('*.xml'))
    paths += list((ROOT/'Luban/Tools/Luban.ClientServer/Templates/config/cs_unity_json').glob('*.tpl'))
    paths += [pathlib.Path(__file__).resolve()]
    paths += list((ROOT/'Assets/ConfigJson').glob('*.json'))
    paths += list((ROOT/'Assets/Gen').glob('*.cs'))
    return {str(p.relative_to(ROOT)).replace('\\','/'):file_hash(p) for p in sorted(paths)}

def available(recipe,L,w,role):
    return [u['canonicalId'] for u in recipe['unlockSchedule'] if u['role']==role and
            (L,w)>=(u['level'],u['wave'])]

def composition(recipe,L,w,n):
    """Fixed schedule, exact slots, no runtime randomness. New mechanics arrive one at a time."""
    slots=[]
    # First four waves always small ground, including later campaign levels.
    final_wave=dimensions(recipe)[1]
    # L1 flying schedule (v6, user-authorized 2026-10-20): first flying at W3,
    # ~13% of each wave (12-20% overall), rotated over the unlocked air pool.
    air=(0 if w<3 else max(1,math.floor(n*.13))) if L==1 else (0 if w<=5 or w in (11,16) else max(1,math.floor(n*(.08 if w<=10 else .12))))
    if w==final_wave:air=min(air,math.floor(n*.2))
    pool=available(recipe,L,w,'air')
    for i in range(air): slots.append((pool[(w+i)%len(pool)],'air'))
    if w==final_wave:
        bosses=available(recipe,L,w,'boss')
        slots.append((bosses[-1] if bosses else 123,'boss' if bosses else 'elite'))
    elif w in (15,20) and L>=5: slots.append((available(recipe,L,w,'heavy')[-1],'elite'))
    for role,ratio,start in [('heavy',.10,11),('fast',.12,6),('medium',.15,5),('swarm',.28,3)]:
        pool=available(recipe,L,w,role)
        if not pool or w<start:continue
        cnt=max(1,math.floor(n*ratio))
        for i in range(min(cnt,max(0,n-len(slots)-1))):slots.append((pool[(L+w+i)%len(pool)],role))
    pool=available(recipe,L,w,'normal')
    while len(slots)<n:slots.append((pool[(len(slots)+w)%len(pool)],'normal'))
    # New unlocked resource appears on its stated first wave even if rotation did not select it.
    for unlock in recipe['unlockSchedule']:
        if (L,w)==(unlock['level'],unlock['wave']):
            pair=(unlock['canonicalId'],unlock['role'])
            if pair not in slots:
                idx=next((i for i,s in enumerate(slots) if s[1]==unlock['role']),len(slots)-1)
                slots[idx]=pair
    # Spread roles through the train. Boss replaces a guard at the end, never adds to count.
    slots.sort(key=lambda t:(ROLE_ORDER.index(t[1]),t[0]))
    ordered=[]
    bins=collections.defaultdict(list)
    for p in slots:bins[p[1]].append(p)
    while any(bins.values()):
        for r in ROLE_ORDER:
            if bins[r]: ordered.append(bins[r].pop(0))
    return ordered

def override_rank(o):
    return {'global':0,'level':1,'range':2,'wave':3}[o.get('scope','global')]
def applies(o,L,w):
    scope=o.get('scope','global')
    if scope=='global':return True
    if o.get('levelId')!=L:return False
    return scope=='level' or (o.get('waveStart',o.get('waveOrdinal',1))<=w<=o.get('waveEnd',o.get('waveOrdinal',2147483647)))
def override_value(values,key,o):
    if o.get('mode','replace')=='multiply':
        if not isinstance(values.get(key),(int,float)): raise ValueError('Cannot multiply '+key)
        values[key]*=o['value']
    else:values[key]=copy.deepcopy(o['value'])

def apply_overrides(values,recipe,profile,L,w,target):
    sources={}
    matches=[o for o in recipe.get('overrides',[]) if o.get('target','wave')==target and
      o.get('profileId',profile)==profile and applies(o,L,w)]
    for rank in range(4):
        seen={}
        for o in [x for x in matches if override_rank(x)==rank]:
            key=o['field']
            if key in seen:raise ValueError(f'Overlapping {target}.{key} overrides at L{L} W{w}: {seen[key]} / {o.get("id")}')
            if key not in values:raise ValueError('Unsupported override field '+target+'.'+key)
            seen[key]=o.get('id','unnamed');override_value(values,key,o)
            sources[key]={'id':o.get('id','unnamed'),'scope':o.get('scope','global'),'mode':o.get('mode','replace'),'value':values[key]}
    return sources

def path_for(cells,blocked=()):
    rows=len(cells);cols=len(cells[0]);start=next(((x,y) for y,r in enumerate(cells) for x,c in enumerate(r) if c=='S'),None)
    end=next(((x,y) for y,r in enumerate(cells) for x,c in enumerate(r) if c=='E'),None)
    if start is None or end is None:return []
    blocked=set(blocked);q=collections.deque([start]);parents={start:None}
    while q:
        p=q.popleft()
        if p==end:
            out=[]
            while p is not None:out.append(p);p=parents[p]
            return out[::-1]
        for dx,dy in ((1,0),(0,1),(-1,0),(0,-1)):
            n=(p[0]+dx,p[1]+dy)
            if 0<=n[0]<cols and 0<=n[1]<rows and cells[n[1]][n[0]] not in '#X' and n not in blocked and n not in parents:
                parents[n]=p;q.append(n)
    return []

def make_maps(baseline,recipe):
    maps=copy.deepcopy(baseline['tblevelmap'])
    for definition in recipe.get('mapDefinitions',[]):
        existing=next((m for m in maps if m['id']==definition['id']),None)
        if existing is None:
            existing=copy.deepcopy(maps[-1]);existing.update(id=definition['id'],levelId=definition['id']);maps.append(existing)
        existing.update(copy.deepcopy(definition))
        existing.update(rows=len(existing['cells']),cols=len(existing['cells'][0]))
    maps=[m for m in maps if m['levelId']<=dimensions(recipe)[0]]
    for m in maps:
        L=m['levelId']
        if L==1 and recipe.get('maps',{}).get('expandTutorial'):
            m.update(cols=13,rows=7,cells=['.'*13]*3+['S'+'.'*11+'E']+['.'*13]*3)
        if 6<=L<=10 and recipe.get('maps',{}).get('sparseObstacles'):
            cells=[list(r) for r in m['cells']]
            for x,y in [(5,2),(5,3),(10,5),(10,6)]:
                if y<len(cells) and x<len(cells[0]) and cells[y][x]=='.':cells[y][x]='#'
            candidate=[''.join(r) for r in cells]
            if path_for(candidate):m['cells']=candidate
        if L in [14,15] and recipe.get('maps',{}).get('longAirCorridors'):
            cells=[list(r.replace('S','.').replace('E','.')) for r in m['cells']]
            mid=len(cells)//2;cells[mid][0]='S';cells[mid][-1]='E';m['cells']=[''.join(r) for r in cells]
        apply_overrides(m,recipe,recipe['_profile'],L,1,'map')
        m['cols']=positive_int(m['cols'],'map cols');m['rows']=positive_int(m['rows'],'map rows')
        counts=collections.Counter(''.join(m['cells']))
        m['desc']=f'M{L} {m["cols"]}x{m["rows"]}; obstacles={counts["#"]+counts["X"]}; no-build={counts["P"]}; open-route building'
    return maps

def load_measurements():
    p=DESIGN/'monster_measurements.json'
    if not p.exists():p=ROOT/'Library/BalanceWorkbench/monster_measurements.json'
    raw=read_json(p,[])
    if isinstance(raw,dict):raw=raw.get('monsters',raw.get('measurements',raw.get('data',[])))
    return {r['resName']:r for r in raw}


def seconds_to_ms(seconds):
    value=float(seconds)
    if not math.isfinite(value):raise ValueError('Non-finite evidence time')
    return math.floor(value*1000+.5) if value>=0 else -math.floor(-value*1000+.5)


def unity_trajectory_finished(record):
    return record.get('state')=='finished' and not any(record.get(k) for k in
      ['pendingOperations','operationError','exception','error']) and bool(record.get('operations'))


def bind_calibration_evidence(plan):
    """Apply derived status only after plan hashing, so evidence never hashes itself.

    The authoritative star decision is emitted by Unity's sole C# evaluator. This
    reader checks identity and completeness, rather than maintaining another score.
    """
    paths=plan['recipe'].get('calibrationEvidence',[])
    if isinstance(paths,str):paths=[paths]
    matched={};rejected=[]
    ratings={r['id']:r for r in plan['tables']['tblevelrating']}
    for value in paths:
        path=pathlib.Path(value)
        if not path.is_absolute():path=ROOT/path
        if not path.is_file():raise ValueError('Calibration evidence not found '+str(path))
        try:key=str(path.relative_to(ROOT)).replace('\\','/')
        except ValueError:key=str(path)
        plan['sourceHashes'][key]=file_hash(path)
        payload=read_json(path)
        records=payload if isinstance(payload,list) else payload.get('results',[])
        for index,record in enumerate(records):
            L=record.get('levelId');rating=ratings.get(L)
            if not rating or record.get('profileId')!=plan['profileId']:continue
            metrics=record.get('metrics',{});profile=record.get('profile',{})
            reasons=[]
            if not unity_trajectory_finished(record):reasons.append('unfinished_operations')
            if not str(record.get('coverage','')).startswith('Unity PlayMode'):reasons.append('not_unity_playmode')
            if not (record.get('valid') is True and record.get('stars')==5 and record.get('fiveStarConditions') is True):reasons.append('not_valid_csharp_five_star')
            if not (record.get('victory') is True and metrics.get('victory') is True):reasons.append('not_victory')
            for key in ['profileId','profileRevision','balanceRevision','ratingRevision','planHash']:
                if str(profile.get(key,''))!=str(rating[key]) or str(metrics.get(key,''))!=str(rating[key]):reasons.append('identity_'+key)
            if metrics.get('statisticsValid') is not True or metrics.get('timingValid') is not True or metrics.get('debugOverride') is not False:reasons.append('invalid_evidence_flags')
            expected_waves=rating['expectedWaveCount']
            if metrics.get('expectedWaveCount')!=expected_waves or metrics.get('completedWaveCount')!=expected_waves:reasons.append('incomplete_wave_count')
            total=rating['expectedEnemyCount']
            if metrics.get('expectedEnemyCount')!=total or metrics.get('successfulSpawned')!=total or metrics.get('killed')!=total or metrics.get('leaked')!=0:reasons.append('incomplete_enemy_inventory')
            waves=metrics.get('waves',[])
            if len(waves)!=expected_waves or [w.get('ordinal') for w in waves]!=list(range(1,expected_waves+1)):
                reasons.append('incomplete_wave_evidence')
            elif any(w.get('successfulSpawned')!=w.get('expected') or w.get('killed')!=w.get('expected') or w.get('leaked')!=0 for w in waves):
                reasons.append('incomplete_wave_inventory')
            if len(waves)==expected_waves:
                previous_combat=previous_level=0.0
                for ordinal,actual in enumerate(waves,1):
                    expected=next(w for w in plan['waves'] if w['levelId']==L and w['waveOrdinal']==ordinal)['count']
                    if actual.get('expected')!=expected:reasons.append('wave_plan_count_mismatch')
                    try:
                        start=float(actual['combatStartSeconds']);end=float(actual['combatEndSeconds']);level_end=float(actual['levelEndSeconds'])
                        if not all(math.isfinite(t) for t in [start,end,level_end]) or start<previous_combat-1e-6 or end<start or level_end<previous_level or level_end<end:
                            reasons.append('invalid_wave_time')
                        previous_combat=end;previous_level=level_end
                    except (KeyError,TypeError,ValueError):reasons.append('invalid_wave_time')
                try:
                    combat=float(metrics['combatElapsedSeconds']);elapsed=float(metrics['levelElapsedSeconds'])
                    if not math.isfinite(combat) or not math.isfinite(elapsed) or combat<=0 or elapsed<combat or abs(combat-previous_combat)>1e-5 or abs(elapsed-previous_level)>1e-5:
                        reasons.append('invalid_run_time')
                except (KeyError,TypeError,ValueError):reasons.append('invalid_run_time')
            if reasons:
                rejected.append({'path':str(path),'recordIndex':index,'levelId':L,'reasons':sorted(set(reasons))});continue
            witness={'path':str(path),'recordIndex':index,'runId':metrics.get('runId'),
              'strategy':record.get('strategy'),'combatElapsedMs':seconds_to_ms(metrics['combatElapsedSeconds']),
              'levelElapsedMs':seconds_to_ms(metrics['levelElapsedSeconds']),'planHash':rating['planHash'],
              'state':record['state'],'fundingPolicy':record.get('fundingPolicy'),'pendingOperationCount':len(record.get('pendingOperations') or [])}
            current=matched.get(L)
            if current is None or witness['combatElapsedMs']<current[0]['combatElapsedMs']:matched[L]=(witness,waves)
    for L,(witness,actual_waves) in matched.items():
        ratings[L]['calibrationStatus']='verified_unity_reference'
        level=next(row for row in plan['levels'] if row['levelId']==L)
        level.update(calibrationStatus='verified_unity_reference',unityReference=witness,unityStars=5,unityLeaked=0,
          unityMeasuredCombatMs=witness['combatElapsedMs'],unityMeasuredLevelMs=witness['levelElapsedMs'])
        for wave in [row for row in plan['waves'] if row['levelId']==L]:
            actual=actual_waves[wave['waveOrdinal']-1]
            wave.update(calibrationStatus='verified_unity_reference',unityMeasuredCombatMs=seconds_to_ms(actual['combatEndSeconds']-actual['combatStartSeconds']),
              unityLeaked=actual['leaked'],unityStars=5,unityRunId=witness['runId'],unitySuccessfulSpawned=actual['successfulSpawned'],
              unityKilled=actual['killed'],unityBalance=actual['gold'],unityHp=actual['hp'],unityPeakAlive=actual['peakAlive'])
    plan['calibrationEvidence']={'verifiedLevelIds':sorted(matched),'rejectedRecords':rejected,
      'pendingLevelIds':[L for L in ratings if L not in matched]}
    return plan

def generate(recipe,profile_id,manifest=None):
    baseline=read_json(DESIGN/'baseline_data.json'); recipe=copy.deepcopy(recipe);recipe['_profile']=profile_id
    profile=next((p for p in recipe['profiles'] if p['id']==profile_id),None)
    if not profile:raise ValueError('Unknown profile '+profile_id)
    f=recipe['formula'];roles=recipe['roles'];proto={r['id']:r for r in baseline['tbenemydata']}
    manifest=copy.deepcopy(manifest or read_json(MANIFEST,{'schemaVersion':1,'profiles':{},'variants':{}}))
    for idx in range(8):manifest['profiles'].setdefault(f'D{idx+1:02}',idx)
    if profile_id not in manifest['profiles']:manifest['profiles'][profile_id]=len(manifest['profiles'])
    pidx=manifest['profiles'][profile_id]
    level_count,wave_count,per_tier=dimensions(recipe)
    manifest=prepare_manifest(manifest,baseline)
    # Reserve additions for all profiles in canonical order before resolving one profile.
    # This makes D01 -> D08 -> D04 identical to generating D04 first.
    for L in range(1,level_count+1):
        for w in range(1,wave_count+1):
            for category in ['rounds','enemyLists']:
                allocate(manifest,category,f'{L}|{w}')
    for preset in sorted(manifest['profiles']):
        for L in range(1,level_count+1):
            for w in range(1,wave_count+1):
                if L<=20 and w<=20:continue
                n=f.get('countLevelCoefficient',1)*L+f.get('countWaveCoefficient',1)*w+f['countOffset']
                for cid,role in sorted(set(composition(recipe,L,w,n))):
                    allocate(manifest,'variants',f'{preset}|{L}|{w}|{cid}|{role}')
    maps=make_maps(baseline,recipe)
    towers=copy.deepcopy(baseline['tbtowerinfo'])
    for t in towers:
        t.update(next(v for v in recipe['towerValues'] if v['id']==t['id']))
        # Tower-specific targetId avoids the ambiguous wave target id.
        ov=[o for o in recipe.get('overrides',[]) if o.get('target')=='tower' and o.get('targetId')==t['id'] and o.get('profileId',profile_id)==profile_id]
        seen=set()
        for o in ov:
            if o['field'] in seen:raise ValueError('Overlapping tower overrides '+str(t['id']))
            seen.add(o['field']);override_value(t,o['field'],o)
        for k in ['power','prices','searchIntervalMs','canAttackAir']:
            if int(t[k])!=t[k]:raise ValueError(f'Tower {t["id"]} {k} does not accept fractional values')
        if float(t['radius'])<=0:raise ValueError(f'Tower {t["id"]} radius must be positive')
        total=sum(x['prices'] for x in towers if x['type']==t['type'] and x['level']<=t['level'])
        t['sellPrice']=math.floor(total*.7);t['desc']=f'Incremental cost {t["prices"]}; cumulative {total}; '+('slow aura; DPS=0' if t['type']==3 else f'continuous theoretical DPS={t["power"]*1000/t["CD"]:.6g}')
    measurements=load_measurements()
    waves=[];variants=[];rounds=[];lists=[];levels=copy.deepcopy(baseline['tbsceneinfo']);ratings=[]
    for L in range(len(levels)+1,level_count+1):
        template=copy.deepcopy(levels[-1]);template.update(id=L,mapId=L,name=f'Level {L}',RoundList=[]);levels.append(template)
    levels=[level for level in levels if level['id']<=level_count]
    budgets={};variant_lookup={};level_reports=[]
    for L in range(1,level_count+1):
        stage=1+(L-1)//per_tier;gold=max(1,round_up((f['initialGold']+f['goldPerLevel']*(L-1))*profile['goldMultiplier']))
        level_values={'initialGold':gold,'initialHp':f['initialHp']}
        level_sources=apply_overrides(level_values,recipe,profile_id,L,1,'level')
        level_waves=[]
        for w in range(1,wave_count+1):
            n=f.get('countLevelCoefficient',1)*L+f.get('countWaveCoefficient',1)*w+f['countOffset'];x=w-1
            raw=Decimal(str(n))*Decimal(str(f['baseEhpPerUnit']))*(1+Decimal(str(f['levelEhpGrowth']))*(L-1))*(1+Decimal(str(f['waveLinear']))*x+Decimal(str(f['waveQuadratic']))*x*x)
            raw*=Decimal(str(f['finalMultiplier'] if w==wave_count else f['pressureMultiplier'] if w%5==0 else 1))
            candidates=[raw]
            for k in [(L,w-1),(L-1,w)]:
                if k in budgets:candidates.append((budgets[k]*Decimal(str(f['minBudgetGrowth']))).to_integral_value(rounding=ROUND_CEILING))
            budgets[L,w]=max(candidates)
            gap=max(f['minSpawnMs'],min(f['maxSpawnMs'],f['spawnBaseMs']-f['spawnWaveReductionMs']*x-f['spawnLevelReductionMs']*(L-1)))
            v={'count':n,'targetEhp':float(budgets[L,w])*profile['ehpMultiplier'],
                'spawnIntervalMs':max(100,min(1500,round_up(gap*profile['gapMultiplier']))),
                'speedMultiplier':profile['speedMultiplier'],'rewardGold':round_up((f['rewardBase']+x//f['rewardWaveBlock']*f.get('rewardBlockIncrement',1))*profile['goldMultiplier']),
               'roleRatios':{},'composition':[], 'hpOverrides':{}}
            sources=apply_overrides(v,recipe,profile_id,L,w,'wave')
            n=positive_int(v['count'],f'L{L} W{w} count');v['spawnIntervalMs']=positive_int(v['spawnIntervalMs'],'spawnIntervalMs')
            positive_int(v['rewardGold'],'rewardGold')
            if v['targetEhp']<=0 or v['speedMultiplier']<=0:raise ValueError(f'Nonpositive EHP/speed L{L} W{w}')
            slots=composition(recipe,L,w,n)
            if v['composition']:
                slots=[]
                for c in v['composition']:
                    slots += [(positive_int(c['canonicalEnemyId'],'canonicalEnemyId'),c['role'])]*positive_int(c['count'],'composition count')
                if len(slots)!=n:raise ValueError(f'Composition count mismatch L{L} W{w}')
            if v['roleRatios']:
                if v['composition']:raise ValueError('roleRatios and explicit composition conflict')
                slots=[]
                if sum(v['roleRatios'].values())>1:raise ValueError('Role ratios sum above 1')
                for role,ratio in v['roleRatios'].items():
                    pool=available(recipe,L,w,role)
                    if not pool and ratio>0:raise ValueError(f'Role {role} unavailable L{L} W{w}')
                    slots += [(pool[i%len(pool)],role) for i in range(math.floor(n*ratio))]
                slots += [(available(recipe,L,w,'normal')[0],'normal')]*(n-len(slots))
            q=sum(roles[r]['weight'] for _,r in slots)
            grouped=collections.Counter(slots);comps=[];enemy_ids=[]
            for (cid,role),cnt in sorted(grouped.items()):
                if cid not in proto or role not in roles:raise ValueError('Unknown canonical/role')
                unlocks=[u for u in recipe['unlockSchedule'] if u['canonicalId']==cid]
                if not unlocks or (L,w)<min((u['level'],u['wave']) for u in unlocks):
                    raise ValueError(f'Resource {cid} is not unlocked at L{L} W{w}')
                if role=='boss' and (L<12 or w!=wave_count):raise ValueError('Bosses unlock only in final waves from level 12')
                if L==1 and w<3 and role=='air':raise ValueError('First flying mechanic is L1 W3')
                key=f'{profile_id}|{L}|{w}|{cid}|{role}'
                legacy_id=100000+pidx*1000000+(L-1)*40000+(w-1)*2000+cid*8+ROLE_ORDER.index(role) if pidx<9 and L<=20 and w<=20 else None
                vid=allocate(manifest,'variants',key,legacy_id)
                if vid in proto:raise ValueError('Variant ID conflicts with existing original')
                # Reward is denominated in *base* EHP (before profile.ehpMultiplier) so that
                # easier profiles keep their gold multiplier instead of inheriting the HP cut.
                base_hp=float(budgets[L,w])*roles[role]['weight']/q*(1-roles[role]['armor'])
                gpe=float(f.get('goldPerEhp',0) or 0)
                reward_value=(max(1,round_up(base_hp*gpe*profile['goldMultiplier'])) if gpe>0
                    else max(1,round_up(roles[role]['reward']*profile['goldMultiplier'])))
                r=roles[role];e=copy.deepcopy(proto[cid]);e.update(id=vid,hp=v['targetEhp']*r['weight']/q*(1-r['armor']),
                    speed=r['speed']*(1+f['speedLevelGrowth']*(L-1)+f['speedWaveGrowth']*x)*v['speedMultiplier'],
                    armor=r['armor'],reward=reward_value,damageToPlayer=r['damage'],type=r['type'],isFlying=int(role=='air'),
                    scale=.5,bodyRadius=.4,desc=f'Balance variant; canonical={cid}; role={role}; profile={profile_id}; level={L}; wave={w}')
                if role=='air' and not proto[cid].get('isFlying'):raise ValueError(f'{cid} has no validated flight identity')
                if role=='boss':
                    m=measurements.get(e['resName'])
                    maxsize=(m.get('maxSide',m.get('maxSize',max(m['width'],m['height']))) if m else None)
                    # Measurements use configScale=.5; preserve prefab root scale exactly.
                    e['scale']=(3.2+.1*min(3,cid-129))/maxsize*float(m.get('configScale',.5)) if maxsize else {129:.95,130:.945,131:.974,132:.556}.get(cid,.5)
                    e['bodyRadius']=.6
                if str(cid) in v['hpOverrides']:
                    e['hp']=float(v['hpOverrides'][str(cid)])
                    # EHP remains a single target: inconsistent individual overrides block apply.
                if e['hp']<=0 or e['speed']<=0 or not 0<=e['armor']<1:raise ValueError('Invalid variant values')
                variants.append(e);variant_lookup[vid]=e
                comps.append({'canonicalEnemyId':cid,'variantId':vid,'role':role,'count':cnt,'hp':e['hp'],'speed':e['speed'],
                    'armor':e['armor'],'reward':e['reward'],'scale':e['scale'],'resName':e['resName']})
            pair_id={(c['canonicalEnemyId'],c['role']):c['variantId'] for c in comps}
            enemy_ids=[pair_id[p] for p in slots]
            actual=sum(variant_lookup[i]['hp']/(1-variant_lookup[i]['armor']) for i in enemy_ids)
            if abs(actual-v['targetEhp'])/v['targetEhp']>.005:raise ValueError(f'Single HP override conflicts with wave EHP L{L} W{w}: actual {actual}, target {v["targetEhp"]}')
            rid=manifest['rounds'][f'{L}|{w}'];list_id=manifest['enemyLists'][f'{L}|{w}']
            wave={'profileId':profile_id,'levelId':L,'waveOrdinal':w,'roundId':rid,'enemyListId':list_id,
              'count':n,'targetEhp':v['targetEhp'],'actualEhp':actual,'spawnIntervalMs':v['spawnIntervalMs'],
              'rewardGold':int(v['rewardGold']),'killGold':sum(variant_lookup[i]['reward'] for i in enemy_ids),
              'composition':comps,'enemyIds':enemy_ids,'overrideSources':sources,
              'flyingCount':sum(c['count'] for c in comps if c['role']=='air'),
              'heavyCount':sum(c['count'] for c in comps if c['role']=='heavy'),
              'eliteCount':sum(c['count'] for c in comps if c['role']=='elite'),
              'bossCount':sum(c['count'] for c in comps if c['role']=='boss'),
              'plannedSpawnSpanMs':(n-1)*v['spawnIntervalMs'],
              'unityMeasuredCombatMs':None,'unityLeaked':None,'unityStars':None,'calibrationStatus':'pending_unity_reference'}
            desc=f'L{L} W{w}/{wave_count}; N={n}; EHP={actual:.6f}; '+','.join(f'{c["role"]}:{c["canonicalEnemyId"]}x{c["count"]}' for c in comps)
            lists.append({'id':list_id,'EnemyIndexs':enemy_ids,'interval':0,'enemyInterval':v['spawnIntervalMs'],'desc':desc})
            rounds.append({'id':rid,'EnemyIndexs':[list_id],'interval':0,'name':f'第 {w}/{wave_count} 波','rewardGold':int(v['rewardGold'])})
            waves.append(wave);level_waves.append(wave)
        level=next(z for z in levels if z['id']==L)
        level.update(RoundList=[wave['roundId'] for wave in level_waves],initialGold=positive_int(level_values['initialGold'],'initialGold'),
          initialHp=positive_int(level_values['initialHp'],'initialHp'),difficulty=stage,waveIntervalMs=f['autoNextRoundDelayMs'])
        m=next(z for z in maps if z['id']==level['mapId']);level['desc']=m['desc']+f'; stage={stage}; preset={profile["name"]}; {wave_count} clearable waves'
        combat_basis={'profile':profile,'level':level,'waves':level_waves,'map':m,'towers':towers,
            'bullets':recipe.get('bulletValues',[]),'globalTiming':{k:f[k] for k in ['autoNextRoundDelayMs','autoStartRoundDelayMs']}}
        basis_hash=digest(combat_basis)
        par=5000*math.ceil(sum(z['plannedSpawnSpanMs']+f['tailBaseMs']+f['tailTierGrowthMs']*(stage-1) for z in level_waves)/5000)
        timing=recipe.get('parCalibration',{}).get(profile_id,{}).get(str(L),{})
        timing_matches=bool(timing and timing.get('combatBasisHash')==basis_hash)
        if timing_matches:par=positive_int(timing['parCombatTimeMs'],'parCombatTimeMs')
        rating={'id':L,'difficultyTier':stage,'profileId':profile_id,'profileRevision':str(profile['revision']),
          'expectedWaveCount':wave_count,'expectedEnemyCount':sum(z['count'] for z in level_waves),**recipe['rating'],
          'parCombatTimeMs':par,'bossVariantIds':sorted(c['variantId'] for z in level_waves for c in z['composition'] if c['role']=='boss'),
          'criticalVariantIds':sorted(c['variantId'] for z in level_waves for c in z['composition'] if c['role'] in ['elite','boss']),
          'balanceRevision':recipe['balanceRevision'],'ratingRevision':recipe['ratingRevision'],
          'calibrationStatus':'pending_unity_reference','runtimeContentHash':''}
        apply_overrides(rating,recipe,profile_id,L,1,'rating')
        # Hash excludes itself and includes everything affecting comparable results.
        rating_for_hash={k:v for k,v in rating.items() if k!='runtimeContentHash'}
        rating['planHash']=digest({'profile':profile,'balanceRevision':recipe['balanceRevision'],'ratingRevision':recipe['ratingRevision'],
          'level':level,'waves':level_waves,'map':m,'towers':towers,'bullets':recipe.get('bulletValues',[]),'rating':rating_for_hash,
          'globalTiming':{k:f[k] for k in ['autoNextRoundDelayMs','autoStartRoundDelayMs']}})
        ratings.append(rating)
        level_reports.append({'levelId':L,'difficultyTier':stage,'initialGold':level['initialGold'],
          'expectedEnemyCount':rating['expectedEnemyCount'],'parCombatTimeMs':rating['parCombatTimeMs'],
          'combatBasisHash':basis_hash,'parCalibrationCurrent':timing_matches,
          'parBasis':timing.get('method') if timing_matches else 'provisional spawn span plus formula tail; uncalibrated',
          'planHash':rating['planHash'],'calibrationStatus':rating['calibrationStatus'],'overrideSources':level_sources})
    glob=copy.deepcopy(baseline['tbglobal']);glob[0].update(autoNextRoundDelayMs=f['autoNextRoundDelayMs'],autoStartRoundDelayMs=f['autoStartRoundDelayMs'],sellRefundRate=1,defaultSearchIntervalMs=100)
    bullets=copy.deepcopy(baseline['tbbulletdata'])
    by_bullet={b['id']:b for b in bullets}
    for value in recipe.get('bulletValues',[]):
        if value['id'] in by_bullet:
            by_bullet[value['id']].update(value)
        else:
            # New rows (e.g. per-level AOE projectiles) are cloned from the base shell
            # so every Luban column stays populated; only declared fields differ.
            shell=copy.deepcopy(next(b for b in bullets if b['id']==2))
            shell.update(id=value['id']);shell.update(value)
            bullets.append(shell);by_bullet[value['id']]=shell
    tables={'tbenemydata':copy.deepcopy(baseline['tbenemydata'])+variants,'tbenemylist':lists,'tbrounddata':rounds,
      'tbsceneinfo':levels,'tbtowerinfo':towers,'tbglobal':glob,'tblevelmap':maps,
      'tbbulletdata':bullets,'tblevelrating':ratings}
    recipe.pop('_profile',None)
    plan={'schemaVersion':1,'profileId':profile_id,'profileName':profile['name'],'customized':any(o.get('profileId',profile_id)==profile_id for o in recipe.get('overrides',[])),
      'levelCount':level_count,'wavesPerLevel':wave_count,'waveCount':level_count*wave_count,'variantCount':len(variants),'recipe':recipe,'tables':tables,'waves':waves,
      'levels':level_reports,'manifest':manifest,'sourceHashes':source_hashes()}
    plan['capacityEconomy']=economy(plan)
    return bind_calibration_evidence(plan)

def validate(plan,export_dir=None):
    level_count,wave_count,per_tier=dimensions(plan['recipe'])
    tables=plan['tables'] if not export_dir else {k:read_json(pathlib.Path(export_dir)/(k+'.json'),[]) for k in plan['tables']}
    errors=[];warnings=[]
    def check(b,msg):
        if not b:errors.append(msg)
    by={k:{r['id']:r for r in rows} for k,rows in tables.items()}
    for k,rows in tables.items():check(len(by[k])==len(rows),'Duplicate IDs '+k)
    check(len(tables['tbsceneinfo'])==level_count,f'Must have {level_count} levels')
    check(len(tables['tbrounddata'])==level_count*wave_count,'Independent round cardinality mismatch')
    check(len(tables['tbenemylist'])==level_count*wave_count,'Independent enemy list cardinality mismatch')
    check(len(tables['tblevelrating'])==level_count,'Rating cardinality mismatch')
    counts={};ehps={};used=[]
    for level in tables['tbsceneinfo']:
        L=level['id'];check(len(level['RoundList'])==wave_count and len(set(level['RoundList']))==wave_count,f'L{L} round cardinality')
        total=0
        for w,rid in enumerate(level['RoundList'],1):
            r=by['tbrounddata'].get(rid);check(bool(r),f'Missing round {rid}')
            if not r:continue
            check(len(r['EnemyIndexs'])==1,f'L{L} W{w} must have 1 list')
            wave=by['tbenemylist'].get(r['EnemyIndexs'][0]);check(bool(wave),f'Missing list {rid}')
            if not wave:continue
            ids=wave['EnemyIndexs'];total+=len(ids);actual=0
            expected=next(z for z in plan['waves'] if z['levelId']==L and z['waveOrdinal']==w)
            check(len(ids)==expected['count'],f'L{L} W{w} count mismatch')
            for eid in ids:
                e=by['tbenemydata'].get(eid);check(bool(e),f'Missing enemy {eid}')
                if not e:continue
                check(e['hp']>0 and e['speed']>0 and 0<=e['armor']<1 and e['reward']>=1,f'Invalid enemy {eid}')
                actual+=e['hp']/(1-e['armor']);used.append(e)
            counts[L,w]=len(ids);ehps[L,w]=actual
            check(abs(actual-expected['targetEhp'])/expected['targetEhp']<=.005,f'L{L} W{w} exported EHP outside .5%')
            check(r['interval']==0 and wave['interval']==0,f'L{L} W{w} must have zero start delays')
        rating=by['tblevelrating'].get(L,{})
        check(rating.get('difficultyTier')==level['difficulty']==1+(L-1)//per_tier,f'L{L} stage mismatch')
        check(rating.get('expectedEnemyCount')==total,f'L{L} expected total mismatch')
        check(rating.get('expectedWaveCount')==wave_count,f'L{L} expected waves mismatch')
        span=sum(z['plannedSpawnSpanMs'] for z in plan['waves'] if z['levelId']==L)
        check(rating.get('parCombatTimeMs',0)>span,f'L{L} Par must exceed spawn span')
        check(rating.get('planHash')==next(z for z in plan['tables']['tblevelrating'] if z['id']==L)['planHash'],f'L{L} rating hash mismatch')
        for key,roles in [('bossVariantIds',['boss']),('criticalVariantIds',['elite','boss'])]:
            expected_ids=sorted(c['variantId'] for z in plan['waves'] if z['levelId']==L for c in z['composition'] if c['role'] in roles)
            check(sorted(rating.get(key,[]))==expected_ids,f'L{L} {key} mismatch')
    for (L,w),n in counts.items():
        for prev in [(L,w-1),(L-1,w)]:
            if prev in counts:
                check(n>counts[prev],f'Count not strictly increasing L{L} W{w} vs {prev}')
                check(ehps[L,w]>ehps[prev],f'EHP not strictly increasing L{L} W{w} vs {prev}')
    res_text=(ROOT/'Assets/Scripts/Core/Res/ResTable.cs').read_text(encoding='utf-8-sig')
    catalog_text=(ROOT/'Assets/Scripts/Data/MonsterCatalog.cs').read_text(encoding='utf-8-sig')
    resources={}
    for e in used:resources[e['resName']]=e
    for name,e in resources.items():
        check((ROOT/'Assets/Prefabs/Enemy'/f'{name}.prefab').is_file(),'Missing prefab '+name)
        check('"'+name+'"' in res_text or ('RegisterMonsters' in res_text and '"'+name.removeprefix('Enemy_')+'"' in catalog_text),'Unregistered prefab '+name)
        if e.get('animController'):check(bool(list((ROOT/'Assets/_Common/Animations').glob(e['animController']+'/**/Controller*'))),'Missing animation '+name)
    for m in tables['tblevelmap']:
        chars=''.join(m['cells']);check(len(m['cells'])==m['rows'] and all(len(r)==m['cols'] for r in m['cells']),f'Map {m["id"]} dimensions')
        check(set(chars)<=set('.PS E#X'.replace(' ','')) and chars.count('S')==1 and chars.count('E')==1,f'Map {m["id"]} characters/S/E')
        check(bool(path_for(m['cells'])),f'Map {m["id"]} disconnected')
    for t in tables['tbtowerinfo']:
        if t['type']==3:check(t['power']==0,f'Slow tower {t["id"]} has damage')
        cumulative=sum(x['prices'] for x in tables['tbtowerinfo'] if x['type']==t['type'] and x['level']<=t['level'])
        check(t['sellPrice']==math.floor(cumulative*.7),f'Tower {t["id"]} sell price')
        check(t['upgradeTo']==(0 if t['level']==3 else t['id']+1),f'Tower {t["id"]} upgrade chain')
        check(t['prices']>0 and t['CD']>0 and t['radius']>0 and t['power']>=0 and 0<=t['effectValue']<1,f'Tower {t["id"]} positive values')
        if t['type']==2:
            bullet=next((b for b in tables['tbbulletdata'] if b['id']==t['bulletId']),None)
            check(bool(bullet) and bullet['aoeRadius']>0,f'Tower {t["id"]} AOE bullet {t["bulletId"]} missing or zero radius')
    if export_dir:
        planned={t['id']:t for t in plan['tables']['tbtowerinfo']}
        for t in tables['tbtowerinfo']:
            p=planned.get(t['id'])
            if not p:continue
            for field in ('radius','bulletId','power','CD','prices','effectValue','canAttackAir','sellPrice'):
                check(t.get(field)==p.get(field),f'Tower {t["id"]} exported {field} differs from resolved plan')
    if export_dir:
        actual_hash=runtime_content_hash(plan,export_dir)
        expected_status={r['id']:r['calibrationStatus'] for r in plan['tables']['tblevelrating']}
        for rating in tables['tblevelrating']:
            check(rating.get('runtimeContentHash')==actual_hash,f'Runtime content hash mismatch L{rating["id"]}')
            check(rating.get('calibrationStatus')==expected_status.get(rating['id']),f'Calibration evidence status mismatch L{rating["id"]}')
    verified=plan.get('calibrationEvidence',{}).get('verifiedLevelIds',[])
    pending=plan.get('calibrationEvidence',{}).get('pendingLevelIds',list(range(1,level_count+1)))
    if pending:warnings.append(f'Hash-matched finished Unity five-star references cover {len(verified)}/{level_count} levels; {len(pending)} remain pending. Static checks do not certify reachability.')
    # Flag individual role changes honestly; aggregate EHP is the hard monotonic invariant.
    prev={};drops=[]
    for z in plan['waves']:
        for c in z['composition']:
            k=(z['levelId'],c['canonicalEnemyId'],c['role']);before=prev.get(k)
            if before and c['hp']<before[1]*.9:drops.append({'levelId':z['levelId'],'waveOrdinal':z['waveOrdinal'],'canonicalId':c['canonicalEnemyId'],'role':c['role'],'previousHp':before[1],'hp':c['hp']})
            prev[k]=(z['waveOrdinal'],c['hp'])
    return {'passed':not errors,'errors':errors,'warnings':warnings,'individualHpDropsOver10Percent':drops,
      'verifiedUnityLevelIds':verified,'pendingUnityLevelIds':pending,
      'checkedLevels':level_count,'checkedWaves':level_count*wave_count,'checkedUniqueResources':len(resources),'exportedJsonChecked':bool(export_dir)}

def same_runtime_value(table,field,before,after):
    if before==after:return True
    if field not in FLOAT_FIELDS.get(table,set()) or not all(isinstance(v,(int,float)) and not isinstance(v,bool) for v in [before,after]):return False
    try:return struct.pack('!f',before)==struct.pack('!f',after)
    except (OverflowError,struct.error):return False


def preview(plan):
    changes=[]
    for table,rows in plan['tables'].items():
        current={r['id']:r for r in read_json(ROOT/'Assets/ConfigJson'/f'{table}.json',[])}
        for row in rows:
            old=current.get(row['id'],{})
            for field,value in row.items():
                # The compiler uses full precision; Luban's float schema serializes
                # float32. Equal runtime values must not bury actual draft changes.
                if table=='tblevelrating' and field=='runtimeContentHash' and not value:continue
                if not same_runtime_value(table,field,old.get(field),value):changes.append({'table':table,'id':row['id'],'field':field,'before':old.get(field),'after':value})
        for rid in current.keys()-{r['id'] for r in rows}:changes.append({'table':table,'id':rid,'field':'__row__','before':'exists','after':None})
    return {k:v for k,v in plan.items() if k not in ['tables','manifest','recipe']}|{'validation':validate(plan),'changes':changes}

def excel_write(stage,plan):
    import openpyxl
    from copy import copy as shallow
    stage=pathlib.Path(stage);stage.mkdir(parents=True,exist_ok=True)
    for p in DATA.glob('*.xlsx'):shutil.copy2(p,stage/p.name)
    for table,rows in plan['tables'].items():
        check_cancel(stage);table_started=time.perf_counter()
        progress('stage_excel_table',table=table,rows=len(rows),completed=0)
        p=stage/(TABLE_FILES[table]+'.xlsx')
        if p.exists():wb=openpyxl.load_workbook(p);ws=wb.active
        else:
            wb=openpyxl.Workbook();ws=wb.active;ws.title='data'
            ws.append(['##']+list(RATING_TYPES));ws.append(['##type']+list(RATING_TYPES.values()));ws.append(['##']+list(RATING_TYPES))
            ws.freeze_panes='C4'
            for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=24
        headers={c.value:c.column for c in ws[1] if c.value}
        max_row=ws.max_row;max_column=ws.max_column;next_row=max_row+1
        template_styles=[shallow(ws.cell(4,c)._style) for c in range(1,max_column+1)] if max_row>=4 else []
        existing={ws.cell(r,headers['id']).value:r for r in range(4,max_row+1) if ws.cell(r,headers['id']).value is not None}
        desired_ids={row['id'] for row in rows}
        free_rows=collections.deque()
        # Only campaign-managed rows are cleared; unrelated prototype fields are untouched.
        if table in ['tbenemydata','tbenemylist','tbrounddata','tblevelrating']:
            free_rows.extend(r for r in range(4,max_row+1) if ws.cell(r,headers['id']).value is None and
              all(ws.cell(r,c).value is None for c in range(1,max_column+1)))
            for rid,r in existing.items():
                if rid not in desired_ids:
                    if table!='tbenemydata' or int(rid)>=100000:
                        for c in range(1,max_column+1):ws.cell(r,c).value=None
                        free_rows.append(r)
        reused=appended=0
        for row_index,row in enumerate(rows):
            if row_index%128==0:check_cancel(stage)
            r=existing.get(row['id'])
            new_row=r is None
            if r is None:
                if free_rows:r=free_rows.popleft();reused+=1
                else:r=next_row;next_row+=1;appended+=1
                for c,style in enumerate(template_styles,1):ws.cell(r,c)._style=shallow(style)
                existing[row['id']]=r
            for field,value in row.items():
                if field not in headers:continue
                if not new_row and table in OWNED_FIELDS and field!='id' and field not in OWNED_FIELDS[table]:continue
                # Preserve all original prototype values, and unknown existing columns.
                if table=='tbenemydata' and row['id']<100000:continue
                if isinstance(value,list):value=('|' if field=='cells' else ',').join(map(str,value))
                if isinstance(value,dict) and all(k in value for k in ['x','y','z']):value=','.join(str(value[k]) for k in ['x','y','z'])
                ws.cell(r,headers[field],value)
        wb.save(p);wb.close()
        progress('stage_excel_table_complete',table=table,completed=len(rows),total=len(rows),reusedRows=reused,appendedRows=appended,elapsedSec=time.perf_counter()-table_started)
    check_cancel(stage)
    p=stage/'__tables__.xlsx';wb=openpyxl.load_workbook(p);ws=wb.active
    if not any(ws.cell(r,2).value=='TBLevelRating' for r in range(4,ws.max_row+1)):
        ws.append(['Level performance rating','TBLevelRating','LevelRating',True,'LevelRating.xlsx'])
    wb.save(p);wb.close()
    p=stage/'Localization.xlsx';wb=openpyxl.load_workbook(p);ws=wb.active
    heads={c.value:c.column for c in ws[1] if c.value};ids={ws.cell(r,heads['id']).value:r for r in range(4,ws.max_row+1)}
    next_row=ws.max_row+1
    for key,zh in read_json(DESIGN/'balance_localization.json',{}).items():
        r=ids.get(key)
        if r is None:r=next_row;next_row+=1;ids[key]=r
        for k,v in {'id':key,'en':key,'zhHans':zh[0],'zhHant':zh[1],'comment':'Balance v1 / five-star rating'}.items():ws.cell(r,heads[k],v)
    wb.save(p);wb.close()

def luban_export(datas,code,data,cache):
    exe=ROOT/'Luban/Tools/Luban.ClientServer/Luban.ClientServer.exe'
    if not exe.is_file():raise RuntimeError('Missing Luban executable '+str(exe))
    args=[str(exe),'-j','cfg','-c',str(cache),'--','-d',str(ROOT/'Luban/Config/Defines/__root__.xml'),
      '--input_data_dir',str(datas),'--output_code_dir',str(code),'--output_data_dir',str(data),
      '--gen_types','code_cs_unity_json,data_json','-s','all']
    env=os.environ.copy();env['DOTNET_ROLL_FORWARD']='LatestMajor'
    result=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    pathlib.Path(cache).with_suffix('.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Luban failed; see '+str(pathlib.Path(cache).with_suffix('.log'))+'\n'+result.stdout[-6000:])
    # Luban's template emits trailing spaces in Tables.cs. Normalize staged code
    # here so every export path stays reproducible and Gen is never hand-edited.
    for generated in pathlib.Path(code).glob('*.cs'):
        raw=generated.read_bytes();original=raw.decode('utf-8-sig')
        normalized='\n'.join(line.rstrip() for line in original.splitlines())+'\n'
        if normalized.encode('utf-8')!=raw:generated.write_text(normalized,encoding='utf-8',newline='\n')
    for table in TABLE_FILES:
        if not (pathlib.Path(data)/(table+'.json')).is_file():raise RuntimeError('Missing staged output '+table)

def runtime_content_hash(plan,export_dir):
    parts=[]
    for key in ['tbenemydata','tbenemylist','tbrounddata','tbsceneinfo','tblevelmap','tbtowerinfo','tbbulletdata','tbglobal']:
        parts.append(key+'\n'+(pathlib.Path(export_dir)/(key+'.json')).read_text(encoding='utf-8-sig')+'\n')
    fields=['id','difficultyTier','profileId','profileRevision','expectedWaveCount','expectedEnemyCount',
      'twoStarHpPermille','threeStarHpPermille','fourStarHpPermille','maxFourStarLeaks','fourStarTimePermille',
      'parCombatTimeMs','bossVariantIds','criticalVariantIds','balanceRevision','ratingRevision','planHash']
    for r in sorted(plan['tables']['tblevelrating'],key=lambda r:r['id']):
        parts.append('|'.join(','.join(map(str,r[k])) if isinstance(r[k],list) else str(r[k]) for k in fields)+'\n')
    return hashlib.sha256(''.join(parts).encode('utf-8')).hexdigest()

def write_rating_excel(path,rows):
    import openpyxl
    wb=openpyxl.load_workbook(path);ws=wb.active;heads={c.value:c.column for c in ws[1] if c.value}
    for row in rows:
        rr=next(r for r in range(4,ws.max_row+1) if ws.cell(r,heads['id']).value==row['id'])
        ws.cell(rr,heads['runtimeContentHash'],row['runtimeContentHash'])
    wb.save(path);wb.close()

@contextmanager
def job_lock():
    JOBS.mkdir(parents=True,exist_ok=True);p=JOBS/'apply.lock'
    if p.exists():
        try:pid=int(p.read_text())
        except (ValueError,OSError):raise RuntimeError('Unreadable apply lock; inspect '+str(p))
        if os.name=='nt':
            import ctypes
            handle=ctypes.windll.kernel32.OpenProcess(0x1000,False,pid)
            active=False
            if handle:
                status=ctypes.c_ulong();ctypes.windll.kernel32.GetExitCodeProcess(handle,ctypes.byref(status));active=status.value==259;ctypes.windll.kernel32.CloseHandle(handle)
        else:
            try:os.kill(pid,0);active=True
            except ProcessLookupError:active=False
        if active:raise RuntimeError('Another active application owns '+str(p))
        # Only an exited task's lock is released. Journal recovery runs under our new lock.
        p.unlink()
    try:fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:raise RuntimeError('Another application acquired '+str(p))
    os.write(fd,str(os.getpid()).encode());os.close(fd)
    try:
        # A prior recovery may have been blocked by external edits after its stale lock
        # was removed. Never let a second attempt silently bypass that journal.
        for jp in JOBS.glob('*/transaction.json'):
            journal=read_json(jp)
            if journal.get('phase') not in ['prepared','committing','rollback_blocked']:continue
            restore_transaction(journal)
            journal['phase']='rolled_back';write_json(jp,journal)
            progress('recovered_interrupted_transaction',jobId=journal['jobId'])
        yield
    finally:p.unlink(missing_ok=True)

def restore_transaction(journal):
    conflicts=[e['path'] for e in journal['entries'] if file_hash(ROOT/e['path']) not in [e['before'],e['after']]]
    if conflicts:raise RuntimeError('External modifications block rollback: '+', '.join(conflicts))
    for e in reversed(journal['entries']):
        dst=ROOT/e['path']
        if file_hash(dst)==e['before']:continue
        if e['backup']:
            # Windows can keep the destination memory-mapped after Luban/Unity
            # reads it. Replacing a staged file avoids truncating that live map.
            temporary=dst.with_name(dst.name+'.rollback-'+uuid.uuid4().hex+'.tmp')
            try:
                shutil.copy2(e['backup'],temporary)
                if file_hash(dst) not in [e['before'],e['after']]:
                    raise RuntimeError('External modification during rollback: '+e['path'])
                os.replace(temporary,dst)
            finally:temporary.unlink(missing_ok=True)
        elif file_hash(dst)==e['after']:dst.unlink(missing_ok=True)

def assert_sources(expected):
    changed=[p for p,h in expected.items() if file_hash(ROOT/p)!=h]
    if changed:raise RuntimeError('External source changes detected; regenerate candidate before apply: '+', '.join(changed[:15]))

def check_managed_conflicts():
    state=read_json(STATE)
    if not state:return
    # Compare managed cell values, not xlsx zip timestamps, and require explicit resolution.
    import openpyxl
    conflicts=[]
    for table,rows in state.get('managedRows',{}).items():
        p=DATA/(TABLE_FILES[table]+'.xlsx')
        if not p.exists():conflicts.append(str(p));continue
        wb=openpyxl.load_workbook(p,data_only=True);ws=wb.active;headers={c.value:c.column for c in ws[1] if c.value}
        current={ws.cell(r,headers['id']).value:r for r in range(4,ws.max_row+1)}
        for row in rows:
            r=current.get(row['id'])
            if not r:conflicts.append(f'{table}/{row["id"]} missing');continue
            for k,v in row.items():
                if k not in headers:continue
                expected=('|' if k=='cells' else ',').join(map(str,v)) if isinstance(v,list) else v
                if isinstance(expected,dict) and all(k in expected for k in ['x','y','z']):expected=','.join(str(expected[k]) for k in ['x','y','z'])
                actual=ws.cell(r,headers[k]).value
                if expected in ('',None) and actual in ('',None):continue
                if isinstance(expected,(int,float)) and isinstance(actual,(int,float)) and math.isclose(expected,actual,rel_tol=1e-12,abs_tol=1e-10):continue
                if actual!=expected:conflicts.append(f'{table}/{row["id"]}/{k}')
        wb.close()
    if conflicts:raise RuntimeError('Managed Excel cells changed externally. Import edits as recipe overrides or discard candidate: '+', '.join(conflicts[:30]))

def commit_files(files,jobdir,plan):
    backup=jobdir/'backup';backup.mkdir(parents=True,exist_ok=True)
    entries=[]
    for src,dst in files:
        if dst.exists() and src.read_bytes()==dst.read_bytes():continue
        rel=str(dst.relative_to(ROOT)).replace('\\','/');bp=backup/rel
        if dst.exists():bp.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,bp)
        entries.append({'path':rel,'before':file_hash(dst),'after':file_hash(src),'backup':str(bp) if dst.exists() else None,'source':str(src)})
    journal={'schemaVersion':1,'jobId':jobdir.name,'phase':'prepared','profileId':plan['profileId'],'entries':entries}
    write_json(jobdir/'transaction.json',journal)
    try:
        journal['phase']='committing';write_json(jobdir/'transaction.json',journal)
        for e in entries:
            dst=ROOT/e['path'];dst.parent.mkdir(parents=True,exist_ok=True)
            temp=dst.with_name(dst.name+'.balance-tmp')
            try:
                shutil.copy2(e['source'],temp);os.replace(temp,dst)
            finally:
                temp.unlink(missing_ok=True)
        journal['phase']='committed';write_json(jobdir/'transaction.json',journal)
    except BaseException as error:
        try:
            restore_transaction(journal)
            journal['phase']='rolled_back';write_json(jobdir/'transaction.json',journal)
        except BaseException as recovery_error:
            journal['phase']='rollback_blocked';journal['recoveryError']=str(recovery_error)
            write_json(jobdir/'transaction.json',journal)
            raise RuntimeError('Commit failed and recovery is blocked; inspect '+str(jobdir/'transaction.json')+': '+str(recovery_error)) from error
        raise
    return journal

def apply_plan(plan,out):
    if not validate(plan)['passed']:raise RuntimeError('Candidate validation failed')
    with job_lock():
        check_managed_conflicts();assert_sources(plan['sourceHashes']);check_cancel(out)
        jobdir=pathlib.Path(out);jobdir.mkdir(parents=True,exist_ok=True)
        progress('stage_excel',jobId=jobdir.name)
        excel_write(jobdir/'Datas',plan)
        check_cancel(out)
        progress('stage_luban',jobId=jobdir.name)
        luban_export(jobdir/'Datas',jobdir/'Gen',jobdir/'ConfigJson',jobdir/'luban.cache.meta')
        check_cancel(out)
        content_hash=runtime_content_hash(plan,jobdir/'ConfigJson')
        for r in plan['tables']['tblevelrating']:r['runtimeContentHash']=content_hash
        write_rating_excel(jobdir/'Datas'/'LevelRating.xlsx',plan['tables']['tblevelrating'])
        luban_export(jobdir/'Datas',jobdir/'Gen',jobdir/'ConfigJson',jobdir/'luban.cache.meta')
        result=validate(plan,jobdir/'ConfigJson');write_json(jobdir/'export_validation.json',result)
        if not result['passed']:raise RuntimeError('Staged JSON validation failed: '+canonical(result['errors']))
        assert_sources(plan['sourceHashes']);check_cancel(out)
        # Stage authoritative metadata in same transaction; manifests are not committed during preview.
        write_json(jobdir/'balance_design.json',plan['recipe']);write_json(jobdir/'variant_manifest.json',plan['manifest'])
        write_json(jobdir/'applied_state.json',{'profileId':plan['profileId'],'jobId':jobdir.name,
          'planHashes':{str(r['id']):r['planHash'] for r in plan['tables']['tblevelrating']},
          'ownedFields':{k:sorted(v) for k,v in OWNED_FIELDS.items()},
          'managedRows':{k:[{f:value for f,value in r.items() if k not in OWNED_FIELDS or f=='id' or f in OWNED_FIELDS[k]}
              for r in v if k!='tbenemydata' or r['id']>=100000] for k,v in plan['tables'].items()}})
        files=[(jobdir/'Datas'/(name+'.xlsx'),DATA/(name+'.xlsx')) for name in TABLE_FILES.values()]
        files.append((jobdir/'Datas/__tables__.xlsx',DATA/'__tables__.xlsx'))
        files.append((jobdir/'Datas/Localization.xlsx',DATA/'Localization.xlsx'))
        for name in ['Gen','ConfigJson']:
            for src in (jobdir/name).glob('*'):
                if src.is_file() and src.suffix in ['.cs','.json']:files.append((src,ROOT/'Assets'/name/src.name))
        files += [(jobdir/'balance_design.json',DEFAULT_RECIPE),(jobdir/'variant_manifest.json',MANIFEST),(jobdir/'applied_state.json',STATE)]
        progress('commit',fileCount=len(files),jobId=jobdir.name)
        journal=commit_files(files,jobdir,plan)
        try:
            final=validate(plan,ROOT/'Assets/ConfigJson');write_json(jobdir/'validation.json',final)
            if not final['passed']:raise RuntimeError('Final readback failed: '+canonical(final['errors']))
        except BaseException as error:
            journal['validationError']=str(error)
            try:
                restore_transaction(journal)
                journal['phase']='rolled_back';write_json(jobdir/'transaction.json',journal)
            except BaseException as recovery_error:
                journal['phase']='rollback_blocked';journal['recoveryError']=str(recovery_error)
                write_json(jobdir/'transaction.json',journal)
                raise RuntimeError('Final readback failed and recovery is blocked; inspect '+str(jobdir/'transaction.json')+': '+str(recovery_error)) from error
            raise RuntimeError('Final readback failed; transaction restored: '+jobdir.name) from error
        progress('complete',passed=True,jobId=jobdir.name,transaction=str(jobdir/'transaction.json'))
        return journal

def rollback(path,force=False):
    p=pathlib.Path(path)
    if p.is_dir():p=p/'transaction.json'
    journal=read_json(p)
    if not journal:raise ValueError('Transaction not found '+str(p))
    if journal['phase']=='rolled_back':return journal
    with job_lock():
        restore_transaction(journal)
        journal['phase']='rolled_back';write_json(p,journal)
    return journal

def export_reports(plan,out):
    out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
    write_json(out/'waves.json',plan['waves']);write_json(out/'levels.json',plan['levels'])
    if 'calibrationEvidence' in plan:write_json(out/'calibration_evidence.json',plan['calibrationEvidence'])
    fields=['profileId','levelId','waveOrdinal','count','targetEhp','actualEhp','spawnIntervalMs','killGold','rewardGold','flyingCount','heavyCount','eliteCount','bossCount','plannedSpawnSpanMs','calibrationStatus',
      'unityMeasuredCombatMs','unitySuccessfulSpawned','unityKilled','unityLeaked','unityStars','unityRunId']
    with (out/'waves.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(plan['waves'])
    maps=[]
    for m in plan['tables']['tblevelmap']:
        p=path_for(m['cells']);counts=collections.Counter(''.join(m['cells']))
        reference=plan['recipe'].get('referencePolicy',{})
        maze=read_json(ROOT/reference.get('mazeDirectory','Library/BalanceWorkbench/no-maze')/f'L{m["levelId"]:02}.json')
        if maze and maze.get('mapCells')!=m['cells']:maze=None
        blocked=[(t['col'],t['row']) for t in maze['layout']] if maze else []
        from balance_campaign import runtime_path_for
        from balance_maze import intervals
        route=runtime_path_for(m['cells'],blocked)
        radius=next(t['radius'] for t in plan['tables']['tbtowerinfo'] if t['id']==1)
        maps.append({'levelId':m['levelId'],'cols':m['cols'],'rows':m['rows'],'obstacleCells':counts['#']+counts['X'],
          'noBuildCells':counts['P'],'buildableCells':counts['.'],'emptyShortestPath':p,'emptyPathLength':len(p)-1,
          'exampleLegalTowerCells':blocked,'examplePath':route,'examplePathLength':len(route)-1,
          'exampleSource':'searched legal maze blueprint; actual construction and damage are in Unity replay waveBoundaries',
          'searchKind':maze['searchKind'] if maze else 'no blueprint',
          'coverageZones':[{'cell':c,'radius':radius,'coveragePasses':intervals(c,route,radius),
            'pathCellsCovered':sum((c[0]-x)**2+(c[1]-y)**2<=radius**2 for x,y in route)} for c in blocked]})
    write_json(out/'maps.json',maps)
    baseline=read_json(DESIGN/'baseline_data.json');measurements=load_measurements();first={};selected=collections.defaultdict(set);selected_ids=collections.defaultdict(set)
    for z in plan['waves']:
        for c in z['composition']:
            key=c['resName'];first.setdefault(key,{'levelId':z['levelId'],'waveOrdinal':z['waveOrdinal']});selected[key].add(c['role']);selected_ids[key].add(c['canonicalEnemyId'])
    catalog=[]
    for e in baseline['tbenemydata']:
        if any(r['resName']==e['resName'] for r in catalog):continue
        candidates=[x for x in baseline['tbenemydata'] if x['resName']==e['resName']]
        e=next((x for x in candidates if x['id']>=11 and x['id']<=128),e);m=measurements.get(e['resName'],{})
        catalog.append({'canonicalId':e['id'],'prototypeIds':sorted(x['id'] for x in candidates),'selectedCanonicalIds':sorted(selected_ids[e['resName']]),
          'resName':e['resName'],'name':e['name'],'width':m.get('width'),'height':m.get('height'),
          'maxSize':m.get('maxSide',m.get('maxSize')),'rootScale':m.get('rootScale'),'configScale':m.get('configScale',.5),
          'measurementStatus':'unity_body_bounds' if m else 'pending_measurement','roles':sorted(selected[e['resName']]),
          'firstAppearance':first.get(e['resName']),'selected':e['resName'] in first,'isFlying':bool(e.get('isFlying')),
          'prefabExists':(ROOT/'Assets/Prefabs/Enemy'/(e['resName']+'.prefab')).exists()})
    write_json(out/'monster_catalog_119.json',catalog)
    write_json(out/'capacity_economy.json',economy(plan))
    markdown=[f'# {plan["profileId"]} {plan["profileName"]} · {plan["levelCount"]} 关 × {plan["wavesPerLevel"]} 波',
      '', '本报告由权威配方编译器生成；每个 Round 独立清场。离线预测和真实 Unity 证据分列，未匹配同一 planHash 的实测不认证五星可达。',
      '',f'- 变体数：{plan["variantCount"]}；完整波数：{len(plan["waves"])}。',
      '- 关卡等级 L、战役阶段 I—V、调参预设和本局 1—5 星分别存储。',
      '- `pending_unity_reference` 表示尚无同内容版本的有效真实五星参考；`verified_unity_reference` 仅由完整 Unity 证据绑定。','']
    for level in plan['levels']:
        L=level['levelId'];seq=[w for w in plan['waves'] if w['levelId']==L];rating=next(r for r in plan['tables']['tblevelrating'] if r['id']==L)
        markdown.extend([f'## 第 {L} 关 · 战役阶段 {level["difficultyTier"]}', '',
          f'初始金币 {level["initialGold"]}；敌人数 {level["expectedEnemyCount"]}；五星战斗用时上限 {rating["parCombatTimeMs"]} ms；状态 `{level["calibrationStatus"]}`。',
          '',f'planHash：`{level["planHash"]}`。','',
          '|波|数量|实际 EHP|出怪间隔 ms|击杀金|清场金|飞/重/精/首|Unity 战斗 ms / 漏怪 / 星|编组（角色:原型×数）|',
          '|---:|---:|---:|---:|---:|---:|---|---|---|'])
        for wave in seq:
            comp='; '.join(f'{c["role"]}:{c["canonicalEnemyId"]}×{c["count"]}' for c in wave['composition'])
            actual='待验证' if wave.get('unityStars') is None else f'{wave["unityMeasuredCombatMs"]} / {wave["unityLeaked"]} / {wave["unityStars"]}'
            flags='/'.join(str(wave[k]) for k in ['flyingCount','heavyCount','eliteCount','bossCount'])
            markdown.append(f'|{wave["waveOrdinal"]}|{wave["count"]}|{wave["actualEhp"]:.3f}|{wave["spawnIntervalMs"]}|{wave["killGold"]}|{wave["rewardGold"]}|{flags}|{actual}|{comp}|')
        markdown.append('')
    (out/'report.md').write_text('\n'.join(markdown)+'\n',encoding='utf-8')

def write_candidate(plan,out):
    """Serializable candidate uses the exact runtime schema and independently bound raw JSON hash."""
    out=pathlib.Path(out);data=out/'ConfigJson'
    for p in (ROOT/'Assets/ConfigJson').glob('*.json'):
        if p.stem not in plan['tables']:
            data.mkdir(parents=True,exist_ok=True);shutil.copy2(p,data/p.name)
    for key,rows in plan['tables'].items():write_json(data/(key+'.json'),rows)
    content_hash=runtime_content_hash(plan,data)
    for r in plan['tables']['tblevelrating']:r['runtimeContentHash']=content_hash
    write_json(data/'tblevelrating.json',plan['tables']['tblevelrating'])
    write_json(out/'resolved-plan.json',plan)
    return data

def require_openpyxl():
    import importlib.util
    if importlib.util.find_spec('openpyxl') is None:
        raise RuntimeError('openpyxl is required for excel write/read. Run this command with '
                           'C:/Users/78296/.workbuddy/binaries/python/envs/default/Scripts/python.exe')


def assert_tower_radius_type():
    """The shipped TowerInfo sheet must declare radius as float, otherwise 2.15/2.3 truncate."""
    import openpyxl
    path=DATA/'TowerInfo.xlsx'
    wb=openpyxl.load_workbook(path,read_only=True);ws=wb[wb.sheetnames[0]]
    header=[c.value for c in next(ws.iter_rows(min_row=1,max_row=1))]
    types=[c.value for c in next(ws.iter_rows(min_row=2,max_row=2))]
    try:
        col=header.index('radius')
    except ValueError:
        raise RuntimeError('TowerInfo.xlsx has no radius column')
    declared=str(types[col]).strip()
    if declared!='float':
        raise RuntimeError(f'TowerInfo.xlsx radius type must be float, found {declared!r}')


def stage_export(plan,out):
    """Full export dry run: mirrors apply_plan's two-pass Luban export without touching the project."""
    require_openpyxl();assert_tower_radius_type()
    jobdir=pathlib.Path(out);jobdir.mkdir(parents=True,exist_ok=True)
    datas=jobdir/'Datas';code=jobdir/'Gen';data=jobdir/'ConfigJson'
    progress('stage_excel',jobId=jobdir.name)
    excel_write(datas,plan)
    progress('stage_luban')
    luban_export(datas,code,data,jobdir/'luban.cache.meta')
    content_hash=runtime_content_hash(plan,data)
    for row in plan['tables']['tblevelrating']:row['runtimeContentHash']=content_hash
    write_rating_excel(datas/'LevelRating.xlsx',plan['tables']['tblevelrating'])
    luban_export(datas,code,data,jobdir/'luban.cache.meta')
    result=validate(plan,str(data));write_json(jobdir/'validation.json',result)
    write_json(jobdir/'resolved-plan.json',plan)
    progress('stage_complete',passed=result['passed'],out=str(jobdir),contentHash=content_hash)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['inspect','generate','preview','validate','apply','stage','rollback','simulate','all-profiles','init'])
    parser.add_argument('--profile',default=None);parser.add_argument('--recipe',default=str(DEFAULT_RECIPE));parser.add_argument('--out',default=None)
    parser.add_argument('--plan');parser.add_argument('--dry-run',action='store_true');parser.add_argument('--transaction')
    parser.add_argument('--level-min',type=int,default=1);parser.add_argument('--level-max',type=int,default=None)
    parser.add_argument('--wave-min',type=int,default=1);parser.add_argument('--wave-max',type=int,default=None)
    parser.add_argument('--strategy',default='mixed');parser.add_argument('--step-ms',type=int,default=100)
    parser.add_argument('--step',type=float);parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--all-profiles',action='store_true');parser.add_argument('--backup')
    parser.add_argument('--export-dir')
    args=parser.parse_args(argv);start=time.perf_counter()
    if args.step_ms<=0 or (args.step is not None and (not math.isfinite(args.step) or args.step<=0)):
        parser.error('simulation step must be a positive finite duration')
    if args.command=='init':
        if DEFAULT_RECIPE.exists():raise RuntimeError('Recipe already exists')
        write_json(DEFAULT_RECIPE,default_recipe());return
    if args.command=='rollback':
        result=rollback(args.transaction or args.backup or args.out);progress('complete',result=result);return
    recipe=read_json(args.recipe)
    if not recipe:raise RuntimeError('Recipe not found; run init')
    level_count,wave_count,_=dimensions(recipe)
    args.level_max=args.level_max or level_count;args.wave_max=args.wave_max or wave_count
    if not 1<=args.level_min<=args.level_max<=level_count:parser.error('level range exceeds campaign dimensions')
    if not 1<=args.wave_min<=args.wave_max<=wave_count:parser.error('wave range exceeds campaign dimensions')
    profile=args.profile or recipe['selectedProfileId'];out=pathlib.Path(args.out or JOBS/(args.command+'-'+uuid.uuid4().hex[:12]))
    if args.command=='all-profiles':
        plans=[];manifest=read_json(MANIFEST,{'schemaVersion':1,'profiles':{},'variants':{}})
        for p in recipe['profiles']:
            progress('generate_profile',profileId=p['id']);plan=generate(recipe,p['id'],manifest);manifest=plan['manifest']
            # Candidate runtime payloads belong in Library; tracked reports contain evidence only.
            data=write_candidate(plan,out/p['id']) if (ROOT/'Library') in out.resolve().parents else None
            result=validate(plan,data);write_json(out/p['id']/'validation.json',result);export_reports(plan,out/p['id']);plans.append(plan)
            if not result['passed']:raise RuntimeError(canonical(result['errors']))
        for L in range(1,level_count+1):
            for w in range(1,wave_count+1):
                seq=[next(z for z in p['waves'] if z['levelId']==L and z['waveOrdinal']==w) for p in plans]
                if any(seq[i]['targetEhp']>seq[i+1]['targetEhp'] for i in range(len(seq)-1)):raise RuntimeError('Eight-profile EHP gradient failure')
                if any(seq[i]['spawnIntervalMs']<seq[i+1]['spawnIntervalMs'] for i in range(len(seq)-1)):raise RuntimeError('Eight-profile interval gradient failure')
                for i in range(len(seq)-1):
                    speeds_a={(c['canonicalEnemyId'],c['role']):c['speed'] for c in seq[i]['composition']}
                    speeds_b={(c['canonicalEnemyId'],c['role']):c['speed'] for c in seq[i+1]['composition']}
                    if any(speeds_a[k]>speeds_b[k] for k in speeds_a.keys()&speeds_b.keys()):raise RuntimeError('Eight-profile speed gradient failure')
        if any(plans[i]['levels'][L-1]['initialGold']<plans[i+1]['levels'][L-1]['initialGold'] for i in range(len(plans)-1) for L in range(1,level_count+1)):
            raise RuntimeError('Eight-profile gold gradient failure')
        write_json(out/f'all_waves_{len(plans)*level_count*wave_count}.json',[z for p in plans for z in p['waves']]);write_json(out/'variant_manifest.json',manifest)
        write_json(out/'validation.json',{'passed':True,'profiles':len(plans),'levels':len(plans)*level_count,'waves':len(plans)*level_count*wave_count,'elapsedSec':time.perf_counter()-start,
          'unityReferenceRuns':'Hash-matched finished PlayMode evidence is counted separately from static checks',
          'verifiedUnityProfileLevels':sum(len(p['calibrationEvidence']['verifiedLevelIds']) for p in plans),
          'pendingUnityProfileLevels':sum(len(p['calibrationEvidence']['pendingLevelIds']) for p in plans)})
        progress('complete',passed=True,out=str(out),waves=len(plans)*level_count*wave_count);return
    plan=read_json(args.plan) if args.plan else generate(recipe,profile)
    if args.command=='inspect':
        result={'profiles':recipe['profiles'],'applied':read_json(STATE),'sourceHashes':plan['sourceHashes'],'python':sys.executable,'openpyxlAvailable':__import__('importlib.util').util.find_spec('openpyxl') is not None}
        write_json(out/'inspect.json',result);progress('complete',**{k:v for k,v in result.items() if k!='applied'},out=str(out));return
    if args.command=='validate':
        result=validate(plan,args.export_dir);write_json(out/'validation.json',result);progress('complete',**result,out=str(out),elapsedSec=time.perf_counter()-start)
        if not result['passed']:raise SystemExit(2)
        return
    if args.command=='simulate':
        from balance_simulator import simulate_campaign
        if args.all_profiles:
            results=[]
            for prof in recipe['profiles']:
                check_cancel(out);candidate=generate(recipe,prof['id'])
                results+=simulate_campaign(candidate,args.level_min,args.level_max,args.strategy,
                  round_up(args.step*1000) if args.step else args.step_ms,out/prof['id'],args.seed)
        else:results=simulate_campaign(plan,args.level_min,args.level_max,args.strategy,round_up(args.step*1000) if args.step else args.step_ms,out,args.seed)
        write_json(out/'result.json',{'passed':True,'results':len(results),'coverage':'offline_prediction_only','elapsedSec':time.perf_counter()-start})
        progress('complete',out=str(out),results=len(results),elapsedSec=time.perf_counter()-start);return
    result=preview(plan)
    write_json(out/'resolved-plan.json',plan);write_json(out/'preview.json',result);export_reports(plan,out)
    # Scope filters affect views only; the full 20-level resolved plan remains consistency-checked.
    write_json(out/'selection.json',[z for z in plan['waves'] if args.level_min<=z['levelId']<=args.level_max and args.wave_min<=z['waveOrdinal']<=args.wave_max])
    if args.command=='stage':
        result=stage_export(plan,out)
        raise SystemExit(0 if result['passed'] else 2)
    if args.command=='apply' and not args.dry_run:
        require_openpyxl();assert_tower_radius_type();apply_plan(plan,out)
    else:progress('complete',passed=result['validation']['passed'],dryRun=True,out=str(out),elapsedSec=time.perf_counter()-start)

def run_cli():
    terminal_out=None
    for index,arg in enumerate(sys.argv[1:],1):
        if arg=='--out' and index+1<len(sys.argv):terminal_out=pathlib.Path(sys.argv[index+1])
        elif arg.startswith('--out='):terminal_out=pathlib.Path(arg.split('=',1)[1])
    exit_code=0;error=None;editor_log=None
    original_stdout=sys.stdout;original_stderr=sys.stderr
    try:
        if terminal_out is not None:
            terminal_out.mkdir(parents=True,exist_ok=True)
            (terminal_out/'cli-exit.json').unlink(missing_ok=True)
        log_path=os.environ.get('FT_BALANCE_EDITOR_LOG')
        if log_path:
            log_path=pathlib.Path(log_path);log_path.parent.mkdir(parents=True,exist_ok=True)
            editor_log=log_path.open('w',encoding='utf-8',buffering=1)
            sys.stdout=editor_log;sys.stderr=editor_log
        elif hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
        main()
    except SystemExit as ex:
        exit_code=ex.code if isinstance(ex.code,int) else (0 if ex.code is None else 1)
        if exit_code:error='Command exited with status '+str(ex.code)
    except BaseException as ex:
        exit_code=130 if isinstance(ex,KeyboardInterrupt) else 1;error=str(ex)
        progress('failed',error=str(ex),errorType=type(ex).__name__)
        traceback.print_exc(file=sys.stderr)
    finally:
        if terminal_out is not None:
            try:
                terminal_out.mkdir(parents=True,exist_ok=True)
                result={'jobId':terminal_out.name,'command':sys.argv[1] if len(sys.argv)>1 else '',
                  'exitCode':exit_code,'finishedUtc':datetime.now(timezone.utc).isoformat().replace('+00:00','Z')}
                if error:result['error']=error
                destination=terminal_out/'cli-exit.json';temporary=terminal_out/('.cli-exit-'+str(os.getpid())+'.tmp')
                temporary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                os.replace(temporary,destination)
            except BaseException as terminal_error:
                print('Could not persist CLI terminal status: '+str(terminal_error),file=sys.stderr)
        if editor_log is not None:
            sys.stdout=original_stdout;sys.stderr=original_stderr
            editor_log.close()
    return exit_code


if __name__=='__main__':raise SystemExit(run_cli())
