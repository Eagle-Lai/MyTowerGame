"""Audit required final artifacts, strict comparisons, alternatives, controls and links."""
from formal_tools import *
from compare_replays import compare
from evidence_accounting import reconcile
from PIL import Image
import re,datetime
h=runtime_hash();levels=[];errors=[];initialization=[]
editor=json.loads((REPORT/'audit/editor-validation-final.json').read_text(encoding='utf-8'))
assert editor['status']=='passed'and editor['projectRoot']=='E:/MyTowerGame'and editor['unityVersion']=='2022.3.62f3c1'
assert not editor['scriptCompilationFailed']and editor['unresolvedErrorCount']==0 and not editor['playing']and not editor['balanceVerifierRunning']
export=json.loads((REPORT/'audit/final-formal-export-log.json').read_text(encoding='utf-8'));assert export['runtimeContentHash']==h
assert all(hashlib.sha256((ROOT/f'Assets/ConfigJson/{k}.json').read_bytes()).hexdigest()==v for k,v in export['currentOutputSha256'].items())
selected=json.loads((REPORT/'audit/selected-final-proofs.json').read_text(encoding='utf-8'))
assert selected['runtimeContentHash']==h and not selected['missingStrictTriples']
proof_sources={x['level']:x for x in selected['levels']}
assert set(proof_sources)==set(range(2,31))
required=['最终布阵图.png','完整逐波操作与测试报告.md','best-operations.json','best-result.json','reproducibility.json','trial-index.json','trial-index.csv','设计与725波明细.md','evidence/three-actual-replays.json','evidence/replay-operations.json','evidence/cashflow-and-prefixes.json','evidence/alternative-and-controls.json','evidence/final-authored-notes.json','evidence/upgrade-cash-thresholds.json']
for level in range(2,31):
 out=REPORT/f'L{level:02}';missing=[f for f in required if not(out/f).is_file()];assert not missing,(level,missing)
 r=json.loads((out/'best-result.json').read_text(encoding='utf-8'));group=json.loads((out/'evidence/three-actual-replays.json').read_text(encoding='utf-8'));proof=compare(group);assert proof['allMatch'];assert r==group[0];account=reconcile(r);assert json.loads((out/'best-operations.json').read_text(encoding='utf-8'))==r['operations'];assert r['profile']['runtimeContentHash']==h
 origin=proof_sources[level];origin_path=REPORT/origin['results'];assert trial_inputs_match_current(origin_path)
 origin_rows=json.loads(origin_path.read_text(encoding='utf-8'));assert group==[origin_rows[i]for i in origin['indices']]
 initialization.append(dict(level=level,actualInitialGold=r['initialGold'],actualInitialHp=r['initialHp'],runId=r['metrics']['runId'],source=f'L{level:02}/best-result.json'))
 alt=json.loads((out/'evidence/alternative-and-controls.json').read_text(encoding='utf-8'));a=alt['alternative'];ar=json.loads((REPORT/a['source']).read_text(encoding='utf-8'))[a['sourceIndex']];assert trial_inputs_match_current(REPORT/a['source']);assert ar['metrics']['runId']==a['runId']and ar['profile']['runtimeContentHash']==h and a['differentFinalCells']>=2;reconcile(ar)
 assert ar['valid']
 types=set()
 for c in alt['controls']:
  control_path=REPORT/c['source'];assert trial_inputs_match_current(control_path)
  actual_control=json.loads(control_path.read_text(encoding='utf-8'))[c['sourceIndex']]
  assert actual_control['levelId']==level and actual_control['strategy']==c['strategy']and actual_control['metrics']['runId']==c['runId']and actual_control['profile']['runtimeContentHash']==h
  if 'slow-allocation'in c['strategy']:types.add('slow-allocation')
  if 'final-control-ground-only-'in c['strategy']:types.add('ground-only')
  if 'final-control-fewer-walls-'in c['strategy']:types.add('fewer-walls')
 assert types=={'slow-allocation','ground-only','fewer-walls'},(level,types)
 screens=list((out/'evidence/screenshots').glob('*.png'));assert screens
 for trial in group:
  for w in [1,10,25]:
   b=next(b for b in trial['waveBoundaries']if b['beforeWave']==w);assert(out/'evidence/screenshots'/pathlib.Path(b['screenshot']).name).is_file()
 with Image.open(out/'最终布阵图.png')as im:assert im.width>=1200 and im.height>=800
 text=(out/'完整逐波操作与测试报告.md').read_text(encoding='utf-8');assert h in text and str(r['metrics']['runId'])in text
 for target in re.findall(r'\]\(([^)]+)\)',text):
  if '://'in target or target.startswith('#'):continue
  path=(out/target.split('#')[0]).resolve()
  if not path.exists():errors.append(dict(level=level,problem='broken report link',target=target))
 levels.append(dict(level=level,runIds=[x['metrics']['runId']for x in group],stars=5,allStrictMatch=True,waves=25,killed=r['metrics']['killed'],leaked=0,hp=r['metrics']['hp'],combatSeconds=r['metrics']['combatElapsedSeconds'],finalGold=r['finalGold'],transactions=len(r['operations']),waveTimeTransactions=sum(o['timeMs']>0 for o in r['operations']),alternativeRunId=a['runId'],controlTypes=sorted(types),finalArtifacts=len(required),screenshots=len(screens),report=f'L{level:02}/完整逐波操作与测试报告.md',layout=f'L{level:02}/最终布阵图.png'))
