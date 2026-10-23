"""Update content identity only for levels whose formal gameplay content changed."""
from formal_tools import *
import openpyxl,sys
revision=sys.argv[1];assert revision in['r2','r3','r4']
t=tables();records=json.loads((REPORT/'audit/current-source-records.json').read_text(encoding='utf-8'));edits=[];ei={r['id']:r for r in t['tbenemydata']};ri={r['id']:r for r in t['tbrounddata']};gi={r['id']:r for r in t['tbenemylist']}
for scene in t['tbsceneinfo']:
 level=scene['id']
 if level==1:continue
 rs=[ri[i]for i in scene['RoundList']];gs=[gi[i]for r in rs for i in r['EnemyIndexs']];ids=[i for g in gs for i in g['EnemyIndexs']];es=[ei[i]for i in sorted(set(ids))]
 content=dict(scene=scene,rounds=rs,groups=gs,enemies=es,map=next(m for m in t['tblevelmap']if m['id']==scene['mapId']))
 digest=hashlib.sha256(json.dumps(content,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();rating=next(r for r in t['tblevelrating']if r['id']==level)
 if digest==rating['planHash']:continue
 rec=records['LevelRating'][str(level)];wb=openpyxl.load_workbook(ROOT/rec['path'],read_only=True)
 decisions=dict(expectedWaveCount=len(rs),expectedEnemyCount=len(ids),bossVariantIds=sorted(e['id']for e in es if e['type']==5),criticalVariantIds=sorted(set(rating['criticalVariantIds']).intersection(ids)|{e['id']for e in es if e['type']==5}),balanceRevision='manual-100g-20261022-'+revision,ratingRevision='manual-reference-'+revision,planHash=digest,calibrationStatus='pending_unity_reference')
 for field,value in decisions.items():
  if isinstance(value,list):value=','.join(map(str,value))
  cell=rec['cells'][field];before=wb[rec['sheet']][cell].value
  if before!=value and not(before is None and value==''):edits.append(dict(path=rec['path'],sheet=rec['sheet'],cell=cell,before=before,after=value,reason='本关真实回放暴露的局部压力修订后，按正规导出更新内容身份、数量与有效关键集合，保留待校准状态'))
 wb.close()
f=REPORT/f'rating-identity-{revision}.cells.json';f.write_text(json.dumps(edits,ensure_ascii=False,indent=2),encoding='utf-8');print(len(edits),'identity cells',f)
