from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,subprocess,sys
D=Path(__file__).resolve().parent;H=D.parent;R=H.parents[2]
sys.path.insert(0,str(H))
from mcp_call import Client
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(p,v):
    assert not p.exists(),str(p)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
c=read(H/'conversation_chain.json')
assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='Sheep' and c['dispatch_token']=='scarabmounted-to-sheep-fd7d7a5afb264ca7a1691363ab276f5f'
t=next(x for x in read(H/'local_baseline.json')['targets'] if x['name']=='Sheep')
base=read(H/'production_fingerprints_before.json')
six=[t['battle'],t['battle']+'.meta',t['source'],t['source']+'.meta',t['atlas'],t['atlas']+'.meta']
assert all(sha(R/p)==base[p] for p in six),'Target/source baseline drift'
assert all(sha(R/p)==sha(D/'reference'/Path(p).name) for p in six),'Reference snapshot drift'
assert not (R/t['art_dir']).exists() and not (D/'anatomy_plan.json').exists()
files={p.relative_to(R).as_posix():sha(p) for f in ['Assets','Packages','ProjectSettings','Luban'] for p in (R/f).rglob('*') if p.is_file()}
git={}
for name,args in [('status',['status','--short','--untracked-files=normal']),('diff_stat',['diff','--stat']),('target_diff',['diff','--',*six]),('head',['rev-parse','HEAD'])]:
    v=subprocess.run(['git',*args],cwd=R,capture_output=True,encoding='utf-8',errors='replace',check=True).stdout
    (D/('git_'+name+'_before_20261028.txt')).write_text(v,encoding='utf-8');git[name]=dict(lines=len(v.splitlines()),sha256=sha(D/('git_'+name+'_before_20261028.txt')))
write(D/'incremental_before_20261028.json',dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),project=str(R),owner=c['owner_thread_id'],dispatch_token=c['dispatch_token'],files=files,protected_six={p:files[p] for p in six},target=t,git=git,source_note='Original six sprite renderers, four hooves and no bound Tail sprite/node. No horns. Cream wool with ochre patches, pale gold face, floppy ears, three original expressions. Root AGENTS stale D:/FreedomTower_1 is retained; actual task E:/MyTowerGame.'))
client=Client();identity=client.identity()
errors=client.tool('read_console',dict(action='get',types=['error'],count='50',format='json'))
state=client.resource('mcpforunity://editor/state')
probe=client.tool('execute_code',dict(action='execute',code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};'))
write(D/'unity_before_20261028.json',dict(project=identity,errors=errors,state=state,probe=probe,history=client.history))
value=probe.get('structuredContent') or json.loads(probe['content'][0]['text'])
p=value['data']['result'];assert all(not v for k,v in p.items() if k!='scene'),p
print(json.dumps(dict(files=len(files),target=t,git=git,identity=identity,probe=p,errors=errors),ensure_ascii=False))
