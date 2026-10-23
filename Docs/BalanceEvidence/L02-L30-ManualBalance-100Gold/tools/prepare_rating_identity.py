"""Derive identity/integrity metadata from the actual formal export, not a recipe."""
from formal_tools import *
import openpyxl
t=tables();source=json.loads((REPORT/'audit/current-source-records.json').read_text(encoding='utf-8'));edits=[]
e={r['id']:r for r in t['tbenemydata']};groups={r['id']:r for r in t['tbenemylist']};rounds={r['id']:r for r in t['tbrounddata']}
for s in t['tbsceneinfo']:
    level=s['id']
    if level==1:continue
    rs=[rounds[i] for i in s['RoundList']];gs=[groups[i] for r in rs for i in r['EnemyIndexs']];ids=[i for g in gs for i in g['EnemyIndexs']]
    es=[e[i] for i in sorted(set(ids))];boss=sorted(x['id'] for x in es if x['type']==5)
    rating=next(r for r in t['tblevelrating'] if r['id']==level)
    critical=sorted(set(boss)|set(rating['criticalVariantIds']).intersection(ids))
    content=dict(scene=s,rounds=rs,groups=gs,enemies=es,map=next(m for m in t['tblevelmap'] if m['id']==s['mapId']))
    digest=hashlib.sha256(json.dumps(content,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    decisions=dict(expectedWaveCount=25,expectedEnemyCount=len(ids),bossVariantIds=boss,criticalVariantIds=critical,balanceRevision='manual-100g-20261022-r1',ratingRevision='manual-reference-r1',planHash=digest,calibrationStatus='pending_unity_reference')
    record=source['LevelRating'][str(level)];p=ROOT/record['path'];wb=openpyxl.load_workbook(p,read_only=True)
    for field,value in decisions.items():
        cell=record['cells'][field];old=wb[record['sheet']][cell].value
        if isinstance(value,list):value=','.join(map(str,value))
        if value=='' and old is None:continue
        if value!=old:edits.append(dict(path=record['path'],sheet=record['sheet'],cell=cell,before=old,after=value,reason='本关正式有序引用核对数量和Boss，内容摘要取当前正规导出；新手工设计版本，待真实参考回放校准'))
    wb.close()
out=REPORT/'rating-identity-r1.cells.json';out.write_text(json.dumps(edits,ensure_ascii=False,indent=2),encoding='utf-8');print(out,len(edits))
