from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib,json,os,re,subprocess,sys
D=Path(__file__).resolve().parent; H=D.parent; R=H.parents[2]
sys.path.insert(0,str(H))
from mcp_call import Client,URL
NAME='TreasureChest'; TOKEN='tiger-to-treasurechest-7472eaa093fc4c088bd266ee703d9e0e'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
def now(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
def owner():
    c=read(H/'conversation_chain.json')
    assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']==NAME and c['dispatch_token']==TOKEN
    return c
def unwrap(v):
    v=v.get('structuredContent') or json.loads(v['content'][0]['text'])
    if 'result' in v and 'data' not in v:v=v['result']
    assert v.get('success'),v
    return v
def inventory(): return {p.relative_to(R).as_posix():sha(p) for f in ['Assets','Packages','ProjectSettings','Luban'] for p in (R/f).rglob('*') if p.is_file()}
def probe(client):
    return unwrap(client.tool('execute_code',dict(action='execute',code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};')))['data']['result']
def audit(label):
    file='scope_TreasureChest_'+label+'_20261028.json'
    v=subprocess.run([sys.executable,str(H/'audit_scope.py'),file],capture_output=True,encoding='utf-8',check=True)
    (D/('legacy_scope_'+label+'_console.txt')).write_text(v.stdout,encoding='utf-8')
    return read(H/file)
if __name__=='__main__':
    owner();action=sys.argv[1]
    t=next(x for x in read(H/'local_baseline.json')['targets'] if x['name']==NAME)
    if action=='intent':
        direction=sys.argv[2];assert direction in ['Up','Down'];out=D/'generation'/direction
        assert not any((out/p).exists() for p in ['request.json','result.json','uncertain_result.json','raw.png','generation_intent.json'])
        assert inventory()==read(D/'incremental_before_20261028.json')['files']
        if direction=='Down': assert read(D/'generation/Up/review_20261028.json')['accepted_for_staging']
        write(out/'generation_intent.json',dict(created_at=now(),owner_thread_id=os.environ['CODEX_THREAD_ID'],dispatch_token=TOKEN,character=NAME,direction=direction,max_requests=1,model='gpt-image-2',quality='medium',size='1536x1024',n=1,transport='curl_https_no_retry',prompt_sha256=sha(out/'prompt.txt'),protected_six=read(D/'incremental_before_20261028.json')['protected_six']))
        print(json.dumps(dict(intent=direction,max_requests=1)))
    if action=='sync':
        assert not (D/'incremental_before_20261028.json').exists()
        files=inventory();original=read(H/'production_fingerprints_before.json')
        protected={p:sha(R/p) for p in [t['battle'],t['battle']+'.meta',t['source'],t['source']+'.meta',t['atlas'],t['atlas']+'.meta']}
        assert all(s==original[p].upper() for p,s in protected.items())
        assert all(sha(D/'reference'/Path(p).name)==s for p,s in protected.items())
        write(D/'incremental_before_20261028.json',dict(observed_at=now(),files=files,protected_six=protected,owner_thread_id=os.environ['CODEX_THREAD_ID'],dispatch_token=TOKEN))
        for label,args in [('status',['status','--short']),('target_diff',['diff','--',t['battle'],str(Path(t['source']).parent)])]:
            v=subprocess.run(['git',*args],cwd=R,capture_output=True,encoding='utf-8',check=True)
            (D/('git_'+label+'_before_20261028.txt')).write_text(v.stdout,encoding='utf-8')
            if label=='target_diff': assert not v.stdout.strip()
        legacy=audit('before')
        client=Client();project=client.identity()
        errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
        state=client.resource('mcpforunity://editor/state');live=probe(client)
        write(D/'unity_before_20261028.json',dict(observed_at=now(),transport=URL,project=project,errors=errors,state=state,live=live,history=client.history))
        assert not any(v for k,v in live.items() if k!='scene'),live
        assert errors['data']==[],errors
    if action in ['sync','contracts']:
        client=Client();project=client.identity()
        code='''var p=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>("Assets/Prefabs/Enemy/Enemy_TreasureChest.prefab");var r=p.GetComponent<FTProject.MonsterAnimEventReceiver>();var c=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.RuntimeAnimatorController>("Assets/_UIAssets/Monsters/_Common/Animations/Container/Controller.controller");return new {receiver=new{head=r.HeadRenderer==null?null:r.HeadRenderer.name,sprites=r.HeadSprites==null?-1:r.HeadSprites.Length},renderers=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(p.GetComponentsInChildren<UnityEngine.SpriteRenderer>(true),s=>new{name=s.name,sprite=s.sprite==null?null:s.sprite.name,active=s.gameObject.activeSelf})),clips=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(System.Linq.Enumerable.Distinct(c.animationClips),a=>new{name=a.name,path=UnityEditor.AssetDatabase.GetAssetPath(a),length=a.length,loop=a.isLooping,bindings=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetCurveBindings(a),b=>new{path=b.path,property=b.propertyName,keys=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetEditorCurve(a,b).keys,k=>new{time=k.time,value=k.value,inTangent=k.inTangent,outTangent=k.outTangent}))})),pptr=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetObjectReferenceCurveBindings(a),b=>new{path=b.path,property=b.propertyName})),events=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetAnimationEvents(a),e=>new{time=e.time,function=e.functionName,intParameter=e.intParameter}))})),dependencies=UnityEditor.AssetDatabase.GetDependencies("Assets/Prefabs/Enemy/Enemy_TreasureChest.prefab",true)};'''
        contracts=unwrap(client.tool('execute_code',dict(action='execute',code=code)))
        write(D/'source_animation_contracts_20261028.json',dict(project=project,contracts=contracts,history=client.history))
        print(json.dumps(dict(contracts=contracts['data']['result'])))
