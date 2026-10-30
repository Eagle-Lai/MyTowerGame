"""Recorded repair: retain the original unassigned horizontal head binding."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib,json,shutil,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mcp_call import Client

d=Path(__file__).resolve().parent
root=d.parents[3]
previous=json.loads((d/'installed_manifest.json').read_text(encoding='utf-8'))
out=d/'repair_01'
if out.exists():raise ValueError('Existing repair evidence must not be replaced')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
for entry in previous['changes']:
    if sha(root/entry['path'])!=entry['after']:raise ValueError('Installed asset drift: '+entry['path'])
client=Client();identity=client.identity()
def unwrap(r):
    v=r.get('structuredContent') or json.loads(r['content'][0]['text'])
    if 'result' in v and 'data' not in v:v=v['result']
    if not v.get('success'):raise ValueError(str(v))
    return v
state=unwrap(client.tool('execute_code',{'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,updating=UnityEditor.EditorApplication.isUpdating,failed=UnityEditor.EditorUtility.scriptCompilationFailed,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty};'}))['data']['result']
if any(state.values()):raise ValueError(str(state))
paths=[root/'Assets/Prefabs/Enemy/Enemy_EvilEye.prefab',root/'Assets/Prefabs/Enemy/Enemy_EvilEye.prefab.meta']+list((root/'Assets/_UIAssets/Monsters/Bats/EvilEye/Directions').rglob('*'))
before={p.relative_to(root).as_posix():sha(p) for p in paths if p.is_file()}
out.mkdir()
for path in before:
    dest=out/'before'/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/path,dest)
shutil.copy2(d/'installed_manifest.json',out/'previous_manifest.json')
code='var path="Assets/Prefabs/Enemy/Enemy_EvilEye.prefab";var clone=UnityEditor.PrefabUtility.LoadPrefabContents(path);try{var receiver=clone.GetComponent<FTProject.MonsterAnimEventReceiver>();if(receiver.HeadRenderer==null||receiver.HeadRenderer.name!="Body")throw new System.Exception("Unexpected receiver binding");receiver.HeadRenderer=null;UnityEditor.PrefabUtility.SaveAsPrefabAsset(clone,path);}finally{UnityEditor.PrefabUtility.UnloadPrefabContents(clone);}FTProject.EditorTools.EnemyDirectionalRigBuilder.Build("EvilEye");FTProject.EditorTools.EnemyDirectionSpec spec;FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("EvilEye",out spec);string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report);var prefab=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>(path);return new {pass=pass&&prefab.GetComponent<FTProject.MonsterAnimEventReceiver>().HeadRenderer==null,report=report,originalBindingRestored=prefab.GetComponent<FTProject.MonsterAnimEventReceiver>().HeadRenderer==null};'
result=unwrap(client.tool('execute_code',{'action':'execute','code':code}))
changes=[{'path':p,'before':s,'after':sha(root/p)} for p,s in before.items()]
manifest={'name':'EvilEye','revision':'repair_01','at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'project':identity,'previous_manifest':'installed_manifest.json','changes':changes,'verification':result,'protocol_history':client.history,'reason':'Restore original null HeadRenderer and preserve it through builder initialization; runtime resolves the original orb once.'}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
(out/'verify.txt').write_text(result['data']['result']['report'],encoding='utf-8')
if not result['data']['result']['pass']:raise ValueError('Repair verify failed')
print(json.dumps({'name':'EvilEye','repair':'repair_01','verified':True,'originalBindingRestored':True}))
