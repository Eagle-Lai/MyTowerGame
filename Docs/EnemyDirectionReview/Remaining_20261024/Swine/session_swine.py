from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, re, subprocess, sys
D=Path(__file__).resolve().parent; H=D.parent; R=H.parents[2]
sys.path.insert(0,str(H))
from mcp_call import Client, URL
NAME='Swine'; TOKEN='slugqueen-to-swine-fa6420308b3143349c4b9b602019510d'
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
    assert v.get('success'),v
    return v
def inventory():
    return {p.relative_to(R).as_posix():sha(p) for f in ['Assets','Packages','ProjectSettings','Luban'] for p in (R/f).rglob('*') if p.is_file()}
def run(script,*args): return subprocess.run([sys.executable,str(H/script),*args],check=True)
def audit(label):
    file='scope_Swine_'+label+'_20261028.json'
    v=subprocess.run([sys.executable,str(H/'audit_scope.py'),file],capture_output=True,encoding='utf-8',check=True)
    (D/('legacy_scope_'+label+'_console.txt')).write_text(v.stdout,encoding='utf-8')
    return read(H/file)
def probe(client):
    return unwrap(client.tool('execute_code',dict(action='execute',code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};')))['data']['result']
if __name__=='__main__':
    owner(); action=sys.argv[1]
    t=next(x for x in read(H/'local_baseline.json')['targets'] if x['name']==NAME)
    if action=='sync':
        assert not (D/'incremental_before_20261028.json').exists()
        files=inventory(); original=read(H/'production_fingerprints_before.json')
        protected={p:sha(R/p) for p in [t['battle'],t['battle']+'.meta',t['source'],t['source']+'.meta',t['atlas'],t['atlas']+'.meta']}
        assert all(s==original[p].upper() for p,s in protected.items())
        for p in protected:
            assert sha(D/'reference'/Path(p).name)==protected[p]
        write(D/'incremental_before_20261028.json',dict(observed_at=now(),files=files,protected_six=protected,owner_thread_id=os.environ['CODEX_THREAD_ID'],dispatch_token=TOKEN))
        v=subprocess.run(['git','status','--short'],cwd=R,capture_output=True,encoding='utf-8',check=True);(D/'git_status_before_20261028.txt').write_text(v.stdout,encoding='utf-8')
        v=subprocess.run(['git','diff','--',t['battle'],str(Path(t['source']).parent)],cwd=R,capture_output=True,encoding='utf-8',check=True);(D/'git_target_diff_before_20261028.txt').write_text(v.stdout,encoding='utf-8');assert not v.stdout.strip()
        prefabs={}
        for label,path in [('source',t['source']),('battle',t['battle'])]:
            text=(R/path).read_text(encoding='utf-8-sig')
            blocks=list(re.finditer(r'^--- !u!(\d+) &(-?\d+)\s*\n(.*?)(?=^--- !u!|\Z)',text,re.M|re.S))
            prefabs[label]=dict(path=path,sha256=sha(R/path),complete_bytes=len((R/path).read_bytes()),serialized_objects=len(blocks),nodes=re.findall(r'^  m_Name: (.+)$',text,re.M),sprites=re.findall(r'^  m_Sprite: (.+)$',text,re.M),scripts=re.findall(r'^  m_Script: (.+)$',text,re.M),controller=re.findall(r'^  m_Controller: (.+)$',text,re.M))
        write(D/'full_prefab_inspection_20261028.json',prefabs)
        legacy=audit('before')
        client=Client(); project=client.identity()
        errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
        state=client.resource('mcpforunity://editor/state'); live=probe(client)
        write(D/'unity_before_20261028.json',dict(observed_at=now(),transport=URL,project=project,errors=errors,state=state,live=live,history=client.history))
        assert not any(v for k,v in live.items() if k!='scene'),live
        assert errors['data']==[],errors
        code='''var c=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.RuntimeAnimatorController>("Assets/_UIAssets/Monsters/_Common/Animations/Boar/Controller.controller");return new {clips=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(System.Linq.Enumerable.Distinct(c.animationClips),a=>new{name=a.name,path=UnityEditor.AssetDatabase.GetAssetPath(a),length=a.length,loop=a.isLooping,bindings=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetCurveBindings(a),b=>new{path=b.path,property=b.propertyName,keys=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetEditorCurve(a,b).keys,k=>new{time=k.time,value=k.value,inTangent=k.inTangent,outTangent=k.outTangent}))})),pptr=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetObjectReferenceCurveBindings(a),b=>new{path=b.path,property=b.propertyName,keys=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetObjectReferenceCurve(a,b),k=>new{time=k.time,asset=UnityEditor.AssetDatabase.GetAssetPath(k.value),name=k.value==null?null:k.value.name}))})),events=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetAnimationEvents(a),e=>new{time=e.time,function=e.functionName,intParameter=e.intParameter,floatParameter=e.floatParameter,stringParameter=e.stringParameter}))})),dependencies=UnityEditor.AssetDatabase.GetDependencies("Assets/Prefabs/Enemy/Enemy_Swine.prefab",true)};'''
        contracts=unwrap(client.tool('execute_code',dict(action='execute',code=code)))
        write(D/'source_animation_contracts_20261028.json',dict(project=project,contracts=contracts,history=client.history))
        print(json.dumps(dict(baseline_files=len(files),protected_drift=[],target_diff_empty=True,live=live,legacy_unexpected=len(legacy['unexpected']),legacy_semantic_failures=[n for n,s in legacy['semantics'].items() if not s['pass']],contracts=[dict(name=x['name'],length=x['length'],loop=x['loop'],bindings=len(x['bindings']),events=x['events']) for x in contracts['data']['result']['clips']])))
    elif action=='intent':
        direction=sys.argv[2]; assert direction in ['Up','Down']
        out=D/'generation'/direction
        assert not any((out/p).exists() for p in ['request.json','result.json','uncertain_result.json','raw.png','generation_intent.json'])
        assert inventory()==read(D/'incremental_before_20261028.json')['files'],'Production drift before generation'
        if direction=='Down': assert read(D/'generation/Up/review_20261028.json')['accepted_for_staging'] is True
        write(out/'generation_intent.json',dict(created_at=now(),owner_thread_id=os.environ['CODEX_THREAD_ID'],dispatch_token=TOKEN,character=NAME,direction=direction,max_requests=1,model='gpt-image-2',quality='medium',size='1536x1024',n=1,transport='curl_https_no_retry',prompt_sha256=sha(out/'prompt.txt'),protected_six=read(D/'incremental_before_20261028.json')['protected_six']))
        print(json.dumps(dict(intent=direction,max_requests=1)))
    elif action=='prepare':
        assert not (D/'anatomy_plan.json').exists()
        run('prepare_character.py',NAME)
        source=(H/'render_source_reference.py').read_text(encoding='utf-8').replace("contact.save(HERE/'source_reference_contact.png')","contact.save(HERE/'Swine'/'reference'/'battle_contact.png')")
        sys.argv=[str(H/'render_source_reference.py'),'--battle','--name',NAME]
        exec(compile(source,str(H/'render_source_reference.py'),'exec'),{'__file__':str(H/'render_source_reference.py'),'__name__':'__main__'})
        plan=read(D/'anatomy_plan.json')
        identity='Very round golden tan boar, broad cream round eyes with small black pupils, ochre irregular round patches, heavy dark smooth outlines, broad golden snout with two long dark nostrils and two large curved ivory cheek tusks. Two small triangular ears belong on the TORSO upper shoulders as in the source atlas, not duplicated on detached face. Four very short solid tan feet without claws or invented black shoes. One tiny smooth pointed tan tail, not curled, tufted or ringed. No helmet, mane, crown, saddle, armor or dorsal spikes.'
        plan.update(identity=identity,source_observations=dict(visible_renderers=6,legs=4,ears='two integrated into original Body sprite; no Head ears',tail='tiny pointed, integrated into Body originally; detached once for axial animation',expressions='normal huge cream eyes, angry angular eyelids, dead blank cream eyes and small hanging tongue',viewed=['reference/source_prefab_offline.png','reference/Swine.png']))
        write(D/'anatomy_plan.json',plan)
        for direction in ['Up','Down']:
            p=D/'generation'/direction/'prompt.txt';text=p.read_text(encoding='utf-8').replace('Round golden-tan spotted boar with ivory tusks, four short feet and tiny tapered tail.',identity)
            text=text.replace('including its original ears/horns/crest/hat','NO ears on detached face; ears are on torso as source; no horns/crest/hat')
            text+='\nSwine-specific anatomy: ONE boar only when assembled; exactly four short tiny solid tan feet total (one forefoot slice mirrored for pair, one hindfoot slice mirrored for pair), no fingers, claws or black shoes. Torso round with tan/ochre large patches, exactly two SMALL triangular ears at its neck/upper shoulders, NO extra ears on the face slices. Ivory tusks only in front face, never on back. Tail is one tiny tapered tan pointed projection, entirely detached cell7, none painted into torso. Keep body neck root solid opaque; no cutout for face. Do not add forehead spikes, bristles, stripe, saddle, jewelry or a second pair of ears. '
            text+=('Up rear head is a low rounded plain golden back of head with NO eyes, mouth, nostrils, tongue or tusks. The rear foot heel is rounded and smooth, no forward toe seam.\n' if direction=='Up' else 'Down front muzzle axial symmetric, two cream round eyes above a broad short golden snout with two dark long nostrils and two ivory upward tusks at cheek sides. Dead face has blank cream eyes and a small tan tongue as original, NOT X eyes.\n')
            p.write_text(text,encoding='utf-8')
        write(D/'reference_review_20261028.json',dict(observed_at=now(),viewed=plan['source_observations']['viewed'],observation=identity,source_sha256={p.name:sha(p) for p in (D/'reference').iterdir() if p.is_file()},prompt_sha256={d:sha(D/'generation'/d/'prompt.txt') for d in ['Up','Down']},root_rule_difference='AGENTS retains D:/FreedomTower_1/8082; explicit current target E:/MyTowerGame/8088 takes precedence'))
        p=read(H/'progress.json');i=next(x for x in p['items'] if x['name']==NAME);assert i['status']=='not_started';i.update(status='reference_prepared',user_approved=False,reference_review_file='Swine/reference_review_20261028.json');p.update(current=NAME,updated_at=now());write(H/'progress.json',p)
        c=owner();c.update(current_stage='reference_prepared_pending_Up_generation',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Swine/reference_review_20261028.json',updated_at=now());write(H/'conversation_chain.json',c)
        print(json.dumps(dict(prepared=NAME,kind=plan['kind'],identity=identity)))
