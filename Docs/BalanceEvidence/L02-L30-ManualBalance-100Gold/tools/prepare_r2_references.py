"""Schedule bounded real r2 tests; all output is player requests and evidence."""
from formal_tools import *
import collections
tag='references-r2-a';runs=json.loads((REPORT/'requests/last-mile-r5-L13-resume.json').read_text(encoding='utf-8'))['runs'];decisions=[]
for level,name in [(14,'group72'),(14,'dense-group'),(23,'group72'),(29,'group72'),(30,'coverage72'),(30,'group72')]:
    request=json.loads((REPORT/f'L{level:02}/search-refined-r2/request.json').read_text(encoding='utf-8'))
    run=next(x for x in request['runs']if x['strategy']=='refined-r2-'+name);run['captureStages']=True;runs.append(run)
for level,kind in [(8,'early'),(9,'early'),(10,'greedy-mixed'),(14,'folded-maze'),(15,'folded-maze'),(16,'folded-maze'),(18,'folded-maze'),(19,'greedy-mixed'),(20,'folded-maze'),(21,'folded-maze'),(22,'folded-maze'),(23,'folded-maze'),(24,'folded-maze'),(25,'greedy-mixed'),(27,'folded-maze'),(28,'greedy-mixed'),(29,'greedy-mixed'),(30,'folded-maze')]:
    if kind=='early':
        batch='campaign-r1-L13-L30-and-refinements';index={8:15,9:22}[level]
        r=json.loads((REPORT/f'raw-trials/{batch}/unity-results.json').read_text(encoding='utf-8'))[index]
        ops=[{k:o[k]for k in ['waveOrdinal','timeMs','action','row','col','towerId']}for o in r['operations']]
        dest=REPORT/f'L{level:02}/r2-preserved-player-actions';dest.mkdir(exist_ok=True)
        f=dest/'early-ground-operations.json';f.write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
        run=dict(profileId='D04',levelId=level,strategy='r2-preserved-'+r['strategy'],speed=1,operationsPath=str(f),waitForFunds=True,screenshots=True,captureStages=True)
        decisions.append(dict(level=level,sourceBatch=batch,sourceIndex=index,sourceRunId=r['metrics']['runId'],purpose='Same real ordered transactions against current formal data; new evidence required'))
    else:
        request=json.loads((REPORT/f'L{level:02}/search-campaign-r1/request.json').read_text(encoding='utf-8'))
        run=next(x for x in request['runs']if x['strategy']=='campaign-r1-'+kind)
        run.update(strategy='r2-preserved-'+kind,screenshots=True,captureStages=True)
        decisions.append(dict(level=level,sourceOperations=run['operationsPath'],purpose='Hold player plan fixed to isolate the effect of the r2 literal pressure edits'))
    runs.append(run)
(REPORT/f'requests/{tag}.json').write_text(json.dumps(dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs),ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/'audit/references-r2-a-search-bounds.json').write_text(json.dumps(dict(maxRuns=len(runs),completed=0,stopCondition='All listed candidates terminate or a real editor/runtime fault; no changes to data during the batch',sources=decisions,unityRequired=True),ensure_ascii=False,indent=2),encoding='utf-8')
print(len(runs),'prepared, not yet run')
