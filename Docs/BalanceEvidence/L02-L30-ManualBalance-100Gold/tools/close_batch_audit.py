"""Validate complete real batches and compare frozen inputs before releasing the editor."""
from formal_tools import *
import sys,datetime,shutil
tag=sys.argv[1];root=ROOT/f'Library/BalanceWorkbench/{tag}';status=json.loads((root/'status.json').read_text(encoding='utf-8'));assert status['phase']=='complete',status
inputs=REPORT/f'audit/batch-inputs/{tag}';manifest=json.loads((inputs/'input-manifest.json').read_text(encoding='utf-8'));rows=json.loads((root/'unity-results.json').read_text(encoding='utf-8'));assert len(rows)==status['total']==manifest['candidateCount']
changed=[]
if manifest.get('inputFingerprintSchema')==2:
    observed=frozen_input_fingerprints()
    for kind in ['codeSha256','combatAssetSha256']:
        for path in set(observed[kind])^set(manifest[kind]):
            changed.append('File set changed: '+path)
for kind in ['codeSha256','combatAssetSha256']:
    for p,h in manifest.get(kind,{}).items():
        if not(ROOT/p).is_file()or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:changed.append(p)
h=runtime_hash();assert h==manifest['runtimeContentHash'];assert all(r['profile']['runtimeContentHash']==h and r['initialGold']==100 and not r['metrics']['debugOverride']for r in rows)
errors=[]
for i,r in enumerate(rows):
    m=r['metrics'];events=r['enemyOutcomes']
    if len(events)!=m['killed']+m['leaked']or m['successfulSpawned']<len(events):errors.append(dict(index=i,problem='enemy events'))
    if any(o['balanceAfter']<0 for o in r['operations']):errors.append(dict(index=i,problem='negative balance'))
    assert r['levelId']==json.loads((inputs/'request.json').read_text(encoding='utf-8'))['runs'][i]['levelId']
ops=manifest.get('operationInputs');timing='before_start'
if ops is None:
    timing='after_batch; original before-start manifest retained; development evidence only'
    ops={};req=json.loads((inputs/'request.json').read_text(encoding='utf-8'))
    for i,r in enumerate(req['runs']):
        if not r.get('operationsPath'):continue
        p=pathlib.Path(r['operationsPath']);dest=inputs/f'operations-observed-after/run-{i:03}.json';dest.parent.mkdir(exist_ok=True);shutil.copy2(p,dest)
        ops[str(i)]=dict(original=str(p),snapshot=dest.relative_to(inputs).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
else:
    for i,e in ops.items():
        if hashlib.sha256(pathlib.Path(e['original']).read_bytes()).hexdigest()!=e['sha256']:changed.append(e['original'])
report=dict(capturedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),batch=tag,phase=status['phase'],requested=status['total'],completed=len(rows),runtimeContentHash=h,inputsUnchanged=not changed,changedInputs=changed,errors=errors,allInitialGold100=True,allDebugOverrideFalse=True,actualZeroLeakLevels=sorted({r['levelId']for r in rows if r['victory']and r['state']=='finished'and not r['metrics']['leaked']}),maxObservedAlive=max(w['peakAlive']for r in rows for w in r['metrics']['waves']),spawnDeferredCount=sum(w['spawnDeferredCount']for r in rows for w in r['metrics']['waves']),operationSnapshotTiming=timing,operationInputs=ops)
(REPORT/f'audit/{tag}-completion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print({k:v for k,v in report.items()if k!='operationInputs'});assert not changed and not errors
