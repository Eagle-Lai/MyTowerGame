"""Select declared route and layout experiments and repeat the three baselines."""
from formal_tools import *
import copy
tag='followups-r2-h';runs=json.loads((REPORT/'requests/controls-r2-current.json').read_text(encoding='utf-8'))['runs'];decisions=[]
route=json.loads((REPORT/'requests/route-r2-g.json').read_text(encoding='utf-8'))
for level in [8,9,15,16,18,19,22,24,25,28]:
    variants=['ordinary-route-retain-air','mixed-route-retain-air']if level==9 else ['mixed-route-retain-air','ordinary-route-late6']
    for variant in variants:
        run=next(x for x in route['runs']if x['levelId']==level and x['strategy'].endswith(variant));runs.append(copy.deepcopy(run));decisions.append(dict(level=level,strategy=run['strategy'],reason='Selected bounded route extension; all numerical configuration unchanged'))
run=next(x for x in route['runs']if x['levelId']==10 and x['strategy'].endswith('mixed-route-retain-air'));runs.append(copy.deepcopy(run))
for level,names in [(10,['group72','balanced-core']),(27,['balanced-core','coverage72'])]:
    request=json.loads((REPORT/f'L{level:02}/search-refined-r2/request.json').read_text(encoding='utf-8'))
    for name in names:
        run=copy.deepcopy(next(x for x in request['runs']if x['strategy']=='refined-r2-'+name));run['captureStages']=True;runs.append(run);decisions.append(dict(level=level,strategy=run['strategy'],reason='Previously unexecuted complete player plan from read-only prediction; prediction failure does not decide Unity outcome'))
for level in [8,19,28]:
    request=json.loads((REPORT/f'L{level:02}/search-campaign-r1/request.json').read_text(encoding='utf-8'))
    run=copy.deepcopy(next(x for x in request['runs']if x['strategy']=='campaign-r1-folded-maze'));run.update(strategy='r2-new-preserved-folded-maze',screenshots=True,captureStages=True);runs.append(run)
    planned=json.loads(pathlib.Path(run['operationsPath']).read_text(encoding='utf-8'))
    decisions.append(dict(level=level,strategy=run['strategy'],lastPlannedInvestmentWave=max(o['waveOrdinal']for o in planned),reason='Old actual long-route candidate failed to air on waves changed in r2; test the preserved full request against current formal data'))
assert len(runs)==115,len(runs)
assert all(not x.get('candidateDirectory')for x in runs)
request=dict(output=str(ROOT/f'Library/BalanceWorkbench/{tag}'),stepSeconds=.02,stepsPerUpdate=4000,captureOutcomes=True,runs=runs)
(REPORT/f'requests/{tag}.json').write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8')
(REPORT/f'audit/{tag}-bounds.json').write_text(json.dumps(dict(maxRuns=115,controls=87,targetedPlayerCandidates=28,decisions=decisions,formalHashAtPreparation=runtime_hash(),termination='One real run per listed plan; keep failures, illegal and unfinished runs distinct; no source data edits during batch'),ensure_ascii=False,indent=2),encoding='utf-8')
print('115 unexecuted:87 declared controls and28 targeted player candidates')
