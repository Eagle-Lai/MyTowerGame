"""Add missing death/pool-reuse Body reset only to Swine's copied Walk."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, shutil, sys
D=Path(__file__).resolve().parent; HERE=D.parent; ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
from mcp_call import Client
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def now(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
def unwrap(v): return v.get('structuredContent') or json.loads(v['content'][0]['text'])
chain=read(HERE/'conversation_chain.json')
assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert chain['current_character']=='Swine' and chain['dispatch_token']=='slugqueen-to-swine-fa6420308b3143349c4b9b602019510d'
out=D/'side_reuse_repair_r01'; assert not out.exists(), 'Inspect prior repair before retrying'
manifest=read(D/'installed_manifest.json')
assert all(sha(ROOT/x['path'])==x['after'].upper() for x in manifest['changes'])
baseline=read(D/'incremental_before_20261028.json')
protected=baseline['protected_six']
assert all(sha(ROOT/p)==s.upper() for p,s in protected.items() if p!='Assets/Prefabs/Enemy/Enemy_Swine.prefab')
c=Client(); project=c.identity()
errors=unwrap(c.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
state=c.resource('mcpforunity://editor/state')
probe=unwrap(c.tool('execute_code',dict(action='execute',code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};')))
assert probe['success'] and not any(v for k,v in probe['data']['result'].items() if k!='scene')
assert probe['data']['result']['scene']=='Assets/Scenes/Boot.unity' and errors['data']==[]
source_probe=unwrap(c.tool('execute_code',dict(action='execute',code='var clips=new[]{"Walk","Death"};return System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(clips,n=>{var clip=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>("Assets/_UIAssets/Monsters/_Common/Animations/Boar/"+n+".anim");return new{name=n,length=clip.length,loop=clip.isLooping,bodyRotation=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(System.Linq.Enumerable.Where(UnityEditor.AnimationUtility.GetCurveBindings(clip),b=>b.path=="Body"&&(b.propertyName.Contains("Euler")||b.propertyName.Contains("Rotation"))),b=>new{path=b.path,property=b.propertyName,values=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetEditorCurve(clip,b).keys,k=>k.value))}))};}));')))
assert source_probe['success']
source_values=source_probe['data']['result']
write(D/'source_death_reuse_probe_20261028.json',dict(project=project,result=source_probe,history=c.history))
if not source_values[1]['bodyRotation']:
    print(json.dumps(dict(body_rotation_reset_needed=False,source=source_values,no_production_changes=True),ensure_ascii=False))
    raise SystemExit(0)
assert source_values[0]['bodyRotation']==[] and source_values[1]['bodyRotation']
write(D/'source_death_reuse_contract_20261028.json',dict(project=project,result=source_probe,note='Source Boar Death rotates Body; source Walk does not reset Body rotation. Add reset only to Swine copied Walk before real Play. Original source unchanged.',history=c.history))
clip='Assets/_UIAssets/Monsters/Pigs/Swine/Directions/Animations/Walk_Directions.anim'
out.mkdir()
for p in ['installed_manifest.json','installed_verify.txt']: shutil.copy2(D/p,out/p)
shutil.copy2(ROOT/clip,out/'Walk_Directions_before.anim')
code='''var path="CLIP";var clip=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>(path);if(!clip)throw new System.Exception("Missing copied Walk");
System.Func<string> signature=()=>UnityEngine.JsonUtility.ToJson(clip)+"|"+string.Join(";",System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetCurveBindings(clip),b=>b.path+"|"+b.propertyName));
var original=UnityEditor.AnimationUtility.GetCurveBindings(clip);foreach(var b in original)if(b.path=="Body"&&(b.propertyName.Contains("Euler")||b.propertyName.Contains("Rotation")))throw new System.Exception("Existing Body rotation; inspect before changing");
var curves=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(original,b=>new{binding=b,curve=UnityEditor.AnimationUtility.GetEditorCurve(clip,b)}));
var pp=UnityEditor.AnimationUtility.GetObjectReferenceCurveBindings(clip);var ppBefore=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(pp,b=>UnityEditor.AnimationUtility.GetObjectReferenceCurve(clip,b)));
string events=string.Join(";",System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetAnimationEvents(clip),e=>UnityEngine.JsonUtility.ToJson(e)));
float length=clip.length;bool loop=clip.isLooping;
foreach(string axis in new[]{"x","y","z"})UnityEditor.AnimationUtility.SetEditorCurve(clip,UnityEditor.EditorCurveBinding.FloatCurve("Body",typeof(UnityEngine.Transform),"localEulerAnglesRaw."+axis),UnityEngine.AnimationCurve.Constant(0f,length,0f));
foreach(var x in curves){var after=UnityEditor.AnimationUtility.GetEditorCurve(clip,x.binding);if(UnityEngine.JsonUtility.ToJson(after)!=UnityEngine.JsonUtility.ToJson(x.curve))throw new System.Exception("Original float curve changed");}
for(int i=0;i<pp.Length;i++){var after=UnityEditor.AnimationUtility.GetObjectReferenceCurve(clip,pp[i]);if(after.Length!=ppBefore[i].Length)throw new System.Exception("PPtr count changed");for(int j=0;j<after.Length;j++)if(after[j].time!=ppBefore[i][j].time||after[j].value!=ppBefore[i][j].value)throw new System.Exception("PPtr changed");}
if(length!=clip.length||loop!=clip.isLooping||events!=string.Join(";",System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetAnimationEvents(clip),e=>UnityEngine.JsonUtility.ToJson(e))))throw new System.Exception("Timing/events changed");
UnityEditor.EditorUtility.SetDirty(clip);UnityEditor.AssetDatabase.SaveAssets();FTProject.EditorTools.EnemyDirectionSpec spec;FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("Swine",out spec);string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report);return new{pass=pass,report=report,length=clip.length,loop=clip.isLooping,originalFloatBindings=original.Length,afterFloatBindings=UnityEditor.AnimationUtility.GetCurveBindings(clip).Length,pptrBindings=pp.Length,originalCurvesEventsTimingPreserved=true};'''.replace('CLIP',clip)
result=unwrap(c.tool('execute_code',dict(action='execute',code=code)))
write(out/'repair_mcp.json',dict(observed_at=now(),project=project,state_before=state,probe_before=probe,errors=errors,result=result,protocol_history=c.history))
assert result['success'] and result['data']['result']['pass'],result
after=sha(ROOT/clip)
changed=[x for x in manifest['changes'] if sha(ROOT/x['path'])!=x['after'].upper()]
assert len(changed)==1 and changed[0]['path']==clip,changed
manifest.setdefault('repair_history',[]).append(dict(observed_at=now(),revision=out.name,path=clip,before=changed[0]['after'],after=after,reason='Reset otherwise unbound Body rotation during Walk/Run after death pool reuse',source_curves_events_timing_retained=True,original_manifest=out.name+'/installed_manifest.json',reapply_if_full_rig_build='Full Build regenerates copied clips; preserve this additive reset'))
changed[0]['after']=after;manifest['verification']=result;write(D/'installed_manifest.json',manifest)
(D/'installed_verify.txt').write_text(result['data']['result']['report'],encoding='utf-8')
write(out/'repair.json',dict(observed_at=now(),path=clip,before=sha(out/'Walk_Directions_before.anim'),after=after,added_bindings=['Body/localEulerAnglesRaw.'+a for a in 'xyz'],constant_value=0,preemptive_from_source_Boar_Death_Body_rotation=True,new_runtime_revisions=['runtime_r01','runtime_updeath_r01'],no_shared_code_or_source_changes=True,verify=True,preservation_checks=result['data']['result']))
write(D/'preplay_version_binding_20261028.json',dict(observed_at=now(),installed_manifest_sha256=sha(D/'installed_manifest.json'),installed_files={x['path']:sha(ROOT/x['path']) for x in manifest['changes']},repair_sha256=sha(out/'repair.json'),selection=read(D/'art_selection.json')))
chain.update(current_stage='Swine_installed_own_Walk_reset_pending_two_Play_rounds',last_stage_evidence=(out/'repair.json').relative_to(ROOT).as_posix(),updated_at=now());write(HERE/'conversation_chain.json',chain)
print(json.dumps(dict(repaired=clip,verify=True,original_bindings=result['data']['result']['originalFloatBindings'],after_bindings=result['data']['result']['afterFloatBindings']),ensure_ascii=False))
