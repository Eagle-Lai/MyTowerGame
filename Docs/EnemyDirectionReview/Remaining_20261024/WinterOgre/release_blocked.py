from session_winterogre import *
import re

owner()
stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
write(D/'blocked_closeout_stamp.json',dict(stamp=stamp,observed_at=now()),fresh=True)
baseline=read(D/'incremental_before_20261029.json')
current=snapshot()
changes=[dict(path=p,before=baseline['files'].get(p),after=current.get(p)) for p in sorted(set(baseline['files'])|set(current)) if baseline['files'].get(p)!=current.get(p)]
assert not changes,changes
assert all(current[p]==s for p,s in baseline['protected_six'].items())
write(D/('scope_incremental_blocked_'+stamp+'.json'),dict(observed_at=now(),basis='Current disk Assets/Packages/ProjectSettings/Luban SHA256 union including all pre-existing modifications; not Git HEAD',baseline='incremental_before_20261029.json',baseline_sha256=sha(D/'incremental_before_20261029.json'),baseline_files=len(baseline['files']),current_files=len(current),changes=changes,added=[],deleted=[],unexpected_incremental=[],protected_six=baseline['protected_six'],protected_six_unchanged=True,shared_CSharp_drift=[],other_character_and_configuration_drift=[],global_audit='Historical 291 unexpected and six other-character semantic failures not rerun or reclassified. This is only a zero-incremental-change audit.'),fresh=True)
c=Client()
report=dict(observed_at=now(),transport='http://127.0.0.1:8088/mcp',project=c.identity())
report['errors_response']=c.tool('read_console',dict(action='get',types=['error'],count='50',format='json'))
errors=report['errors_response'].get('structuredContent') or json.loads(report['errors_response']['content'][0]['text'])
assert errors.get('success') and errors['data']==[],errors
report['cache_refresh']=c.tool('execute_code',dict(action='execute',code='var t=System.Linq.Enumerable.FirstOrDefault(System.Linq.Enumerable.Select(System.AppDomain.CurrentDomain.GetAssemblies(),a=>a.GetType("MCPForUnity.Editor.Services.EditorStateCache")),x=>x!=null);if(t==null)throw new System.Exception("Editor state cache type unavailable");var m=t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic);if(m==null)throw new System.Exception("Cache refresh unavailable");m.Invoke(null,new object[]{"WinterOgre factual blocked release; no Play or install"});return true;'))
report['state']=c.resource('mcpforunity://editor/state')
report['live']=probe(c)
idle(report['live'])
s=report['state']['data']
assert not s['tests']['is_running'] and s['advice']['ready_for_tools']
assert not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending']
assert not s['assets']['is_updating'] and not s['assets']['external_changes_dirty'] and not s['staleness']['is_stale']
report['error_count']=0
report['safe_to_handoff']=True
report['no_play_mode_change']=True
report['no_console_clear']=True
report['protocol_history']=c.history
write(D/('unity_release_blocked_'+stamp+'.json'),report,fresh=True)
attempts=[]
for relative in ['generation/Up','generation/Up/revision_01','generation/Up/revision_02']:
    path=D/relative
    request=read(path/'request.json')
    assert not (path/'result.json').exists() and not (path/'raw.png').exists()
    assert request['model']=='gpt-image-2' and request['quality']=='medium' and request['size']=='1536x1024' and request['n']==1
    attempts.append(dict(path=relative,started=request['started'],transport=request['transport'],outcome=read(path/'uncertain_result.json'),http_status=None,raw=None,result=None,charge='unknown_not_reclassified',recovery=request.get('recovery'),files={p.name:sha(p) for p in sorted(path.iterdir()) if p.is_file()}))
