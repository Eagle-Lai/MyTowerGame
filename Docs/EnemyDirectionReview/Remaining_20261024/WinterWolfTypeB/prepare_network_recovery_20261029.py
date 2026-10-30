from pathlib import Path
import json,sys,hashlib,shutil,difflib,subprocess
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from session_current import owner,read,save,now
chain=owner();RUN=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
revision,prior=sys.argv[1:3]
assert revision in ['revision_01','revision_02']
parent=HERE/'generation/Up';before=parent if prior=='initial' else parent/prior
assert not list(parent.rglob('raw.png'))
assert read(before/'uncertain_result.json')['message'].startswith('curl transport failed 55 curl: (55) Send failure: Connection was aborted')
assert not (before/'result.json').exists()
assert 'curl: (55) Send failure: Connection was aborted' in (before/'console.txt').read_text(encoding='utf-8-sig')
used=sum(read(p).get('recovery',{}).get('mode')=='standing_user_authorized_network_recovery' for p in parent.rglob('request.json'))
assert used<2 and int(revision[-2:])==used+1
authfile=RUN/'standing_network_recovery_authorization_20261028.json';auth=read(authfile)
original_path=RUN/'WinterWolfTypeA/standing_authorization_original_messages_20261029.json';original=read(original_path)
assert any(i.get('id')=='01a180aa-7768-7222-bc85-7aa51e801cdd' and i['content'][0]['text'].strip()==auth['user_statement'] for t in original['turns'] for i in t['items'])
assert auth['accept_possible_duplicate_charge'] and auth['chain_id']==chain['chain_id'] and auth['max_additional_network_retries_per_direction']==2
application=HERE/'standing_recovery_application_20261029_Up.json'
if not application.exists():
    save(application,dict(recorded_at=now(),character='WinterWolfTypeB',direction='Up',owner_thread_id=chain['owner_thread_id'],dispatch_token=chain['dispatch_token'],
        user_statement=auth['user_statement'],source_thread_id=original['thread'],source_turn_id='01a180aa-774c-7ee3-8d35-d144e9389b9a',source_user_message_id='01a180aa-7768-7222-bc85-7aa51e801cdd',
        source_verified='Read original selected human messages preserved by predecessor; exact human reply matches standing authorization. Not a new live read and not the prior-character one-off Down03 grant.',
        original_messages_file=original_path.relative_to(RUN).as_posix(),original_messages_sha256=sha(original_path),authorization_sha256=sha(authfile),
        accept_possible_duplicate_charge=True,max_additional_network_retries_per_direction=2,limit_origin=auth['limit_origin'],
        interpretation='Same documented uncertain transport interruption class, Curl55 send abort. Apply standing chain authorization to this character with max two additional attempts; old outcome and charge remain unknown.',
        preserved_evidence=[{'path':p.relative_to(HERE).as_posix(),'sha256':sha(p)} for p in sorted(parent.iterdir()) if p.is_file()],
        parameters=auth['parameters'],process_check='Original generator exited and current Win32_Process scan has no generate.mjs process.',
        result_lookup='No HTTP/raw/result/job ID returned; no documented individual result lookup. Request is not treated as unsent or uncharged.',
        free_control='unauthenticated_direct_edge_control_20261029.json: complete upload506669, TLS verification0, actual remote191.101.132.254 HTTP401; verifies TLS/upload only, not authenticated image service recovery.'))
    generator=RUN/'generate.mjs';old=generator.read_text(encoding='utf-8')
    backup=HERE/'generate_before_current_recovery_20261029.mjs';assert not backup.exists();shutil.copy2(generator,backup)
    marker="  if(!tigerCurl55&&!treasureChestCurl56&&!treasureChestCurl55&&!whiteWolfCurl&&!winterOgreCurl55&&!winterWargCurl55&&!winterWargCurl52&&!winterWolfTypeACurl55)"
    assert old.count(marker)==1
    new=old.replace(marker,"  const winterWolfTypeBCurl55=name==='WinterWolfTypeB'&&direction==='Up'&&['revision_01','revision_02'].includes(revision)&&uncertain.message.startsWith('curl transport failed 55 curl: (55) Send failure: Connection was aborted')&&consoleText.includes('curl: (55) Send failure: Connection was aborted');\n"+marker[:-1]+"&&!winterWolfTypeBCurl55)")
    needle="whiteWolfCurl||winterOgreCurl55||winterWargCurl55||winterWolfTypeACurl55?"
    assert new.count(needle)==1
    new=new.replace(needle,needle[:-1]+'||winterWolfTypeBCurl55?')
    generator.write_text(new,encoding='utf-8')
    patch=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(backup),tofile=str(generator)))
    (HERE/'docs_generator_recovery_20261029.patch').write_text(patch,encoding='utf-8')
    save(HERE/'docs_generator_recovery_20261029.json',{'before_sha256':sha(backup),'after_sha256':sha(generator),'backup':str(backup),
        'scope':'Only WinterWolfTypeB Up Curl55 exact failure application added to documented standing guard. Active owner/token, preserved SHA, no-success reuse, two-attempt counter and user --resolve route unchanged. No production or C# changes.'})
out=parent/revision;assert not out.exists();out.mkdir();shutil.copy2(parent/'prompt.txt',out/'prompt.txt')
save(out/'recovery_intent.json',dict(recorded_at=now(),character='WinterWolfTypeB',direction='Up',revision=revision,prior_revision=prior,
    owner_thread_id=chain['owner_thread_id'],dispatch_token=chain['dispatch_token'],max_requests=1,authorization_sha256=sha(authfile),application_sha256=sha(application),
    prior_request_sha256=sha(before/'request.json'),prior_uncertain_sha256=sha(before/'uncertain_result.json'),prior_console_sha256=sha(before/'console.txt'),
    reason='Existing verified standing human grant, same Curl55 uncertain network class. Fresh single production attempt on same direct pinned route. All old outcomes and charges remain unknown.'))
print(json.dumps({'prepared':revision,'additional_attempt':used+1,'limit':2,'prior_outcome_and_charge':'unknown'}))
