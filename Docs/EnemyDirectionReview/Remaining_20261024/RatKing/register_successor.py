"""Exactly-once ownership transfer after the successful desktop create response."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,sys,os,uuid
D=Path(__file__).resolve().parent;H=D.parent
thread,host=sys.argv[1:3];uuid.UUID(thread);assert host=='local'
c=json.loads((H/'conversation_chain.json').read_text(encoding='utf-8'))
assert c['state']=='handoff_ready' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='RedScorpion'
assert c['parent_thread_id']==os.environ['CODEX_THREAD_ID'] and c['dispatch_token'].startswith('ratking-to-redscorpion-')
assert not any(x['thread_id']==thread or x['character']=='RedScorpion' and x['dispatch_token']==c['dispatch_token'] for x in c['dispatch_history'])
now=datetime.now(timezone(timedelta(hours=8))).isoformat()
c['dispatch_history'].append(dict(sequence=len(c['dispatch_history'])+1,character='RedScorpion',thread_id=thread,host_id=host,dispatch_token=c['dispatch_token'],created=True,project_association_confirmed=True,handoff_file=c['last_handoff_file'],created_at=now))
c.update(state='active',owner_thread_id=thread,owner_host_id=host,activated_at=now)
(H/'conversation_chain.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(state=c['state'],owner=thread,current_character=c['current_character'],token=c['dispatch_token']),ensure_ascii=False))
