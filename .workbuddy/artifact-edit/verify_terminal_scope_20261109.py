"""Verify authorized source cells, export values, protected records and starting gold."""
from pathlib import Path
import hashlib,json,struct
import openpyxl
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Library/BalanceStage/trusted-terminal-design-20261109'
before=json.loads((OUT/'scope-before.json').read_text(encoding='utf-8'))
manifest=json.loads((OUT/'source-authoring/located-manifest.json').read_text(encoding='utf-8'))
allowed={'EnemyData','EnemyList','RoundData'}
allowed_paths={f'Luban/Config/Datas/Levels/L02/{t}.xlsx' for t in allowed}
changed_sources=[]
for name,digest in before['sources'].items():
    current=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    if current!=digest:
        assert name in allowed_paths,f'Protected source changed: {name}'
        changed_sources.append(name)
assert len(changed_sources)==3,'Expected exactly three L02 source changes'
def exported_value(value):return ','.join(map(str,value)) if isinstance(value,list) else value
def equivalent(a,b):
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):
        return struct.pack('f',a)==struct.pack('f',b)
    return a==b
ids={t:{e['id'] for e in manifest['edits'] if e['table']==t} for t in allowed}
verified=0
current_exports={}
export_changes=[]
for name,base in before['exports'].items():
    file=ROOT/'Assets/ConfigJson'/name
    now=json.loads(file.read_text(encoding='utf-8-sig'));current_exports[name]=now
    table=next((t for t in allowed if name=='tb'+t.lower()+'.json'),None)
    protected={r['id']:r for r in base['rows'] if table is None or r['id'] not in ids[table]}
    lookup={r['id']:r for r in now}
    assert len(lookup)==len(now) and len(now)==len(base['rows']),f'Export IDs changed: {name}'
    for key,row in protected.items():assert lookup[key]==row,f'Protected exported row changed: {name}/{key}'
    digest=hashlib.sha256(file.read_bytes()).hexdigest()
    if digest!=base['sha256']:
        assert table is not None,f'Unexpected export change: {name}'
        assert file.stat().st_mtime_ns>base['mtimeNs'],f'Export mtime not advanced: {name}'
        export_changes.append({'file':str(file),'beforeSha256':base['sha256'],'afterSha256':digest,'mtimeNs':file.stat().st_mtime_ns})
assert len(export_changes)==3,'Three exported JSON files must actually change'
for table in sorted(allowed):
    book=openpyxl.load_workbook(ROOT/f'Luban/Config/Datas/Levels/L02/{table}.xlsx',data_only=False)
    export={r['id']:r for r in current_exports['tb'+table.lower()+'.json']}
    for e in manifest['edits']:
        if e['table']!=table:continue
        cell=book[e['sheet']].cell(e['row'],e['col'])
        assert cell.value==exported_value(e['value']),f'Source readback: {table}/{cell.coordinate}'
        assert equivalent(export[e['id']][e['field']],e['value']),f'Source/export mismatch: {table}/{e["id"]}/{e["field"]}'
        verified+=1
    book.close()
scenes=current_exports['tbsceneinfo.json']
assert len(scenes)==30 and all(s['initialGold']==100 for s in scenes),'initialGold must be 100 in all 30 levels'
report={'sourceCellsVerified':verified,'changedSourceFiles':changed_sources,'protectedSourceChanges':0,
        'protectedExportRecordChanges':0,'changedExports':export_changes,'initialGold100Levels':len(scenes)}
(OUT/'scope-after.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
