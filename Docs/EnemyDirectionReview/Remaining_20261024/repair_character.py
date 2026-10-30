"""Install one explicit art repair, preserving prior manifests, assets and runtime evidence."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib,json,shutil,sys
from mcp_call import Client

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
name,revision=sys.argv[1:3]
if not revision.replace('_','').isalnum():raise ValueError('Simple unique repair revision required')
d=HERE/name
t=next(t for t in json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))['targets'] if t['name']==name)
out=d/revision
if out.exists():raise ValueError('Repair evidence already exists; inspect before retrying')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
baseline=json.loads((HERE/'production_fingerprints_before.json').read_text(encoding='utf-8'))
for p in [t['source'],t['source']+'.meta',t['atlas'],t['atlas']+'.meta',t['battle']+'.meta']:
    if sha(ROOT/p)!=baseline[p]:raise ValueError('Original source/GUID drift: '+p)
latest=d/'installed_manifest.json'
repairs=sorted(d.glob('repair_*/manifest.json'))
if repairs:latest=repairs[-1]
previous=json.loads(latest.read_text(encoding='utf-8'))
recovered=[]
incomplete=[p for p in d.glob('repair_*') if p.is_dir() and (p/'previous_manifest.json').is_file() and not (p/'manifest.json').exists()]
for c in previous['changes']:
    current=sha(ROOT/c['path'])
    if current==c['after']:continue
    path=Path(c['path'])
    staged=d/'staged_art'/path.name
    allowed={name+'_Directions'+suffix for suffix in ['.png','.sprites.json','.layout.json']}
    evidence=next((p for p in incomplete if sha(p/'before'/path)==c['after']),None)
    if path.name not in allowed or current!=sha(staged) or evidence is None:
        raise ValueError('Installed asset drift: '+c['path'])
    recovered.append({'path':c['path'],'previous':c['after'],'current':current,'interrupted_repair':evidence.name,'reason':'Exact staged input copied by interrupted repair; protected backup matches prior installed manifest.'})
client=Client();identity=client.identity()
def unwrap(v):
    v=v.get('structuredContent') or json.loads(v['content'][0]['text'])
    if isinstance(v.get('result'),dict) and 'success' in v['result']:
        v=v['result']
    if not v.get('success'):raise ValueError(str(v))
    return v
state=unwrap(client.tool('execute_code',{'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,updating=UnityEditor.EditorApplication.isUpdating,failed=UnityEditor.EditorUtility.scriptCompilationFailed,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty)};' }))['data']['result']
if any(state.values()):raise ValueError('Editor unavailable: '+str(state))
art=ROOT/t['art_dir']
inputs=[d/'staged_art'/(name+'_Directions'+suffix) for suffix in ['.png','.sprites.json','.layout.json']]
if not all(p.is_file() for p in inputs):raise ValueError('Missing staged inputs')
paths=[ROOT/t['battle'],ROOT/(t['battle']+'.meta')]+[p for p in art.rglob('*') if p.is_file()]
before={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
out.mkdir()
for p in paths:
    dest=out/'before'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
shutil.copy2(latest,out/'previous_manifest.json')
for p in inputs:shutil.copy2(p,art/p.name)
unwrap(client.tool('refresh_unity',{'mode':'force','scope':'assets','compile':'none','wait_for_ready':True}))
client.identity()
result=unwrap(client.tool('execute_code',{'action':'execute','code':'FTProject.EditorTools.EnemyDirectionalRigBuilder.Build('+json.dumps(name)+');FTProject.EditorTools.EnemyDirectionSpec s;FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec('+json.dumps(name)+',out s);string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(s,out report);return new {pass=pass,report=report};'}))
after={p.relative_to(ROOT).as_posix():sha(p) for p in [ROOT/t['battle'],ROOT/(t['battle']+'.meta')]+list(art.rglob('*')) if p.is_file()}
changes=[{'path':p,'before':before.get(p),'after':s} for p,s in after.items()]
manifest={'name':name,'revision':revision,'at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'project':identity,'previous_manifest':latest.relative_to(d).as_posix(),'changes':changes,'verification':result,'protocol_history':client.history}
manifest['recovered_interrupted_inputs']=recovered
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'verify.txt').write_text(result['data']['result']['report'],encoding='utf-8')
if not result['data']['result']['pass']:raise ValueError('Repair Verify failed; preserve evidence')
print(json.dumps({'name':name,'revision':revision,'verify':True,'assets':len(changes)},ensure_ascii=False))
