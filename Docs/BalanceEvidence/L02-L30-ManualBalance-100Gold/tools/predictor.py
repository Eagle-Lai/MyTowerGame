"""Deterministic spatial predictions; emits evidence for the C# unique rating evaluator.

Approximations are explicit: BFS tie-breaking can differ from Unity A*, movement/attacks
use a fixed step, float64 replaces Unity float32, and visuals/frame scheduling are absent.
There is deliberately no second authoritative star evaluator in this module.
"""
import collections, math, pathlib, time, functools
from balance_pipeline import write_json,progress,check_cancel
from balance_campaign import capacity,runtime_path_for as path_for

VERSION='manual-prediction-air-priority-reverse-towers-r1'
POLICY={}
APPROXIMATIONS=['Air priority, periodic ground-to-air retargeting and reverse tower order follow current code; spatial-grid tie order remains approximate',
 'Four-direction path search mirrors shipped AStarWrapper insertion ties; battle timing still approximate',
 'Fixed-step movement then tower attacks instead of Unity frame scheduling',
 'Float64 arithmetic instead of Unity float32; near-threshold results need Unity comparison',
 'No visual/camera/touch validation; no certification of five-star reachability',
 'Build and upgrade operations only at wave boundaries; no borrowing future kill income']

def d2(a,b):return (a[0]-b[0])**2+(a[1]-b[1])**2
def straight(a,b,step=.5):
    n=max(1,math.ceil(math.sqrt(d2(a,b))/step))
    return [(a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n) for i in range(n+1)]
@functools.lru_cache(maxsize=65536)
def _coverage(cell,path,radius):return sum(d2(cell,p)<=radius*radius for p in path)
def coverage(cell,path,radius):return _coverage(cell,tuple(map(tuple,path)),radius)

def next_type(strategy,n):
    if n<POLICY.get('earlyNormalCount',0):return 1
    if POLICY.get('types'):return POLICY['types'][n%len(POLICY['types'])]
    if strategy=='normal':return 1
    if strategy=='power':return [4,4,1,4][n%4]
    if strategy=='mistake':return 1
    if strategy=='optimized':return [1,1,1,4,7,1,4,1,7,1][n%10]
    return [1,4,1,7,1][n%5]

