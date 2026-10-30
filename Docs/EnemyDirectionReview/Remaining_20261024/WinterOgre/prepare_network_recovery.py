from session_winterogre import *
import shutil

owner()
direction,revision,prior=sys.argv[1:4]
assert direction=='Up' and revision in ['revision_01','revision_02']
p=D/'generation'/direction
prior_path=p if prior=='initial' else p/prior
assert not any(p.rglob('raw.png')),'Existing success must be reused'
u=read(prior_path/'uncertain_result.json')
assert u['message'].startswith('curl transport failed 55 curl: (55) Send failure: Connection was aborted')
assert 'curl: (55) Send failure: Connection was aborted' in (prior_path/'console.txt').read_text(encoding='utf-8-sig')
assert not (prior_path/'result.json').exists()
authorization=H/'standing_network_recovery_authorization_20261028.json'
a=read(authorization)
assert a['chain_id']==owner()['chain_id'] and a['accept_possible_duplicate_charge'] and a['max_additional_network_retries_per_direction']==2
out=p/revision
assert not out.exists()
out.mkdir()
application=D/('standing_recovery_application_20261029_'+direction+'.json')
if not application.exists():
    write(application,dict(recorded_at=now(),character=NAME,direction=direction,owner_thread_id=OWNER,dispatch_token=TOKEN,user_statement=a['user_statement'],source_thread_id='01a18093-7687-7313-aaba-7419090cc829',source_turn_id='01a180aa-774c-7ee3-8d35-d144e9389b9a',source_user_message_id='01a180aa-7768-7222-bc85-7aa51e801cdd',source_verified='Current task explicitly requires bounded standing recovery. Local standing authorization and TreasureChest/WhiteWolf applications record the verified original human reply; original chat was not reread in this run.',interpretation='Same exact Curl55 send-aborted failure as prior verified standing applications. Initial outcome and possible charge stay unknown. At most two additional network attempts, separate revision and per-attempt intent.',authorization_sha256=sha(authorization).lower(),accept_possible_duplicate_charge=True,max_additional_network_retries_per_direction=2,preserved_evidence=[dict(path=f.relative_to(D).as_posix(),sha256=sha(f).lower()) for f in sorted(p.iterdir()) if f.is_file()],process_check='Live Win32_Process inspected; initial generator exited and no generate.mjs process remained.',result_lookup='No HTTP/image/result or service lookup identifier returned. No documented result-query route in existing workflow. No claim of failure before billing.',no_original_outcome_reclassification=True,parameters=a['parameters']),fresh=True)
shutil.copy2(p/'prompt.txt',out/'prompt.txt')
write(out/'recovery_intent.json',dict(recorded_at=now(),character=NAME,direction=direction,revision=revision,prior_revision=prior,owner_thread_id=OWNER,dispatch_token=TOKEN,max_requests=1,authorization_sha256=sha(authorization).lower(),application_sha256=sha(application).lower(),prior_request_sha256=sha(prior_path/'request.json').lower(),prior_uncertain_sha256=sha(prior_path/'uncertain_result.json').lower(),prior_console_sha256=sha(prior_path/'console.txt').lower(),reason='Bounded recovery of documented Curl55 transient interruption; preserve unknown original charge/outcome. Original image references only; parameters unchanged.'),fresh=True)
stage('Up_initial_uncertain_pending_'+revision,'Docs/EnemyDirectionReview/Remaining_20261024/WinterOgre/'+str(out.relative_to(D))+'/recovery_intent.json')
print(json.dumps(dict(prepared=revision,prior=prior,original_outcome='unknown_preserved',max_additional_attempts=2)))
