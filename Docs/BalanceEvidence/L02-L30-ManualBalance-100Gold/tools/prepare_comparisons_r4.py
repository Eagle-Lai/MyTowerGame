"""Bounded player comparisons on the current formal data. Never writes game data."""
from formal_tools import *
import copy
tag='comparisons-r4-u';runs=[];bounds=[]
for old in ['alternatives-r2-m','l28-phased-r2-o']:
 request=json.loads((REPORT/f'requests/{old}.json').read_text(encoding='utf-8'))
 for index,run in enumerate(request['runs']):
  q=copy.deepcopy(run);q['strategy']=f'{tag}-{old}-{index}';q['screenshots']=False;q['captureStages']=False;runs.append(q)
 bounds.append(dict(sourceRequest=f'requests/{old}.json',candidateCount=len(request['runs']),purpose='Observed reference budget redirected to a materially different legal layout or investment sequence; unknown outcomes.'))
tc={x['id']:x for x in tables()['tbtowerinfo']}
for entry in json.loads((REPORT/'audit/development-reference-selections.json').read_text(encoding='utf-8'))['levels']:
 r=json.loads((REPORT/entry['source']).read_text(encoding='utf-8'))[entry['sourceIndex']];ops=[]
 for o in r['operations']:
  op={k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}
  if tc[o['towerId']]['type']==3:
   if o['action']=='upgrade':continue
   op['towerId']=1
  ops.append(op)
 directory=REPORT/f'L{entry["level"]:02}/search-{tag}';directory.mkdir(exist_ok=True);f=directory/'no-slow-same-geometry.json';assert not f.exists();f.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
 runs.append(dict(profileId='D04',levelId=entry['level'],strategy=tag+'-no-slow-same-geometry',speed=1,operationsPath=str(f),waitForFunds=True,screenshots=False,captureStages=False))
 bounds.append(dict(level=entry['level'],sourceRunId=r['metrics']['runId'],purpose='Keep original geometry, replace all slow builds with ordinary1, omit slow upgrades, retain saved cash. Real results determine whether no-slow harms or improves defense.'))
out=REPORT/f'requests/{tag}.json';assert not out.exists();out.write_text(json.dumps(dict(output=str(ROOT/'Library/BalanceWorkbench'/tag),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/f'audit/{tag}-bounds.json').write_text(json.dumps(dict(maxRuns=len(runs),declaredCandidates=bounds,termination='Each listed real player plan once. Stop on verifier fault, retain all actual failures. Screenshots disabled for comparisons; final certified reference captures are separate.'),ensure_ascii=False,indent=2),encoding='utf-8');print(len(runs),'comparisons prepared, unexecuted')
