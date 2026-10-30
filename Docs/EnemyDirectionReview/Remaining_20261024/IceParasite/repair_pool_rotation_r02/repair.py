from pathlib import Path
from datetime import datetime, timezone
import sys, json, hashlib, shutil, subprocess

REV = Path(__file__).resolve().parent
CHAR = REV.parent
HERE = CHAR.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from mcp_call import Client

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def unwrap(value):
    value = value.get('structuredContent') or json.loads(value['content'][0]['text'])
    if 'result' in value and 'data' not in value:
        value = value['result']
    if not value.get('success'):
        raise RuntimeError(str(value))
    return value['data']['result']

progress = json.loads((HERE/'progress.json').read_text(encoding='utf-8'))
item = next(x for x in progress['items'] if x['name'] == 'IceParasite')
assert progress['current'] == 'IceParasite' and item['status'] == 'blocked'
assert not (REV/'repair_result.json').exists(), 'Repair already executed'
client = Client()
project = client.identity()
probe = unwrap(client.tool('execute_code', {'action':'execute','code':
    'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,updating=UnityEditor.EditorApplication.isUpdating,failed=UnityEditor.EditorUtility.scriptCompilationFailed,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty};'}))
assert not any(probe.values()), probe
manifest = json.loads((CHAR/'installed_manifest.json').read_text(encoding='utf-8'))
drift = [x['path'] for x in manifest['changes'] if sha(ROOT/x['path']) != x['after']]
baseline = json.loads((HERE/'production_fingerprints_before.json').read_text(encoding='utf-8'))
target = next(x for x in json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))['targets'] if x['name']=='IceParasite')
for path in [target['battle']+'.meta',target['source'],target['source']+'.meta',target['atlas'],target['atlas']+'.meta']:
    if sha(ROOT/path) != baseline[path]:
        drift.append(path)
assert not drift, 'Fingerprint drift: '+str(drift)
files = {p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
(REV/'scope_before.json').write_text(json.dumps(files,indent=2),encoding='utf-8')
for path in ['runtime_summary.json','runtime_visual_strip.png','installed_manifest.json','blocked_visual_review.json']:
    dest = REV/'before'/path
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(CHAR/path,dest)
shutil.copy2(HERE/'progress.json',REV/'before/progress.json')
for action in ['Ready','Walk']:
    path = ROOT/target['art_dir']/'Animations'/(action+'_Directions.anim')
    shutil.copy2(path,REV/'before'/path.name)
(REV/'git_status_before.txt').write_text(subprocess.check_output(['git','status','--short'],cwd=ROOT).decode('utf-8'),encoding='utf-8')
(REV/'baseline.json').write_text(json.dumps({'project':project,'state':probe,'drift':drift,'captured_at':datetime.now(timezone.utc).isoformat(),'protected_file_count':len(files),'protocol_history':client.history},ensure_ascii=False,indent=2),encoding='utf-8')
code = '''
if(UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode || UnityEditor.EditorApplication.isCompiling || UnityEditor.EditorApplication.isUpdating) throw new System.InvalidOperationException("Editor busy");
string folder="Assets/_UIAssets/Monsters/Parasites/IceParasite/Directions/Animations/";
var changed=new System.Collections.Generic.List<string>();
foreach(string action in new[]{"Ready","Walk"}) {
 var clip=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>(folder+action+"_Directions.anim");
 if(!clip) throw new System.InvalidOperationException("Missing dedicated clip");
 float duration=clip.length;
 foreach(var binding in UnityEditor.AnimationUtility.GetCurveBindings(clip))
  if(binding.path=="Body" && (binding.propertyName.StartsWith("localEulerAngles") || binding.propertyName.StartsWith("m_LocalRotation"))) throw new System.InvalidOperationException("Unexpected existing rotation binding");
 foreach(string axis in new[]{"x","y","z"})
  UnityEditor.AnimationUtility.SetEditorCurve(clip,UnityEditor.EditorCurveBinding.FloatCurve("Body",typeof(UnityEngine.Transform),"localEulerAnglesRaw."+axis),UnityEngine.AnimationCurve.Constant(0,duration,0));
 UnityEditor.EditorUtility.SetDirty(clip);
 changed.Add(UnityEditor.AssetDatabase.GetAssetPath(clip));
}
UnityEditor.AssetDatabase.SaveAssets();
return changed;
'''
result = unwrap(client.tool('execute_code',{'action':'execute','code':code}))
(REV/'repair_result.json').write_text(json.dumps({'changed':result,'protocol_history':client.history,'reason':'Dedicated Ready/Walk clips restore horizontal Body rotation after Death ends at -180 degrees; no source/shared curves replaced.'},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'repaired':result,'scope_files':len(files),'fingerprint_drift':drift},ensure_ascii=False),flush=True)
