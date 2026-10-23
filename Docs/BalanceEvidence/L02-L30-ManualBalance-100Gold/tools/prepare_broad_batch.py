"""Schedule bounded real trials, controls, and current-version baseline replays."""
from formal_tools import *
tag='campaign-r1-L13-L30-and-refinements';runs=[]
def actual(path,index,label):
    a=json.loads(path.read_text(encoding='utf-8'));r=a[index]if isinstance(a,list)else a
    level=r.get('levelId',1)
    ops=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']]
    out=REPORT/f'L{level:02}/current-version-seed';out.mkdir(parents=True,exist_ok=True)
    opfile=out/f'{label}-operations.json';opfile.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
    return dict(profileId='D04',levelId=level,strategy=label,speed=1,operationsPath=str(opfile),waitForFunds=False,screenshots=True,captureStages=True)
runs.append(actual(REPORT/'L01-reference/best-result.json',0,'historical-L01-current-version'))
runs.append(actual(REPORT/'raw-trials/manual-r6-L02/unity-results.json',1,'zero-L02-current-version'))
runs.append(actual(REPORT/'raw-trials/manual-campaign-r1-L03/unity-results.json',0,'zero-L03-exact-times'))
for name in ['early-ground-r2','early-ground-r2b']:
    runs+=json.loads((REPORT/f'requests/{name}.json').read_text(encoding='utf-8'))['runs']
runs+=json.loads((REPORT/'L04/search-expanded-r1/request.json').read_text(encoding='utf-8'))['runs']
for level in [2,3,4]:
    for strategy in ['normal','power','mistake']:runs.append(dict(profileId='D04',levelId=level,strategy=strategy,speed=1,waitForFunds=False,screenshots=True))
for level in range(13,31):
    runs+=json.loads((REPORT/f'L{level:02}/search-campaign-r1/request.json').read_text(encoding='utf-8'))['runs']
    for strategy in ['normal','power','mistake']:runs.append(dict(profileId='D04',levelId=level,strategy=strategy,speed=1,waitForFunds=False,screenshots=True))
request=dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs)
out=REPORT/f'requests/{tag}.json';out.write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8');print(out,len(runs))
