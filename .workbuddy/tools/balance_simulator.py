"""Deterministic spatial predictions; emits evidence for the C# unique rating evaluator.

Approximations are explicit: BFS tie-breaking can differ from Unity A*, movement/attacks
use a fixed step, float64 replaces Unity float32, and visuals/frame scheduling are absent.
There is deliberately no second authoritative star evaluator in this module.
"""
import collections, math, pathlib, time
from balance_pipeline import path_for,write_json,progress,check_cancel

VERSION='spatial-fixed-step-v1'
POLICY={}
APPROXIMATIONS=['Four-direction BFS tie order may differ from Unity A*',
 'Fixed-step movement then tower attacks instead of Unity frame scheduling',
 'Float64 arithmetic instead of Unity float32; near-threshold results need Unity comparison',
 'No visual/camera/touch validation; no certification of five-star reachability',
 'Build and upgrade operations only at wave boundaries; no borrowing future kill income']

def d2(a,b):return (a[0]-b[0])**2+(a[1]-b[1])**2
def straight(a,b,step=.5):
    n=max(1,math.ceil(math.sqrt(d2(a,b))/step))
    return [(a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n) for i in range(n+1)]
def coverage(cell,path,radius):return sum(d2(cell,p)<=radius*radius for p in path)

def next_type(strategy,n):
    if POLICY.get('types'):return POLICY['types'][n%len(POLICY['types'])]
    if strategy=='normal':return 1
    if strategy=='power':return [4,4,1,4][n%4]
    if strategy=='mistake':return 1
    if strategy=='optimized':return [1,1,1,4,7,1,4,1,7,1][n%10]
    return [1,4,1,7,1][n%5]

def choose_build(cells,towers,table,strategy):
    blocked=[t['cell'] for t in towers];oldpath=path_for(cells,blocked)
    air=straight(oldpath[0],oldpath[-1]);tid=next_type(strategy,len(towers));cfg=table[tid]
    for rawcell in POLICY.get('preferredCells',[]):
        cell=tuple(rawcell);x,y=cell
        if 0<=y<len(cells) and 0<=x<len(cells[0]) and cells[y][x]=='.' and cell not in blocked and path_for(cells,blocked+[cell]):return cell,tid
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
    best=None
    for y,row in enumerate(cells):
        for x,c in enumerate(row):
            cell=(x,y)
            if c!='.' or cell in blocked:continue
            p=path_for(cells,blocked+[cell])
            if not p:continue
            # Extend the traversable route while building overlapping firing zones.
            ground=coverage(cell,p,cfg['radius'])
            air_cov=coverage(cell,air,cfg['radius'])/2 if cfg['canAttackAir'] else 0
            support=sum(coverage(t['cell'],p,table[t['id']]['radius']) for t in towers)
            gain=len(p)-len(oldpath)
            score=gain*5+ground*3+air_cov*2+support*.12
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
    for _ in range(40):
        # Deliberate poor-control comparison stalls at three scattered basic towers.
        if strategy=='mistake' and len(towers)>=3:break
        # Establish a route/air coverage before upgrading; prioritize efficient final tiers.
        target_count=POLICY.get('targetCount',6 if strategy=='normal' else 8 if strategy=='power' else 10)
        up=[]
        if len(towers)>=POLICY.get('upgradeAfter',6 if strategy=='optimized' else min(4,target_count)):
            p=path_for(cells,[t['cell'] for t in towers]);air=straight(p[0],p[-1])
            for i,t in enumerate(towers):
                old=table[t['id']];nid=old['upgradeTo']
                if not nid:continue
                new=table[nid]
                if new['prices']>gold:continue
                g=coverage(t['cell'],p,new['radius']);a=coverage(t['cell'],air,new['radius'])/2
                gain=(new['power']*1000/new['CD']-old['power']*1000/old['CD'])*(g+(a if old['canAttackAir'] else 0))
                if old['type']==3:gain=(new['effectValue']-old['effectValue'])*400*g
                up.append((gain/new['prices'],i,nid))
        build=choose_build(cells,towers,table,strategy) if (len(towers)<target_count and not ((strategy=='optimized' or POLICY.get('preferUpgrade')) and up)) or not up else None
        if (strategy=='optimized' or POLICY.get('cheapFallback')) and build and table[build[1]]['prices']>gold and gold>=table[1]['prices'] and len(towers)<POLICY.get('upgradeAfter',6):
            build=(build[0],1)
        if build and table[build[1]]['prices']<=gold:
            cell,tid=build;cost=table[tid]['prices'];gold-=cost;spent+=cost
            towers.append({'id':tid,'cell':cell,'fireTimer':0.0,'searchTimer':0.0,'target':None})
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
    p=e['path'];idx=e['segment'];u=e['segmentProgress']
    if idx>=len(p)-1:return p[-1]
    a,b=p[idx],p[idx+1];length=math.sqrt(d2(a,b))
    ratio=u/length if length else 1
    return (a[0]+(b[0]-a[0])*ratio,a[1]+(b[1]-a[1])*ratio)

