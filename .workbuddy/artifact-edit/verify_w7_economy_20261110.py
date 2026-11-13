"""Read-only verification of the explicitly approved five L02 W7 cells."""
from pathlib import Path
from collections import Counter
import hashlib,json,struct,openpyxl

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Library/BalanceStage/w7-economy-apply-20261110'
base=json.loads((OUT/'scope-before.json').read_text(encoding='utf-8'))
manifest=json.loads((OUT/'source-authoring/located-manifest.json').read_text(encoding='utf-8'))
edits=manifest['edits']
expected_keys={('EnemyData',i,'hp') for i in (6000060,6000061,6000062,6000065)}|{('EnemyList',2007,'EnemyIndexs')}
assert len(edits)==5 and {(e['table'],e['id'],e['field']) for e in edits}==expected_keys
expected_hp={6000060:373.371334,6000061:242.691359,6000062:687.003288,6000065:311.548419}
expected_counts=Counter({6000060:297,6000061:174,6000062:110,6000065:31})
allowed_sources={f'Luban/Config/Datas/Levels/L02/{t}.xlsx' for t in ('EnemyData','EnemyList')}
sources_changed=[]
assert {p.relative_to(ROOT).as_posix() for p in (ROOT/'Luban/Config/Datas').rglob('*.xlsx')}==set(base['sources'])
for rel,oldhash in base['sources'].items():
    if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=oldhash:
        assert rel in allowed_sources,rel
        sources_changed.append(rel)
assert set(sources_changed)==allowed_sources
for table in ('EnemyData','EnemyList'):
    b=openpyxl.load_workbook(ROOT/f'Luban/Config/Datas/Levels/L02/{table}.xlsx',read_only=True,data_only=False)
    for e in edits:
        if e['table']!=table:continue
        expected=','.join(map(str,e['value'])) if isinstance(e['value'],list) else e['value']
        assert b[e['sheet']].cell(e['row'],e['col']).value==expected,(table,e['id'])
    b.close()
white={(f'tb{e["table"].lower()}.json',e['id'],e['field']):e['value'] for e in edits}
exports={};exports_changed=[]
assert {p.name for p in (ROOT/'Assets/ConfigJson').glob('*.json')}==set(base['exports'])
for name,old in base['exports'].items():
    p=ROOT/'Assets/ConfigJson'/name
    now=json.loads(p.read_text(encoding='utf-8-sig'));exports[name]=now
    by_id={r['id']:r for r in now}
    assert len(now)==len(by_id)==len(old['rows'])
    for row in old['rows']:
        actual=by_id[row['id']];assert row.keys()==actual.keys()
        for field,previous in row.items():
            k=(name,row['id'],field)
            if k in white:
                expected=white[k]
                assert actual[field]==expected if isinstance(expected,list) else struct.pack('f',actual[field])==struct.pack('f',expected),k
            else:assert actual[field]==previous,k
    if hashlib.sha256(p.read_bytes()).hexdigest()!=old['sha256']:
        assert name in ('tbenemydata.json','tbenemylist.json')
        assert p.stat().st_mtime_ns>old['mtimeNs']
        exports_changed.append(name)
assert set(exports_changed)=={'tbenemydata.json','tbenemylist.json'}
es={r['id']:r for r in exports['tbenemydata.json']};gs={r['id']:r for r in exports['tbenemylist.json']}
seq=gs[2007]['EnemyIndexs'];assert Counter(seq)==expected_counts
for eid,hp in expected_hp.items():assert struct.pack('f',es[eid]['hp'])==struct.pack('f',hp)
assert gs[2007]['enemyInterval']==238
rounds={r['id']:r for r in exports['tbrounddata.json']}
assert rounds[2007]['rewardGold']==74 and rounds[2006]['rewardGold']==74
assert all(r['initialGold']==100 for r in exports['tbsceneinfo.json']) and len(exports['tbsceneinfo.json'])==30
def source_records(level,table):
    b=openpyxl.load_workbook(ROOT/f'Luban/Config/Datas/Levels/L{level:02}/{table}.xlsx',read_only=True,data_only=False)
    rr=list(b.worksheets[0].values);heads=rr[0]
    result={r[1]:{h:r[i] for i,h in enumerate(heads) if h and h!='##'} for r in rr[3:] if len(r)>1 and isinstance(r[1],int)}
    b.close();return result
e1=source_records(1,'EnemyData');g1=source_records(1,'EnemyList');r1=source_records(1,'RoundData')[7]
ids=lambda value:[int(i) for i in str(value).split(',')]
ref=[i for g in ids(r1['EnemyIndexs']) for i in ids(g1[g]['EnemyIndexs'])]
new_by_type={(es[i]['resName'],es[i]['isFlying']!=0):i for i in expected_counts}
mapped=[new_by_type[e1[i]['resName'],e1[i]['isFlying']!=0] for i in ref]
iterator=iter(seq)
assert all(any(actual==wanted for actual in iterator) for wanted in mapped),'Trusted L01 sequence skeleton lost'
full=[]
scene2=next(r for r in exports['tbsceneinfo.json'] if r['id']==2)
for rid in scene2['RoundList']:
    for gid in rounds[rid]['EnemyIndexs']:full.extend(gs[gid]['EnemyIndexs'])
assert not any(es[a]['isFlying']!=0 and es[b]['isFlying']!=0 for a,b in zip(full,full[1:]))
for r in exports['tbrounddata.json']:
    if r['id']==2007:continue
    assert not set(expected_counts).intersection(i for gid in r['EnemyIndexs'] for i in gs[gid]['EnemyIndexs'])
report={'verifiedSourceCells':5,'changedSources':sources_changed,'changedExports':exports_changed,
        'outsideWhitelistSourceChanges':0,'outsideWhitelistExportChanges':0,'W6Unchanged':True,
        'otherWavesAndLevelsUnchanged':True,'all30InitialGold100':True,
        'trustedL01SequenceSkeletonPreserved':True,'L02CrossWaveAirSeparationPassed':True,
        'W7Counts':dict(Counter(seq)),'W7Total':len(seq),'W7Ground':sum(es[i]['isFlying']==0 for i in seq),
        'W7Air':sum(es[i]['isFlying']!=0 for i in seq),'W7IntervalMs':238,'W7RoundReward':74}
(OUT/'scope-after.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
