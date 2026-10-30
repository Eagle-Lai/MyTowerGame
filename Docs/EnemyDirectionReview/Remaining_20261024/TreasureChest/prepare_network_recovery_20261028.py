from session_treasurechest import *
owner();assert inventory()==read(D/'incremental_before_20261028.json')['files']
parent=D/'generation/Up';uncertain=read(parent/'uncertain_result.json')
assert uncertain['message'].startswith('curl transport failed 56 curl: (56) Recv failure: Connection was reset')
console=parent/'console.txt'
if not console.exists():
    console.write_text('Observed terminal output from exec session22645 (excerpt, copied after process exited1):\nError: curl transport failed 56 curl: (56) Recv failure: Connection was reset\nNode.js v24.22.1\nImage request failed for TreasureChest Up\n',encoding='utf-8')
attempts=[parent]+sorted(parent.glob('revision_*'))
assert not any((p/'raw.png').exists() or (p/'result.json').exists() for p in attempts)
sent=[p for p in attempts if (p/'request.json').exists()]
assert all((p/'uncertain_result.json').exists() for p in sent)
used=sum(read(p/'request.json').get('recovery',{}).get('mode')=='standing_user_authorized_network_recovery' for p in sent);assert used<2
if used:
    assert sent[-1].name=='revision_01' and read(sent[-1]/'uncertain_result.json')['message'].startswith('curl transport failed 55 curl: (55) Send failure: Connection was aborted')
    write(D/'recovery_attempt02_assessment_20261028.json',dict(observed_at=now(),owner_thread_id=os.environ['CODEX_THREAD_ID'],dispatch_token=TOKEN,character=NAME,direction='Up',previous='generation/Up/revision_01',prior_outcome='still uncertain; no image/result/HTTP',failure='Curl55 Send failure Connection was aborted',authorization='same verified standing human authorization; second and final additional attempt',no_active_generator=True,production_drift=False,preserved={p.relative_to(D).as_posix():sha(p) for p in sent[-1].iterdir() if p.is_file()}))
authorization=H/'standing_network_recovery_authorization_20261028.json';application=D/'standing_recovery_application_20261028.json'
if not application.exists():
    write(application,dict(recorded_at=now(),character=NAME,direction='Up',owner_thread_id=os.environ['CODEX_THREAD_ID'],dispatch_token=TOKEN,user_statement=read(authorization)['user_statement'],source_thread_id='01a18093-7687-7313-aaba-7419090cc829',source_turn_id='01a180aa-774c-7ee3-8d35-d144e9389b9a',source_user_message_id='01a180aa-7768-7222-bc85-7aa51e801cdd',source_verified='Original human userMessage read with Codex read_thread in this chat2026-10-28; exact statement confirmed. Prior answer described network reset without HTTP/image and bounded retry accepting duplicate charge.',interpretation='Curl56 receive reset with no result/image is the same uncertain transient network situation; conservatively apply the existing two-additional-attempt cap. Original charge and outcome stay unknown.',authorization_sha256=sha(authorization).lower(),accept_possible_duplicate_charge=True,max_additional_network_retries_per_direction=2,preserved_evidence=[dict(path=p.relative_to(D).as_posix(),sha256=sha(p).lower()) for p in parent.iterdir() if p.is_file()],parameters=read(authorization)['parameters'],console_provenance='console.txt is the explicitly marked excerpt from session22645, not a claim of a full saved stream.',no_original_outcome_reclassification=True))
prior=sent[-1];revision=f'revision_{used+1:02d}';out=parent/revision;assert not out.exists();out.mkdir();(out/'prompt.txt').write_bytes((parent/'prompt.txt').read_bytes())
write(out/'recovery_intent.json',dict(created_at=now(),character=NAME,direction='Up',revision=revision,owner_thread_id=os.environ['CODEX_THREAD_ID'],dispatch_token=TOKEN,max_requests=1,authorization_sha256=sha(authorization).lower(),application_sha256=sha(application).lower(),prior_revision='initial' if prior==parent else prior.name,prior_request_sha256=sha(prior/'request.json').lower(),prior_uncertain_sha256=sha(prior/'uncertain_result.json').lower(),prior_console_sha256=sha(prior/'console.txt').lower(),additional_attempt=used+1,reason='Same documented transient connection reset under verified standing human authorization; no original outcome reclassification.'))
c=owner();c.update(current_stage='TreasureChest_Up_bounded_standing_Curl56_recovery',last_stage_evidence=str(application.relative_to(R)).replace('\\','/'),updated_at=now());write(H/'conversation_chain.json',c)
print(json.dumps(dict(revision=revision,additional_attempt=used+1,max_additional=2)))