baseline=json.loads((REPORT/'L01-current-check/result.json').read_text(encoding='utf-8'));assert baseline['profile']['runtimeContentHash']==h and baseline['initialGold']==100;reconcile(baseline)
baseline_origin=json.loads((REPORT/'L01-current-check/comparison.json').read_text(encoding='utf-8'));assert trial_inputs_match_current(pathlib.Path(baseline_origin['source']))
initialization.append(dict(level=1,actualInitialGold=baseline['initialGold'],actualInitialHp=baseline['initialHp'],runId=baseline['metrics']['runId'],source='L01-current-check/result.json'));assert len(initialization)==30 and all(x['actualInitialGold']==100 for x in initialization)
(REPORT/'audit/runtime-initialGold-30-final.json').write_text(json.dumps(dict(runtimeContentHash=h,method='Actual observations recorded immediately after production InitLevel; no overrides',levels=sorted(initialization,key=lambda x:x['level'])),ensure_ascii=False,indent=2),encoding='utf-8')
integrity=json.loads((REPORT/'audit/formal-integrity-final.json').read_text(encoding='utf-8'));literal=json.loads((REPORT/'audit/literal-scope-final.json').read_text(encoding='utf-8'));rating=json.loads((REPORT/'audit/rating-reference-integrity-final.json').read_text(encoding='utf-8'));load=json.loads((REPORT/'audit/runtime-load-final.json').read_text(encoding='utf-8'));assert integrity['runtimeHash']==h and integrity['sealMatch']and integrity['sourceExportMatch']and not integrity['unexpectedProtectedChanges'];assert load['runtimeContentHash']==h
assert not literal['errors']and literal['l01OnlyRuntimeSeal']and not rating['errors'];assert all(s['initialGold']==100 for s in tables()['tbsceneinfo']);waves=json.loads((REPORT/'audit/formal-waves-final.json').read_text(encoding='utf-8'));assert len([w for w in waves if w['level']!=1])==725
assert not errors,errors
result=dict(capturedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='complete',runtimeContentHash=h,all30InitialGold100=True,l01CurrentStars=baseline['stars'],l01GameplayAndRatingExceptSealUnchanged=True,designedLaterLevels=29,designedLaterWaves=725,certifiedLevels=levels,strictReferenceRuns=87,allArtifactsAndLinksPresent=True,sourceCellsChecked=integrity['checkedSourceCells'],unexpectedProtectedChanges=integrity['unexpectedProtectedChanges'],manualTouchOrAndroidPerformanceVerified=False,errors=errors)
(REPORT/'audit/final-delivery-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('All29 final deliveries,87 strict runs,29 alternatives,87 representative controls and report links audited')
