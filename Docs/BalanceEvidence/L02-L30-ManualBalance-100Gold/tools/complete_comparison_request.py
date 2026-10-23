"""Add the newly solved L10 control and the frozen L01 baseline before snapshot."""
from formal_tools import *
tag='comparisons-r4-u';f=REPORT/f'requests/{tag}.json';request=json.loads(f.read_text(encoding='utf-8'));assert len(request['runs'])==75
selected=json.loads((REPORT/'audit/development-reference-selections.json').read_text(encoding='utf-8'))['levels'];x=next(x for x in selected if x['level']==10);r=json.loads((REPORT/x['source']).read_text(encoding='utf-8'))[x['sourceIndex']];tc={x['id']:x for x in tables()['tbtowerinfo']};ops=[]
for o in r['operations']:
 op={k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}
 if tc[o['towerId']]['type']==3:
  if o['action']=='upgrade':continue
  op['towerId']=1
 ops.append(op)
directory=REPORT/f'L10/search-{tag}';directory.mkdir(exist_ok=True);out=directory/'no-slow-same-geometry.json';assert not out.exists();out.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
request['runs'].append(dict(profileId='D04',levelId=10,strategy=tag+'-no-slow-same-geometry',speed=1,operationsPath=str(out),waitForFunds=True,screenshots=False,captureStages=False))
original=json.loads((REPORT/'L01-current-check/result.json').read_text(encoding='utf-8'));ops=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in original['operations']];out=REPORT/f'requests/{tag}-L01-exact-operations.json';assert not out.exists();out.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
request['runs'].append(dict(profileId='D04',levelId=1,strategy=tag+'-L01-frozen-baseline',speed=1,operationsPath=str(out),waitForFunds=False,screenshots=True,captureStages=True))
f.write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8');bounds=REPORT/f'audit/{tag}-bounds.json';b=json.loads(bounds.read_text(encoding='utf-8'));b['maxRuns']=77;b['newL10Source']=x['runId'];b['baseline']=dict(level=1,source='L01-current-check/result.json',originalRunId=original['metrics']['runId'],waitForFunds=False,parUnchanged=True);bounds.write_text(json.dumps(b,ensure_ascii=False,indent=2),encoding='utf-8');print('77 bounded actual comparisons and baseline prepared')
