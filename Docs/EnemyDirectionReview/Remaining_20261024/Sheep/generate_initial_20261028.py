from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,subprocess,sys
D=Path(__file__).resolve().parent;H=D.parent;R=H.parents[2]
direction=sys.argv[1];assert direction in ['Up','Down']
c=json.loads((H/'conversation_chain.json').read_text(encoding='utf-8'))
assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='Sheep' and c['dispatch_token']=='scarabmounted-to-sheep-fd7d7a5afb264ca7a1691363ab276f5f'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
base=json.loads((D/'incremental_before_20261028.json').read_text(encoding='utf-8'))
assert all(sha(R/p)==s for p,s in base['protected_six'].items())
folder=D/'generation'/direction
assert not list(folder.rglob('request.json')) and not list(folder.rglob('raw.png')) and not list(folder.rglob('uncertain_result.json'))
if direction=='Down':
    review=json.loads((D/'generation/Up/review_20261028.json').read_text(encoding='utf-8'))
    assert review['accepted_for_staging'] and review['raw_sha256']==sha(D/'generation/Up/raw.png')
prompt=folder/'prompt.txt';text=prompt.read_text(encoding='utf-8')
text=text.replace('front-facing hoof/paw at bottom; show the view-appropriate front/back of foot','view-appropriate hoof at bottom; show the correct front/back of foot').replace('rump and tail are visible','rump are visible').replace('including its original ears/horns/crest/hat','including its original drooping ears and wool crown')
prompt.write_text(text,encoding='utf-8')
intent=dict(created_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),character='Sheep',direction=direction,revision='initial',owner_thread_id=c['owner_thread_id'],dispatch_token=c['dispatch_token'],max_requests=1,transport='curl_https_no_retry',prompt_sha256=sha(prompt),source_fingerprints=base['protected_six'],authorization='User serial enemy task, unchanged images/edits gpt-image-2 medium 1536x1024 n=1. No retry in this invocation.')
with (folder/'generation_intent.json').open('x',encoding='utf-8') as f:json.dump(intent,f,ensure_ascii=False,indent=2)
result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(H/'generate_character.ps1'),'-Character','Sheep','-Direction',direction],cwd=R,capture_output=True,encoding='utf-8',errors='replace')
with (folder/'console.txt').open('x',encoding='utf-8') as f:f.write(result.stdout+'\n'+result.stderr)
print(result.stdout,flush=True)
if result.returncode:print(result.stderr,flush=True)
raise SystemExit(result.returncode)
