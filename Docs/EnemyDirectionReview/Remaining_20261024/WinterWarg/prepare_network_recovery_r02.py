from session_winterwarg import *
import shutil

owner()
p=D/'generation/Up';prior=p/'revision_01';out=p/'revision_02'
assert not any(p.rglob('raw.png')) and not out.exists()
u=read(prior/'uncertain_result.json')
assert u['message'].startswith('curl transport failed 52 curl: (52) Empty reply from server')
assert 'curl: (52) Empty reply from server' in (prior/'console.txt').read_text(encoding='utf-8-sig')
auth=H/'standing_network_recovery_authorization_20261028.json';a=read(auth)
assert a['chain_id']==owner()['chain_id'] and a['accept_possible_duplicate_charge']
assert sum(read(f).get('recovery',{}).get('mode')=='standing_user_authorized_network_recovery' for f in p.rglob('request.json'))==1
app=D/'standing_recovery_application_20261029_Up_r02.json'
write(app,{'recorded_at':now(),'character':NAME,'direction':'Up','owner_thread_id':OWNER,'dispatch_token':TOKEN,'user_statement':a['user_statement'],'source_thread_id':'01a18093-7687-7313-aaba-7419090cc829','source_user_message_id':'01a180aa-7768-7222-bc85-7aa51e801cdd','source_verified':'Original human reply and preceding possible-duplicate-charge question reread live in this chat; standing_authorization_original_messages_20261029.json',
    'interpretation':'Same uncertain transient image-service transport situation, factual Curl52 empty response rather than Curl55 send abort. This uses the second and last of the pre-existing two agent-bounded network attempts, not a reset or new user monetary budget. No authentication, balance or model-policy failure is being overridden.',
    'authorization_sha256':sha(auth).lower(),'accept_possible_duplicate_charge':True,'max_additional_network_retries_per_direction':2,'additional_attempt':2,'resets_counter':False,'limit_origin':a['limit_origin'],
    'preserved_evidence':[{'path':f.relative_to(D).as_posix(),'sha256':sha(f).lower()} for folder in [p,prior] for f in sorted(folder.iterdir()) if f.is_file()],
    'read_only_service_check':'read_only_service_recheck_20261029T084500Z.json','limits':'models/usage200 and complete unauthenticated401 upload do not establish image availability or assign old charges; no paid diagnostics.',
    'transport':'One direct Curl command using process-only NO_PROXY=*; parent environment restored afterwards; no system proxy changes, redirects or Curl retry. HTTPS host, model, quality, n and references unchanged.'},True)
out.mkdir();shutil.copy2(p/'prompt.txt',out/'prompt.txt')
write(out/'recovery_intent.json',{'recorded_at':now(),'character':NAME,'direction':'Up','revision':'revision_02','prior_revision':'revision_01','owner_thread_id':OWNER,'dispatch_token':TOKEN,'max_requests':1,'authorization_sha256':sha(auth).lower(),'application_sha256':sha(app).lower(),'prior_request_sha256':sha(prior/'request.json').lower(),'prior_uncertain_sha256':sha(prior/'uncertain_result.json').lower(),'prior_console_sha256':sha(prior/'console.txt').lower(),'reason':'Second/last bounded network attempt following two preserved uncertain results. Factual Curl52 classification, direct per-process transport, no new paid diagnostic.'},True)
files=snapshot();before=read(D/'incremental_before_20261029.json')['files'];delta=[{'path':k,'before':before.get(k),'after':files.get(k)} for k in sorted(set(files)|set(before)) if files.get(k)!=before.get(k)]
write(D/'network_checkpoint_before_r02_20261029.json',{'observed_at':now(),'production_file_count':len(files),'full_union_delta':delta,'raw_count':0,'paid_attempts':2,'standing_recovery_used':1,'standing_recovery_limit':2,'all_prior_outcomes':'still_unknown','Down':'not_requested','staged':False,'installed':False,'runtime_rounds':0,'generator_before_sha256':sha(D/'generate_before_current_recovery_20261029.mjs'),'generator_after_sha256':sha(H/'generate.mjs')},True)
stage('Up_two_uncertain_second_network_recovery_prepared',out/'recovery_intent.json')
print(json.dumps({'prepared':'revision_02','production_delta':delta,'remaining_after_this_single_attempt':0}))
