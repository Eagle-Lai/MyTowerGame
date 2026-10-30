"""Read-only closeout checks; write evidence only in this character's Docs folder."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import difflib
import hashlib
import json
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(RUN))
from mcp_call import Client
from PIL import Image

TOKEN = 'winterwarg-to-winterwolftypea-20261029_173527-8e8dd053-9008-4a8f-b69a-61a589f400a4'
STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
NOW = datetime.now(timezone(timedelta(hours=8))).isoformat()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def save(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return relative(path)


def unbox(value):
    if 'structuredContent' in value:
        return value['structuredContent']
    return json.loads(next(c['text'] for c in value['content'] if c.get('type') == 'text'))


chain = load(RUN / 'conversation_chain.json')
assert chain['state'] == 'active'
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['dispatch_token'] == TOKEN and chain['current_character'] == 'WinterWolfTypeA'

# Never save or display complete process command lines: unrelated Unity launches contain credentials.
ps = r"""$directionProcesses = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'curl.exe' -or
    ($_.Name -match '^(node|python|powershell|pwsh)\.exe$' -and
     $_.CommandLine -match '(generate\.mjs|generate_character\.ps1)')
} | Select-Object ProcessId,Name,@{n='current_character';e={$_.CommandLine -match 'WinterWolfTypeA'}},@{n='image_generator';e={$_.CommandLine -match '(generate\.mjs|generate_character\.ps1)'}})
ConvertTo-Json -InputObject $directionProcesses -Depth 3"""
result = subprocess.run(['powershell.exe', '-NoProfile', '-Command', ps], capture_output=True, text=True, check=True)
processes = json.loads(result.stdout or '[]')
assert not any(p['image_generator'] or p['current_character'] for p in processes), processes
process_file = save('request_process_recheck_' + STAMP + '.json', {
    'observed_at': NOW, 'owner_thread_id': chain['owner_thread_id'], 'dispatch_token': TOKEN,
    'processes': processes, 'active_current_generator_found': False,
    'limits': 'Local processes cannot establish whether the provider accepted a prior request or charged it.'
})

attempts = []
for name in ['', 'revision_01', 'revision_02']:
    folder = HERE / 'generation' / 'Down' / name
    request = load(folder / 'request.json')
    uncertain = load(folder / 'uncertain_result.json')
    assert not (folder / 'raw.png').exists() and not (folder / 'result.json').exists()
    attempts.append({
        'path': relative(folder), 'started': request.get('started'), 'finished': uncertain.get('finished'),
        'endpoint': request.get('endpoint'), 'model': request.get('model'),
        'quality': request.get('quality'), 'size': request.get('size'), 'n': request.get('n'),
        'transport': request.get('transport'), 'recovery': request.get('recovery'),
        'message': uncertain.get('message'), 'http_status': None, 'raw_image': None,
        'result': None, 'provider_query_id': None, 'charge': 'unknown',
        'evidence_sha256': {p.name: sha(p) for p in sorted(folder.iterdir()) if p.is_file()},
    })
assert len(list((HERE / 'generation' / 'Down').rglob('request.json'))) == 3
request_file = save('down_request_recheck_' + STAMP + '.json', {
    'observed_at': NOW, 'attempts': attempts, 'requests': 3, 'unknown_outcomes': 3,
    'additional_recovery_used': 2, 'additional_recovery_limit': 2,
    'limit_origin': 'Conservative agent execution bound, not a user monetary budget',
    'no_new_paid_request_in_closeout': True, 'process_check': process_file,
})

# Fresh identity discovery precedes every editor call; no refresh, compile request or Play is needed.
client = Client()
project = client.identity()
errors = client.tool('read_console', {'action': 'get', 'types': ['error'], 'count': '50', 'format': 'json'})
state = client.resource('mcpforunity://editor/state')
probe = client.tool('execute_code', {'action': 'execute', 'code': 'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,manual=FTProject.GameClock.IsManualSimulation,scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty,scenes=System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount).Select(i=>new {path=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).path,dirty=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty}).ToArray()};'})
error_cs = client.tool('read_console', {'action': 'get', 'types': ['error'], 'count': '50', 'format': 'json', 'filter_text': 'error CS'})
state_after = client.resource('mcpforunity://editor/state')
p = unbox(probe)['data']['result']
s = state_after['data']
log_entries = unbox(errors)['data']
assert isinstance(p, dict) and isinstance(log_entries, list)
safe = (not any(p[k] for k in ['playing', 'compiling', 'failed', 'review', 'balance', 'manual', 'dirty'])
        and all(not x['dirty'] for x in p['scenes'])
        and not s['compilation']['is_compiling']
        and not s['compilation']['is_domain_reload_pending']
        and not s['assets']['is_updating'] and not s['tests']['is_running']
        and not any(s['editor']['play_mode'].values()) and s['advice']['ready_for_tools'])
unity_file = save('unity_release_blocked_' + STAMP + '.json', {
    'observed_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
    'transport': 'http://127.0.0.1:8088/mcp', 'project': project,
    'errors': errors, 'error_cs': error_cs, 'state_before': state, 'probe': probe,
    'state_after': state_after, 'safe_release': safe, 'error_count_returned': len(log_entries),
    'no_refresh_or_compile_request': True, 'no_play_or_scene_mutation': True,
    'protocol_history': client.history,
})
assert safe, unity_file

before = load(HERE / 'production_paths_before_20261029.json')
after = {relative(p): sha(p) for folder in ['Assets', 'Packages', 'ProjectSettings', 'Luban']
         for p in sorted((ROOT / folder).rglob('*')) if p.is_file()}
changes = [{'path': path, 'before': before.get(path), 'after': after.get(path),
            'kind': 'added' if path not in before else 'deleted' if path not in after else 'modified'}
           for path in sorted(set(before) | set(after)) if before.get(path) != after.get(path)]
sync = load(HERE / 'sync_start_20261029.json')
original = load(RUN / 'production_fingerprints_before.json')
six = {path: {'before': digest, 'after': after.get(path), 'original': original.get(path),
              'unchanged': digest == after.get(path) == original.get(path)}
       for path, digest in sync['protected_six'].items()}
invariant = {path: {'start': digest, 'now': sha(ROOT / path), 'unchanged': digest == sha(ROOT / path)}
             for path, digest in sync['read_full_json_sha256'].items()
             if Path(path).name not in ['progress.json', 'conversation_chain.json']}
scope_file = save('scope_incremental_blocked_' + STAMP + '.json', {
    'observed_at': NOW, 'method': 'Full file-path union and SHA256, including additions and deletions',
    'roots': ['Assets', 'Packages', 'ProjectSettings', 'Luban'],
    'before_file': relative(HERE / 'production_paths_before_20261029.json'),
    'before_count': len(before), 'after_count': len(after), 'changes': changes,
    'added': [x['path'] for x in changes if x['kind'] == 'added'],
    'deleted': [x['path'] for x in changes if x['kind'] == 'deleted'],
    'modified': [x['path'] for x in changes if x['kind'] == 'modified'],
    'protected_six': six, 'source_baselines_approval_gif_manifest': invariant,
    'production_unchanged': not changes, 'reporter_timestamp_exception_applied': False,
    'scope_limit': 'This task incremental audit only. Historical global scope failures are not reclassified.',
})
assert not changes and all(x['unchanged'] for x in six.values())
assert all(x['unchanged'] for x in invariant.values())

progress = load(RUN / 'progress.json')
completed = [x for x in progress['items'] if x['status'] in ['completed_pending_user_art_review', 'user_approved']]
remaining = sorted([x for x in progress['items'] if x not in completed], key=lambda x: x['index'])
assessment = []
for item in remaining:
    folder = RUN / item['name']
    files = sorted(p for p in folder.rglob('*') if p.is_file())
    phases = {key: [relative(p) for p in files if match(p)] for key, match in {
        'generated_images': lambda p: p.name == 'raw.png' and 'generation' in p.parts,
        'generation_results': lambda p: p.name == 'result.json' and 'generation' in p.parts,
        'generation_requests': lambda p: p.name == 'request.json' and 'generation' in p.parts,
        'staged_files': lambda p: any(x in ['staged', 'staged_art'] for x in p.parts),
        'install_manifests': lambda p: p.name == 'installed_manifest.json',
        'runtime_summaries': lambda p: p.name == 'runtime_summary.json',
        'runtime_images': lambda p: p.suffix.lower() in ['.png', '.gif'] and any(x.startswith('runtime') for x in p.parts),
    }.items()}
    reason = ('Historical Down outcome still unknown, no saved response/job ID or independent install/runtime phase.'
              if item['name'] == 'PossessedWarg' else
              'Down initial plus two bounded recovery requests have unknown outcomes. Up alone is not a complete four-direction asset.'
              if item['name'] == 'WinterWolfTypeA' else
              'Reference-only; first image generations depend on the currently failing shared paid POST path.')
    assessment.append({'index': item['index'], 'name': item['name'], 'status_at_scan': item['status'],
                       'recursive_file_count': len(files), 'phases': phases,
                       'independent_recoverable_delivery_phase': False, 'reason': reason,
                       'files': {relative(p): sha(p) for p in files}})
assert len(completed) == progress['completed_count'] == 101
assert [x['name'] for x in remaining] == ['PossessedWarg', 'WinterWolfTypeA', 'WinterWolfTypeB', 'Wolf', 'WolfHound', 'WolfMounfed', 'Zombie']
assert all(not any(x['phases'][k] for k in ['staged_files', 'install_manifests', 'runtime_summaries', 'runtime_images']) for x in assessment)
successor_file = save('successor_assessment_blocked_' + STAMP + '.json', {
    'observed_at': NOW, 'completed_count': 101, 'authorized_count': 108,
    'selection_order': 'Recover started usable phases, then minimum index not_started item',
    'remaining': assessment, 'normal_next_character': 'WinterWolfTypeB', 'normal_next_index': 114,
    'independent_successor_available': False, 'create_successor': False,
    'reason': 'All remaining full deliverables require the blocked image service. Do not create an empty chat or use another character as a paid service probe.',
})

up = HERE / 'generation' / 'Up'
images = []
for pth in [up / 'raw.png'] + sorted(up.glob('local_revision_*/raw.png')):
    with Image.open(pth) as image:
        images.append({'path': relative(pth), 'sha256': sha(pth), 'mode': image.mode,
                       'size': list(image.size), 'bytes': pth.stat().st_size})
review_file = save('up_art_review_blocked_' + STAMP + '.json', {
    'observed_at': NOW, 'character': 'WinterWolfTypeA',
    'review_basis': 'Actual full original atlas and serialized source reference, full Up AI raw, body/heel zoom comparisons and full local_revision_03 were viewed in this chat before context compaction. No additional image generation or repeat rendering in closeout.',
    'identity': load(HERE / 'anatomy_plan.json')['identity'],
    'images': images, 'last_reviewed_candidate': relative(up / 'local_revision_03' / 'raw.png'),
    'findings': [
        'Up AI heads show the brown pointed ears and face-free rear crown.',
        'Original Up torso duplicated ear-like protrusions; local_revision_01 removed them and closed the ivory shoulder crest.',
        'Rear paws originally retained front toe lines. Local revisions removed the lines; local_revision_02 left mottled fills.',
        'Local_revision_03 uses smooth flat ivory cel fill inside the lower rear heels and protects the four-pixel exterior border.',
        'Whole bushy tail remains ivory/taupe, following the actual original reference.',
    ],
    'local_raster_not_new_AI_output': True, 'history_preserved': True,
    'final_art_selection_created': False, 'staging_or_rig_acceptance': False,
    'not_validated': ['Down', 'true alpha removal', 'atlas and slicing', 'pivots and PPU', 'four-direction layout', 'animation and runtime'],
    'user_approved': False,
})

generator_before = HERE / 'generate_before_current_recovery_20261029.mjs'
generator_now = RUN / 'generate.mjs'
patch = ''.join(difflib.unified_diff(generator_before.read_text(encoding='utf-8').splitlines(True),
                                    generator_now.read_text(encoding='utf-8').splitlines(True),
                                    fromfile=relative(generator_before), tofile=relative(generator_now)))
patch_path = HERE / ('docs_generator_recovery_final_' + STAMP + '.patch')
patch_path.write_text(patch, encoding='utf-8')
tooling_file = save('docs_tooling_final_' + STAMP + '.json', {
    'before_sha256': sha(generator_before), 'after_sha256': sha(generator_now),
    'patch': relative(patch_path), 'unity_CSharp_modified': False,
    'scope': 'Docs generator only: current WinterWolfTypeA Down Curl55 standing recovery revisions01/02, and SHA-bound existing-proxy transport for revision02. Existing ownership, original authorization, no-existing-success, evidence and consumed-attempt guards remain.',
    'change_records': [relative(HERE / ('docs_generator_recovery_revision_0' + n + '.json')) for n in ['1', '2']],
    'additional_execution_performed_in_closeout': False,
})
outputs = {'observed_at': NOW, 'stamp': STAMP, 'process_check': process_file,
           'requests': request_file, 'unity_release': unity_file, 'scope': scope_file,
           'successor_assessment': successor_file, 'up_review': review_file,
           'docs_tooling': tooling_file, 'error_count': len(log_entries)}
save('closeout_inspection_index_' + STAMP + '.json', outputs)
print(json.dumps(outputs, ensure_ascii=False))
