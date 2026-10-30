"""Porcupine-only pose repair; preserve every prior animation and runtime revision."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, shutil, subprocess, sys

D = Path(__file__).resolve().parent
HERE = D.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from mcp_call import Client

OUT = D / 'repair_pose_r01'
ART = ROOT / 'Assets/_UIAssets/Monsters/Rats/Porcupine/Directions'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
def unwrap(result):
    value = result.get('structuredContent') or json.loads(result['content'][0]['text'])
    if not value.get('success'):
        raise RuntimeError(str(value))
    return value['data']['result']

if OUT.exists():
    raise SystemExit('Repair revision exists; inspect evidence instead of overwriting.')
progress = json.loads((HERE / 'progress.json').read_text(encoding='utf-8'))
item = next(x for x in progress['items'] if x['name'] == 'Porcupine')
assert item['status'] == 'blocked' and progress['completed_count'] == 62
previous = json.loads((D / 'installed_manifest.json').read_text(encoding='utf-8'))
for change in previous['changes']:
    assert sha(ROOT / change['path']) == change['after'], 'Installed drift: ' + change['path']
target = next(x for x in json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))['targets'] if x['name']=='Porcupine')
original = json.loads((HERE/'production_fingerprints_before.json').read_text(encoding='utf-8'))
for path in [target['source'],target['source']+'.meta',target['atlas'],target['atlas']+'.meta',target['battle']+'.meta']:
    assert sha(ROOT/path)==original[path], 'Source/GUID drift: '+path
client = Client()
identity = client.identity()
state = unwrap(client.tool('execute_code', {'action':'execute','code':'return Newtonsoft.Json.JsonConvert.SerializeObject(new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,updating=UnityEditor.EditorApplication.isUpdating,failed=UnityEditor.EditorUtility.scriptCompilationFailed,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty)});'}))
state = json.loads(state)
assert not any(state.values()), state
OUT.mkdir()
protected = [p for folder in ['Assets/Prefabs/Enemy','Assets/Scripts','Assets/Editor','Assets/_UIAssets/Monsters/_Common/Animations','Assets/ConfigJson','Assets/Gen','Luban/Config/Datas/Levels'] for p in (ROOT/folder).rglob('*') if p.is_file()]
protected += [ROOT/p for p in ['Luban/Config/Datas/EnemyData.xlsx','Luban/Config/Datas/__tables__.xlsx'] if (ROOT/p).is_file()]
protected += [p for p in ART.rglob('*') if p.is_file()]
before = {p.relative_to(ROOT).as_posix():sha(p) for p in protected}
for p in [ROOT/target['battle'],ROOT/(target['battle']+'.meta'),*[p for p in ART.rglob('*') if p.is_file()]]:
    dest = OUT/'before'/p.relative_to(ROOT)
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(p,dest)
for filename in ['installed_manifest.json','runtime_summary.json','runtime_visual_strip.png']:
    shutil.copy2(D/filename,OUT/('previous_'+filename))
(OUT/'baseline.json').write_text(json.dumps({'project':identity,'state':state,'progress':item,'completed_count':62,'fingerprints':before,'git_status':subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True,encoding='utf-8'),'at':datetime.now(timezone(timedelta(hours=8))).isoformat()},ensure_ascii=False,indent=2),encoding='utf-8')
code = r'''
if(UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode || UnityEditor.EditorApplication.isCompiling || UnityEditor.EditorApplication.isUpdating) throw new System.InvalidOperationException("Editor busy");
var edits=new System.Collections.Generic.List<object>();
foreach(string name in new[]{"Ready","Walk"}) {
 string path="Assets/_UIAssets/Monsters/Rats/Porcupine/Directions/Animations/"+name+"_Directions.anim";
 var clip=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>(path);
 if(!clip)throw new System.InvalidOperationException(path);
 foreach(string axis in new[]{"x","y","z"}) {
  var binding=UnityEditor.EditorCurveBinding.FloatCurve("Body",typeof(UnityEngine.Transform),"localEulerAnglesRaw."+axis);
  if(UnityEditor.AnimationUtility.GetEditorCurve(clip,binding)!=null)throw new System.InvalidOperationException("Refuse existing curve overwrite");
  UnityEditor.AnimationUtility.SetEditorCurve(clip,binding,UnityEngine.AnimationCurve.Constant(0f,clip.length,0f));
  edits.Add(new {path=path,property=binding.propertyName,value=0f});
 }
 UnityEditor.EditorUtility.SetDirty(clip);
}
UnityEditor.AssetDatabase.SaveAssets();
FTProject.EditorTools.EnemyDirectionSpec spec;
FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("Porcupine",out spec);
string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report);
return Newtonsoft.Json.JsonConvert.SerializeObject(new {pass=pass,report=report,edits=edits});
'''
(OUT/'patch.cs.txt').write_text(code,encoding='utf-8')
result=json.loads(unwrap(client.tool('execute_code',{'action':'execute','code':code})))
(OUT/'verify.txt').write_text(result['report'],encoding='utf-8')
after={p.relative_to(ROOT).as_posix():sha(p) for p in protected}
changes=[{'path':p,'before':s,'after':after[p]} for p,s in before.items() if s!=after[p]]
expected={'Assets/_UIAssets/Monsters/Rats/Porcupine/Directions/Animations/'+n+'_Directions.anim' for n in ['Ready','Walk']}
assert {c['path'] for c in changes}==expected, changes
manifest={'name':'Porcupine','revision':'repair_pose_r01','project':identity,'previous_manifest':'installed_manifest.json','changes':changes,'verification':result,'protocol_history':client.history,'reason':'Death writes Body rotation to -180 while Ready/Walk omit it. Add only missing neutral Euler curves in the character-specific clips; original curves, events, PPtr curves, duration, loops and shared assets are retained. Reapply this documented patch after any future full Builder rebuild.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
assert result['pass'], result
print(json.dumps({'repair':'repair_pose_r01','verify':result['pass'],'changed_files':changes}))
