from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,sys,hashlib,shutil
base=Path('Docs/EnemyDirectionReview/Remaining_20261024').resolve();root=base.parents[2];d=base/'MeatBug'
sys.path.insert(0,str(base));from mcp_call import Client
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
original=json.loads((d/'installed_manifest.json').read_text(encoding='utf-8'))
for x in original['changes']:
 assert sha(root/x['path'])==x['after'],'Installed fingerprint drift: '+x['path']
b=json.loads((d/'session_baseline_20261025.json').read_text(encoding='utf-8'))
for p,h in b['fingerprints'].items():
 if p!='Assets/Prefabs/Enemy/Enemy_MeatBug.prefab':assert sha(root/p)==h,p
out=d/'repair_02';assert not out.exists()
c=Client();identity=c.identity()
def unwrap(r):
 v=r.get('structuredContent') or json.loads(r['content'][0]['text']);assert v.get('success'),v
 return v['data']['result']
state=unwrap(c.tool('execute_code',{'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,recorder=FTProject.EditorTools.BalanceVideoRecorder.Running,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty};'}))
assert not any(state.values()),state
out.mkdir();shutil.copy2(d/'installed_manifest.json',out/'previous_manifest.json')
paths=[root/x['path'] for x in original['changes']]
before={p.relative_to(root).as_posix():sha(p) for p in paths}
for p in paths:
 q=out/'before'/p.relative_to(root);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
code='var path="Assets/Prefabs/Enemy/Enemy_MeatBug.prefab";var root=UnityEditor.PrefabUtility.LoadPrefabContents(path);try {var receiver=root.GetComponent<FTProject.MonsterAnimEventReceiver>();var body=root.transform.Find("Body").GetComponent<UnityEngine.SpriteRenderer>();if(!receiver||!body||!body.sprite)throw new System.InvalidOperationException("Original MeatBug Body unavailable");if(receiver.HeadRenderer)throw new System.InvalidOperationException("Unexpected existing head binding");receiver.HeadRenderer=body;receiver.HeadSprites=new UnityEngine.Sprite[]{body.sprite,body.sprite,body.sprite};UnityEditor.EditorUtility.SetDirty(receiver);UnityEditor.PrefabUtility.SaveAsPrefabAsset(root,path);}finally{UnityEditor.PrefabUtility.UnloadPrefabContents(root);}UnityEditor.AssetDatabase.SaveAssets();FTProject.EditorTools.EnemyDirectionSpec spec;FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("MeatBug",out spec);string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report);return new {pass=pass,report=report};'
r=unwrap(c.tool('execute_code',{'action':'execute','code':code}));assert r['pass'],r
changes=[{'path':p.relative_to(root).as_posix(),'before':before[p.relative_to(root).as_posix()],'after':sha(p)} for p in paths]
reason='Runtime r01 exposed pre-existing null HeadRenderer. MeatBug original face is integrated into its Body sprite. Bind receiver to that original renderer and use its unchanged Body sprite for all side states; dedicated Up/Down heads keep their real expression states. No shared code, original sprite, transform or animation modified.'
(out/'manifest.json').write_text(json.dumps({'name':'MeatBug','revision':'repair_02','at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'project':identity,'reason':reason,'changes':changes,'verification':r,'protocol_history':c.history},ensure_ascii=False,indent=2),encoding='utf-8')
(out/'verify.txt').write_text(r['report'],encoding='utf-8')
print(json.dumps({'repair':'repair_02','pass':r['pass'],'changed':[x['path'] for x in changes if x['before']!=x['after']],'reason':reason}))