"""Register a confirmed TreasureChest chat; chain write is the final parent mutation."""
from session_tiger import D,H,R,read,write,sha,now
import os,sys,json
from pathlib import Path

response_path = Path(sys.argv[1]).resolve()
thread,host,project = sys.argv[2:5]
chain = read(H/'conversation_chain.json')
assert chain['state'] == 'handoff_ready' and chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['current_character'] == 'TreasureChest' and chain['parent_thread_id'] == os.environ['CODEX_THREAD_ID']
dispatch_path = R/chain['prepared_dispatch_file'];dispatch = read(dispatch_path)
assert not dispatch['created'] and dispatch['dispatch_token'] == chain['dispatch_token']
assert sha(H/'progress.json') == dispatch['progress_sha256']
assert sha(R/dispatch['handoff_file']) == dispatch['handoff_sha256']
response = read(response_path)
assert thread in json.dumps(response,ensure_ascii=False) and thread != chain['owner_thread_id']
assert not response.get('isError') and host == 'local'
assert not any(x.get('thread_id') == thread for x in chain['dispatch_history'])
dispatch.update(created=True,created_at=now(),child_thread_id=thread,child_host_id=host,project_id=project,
    creation_response=response_path.relative_to(R).as_posix(),creation_response_sha256=sha(response_path))
write(dispatch_path,dispatch)
chain.setdefault('dispatch_history',[]).append(dict(sequence=max(x['sequence'] for x in chain['dispatch_history'])+1,
    character='TreasureChest',thread_id=thread,host_id=host,dispatch_token=chain['dispatch_token'],created=True,
    project_association_confirmed=True,handoff_file=chain['last_handoff_file'],created_at=now(),
    creation_response=response_path.relative_to(R).as_posix()))
chain.update(state='active',owner_thread_id=thread,owner_host_id=host,project_id=project,current_stage='not_started_reference_only',
    updated_at=now(),activated_at=now(),parent_writes_stopped_at=now(),successor_created=True,dispatch_ready_for=None,
    ownership_transfer_note='Fresh local TreasureChest chat confirmed. Registration is the final parent workspace mutation; child owns all subsequent work.')
write(H/'conversation_chain.json',chain)
print(json.dumps(dict(state='active',owner_thread_id=thread,host_id=host,character='TreasureChest',
    token=chain['dispatch_token'],parent_writes_stopped=True),ensure_ascii=False))
