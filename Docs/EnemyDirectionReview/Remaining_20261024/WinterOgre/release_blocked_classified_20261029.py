"""Close the exhausted WinterOgre request sequence without another image request.

The original failed release script and its stamp are evidence, not retry inputs.
Only the exact observed Reporter timestamp drift and MCP transport logs are
classified here. Any additional production drift or different error stops this
script before progress or chain ownership can change.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from session_winterogre import *


def unpack(response):
    value = response.get('structuredContent') or json.loads(response['content'][0]['text'])
    assert value.get('success'), value
    return value


owner()
stamp_record = read(D/'blocked_closeout_stamp.json')
stamp = stamp_record['stamp']
assert stamp == '20261029_134607'
assert not (D/('blocked_generation_recovery_'+stamp+'.json')).exists()
baseline = read(D/'incremental_before_20261029.json')
expected_reporter_change = dict(
    path='Assets/StreamingAssets/build_info',
    before='B0F0E60D467FF1667D356F9F300769E32AC0DB6A99769DB65CD1580D5EF55A73',
    after='97518424ECA99D1F6E29D6946E56A9D899EFD32F740CD3B09C9D096415D466B3')
current = snapshot()
changes = [dict(path=p, before=baseline['files'].get(p), after=current.get(p))
           for p in sorted(set(baseline['files']) | set(current))
           if baseline['files'].get(p) != current.get(p)]
assert changes == [expected_reporter_change], changes
assert len(baseline['files']) == len(current) == 5545
assert all(current.get(p) == s for p, s in baseline['protected_six'].items())
reporter_source = 'Assets/Reporter/Editor/ReporterEditor.cs'
assert current[reporter_source] == baseline['files'][reporter_source]
assert (ROOT/expected_reporter_change['path']).read_text() == 'Build from BF-202610081033 at 2026/10/29 13:36:33'

write(D/('closeout_attempt_failed_'+stamp+'.json'), dict(
    recorded_at=now(), attempted_at=stamp_record['observed_at'],
    failed_script='release_blocked.py', failed_script_sha256=sha(D/'release_blocked.py'),
    observation='The original release stopped at its first assert not changes, after creating blocked_closeout_stamp.json. Later Unity/progress/chain closeout operations did not execute.',
    evidence_type='Retrospective record from the preserved script, stamp and subsequent drift investigation; not a captured original stdout transcript.',
    observed_changes=changes,
    followup='closeout_drift_probe_20261029.json',
    retained_stamp=True, original_script_and_baseline_preserved=True), fresh=True)

c = Client()
release = dict(observed_at=now(), transport='http://127.0.0.1:8088/mcp', project=c.identity())
release['errors_response'] = c.tool('read_console', dict(
    action='get', types=['error'], count='50', format='json', include_stacktrace=True))
errors = unpack(release['errors_response'])['data']
assert len(errors) == 2, errors
assert all('[WebSocket] Connection failed.' in e['message']
           and e['file'].replace('\\', '/').endswith('/Editor/Helpers/McpLog.cs')
           and 'WebSocketTransportClient' in (e.get('stackTrace') or '') for e in errors), errors
release['compile_errors_response'] = c.tool('read_console', dict(
    action='get', types=['error'], filter_text='error CS', count='50', format='json'))
assert unpack(release['compile_errors_response'])['data'] == []
release['cache_refresh'] = c.tool('execute_code', dict(action='execute', code=
    'var t=System.Linq.Enumerable.FirstOrDefault(System.Linq.Enumerable.Select(System.AppDomain.CurrentDomain.GetAssemblies(),a=>a.GetType("MCPForUnity.Editor.Services.EditorStateCache")),x=>x!=null);'
    'if(t==null)throw new System.Exception("Editor state cache type unavailable");'
    'var m=t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic);'
    'if(m==null)throw new System.Exception("Cache refresh unavailable");'
    'm.Invoke(null,new object[]{"WinterOgre factual blocked release; no Play or install"});return true;'))
release['state'] = c.resource('mcpforunity://editor/state')
release['live'] = probe(c)
idle(release['live'])
s = release['state']['data']
assert not s['tests']['is_running'] and s['advice']['ready_for_tools']
assert not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending']
assert not s['assets']['is_updating'] and not s['assets']['external_changes_dirty']
assert not s['staleness']['is_stale']
target_identity_file = sorted(D.glob('target_log_identity_*.json'))[-1]
target_log = result(read(target_identity_file)['response'])
log_path = Path(target_log['logPath'])
log_lines = log_path.read_text(encoding='utf-8', errors='replace').splitlines()
project_args = [log_lines[i+1] for i, line in enumerate(log_lines[:-1])
                if line.strip().lower() == '-projectpath']
release['log_identity_assessment'] = dict(
    target_probe=target_identity_file.name, target_probe_sha256=sha(target_identity_file),
    target_process_id=target_log['processId'], target_process_started=target_log['processStarted'],
    reported_log_path=str(log_path), current_log_header_project_arguments=project_args,
    target_console_entry_fields=target_log['logEntryFields'],
    conclusion='The shared local Editor.log currently names D:/FishTestGame. It is excluded as evidence for target Unity errors and timing. Target errors and stack traces come from the identity-checked 8088 read_console. Its LogEntry fields expose no timestamp; exact error emission times are unproven.')
release.update(
    error_count=len(errors), error_cs_count=0, error_free_release=False,
    errors_classification='Two retained MCP WebSocket transport connection errors; current 8088 identity, execute_code and editor/state requests succeeded. No current target script compilation failure. Exact historic emission time is unavailable.',
    error_observation_interval=dict(preflight_at=read(D/'preflight_20261029.json')['observed_at'], preflight_count=0,
                                    first_saved_nonzero_at=read(D/'closeout_drift_probe_20261029.json')['observed_at']),
    limitation='The requested console error0 condition is not satisfied. No logs cleared or errors relabelled as zero.',
    safe_to_stop_with_recorded_transport_error_limitation=True,
    no_play_mode_change=True, no_console_clear=True, no_asset_refresh_or_compilation_requested=True,
    successor_handoff_performed=False, completed_at=now(), protocol_history=c.history)
write(D/('unity_release_blocked_'+stamp+'.json'), release, fresh=True)

# Recheck the path union after the live read-only operations; never roll back drift.
final_snapshot = snapshot()
assert final_snapshot == current, 'Additional production drift during closeout'
write(D/('scope_incremental_blocked_'+stamp+'.json'), dict(
    observed_at=now(), basis='Current disk Assets/Packages/ProjectSettings/Luban SHA256 path union, including all pre-existing user changes; not Git HEAD',
    baseline='incremental_before_20261029.json', baseline_sha256=sha(D/'incremental_before_20261029.json'),
    baseline_files=len(baseline['files']), current_files=len(current), changes=changes,
    added=[], deleted=[], unexpected_incremental=[],
    classified_automatic_side_effects=[dict(**expected_reporter_change,
        text=(ROOT/expected_reporter_change['path']).read_text(), source=reporter_source,
        source_sha256=current[reporter_source], source_unchanged=True,
        mechanism='Existing InitializeOnLoad BuildInfo subscribes to EditorApplication.update; its initial isCompiling=true causes a timestamp write once compilation is idle, and on subsequent compile-to-idle transitions. A Play request is not required.',
        target_process_started=target_log['processStarted'],
        attribution_limit='Timestamp and unchanged existing callback are consistent with the observed editor restart/domain reload. No task Play or direct build_info write was performed; the callback itself was not instrumented.')],
    protected_six=baseline['protected_six'], protected_six_unchanged=True,
    character_production_resource_changes=[], shared_CSharp_drift=[], other_character_and_configuration_drift=[],
    global_audit='Historical 291 unexpected and six other-character semantic failures were not rerun or reclassified. This is an incremental SHA audit, not a global PASS.'), fresh=True)

attempts = []
for i, relative in enumerate(['generation/Up', 'generation/Up/revision_01', 'generation/Up/revision_02']):
    path = D/relative
    request = read(path/'request.json')
    assert not (path/'result.json').exists() and not (path/'raw.png').exists()
    assert (request['endpoint'], request['model'], request['quality'], request['size'], request['n']) == (
        'https://aihub.dog/v1/images/edits', 'gpt-image-2', 'medium', '1536x1024', 1)
    assert request.get('recovery', {}).get('additional_attempt', 0) == i
    assert all(sha(Path(p)).lower() == expected for p, expected in zip(request['inputs'], request['input_sha256']))
    attempts.append(dict(path=relative, started=request['started'], transport=request['transport'],
        outcome=read(path/'uncertain_result.json'), http_status=None, raw=None, result=None,
        charge='unknown_not_reclassified', recovery=request.get('recovery'),
        files={p.name:sha(p) for p in sorted(path.iterdir()) if p.is_file()}))
assert 'ECONNRESET' in (D/'generation/Up/revision_02/console.txt').read_text()
assert len(attempts) == 3 and sum(bool(a['recovery']) for a in attempts) == 2
assert not (D/'generation/Down/request.json').exists()
assert not any((D/'generation').rglob('raw.png')) and not any((D/'generation').rglob('result.json'))
assert not any((D/x).exists() for x in ['staged_art', 'installed_manifest.json', 'runtime_summary.json'])
process_query = subprocess.run(['powershell', '-NoProfile', '-Command',
    "@(Get-CimInstance Win32_Process | Where-Object { $_.Name -in @('node.exe','curl.exe') -and $_.CommandLine -match '(generate\\.mjs|WinterOgre)' } | ForEach-Object { @{pid=$_.ProcessId;name=$_.Name} }) | ConvertTo-Json -Compress"],
    capture_output=True, text=True, check=True)
active_generation = json.loads(process_query.stdout) if process_query.stdout.strip() else []
assert active_generation == [], active_generation

progress = read(H/'progress.json')
assert progress['completed_count'] == 99 and progress['authorized_count'] == 108
remaining = [i for i in progress['items'] if i['status'] not in ['completed_pending_user_art_review', 'user_approved']]
others = [i for i in remaining if i['name'] not in [NAME, 'PossessedWarg']]
assert len(remaining) == 9 and len(others) == 7 and all(i['status'] == 'not_started' for i in others)
assessment = []
for item in remaining:
    folder = H/item['name']
    files = sorted(p for p in folder.rglob('*') if p.is_file())
    stages = {key:[p.relative_to(folder).as_posix() for p in folder.rglob(key)]
              for key in ['raw.png', 'result.json', 'installed_manifest.json', 'runtime_summary.json']}
    if item in others:
        assert len(files) == 8 and all(p.relative_to(folder).parts[0] == 'reference' for p in files)
        assert not any(stages.values())
    assessment.append(dict(index=item['index'], name=item['name'], status_before_closeout=item['status'],
        existing_files={p.relative_to(folder).as_posix():sha(p) for p in files if '__pycache__' not in p.parts},
        stage_evidence=stages, common_image_network_dependency=item['status'] == 'not_started',
        recoverable_without_paid_request=False,
        reason='Up recovered image exists, but original Down paid request outcome is still unknown; preserve its old blocker.'
            if item['name'] == 'PossessedWarg' else
            'Three Up outcomes unknown, no raw or staged/installed/runtime result, additional retry cap exhausted.'
            if item['name'] == NAME else
            'Reference files only; no independent generated/staged/installed/runtime work. Shares blocked image endpoint.'))
assert next(i for i in remaining if i['name'] == 'PossessedWarg')['status'] == 'blocked'
write(D/('successor_assessment_blocked_'+stamp+'.json'), dict(
    observed_at=now(), remaining=assessment, selected_successor=None,
    active_generation_processes=active_generation,
    reason='No independent unpaid continuation. Seven reference-only characters depend on the same image endpoint. Do not use another direction or character as a paid service probe. PossessedWarg Down remains unknown.'), fresh=True)

entry = H/'generate.mjs'
original = D/'generate_entry_before_recovery.mjs'
diff = subprocess.run(['git','diff','--no-index','--',str(original),str(entry)],
    capture_output=True, text=True, encoding='utf-8')
assert diff.returncode in [0, 1]
write(D/('docs_tooling_change_'+stamp+'.json'), dict(
    observed_at=now(), path=entry.relative_to(ROOT).as_posix(), before_sha256=sha(original), after_sha256=sha(entry),
    diff=diff.stdout,
    scope='Docs-only exact WinterOgre Up Curl55 application for revision_01/revision_02. Existing owner/token/input SHA/intent checks, two-additional-attempt cap, same endpoint/model/quality/size/n and no-auto-retry preserved; not Unity C#.'), fresh=True)
reason = ('WinterOgre Up initial and revision_01 ended Curl55 send-aborted; revision_02 ended fetch failed / ECONNRESET before secure TLS. '
          'No HTTP result, image or service query ID. Both additional recovery attempts are exhausted. '
          'All three outcomes and possible charges remain unknown. Down unrequested; no independent unpaid continuation in the remaining queue.')
blocked = dict(observed_at=now(), character=NAME, index=111, status='blocked', user_approved=False,
    owner_thread_id=OWNER, dispatch_token=TOKEN, reason=reason, attempts=attempts,
    new_requests=3, new_HTTP200=0, new_uncertain=3, additional_network_attempts_used=dict(Up=2, Down=0), network_limit=2,
    cost='Unknown; no actual bill or usage response returned. Do not infer zero charge.',
    down='Prompt only; no paid request', source_review='reference_review_20261029.json',
    source_contract='source_contract_20261029.json', character_production_changes=False,
    automatic_production_side_effect=expected_reporter_change,
    staging='not_executed', install_verify='not_executed', runtime='not_executed', record='not_executed', new_gifs=0,
    completed_count=99, allgif_count=read(H.parent/'AllGIF/manifest.json')['count'],
    scope='scope_incremental_blocked_'+stamp+'.json', unity_release='unity_release_blocked_'+stamp+'.json',
    successor_assessment='successor_assessment_blocked_'+stamp+'.json', docs_tooling='docs_tooling_change_'+stamp+'.json',
    retained_failed_closeout='closeout_attempt_failed_'+stamp+'.json',
    unity_error_count=len(errors), unity_error_free_release=False,
    unity_limitation='Two retained MCP connection errors; current endpoint works, editor is idle and compilationFailed=false. error0 is unmet.',
    no_successor_created=True,
    recovery='First inspect preserved requests/processes/provider result availability without another paid request. Reuse an existing recovered raw if available. No third additional Up request, reset, Down or other-character paid probe. Any new paid recovery needs actual resolution evidence and a newly permitted bounded scope; preserve all unknown outcomes and charges.')
assert blocked['allgif_count'] == 1594
write(D/('blocked_generation_recovery_'+stamp+'.json'), blocked, fresh=True)
print(json.dumps(dict(stamp=stamp, completed_count=99, character_status='blocked_evidence_ready',
    requests=3, uncertain=3, errors=len(errors), compiler_failed=release['live']['failed'],
    production_changes=changes, no_successor=True), ensure_ascii=False))
