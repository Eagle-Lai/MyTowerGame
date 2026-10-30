from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys,shutil
D=Path(__file__).resolve().parent;H=D.parent;ROOT=H.parents[2];R=D/'repair_proportions_r02'
sys.path.insert(0,str(H))
from mcp_call import Client
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
c=read(H/'conversation_chain.json');assert c['state']=='active' and c['current_character']=='Warg' and c['owner_thread_id']=='01a1830c-598a-7473-8ee1-01bccdd1f9be'
assert not (R/'manifest.json').exists() and not (R/'before').exists()
old=read(D/'installed_manifest.json')
for row in old['changes']:assert sha(ROOT/row['path'])==row['after'],row['path']
t=read(D/'incremental_before_20261028.json')['target'];art=ROOT/t['art_dir'];battle=ROOT/t['battle']
client=Client();project=client.identity()
def unwrap(v):
    v=v.get('structuredContent') or json.loads(v['content'][0]['text']);assert v['success'],v
    return v['data']['result']
probe=unwrap(client.tool('execute_code',{'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,updating=UnityEditor.EditorApplication.isUpdating,failed=UnityEditor.EditorUtility.scriptCompilationFailed,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,manual=FTProject.GameClock.IsManualSimulation};'}))
assert not any(probe.values()),probe
paths=[battle,Path(str(battle)+'.meta')]+[p for p in art.rglob('*') if p.is_file()]
before={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
for p in paths:
    q=R/'before'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
shutil.copy2(D/'staged_art/Warg_Directions.layout.json',art/'Warg_Directions.layout.json')
client.tool('refresh_unity',{'mode':'force','scope':'assets','compile':'none','wait_for_ready':True});client.identity()
result=unwrap(client.tool('execute_code',{'action':'execute','code':'FTProject.EditorTools.EnemyDirectionalRigBuilder.Build("Warg"); FTProject.EditorTools.EnemyDirectionSpec spec; FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("Warg",out spec); string report; bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report);return new {pass=pass,report=report};'}))
assert result['pass'],result
after={p.relative_to(ROOT).as_posix():sha(p) for p in [battle,Path(str(battle)+'.meta')]+[p for p in art.rglob('*') if p.is_file()]}
report={'revision':'repair_proportions_r02','name':'Warg','observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'project':project,'verification':result,'changes':[{'path':p,'before':before.get(p),'after':s} for p,s in after.items() if s!=before.get(p)],'final_files':after,'protocol_history':client.history}
(R/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(R/'verify.txt').write_text(result['report'],encoding='utf-8')
print(json.dumps({'name':'Warg','revision':'R02','verify':True,'changed_paths':len(report['changes']),'final_paths':len(after)}))
