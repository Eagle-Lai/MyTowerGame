"""Apply only the user-approved L02 W10-W25 HP/list cells; verify real Luban outputs."""
from pathlib import Path
from collections import Counter
import json, hashlib, sys, subprocess, os, shutil, struct, datetime
import openpyxl

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Library/BalanceStage/w10-w25-apply-20261110'
STAGE=OUT/'source-authoring'
DESIGN=ROOT/'Library/BalanceStage/w9-w25-design-20261110'
CALC=json.loads((DESIGN/'calculation.json').read_text(encoding='utf-8'))
WAVES=[w for w in CALC['waves'] if 10<=w['wave']<=25]
ROWS=[r for r in CALC['rows'] if 10<=r['wave']<=25]
IDS={r['id'] for r in ROWS}
RIDS={w['roundId'] for w in WAVES}
WHITE={('EnemyData',i,'hp') for i in IDS}|{('EnemyList',i,'EnemyIndexs') for i in RIDS}
assert len(WAVES)==16 and len(ROWS)==len(IDS)==80 and len(WHITE)==96
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
normal=lambda v:','.join(map(str,v)) if isinstance(v,list) else v

def air_check(name):
    p=subprocess.run([sys.executable,str(ROOT/'.workbuddy/tools/check_air_spawn_order.py'),'--root',str(ROOT),'--source','both','--levels','2','--format','json'],
                     capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONIOENCODING':'utf-8'})
    (OUT/name).write_text(p.stdout,encoding='utf-8')
    assert p.returncode==0,(p.stderr,p.stdout[:1000]);assert json.loads(p.stdout)['ok']

def prepare():
    assert not (OUT/'scope-before.json').exists(),'Preserve previous attempt baseline; inspect before resuming'
    STAGE.mkdir(parents=True,exist_ok=True)
    design_hashes=json.loads((DESIGN/'source-hashes.json').read_text(encoding='utf-8'))
    # Reuse accepted calculations only while their trusted inputs remain unchanged.
    for rel,h in design_hashes.items():
        if rel.startswith('Luban/Config/Datas/Levels/L01/') or (rel.startswith('Luban/Config/Datas/Levels/L02/') and Path(rel).stem not in ('EnemyData','EnemyList')) or rel=='Luban/Config/Datas/WaveTuning.xlsx':
            assert sha(ROOT/rel)==h,('Design input changed',rel)
    proposal=json.loads((DESIGN/'manifest.json').read_text(encoding='utf-8'))
    edits=[e for e in proposal['edits'] if (e['table'],e['id'],e['field']) in WHITE]
    assert len(edits)==96 and {(e['table'],e['id'],e['field']) for e in edits}==WHITE
    for r in ROWS:assert next(e for e in edits if e['table']=='EnemyData' and e['id']==r['id'])['value']==r['newHp']
    for w in WAVES:
        seq=next(e['value'] for e in edits if e['table']=='EnemyList' and e['id']==w['roundId'])
        assert Counter(seq)==Counter({r['id']:r['count'] for r in w['roster']})
    base={'sources':{p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'Luban/Config/Datas').rglob('*.xlsx')},'exports':{}}
    for p in (ROOT/'Assets/ConfigJson').glob('*.json'):
        base['exports'][p.name]={'sha256':sha(p),'mtimeNs':p.stat().st_mtime_ns,'rows':json.loads(p.read_text(encoding='utf-8-sig'))}
    gen={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'Assets/Gen').rglob('*') if p.is_file()}
    (OUT/'generated-before.json').write_text(json.dumps(gen,indent=2),encoding='utf-8')
    for p in (ROOT/'Assets/Gen').glob('*.asmdef*'):shutil.copy2(p,OUT/p.name)
    for t in ('EnemyData','EnemyList'):
        wb=openpyxl.load_workbook(ROOT/f'Luban/Config/Datas/Levels/L02/{t}.xlsx',read_only=True,data_only=False)
        rr=list(wb.worksheets[0].values);headers={h:k for k,h in enumerate(rr[0])};byid={r[headers['id']]:r for r in rr[3:] if isinstance(r[headers['id']],int)}
        for e in edits:
            if e['table']==t:assert byid[e['id']][headers[e['field']]]==normal(e['old']),(t,e['id'],'old mismatch')
        wb.close()
    es={r['id']:r for r in base['exports']['tbenemydata.json']['rows']};gs={r['id']:r for r in base['exports']['tbenemylist.json']['rows']}
    rounds={r['id']:r for r in base['exports']['tbrounddata.json']['rows']}
    scene=next(r for r in base['exports']['tbsceneinfo.json']['rows'] if r['id']==2)
    assert scene['RoundList'][9:25]==[w['roundId'] for w in WAVES]
    for e in edits:
        if e['table']=='EnemyData':assert struct.pack('f',es[e['id']]['hp'])==struct.pack('f',e['old'])
        else:assert gs[e['id']]['EnemyIndexs']==e['old']
    accepted={6000080:(537.084089,342),6000081:(349.104669,201),6000082:(988.234765,130),6000085:(446.303791,47)}
    c9=Counter(gs[2009]['EnemyIndexs'])
    for i,(hp,n) in accepted.items():assert struct.pack('f',es[i]['hp'])==struct.pack('f',hp) and c9[i]==n
    for rid,r in rounds.items():
        if rid not in RIDS:assert not IDS.intersection(i for gid in r['EnemyIndexs'] for i in gs[gid]['EnemyIndexs']),('HP IDs shared outside scope',rid)
    manifest={'scope':'Only L02 W10-W25; 80 HP cells and 16 list cells. W9 playtested accepted; user explicitly authorized application of published algorithm candidates.',
              'sourceHashes':{t:base['sources'][f'Luban/Config/Datas/Levels/L02/{t}.xlsx'] for t in ('EnemyData','EnemyList')},'edits':edits}
    (OUT/'scope-before.json').write_text(json.dumps(base,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    air_check('air-order-before.json')
    print(json.dumps({'sourceCells':96,'hpCells':80,'listCells':16,'sourceWorkbooks':len(base['sources']),'jsonTables':len(base['exports']),'W9AcceptedBaselineMatched':True,'airBeforePassed':True}))

def verify():
    base=json.loads((OUT/'scope-before.json').read_text(encoding='utf-8'))
    manifest=json.loads((STAGE/'located-manifest.json').read_text(encoding='utf-8'))
    assert {(e['table'],e['id'],e['field']) for e in manifest['edits']}==WHITE
    source_paths={p.relative_to(ROOT).as_posix() for p in (ROOT/'Luban/Config/Datas').rglob('*.xlsx')}
    assert source_paths==set(base['sources'])
    changed=[p for p,h in base['sources'].items() if sha(ROOT/p)!=h]
    assert set(changed)=={f'Luban/Config/Datas/Levels/L02/{t}.xlsx' for t in ('EnemyData','EnemyList')}
    for t in ('EnemyData','EnemyList'):
        wb=openpyxl.load_workbook(ROOT/f'Luban/Config/Datas/Levels/L02/{t}.xlsx',read_only=True,data_only=False)
        for e in manifest['edits']:
            if e['table']==t:assert wb[e['sheet']].cell(e['row'],e['col']).value==normal(e['value'])
        wb.close()
    white={(f'tb{e["table"].lower()}.json',e['id'],e['field']):e['value'] for e in manifest['edits']}
    exports={};changed_exports=[]
    assert {p.name for p in (ROOT/'Assets/ConfigJson').glob('*.json')}==set(base['exports'])
    for name,old in base['exports'].items():
        p=ROOT/'Assets/ConfigJson'/name;rows=json.loads(p.read_text(encoding='utf-8-sig'));exports[name]=rows
        now={r['id']:r for r in rows};assert len(now)==len(rows)==len(old['rows'])
        for prev in old['rows']:
            cur=now[prev['id']];assert cur.keys()==prev.keys()
            for field,v in prev.items():
                key=(name,prev['id'],field)
                if key in white:
                    expected=white[key];assert cur[field]==expected if isinstance(expected,list) else struct.pack('f',cur[field])==struct.pack('f',expected),key
                else:assert cur[field]==v,key
        if sha(p)!=old['sha256']:
            changed_exports.append(name);assert p.stat().st_mtime_ns>old['mtimeNs']
    assert set(changed_exports)=={'tbenemydata.json','tbenemylist.json'}
    es={r['id']:r for r in exports['tbenemydata.json']};gs={r['id']:r for r in exports['tbenemylist.json']};rs={r['id']:r for r in exports['tbrounddata.json']}
    for w in WAVES:
        rid=w['roundId'];assert Counter(gs[rid]['EnemyIndexs'])==Counter({r['id']:r['count'] for r in w['roster']})
        assert gs[rid]['enemyInterval']==w['intervalMs'] and rs[rid]['rewardGold']==w['roundReward']
    scene=next(r for r in exports['tbsceneinfo.json'] if r['id']==2)
    economy=100.
    for rid in scene['RoundList']:
        economy+=sum(es[i]['reward'] for gid in rs[rid]['EnemyIndexs'] for i in gs[gid]['EnemyIndexs'])+rs[rid]['rewardGold']
    assert abs(economy-CALC['newTotalEconomy'])<0.001
    assert len(exports['tbsceneinfo.json'])==30 and all(r['initialGold']==100 for r in exports['tbsceneinfo.json'])
    gen=json.loads((OUT/'generated-before.json').read_text(encoding='utf-8'))
    assert {p.relative_to(ROOT).as_posix() for p in (ROOT/'Assets/Gen').rglob('*') if p.is_file()}==set(gen)
    assert all(sha(ROOT/p)==h for p,h in gen.items())
    air_check('air-order-after.json')
    result={'sourceCellsVerified':96,'hpCells':80,'listCells':16,'comparedSourceWorkbooks':len(base['sources']),'comparedJsonTables':len(exports),
            'changedSources':changed,'changedExports':changed_exports,'outsideWhitelistSourceChanges':0,'outsideWhitelistJsonChanges':0,
            'W1ThroughW9Unchanged':True,'otherLevelsUnchanged':True,'all30InitialGold100':True,'airBeforeAndAfterPassed':True,
            'generatedFilesUnchanged':len(gen),'L02TotalEarnedFromExport':economy,'L02TotalEarnedSourcePrecision':CALC['newTotalEconomy'],
            'roundIds':[w['roundId'] for w in WAVES],'exportedAtShanghai':datetime.datetime.fromtimestamp((ROOT/'Assets/ConfigJson/tbenemydata.json').stat().st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat()}
    (OUT/'scope-after.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':{'prepare':prepare,'verify':verify}[sys.argv[1]]()
