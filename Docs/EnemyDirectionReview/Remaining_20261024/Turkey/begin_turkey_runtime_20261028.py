from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json
import os
import sys

D = Path(__file__).resolve().parent
H = D.parent
R = H.parents[2]
NAME = 'Turkey'
TOKEN = 'troll-to-turkey-1e2dd1235ed84e41b82b178e45f86309'
sys.path.insert(0, str(H))
from mcp_call import Client, URL


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def inventory():
    return {
        path.relative_to(R).as_posix(): sha(path)
        for folder in ['Assets', 'Packages', 'ProjectSettings', 'Luban']
        for path in (R / folder).rglob('*')
        if path.is_file()
    }


def unwrap(value):
    value = value.get('structuredContent') or json.loads(value['content'][0]['text'])
    if 'result' in value and 'data' not in value:
        value = value['result']
    assert value.get('success'), value
    return value


chain_path = H / 'conversation_chain.json'
progress_path = H / 'progress.json'
chain = read(chain_path)
assert chain['state'] == 'active'
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['current_character'] == NAME
assert chain['dispatch_token'] == TOKEN
assert chain['current_stage'] == 'preinstall_reviewed_pending_install'

progress = read(progress_path)
item = next(value for value in progress['items'] if value['name'] == NAME)
assert item['status'] == 'reference_prepared'
assert item.get('user_approved') is False
assert item['stage'] == 'preinstall_reviewed_pending_install'

assert not (D / 'runtime_r01').exists()
assert not (D / 'runtime_updeath_r01').exists()
assert not (D / 'runtime_summary.json').exists()

preinstall = read(D / 'preinstall_review_20261028.json')
assert preinstall['project']['projectRoot'].lower() == 'e:/mytowergame'
assert preinstall['decision']['user_approved'] is False
manifest = read(D / 'installed_manifest.json')
assert manifest['name'] == NAME
assert manifest['verification']['data']['result']['pass'] is True
verify_lines = (D / 'installed_verify.txt').read_text(encoding='utf-8-sig').splitlines()
assert verify_lines and all(line.startswith('PASS ') for line in verify_lines), verify_lines

baseline = read(D / 'incremental_before_20261028.json')
target = next(value for value in read(H / 'local_baseline.json')['targets'] if value['name'] == NAME)
before = baseline['files']
current = inventory()
expected = {entry['path']: entry['after'] for entry in manifest['changes']}
directory_meta = target['art_dir'] + '.meta'
unity_metadata = {}
if before.get(directory_meta) != current.get(directory_meta):
    assert current.get(directory_meta) is not None, 'Unity Directions folder metadata is missing'
    unity_metadata[directory_meta] = current[directory_meta]
changed = {
    path for path in set(before) | set(current)
    if before.get(path) != current.get(path)
}
allowed = {**expected, **unity_metadata}
assert changed == set(allowed), {
    'unexpected': sorted(changed - set(allowed)),
    'missing_manifest_paths': sorted(set(allowed) - changed),
}
assert all(current.get(path) == digest for path, digest in allowed.items())

client = Client()
project = client.identity()
errors = unwrap(client.tool('read_console', {
    'action': 'get', 'types': ['error'], 'count': '50', 'format': 'json'
}))
state = client.resource('mcpforunity://editor/state')
code = '''return new {
    playing = UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,
    compiling = UnityEditor.EditorApplication.isCompiling,
    failed = UnityEditor.EditorUtility.scriptCompilationFailed,
    updating = UnityEditor.EditorApplication.isUpdating,
    balance = FTProject.EditorTools.BalancePlayModeVerifier.Running,
    recording = FTProject.EditorTools.BalanceVideoRecorder.Running,
    review = FTProject.EditorTools.EnemyDirectionBatchReview.Running,
    manual = FTProject.GameClock.IsManualSimulation,
    dirty = System.Linq.Enumerable.Any(
        System.Linq.Enumerable.Range(0, UnityEngine.SceneManagement.SceneManager.sceneCount),
        i => UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),
    scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene().path,
    scenes = System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(
        System.Linq.Enumerable.Range(0, UnityEngine.SceneManagement.SceneManager.sceneCount),
        i => new {
            path = UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).path,
            dirty = UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty
        }))
};'''
live = unwrap(client.tool('execute_code', {'action': 'execute', 'code': code}))['data']['result']
state_data = state['data']
assert project['projectRoot'].replace('\\', '/').rstrip('/').lower() == 'e:/mytowergame'
assert project['unityVersion'] == (R / 'ProjectSettings/ProjectVersion.txt').read_text(encoding='utf-8-sig').splitlines()[0].split(':', 1)[1].strip()
assert errors['data'] == [], errors
assert not any(value for key, value in live.items() if key not in ['scene', 'scenes']), live
assert live['scene'] == 'Assets/Scenes/Boot.unity'
assert live['scenes'] == [{'path': 'Assets/Scenes/Boot.unity', 'dirty': False}], live
assert state_data['advice']['ready_for_tools'] is True
assert state_data['compilation']['is_compiling'] is False
assert state_data['compilation']['is_domain_reload_pending'] is False
assert state_data['assets']['is_updating'] is False
assert state_data['tests']['is_running'] is False

report = {
    'observed_at': now(),
    'owner_thread_id': chain['owner_thread_id'],
    'dispatch_token': TOKEN,
    'transport': URL,
    'project': project,
    'unity_instance': state_data['unity']['instance_id'],
    'editor_state': state,
    'live_probe': live,
    'existing_errors': errors,
    'baseline_sha256': sha(D / 'incremental_before_20261028.json'),
    'baseline_file_count': len(before),
    'install_manifest_sha256': sha(D / 'installed_manifest.json'),
    'install_verify_sha256': sha(D / 'installed_verify.txt'),
    'installed_file_changes_match_manifest_plus_unity_directory_meta': True,
    'installed_changed_paths': sorted(changed),
    'installed_manifest_paths': expected,
    'unity_created_directory_metadata': unity_metadata,
    'runtime_directories_absent': True,
    'protocol_history': client.history,
    'decision': {'begin_two_actual_play_runs': True, 'user_approved': False},
}
report_path = D / 'pre_runtime_review_20261028.json'
assert not report_path.exists()
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

item['stage'] = 'installed_pending_runtime'
progress.update(current=NAME, updated_at=now())
progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
chain = read(chain_path)
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID'] and chain['dispatch_token'] == TOKEN
chain.update(
    current_stage='installed_pending_runtime',
    last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Turkey/pre_runtime_review_20261028.json',
    updated_at=now(),
)
chain_path.write_text(json.dumps(chain, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print(json.dumps({
    'character': NAME,
    'project': project,
    'scene': live['scene'],
    'errors': len(errors['data']),
    'installed_files_match_manifest_plus_unity_directory_meta': True,
    'editor_ready': state_data['advice']['ready_for_tools'],
}, ensure_ascii=False))
