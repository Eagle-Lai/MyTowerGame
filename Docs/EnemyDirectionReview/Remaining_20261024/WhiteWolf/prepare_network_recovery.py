"""Apply existing human authorization to a fresh bounded WhiteWolf network retry."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys

D=Path(__file__).resolve().parent; H=D.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
direction, revision=sys.argv[1:3]
assert direction in ['Up','Down'] and revision in ['revision_01','revision_02']
chain=read(H/'conversation_chain.json')
assert chain['state']=='active' and chain['current_character']=='WhiteWolf'
assert chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']=='01a183d9-2ad7-73d2-b736-3057ef92f215'
assert chain['dispatch_token']=='watchdog-to-whitewolf-20261029_024758-616f3dd3-f8a9-4ec4-b44b-f70f383f1fbf'
auth_path=H/'standing_network_recovery_authorization_20261028.json'; auth=read(auth_path)
assert auth['user_statement']=='继续任务。后续同样的情况，不再需要我确认，可以继续静默执行'
assert auth['accept_possible_duplicate_charge'] and auth['max_additional_network_retries_per_direction']==2
parent=D/'generation'/direction
assert not any(parent.rglob('raw.png')), 'Reuse successful output'
prior_revision='initial' if revision=='revision_01' else 'revision_01'
prior=parent if prior_revision=='initial' else parent/prior_revision
uncertain=read(prior/'uncertain_result.json'); console=(prior/'console.txt').read_text(encoding='utf-8-sig')
assert any(uncertain['message'].startswith(prefix) and text in console for prefix,text in [
 ('curl transport failed 55 curl: (55) Send failure: Connection was aborted','curl: (55) Send failure: Connection was aborted'),
 ('curl transport failed 56 curl: (56) Recv failure: Connection was reset','curl: (56) Recv failure: Connection was reset')])
assert not (prior/'result.json').exists()
out=parent/revision; assert not out.exists(); out.mkdir()
application_path=D/('standing_recovery_application_20261029_'+direction+'.json')
if not application_path.exists():
    evidence=[p for p in parent.iterdir() if p.is_file()]
    application=dict(recorded_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),character='WhiteWolf',direction=direction,
        owner_thread_id=chain['owner_thread_id'],dispatch_token=chain['dispatch_token'],user_statement=auth['user_statement'],
        source_thread_id='01a18093-7687-7313-aaba-7419090cc829',source_turn_id='01a180aa-774c-7ee3-8d35-d144e9389b9a',
        source_user_message_id='01a180aa-7768-7222-bc85-7aa51e801cdd',source_verified='Original human reply read with Codex read_thread during WhiteWolf continuation; exact statement matched.',
        interpretation='Curl send aborted or receive reset with no HTTP result/image is the same uncertain transient network situation. Preserve unknown original charge and outcome; at most two additional attempts.',
        authorization_sha256=sha(auth_path),accept_possible_duplicate_charge=True,max_additional_network_retries_per_direction=2,
        preserved_evidence=[dict(path=p.relative_to(D).as_posix(),sha256=sha(p)) for p in evidence],
        process_check='No generate.mjs or AIHub curl process remained in live Win32_Process inspection before recovery.',
        result_lookup='No raw, result or request identifier returned; existing endpoint provides no documented lookup used by this workflow. Unknown outcome is retained.',
        no_original_outcome_reclassification=True,parameters=auth['parameters'])
    application_path.write_text(json.dumps(application,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
application=read(application_path)
assert all(sha(D/e['path'])==e['sha256'] for e in application['preserved_evidence'])
(out/'prompt.txt').write_bytes((parent/'prompt.txt').read_bytes())
intent=dict(recorded_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),character='WhiteWolf',direction=direction,revision=revision,
    owner_thread_id=chain['owner_thread_id'],dispatch_token=chain['dispatch_token'],max_requests=1,
    authorization_sha256=sha(auth_path),application_sha256=sha(application_path),prior_revision=prior_revision,
    prior_request_sha256=sha(prior/'request.json'),prior_uncertain_sha256=sha(prior/'uncertain_result.json'),prior_console_sha256=sha(prior/'console.txt'),
    reason='One bounded retry under verified standing authorization, preserving the original unknown outcome.')
(out/'recovery_intent.json').write_text(json.dumps(intent,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(character='WhiteWolf',direction=direction,revision=revision,request_sent=False)))
