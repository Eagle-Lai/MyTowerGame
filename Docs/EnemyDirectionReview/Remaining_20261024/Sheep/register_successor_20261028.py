"""Register exactly one explicitly successful creation; writing chain is the final workspace mutation."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys

D = Path(__file__).resolve().parent
H = D.parent
R = H.parents[2]
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p, value): p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def now(): return datetime.now(timezone(timedelta(hours=8))).isoformat()

response_path = Path(sys.argv[1]).resolve()
thread_id, host_id, project_id = sys.argv[2:5]
chain = read(H / 'conversation_chain.json')
assert chain['state'] == 'handoff_ready' and chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['current_character'] == 'SlugQueen' and chain['parent_thread_id'] == os.environ['CODEX_THREAD_ID']
dispatch_path = R / chain['prepared_dispatch_file']
dispatch = read(dispatch_path)
assert not dispatch['created'] and dispatch['dispatch_token'] == chain['dispatch_token']
assert sha(H / 'progress.json') == dispatch['progress_sha256'] and sha(R / dispatch['handoff_file']) == dispatch['handoff_sha256']
response = read(response_path)
assert thread_id in json.dumps(response, ensure_ascii=False) and thread_id != chain['owner_thread_id']
assert not response.get('isError') and host_id == 'local'
assert not any(x.get('thread_id') == thread_id for x in chain['dispatch_history'])
dispatch.update(created=True, created_at=now(), child_thread_id=thread_id, child_host_id=host_id, project_id=project_id, creation_response=response_path.relative_to(R).as_posix(), creation_response_sha256=sha(response_path))
write(dispatch_path, dispatch)
chain.setdefault('dispatch_history', []).append(dict(sequence=max(x['sequence'] for x in chain['dispatch_history']) + 1, character='SlugQueen', thread_id=thread_id, host_id=host_id, dispatch_token=chain['dispatch_token'], created=True, project_association_confirmed=True, handoff_file=chain['last_handoff_file'], created_at=now(), creation_response=response_path.relative_to(R).as_posix()))
chain.update(state='active', owner_thread_id=thread_id, owner_host_id=host_id, project_id=project_id, current_stage='not_started_reference_only', updated_at=now(), parent_writes_stopped_at=now(), ownership_transfer_note='Confirmed fresh local SlugQueen chat created. This ownership registration is the final parent workspace mutation; child owns all further work.')
write(H / 'conversation_chain.json', chain)
print(json.dumps(dict(state='active', owner_thread_id=thread_id, host_id=host_id, character='SlugQueen', token=chain['dispatch_token'], parent_writes_stopped=True), ensure_ascii=False))
