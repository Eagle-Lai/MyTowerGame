"""Resolve explicitly chosen draft literals to exact existing source cells; no writes."""
from formal_tools import *
import openpyxl,sys,copy
levels=list(map(int,sys.argv[1:]));assert levels and len(levels)==len(set(levels))
status=json.loads((ROOT/'Library/BalanceWorkbench/targeted-r2-n/status.json').read_text(encoding='utf-8'));assert status['phase']=='complete'
draft=json.loads((REPORT/'design-ground-refinement-r3.proposal.json').read_text(encoding='utf-8'))
assert all(l in {w['level']for w in draft['waves']}for l in levels)
spec=dict(status='reviewed_literal_decisions_pending_apply',reviewedAfterBatch='targeted-r2-n',waves=[copy.deepcopy(w)for w in draft['waves']if w['level']in levels])
waves=json.loads((REPORT/'audit/formal-waves-r2.json').read_text(encoding='utf-8'));records=json.loads((REPORT/'audit/current-source-records.json').read_text(encoding='utf-8'));books={};edits=[]
for decision in spec['waves']:
    w=next(w for w in waves if w['level']==decision['level']and w['wave']==decision['wave'])
    desired={}
    for name,fields in decision.get('enemies',{}).items():
        targets=[v['data']['id']for v in w['variants']if v['data']['name']==name];assert len(targets)==1,(decision['level'],name,targets)
        desired[targets[0]]=fields
    for id,fields in decision.get('variantOverrides',{}).items():
        assert int(id)in w['orderedEnemyIds'];desired.setdefault(int(id),{}).update(fields)
    for id,fields in desired.items():
        uses=[(q['level'],q['wave'])for q in waves if id in q['orderedEnemyIds']];assert uses==[(w['level'],w['wave'])],(id,uses)
        record=records['EnemyData'][str(id)];p=record['path']
        if p not in books:books[p]=openpyxl.load_workbook(ROOT/p,read_only=True)
        for field,value in fields.items():
            assert field in['hp','speed'];cell=record['cells'][field];before=books[p][record['sheet']][cell].value
            if before!=value:edits.append(dict(path=p,sheet=record['sheet'],cell=cell,before=before,after=value,reason=decision['reason']))
for wb in books.values():wb.close()
out=REPORT/'design-ground-refinement-r3.json';assert not out.exists()
out.write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
cells=REPORT/'design-ground-refinement-r3.cells.json';assert not cells.exists();cells.write_text(json.dumps(edits,ensure_ascii=False,indent=2),encoding='utf-8')
print('Prepared, not applied:',len(levels),'explicitly chosen levels',len(edits),'literal cells')
