"""Read-only integrity and full 750-wave extraction from formal source/export."""
from formal_tools import *
import openpyxl,csv,collections,struct
parser=argparse.ArgumentParser();parser.add_argument('--tag',default='r1');args=parser.parse_args();tag=args.tag
assert tag in ['r1','r2','r3','r4','final']
t=tables();records=json.loads((REPORT/'audit/current-source-records.json').read_text(encoding='utf-8'))
books={};differences=[];checked=0
def normalized(value,template):
    if isinstance(template,str) and value is None:return ''
    if isinstance(template,dict):return dict(zip(template.keys(),map(float,str(value).split(','))))
    if isinstance(template,list) and template and isinstance(template[0],str):return str(value).split('|')
    if isinstance(template,list):return [] if value is None or value=='' else [int(x) for x in str(value).split(',')]
    if isinstance(template,bool):return bool(value)
    return value
def equivalent(a,b):
    if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all(equivalent(a[k],b[k])for k in a)
    if isinstance(a,float) or isinstance(b,float):return struct.pack('f',a)==struct.pack('f',b)
    return a==b
for tab,rows in records.items():
    exported={str(r['id']):r for r in t['tb'+tab.lower()]}
    for key,record in rows.items():
        path=record['path']
        if path not in books:books[path]=openpyxl.load_workbook(ROOT/path,read_only=False,data_only=False)
        row=exported.get(key)
        if row is None:differences.append(dict(table=tab,id=key,problem='missing export'));continue
        for field,cell in record['cells'].items():
            value=books[path][record['sheet']][cell].value;actual=normalized(value,row[field]);checked+=1
            if not equivalent(actual,row[field]):differences.append(dict(path=path,sheet=record['sheet'],cell=cell,field=field,source=actual,export=row[field]))
def location(record):return {k:v for k,v in record.items()if k!='data'}
waves=[];levels=[];ei={e['id']:e for e in t['tbenemydata']};ri={r['id']:r for r in t['tbrounddata']};gi={g['id']:g for g in t['tbenemylist']}
for scene in t['tbsceneinfo']:
    level=scene['id'];ls=[]
    for ordinal,rid in enumerate(scene['RoundList'],1):
        r=ri[rid];gs=[gi[i] for i in r['EnemyIndexs']];ids=[i for g in gs for i in g['EnemyIndexs']]
        variants=[dict(data=ei[i],count=ids.count(i),source=location(records['EnemyData'][str(i)])) for i in dict.fromkeys(ids)]
        row=dict(level=level,wave=ordinal,roundId=rid,groupIds=r['EnemyIndexs'],count=len(ids),air=sum(ei[i]['isFlying'] for i in ids),ehp=sum(ei[i]['hp']/(1-ei[i]['armor']) for i in ids),kill=sum(ei[i]['reward'] for i in ids),clear=r['rewardGold'],gap=gs[0]['enemyInterval'],roundDelay=r['interval'],groupDelay=gs[0]['interval'],orderedEnemyIds=ids,variants=variants,sourceRound=records['RoundData'][str(rid)],sourceGroups=[records['EnemyList'][str(g['id'])] for g in gs])
        row['sourceRound']=location(row['sourceRound']);row['sourceGroups']=[location(g)for g in row['sourceGroups']]
        waves.append(row);ls.append(row)
    levels.append(dict(level=level,initialGold=scene['initialGold'],mapId=scene['mapId'],waves=len(ls),count=sum(w['count'] for w in ls),air=sum(w['air'] for w in ls),ehp=sum(w['ehp'] for w in ls),kill=sum(w['kill'] for w in ls),clear=sum(w['clear'] for w in ls)))
result=dict(runtimeHash=runtime_hash(),checkedSourceCells=checked,differences=differences,sourceExportMatch=not differences,allInitialGold100=all(s['initialGold']==100 for s in t['tbsceneinfo']),all25Waves=all(len(s['RoundList'])==25 for s in t['tbsceneinfo']),sealMatch=all(r['runtimeContentHash']==runtime_hash() for r in t['tblevelrating']))
protected=json.loads((REPORT/'audit/protected-files-before.json').read_text(encoding='utf-8'));result['protectedMatches']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in protected.items()}
def allowed(p):
    return p=='Assets/Editor/Balance/BalancePlayModeVerifier.cs' or p.startswith('Assets/ConfigJson/') or p.startswith('Luban/Config/Datas/Levels/') and not p.endswith('LevelMap.xlsx') and ('/L01/' not in p or p.endswith('LevelRating.xlsx'))
result['unexpectedProtectedChanges']=[p for p,v in result['protectedMatches'].items()if not v and not allowed(p)]
external=REPORT/'audit/coordinated-external-changes.json'
result['coordinatedExternalChanges']=[]
if external.exists():
    agreement=json.loads(external.read_text(encoding='utf-8'))
    for p,e in agreement['files'].items():
        if p in result['unexpectedProtectedChanges'] and e['originalBaselineSha256']==protected[p] and e['frozenSha256']==hashlib.sha256((ROOT/p).read_bytes()).hexdigest():
            result['coordinatedExternalChanges'].append(dict(path=p,**e))
            result['unexpectedProtectedChanges'].remove(p)
for name,value in [(f'formal-waves-{tag}.json',waves),(f'formal-levels-{tag}.json',levels),(f'formal-integrity-{tag}.json',result)]:
    (REPORT/'audit'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
with (REPORT/f'audit/formal-waves-{tag}.csv').open('w',encoding='utf-8-sig',newline='') as f:
    fields=['level','wave','roundId','count','air','ehp','kill','clear','gap','roundDelay','groupDelay'];writer=csv.DictWriter(f,fields);writer.writeheader();writer.writerows({k:w[k] for k in fields}for w in waves)
print(json.dumps({k:v for k,v in result.items()if k!='protectedMatches'},ensure_ascii=False)[:2500]);assert not differences;assert not result['unexpectedProtectedChanges']
