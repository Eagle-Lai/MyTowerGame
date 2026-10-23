"""Read-only reference, rating identity and shared frozen-gameplay validation."""
from formal_tools import *
import sys
tag=sys.argv[1];assert tag in ['r2','r3','r4','final'];t=tables();errors=[];rows=[]
index={name:{r['id']:r for r in values}for name,values in t.items()if isinstance(values,list)and values and isinstance(values[0],dict)and'id'in values[0]}
for name,values in t.items():
    if name in index and len(index[name])!=len(values):errors.append(dict(table=name,problem='duplicate primary key'))
for s in t['tbsceneinfo']:
    level=s['id'];rating=index['tblevelrating'][level];rs=[index['tbrounddata'][i]for i in s['RoundList']];gs=[index['tbenemylist'][i]for r in rs for i in r['EnemyIndexs']];ids=[i for g in gs for i in g['EnemyIndexs']];es=[index['tbenemydata'][i]for i in sorted(set(ids))];boss={e['id']for e in es if e['type']==5}
    assert s['mapId']in index['tblevelmap']
    checks=dict(waveCount=rating['expectedWaveCount']==len(rs)==25,enemyCount=rating['expectedEnemyCount']==len(ids),bossSet=set(rating['bossVariantIds'])==boss,criticalValid=set(rating['criticalVariantIds']).issubset(ids),bossIncludedInCritical=boss.issubset(rating['criticalVariantIds']),initialGold100=s['initialGold']==100,allEnemyPositiveHp=all(e['hp']>0 for e in es),allEnemyRewardPositive=all(e['reward']>0 for e in es),sameSharedSeal=rating['runtimeContentHash']==runtime_hash())
    if level>1:
        content=dict(scene=s,rounds=rs,groups=gs,enemies=es,map=index['tblevelmap'][s['mapId']])
        digest=hashlib.sha256(json.dumps(content,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();checks['contentIdentity']=rating['planHash']==digest
    if tag=='final'and level>1:checks['calibrated']='pending'not in rating['calibrationStatus'].lower()
    if not all(checks.values()):errors.append(dict(level=level,failed=[k for k,v in checks.items()if not v]))
    rows.append(dict(level=level,count=len(ids),bossIds=sorted(boss),criticalIds=rating['criticalVariantIds'],calibrationStatus=rating['calibrationStatus'],checks=checks))
original=json.loads((REPORT/'audit/runtime-snapshots/8d554ec8df7109b815762cbd0e35a685e906b0580676cf877bf463947be0f6d0/tblevelrating.json').read_text(encoding='utf-8-sig'))[0]
l01=index['tblevelrating'][1];frozen={k:l01[k]==v for k,v in original.items()if k!='runtimeContentHash'}
assert all(frozen.values()),frozen
record=dict(tag=tag,runtimeContentHash=runtime_hash(),allReferencesResolved=True,l01OtherRatingFieldsUnchangedFromR1=frozen,errors=errors,levels=rows)
(REPORT/f'audit/rating-reference-integrity-{tag}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print(len(rows),'levels',len(errors),'errors');assert not errors
