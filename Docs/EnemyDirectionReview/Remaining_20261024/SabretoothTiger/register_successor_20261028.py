"""Register the one successful creation, then relinquish all write ownership."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os

D=Path(__file__).resolve().parent
HERE=D.parent
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def now(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
chain=read(HERE/'conversation_chain.json')
intent=read(D/'successor_dispatch_intent_20261028.json')
new_id='01a18093-7687-7313-aaba-7419090cc829'
assert chain['state']=='handoff_ready' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']==intent['parent_thread_id']
assert chain['dispatch_token']==intent['dispatch_token']=='sabretoothtiger-to-scarab-a14cefa3c87b4f9187c899d88ead8c0c'
assert chain['current_character']=='Scarab' and not chain['successor_created']
response_path=D/'successor_creation_response_20261028.json'
assert not response_path.exists(), 'Creation already saved; inspect, do not dispatch again'
write(response_path,dict(observed_at=now(),tool='create_thread',raw_response={'content':[{'type':'text','text':'{"threadId":"01a18093-7687-7313-aaba-7419090cc829","hostId":"local"}'}],'isError':False},
    thread_id=new_id,host_id='local',project_id=intent['project_id'],project_root=intent['project_root'],created=True,create_calls=1))
intent.update(state='created_registered_active',thread_id=new_id,host_id='local',activated_at=now(),creation_response_file=response_path.name)
write(D/'successor_dispatch_intent_20261028.json',intent)
chain.update(state='active',owner_thread_id=new_id,owner_host_id='local',current_character='Scarab',parent_thread_id=os.environ['CODEX_THREAD_ID'],
    activated_at=now(),updated_at=now(),dispatch_ready_for=None,successor_created=True,current_blocked=False,
    recovery_file=intent['assessment'],last_stage_evidence=intent['assessment'],resume_authorization=None,
    ownership_transfer_note='SabretoothTiger fully recorded, evidence persisted and Unity safely released. Exactly one fresh local Scarab successor created and registered. Parent stops all workspace and chain mutations after this write.')
chain['dispatch_history'].append(dict(sequence=max(x['sequence'] for x in chain['dispatch_history'])+1,character='Scarab',thread_id=new_id,host_id='local',
    dispatch_token=intent['dispatch_token'],created=True,project_association_confirmed=True,handoff_file=intent['handoff_file'],created_at=now(),
    creation_response_file='Docs/EnemyDirectionReview/Remaining_20261024/SabretoothTiger/'+response_path.name))
chain['progress_sha256_at_handoff']=hashlib.sha256((HERE/'progress.json').read_bytes()).hexdigest().upper()
write(HERE/'conversation_chain.json',chain)
# Ownership has transferred. Only read verification follows; no more document mutations.
check=read(HERE/'conversation_chain.json')
assert check['state']=='active' and check['owner_thread_id']==new_id and check['dispatch_token']==intent['dispatch_token']
print(json.dumps(dict(state=check['state'],new_owner=new_id,character=check['current_character'],dispatch_token=check['dispatch_token'],parent_write_ownership_released=True),ensure_ascii=False))
