"""Wasp-only sprite cadence revision; preserves every other installed curve/event."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, shutil, sys, time
D=Path(__file__).resolve().parent;H=D.parent;ROOT=H.parents[2]
sys.path.insert(0,str(H))
from mcp_call import Client
OWNER='01a1833c-f96c-74a1-b7f2-2281f6ab321d'
TOKEN='warg-to-wasp-20261028_235853-1e651dcf-1586-4ebc-9926-3b8be7348e7d'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def data(r):return r.get('structuredContent') or json.loads(r['content'][0]['text'])
def owned():
    chain=read(H/'conversation_chain.json')
    assert chain['state']=='active' and chain['owner_thread_id']==OWNER and chain['dispatch_token']==TOKEN and chain['current_character']=='Wasp'
    assert os.environ.get('CODEX_THREAD_ID')==OWNER
owned()
V=D/'flap_cadence_r03';assert not V.exists()
base=read(D/'incremental_before_20261029.json');target=base['target'];art=target['art_dir'];battle=target['battle']
assert all(sha(ROOT/r['path'])==r['after'] for r in read(D/'installed_manifest.json')['changes'])
paths=[ROOT/battle,ROOT/(battle+'.meta'),ROOT/(art+'.meta')]+sorted((ROOT/art).rglob('*'))
paths=[p for p in paths if p.is_file()]
c=Client();project=c.identity()
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
assert data(errors)['data']==[],data(errors)
state=c.resource('mcpforunity://editor/state')
live=data(c.tool('execute_code',{'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path,sceneCount=UnityEngine.SceneManagement.SceneManager.sceneCount,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation};'}))['data']['result']
assert live['scene']=='Assets/Scenes/Boot.unity' and live['sceneCount']==1
assert all(not live[k] for k in ['playing','compiling','failed','updating','dirty','balance','recording','review','manual']),live
assert not state['data']['compilation']['is_domain_reload_pending'],state
V.mkdir()
before={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
for p in paths:
    out=V/'before'/p.relative_to(ROOT);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
write(V/'before.json',{'project':project,'files':before,'live':live,'state':state,'errors':errors})
code=r'''
string root="Assets/_UIAssets/Monsters/Insects/Wasp/Directions";
var sprites=System.Linq.Enumerable.ToDictionary(System.Linq.Enumerable.OfType<UnityEngine.Sprite>(UnityEditor.AssetDatabase.LoadAllAssetsAtPath(root+"/Wasp_Directions.png")),s=>s.name);
System.Func<UnityEngine.AnimationClip,string> signature=clip=>{
 var text=new System.Text.StringBuilder();
 text.Append(clip.length.ToString("R")).Append('|').Append(clip.frameRate.ToString("R")).Append('|').Append(UnityEngine.JsonUtility.ToJson(UnityEditor.AnimationUtility.GetAnimationClipSettings(clip)));
 foreach(var b in UnityEditor.AnimationUtility.GetCurveBindings(clip)){
  text.Append(b.path).Append('|').Append(b.type.FullName).Append('|').Append(b.propertyName);
  var curve=UnityEditor.AnimationUtility.GetEditorCurve(clip,b);text.Append(curve.preWrapMode).Append(curve.postWrapMode);
  foreach(var k in curve.keys)text.AppendFormat(System.Globalization.CultureInfo.InvariantCulture,"{0:R},{1:R},{2:R},{3:R},{4:R},{5:R},{6};",k.time,k.value,k.inTangent,k.outTangent,k.inWeight,k.outWeight,k.weightedMode);
 }
 foreach(var b in UnityEditor.AnimationUtility.GetObjectReferenceCurveBindings(clip)){
  if(b.path.StartsWith("DirectionVisual/") && (b.path.EndsWith("/WingL/Sprite") || b.path.EndsWith("/WingR/Sprite")) && b.propertyName=="m_Sprite")continue;
  text.Append(b.path).Append('|').Append(b.type.FullName).Append('|').Append(b.propertyName);
  foreach(var k in UnityEditor.AnimationUtility.GetObjectReferenceCurve(clip,b))text.Append(k.time.ToString("R")).Append(':').Append(k.value==null?0:k.value.GetInstanceID()).Append(';');
 }
 foreach(var e in UnityEditor.AnimationUtility.GetAnimationEvents(clip))text.Append(e.time.ToString("R")).Append('|').Append(e.functionName).Append('|').Append(e.stringParameter).Append('|').Append(e.intParameter).Append('|').Append(e.floatParameter.ToString("R")).Append('|').Append(e.objectReferenceParameter==null?0:e.objectReferenceParameter.GetInstanceID()).Append('|').Append(e.messageOptions);
 return text.ToString();
};
var clips=new System.Collections.Generic.List<object>();
foreach(string action in new[]{"Ready","Walk","Attack","Death"}){
 var clip=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>(root+"/Animations/"+action+"_Directions.anim");
 if(clip==null || UnityEngine.Mathf.Abs(clip.length-.5f)>.0001f)throw new System.Exception("Wasp clip contract mismatch "+action);
 string prior=signature(clip);float duration=clip.length;
 foreach(string direction in new[]{"Up","Down"})foreach(string wing in new[]{"WingL","WingR"}){
  var binding=UnityEditor.EditorCurveBinding.PPtrCurve("DirectionVisual/"+direction+"/Motion/"+wing+"/Sprite",typeof(UnityEngine.SpriteRenderer),"m_Sprite");
  if(UnityEditor.AnimationUtility.GetObjectReferenceCurve(clip,binding)==null)throw new System.Exception("Missing wing binding");
  UnityEditor.ObjectReferenceKeyframe[] keys;
  if(action=="Death")keys=new[]{new UnityEditor.ObjectReferenceKeyframe{time=0,value=sprites[direction+"_WingLowered"]}};
  else{
   keys=new UnityEditor.ObjectReferenceKeyframe[7];
   for(int i=0;i<6;i++)keys[i]=new UnityEditor.ObjectReferenceKeyframe{time=i/12f,value=sprites[direction+(i%2==0?"_WingRaised":"_WingLowered")]};
   keys[6]=new UnityEditor.ObjectReferenceKeyframe{time=duration-1f/clip.frameRate,value=sprites[direction+"_WingRaised"]};
  }
  UnityEditor.AnimationUtility.SetObjectReferenceCurve(clip,binding,keys);
 }
 if(prior!=signature(clip))throw new System.Exception("Non-wing contract changed "+action);
 UnityEditor.EditorUtility.SetDirty(clip);
 var curve=UnityEditor.AnimationUtility.GetObjectReferenceCurve(clip,UnityEditor.EditorCurveBinding.PPtrCurve("DirectionVisual/Up/Motion/WingL/Sprite",typeof(UnityEngine.SpriteRenderer),"m_Sprite"));
 clips.Add(new{action=action,duration=clip.length,frameRate=clip.frameRate,nonWingCurvesEventsSettingsUnchanged=true,keys=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(curve,k=>new{time=k.time,sprite=k.value.name}))});
}
UnityEditor.AssetDatabase.SaveAssets();
FTProject.EditorTools.EnemyDirectionSpec spec;
if(!FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("Wasp",out spec))throw new System.Exception("Missing Wasp spec");
string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report);
if(!pass)throw new System.Exception(report);
return new{pass=pass,report=report,clips=clips};
'''
owned()
response=c.tool('execute_code',{'action':'execute','code':code});write(V/'patch_response.json',response)
result=data(response);assert result['success'],result
result=result['data']['result'];assert result['pass'],result
(V/'verify.txt').write_text(result['report']+'\n',encoding='utf-8')
refresh=c.tool('refresh_unity',{'mode':'force','scope':'all','compile':'request','wait_for_ready':True});write(V/'refresh.json',refresh)
deadline=time.monotonic()+120
while True:
    c=Client();project=c.identity();state=c.resource('mcpforunity://editor/state');s=state['data']
    if not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']:break
    if time.monotonic()>deadline:raise TimeoutError('Refresh not ready')
    time.sleep(2)
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
failed=c.tool('execute_code',{'action':'execute','code':'return UnityEditor.EditorUtility.scriptCompilationFailed;'})
assert data(errors)['data']==[] and data(failed)['data']['result'] is False,(errors,failed)
final={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
changed=[p for p in final if final[p]!=before[p]]
assert len(changed)==4 and all(p.startswith(art+'/Animations/') and p.endswith('_Directions.anim') for p in changed),changed
write(V/'manifest.json',{'character':'Wasp','revision':'art_r02_flap_r03','observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'owner_thread_id':OWNER,'dispatch_token':TOKEN,'parent_manifest':'../installed_manifest.json','parent_manifest_sha256':sha(D/'installed_manifest.json'),'reason':'Restore original 1/12-second paired-wing flap timing for Ready/Walk/Attack; Death stays Lowered. Extra final Raised key remains before clip stop to preserve 0.5s duration. Only four Wasp clips change.','before_files':before,'changed_paths':changed,'final_files':final,'verification':result,'project':project,'state':state,'errors':errors,'script_compilation_failed':False,'protocol_history':c.history})
print(json.dumps({'pass':True,'changed':changed,'snapshot_paths':len(final),'clips':result['clips'],'console_errors':0,'failed':False},ensure_ascii=False))
