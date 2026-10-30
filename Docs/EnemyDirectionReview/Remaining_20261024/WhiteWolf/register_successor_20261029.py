"""Final parent workspace write: register the actual fresh local WildGoat owner."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
OWNER = '01a183d9-2ad7-73d2-b736-3057ef92f215'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()

def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

assert os.environ['CODEX_THREAD_ID'] == OWNER
dispatch_path = H / 'WildGoat/prepared_dispatch_20261029.json'
dispatch = read(dispatch_path)
chain = read(H / 'conversation_chain.json')
thread, host = sys.argv[1:3]
response_path = ROOT / dispatch['response_file']
raw = read(response_path)
assert raw.get('isError') is not True
result = raw.get('structuredContent') or next(json.loads(r['text']) for r in raw['content'] if r['type'] == 'text')
if isinstance(result, str):
    result = json.loads(result)
assert result['threadId'] == thread and result['hostId'] == host and host == 'local'
assert chain['state'] == 'handoff_ready' and chain['owner_thread_id'] == OWNER
assert chain['parent_thread_id'] == OWNER and chain['current_character'] == 'WildGoat'
assert chain['dispatch_token'] == dispatch['dispatch_token'] and dispatch['created'] is False
assert dispatch['project_live_confirmed'] and dispatch['project_id']
assert sha(ROOT / dispatch['project_list_response_file']) == dispatch['project_list_response_sha256']
for key in ['prompt', 'handoff', 'assessment', 'unity_release', 'next_task']:
    assert sha(ROOT / dispatch[key + '_file']) == dispatch[key + '_sha256']
assert sha(H / 'progress.json') == dispatch['progress_sha256']
assert not any(r.get('dispatch_token') == dispatch['dispatch_token'] for r in chain.get('dispatch_history', []))
stamp = datetime.now(timezone(timedelta(hours=8))).isoformat()
dispatch.update(created=True, created_at=stamp, thread_id=thread, host_id=host,
                response_sha256=sha(response_path), project_association_confirmed=True)
write(dispatch_path, dispatch)
history = chain.setdefault('dispatch_history', [])
sequence = max((r.get('sequence', 0) for r in history), default=0) + 1
history.append({
    'sequence': sequence, 'character': 'WildGoat', 'thread_id': thread, 'host_id': host,
    'dispatch_token': dispatch['dispatch_token'], 'created': True, 'project_association_confirmed': True,
    'project_id': dispatch['project_id'], 'handoff_file': dispatch['handoff_file'],
    'successor_prompt_file': dispatch['prompt_file'], 'creation_response_file': dispatch['response_file'],
    'created_at': stamp})
chain.update(
    state='active', parent_thread_id=OWNER, owner_thread_id=thread, owner_host_id=host,
    project_id=dispatch['project_id'], successor_created=True,
    creation_response_file=dispatch['response_file'], dispatch_ready_for=None,
    current_stage='not_started_owner_registered', last_stage_evidence=dispatch['assessment_file'],
    resume_character='WildGoat', resume_stage='Verify owner/token; inspect WildGoat anatomy and native motion; establish its own baseline',
    ownership_transfer_note='Fresh local WildGoat child confirmed and registered. Child owns production/Unity; parent stops all workspace writes.',
    updated_at=stamp, activated_at=stamp, parent_writes_stopped_at=stamp)
write(H / 'conversation_chain.json', chain)
print(json.dumps({'state': 'active', 'thread_id': thread, 'host_id': host, 'character': 'WildGoat',
                  'sequence': sequence, 'dispatch_token': dispatch['dispatch_token'],
                  'project_association_confirmed': True}, ensure_ascii=False))
