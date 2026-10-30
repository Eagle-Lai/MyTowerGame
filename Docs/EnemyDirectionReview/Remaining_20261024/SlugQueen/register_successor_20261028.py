"""Register one confirmed fresh Swine chat; chain write is final parent mutation."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,sys
D=Path(__file__).resolve().parent;H=D.parent;R=H.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
response_path=Path(sys.argv[1]).resolve();thread,host,project=sys.argv[2:5]
c=read(H/'conversation_chain.json');assert c['state']=='handoff_ready' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert c['current_character']=='Swine' and c['parent_thread_id']==os.environ['CODEX_THREAD_ID']
p=R/c['prepared_dispatch_file'];d=read(p)
assert not d['created'] and d['dispatch_token']==c['dispatch_token']
assert sha(H/'progress.json')==d['progress_sha256'] and sha(R/d['handoff_file'])==d['handoff_sha256']
response=read(response_path);assert thread in json.dumps(response,ensure_ascii=False) and thread!=c['owner_thread_id']
assert not response.get('isError') and host=='local' and not any(x.get('thread_id')==thread for x in c['dispatch_history'])
d.update(created=True,created_at=now(),child_thread_id=thread,child_host_id=host,project_id=project,creation_response=response_path.relative_to(R).as_posix(),creation_response_sha256=sha(response_path));write(p,d)
c.setdefault('dispatch_history',[]).append(dict(sequence=max(x['sequence'] for x in c['dispatch_history'])+1,character='Swine',thread_id=thread,host_id=host,dispatch_token=c['dispatch_token'],created=True,project_association_confirmed=True,handoff_file=c['last_handoff_file'],created_at=now(),creation_response=response_path.relative_to(R).as_posix()))
c.update(state='active',owner_thread_id=thread,owner_host_id=host,project_id=project,current_stage='not_started_reference_only',updated_at=now(),activated_at=now(),parent_writes_stopped_at=now(),ownership_transfer_note='Fresh local Swine chat confirmed. This registration is the final parent workspace mutation; child owns subsequent work.')
write(H/'conversation_chain.json',c)
print(json.dumps(dict(state='active',owner_thread_id=thread,host_id=host,character='Swine',token=c['dispatch_token'],parent_writes_stopped=True),ensure_ascii=False))
