from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,os,sys,hashlib,subprocess,shutil
HERE=Path(__file__).resolve().parent;RUN=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
now=lambda:datetime.now(timezone(timedelta(hours=8))).isoformat()
def write(p,v):
    assert not p.exists(),p
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
c=read(RUN/'conversation_chain.json')
assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='WinterWolfTypeA'
p=HERE/'generation/Down';rev=sys.argv[1];prior=sys.argv[2]
assert rev in ['revision_01','revision_02']
before=p if prior=='initial' else p/prior
assert not list(p.rglob('raw.png'))
u=read(before/'uncertain_result.json')
assert u['message'].startswith('curl transport failed 55 curl: (55) Send failure: Connection was aborted')
assert 'curl: (55) Send failure: Connection was aborted' in (before/'console.txt').read_text(encoding='utf-8-sig')
assert not (before/'result.json').exists()
active=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -match 'generate\\.mjs' }).Count"],capture_output=True,text=True,check=True).stdout.strip()
assert active=='0',active
authfile=RUN/'standing_network_recovery_authorization_20261028.json';a=read(authfile)
original=read(HERE/'standing_authorization_original_messages_20261029.json')
assert any(i.get('id')=='01a180aa-7768-7222-bc85-7aa51e801cdd' and i['content'][0]['text'].strip()==a['user_statement'] for t in original['turns'] for i in t['items'])
assert a['accept_possible_duplicate_charge'] and a['chain_id']==c['chain_id']
application=HERE/'standing_recovery_application_20261029_Down.json'
if not application.exists():
    write(application,dict(recorded_at=now(),character='WinterWolfTypeA',direction='Down',owner_thread_id=c['owner_thread_id'],dispatch_token=c['dispatch_token'],user_statement=a['user_statement'],source_thread_id=original['thread'],source_turn_id='01a180aa-774c-7ee3-8d35-d144e9389b9a',source_user_message_id='01a180aa-7768-7222-bc85-7aa51e801cdd',source_verified='Original user reply and preceding unknown-outcome closeout reread live using read_thread in this chat; selected original messages saved.',original_messages_sha256=sha(HERE/'standing_authorization_original_messages_20261029.json'),authorization_sha256=sha(authfile),accept_possible_duplicate_charge=True,max_additional_network_retries_per_direction=2,limit_origin=a['limit_origin'],interpretation='Same transient uncertain transport interruption: Curl55 send abort. Fresh bounded revision; previous result and charge stay unknown. Not a prior-character one-off authorization.',preserved_evidence=[{'path':f.relative_to(HERE).as_posix(),'sha256':sha(f)} for f in sorted(before.iterdir()) if f.is_file()],parameters=a['parameters'],process_check='No active image generator after original exit.',result_lookup='No HTTP status, raw, result or request/job ID; no documented lookup route. Aggregate usage cannot assign the old individual outcome.'))
out=p/rev;assert not out.exists();out.mkdir()
shutil.copy2(p/'prompt.txt',out/'prompt.txt')
write(out/'recovery_intent.json',dict(recorded_at=now(),character='WinterWolfTypeA',direction='Down',revision=rev,prior_revision=prior,owner_thread_id=c['owner_thread_id'],dispatch_token=c['dispatch_token'],max_requests=1,authorization_sha256=sha(authfile),application_sha256=sha(application),prior_request_sha256=sha(before/'request.json'),prior_uncertain_sha256=sha(before/'uncertain_result.json'),prior_console_sha256=sha(before/'console.txt'),reason='Verified standing human recovery grant; matching Curl55 uncertain transport; fresh single request and all evidence preserved. Authenticated read-only models/usage200 supports account validity, not old result or image POST availability.'))
write(HERE/('docs_generator_recovery_'+rev+'.json'),{'before_sha256':sha(HERE/'generate_before_current_recovery_20261029.mjs'),'after_sha256':sha(RUN/'generate.mjs'),'scope':'Only WinterWolfTypeA Down Curl55 is added to existing standing recovery guard. Active owner/token, original user evidence, preserved SHA, no-success rule and two-attempt conservative counter are retained. No production/CSharp change.'})
print(json.dumps({'prepared':rev,'additional_attempt':len(list(p.glob('revision_*/request.json')))+1,'old_outcome_and_charge':'unknown'}))
