"""Prepare a bounded fresh revision under the standing network recovery authorization."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib,json,os,sys,subprocess
D=Path(__file__).resolve().parent;HERE=D.parent
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
direction,prior_revision,revision=sys.argv[1:4]
assert direction in ['Up','Down']
c=read(HERE/'conversation_chain.json');assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='ScarabMounted' and c['dispatch_token']=='scarab-to-scarabmounted-dd3da45145854f44998a5b6bdc48d12e'
parent=D/'generation'/direction;prior=parent if prior_revision=='initial' else parent/prior_revision;out=parent/revision
assert not out.exists() and not list(parent.rglob('raw.png'))
assert read(prior/'uncertain_result.json')['message']=='fetch failed'
console=(prior/'console.txt').read_text(encoding='utf-8-sig');assert 'ECONNRESET' in console and 'before secure TLS connection was established' in console
used=sum(read(p).get('recovery',{}).get('mode')=='standing_user_authorized_network_recovery' for p in parent.rglob('request.json'))
authorization=HERE/'standing_network_recovery_authorization_20261028.json'
assert used<read(authorization)['max_additional_network_retries_per_direction']
out.mkdir();(out/'prompt.txt').write_bytes((prior/'prompt.txt').read_bytes())
write(out/'recovery_intent.json',dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),character='ScarabMounted',direction=direction,revision=revision,prior_revision=prior_revision,max_requests=1,owner_thread_id=c['owner_thread_id'],dispatch_token=c['dispatch_token'],authorization_sha256=sha(authorization),prior_request_sha256=sha(prior/'request.json'),prior_uncertain_sha256=sha(prior/'uncertain_result.json'),prior_console_sha256=sha(prior/'console.txt'),reason='Standing direct-user authorization for same ECONNRESET before TLS case. Preserve prior uncertain classification and any charge uncertainty; one request only in fresh revision.',additional_network_attempt=used+1))
print(json.dumps(dict(direction=direction,revision=revision,additional_network_attempt=used+1,prior_outcome='uncertain_preserved')))
