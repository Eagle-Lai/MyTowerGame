"""Register an explicitly successful creation; chain activation is the last workspace write."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import re

HERE = Path(__file__).resolve().parent
ROOT = Path('E:/MyTowerGame')
RUN = HERE.parent
PARENT = '01a18832-7895-7a23-ba81-c2c410a5a454'
TOKEN = 'zombie-to-possessedwarg-20261030_092519-e9c91d1a-28d7-428f-ac88-9ea00046da2b'


def read(path):
    return Path(path).read_text(encoding='utf-8-sig')


def data(path):
    return json.loads(read(path))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def save_new(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def replace_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.possessedwarg_activation_tmp')
    save_new(temporary, value)
    temporary.replace(path)


assert os.environ.get('CODEX_THREAD_ID') == PARENT
response_path = HERE / 'creation_response.json'
response = data(response_path)
assert not response.get('isError'), 'Creation failed; retain handoff_ready'
texts = [part['text'] for part in response['content'] if part.get('type') == 'text']
assert len(texts) == 1, 'Inspect ambiguous creation response before activation'
created = json.loads(texts[0])
child = created.get('threadId')
host = created.get('hostId')
assert child and re.fullmatch(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', child)
assert child != PARENT and host == 'local' and not created.get('clientThreadId')
dispatch = data(HERE / 'prepared_dispatch.json')
assert dispatch['dispatch_token'] == TOKEN and dispatch['parent_thread_id'] == PARENT
assert dispatch['project_id'] == '935c594c-f414-48e0-bd08-ed8ba342f7fd'
assert dispatch['target']['environment'] == {'type': 'local'}
assert sha(ROOT / dispatch['prompt_file']) == dispatch['prompt_sha256']
assert sha(ROOT / dispatch['decision_file']) == dispatch['decision_sha256']
chain_path = RUN / 'conversation_chain.json'
progress_path = RUN / 'progress.json'
chain_before_sha = sha(chain_path)
chain = data(chain_path)
assert chain['state'] == 'handoff_ready' and chain['owner_thread_id'] == PARENT
assert chain['dispatch_token'] == TOKEN and chain['current_character'] == 'PossessedWarg'
assert not chain['successor_created'] and len(chain['dispatch_history']) == 37
assert not any(row.get('dispatch_token') == TOKEN for row in chain['dispatch_history'])
progress = data(progress_path)
assert progress['completed_count'] == 107 and progress['authorized_count'] == 108
remaining = [item for item in progress['items'] if item['status'] not in ('completed_pending_user_art_review', 'user_approved')]
assert len(remaining) == 1 and remaining[0]['name'] == 'PossessedWarg'
timestamp = datetime.now(timezone(timedelta(hours=8))).isoformat()
record = {
    'registered_at': timestamp, 'created': True, 'character': 'PossessedWarg',
    'thread_id': child, 'host_id': host, 'parent_thread_id': PARENT,
    'dispatch_token': TOKEN, 'project_id': dispatch['project_id'],
    'project_association_confirmed': True, 'environment': 'local',
    'prompt_file': dispatch['prompt_file'], 'prompt_sha256': dispatch['prompt_sha256'],
    'handoff_file': dispatch['handoff_file'], 'decision_file': dispatch['decision_file'],
    'creation_response_file': relative(response_path), 'creation_response_sha256': sha(response_path),
    'ownership_rule': 'Child alone may produce only after final active chain registration. Parent stops all workspace writes at that registration.',
}
save_new(HERE / 'creation_registered.json', record)
progress['updated_at'] = timestamp
progress['status'] = 'in_progress'
progress['resume_owner_thread_id'] = child
item = next(item for item in progress['items'] if item['name'] == 'PossessedWarg')
item.update(current_stage='authorized_resume_pending_generation', resume_owner_thread_id=child, resume_dispatch_token=TOKEN, resume_status='authorized_pending_execution')
replace_json(progress_path, progress)
chain['dispatch_history'].append({
    'sequence': 38, 'character': 'PossessedWarg', 'thread_id': child,
    'host_id': host, 'dispatch_token': TOKEN, 'created': True,
    'project_association_confirmed': True, 'project_id': dispatch['project_id'],
    'handoff_file': dispatch['handoff_file'], 'successor_prompt_file': dispatch['prompt_file'],
    'creation_response_file': relative(response_path), 'created_at': timestamp,
})
chain.update(state='active', owner_thread_id=child, owner_host_id=host,
             parent_thread_id=PARENT, dispatch_token=TOKEN, current_character='PossessedWarg',
             activated_at=timestamp, updated_at=timestamp, successor_created=True,
             successor_thread_id=child, dispatch_ready_for=None,
             current_stage='authorized_resume_pending_generation', current_blocked=False,
             character_status_at_handoff='reference_prepared',
             creation_response_file=relative(response_path),
             progress_sha256_at_handoff=sha(progress_path),
             parent_writes_stopped_at=timestamp,
             last_owner_character='PossessedWarg',
             last_stage_evidence=dispatch['decision_file'],
             unity_release_is_historical=True,
             ownership_transfer_note='Fresh local PossessedWarg successor registered. Only this child owns production and Unity under the new token. Parent stops every workspace write after this activation; old Down outcome and charge remain unknown.')
if 'stop_record' in chain:
    chain['previous_stop_record'] = chain.pop('stop_record')
chain.setdefault('stage_history', []).append({'at': timestamp, 'character': 'PossessedWarg', 'stage': 'authorized_resume_owner_activated', 'owner_thread_id': child, 'dispatch_token': TOKEN, 'evidence': relative(HERE / 'creation_registered.json')})
assert sha(chain_path) == chain_before_sha, 'Concurrent chain change: do not overwrite'
replace_json(chain_path, chain)
print(json.dumps({'state': 'active', 'character': 'PossessedWarg', 'owner_thread_id': child, 'owner_host_id': host, 'dispatch_token': TOKEN, 'parent_workspace_writes_stopped': True}, ensure_ascii=False))
