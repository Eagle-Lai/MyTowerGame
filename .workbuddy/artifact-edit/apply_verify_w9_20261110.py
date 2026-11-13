"""User-approved five-cell W9 patch: prepare, preserve OOXML, verify real Luban output."""
from pathlib import Path
from collections import Counter
import sys, json, hashlib, shutil, subprocess, re, zipfile, struct
from xml.sax.saxutils import escape
import openpyxl

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Library/BalanceStage/w9-candidate-apply-20261110'
STAGE=OUT/'source-authoring'
EXPECTED={6000080:537.084089,6000081:349.104669,6000082:988.234765,6000085:446.303791}
COUNTS=Counter({6000080:342,6000081:201,6000082:130,6000085:47})
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
normal=lambda v:','.join(map(str,v)) if isinstance(v,list) else v

def air_check(name):
    cmd=[sys.executable,str(ROOT/'.workbuddy/tools/check_air_spawn_order.py'),'--root',str(ROOT),'--source','both','--levels','2','--format','json']
    r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',env={**__import__('os').environ,'PYTHONIOENCODING':'utf-8'})
    (OUT/name).write_text(r.stdout,encoding='utf-8')
    assert r.returncode==0,(r.stderr,r.stdout[:800])
    j=json.loads(r.stdout);assert j['ok'];return j

