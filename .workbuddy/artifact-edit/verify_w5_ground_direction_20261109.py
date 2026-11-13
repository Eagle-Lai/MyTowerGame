"""Read-only verification against this request's preserved baseline."""
from pathlib import Path
import hashlib,json,struct,sys
import openpyxl
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/(sys.argv[1] if len(sys.argv)>1 else 'Library/BalanceStage/w5-ground-direction-20261109')
base=json.loads((OUT/'scope-before.json').read_text(encoding='utf-8'))
manifest=json.loads((OUT/'source-authoring/located-manifest.json').read_text(encoding='utf-8'))
edits=manifest['edits']
mandatory={('EnemyData',6000040,'hp'),('EnemyData',6000041,'hp'),('EnemyData',6000042,'hp')}
w6={('EnemyData',i,'hp') for i in (6000050,6000051,6000052,6000055)}|{('EnemyList',2006,'EnemyIndexs')}
w6_hp_only={('EnemyData',i,'hp') for i in (6000050,6000051,6000052,6000055)}
promotion={('EnemyData',i,'hp') for i in (6000040,6000041,6000042,6000050,6000051,6000052)}|{('EnemyList',g,'EnemyIndexs') for g in (2005,2006)}
edit_keys={(e['table'],e['id'],e['field']) for e in edits}
assert len(edits)==len(edit_keys) and edit_keys in (mandatory,mandatory|{('EnemyList',2005,'EnemyIndexs')},{('EnemyData',6000045,'hp')},w6,w6_hp_only,promotion)
target_groups=[2005,2006] if edit_keys==promotion else [2006] if edit_keys in (w6,w6_hp_only) else [2005]
changed=[]
allowed={f'Luban/Config/Datas/Levels/L02/{e["table"]}.xlsx' for e in edits}
allowed_exports={f'tb{e["table"].lower()}.json' for e in edits}
for name,digest in base['sources'].items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
        assert name in allowed,name
        changed.append(name)
assert set(changed)==allowed
white={(f'tb{e["table"].lower()}.json',e['id'],e['field']):e for e in edits}
exports={}
export_changed=[]
for name,old in base['exports'].items():
    file=ROOT/'Assets/ConfigJson'/name
    now=json.loads(file.read_text(encoding='utf-8-sig'));exports[name]=now
    current={r['id']:r for r in now}
    assert len(current)==len(now)==len(old['rows'])
    for row in old['rows']:
        assert row.keys()==current[row['id']].keys()
        for field,previous in row.items():
            key=(name,row['id'],field)
            actual=current[row['id']][field]
            if key in white:
                target=white[key]['value']
                assert struct.pack('f',actual)==struct.pack('f',target) if isinstance(target,(int,float)) else actual==target,key
            else:assert actual==previous,key
    if hashlib.sha256(file.read_bytes()).hexdigest()!=old['sha256']:
        assert name in allowed_exports
        assert file.stat().st_mtime_ns>old['mtimeNs']
        export_changed.append(name)
assert set(export_changed)==allowed_exports
for table in {e['table'] for e in edits}:
    book=openpyxl.load_workbook(ROOT/f'Luban/Config/Datas/Levels/L02/{table}.xlsx',data_only=False)
    for e in edits:
        if e['table']!=table:continue
        expect=','.join(map(str,e['value'])) if isinstance(e['value'],list) else e['value']
        assert book[e['sheet']].cell(e['row'],e['col']).value==expect
    book.close()
assert len(exports['tbsceneinfo.json'])==30 and all(s['initialGold']==100 for s in exports['tbsceneinfo.json'])
es={r['id']:r for r in exports['tbenemydata.json']}
old_groups={r['id']:r for r in base['exports']['tbenemylist.json']['rows']}
new_groups={r['id']:r for r in exports['tbenemylist.json']}
group_reports=[]
for target_group in target_groups:
    old_seq=old_groups[target_group]['EnemyIndexs'];new_seq=new_groups[target_group]['EnemyIndexs']
    old_air=[i for i in old_seq if es[i]['isFlying']!=0];new_air=[i for i in new_seq if es[i]['isFlying']!=0]
    if edit_keys==promotion:
        it=iter(new_seq)
        assert all(any(i==wanted for i in it) for wanted in old_seq),'Original spawn order changed'
        assert len(new_air)>=len(old_air)
    else:assert old_air==new_air
    if not any(e['table']=='EnemyList' for e in edits):assert old_seq==new_seq
    group_reports.append({'groupId':target_group,'oldCount':len(old_seq),'newCount':len(new_seq),'oldAir':len(old_air),'newAir':len(new_air)})
if edit_keys==promotion:
    old_es={r['id']:r for r in base['exports']['tbenemydata.json']['rows']}
    for i5,i6 in ((6000040,6000050),(6000041,6000051),(6000042,6000052),(6000045,6000055)):
        assert struct.pack('f',es[i5]['hp'])==struct.pack('f',old_es[i6]['hp'])
        assert new_groups[2005]['EnemyIndexs'].count(i5)==old_groups[2006]['EnemyIndexs'].count(i6)
        assert es[i6]['hp']>=es[i5]['hp']
        assert new_groups[2006]['EnemyIndexs'].count(i6)>new_groups[2005]['EnemyIndexs'].count(i5)
report={'verifiedSourceCells':len(edits),'changedSources':changed,'changedExports':export_changed,'otherSourceChanges':0,'outsideWhitelistExportChanges':0,
        'all30InitialGold100':True,'originalAirIdsOrderPreserved':True,'groups':group_reports,'W5CopiedPreChangeW6':edit_keys==promotion}
(OUT/'scope-after.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
