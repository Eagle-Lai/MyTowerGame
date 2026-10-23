"""Resolve eight individually selected L10 source literals after actual r3 failures."""
from formal_tools import *
import openpyxl
status=json.loads((ROOT/'Library/BalanceWorkbench/references-r3-q/status.json').read_text(encoding='utf-8'));assert status['phase']=='complete'
reason='r3四种布局的末波实测仍由Tiger、Crawler/Pig、Bull/Bear和精英Rat漏过；逐项修正这些已观察角色。Rat保留高于普通重型的护甲折算耐久，并改为更慢的耐久目标，给予终段持续攻击窗口；其他前24波、空袭、未列角色与经济保持不变。'
decisions={10017490:{'hp':192},10017484:{'hp':300},10017493:{'hp':380},10017498:{'hp':395},10017487:{'hp':520},10017488:{'hp':700},10017499:{'hp':890,'speed':.53}}
records=json.loads((REPORT/'audit/current-source-records.json').read_text(encoding='utf-8'));waves=json.loads((REPORT/'audit/formal-waves-r3.json').read_text(encoding='utf-8'));edits=[];books={}
for id,fields in decisions.items():
    assert [(w['level'],w['wave'])for w in waves if id in w['orderedEnemyIds']]==[(10,25)]
    rec=records['EnemyData'][str(id)];p=rec['path'];assert '/L10/'in p
    if p not in books:books[p]=openpyxl.load_workbook(ROOT/p,read_only=True)
    for field,value in fields.items():
        cell=rec['cells'][field];before=books[p][rec['sheet']][cell].value
        if before!=value:edits.append(dict(path=p,sheet=rec['sheet'],cell=cell,before=before,after=value,reason=reason))
for wb in books.values():wb.close()
spec=REPORT/'design-L10-refinement-r4.json';out=REPORT/'design-L10-refinement-r4.cells.json';assert not spec.exists()and not out.exists()
spec.write_text(json.dumps(dict(status='reviewed_literal_decisions_pending_apply',waves=[dict(level=10,wave=25,reason=reason,variantOverrides=decisions)]),ensure_ascii=False,indent=2),encoding='utf-8')
out.write_text(json.dumps(edits,ensure_ascii=False,indent=2),encoding='utf-8');print(len(edits),'explicit L10 cells, not applied')
