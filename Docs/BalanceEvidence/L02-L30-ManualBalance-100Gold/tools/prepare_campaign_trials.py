"""Assemble real Unity experiments from bounded action searches and controls."""
from formal_tools import *
import sys
tag=sys.argv[1];lo=int(sys.argv[2]);hi=int(sys.argv[3]);runs=[]
for level in range(lo,hi+1):
    request=REPORT/f'L{level:02}/search-campaign-r1/request.json'
    if request.exists():
        rows=json.loads(request.read_text(encoding='utf-8'))['runs']
        for r in rows:
            r['screenshots']=True;runs.append(r)
    for strategy in ['normal','power','mistake']:
        runs.append(dict(profileId='D04',levelId=level,strategy=strategy,speed=1,waitForFunds=False,screenshots=True))
out=REPORT/'requests';out.mkdir(exist_ok=True)
path=out/f'{tag}.json';path.write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=1200,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8');print(path,len(runs))
