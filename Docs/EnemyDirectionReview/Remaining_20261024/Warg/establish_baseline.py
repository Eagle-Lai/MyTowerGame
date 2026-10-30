from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, subprocess, sys

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

chain = json.loads((BASE/'conversation_chain.json').read_text(encoding='utf-8'))
assert chain['state']=='active' and chain['owner_thread_id']=='01a1830c-598a-7473-8ee1-01bccdd1f9be' and chain['current_character']=='Warg'
assert chain['dispatch_token']=='volcanoparasite-to-warg-20261028-7f2313bf-967a-440d-94c4-79bf845d2b6f'
t = next(t for t in json.loads((BASE/'local_baseline.json').read_text(encoding='utf-8'))['targets'] if t['name']=='Warg')
files = {p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
six = [t[k]+suffix for k in ['battle','source','atlas'] for suffix in ['', '.meta']]
protected = {p:files[p] for p in six}
assessment = json.loads((D/'successor_assessment_20261028_230454.json').read_text(encoding='utf-8'))
assert protected==assessment['protected_six'], 'Source drift since dispatch'
historical = json.loads((BASE/'production_fingerprints_before.json').read_text(encoding='utf-8'))
assert all(protected[p]==historical[p] for p in six), 'Historical Warg target drift; do not install'
now = datetime.now(timezone(timedelta(hours=8))).isoformat()
write(D/'incremental_before_20261028.json', {'observed_at':now,'owner_thread_id':chain['owner_thread_id'],'dispatch_token':chain['dispatch_token'],'files':files,'protected_six':protected,'target':t,'basis':'Current disk, including all pre-existing changes. Never Git HEAD.'})
for args, fname in [(['status','--short'], 'git_status_before.txt'), (['diff','--stat'], 'git_diff_stat_before.txt')]:
    result = subprocess.run(['git',*args],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    (D/fname).write_bytes(result.stdout)

c = Client()
report = {'observed_at':now,'project':c.identity()}
report['errors'] = c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
report['state'] = c.resource('mcpforunity://editor/state')
code = 'return new { playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path,sceneCount=UnityEngine.SceneManagement.SceneManager.sceneCount,sceneDirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation };'
report['probe'] = c.tool('execute_code',{'action':'execute','code':code})
code = '''var p=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>("Assets/Prefabs/Enemy/Enemy_Warg.prefab"); var a=p.GetComponent<UnityEngine.Animator>();var ctrl=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEditor.Animations.AnimatorController>("Assets/_UIAssets/Monsters/_Common/Animations/Wolf/Controller.controller");return new { battle=p.name,rootPosition=p.transform.localPosition,rootScale=p.transform.localScale,components=System.Linq.Enumerable.Select(p.GetComponents<UnityEngine.Component>(),v=>v.GetType().FullName).ToArray(),renderers=System.Linq.Enumerable.Select(p.GetComponentsInChildren<UnityEngine.SpriteRenderer>(true),v=>new {path=UnityEditor.AnimationUtility.CalculateTransformPath(v.transform,p.transform),sprite=v.sprite?v.sprite.name:null,position=v.transform.localPosition,scale=v.transform.localScale,order=v.sortingOrder}).ToArray(),dependencies=UnityEditor.AssetDatabase.GetDependencies("Assets/Prefabs/Enemy/Enemy_Warg.prefab",true),parameters=System.Linq.Enumerable.Select(ctrl.parameters,v=>new {name=v.name,type=v.type.ToString()}).ToArray(),clips=System.Linq.Enumerable.Select(System.Linq.Enumerable.Distinct(ctrl.animationClips),v=>new {name=v.name,path=UnityEditor.AssetDatabase.GetAssetPath(v),length=v.length,rate=v.frameRate,loop=UnityEditor.AnimationUtility.GetAnimationClipSettings(v).loopTime,floatCurves=System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetCurveBindings(v),b=>new {b.path,b.propertyName,keyCount=UnityEditor.AnimationUtility.GetEditorCurve(v,b).length}).ToArray(),pptrCurves=System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetObjectReferenceCurveBindings(v),b=>new {b.path,b.propertyName,keyCount=UnityEditor.AnimationUtility.GetObjectReferenceCurve(v,b).Length}).ToArray(),events=System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetAnimationEvents(v),e=>new {e.time,e.functionName,e.intParameter,e.stringParameter}).ToArray()}).ToArray() };'''
report['source_contract'] = c.tool('execute_code',{'action':'execute','code':code})
report['protocol_history'] = c.history
write(D/'preflight_20261028.json',report)
print(json.dumps({'baseline_files':len(files),'protected_six_match':True,'project':report['project'],'probe':report['probe'],'errors':report['errors'],'contract_saved':True},ensure_ascii=False))
