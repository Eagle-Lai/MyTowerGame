"""Bind the discovered local project, or make the parent's final workspace ownership write."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,sys

D=Path(__file__).resolve().parent;H=D.parent;ROOT=H.parents[2];N=H/'WinterWarg'
OWNER='01a18619-6aa0-7a31-ac62-10a82077950b'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def unwrap(v):
    r=v.get('structuredContent') or next(json.loads(c['text']) for c in v['content'] if c['type']=='text')
    return json.loads(r) if isinstance(r,str) else r
assert os.environ['CODEX_THREAD_ID']==OWNER
chain=read(H/'conversation_chain.json');dispatch_path=N/'prepared_dispatch_20261029.json';d=read(dispatch_path)
assert chain['state']=='handoff_ready' and chain['owner_thread_id']==chain['parent_thread_id']==OWNER
assert chain['current_character']==d['character']=='WinterWarg' and chain['dispatch_token']==d['dispatch_token'] and not d['created']
for key in ['prompt','handoff','assessment','unity_release','next_task']:
    assert sha(ROOT/d[key+'_file'])==d[key+'_sha256']
assert sha(H/'progress.json')==d['progress_sha256']
if sys.argv[1]=='bind-project':
    p=N/'project_list_response_20261029.json';result=unwrap(read(p))
    # Inspect the actual result schema; accept the documented project list wrapper.
    rows=result if isinstance(result,list) else result.get('projects',[])
    matches=[r for r in rows if str(r.get('path') or r.get('rootPath') or r.get('workspacePath') or '').replace('\\','/').rstrip('/').lower()=='e:/mytowergame']
    assert len(matches)==1,matches
    item=matches[0];pid=item.get('id') or item.get('projectId');assert pid
    d.update(project_id=pid,project_live_confirmed=True,project_list_response_file=p.relative_to(ROOT).as_posix(),project_list_response_sha256=sha(p))
    write(dispatch_path,d)
    print(json.dumps({'project_id':pid,'prompt_file':d['prompt_file'],'response_file':d['response_file']},ensure_ascii=False))
    raise SystemExit(0)
assert sys.argv[1]=='activate'
response_path=ROOT/d['response_file'];raw=read(response_path);r=unwrap(raw)
assert raw.get('isError') is not True and r['hostId']=='local'
thread=r['threadId'];host=r['hostId'];assert thread and thread!=OWNER
assert d['project_live_confirmed'] and d['project_id']
assert sha(ROOT/d['project_list_response_file'])==d['project_list_response_sha256']
assert not any(x.get('dispatch_token')==d['dispatch_token'] for x in chain.get('dispatch_history',[]))
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
d.update(created=True,created_at=stamp,thread_id=thread,host_id=host,response_sha256=sha(response_path),project_association_confirmed=True)
write(dispatch_path,d)
history=chain.setdefault('dispatch_history',[]);sequence=max((x.get('sequence',0) for x in history),default=0)+1
history.append({'sequence':sequence,'character':'WinterWarg','thread_id':thread,'host_id':host,'dispatch_token':d['dispatch_token'],
    'created':True,'project_association_confirmed':True,'project_id':d['project_id'],'handoff_file':d['handoff_file'],
    'successor_prompt_file':d['prompt_file'],'creation_response_file':d['response_file'],'created_at':stamp})
chain.update(state='active',parent_thread_id=OWNER,owner_thread_id=thread,owner_host_id=host,project_id=d['project_id'],successor_created=True,
    dispatch_ready_for=None,current_stage='not_started_owner_registered',last_stage_evidence=d['assessment_file'],resume_character='WinterWarg',
    resume_stage='Verify owner/token; inspect WinterWarg source anatomy and Wolf native contract; establish baseline',
    ownership_transfer_note='Fresh local WinterWarg child registered; child alone owns production/Unity; parent stops all workspace writes.',
    updated_at=stamp,activated_at=stamp,parent_writes_stopped_at=stamp)
write(H/'conversation_chain.json',chain)
print(json.dumps({'state':'active','thread_id':thread,'host_id':host,'character':'WinterWarg','sequence':sequence,
    'dispatch_token':d['dispatch_token'],'parent_mutations_stopped':True},ensure_ascii=False))
