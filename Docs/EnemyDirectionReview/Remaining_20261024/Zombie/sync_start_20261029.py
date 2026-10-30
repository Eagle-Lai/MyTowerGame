from pathlib import Path
from datetime import datetime, timezone, timedelta
import sys, os, json, hashlib, subprocess

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(RUN))
from mcp_call import Client

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()

def save(name, value):
    p = HERE / name
    if p.exists():
        raise FileExistsError(p)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

chain = json.loads((RUN/'conversation_chain.json').read_text(encoding='utf-8'))
assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert chain['current_character']=='Zombie'
assert chain['dispatch_token']=='wolfmounfed-to-zombie-20261029_230534-9abf79b2-282d-4c43-bc85-2b10f14a62f1'
progress=json.loads((RUN/'progress.json').read_text(encoding='utf-8'))
baseline=json.loads((RUN/'local_baseline.json').read_text(encoding='utf-8'))
original_hashes=json.loads((RUN/'production_fingerprints_before.json').read_text(encoding='utf-8'))
approval=json.loads((RUN.parent/'Batch01_10/user_approval_20261023.json').read_text(encoding='utf-8'))
gifs=json.loads((RUN.parent/'AllGIF/manifest.json').read_text(encoding='utf-8'))
t=next(x for x in baseline['targets'] if x['name']=='Zombie')
protected={p:digest(ROOT/p) for p in [t[k]+suffix for k in ['battle','source','atlas'] for suffix in ['', '.meta']]}
assert all(original_hashes[p]==h for p,h in protected.items())
assert not any((HERE/p).exists() for p in ['anatomy_plan.json','generation','staged_art','installed_manifest.json','runtime_summary.json'])
files={p.relative_to(ROOT).as_posix():digest(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in sorted((ROOT/folder).rglob('*')) if p.is_file()}
save('production_paths_before_20261029.json',files)
for args,name in [(['git','status','--porcelain=v1','--untracked-files=all'],'git_status_before_20261029.txt'),(['git','diff','--stat'],'git_diff_stat_before_20261029.txt'),(['git','diff','--',t['battle'],t['source'],t['atlas']+'.meta'],'target_diff_before_20261029.txt')]:
    result=subprocess.run(args,cwd=ROOT,capture_output=True,check=True)
    (HERE/name).write_bytes(result.stdout)
summary={'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'owner_thread_id':chain['owner_thread_id'],'dispatch_token':chain['dispatch_token'],'chain_history_count':len(chain['dispatch_history']),'completed_count':progress['completed_count'],'authorized_count':progress['authorized_count'],'progress_current':progress.get('current'),'remaining':[x for x in progress['items'] if x['status'] not in ['completed_pending_user_art_review','user_approved']],'target':t,'protected_six':protected,'production_paths':len(files),'original_baseline_target_count':len(baseline['targets']),'original_fingerprint_count':len(original_hashes),'approval_keys':list(approval),'gif_count':gifs['count'],'read_full_json_sha256':{str(p.relative_to(ROOT)):digest(p) for p in [RUN/'progress.json',RUN/'conversation_chain.json',RUN/'local_baseline.json',RUN/'production_fingerprints_before.json',RUN.parent/'Batch01_10/user_approval_20261023.json',RUN.parent/'AllGIF/manifest.json']}}
save('sync_start_20261029.json',summary)
client=Client()
project=client.identity()
errors=client.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
cs=client.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json','filter_text':'error CS'})
state=client.resource('mcpforunity://editor/state')
from session_current import probe,idle
p=probe(client);idle(p)
save('unity_start_20261029.json',{'project':project,'errors':errors,'errorCS':cs,'state':state,'probe':p,'protocol_history':client.history})
print(json.dumps({'project':project,'errors':errors,'errorCS':cs,'state':state,'probe':p,'production_paths':len(files),'protected_six_match':True,'remaining':[{'index':x['index'],'name':x['name'],'status':x['status']} for x in summary['remaining']],'gif_count':gifs['count']},ensure_ascii=False))
