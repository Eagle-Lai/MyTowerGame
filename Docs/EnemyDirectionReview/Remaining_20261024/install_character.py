"""Install one reviewed staged character; refuse baseline drift and record exact changes."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,sys,hashlib,shutil
from mcp_call import Client
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
name=sys.argv[1]
t=next(t for t in json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))['targets'] if t['name']==name)
baseline=json.loads((HERE/'production_fingerprints_before.json').read_text(encoding='utf-8'))
directory=HERE/name
if (directory/'installed_manifest.json').exists(): raise SystemExit('Already installed; use a separately recorded repair revision.')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
protected=[t['battle'],t['battle']+'.meta',t['source'],t['source']+'.meta',t['atlas'],t['atlas']+'.meta']
for path in protected:
    if sha(ROOT/path)!=baseline[path]: raise ValueError('Concurrent target/source drift: '+path)
client=Client();identity=client.identity()
def unwrap(value):
    v=value.get('structuredContent')
    if v is None:v=json.loads(value['content'][0]['text'])
    if 'result' in v and 'data' not in v:v=v['result']
    if not v.get('success',False):raise RuntimeError(json.dumps(v,ensure_ascii=False))
    return v
probe=unwrap(client.tool('execute_code',{'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty};'}))['data']['result']
if any(probe.values()):raise ValueError('Editor window unavailable: '+str(probe))
before_paths=[ROOT/t['battle'],ROOT/(t['battle']+'.meta')]
art=ROOT/t['art_dir'];before_paths+=list(art.rglob('*')) if art.exists() else []
before={p.relative_to(ROOT).as_posix():sha(p) for p in before_paths if p.is_file()}
for path in before:
    dest=directory/'before'/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,dest)
art.mkdir(parents=True,exist_ok=True)
for suffix in ['.png','.sprites.json','.layout.json']:
    source=directory/'staged_art'/(name+'_Directions'+suffix)
    if not source.is_file():raise ValueError('Staged input missing: '+str(source))
    shutil.copy2(source,art/source.name)
unwrap(client.tool('refresh_unity',{'mode':'force','scope':'assets','compile':'none','wait_for_ready':True}))
client.identity()
report_path=(directory/'installed_verify.txt').relative_to(ROOT).as_posix()
code='FTProject.EditorTools.EnemyDirectionalRigBuilder.Build('+json.dumps(name)+'); FTProject.EditorTools.EnemyDirectionSpec spec; FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec('+json.dumps(name)+',out spec); string report; bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report); System.IO.File.WriteAllText('+json.dumps(report_path)+',report); return new {pass=pass,report=report};'
result=unwrap(client.tool('execute_code',{'action':'execute','code':code}))
after_paths=[ROOT/t['battle'],ROOT/(t['battle']+'.meta')]+list(art.rglob('*'))
after={p.relative_to(ROOT).as_posix():sha(p) for p in after_paths if p.is_file()}
changes=[{'path':p,'before':before.get(p),'after':s} for p,s in after.items() if s!=before.get(p)]
manifest={'name':name,'installed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'project':identity,'verification':result,'changes':changes,'protocol_history':client.history}
(directory/'installed_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if not result['data']['result']['pass']:raise SystemExit('Installed verification failed; preserve evidence and repair before runtime review.')
print(json.dumps({'name':name,'installed':True,'verify':True,'changes':len(changes)},ensure_ascii=False))
