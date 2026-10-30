from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, subprocess, sys, os

D = Path(__file__).resolve().parent
BASE = D.parent
ROOT = BASE.parents[2]
sys.path.insert(0, str(BASE))
from mcp_call import Client

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest().upper()

def write(p, value):
    if p.exists():
        raise RuntimeError('Refuse overwriting evidence: '+str(p))
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def value(result):
    v = result.get('structuredContent') or json.loads(result['content'][0]['text'])
    if not v.get('success'): raise RuntimeError(str(v))
    return json.loads(v['data']['result'])

chain = json.loads((BASE/'conversation_chain.json').read_text(encoding='utf-8'))
assert chain['state']=='active' and chain['owner_thread_id']=='01a18619-6aa0-7a31-ac62-10a82077950b' and chain['current_character']=='WinterOgre'
assert chain['dispatch_token']=='winterboar-to-winterogre-20261029_131318-14b528b1-8990-455f-8069-d7ea49019046'
assert os.environ.get('CODEX_THREAD_ID') == chain['owner_thread_id']
t = next(t for t in json.loads((BASE/'local_baseline.json').read_text(encoding='utf-8'))['targets'] if t['name']=='WinterOgre')
files = {p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
six = [t[k]+suffix for k in ['battle','source','atlas'] for suffix in ['', '.meta']]
protected = {p:files[p] for p in six}
assessment = json.loads((D/'successor_assessment_20261029_131318.json').read_text(encoding='utf-8'))
assert protected==assessment['protected_six'], 'Source drift since dispatch'
historical = json.loads((BASE/'production_fingerprints_before.json').read_text(encoding='utf-8'))
assert all(protected[p]==historical[p] for p in six), 'Historical WinterOgre target drift; do not install'
now = datetime.now(timezone(timedelta(hours=8))).isoformat()
write(D/'incremental_before_20261029.json', {'observed_at':now,'owner_thread_id':chain['owner_thread_id'],'dispatch_token':chain['dispatch_token'],'files':files,'protected_six':protected,'target':t,'basis':'Current disk, including all pre-existing changes. Never Git HEAD.'})
for args, fname in [(['status','--short'], 'git_status_before.txt'), (['diff','--stat'], 'git_diff_stat_before.txt')]:
    result = subprocess.run(['git',*args],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    p=D/fname
    assert not p.exists()
    p.write_bytes(result.stdout)

c = Client()
report = {'observed_at':now,'project':c.identity()}
report['errors'] = c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
report['state'] = c.resource('mcpforunity://editor/state')
code = '''return Newtonsoft.Json.JsonConvert.SerializeObject(new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,scenes=System.Linq.Enumerable.Select(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>new {path=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).path,dirty=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty}).ToArray(),balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation});'''
report['probe_response'] = c.tool('execute_code',{'action':'execute','code':code})
report['probe'] = value(report['probe_response'])
report['protocol_history']=c.history
write(D/'preflight_20261029.json',report)
probe=report['probe']
assert not any(probe[k] for k in ['playing','compiling','failed','updating','balance','recording','review','manual']), probe
assert len(probe['scenes'])==1 and probe['scenes'][0]['path']=='Assets/Scenes/Boot.unity' and not probe['scenes'][0]['dirty'],probe

code = '''var p=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>("Assets/Prefabs/Enemy/Enemy_WinterOgre.prefab");var ctrl=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEditor.Animations.AnimatorController>("Assets/_UIAssets/Monsters/_Common/Animations/Giant/Controller.controller");return Newtonsoft.Json.JsonConvert.SerializeObject(new {battle=p.name,rootPosition=p.transform.localPosition.ToString(),rootScale=p.transform.localScale.ToString(),components=System.Linq.Enumerable.Select(p.GetComponents<UnityEngine.Component>(),v=>v.GetType().FullName).ToArray(),hierarchy=System.Linq.Enumerable.Select(p.GetComponentsInChildren<UnityEngine.Transform>(true),v=>new {path=UnityEditor.AnimationUtility.CalculateTransformPath(v,p.transform),position=v.localPosition.ToString(),scale=v.localScale.ToString(),active=v.gameObject.activeSelf,components=System.Linq.Enumerable.Select(v.GetComponents<UnityEngine.Component>(),x=>x.GetType().FullName).ToArray()}).ToArray(),renderers=System.Linq.Enumerable.Select(p.GetComponentsInChildren<UnityEngine.SpriteRenderer>(true),v=>new {path=UnityEditor.AnimationUtility.CalculateTransformPath(v.transform,p.transform),sprite=v.sprite?v.sprite.name:null,position=v.transform.localPosition.ToString(),scale=v.transform.localScale.ToString(),order=v.sortingOrder,material=v.sharedMaterial?UnityEditor.AssetDatabase.GetAssetPath(v.sharedMaterial):null}).ToArray(),dependencies=UnityEditor.AssetDatabase.GetDependencies("Assets/Prefabs/Enemy/Enemy_WinterOgre.prefab",true),parameters=System.Linq.Enumerable.Select(ctrl.parameters,v=>new {name=v.name,type=v.type.ToString(),v.defaultBool,v.defaultFloat,v.defaultInt}).ToArray(),clips=System.Linq.Enumerable.Select(System.Linq.Enumerable.Distinct(ctrl.animationClips),v=>new {name=v.name,path=UnityEditor.AssetDatabase.GetAssetPath(v),length=v.length,rate=v.frameRate,loop=UnityEditor.AnimationUtility.GetAnimationClipSettings(v).loopTime,floatCurves=System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetCurveBindings(v),b=>new {b.path,b.propertyName,type=b.type.FullName,keys=System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetEditorCurve(v,b).keys,k=>new {k.time,k.value,k.inTangent,k.outTangent,k.inWeight,k.outWeight,weightedMode=k.weightedMode.ToString()}).ToArray()}).ToArray(),pptrCurves=System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetObjectReferenceCurveBindings(v),b=>new {b.path,b.propertyName,type=b.type.FullName,keys=System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetObjectReferenceCurve(v,b),k=>new {k.time,name=k.value?k.value.name:null,asset=k.value?UnityEditor.AssetDatabase.GetAssetPath(k.value):null}).ToArray()}).ToArray(),events=System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetAnimationEvents(v),e=>new {e.time,e.functionName,e.intParameter,e.floatParameter,e.stringParameter,objectParameter=e.objectReferenceParameter?UnityEditor.AssetDatabase.GetAssetPath(e.objectReferenceParameter):null}).ToArray()}).ToArray()});'''
contract_response = c.tool('execute_code',{'action':'execute','code':code})
contract=value(contract_response)
write(D/'source_contract_20261029.json',{'project':report['project'],'contract':contract,'protocol_history':c.history})
print(json.dumps({'baseline_files':len(files),'protected_six_match':True,'project':report['project'],'probe':probe,'errors':report['errors'],'clips':[{k:v[k] for k in ['name','length','loop','events']} for v in contract['clips']],'parameters':contract['parameters']},ensure_ascii=False))
