from session_current import *
import shutil
owner();assert not (HERE/'head_binding_repair_r02_20261029.json').exists()
c=Client();project=c.identity()
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json','include_stacktrace':True})
state=c.resource('mcpforunity://editor/state');p=probe(c);idle(p)
assert state['data']['advice']['ready_for_tools'] and not state['data']['tests']['is_running']
pre=read(HERE/'preplay_version_binding_20261029.json');files=snapshot()
assert bound(files)==pre['production_fingerprints']
assert sha(HERE/'installed_manifest.json')==pre['manifest_sha256']
backup=HERE/'before_head_binding_repair_r02';backup.mkdir()
shutil.copy2(ROOT/target()['battle'],backup/'Enemy_WolfMounfed.prefab')
code='''var atlas="Assets/_UIAssets/Monsters/Mounts/WolfMount/WolfMounted.png";
var path="Assets/Prefabs/Enemy/Enemy_WolfMounfed.prefab";
var all=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.OfType<UnityEngine.Sprite>(UnityEditor.AssetDatabase.LoadAllAssetsAtPath(atlas)));
var names=new[]{"HeadNormal","HeadAngry","HeadDead"};
var heads=names.Select(n=>all.Single(s=>s.name==n)).ToArray();
var refs=heads.Select(s=>{string guid;long id;if(!UnityEditor.AssetDatabase.TryGetGUIDAndLocalFileIdentifier(s,out guid,out id))throw new System.Exception("No Sprite ID");return new {name=s.name,guid=guid,fileID=id,path=UnityEditor.AssetDatabase.GetAssetPath(s)};}).ToArray();
var root=UnityEditor.PrefabUtility.LoadPrefabContents(path);
try{var receiver=root.GetComponent<FTProject.MonsterAnimEventReceiver>();
if(!receiver||!receiver.HeadRenderer||receiver.HeadSprites==null||receiver.HeadSprites.Length!=0)throw new System.Exception("Unexpected receiver contract; no repair applied");
var head=receiver.HeadRenderer;if(head.sprite!=heads[0])throw new System.Exception("Normal original head mismatch");
receiver.HeadSprites=heads;UnityEditor.PrefabUtility.SaveAsPrefabAsset(root,path);
return Newtonsoft.Json.JsonConvert.SerializeObject(new {repaired=true,beforeCount=0,afterCount=heads.Length,headPath=UnityEditor.AnimationUtility.CalculateTransformPath(head.transform,root.transform),bindings=refs});}
finally{UnityEditor.PrefabUtility.UnloadPrefabContents(root);}'''
result=unwrap(c.tool('execute_code',{'action':'execute','code':code}));assert result['repaired'] and result['afterCount']==3
c.identity();idle(probe(c))
verify=unwrap(c.tool('execute_code',{'action':'execute','code':'FTProject.EditorTools.EnemyDirectionSpec spec; FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("WolfMounfed",out spec);string text;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out text);return new {pass=pass,report=text};'}))
assert verify['pass'];(HERE/'installed_verify_repair_r02.txt').write_text(verify['report']+'\n',encoding='utf-8')
after=snapshot();changed=[x for x in sorted(set(files)|set(after)) if files.get(x)!=after.get(x)]
assert changed==[target()['battle']],changed
save(HERE/'head_binding_repair_r02_20261029.json',{'observed_at':now(),'project':project,'reason':'Original battle prefab serializes HeadSprites: [] despite own atlas containing normal/angry/dead sprites. Real Play r01 StaticChecks indexed empty original receiver array; that also prevented native side expression events. Repair only this prefab to reference its three original atlas sprites. No CSharp/source prefab/atlas/meta or animation modification.',
 'failed_revision':'runtime_r01','failure_scene_sha256':sha(HERE/'runtime_r01_failure_scene_20261029.json'),
 'result':result,'before_prefab_sha256':sha(backup/'Enemy_WolfMounfed.prefab'),'after_prefab_sha256':sha(ROOT/target()['battle']),
 'original_installed_manifest_sha256':sha(HERE/'installed_manifest.json'),'repair_verify_sha256':sha(HERE/'installed_verify_repair_r02.txt'),
 'changes':[{'path':x,'before':files.get(x),'after':after.get(x)} for x in changed],
 'historical_errors':errors,'state':state,'probe':p,'verify':verify,'protocol_history':c.history})
print(json.dumps({'repaired':result,'verify':verify['pass'],'changed_paths':changed},ensure_ascii=False))
