"""Read current trusted L01 sources and current L02 values without modifying workbooks."""
from pathlib import Path
import hashlib,json,sys,struct
from collections import Counter
import openpyxl

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/sys.argv[1]
baseline=json.loads((OUT/'scope-before.json').read_text(encoding='utf-8'))
result={}
for level in (1,2):
    tables={}
    for table in ('EnemyData','EnemyList','RoundData','SceneInfo','TowerInfo','BulletData','LevelMap'):
        file=ROOT/f'Luban/Config/Datas/Levels/L{level:02}/{table}.xlsx'
        relative=file.relative_to(ROOT).as_posix()
        digest=hashlib.sha256(file.read_bytes()).hexdigest()
        assert baseline['sources'][relative]==digest,relative
        book=openpyxl.load_workbook(file,read_only=True,data_only=False)
        for extra in book.worksheets[1:]:
            assert not any(any(v is not None for v in r) for r in extra.values),'Unexpected populated extra sheet'
        sheet=book.worksheets[0]
        rows=list(sheet.values)
        heads=rows[0]
        records=[{key:row[i] if i<len(row) else None for i,key in enumerate(heads) if key and key!='##'}
                 for row in rows[3:] if len(row)>1 and isinstance(row[1],int)]
        assert len({r['id'] for r in records})==len(records)
        tables[table]={'path':relative,'sheet':sheet.title,'sha256':digest,'records':records}
        book.close()
    result[f'L{level:02}']=tables

def ids(value):
    return [int(s) for s in str(value).split(',') if s.strip()]
def wave(tables,ordinal):
    scene=tables['SceneInfo']['records'][0]
    rounds={r['id']:r for r in tables['RoundData']['records']}
    groups={r['id']:r for r in tables['EnemyList']['records']}
    row=rounds[ids(scene['RoundList'])[ordinal-1]]
    return row,[i for g in ids(row['EnemyIndexs']) for i in ids(groups[g]['EnemyIndexs'])]
for level in (1,2):
    tables=result[f'L{level:02}']
    row,sequence=wave(tables,5)
    tables['W5']={'round':row,'sequence':sequence}
    assert tables['SceneInfo']['records'][0]['initialGold']==100
    es={r['id']:r for r in tables['EnemyData']['records']}
    tables['W5']['counts']={str(i):n for i,n in Counter(sequence).items()}
    if level==2:
        assert row['id']==2005 and ids(row['EnemyIndexs'])==[2005]
        ground={i for i in sequence if es[i]['isFlying']==0}
        assert ground=={6000040,6000041,6000042}
        assert Counter(sequence)[6000045]==12
        for n in range(1,26):
            if n!=5:assert not ((ground|{6000045}) & set(wave(tables,n)[1])),f'W5 IDs shared with W{n}'
        exported={r['id']:r for r in baseline['exports']['tbenemydata.json']['rows']}
        for i in set(sequence):
            for field in ('hp','speed','armor','reward'):
                assert struct.pack('f',es[i][field])==struct.pack('f',exported[i][field]),(i,field)
        eg=next(r for r in baseline['exports']['tbenemylist.json']['rows'] if r['id']==2005)
        assert sequence==eg['EnemyIndexs']

target=OUT/'current-source-inputs.json'
assert not target.exists(),'Preserve original input snapshot'
target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'input':str(target),'L01W5Counts':result['L01']['W5']['counts'],
                  'L02W5Counts':result['L02']['W5']['counts'],'allModifiedIdsExclusiveToW5':True}))
