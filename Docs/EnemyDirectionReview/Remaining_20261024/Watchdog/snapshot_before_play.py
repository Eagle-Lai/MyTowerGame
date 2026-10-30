from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os
D=Path(__file__).resolve().parent; H=D.parent; ROOT=H.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
chain=read(H/'conversation_chain.json')
assert chain['state']=='active' and chain['current_character']=='Watchdog'
assert chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']=='01a18379-8413-7bb3-bbc3-e0e5b2544d59'
assert chain['dispatch_token']=='wasp-to-watchdog-20261029_010456-a6f96d67-324e-4b30-9ff0-555b83354188'
assert not (D/'production_before_play_20261029.json').exists()
assert not (D/'runtime_r01').exists() and not (D/'runtime_updeath_r01').exists()
b=read(D/'incremental_before_20261029.json'); t=b['target']; art=ROOT/t['art_dir']
files=[ROOT/t['battle'],ROOT/(t['battle']+'.meta'),ROOT/(t['art_dir']+'.meta')]+[p for p in art.rglob('*') if p.is_file()]
snapshot={p.relative_to(ROOT).as_posix():sha(p) for p in files}
m=read(D/'installed_manifest.json')
assert m['verification']['data']['result']['pass']
assert all(snapshot[c['path']]==c['after'] for c in m['changes'])
out={'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'revision':'art_r04',
     'manifest':'installed_manifest.json','manifest_sha256':sha(D/'installed_manifest.json'),
     'final_files':snapshot,'verify_pass':True,'basis':'Captured after install, before either authorized Play run.'}
(D/'production_before_play_20261029.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'revision':'art_r04','production_files':len(snapshot),'installed_changes':len(m['changes'])}))