def choose_build(cells,towers,table,strategy):
    blocked=[t['cell'] for t in towers];oldpath=path_for(cells,blocked)
    air=straight(oldpath[0],oldpath[-1]);tid=next_type(strategy,len(towers));cfg=table[tid]
    reserved={tuple(cell) for cell in POLICY.get('reservedPath',[])}
    blueprint=POLICY.get('blueprintCells')
    allowed={tuple(cell) for cell in blueprint} if blueprint is not None else None
    final_path=POLICY.get('blueprintPath',[])
    for rawcell in POLICY.get('preferredCells',[]):
        cell=tuple(rawcell);x,y=cell
        if 0<=y<len(cells) and 0<=x<len(cells[0]) and cells[y][x]=='.' and cell not in blocked and path_for(cells,blocked+[cell]):
            hinted=next((h['towerId']for h in POLICY.get('towerTypeHints',[])if h['row']==y and h['col']==x),tid)
            return cell,hinted
    if strategy=='optimized' and len(towers)<7:
        start,end=oldpath[0],oldpath[-1];horizontal=abs(end[0]-start[0])>=abs(end[1]-start[1])
        midy=len(cells)//2;midx=len(cells[0])//2
        offsets=[0,-1,1,-2,2,-3,3]
        if horizontal:
            wallx=max(2,len(cells[0])//3);preferred=[(wallx,midy+off) for off in offsets]
        else:
            wally=max(2,len(cells)//2);preferred=[(midx+off,wally) for off in offsets]
        for cell in preferred:
            x,y=cell
            if 0<=y<len(cells) and 0<=x<len(cells[0]) and cells[y][x]=='.' and cell not in blocked and path_for(cells,blocked+[cell]):return cell,tid
    best=None;oldpathset=set(oldpath);support_cache={}
    for y,row in enumerate(cells):
        for x,c in enumerate(row):
            cell=(x,y)
            if c!='.' or cell in blocked or cell in reserved or (allowed is not None and cell not in allowed) or list(cell)==POLICY.get('_soldCellThisBoundary'):continue
            tid=next((h['towerId'] for h in POLICY.get('towerTypeHints',[]) if h['row']==y and h['col']==x),next_type(strategy,len(towers)))
            cfg=table[tid]
            # Blocking a cell outside this shortest path cannot invalidate that path.
            p=oldpath if cell not in oldpathset else path_for(cells,blocked+[cell])
            if not p:continue
            # Extend the traversable route while building overlapping firing zones.
            ground=coverage(cell,p,cfg['radius'])
            air_cov=coverage(cell,air,cfg['radius'])/2 if cfg['canAttackAir'] else 0
            keypath=tuple(p)
            if keypath not in support_cache:support_cache[keypath]=sum(coverage(t['cell'],p,table[t['id']]['radius']) for t in towers)
            support=support_cache[keypath]
            gain=len(p)-len(oldpath)
            # A newly extended maze is harmful if it abandons the existing firing line.
            # Preserve aggregate support before chasing a few extra path steps.
            score=gain*POLICY.get('pathWeight',2)+ground*3+air_cov*POLICY.get('airWeight',2)+support*2
            if final_path:
                from balance_maze import intervals
                # Complete useful folds, retain present firing support, and place
                # towers that will meet the same enemy again on a later segment.
                score=gain*POLICY.get('pathGainWeight',8)+ground*3+air_cov*POLICY.get('airWeight',3)+support*2
                score+=coverage(cell,final_path,cfg['radius'])*POLICY.get('futureCoverageWeight',1.2)+max(0,intervals(cell,final_path,cfg['radius'])-1)*4
                if not cfg['canAttackAir'] and len(towers)>=8:
                    # Ground-only guns should not consume the few wall positions
                    # that intercept a short, unbendable flying route.
                    score-=coverage(cell,air,cfg['radius'])/2*POLICY.get('reserveAirCells',12)
            if strategy=='optimized':
                # Preserve long firing lanes across the straight air route and stagger
                # coverage; early kills provide the first real upgrade funds sooner.
                nearest_index=min(range(len(oldpath)),key=lambda i:d2(cell,oldpath[i]))
                overlap=sum(max(0,9-d2(cell,t['cell'])) for t in towers)
                score=gain*2+ground*3+air_cov*2-nearest_index*.12-overlap*.8
            if cfg['type']==3:score+=sum(d2(cell,t['cell'])<=16 for t in towers)*2
            if strategy=='mistake':score=-ground-air_cov
            key=(score,-abs(x-len(row)/2),-y,-x)
            if best is None or key>best[0]:best=(key,cell,tid)
    return (best[1],best[2]) if best else None

def spend_boundary(cells,towers,table,gold,strategy,wave,operations):
    spent=0
    if wave in POLICY.get('relocationWaves',[]) and towers:
        # A real sale consumes the configured resale loss; the removed cell is
        # excluded from that boundary's rebuild rather than immediately rebought.
        t=min(towers,key=lambda t:t['damage']+t['slowApplications']*2)
        refund=table[t['id']]['sellPrice'];gold+=refund;spent-=refund;towers.remove(t)
        POLICY['_soldCellThisBoundary']=list(t['cell'])
        operations.append({'waveOrdinal':wave,'timeMs':0,'action':'sell','row':t['cell'][1],'col':t['cell'][0],
            'towerId':t['id'],'cost':-refund,'balanceAfter':gold})
    else:POLICY.pop('_soldCellThisBoundary',None)
    if POLICY.get('scriptedOperations') and wave < POLICY.get('adaptiveFromWave', 26):
        for op in POLICY['scriptedOperations']:
            if op['waveOrdinal']!=wave:continue
            if op['timeMs']!=0:raise ValueError('Boundary replay requires timeMs=0')
            cell=(op['col'],op['row']);tid=op['towerId'];cost=table[tid]['prices']
            if gold<cost:raise ValueError('Scripted purchase is unaffordable')
            if op['action']=='build':
                if cells[cell[1]][cell[0]]!='.' or any(t['cell']==cell for t in towers) or not path_for(cells,[t['cell'] for t in towers]+[cell]):raise ValueError('Illegal scripted build')
                towers.append({'id':tid,'cell':cell,'fireTimer':0.,'searchTimer':0.,'target':None,
                    'damage':0.,'hits':0,'airHits':0,'slowApplications':0,'reusedEnemies':set(),'enemyContacts':{},'rangeEntries':{}})
            elif op['action']=='upgrade':
                t=next(t for t in towers if t['cell']==cell)
                if table[t['id']]['upgradeTo']!=tid:raise ValueError('Illegal scripted upgrade')
                t.update(id=tid,fireTimer=0.,searchTimer=0.,target=None)
            else:raise ValueError('Unsupported scripted action')
            gold-=cost;spent+=cost
            operations.append({**op,'cost':cost,'balanceAfter':gold})
        return gold,spent
    for _ in range(200):
        # Deliberate poor-control comparison stalls at three scattered basic towers.
        if strategy=='mistake' and len(towers)>=3:break
        # Establish a route/air coverage before upgrading; prioritize efficient final tiers.
        target_count=POLICY.get('targetCount',math.ceil((POLICY['capacity'] if 'capacity' in POLICY else capacity(cells)['capacity'])*.9))
        hard_cap=POLICY.get('maxTowers',target_count)
        target_count=min(hard_cap,target_count)
        up=[]
        builds=sum(op['cost'] for op in operations if op['action']=='build')
        upgrades=sum(op['cost'] for op in operations if op['action']=='upgrade')
        upgrade_cap=POLICY.get('upgradeBudgetGold')
        upgrade_left=(upgrade_cap-upgrades) if upgrade_cap is not None else None
        if not POLICY.get('forbidUpgrades') and (upgrade_left is None or upgrade_left>0) and len(towers)>=POLICY.get('upgradeAfter',8):
            p=path_for(cells,[t['cell'] for t in towers]);air=straight(p[0],p[-1])
            for i,t in enumerate(towers):
                old=table[t['id']];nid=old['upgradeTo']
                if not nid:continue
                new=table[nid]
                if new['prices']>gold:continue
                if upgrade_left is not None and new['prices']>upgrade_left:continue
                if wave>=20 and gold-new['prices'] < POLICY.get('upgradeReserve',0)*max(0,target_count-len(towers)):continue
                g=coverage(t['cell'],p,new['radius']);a=coverage(t['cell'],air,new['radius'])/2
                gain=(new['power']*1000/new['CD']-old['power']*1000/old['CD'])*(g+(a*POLICY.get('upgradeAirWeight',1) if old['canAttackAir'] else 0))
                if old['type']==3:gain=(new['effectValue']-old['effectValue'])*POLICY.get('slowUpgradeWeight',160)*g
                up.append((gain/new['prices'],i,nid))
        prefer_upgrade=POLICY.get('preferUpgrade',False) or (len(towers)>=8 and upgrades<builds*POLICY.get('upgradeShare',.3))
        build=choose_build(cells,towers,table,strategy) if len(towers)<target_count and (not (prefer_upgrade and up) or not up) else None
        if (strategy=='optimized' or POLICY.get('cheapFallback')) and build and table[build[1]]['prices']>gold and gold>=table[1]['prices'] and len(towers)<POLICY.get('upgradeAfter',6):
            build=(build[0],1)
        if build and table[build[1]]['prices']<=gold:
            cell,tid=build;cost=table[tid]['prices'];gold-=cost;spent+=cost
            towers.append({'id':tid,'cell':cell,'fireTimer':0.0,'searchTimer':0.0,'target':None,
                'damage':0.,'hits':0,'airHits':0,'slowApplications':0,'reusedEnemies':set(),'enemyContacts':{},'rangeEntries':{}})
            operations.append({'waveOrdinal':wave,'timeMs':0,'action':'build','row':cell[1],'col':cell[0],
              'towerId':tid,'cost':cost,'balanceAfter':gold})
        elif up:
            _,i,tid=max(up);cost=table[tid]['prices'];gold-=cost;spent+=cost
            towers[i].update(id=tid,fireTimer=0.0,searchTimer=0.0,target=None);cell=towers[i]['cell']
            operations.append({'waveOrdinal':wave,'timeMs':0,'action':'upgrade','row':cell[1],'col':cell[0],
              'towerId':tid,'cost':cost,'balanceAfter':gold})
        else:break
    return gold,spent

def position(e):
    if 'positionCache' in e:return e['positionCache']
    p=e['path'];idx=e['segment'];u=e['segmentProgress']
    if idx>=len(p)-1:return p[-1]
    a,b=p[idx],p[idx+1];length=math.sqrt(d2(a,b))
    ratio=u/length if length else 1
    return (a[0]+(b[0]-a[0])*ratio,a[1]+(b[1]-a[1])*ratio)

def advance(e,dist):
    e.pop('positionCache',None)
    while dist>0 and e['segment']<len(e['path'])-1:
        p=e['path'];idx=e['segment'];length=math.sqrt(d2(p[idx],p[idx+1]));remain=length-e['segmentProgress']
        if dist+1e-12>=remain:e['segment']+=1;e['segmentProgress']=0.0;dist-=remain
        else:e['segmentProgress']+=dist;dist=0

def simulate_level(plan,L,strategy,step_ms,out,seed=42):
    if strategy not in ['normal','power','mixed','mistake','optimized']:raise ValueError('Unknown strategy '+strategy)
    if not 1<=step_ms<=200:raise ValueError('step-ms requires 1..200')
    tables=plan['tables'];level=next(x for x in tables['tbsceneinfo'] if x['id']==L)
    rating=next(x for x in tables['tblevelrating'] if x['id']==L)
    cells=next(x['cells'] for x in tables['tblevelmap'] if x['id']==level['mapId'])
    map_capacity=capacity(cells)
    enemy_table={x['id']:x for x in tables['tbenemydata']};tower_table={x['id']:x for x in tables['tbtowerinfo']}
    waves=[w for w in plan['waves'] if w['levelId']==L];dt=step_ms/1000
    gold=level['initialGold'];hp=level['initialHp'];towers=[];operations=[];reports=[]
    killed=leaked=boss_leaked=critical_leaked=successful=0;combat_sec=0;level_sec=0;max_alive=0
    total_overkill=0;aoe_hits=aoe_shots=0;coverage_ground=coverage_air=slow_seconds=0
    started=time.perf_counter();error=None
    for w in waves:
        check_cancel(out)
        if time.perf_counter()-started>POLICY.get('maxWallSeconds',300):error='single-level simulation exceeded wall budget';break
        if hp<=0:break
        before=gold;gold,spent=spend_boundary(cells,towers,tower_table,gold,strategy,w['waveOrdinal'],operations)
        path=path_for(cells,[t['cell'] for t in towers]);airpath=[path[0],path[-1]]
        alive=[];cursor=0;elapsed=0.0;wave_kills=wave_leaks=wave_income=wave_boss=wave_critical=peak=0
        wave_overkill=0;wave_air_window=wave_ground_window=0
        initial_ops=len(operations);deferred=0;leak_roles=collections.Counter()
        upgrade_spent=sum(op['cost'] for op in operations if op['action']=='upgrade')
        upgrade_cap=POLICY.get('upgradeBudgetGold')
        # Full wave; do not overlap the next wave or pre-credit any income.
        while cursor<len(w['enemyIds']) or alive:
            if elapsed>240:error='wave simulation exceeded 240 seconds';break
            while cursor<len(w['enemyIds']) and elapsed+1e-9>=cursor*w['spawnIntervalMs']/1000:
                if len(alive)>=tables['tbglobal'][0].get('maxEnemyAlive',200):deferred+=1;break
                cfg=enemy_table[w['enemyIds'][cursor]];role=next(c['role'] for c in w['composition'] if c['variantId']==cfg['id'])
                alive.append({'spawnIndex':cursor,'cfg':cfg,'role':role,'hp':cfg['hp'],'path':airpath if cfg['isFlying'] else path,
                  'segment':0,'segmentProgress':0.0,'slowRatio':0.0,'slowUntil':0.0,'alive':True})
                cursor+=1;successful+=1
            peak=max(peak,len(alive));max_alive=max(max_alive,len(alive))
            for e in alive:
                if elapsed>=e['slowUntil']:e['slowRatio']=0
                advance(e,e['cfg']['speed']*(1-e['slowRatio'])*dt)
                e['positionCache']=position(e)
                if e['slowRatio']>0:slow_seconds+=dt
            # Apply leak completion before towers, as an explicit scheduling approximation.
            for e in alive:
                if e['segment']>=len(e['path'])-1:
                    e['alive']=False;wave_leaks+=1;leaked+=1;hp-=e['cfg']['damageToPlayer']
                    leak_roles[e['role']]+=1
                    if e['role']=='boss':boss_leaked+=1;wave_boss+=1
                    if e['role'] in ['boss','elite']:critical_leaked+=1;wave_critical+=1
            alive=[e for e in alive if e['alive']]
            if ((strategy=='optimized' or POLICY.get('midwaveUpgrades')) and len(towers)>=POLICY.get('midwaveAfter',5)
                    and not POLICY.get('forbidUpgrades') and (upgrade_cap is None or upgrade_spent<upgrade_cap)):
                choices=[]
                for ti,t in enumerate(towers):
                    old=tower_table[t['id']];nid=old['upgradeTo']
                    if not nid or tower_table[nid]['prices']>gold:continue
                    if upgrade_cap is not None and upgrade_spent+tower_table[nid]['prices']>upgrade_cap:continue
                    cfg=tower_table[nid];ground=coverage(t['cell'],path,cfg['radius']);a=coverage(t['cell'],straight(path[0],path[-1]),cfg['radius'])/2
                    delta=(cfg['power']*1000/cfg['CD']-old['power']*1000/old['CD'])*(ground+(a if cfg['canAttackAir'] else 0))
                    if cfg['type']==3:delta=(cfg['effectValue']-old['effectValue'])*300*ground
                    choices.append((delta/cfg['prices'],ti,nid))
                if choices:
                    _,ti,nid=max(choices);t=towers[ti];cost=tower_table[nid]['prices'];gold-=cost;spent+=cost;upgrade_spent+=cost
                    t.update(id=nid,fireTimer=0.0,searchTimer=0.0,target=None)
                    operations.append({'waveOrdinal':w['waveOrdinal'],'timeMs':math.floor(elapsed*1000),'action':'upgrade',
                      'row':t['cell'][1],'col':t['cell'][0],'towerId':nid,'cost':cost,'balanceAfter':gold})
            for e in alive:
                count=any(tower_table[t['id']]['type']!=3 and (not e['cfg']['isFlying'] or tower_table[t['id']]['canAttackAir']) and
                    d2(t['cell'],position(e))<=tower_table[t['id']]['radius']**2 for t in towers)
                if count:
                    if e['cfg']['isFlying']:coverage_air+=dt;wave_air_window+=dt
                    else:coverage_ground+=dt;wave_ground_window+=dt
            for t in reversed(towers):
                cfg=tower_table[t['id']];radius2=cfg['radius']**2
                for e in (alive if POLICY.get('trackReentry',False) else []):
                    contact=(w['waveOrdinal'],e['spawnIndex']);inside=d2(t['cell'],position(e))<=radius2
                    old=t['rangeEntries'].get(contact,(False,0))
                    t['rangeEntries'][contact]=(inside,old[1]+int(inside and not old[0]))
                if cfg['type']==3:
                    t['fireTimer']+=dt
                    if t['fireTimer']+1e-9>=cfg['CD']/1000:
                        t['fireTimer']=0
                        for e in alive:
                            if e['alive'] and (not e['cfg']['isFlying'] or cfg['canAttackAir']) and d2(t['cell'],position(e))<=radius2:
                                if cfg['effectValue']>=e['slowRatio'] or elapsed>=e['slowUntil']:
                                    e['slowRatio']=cfg['effectValue'];e['slowUntil']=elapsed+cfg['CD']/1000+.1
                                    t['slowApplications']+=1
                                    if POLICY.get('trackReentry',False):
                                        contact=(w['waveOrdinal'],e['spawnIndex']);entry=t['rangeEntries'][contact][1]
                                        last=t['enemyContacts'].get(contact)
                                        if last is not None and entry>last:t['reusedEnemies'].add(contact)
                                        t['enemyContacts'][contact]=entry
                    continue
                target=t['target']
                if target and (not target['alive'] or d2(t['cell'],position(target))>radius2):t['target']=target=None
                t['searchTimer']+=dt
                if t['searchTimer']+1e-9>=cfg['searchIntervalMs']/1000:
                    t['searchTimer']=0
                    if target is None or cfg['canAttackAir'] and not target['cfg']['isFlying']:
                        options=[e for e in alive if e['alive'] and (not e['cfg']['isFlying'] or cfg['canAttackAir']) and d2(t['cell'],position(e))<=radius2]
                        air=[e for e in options if e['cfg']['isFlying']]
                        if air:options=air
                        elif target is not None:options=[]
                        if options:
                            mode=cfg.get('targetMode',0)
                            def rank(e):
                                if mode==1:return -d2(t['cell'],position(e))
                                if mode==2:return e['hp']
                                return 0 if e['cfg']['isFlying'] else (e['segment']+1)/max(1,len(e['path'])-1)
                            target=max(options,key=rank);t['target']=target
                if target is None:continue
                t['fireTimer']+=dt
                if t['fireTimer']+1e-9<cfg['CD']/1000:continue
                t['fireTimer']=0;victims=[target]
                if cfg['type']==2:
                    center=position(target);blast=next(b for b in tables['tbbulletdata'] if b['id']==cfg['bulletId'])['aoeRadius']
                    victims=[e for e in alive if e['alive'] and not e['cfg']['isFlying'] and d2(position(e),center)<=blast**2]
                    aoe_shots+=1;aoe_hits+=len(victims)
                for e in victims:
                    damage=cfg['power']*(1-e['cfg']['armor']);wave_overkill+=max(0,damage-e['hp']);t['damage']+=min(damage,e['hp']);t['hits']+=1
                    if e['cfg']['isFlying']:t['airHits']+=1
                    if POLICY.get('trackReentry',False):
                        contact=(w['waveOrdinal'],e['spawnIndex']);entry=t['rangeEntries'][contact][1];last=t['enemyContacts'].get(contact)
                        if last is not None and entry>last:t['reusedEnemies'].add(contact)
                        t['enemyContacts'][contact]=entry
                    e['hp']-=damage
                    if e['hp']<=0 and e['alive']:
                        e['alive']=False;killed+=1;wave_kills+=1;gold+=e['cfg']['reward'];wave_income+=e['cfg']['reward']
            alive=[e for e in alive if e['alive']]
            elapsed+=dt
            if hp<=0:break
        combat_sec+=elapsed;level_sec+=elapsed+(0 if w['waveOrdinal']==1 else 5);total_overkill+=wave_overkill
        cleared=cursor==len(w['enemyIds']) and not alive and hp>0
        if cleared:gold+=w['rewardGold']
        reports.append({'waveOrdinal':w['waveOrdinal'],'planned':w['count'],'successfulSpawned':cursor,'totalEhp':w['actualEhp'],
          'towerCount':len(towers),'capacity':map_capacity['capacity'],'occupancy':len(towers)/map_capacity['capacity'],'leakedByRole':dict(leak_roles),
          'pathLength':len(path)-1,'spawnDeferredCount':deferred,'layout':[{'row':t['cell'][1],'col':t['cell'][0],'towerId':t['id']} for t in towers],
          'repeatedCoverageTowers':sum(__import__('balance_maze').intervals(t['cell'],path,tower_table[t['id']]['radius'])>1 for t in towers),
          'flyingCount':w['flyingCount'],'heavyCount':w['heavyCount'],'eliteCount':w['eliteCount'],'bossCount':w['bossCount'],
          'killed':wave_kills,'leaked':wave_leaks,'bossLeaked':wave_boss,'criticalLeaked':wave_critical,'killGold':wave_income,
          'clearReward':w['rewardGold'] if cleared else 0,'goldBeforePurchases':before,'spent':spent,'balance':gold,'hp':max(0,hp),
          'towerComposition':dict(collections.Counter(t['id'] for t in towers)),'combatElapsedMs':math.floor(elapsed*1000),
          'levelElapsedMs':math.floor(level_sec*1000),'alivePeak':peak,'groundEffectiveShootingWindowSec':wave_ground_window,
          'airEffectiveShootingWindowSec':wave_air_window,'overkillDamage':wave_overkill,'cleared':cleared})
        if error or hp<=0:break
    completed=sum(r['cleared'] for r in reports);win=completed==rating['expectedWaveCount'] and hp>0 and not error
    metrics={'runId':f'offline:{plan["profileId"]}:L{L}:{strategy}:{VERSION}','profileId':plan['profileId'],
      'profileRevision':rating['profileRevision'],'balanceRevision':rating['balanceRevision'],'ratingRevision':rating['ratingRevision'],'planHash':rating['planHash'],
       'expectedWaveCount':rating['expectedWaveCount'],'completedWaveCount':completed,'expectedEnemyCount':rating['expectedEnemyCount'],
      'successfulSpawned':successful,'killed':killed,'leaked':leaked,'bossLeaked':boss_leaked,'criticalLeaked':critical_leaked,
      'hp':max(0,hp),'maxHp':level['initialHp'],'combatElapsedMs':math.floor(combat_sec*1000),'levelElapsedMs':math.floor(level_sec*1000),
      'combatElapsedSeconds':combat_sec,'levelElapsedSeconds':level_sec,'debugOverride':False,'statisticsValid':not bool(error),'timingValid':True,'victory':win,
      'waves':[]}
    cumulative=0.0
    for wr in reports:
        begin=cumulative;cumulative+=wr['combatElapsedMs']/1000
        metrics['waves'].append({'ordinal':wr['waveOrdinal'],'expected':wr['planned'],'successfulSpawned':wr['successfulSpawned'],
          'killed':wr['killed'],'leaked':wr['leaked'],'bossLeaked':wr['bossLeaked'],'criticalLeaked':wr['criticalLeaked'],
          'gold':wr['balance'],'hp':wr['hp'],'killGold':wr['killGold'],'clearGold':wr['clearReward'],'peakAlive':wr['alivePeak'],
          'combatStartSeconds':begin,'combatEndSeconds':cumulative,'levelEndSeconds':wr['levelElapsedMs']/1000})
    result={'profileId':plan['profileId'],'levelId':L,'planHash':rating['planHash'],'strategyId':strategy,'strategyRevision':VERSION,'policy':POLICY.copy(),
      'stepMs':step_ms,'seed':seed,'coverage':'offline_prediction_only','approximations':APPROXIMATIONS,
      'result':'predicted_clear' if win else 'predicted_failure','error':error,'predictionStars':None,
      'ratingStatus':'requires C# LevelRatingEvaluator; simulator does not implement another scoring algorithm',
      'combatToParRatio':combat_sec*1000/rating['parCombatTimeMs'],'balance':gold,'leaked':leaked,'metrics':metrics,'ratingProfile':rating,
      'operations':operations,'waves':reports,'elapsedSec':time.perf_counter()-started,'alivePeak':max_alive,
      'overkillDamage':total_overkill,'aoeAverageActualHits':aoe_hits/aoe_shots if aoe_shots else 0,
      'groundEffectiveShootingWindowSec':coverage_ground,'airEffectiveShootingWindowSec':coverage_air,'slowCoveredEnemySec':slow_seconds}
    result['towerContributions']=[{'row':t['cell'][1],'col':t['cell'][0],'towerId':t['id'],'damage':t['damage'],
        'hits':t['hits'],'airHits':t['airHits'],'slowApplications':t['slowApplications'],'repeatAttackEnemies':len(t['reusedEnemies']),
        'coveragePasses':__import__('balance_maze').intervals(t['cell'],path,tower_table[t['id']]['radius'])} for t in towers]
    p=pathlib.Path(out)/f'L{L:02}-{strategy}';write_json(p/'result.json',result);write_json(p/'operations.json',operations)
    return result

def simulate_campaign(plan,level_min,level_max,strategy,step_ms,out,seed=42):
    results=[]
    for L in range(level_min,level_max+1):
        check_cancel(out);progress('simulate_level',profileId=plan['profileId'],levelId=L,completed=L-level_min,total=level_max-level_min+1)
        result=simulate_level(plan,L,strategy,step_ms,out,seed);results.append(result)
        progress('simulated_level',profileId=plan['profileId'],levelId=L,result=result['result'],leaked=result['leaked'],combatToParRatio=result['combatToParRatio'])
    write_json(pathlib.Path(out)/'matrix.json',[{k:v for k,v in r.items() if k not in ['waves','operations','ratingProfile']} for r in results])
    return results
