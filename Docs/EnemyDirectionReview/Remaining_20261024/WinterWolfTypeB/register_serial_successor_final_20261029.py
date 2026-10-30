from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,os

D=Path(__file__).resolve().parent;H=D.parent;ROOT=H.parents[2]
OWNER='01a1879d-59b4-73a3-b061-6e37d031ddcb'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def write(p,obj):Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def unwrap(raw):return raw.get('structuredContent') or next(json.loads(c['text']) for c in raw['content'] if c['type']=='text')
assert os.environ['CODEX_THREAD_ID']==OWNER
chain=read(H/'conversation_chain.json');dispatchpath=D/'prepared_successor_dispatch_final_20261029.json';d=read(dispatchpath)
assert chain['state']=='handoff_ready' and chain['owner_thread_id']==chain['parent_thread_id']==OWNER
assert chain['current_character']==d['character']=='Wolf' and chain['dispatch_token']==d['dispatch_token'] and not d['created']
for key in ['prompt','handoff','assessment','unity_release','next_task']:
    assert sha(ROOT/d[key+'_file'])==d[key+'_sha256']
assert sha(H/'progress.json')==d['progress_sha256']
responsepath=ROOT/d['response_file'];raw=read(responsepath);r=unwrap(raw)
assert not raw.get('isError') and r['hostId']=='local' and r['threadId']!=OWNER
thread=r['threadId'];host=r['hostId'];assert thread
assert d['project_live_confirmed'] and sha(ROOT/d['project_list_response_file'])==d['project_list_response_sha256']
assert not any(row.get('dispatch_token')==d['dispatch_token'] for row in chain['dispatch_history'])
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
d.update(created=True,created_at=stamp,thread_id=thread,host_id=host,response_sha256=sha(responsepath),project_association_confirmed=True)
write(dispatchpath,d)
progress=read(H/'progress.json');item=next(r for r in progress['items'] if r['name']=='WinterWolfTypeB')
item.update(successor_created=True,successor_thread_id=thread,successor_dispatch_token=d['dispatch_token'])
progress['updated_at']=stamp;write(H/'progress.json',progress)
sequence=max(row.get('sequence',0) for row in chain['dispatch_history'])+1
chain['dispatch_history'].append({'sequence':sequence,'character':'Wolf','thread_id':thread,'host_id':host,
    'dispatch_token':d['dispatch_token'],'created':True,'project_association_confirmed':True,'project_id':d['project_id'],
    'handoff_file':d['handoff_file'],'successor_prompt_file':d['prompt_file'],'creation_response_file':d['response_file'],'created_at':stamp})
chain.update(state='active',owner_thread_id=thread,owner_host_id=host,parent_thread_id=OWNER,project_id=d['project_id'],
    successor_created=True,dispatch_ready_for=None,current_stage='not_started_owner_registered',last_stage_evidence=d['assessment_file'],
    resume_character='Wolf',resume_stage='Verify owner/token; inspect own source and native animation contract; establish baseline',
    progress_sha256_at_handoff=sha(H/'progress.json'),updated_at=stamp,activated_at=stamp,parent_writes_stopped_at=stamp,
    ownership_transfer_note='Fresh local Wolf successor registered. Child alone owns production and Unity; parent stops all workspace writes.')
# This must be the final workspace write by this parent chat.
write(H/'conversation_chain.json',chain)
print(json.dumps({'state':'active','thread_id':thread,'host_id':host,'character':'Wolf','sequence':sequence,
    'dispatch_token':d['dispatch_token'],'parent_mutations_stopped':True},ensure_ascii=False))