def prepare():
    assert not (OUT/'scope-before.json').exists(),'Do not overwrite current baseline'
    STAGE.mkdir(parents=True,exist_ok=True)
    proposal=json.loads((ROOT/'Library/BalanceStage/w9-w25-design-20261110/manifest.json').read_text(encoding='utf-8'))
    white={('EnemyData',i,'hp') for i in EXPECTED}|{('EnemyList',2009,'EnemyIndexs')}
    edits=[e for e in proposal['edits'] if (e['table'],e['id'],e['field']) in white]
    assert len(edits)==5
    for e in edits:
        if e['table']=='EnemyData':assert e['value']==EXPECTED[e['id']]
        else:assert Counter(e['value'])==COUNTS
    base={'sources':{p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'Luban/Config/Datas').rglob('*.xlsx')},'exports':{}}
    for p in (ROOT/'Assets/ConfigJson').glob('*.json'):
        base['exports'][p.name]={'sha256':sha(p),'mtimeNs':p.stat().st_mtime_ns,'rows':json.loads(p.read_text(encoding='utf-8-sig'))}
    gen={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'Assets/Gen').rglob('*') if p.is_file()}
    (OUT/'generated-before.json').write_text(json.dumps(gen,indent=2),encoding='utf-8')
    for p in (ROOT/'Assets/Gen').glob('*.asmdef*'):shutil.copy2(p,OUT/p.name)
    manifest={'scope':'Only L02 W9, roundId 2009; four HP cells and one enemy list; user explicitly approved.',
              'sourceHashes':{t:base['sources'][f'Luban/Config/Datas/Levels/L02/{t}.xlsx'] for t in ('EnemyData','EnemyList')},'edits':edits}
    # Assert every old value and ID/column before any authoring.
    for t in ('EnemyData','EnemyList'):
        p=ROOT/f'Luban/Config/Datas/Levels/L02/{t}.xlsx';wb=openpyxl.load_workbook(p,read_only=True,data_only=False)
        ws=wb.worksheets[0];rr=list(ws.values);headers={v:k for k,v in enumerate(rr[0])};byid={r[headers['id']]:r for r in rr[3:] if isinstance(r[headers['id']],int)}
        for e in edits:
            if e['table']==t:assert byid[e['id']][headers[e['field']]]==normal(e['old'])
        wb.close()
    es={r['id']:r for r in base['exports']['tbenemydata.json']['rows']}
    gs={r['id']:r for r in base['exports']['tbenemylist.json']['rows']}
    for e in edits:
        if e['table']=='EnemyData':assert struct.pack('f',es[e['id']]['hp'])==struct.pack('f',e['old'])
        else:assert gs[2009]['EnemyIndexs']==e['old']
    for r in base['exports']['tbrounddata.json']['rows']:
        if r['id']!=2009:assert not set(COUNTS).intersection(i for g in r['EnemyIndexs'] for i in gs[g]['EnemyIndexs'])
    (OUT/'scope-before.json').write_text(json.dumps(base,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    air_check('air-order-before.json')
    print(json.dumps({'preparedEdits':5,'sourceFiles':len(base['sources']),'exportTables':len(base['exports']),'airBeforePassed':True}))

def commit():
    manifest=json.loads((STAGE/'located-manifest.json').read_text(encoding='utf-8'))
    assert {(e['table'],e['id'],e['field']) for e in manifest['edits']}=={('EnemyData',i,'hp') for i in EXPECTED}|{('EnemyList',2009,'EnemyIndexs')}
    prepared=[]
    for t in ('EnemyData','EnemyList'):
        p=ROOT/f'Luban/Config/Datas/Levels/L02/{t}.xlsx';assert sha(p)==manifest['sourceHashes'][t]
        original=p.read_bytes();wb=openpyxl.load_workbook(p,data_only=False)
        authored=openpyxl.load_workbook(STAGE/f'{t}.xlsx',data_only=False)
        edits=[e for e in manifest['edits'] if e['table']==t]
        with zipfile.ZipFile(p) as z:infos=z.infolist();entries={i.filename:z.read(i.filename) for i in infos}
        xml=entries['xl/worksheets/sheet1.xml'].decode('utf-8');white=[]
        for e in edits:
            assert e['sheet']=='Sheet'
            addr=openpyxl.utils.get_column_letter(e['col'])+str(e['row']);white.append(addr)
            assert wb[e['sheet']][addr].value==normal(e['old'])
            v=authored[e['sheet']][addr].value;assert v==normal(e['value'])
            pattern=rf'<(?P<prefix>(?:\w+:)?)c\b(?=[^>]*\br="{addr}")[^>]*>.*?</(?P=prefix)c>'
            matches=list(re.finditer(pattern,xml,re.S));assert len(matches)==1
            m=matches[0];cell=m.group();opening=re.sub(r'\s+t="[^"]*"','',cell[:cell.index('>')+1]);prefix=m.group('prefix')
            replacement=(opening[:-1]+f' t="inlineStr"><{prefix}is><{prefix}t>'+escape(v)+f'</{prefix}t></{prefix}is></{prefix}c>' if isinstance(v,str) else opening+f'<{prefix}v>{v}</{prefix}v></{prefix}c>')
            xml=xml[:m.start()]+replacement+xml[m.end():]
        def mask(data):
            txt=data.decode('utf-8')
            for addr in white:txt=re.sub(rf'<(?P<prefix>(?:\w+:)?)c\b(?=[^>]*\br="{addr}")[^>]*>.*?</(?P=prefix)c>',f'<AUTHORIZED:{addr}/>',txt,flags=re.S)
            return txt
        changed=xml.encode('utf-8');assert mask(entries['xl/worksheets/sheet1.xml'])==mask(changed)
        backup=STAGE/f'{t}-before.xlsx';assert not backup.exists();backup.write_bytes(original)
        dest=STAGE/f'{t}-patched.xlsx'
        with zipfile.ZipFile(dest,'w') as z:
            for info in infos:z.writestr(info,changed if info.filename=='xl/worksheets/sheet1.xml' else entries[info.filename])
        check=openpyxl.load_workbook(dest,data_only=False);allowed={(e['sheet'],e['row'],e['col']):normal(e['value']) for e in edits}
        assert wb.sheetnames==check.sheetnames
        for ws in wb:
            after=check[ws.title];assert (ws.max_row,ws.max_column)==(after.max_row,after.max_column)
            for row in ws:
                for c in row:assert after.cell(c.row,c.column).value==allowed.get((ws.title,c.row,c.column),c.value),(t,c.coordinate)
        with zipfile.ZipFile(dest) as z:
            assert z.namelist()==[i.filename for i in infos] and z.testzip() is None
            for k,v in entries.items():assert z.read(k)==(changed if k=='xl/worksheets/sheet1.xml' else v)
        wb.close();authored.close();check.close();prepared.append((p,dest,manifest['sourceHashes'][t]))
    for p,dest,old in prepared:assert sha(p)==old
    for p,dest,old in prepared:p.write_bytes(dest.read_bytes())
    (STAGE/'committed.json').write_text(json.dumps({'edits':manifest['edits'],'outsideWhitelistChanges':0},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'sourceCellsWritten':5,'outsideWhitelistChanges':0,'sourceReadbackPassed':True}))

def verify():
    base=json.loads((OUT/'scope-before.json').read_text(encoding='utf-8'))
    manifest=json.loads((STAGE/'located-manifest.json').read_text(encoding='utf-8'))
    allowed={f'Luban/Config/Datas/Levels/L02/{t}.xlsx' for t in ('EnemyData','EnemyList')}
    changed=[p for p,h in base['sources'].items() if sha(ROOT/p)!=h];assert set(changed)==allowed
    white={(f'tb{e["table"].lower()}.json',e['id'],e['field']):e['value'] for e in manifest['edits']}
    exports={};changed_exports=[]
    for name,old in base['exports'].items():
        p=ROOT/'Assets/ConfigJson'/name;rows=json.loads(p.read_text(encoding='utf-8-sig'));exports[name]=rows
        now={r['id']:r for r in rows};assert len(now)==len(rows)==len(old['rows'])
        for prev in old['rows']:
            cur=now[prev['id']];assert cur.keys()==prev.keys()
            for field,v in prev.items():
                key=(name,prev['id'],field)
                if key in white:
                    expected=white[key];assert cur[field]==expected if isinstance(expected,list) else struct.pack('f',cur[field])==struct.pack('f',expected)
                else:assert cur[field]==v,key
        if sha(p)!=old['sha256']:
            changed_exports.append(name);assert p.stat().st_mtime_ns>old['mtimeNs']
    assert set(changed_exports)=={'tbenemydata.json','tbenemylist.json'}
    es={r['id']:r for r in exports['tbenemydata.json']};gs={r['id']:r for r in exports['tbenemylist.json']}
    assert Counter(gs[2009]['EnemyIndexs'])==COUNTS and gs[2009]['enemyInterval']==224
    assert next(r for r in exports['tbrounddata.json'] if r['id']==2009)['rewardGold']==74
    assert len(exports['tbsceneinfo.json'])==30 and all(r['initialGold']==100 for r in exports['tbsceneinfo.json'])
    for e in manifest['edits']:
        wb=openpyxl.load_workbook(ROOT/f'Luban/Config/Datas/Levels/L02/{e["table"]}.xlsx',read_only=True,data_only=False)
        assert wb[e['sheet']].cell(e['row'],e['col']).value==normal(e['value']);wb.close()
    gen=json.loads((OUT/'generated-before.json').read_text(encoding='utf-8'))
    assert {p.relative_to(ROOT).as_posix() for p in (ROOT/'Assets/Gen').rglob('*') if p.is_file()}==set(gen)
    assert all(sha(ROOT/p)==h for p,h in gen.items())
    air_check('air-order-after.json')
    result={'sourceCellsVerified':5,'comparedSourceWorkbooks':len(base['sources']),'comparedJsonTables':len(exports),
            'changedSources':changed,'changedExports':changed_exports,'outsideWhitelistSourceChanges':0,'outsideWhitelistJsonChanges':0,
            'W8AndOtherWavesUnchanged':True,'otherLevelsUnchanged':True,'all30InitialGold100':True,'airBeforeAndAfterPassed':True,
            'generatedFilesUnchanged':len(gen),'W9Ground':673,'W9Air':47,'W9Total':720,'intervalMs':224,'roundReward':74}
    (OUT/'scope-after.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    {'prepare':prepare,'commit':commit,'verify':verify}[sys.argv[1]]()
