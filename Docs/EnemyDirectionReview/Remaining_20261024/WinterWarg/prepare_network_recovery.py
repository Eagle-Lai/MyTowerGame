from session_winterwarg import *
import shutil

owner()
direction,revision,prior=sys.argv[1:4]
assert direction=='Up' and revision in ['revision_01','revision_02']
p=D/'generation'/direction
prior_path=p if prior=='initial' else p/prior
assert not any(p.rglob('raw.png'))
u=read(prior_path/'uncertain_result.json')
assert u['message'].startswith('curl transport failed 55 curl: (55) Send failure: Connection was aborted')
assert 'curl: (55) Send failure: Connection was aborted' in (prior_path/'console.txt').read_text(encoding='utf-8-sig')
assert not (prior_path/'result.json').exists()
auth=H/'standing_network_recovery_authorization_20261028.json';a=read(auth)
original=read(D/'standing_authorization_original_messages_20261029.json')
assert any(i.get('id')=='01a180aa-7768-7222-bc85-7aa51e801cdd' and i['content'][0]['text'].strip()==a['user_statement'] for t in original['turns'] for i in t['items'])
assert a['chain_id']==owner()['chain_id'] and a['accept_possible_duplicate_charge'] and a['max_additional_network_retries_per_direction']==2
assert read(D/'unauthenticated_transport_control_20261029.json')['controls'][1]['exit_code']==0
active=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -match 'generate\\.mjs' }).Count"],stdout=subprocess.PIPE,check=True,encoding='utf-8').stdout.strip()
assert active=='0',active
application=D/'standing_recovery_application_20261029_Up.json'
if not application.exists():
    write(application,dict(recorded_at=now(),character=NAME,direction=direction,owner_thread_id=OWNER,dispatch_token=TOKEN,user_statement=a['user_statement'],source_thread_id=original['thread'],source_turn_id='01a180aa-774c-7ee3-8d35-d144e9389b9a',source_user_message_id='01a180aa-7768-7222-bc85-7aa51e801cdd',source_verified='Original human reply and preceding uncertain-outcome closeout reread live with read_thread in this chat; selected messages saved with SHA.',original_messages_sha256=sha(D/'standing_authorization_original_messages_20261029.json'),interpretation='Same class of transient uncertain network transport interruption, here factual Curl55 send abort. Applying the existing serial-chain human recovery grant, not another character-specific max1 or budget. Original outcome/charge remains unknown.',authorization_sha256=sha(auth).lower(),accept_possible_duplicate_charge=True,max_additional_network_retries_per_direction=2,limit_origin=a['limit_origin'],preserved_evidence=[dict(path=f.relative_to(D).as_posix(),sha256=sha(f).lower()) for f in sorted(p.iterdir()) if f.is_file()],process_check='No active generate.mjs node process after original exit.',result_lookup='No HTTP status/raw/result/query identifier returned; no documented per-request query route available. No assertion of non-billing.',parameters=a['parameters'],transport_control='unauthenticated_transport_control_20261029.json',transport_control_sha256=sha(D/'unauthenticated_transport_control_20261029.json'),transport='Explicit already-existing local proxy 127.0.0.1:7897 for this command only. Same HTTPS host, TLS verification and no redirect/retry; does not change system proxy or establish a different external route.'),True)
out=p/revision;assert not out.exists();out.mkdir()
shutil.copy2(p/'prompt.txt',out/'prompt.txt')
write(out/'recovery_intent.json',dict(recorded_at=now(),character=NAME,direction=direction,revision=revision,prior_revision=prior,owner_thread_id=OWNER,dispatch_token=TOKEN,max_requests=1,authorization_sha256=sha(auth).lower(),application_sha256=sha(application).lower(),prior_request_sha256=sha(prior_path/'request.json').lower(),prior_uncertain_sha256=sha(prior_path/'uncertain_result.json').lower(),prior_console_sha256=sha(prior_path/'console.txt').lower(),reason='Existing user grant for same uncertain transient transport failure; fresh single attempt with factual complete-upload401 control; preserve all unknown results/charges.'),True)
write(D/('docs_generator_recovery_change_'+revision+'.json'),{'observed_at':now(),'before_sha256':sha(D/'generate_before_current_recovery_20261029.mjs'),'after_sha256':sha(H/'generate.mjs'),'scope':'Only current WinterWarg Up Curl55 standing recovery revisions01/02 plus per-command existing proxy. Existing two-attempt counter, owner/token and all prior role protections retained. No Unity CSharp or production resource changed.'},True)
stage('Up_initial_uncertain_recovery_prepared',out/'recovery_intent.json')
print('Prepared '+revision+'; original outcome and possible charge remain unknown.')
