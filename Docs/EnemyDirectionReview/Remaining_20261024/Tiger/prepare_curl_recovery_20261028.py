"""Apply the verified human standing decision, keeping every uncertain original intact."""
from session_tiger import *

owner()
assert inventory() == read(D/'incremental_before_20261028.json')['files']
check = subprocess.run(['powershell','-NoProfile','-Command',
    "@(Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'node.exe' -and $_.CommandLine -match 'generate\\.mjs') -or ($_.Name -eq 'curl.exe' -and $_.CommandLine -match 'aihub.dog') } | Select-Object Name,ProcessId) | ConvertTo-Json -Compress"],capture_output=True,encoding='utf-8',check=True)
assert not check.stdout.strip(), check.stdout
parent=D/'generation/Up'
attempts=[parent]+sorted(p for p in parent.glob('revision_*') if p.is_dir())
assert not any((p/'raw.png').exists() or (p/'result.json').exists() for p in attempts)
sent=[p for p in attempts if (p/'request.json').exists()]
assert sent and all((p/'uncertain_result.json').exists() for p in sent)
used=sum(read(p/'request.json').get('recovery',{}).get('mode')=='standing_user_authorized_network_recovery' for p in sent)
assert used<2
prior=sent[-1]
assert read(prior/'uncertain_result.json')['message'].startswith('curl transport failed 55 curl: (55) Send failure: Connection was aborted')
authorization=H/'standing_network_recovery_authorization_20261028.json'
application=D/'standing_recovery_application_20261028.json'
if not application.exists():
    write(application,dict(recorded_at=now(),character=NAME,direction='Up',owner_thread_id=os.environ['CODEX_THREAD_ID'],dispatch_token=TOKEN,
        user_statement='继续任务。后续同样的情况，不再需要我确认，可以继续静默执行',
        source_thread_id='01a18093-7687-7313-aaba-7419090cc829',source_turn_id='01a180aa-774c-7ee3-8d35-d144e9389b9a',source_user_message_id='01a180aa-7768-7222-bc85-7aa51e801cdd',
        source_verified='Read original chat with Codex read_thread on 2026-10-28. Human reply followed a closeout describing a network disconnect, no HTTP/image, uncertain delivery, and a bounded retry accepting possible duplicate charge. The closeout did not limit the decision to a literal TLS error string.',
        preceding_closeout='Down 遇到真实阻断：单次请求发生 ECONNRESET，无 HTTP 响应或图片，结果不明；已停止后续付费请求，没有重发。继续前需确认 Down 原请求结果，或由你明确授权接受可能重复计费的一次有界补发。',
        interpretation='Curl55 send-aborted is the same uncertain network-failure situation. The exact TLS-before-send check was an agent implementation restriction, not the wording of the human decision. Apply the existing standing decision within the same conservative two-additional-attempt cap; this is not a new user approval or a claim that the original was unbilled.',
        authorization_sha256=sha(authorization).lower(),accept_possible_duplicate_charge=True,max_additional_network_retries_per_direction=2,
        parameters=dict(endpoint='https://aihub.dog/v1/images/edits',model='gpt-image-2',quality='medium',size='1536x1024',n=1),
        preserved_evidence=[dict(path=p.relative_to(D).as_posix(),sha256=sha(p).lower()) for p in parent.iterdir() if p.is_file()],
        no_new_human_approval_requested=True,no_original_outcome_reclassification=True))
revision=f'revision_{used+1:02d}'
out=parent/revision
assert not out.exists()
out.mkdir()
(out/'prompt.txt').write_bytes((parent/'prompt.txt').read_bytes())
write(out/'recovery_intent.json',dict(created_at=now(),character=NAME,direction='Up',revision=revision,
    owner_thread_id=os.environ['CODEX_THREAD_ID'],dispatch_token=TOKEN,max_requests=1,
    authorization_sha256=sha(authorization).lower(),application_sha256=sha(application).lower(),
    prior_revision='initial' if prior==parent else prior.name,prior_request_sha256=sha(prior/'request.json').lower(),
    prior_uncertain_sha256=sha(prior/'uncertain_result.json').lower(),prior_console_sha256=sha(prior/'console.txt').lower(),
    additional_attempt=used+1,reason='Verified standing human decision covers this uncertain network failure; preserve original and keep parameters/cap unchanged.',
    prompt_sha256=sha(out/'prompt.txt'),protected_six=read(D/'incremental_before_20261028.json')['protected_six']))
c=owner();c.update(current_stage='Tiger_Up_bounded_standing_Curl55_recovery',last_stage_evidence=str(application.relative_to(R)).replace('\\','/'),updated_at=now());write(H/'conversation_chain.json',c)
print(json.dumps(dict(revision=revision,additional_attempt=used+1,max_additional=2,original_outcome='uncertain_preserved',production_changes=0)))