def advance(e,dist):
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
    enemy_table={x['id']:x for x in tables['tbenemydata']};tower_table={x['id']:x for x in tables['tbtowerinfo']}
    waves=[w for w in plan['waves'] if w['levelId']==L];dt=step_ms/1000
    gold=level['initialGold'];hp=level['initialHp'];towers=[];operations=[];reports=[]
    killed=leaked=boss_leaked=critical_leaked=successful=0;combat_sec=0;level_sec=0;max_alive=0
    total_overkill=0;aoe_hits=aoe_shots=0;coverage_ground=coverage_air=slow_seconds=0
    started=time.perf_counter();error=None
    for w in waves:
        check_cancel(out)
        if time.perf_counter()-started>90:error='single-level simulation exceeded 90 seconds';break
        if hp<=0:break
        before=gold;gold,spent=spend_boundary(cells,towers,tower_table,gold,strategy,w['waveOrdinal'],operations)
        path=path_for(cells,[t['cell'] for t in towers]);airpath=[path[0],path[-1]]
        alive=[];cursor=0;elapsed=0.0;wave_kills=wave_leaks=wave_income=wave_boss=wave_critical=peak=0
        wave_overkill=0;wave_air_window=wave_ground_window=0
        initial_ops=len(operations)
        # Full wave; do not overlap the next wave or pre-credit any income.
        while cursor<len(w['enemyIds']) or alive:
            if elapsed>240:error='wave simulation exceeded 240 seconds';break
            while cursor<len(w['enemyIds']) and elapsed+1e-9>=cursor*w['spawnIntervalMs']/1000:
                cfg=enemy_table[w['enemyIds'][cursor]];role=next(c['role'] for c in w['composition'] if c['variantId']==cfg['id'])
                alive.append({'spawnIndex':cursor,'cfg':cfg,'role':role,'hp':cfg['hp'],'path':airpath if cfg['isFlying'] else path,
                  'segment':0,'segmentProgress':0.0,'slowRatio':0.0,'slowUntil':0.0,'alive':True})
                cursor+=1;successful+=1
            peak=max(peak,len(alive));max_alive=max(max_alive,len(alive))
            for e in alive:
                if elapsed>=e['slowUntil']:e['slowRatio']=0
                advance(e,e['cfg']['speed']*(1-e['slowRatio'])*dt)
                if e['slowRatio']>0:slow_seconds+=dt
            # Apply leak completion before towers, as an explicit scheduling approximation.
            for e in alive:
                if e['segment']>=len(e['path'])-1:
                    e['alive']=False;wave_leaks+=1;leaked+=1;hp-=e['cfg']['damageToPlayer']
                    if e['role']=='boss':boss_leaked+=1;wave_boss+=1
                    if e['role'] in ['boss','elite']:critical_leaked+=1;wave_critical+=1
            alive=[e for e in alive if e['alive']]
            if (strategy=='optimized' or POLICY.get('midwaveUpgrades')) and len(towers)>=POLICY.get('midwaveAfter',5):
                choices=[]
                for ti,t in enumerate(towers):
                    old=tower_table[t['id']];nid=old['upgradeTo']
                    if not nid or tower_table[nid]['prices']>gold:continue
                    cfg=tower_table[nid];ground=coverage(t['cell'],path,cfg['radius']);a=coverage(t['cell'],straight(path[0],path[-1]),cfg['radius'])/2
                    delta=(cfg['power']*1000/cfg['CD']-old['power']*1000/old['CD'])*(ground+(a if cfg['canAttackAir'] else 0))
                    if cfg['type']==3:delta=(cfg['effectValue']-old['effectValue'])*300*ground
                    choices.append((delta/cfg['prices'],ti,nid))
                if choices:
                    _,ti,nid=max(choices);t=towers[ti];cost=tower_table[nid]['prices'];gold-=cost;spent+=cost
                    t.update(id=nid,fireTimer=0.0,searchTimer=0.0,target=None)
                    operations.append({'waveOrdinal':w['waveOrdinal'],'timeMs':math.floor(elapsed*1000),'action':'upgrade',
                      'row':t['cell'][1],'col':t['cell'][0],'towerId':nid,'cost':cost,'balanceAfter':gold})
            for e in alive:
                count=sum(tower_table[t['id']]['type']!=3 and (not e['cfg']['isFlying'] or tower_table[t['id']]['canAttackAir']) and
                    d2(t['cell'],position(e))<=tower_table[t['id']]['radius']**2 for t in towers)
                if count:
                    if e['cfg']['isFlying']:coverage_air+=dt;wave_air_window+=dt
                    else:coverage_ground+=dt;wave_ground_window+=dt
            for t in towers:
                cfg=tower_table[t['id']];radius2=cfg['radius']**2
                if cfg['type']==3:
                    t['fireTimer']+=dt
                    if t['fireTimer']+1e-9>=cfg['CD']/1000:
                        t['fireTimer']=0
                        for e in alive:
                            if e['alive'] and (not e['cfg']['isFlying'] or cfg['canAttackAir']) and d2(t['cell'],position(e))<=radius2:
                                if cfg['effectValue']>=e['slowRatio'] or elapsed>=e['slowUntil']:
                                    e['slowRatio']=cfg['effectValue'];e['slowUntil']=elapsed+cfg['CD']/1000+.3
                    continue
                target=t['target']
                if target and (not target['alive'] or d2(t['cell'],position(target))>radius2):t['target']=target=None
                t['searchTimer']+=dt
                if target is None and t['searchTimer']+1e-9>=cfg['searchIntervalMs']/1000:
                    t['searchTimer']=0
                    options=[e for e in alive if e['alive'] and (not e['cfg']['isFlying'] or cfg['canAttackAir']) and d2(t['cell'],position(e))<=radius2]
                    if options:
                        # Normalized path progress; persistent lock until out of range.
                        target=max(options,key=lambda e:(e['segment']+e['segmentProgress'])/max(1,len(e['path'])-1));t['target']=target
                if target is None:continue
                t['fireTimer']+=dt
                if t['fireTimer']+1e-9<cfg['CD']/1000:continue
                t['fireTimer']=0;victims=[target]
                if cfg['type']==2:
                    center=position(target);victims=[e for e in alive if e['alive'] and not e['cfg']['isFlying'] and d2(position(e),center)<=1.2**2]
                    aoe_shots+=1;aoe_hits+=len(victims)
                for e in victims:
                    damage=cfg['power']*(1-e['cfg']['armor']);wave_overkill+=max(0,damage-e['hp']);e['hp']-=damage
                    if e['hp']<=0 and e['alive']:
                        e['alive']=False;killed+=1;wave_kills+=1;gold+=e['cfg']['reward'];wave_income+=e['cfg']['reward']
            alive=[e for e in alive if e['alive']]
            elapsed+=dt
            if hp<=0:break
        combat_sec+=elapsed;level_sec+=elapsed+(0 if w['waveOrdinal']==1 else 5);total_overkill+=wave_overkill
        cleared=cursor==len(w['enemyIds']) and not alive and hp>0
        if cleared:gold+=w['rewardGold']
        reports.append({'waveOrdinal':w['waveOrdinal'],'planned':w['count'],'successfulSpawned':cursor,'totalEhp':w['actualEhp'],
          'flyingCount':w['flyingCount'],'heavyCount':w['heavyCount'],'eliteCount':w['eliteCount'],'bossCount':w['bossCount'],
          'killed':wave_kills,'leaked':wave_leaks,'bossLeaked':wave_boss,'criticalLeaked':wave_critical,'killGold':wave_income,
          'clearReward':w['rewardGold'] if cleared else 0,'goldBeforePurchases':before,'spent':spent,'balance':gold,'hp':max(0,hp),
          'towerComposition':dict(collections.Counter(t['id'] for t in towers)),'combatElapsedMs':math.floor(elapsed*1000),
          'levelElapsedMs':math.floor(level_sec*1000),'alivePeak':peak,'groundEffectiveShootingWindowSec':wave_ground_window,
          'airEffectiveShootingWindowSec':wave_air_window,'overkillDamage':wave_overkill,'cleared':cleared})
        if error or hp<=0:break
    completed=sum(r['cleared'] for r in reports);win=completed==20 and hp>0 and not error
    metrics={'runId':f'offline:{plan["profileId"]}:L{L}:{strategy}:{VERSION}','profileId':plan['profileId'],
      'profileRevision':rating['profileRevision'],'balanceRevision':rating['balanceRevision'],'ratingRevision':rating['ratingRevision'],'planHash':rating['planHash'],
      'expectedWaveCount':20,'completedWaveCount':completed,'expectedEnemyCount':rating['expectedEnemyCount'],
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