assert len(attempts)==3 and sum(bool(a['recovery']) for a in attempts)==2
assert not (D/'generation/Down/request.json').exists()
assert not any((D/'generation').rglob('raw.png'))
assert not any((D/'generation').rglob('result.json'))
assert not any((D/x).exists() for x in ['staged_art','installed_manifest.json','runtime_summary.json'])
progress=read(H/'progress.json')
assert progress['completed_count']==99 and progress['authorized_count']==108
remaining=[i for i in progress['items'] if i['status'] not in ['completed_pending_user_art_review','user_approved']]
assessment=[]
for item in remaining:
    folder=H/item['name']
    existing=sorted(p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file())
    stages={key:[p.relative_to(folder).as_posix() for p in folder.rglob(key)] for key in ['raw.png','installed_manifest.json','runtime_summary.json']}
    assessment.append(dict(index=item['index'],name=item['name'],status=item['status'],existing_files=existing,stage_evidence=stages,common_image_network_dependency=item['status']=='not_started',recoverable_without_paid_request=False))
assert len(remaining)==9
others=[i for i in remaining if i['name'] not in [NAME,'PossessedWarg']]
assert len(others)==7 and all(i['status']=='not_started' for i in others)
assert all(not any(x['stage_evidence'].values()) for x in assessment if x['name'] not in [NAME,'PossessedWarg'])
assert next(i for i in remaining if i['name']=='PossessedWarg')['status']=='blocked'
write(D/('successor_assessment_blocked_'+stamp+'.json'),dict(observed_at=now(),remaining=assessment,selected_successor=None,reason='No independent staged/installed/runtime work. Seven unstarted characters depend on the same image endpoint and have reference files only; do not use a new character as a paid probe after the network retry cap. PossessedWarg original Down outcome remains unknown and blocked.'),fresh=True)
entry=H/'generate.mjs'
original=D/'generate_entry_before_recovery.mjs'
write(D/('docs_tooling_change_'+stamp+'.json'),dict(observed_at=now(),path=entry.relative_to(ROOT).as_posix(),before_sha256=sha(original),after_sha256=sha(entry),diff=subprocess.run(['git','diff','--no-index','--',str(original),str(entry)],capture_output=True,text=True,encoding='utf-8').stdout,scope='Docs-only exact WinterOgre Up Curl55 application for revision_01/revision_02. Existing owner/token/input SHA/intent checks, two-attempt cap, same endpoint/model/quality/size/n and no-auto-retry preserved; not shared Unity C#.'),fresh=True)
reason='WinterOgre Up initial and revision_01 ended Curl55 send-aborted, revision_02 ended fetch failed / ECONNRESET before secure TLS. No HTTP result, image or service query ID. Both additional recovery attempts are exhausted. All three outcomes and possible charges remain unknown; stop paid requests. Down unrequested. No independent non-paid continuation in the remaining queue.'
blocked=dict(observed_at=now(),character=NAME,index=111,status='blocked',user_approved=False,owner_thread_id=OWNER,dispatch_token=TOKEN,reason=reason,attempts=attempts,new_requests=3,new_HTTP200=0,new_uncertain=3,additional_network_attempts_used=dict(Up=2,Down=0),network_limit=2,cost='Unknown; no actual bill or usage response returned. No no-charge inference.',down='Prompt only; no paid request',source_review='reference_review_20261029.json',source_contract='source_contract_20261029.json',production_changes=False,staging='not_executed',install_verify='not_executed',runtime='not_executed',record='not_executed',new_gifs=0,completed_count=99,allgif_count=read(H.parent/'AllGIF/manifest.json')['count'],scope='scope_incremental_blocked_'+stamp+'.json',unity_release='unity_release_blocked_'+stamp+'.json',successor_assessment='successor_assessment_blocked_'+stamp+'.json',docs_tooling='docs_tooling_change_'+stamp+'.json',no_successor_created=True,recovery='Inspect preserved requests/processes/result availability. No third additional request or new revision without an actual network-resolution assessment and newly permitted bounded execution. Reuse a returned existing raw if recovered, then resume original stage-by-stage work; never reset the two-attempt count or unknown charges.')
assert blocked['allgif_count']==1594
write(D/('blocked_generation_recovery_'+stamp+'.json'),blocked,fresh=True)
print(json.dumps(dict(stamp=stamp,production_changed=changes,baseline_files=len(current),requests=3,uncertain=3,Down='not_requested',unity=report['live'],errors=0,no_successor=True)))
