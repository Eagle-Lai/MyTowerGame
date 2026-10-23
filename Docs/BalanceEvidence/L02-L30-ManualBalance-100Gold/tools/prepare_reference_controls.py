"""Reference-derived controls preserve geometry and remove slow investment."""
from formal_tools import *
import sys
tag=sys.argv[1];entries=json.loads((REPORT/'audit/development-reference-selections.json').read_text(encoding='utf-8'))['levels']
t=tables();tc={x['id']:x for x in t['tbtowerinfo']};runs=[];notes=[]
for entry in entries:
    r=json.loads((REPORT/entry['source']).read_text(encoding='utf-8'))[entry['sourceIndex']]
    ops=[];changed=[]
    for o in r['operations']:
        op={k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}
        if tc[o['towerId']]['type']==3:
            if o['action']=='upgrade':changed.append(dict(original=o,replacement=None));continue
            op['towerId']=1;changed.append(dict(original=o,replacement=op))
        ops.append(op)
    out=REPORT/f'L{entry["level"]:02}/search-{tag}';out.mkdir(parents=True,exist_ok=True)
    f=out/'no-slow-same-geometry.json';assert not f.exists();f.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
    runs.append(dict(profileId='D04',levelId=entry['level'],strategy=tag+'-no-slow-same-geometry',speed=1,operationsPath=str(f),waitForFunds=True,screenshots=True,captureStages=True))
    notes.append(dict(level=entry['level'],sourceRunId=r['metrics']['runId'],changes=changed,predictionOnly=True,scope='Keep reference build coordinates and ground-wall geometry, replace slow builds by ordinary level1, omit slow upgrades, retain saved money. Real costs and order still apply; results may improve or worsen and must be observed.'))
(REPORT/f'requests/{tag}.json').write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/f'audit/{tag}-bounds.json').write_text(json.dumps(dict(maxRuns=len(runs),decisions=notes,termination='One real replay per current selected reference; unknown outcomes'),ensure_ascii=False,indent=2),encoding='utf-8')
print(len(runs),'unexecuted reference-derived controls')
