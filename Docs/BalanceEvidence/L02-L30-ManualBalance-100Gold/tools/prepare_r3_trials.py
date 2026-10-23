"""Replay previously measured player plans after six explicit source refinements."""
from formal_tools import *
import sys,math
tag=sys.argv[1];runs=[];notes=[];t=tables();tc={x['id']:x for x in t['tbtowerinfo']}
sources={name:json.loads((REPORT/f'raw-trials/{name}/unity-results.json').read_text(encoding='utf-8'))for name in['targeted-r2-n','followups-r2-h']}
cases=[('targeted-r2-n',i)for i in[0,1,6,35,12,36,37,13,14,47,43,45]]+[('followups-r2-h',i)for i in[107,109]]
for source,index in cases:
    r=sources[source][index];level=r['levelId'];assert level in[9,10,19,24,25,27]
    ops=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']]
    out=REPORT/f'L{level:02}/search-{tag}';out.mkdir(parents=True,exist_ok=True);name=f'{source}-{index}';f=out/f'{name}.json';assert not f.exists()
    f.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
    runs.append(dict(profileId='D04',levelId=level,strategy=tag+'-'+name,speed=1,operationsPath=str(f),waitForFunds=True,screenshots=True,captureStages=True))
    notes.append(dict(level=level,sourceBatch=source,sourceIndex=index,sourceRunId=r['metrics']['runId'],scope='Same observed transaction sequence against newly exported/sealed formal r3 data. This is a new actual run, not relabelled evidence.'))
r=sources['targeted-r2-n'][46];assert r['levelId']==27
ops=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']]
at=max(o['timeMs']for o in ops if o['waveOrdinal']==25)+1000;path=r['finalPathCells']
choices=sorted([x for x in r['towerContributions']if x['towerId']==5],key=lambda x:sum(.3+j/max(1,len(path)-1)for j,(col,row)in enumerate(path)if(col-x['col'])**2+(row-x['row'])**2<=tc[6]['radius']**2),reverse=True)
for count in[3,4]:
    assert len(choices)>=count
    extra=[dict(waveOrdinal=25,timeMs=at,action='upgrade',row=x['row'],col=x['col'],towerId=6)for x in choices[:count]]
    out=REPORT/f'L27/search-{tag}';f=out/f'six-conversions-plus-{count}-group3.json';assert not f.exists()
    f.write_text(json.dumps(ops+extra,ensure_ascii=False,indent=2),encoding='utf-8')
    runs.append(dict(profileId='D04',levelId=27,strategy=f'{tag}-six-conversions-plus-{count}-group3',speed=1,operationsPath=str(f),waitForFunds=True,screenshots=True,captureStages=True))
    notes.append(dict(level=27,sourceBatch='targeted-r2-n',sourceIndex=46,sourceRunId=r['metrics']['runId'],additionalInvestments=extra,additionalCost=210*count,earliestTimeMs=at,scope='Alternative retains three more ordinary towers than the nine-conversion plan and instead invests actual available income/refunds in higher group tiers. Wait for real funds during development; actual result pending.'))
assert len(runs)==16
(REPORT/f'requests/{tag}.json').write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/f'audit/{tag}-bounds.json').write_text(json.dumps(dict(maxRuns=16,formalHash=runtime_hash(),decisions=notes,termination='One actual replay for each listed player plan; keep every failure and incomplete run'),ensure_ascii=False,indent=2),encoding='utf-8')
print('16 unexecuted r3 reference/alternative trials')
