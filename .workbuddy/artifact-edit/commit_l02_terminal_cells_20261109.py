"""Copy only authorized artifact-authored cell values into the original OOXML package."""
import copy,hashlib,json,re,zipfile,sys
from pathlib import Path
from xml.sax.saxutils import escape
import openpyxl
ROOT=Path(__file__).resolve().parents[2]
stage_arg=sys.argv[sys.argv.index('--stage')+1] if '--stage' in sys.argv else 'Library/BalanceStage/trusted-terminal-design-20261109/source-authoring'
STAGE=ROOT/stage_arg
manifest=json.loads((STAGE/'located-manifest.json').read_text(encoding='utf-8'))
def colname(n):
    s=''
    while n:n,r=divmod(n-1,26);s=chr(65+r)+s
    return s
def normal(v):return ','.join(map(str,v)) if isinstance(v,list) else v
prepared=[]
for table in dict.fromkeys(e['table'] for e in manifest['edits']):
    file=ROOT/'Luban/Config/Datas/Levels/L02'/f'{table}.xlsx'
    original=file.read_bytes()
    expected=manifest['sourceHashes'][table]
    assert hashlib.sha256(original).hexdigest()==expected, f'Source changed: {file}'
    entries={}
    with zipfile.ZipFile(file) as archive:
        infos=archive.infolist()
        for info in infos: entries[info.filename]=archive.read(info.filename)
    beforebook=openpyxl.load_workbook(file,data_only=False)
    authored=openpyxl.load_workbook(STAGE/f'{table}.xlsx',data_only=False)
    edits=[e for e in manifest['edits'] if e['table']==table and e['old']!=e['value']]
    white=set()
    xml=entries['xl/worksheets/sheet1.xml'].decode('utf-8')
    for e in edits:
        addr=colname(e['col'])+str(e['row']);white.add((e['sheet'],addr))
        assert beforebook[e['sheet']][addr].value==normal(e['old']),f'Old value changed: {addr}'
        value=authored[e['sheet']][addr].value
        assert value==normal(e['value']),f'Authored value changed: {addr}'
        pattern=rf'<(?P<prefix>(?:\w+:)?)c\b(?=[^>]*\br="{addr}")[^>]*>.*?</(?P=prefix)c>'
        matches=list(re.finditer(pattern,xml,re.S));assert len(matches)==1,(table,addr)
        cell=matches[0].group();opening=cell[:cell.index('>')+1]
        opening=re.sub(r'\s+t="[^"]*"','',opening)
        prefix=matches[0].group('prefix')
        if isinstance(value,str):replacement=opening[:-1]+f' t="inlineStr"><{prefix}is><{prefix}t>'+escape(value)+f'</{prefix}t></{prefix}is></{prefix}c>'
        else: replacement=opening+f'<{prefix}v>'+str(value)+f'</{prefix}v></{prefix}c>'
        xml=xml[:matches[0].start()]+replacement+xml[matches[0].end():]
    changedxml=xml.encode('utf-8')
    # Strip authorized cells; everything else in the worksheet must be byte-identical.
    def mask(data):
        text=data.decode('utf-8')
        for _,addr in white:text=re.sub(rf'<(?P<prefix>(?:\w+:)?)c\b(?=[^>]*\br="{addr}")[^>]*>.*?</(?P=prefix)c>',f'<AUTHORIZED:{addr}/>',text,flags=re.S)
        return text
    assert mask(entries['xl/worksheets/sheet1.xml'])==mask(changedxml),'Non-whitelist XML changed'
    backup=STAGE/f'{table}-before.xlsx'
    if backup.exists():assert backup.read_bytes()==original,'Preserved baseline differs'
    else:backup.write_bytes(original)
    entries['xl/worksheets/sheet1.xml']=changedxml
    temp=STAGE/f'{table}-patched.xlsx'
    with zipfile.ZipFile(temp,'w') as archive:
        for info in infos:archive.writestr(info,entries[info.filename])
    check=openpyxl.load_workbook(temp,data_only=False)
    for sheet in beforebook:
        after=check[sheet.title]
        assert sheet.max_row==after.max_row and sheet.max_column==after.max_column
        for row in sheet:
            for cell in row:
                if (sheet.title,cell.coordinate) not in white:assert cell.value==after[cell.coordinate].value,cell.coordinate
        for e in edits:
            if e['sheet']==sheet.title:assert after.cell(e['row'],e['col']).value==normal(e['value'])
    with zipfile.ZipFile(temp) as archive:
        for info in infos:
            if info.filename!='xl/worksheets/sheet1.xml':assert archive.read(info.filename)==entries[info.filename]
    prepared.append((file,temp,expected,len(edits)))
    beforebook.close();authored.close();check.close()
# Validate all files before the first source mutation.
for file,temp,expected,count in prepared:
    assert hashlib.sha256(file.read_bytes()).hexdigest()==expected
if '--commit' not in sys.argv:
    print(json.dumps({'mode':'dry-run','validatedCells':sum(x[3] for x in prepared),'outsideWhitelistChanges':0,'sourceFilesWritten':0}))
    raise SystemExit(0)
for file,temp,expected,count in prepared:
    file.write_bytes(temp.read_bytes())
    assert file.read_bytes()==temp.read_bytes()
    print(json.dumps({'file':str(file),'changedCells':count,'outsideWhitelistChanges':0,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}))
(STAGE/'committed.json').write_text(json.dumps({'files':[str(x[0]) for x in prepared],'edits':manifest['edits'],'outsideWhitelistChanges':0},ensure_ascii=False,indent=2),encoding='utf-8')
