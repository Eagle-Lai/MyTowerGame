"""Replay four observed L10 player plans against the eight reviewed r4 literals."""
from formal_tools import *
import copy
tag='references-r4-s'
source=json.loads((REPORT/'requests/references-r3-q.json').read_text(encoding='utf-8'))
runs=[]
for index in [10,11,12,13]:
    run=copy.deepcopy(source['runs'][index]);assert run['levelId']==10
    run['strategy']=f'{tag}-q{index}'
    runs.append(run)
request=dict(output=str(ROOT/'Library/BalanceWorkbench'/tag),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs)
out=REPORT/f'requests/{tag}.json';assert not out.exists()
out.write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8')
print(out,len(runs))
