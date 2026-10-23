"""Preserve exact formal runtime inputs and code fingerprints for an isolated batch."""
from formal_tools import *
import sys,shutil,datetime,argparse,subprocess
p=argparse.ArgumentParser();p.add_argument('request',type=pathlib.Path);p.add_argument('--phase',default='before_start');a=p.parse_args()
request=json.loads(a.request.read_text(encoding='utf-8'));h=runtime_hash();tag=pathlib.Path(request['output']).name
assert all(not r.get('candidateDirectory')for r in request['runs'])
assert all(x['runtimeContentHash']==h for x in tables()['tblevelrating']),'Unsealed runtime data'
assert all(x['initialGold']==100 for x in tables()['tbsceneinfo']),'Unexpected initial gold'
snap=REPORT/'audit/runtime-snapshots'/h;snap.mkdir(parents=True,exist_ok=True)
for name in KEYS+['tblevelrating']:
    source=ROOT/f'Assets/ConfigJson/{name}.json';dest=snap/source.name
    if dest.exists():assert dest.read_bytes()==source.read_bytes()
    else:shutil.copy2(source,dest)
out=REPORT/'audit/batch-inputs'/tag;out.mkdir(parents=True,exist_ok=True)
shutil.copy2(a.request,out/'request.json')
operationInputs={}
for i,run in enumerate(request['runs']):
    if not run.get('operationsPath'):continue
    original=pathlib.Path(run['operationsPath']);assert original.is_file(),original
    saved=out/f'operations/run-{i:03}.json';saved.parent.mkdir(exist_ok=True);shutil.copy2(original,saved)
    operationInputs[str(i)]=dict(original=str(original),snapshot=saved.relative_to(out).as_posix(),sha256=hashlib.sha256(original.read_bytes()).hexdigest())
code,assets=frozen_input_paths()
fingerprint={x.relative_to(ROOT).as_posix():hashlib.sha256(x.read_bytes()).hexdigest()for x in code}
for source in code:
    saved=out/'code'/source.relative_to(ROOT);saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,saved)
assetHashes={x.relative_to(ROOT).as_posix():hashlib.sha256(x.read_bytes()).hexdigest()for x in assets if x.is_file()}
audit=next(REPORT/f'audit/formal-integrity-{v}.json'for v in ['final','r4','r3','r2','r1']if(REPORT/f'audit/formal-integrity-{v}.json').exists())
integrity=json.loads(audit.read_text(encoding='utf-8'));assert integrity['runtimeHash']==h and not integrity['differences']and not integrity['unexpectedProtectedChanges']
shutil.copy2(audit,out/'source-protection-audit.json')
manifest=dict(inputFingerprintSchema=2,capturedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),phase=a.phase,request=str(a.request.resolve()),output=request['output'],runtimeContentHash=h,formalSnapshot=str(snap.relative_to(REPORT)),codeSha256=fingerprint,codeSnapshot='code/',combatAssetSha256=assetHashes,operationInputs=operationInputs,sourceProtectionAudit=audit.relative_to(REPORT).as_posix(),sourceProtectionAuditSnapshot='source-protection-audit.json',sourceProtectionAuditSha256=hashlib.sha256(audit.read_bytes()).hexdigest(),candidateCount=len(request['runs']),candidateDirectories=False)
(out/'input-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
diff=subprocess.run(['git','diff','--','Assets/Editor/Balance/BalancePlayModeVerifier.cs'],cwd=ROOT,capture_output=True).stdout
(out/'verifier-current.diff').write_bytes(diff)
print(tag,len(request['runs']),h)
