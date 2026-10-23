"""Current gameplay applicability and real evidence gaps; never promotes certification."""
from formal_tools import *
import collections,datetime
current=tables();current_hash=runtime_hash();cache={current_hash:current}
delivery_path=REPORT/'audit/final-delivery-audit.json'
delivery=json.loads(delivery_path.read_text(encoding='utf-8'))if delivery_path.exists()else{}
certified={x['level']for x in delivery.get('certifiedLevels',[])}if delivery.get('status')=='complete'and delivery.get('runtimeContentHash')==current_hash else set()
def local_identity(level,t):
    scene=next(x for x in t['tbsceneinfo']if x['id']==level)
    rounds={x['id']:x for x in t['tbrounddata']};groups={x['id']:x for x in t['tbenemylist']};enemies={x['id']:x for x in t['tbenemydata']}
    selected_rounds=[rounds[i]for i in scene['RoundList']];gids=[i for r in selected_rounds for i in r['EnemyIndexs']];selected_groups=[groups[i]for i in gids]
    ids=sorted({i for g in selected_groups for i in g['EnemyIndexs']})
    payload=dict(scene=scene,rounds=selected_rounds,groups=selected_groups,enemies=[enemies[i]for i in ids],map=next(x for x in t['tblevelmap']if x['id']==scene['mapId']),tower=t['tbtowerinfo'],bullet=t['tbbulletdata'],globalConfig=t['tbglobal'])
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
current_local={l:local_identity(l,current)for l in range(1,31)}
def original_tables(h):
    if h in cache:return cache[h]
    p=REPORT/'audit/runtime-snapshots'/h
    if not all((p/f'{k}.json').exists()for k in KEYS):cache[h]=None
    else:cache[h]={k:json.loads((p/f'{k}.json').read_text(encoding='utf-8-sig'))for k in KEYS}
    return cache[h]
by=collections.defaultdict(list)
for f in (REPORT/'raw-trials').glob('*/unity-results.json'):
    for i,r in enumerate(json.loads(f.read_text(encoding='utf-8'))):
        level=r['levelId'];m=r['metrics'];h=r['profile']['runtimeContentHash'];t=original_tables(h)
        if r.get('initialGold')!=100 or m.get('debugOverride')or not t:continue
        match=local_identity(level,t)==current_local[level]
        by[level].append(dict(source=f.relative_to(REPORT).as_posix(),sourceIndex=i,runId=m['runId'],strategy=r['strategy'],runtimeHash=h,gameplayMatchesCurrent=match,exactCampaignHash=h==current_hash,state=r['state'],victory=r['victory'],waves=m['completedWaveCount'],leaked=m['leaked'],stars=r['stars'],operations=len(r['operations']),timedOperations=sum(o['timeMs']>0 for o in r['operations']),pending=len(r['pendingOperations'])if isinstance(r['pendingOperations'],list)else r['pendingOperations'],codeIdentityScope='See original batch input manifest; gameplay-table equivalence does not certify code or final rating',layout=sorted((x['row'],x['col'],x['towerId'])for x in r['towerContributions'])))
levels=[]
for level in range(2,31):
    applicable=[x for x in by[level]if x['gameplayMatchesCurrent']]
    wins=[x for x in applicable if x['victory']and x['waves']==25 and x['state']=='finished'and not x['pending']]
    zero=[x for x in wins if x['leaked']==0]
    exact_controls=[x for x in applicable if x['exactCampaignHash']and x['strategy']in['normal','power','mistake']and x['state']=='finished']
    distinct={json.dumps(x['layout'])for x in wins}
    levels.append(dict(level=level,localGameplaySha256=current_local[level],applicableObservedTrials=len(applicable),exactCampaignTrials=sum(x['exactCampaignHash']for x in applicable),legal25WaveVictories=len(wins),zeroLeakDevelopmentCandidates=len(zero),distinctWinningLayouts=len(distinct),exactControls=sorted({x['strategy']for x in exact_controls}),finalCertificationComplete=False,remaining='Final Par, final-data first success and two strict reruns, full final artifacts; alternatives and comparisons still require level-specific interpretation',zeroLeakSources=[{k:v for k,v in x.items()if k!='layout'}for x in zero]))
value=dict(capturedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),runtimeHash=current_hash,scope='Read-only full referenced gameplay records and shared tower/bullet/global comparison. Ratings excluded from local identity. This is development applicability, not certification.',levels=levels)
for level in levels:
    level['finalCertificationComplete']=level['level']in certified
    if level['finalCertificationComplete']:
        level['remaining']='None: complete final certification recorded independently in final-delivery-audit.json'
        level['finalCertificationSource']='final-delivery-audit.json'
value['scope']+=' Final certification flags, when present, are taken only from the separate successful final delivery audit.'
(REPORT/'audit/current-gameplay-evidence-catalog.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
print('Development zero-leak levels:',[x['level']for x in levels if x['zeroLeakDevelopmentCandidates']]);print('Missing zero-leak:',[x['level']for x in levels if not x['zeroLeakDevelopmentCandidates']])
