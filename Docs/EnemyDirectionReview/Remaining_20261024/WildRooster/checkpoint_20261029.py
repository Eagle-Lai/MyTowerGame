"""Guarded WildRooster-only checkpoints. Never rewrites shared C# or source assets."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, re, subprocess, sys

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
NAME = 'WildRooster'
OWNER = '01a18560-5f4b-7b42-a2cf-f926c68a77ae'
TOKEN = 'wildgoat-to-wildrooster-20261029_095556-9aeda72a-08aa-4bfe-aca0-1b03c0381c5e'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
now = lambda: datetime.now(timezone(timedelta(hours=8))).isoformat()
sys.path.insert(0, str(H))
from mcp_call import Client, URL

def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def owner():
    c = read(H/'conversation_chain.json')
    assert c['state']=='active' and c['owner_thread_id']==OWNER==os.environ.get('CODEX_THREAD_ID')
    assert c['dispatch_token']==TOKEN and c['current_character']==NAME
    return c

def unwrap(v):
    v = v.get('structuredContent') or json.loads(v['content'][0]['text'])
    assert v.get('success'), v
    return v

def result(v):
    v = unwrap(v)['data']['result']
    return json.loads(v) if isinstance(v,str) else v

LIVE = 'return new {projectRoot=System.IO.Path.GetFullPath(System.IO.Path.Combine(UnityEngine.Application.dataPath,"..")),unityVersion=UnityEngine.Application.unityVersion,playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path,sceneCount=UnityEngine.SceneManagement.SceneManager.sceneCount,sceneDirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation};'

def idle(v):
    assert v['projectRoot'].replace('\\','/').lower()=='e:/mytowergame' and v['unityVersion']=='2022.3.62f3c1'
    assert v['scene']=='Assets/Scenes/Boot.unity' and v['sceneCount']==1
    assert not any(v[k] for k in ['playing','compiling','failed','updating','sceneDirty','balance','recording','review','manual']), v

def files():
    return {p.relative_to(ROOT).as_posix():sha(p) for f in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/f).rglob('*') if p.is_file()}

def target():
    return next(t for t in read(H/'local_baseline.json')['targets'] if t['name']==NAME)

if __name__=='__main__':
    owner()
    phase=sys.argv[1]
    if phase=='baseline':
        out=D/'incremental_before_20261029.json'
        assert not out.exists(), 'Keep the original current-disk baseline'
        t=target(); paths=[t[k]+s for k in ['battle','source','atlas'] for s in ['', '.meta']]
        protected={p:sha(ROOT/p) for p in paths}
        assert all(sha(D/'reference'/Path(p).name)==v for p,v in protected.items())
        status=subprocess.run(['git','status','--porcelain=v1','--untracked-files=normal'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',check=True).stdout
        (D/'git_status_before_20261029.txt').write_text(status,encoding='utf-8')
        snapshot=files()
        progress=read(H/'progress.json')
        write(out,{'observed_at':now(),'owner_thread_id':OWNER,'dispatch_token':TOKEN,'basis':'Current disk including existing changes, no Git HEAD restoration','files':[{'path':p,'sha256':v} for p,v in sorted(snapshot.items())],'protected_six':protected,'target':t,'progress':{k:v for k,v in progress.items() if k!='items'},'remaining':[i for i in progress['items'] if i['status'] not in ['completed_pending_user_art_review','user_approved']]})
        print(json.dumps({'files':len(snapshot),'protected_six':protected,'completed_count':progress['completed_count'],'target':t,'git_status_lines':len(status.splitlines())},ensure_ascii=False))
    elif phase=='probe':
        label=sys.argv[2]
        out=D/('unity_'+label+'_20261029.json'); assert not out.exists()
        c=Client(); report={'observed_at':now(),'transport':URL}
        try:
            report['project']=c.identity()
            report['errors']=unwrap(c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'}))
            report['state']=c.resource('mcpforunity://editor/state')
            report['live_response']=c.tool('execute_code',{'action':'execute','code':LIVE})
            report['live']=result(report['live_response']); idle(report['live'])
            assert report['errors']['data']==[],report['errors']
            report['success']=True
        except Exception as e:
            report.update(success=False,error=str(e))
        finally:
            report['protocol_history']=c.history; write(out,report)
        print(json.dumps({k:v for k,v in report.items() if k not in ['state','protocol_history','live_response']},ensure_ascii=False))
        if not report['success']:sys.exit(1)
    elif phase=='preplay':
        out=D/'production_before_play_20261029.json';assert not out.exists()
        manifest=read(D/'installed_manifest.json');assert manifest['verification']['data']['result']['pass']
        t=target();art=ROOT/t['art_dir'];paths=[ROOT/t['battle'],ROOT/(t['battle']+'.meta'),ROOT/(t['art_dir']+'.meta')]+[p for p in art.rglob('*') if p.is_file()]
        snapshot={p.relative_to(ROOT).as_posix():sha(p) for p in paths};assert all(snapshot.values())
        baseline=read(D/'incremental_before_20261029.json');before={r['path']:r['sha256'] for r in baseline['files']};current=files()
        changes=[p for p in set(before)|set(current) if before.get(p)!=current.get(p)]
        assert set(changes)<=set(snapshot),changes
        assert all(current[p]==v for p,v in baseline['protected_six'].items() if p!=t['battle'])
        assert all(current[c['path']]==c['after'] for c in manifest['changes'])
        for suffix in ['.png','.layout.json','.sprites.json']:assert sha(D/'staged_art'/(NAME+'_Directions'+suffix))==sha(art/(NAME+'_Directions'+suffix))
        write(out,{'at':now(),'revision':'art_r03','manifest':'installed_manifest.json','manifest_sha256':sha(D/'installed_manifest.json'),'verify_pass':True,'stage_review':'offline_review_art_r03_20261029.json','stage_review_sha256':sha(D/'offline_review_art_r03_20261029.json'),'final_files':snapshot,'preplay_changes':changes})
        p=read(H/'progress.json');i=next(i for i in p['items'] if i['name']==NAME);i.update(status='staged_pending_visual_check',stage='installed_verified_pending_runtime',final_revision='art_r03');p.update(updated_at=now());write(H/'progress.json',p)
        print(json.dumps({'preplay_files':len(snapshot),'changes':len(changes),'installer_verify':True,'stage_identical':True}))
    elif phase=='preinstall':
        from PIL import Image
        import numpy as np
        out=D/'offline_review_art_r03_20261029.json';assert not out.exists()
        baseline=read(D/'incremental_before_20261029.json');before={r['path']:r['sha256'] for r in baseline['files']}
        current=files();assert current==before,'Production changed before installation; inspect drift'
        art=D/'staged_art';spec=read(art/(NAME+'_Directions.sprites.json'));layout=read(art/(NAME+'_Directions.layout.json'))
        assert len(spec['sprites'])==14 and spec['ppu']==100 and layout['motionKind']=='bird'
        assert layout['anatomy']=={'legs':2,'wings':2,'claws':0,'tails':0,'arms':0,'feelers':0}
        atlas=Image.open(art/(NAME+'_Directions.png')).convert('RGBA');a=np.array(atlas).astype(np.int16)
        assert atlas.size==(2048,2048) and np.any(a[:,:,3]==0)
        magenta=(a[:,:,0]>a[:,:,1]+60)&(a[:,:,2]>a[:,:,1]+50)&(a[:,:,3]>200)
        assert not np.any(magenta),'Magenta retained in opaque foreground'
        pieces=[]
        for s in spec['sprites']:
            piece=Image.open(art/(s['name']+'.png')).convert('RGBA')
            assert piece.size==(s['w'],s['h'])
            if s['name'].endswith('_Tail'):assert piece.getbbox() is None
            else:assert piece.getbbox() is not None
            assert 0<=s['pivotX']<=1 and 0<=s['pivotY']<=1
            crop=atlas.crop((s['x'],2048-s['y']-s['h'],s['x']+s['w'],2048-s['y']))
            assert np.array_equal(np.array(piece),np.array(crop))
            pieces.append({'name':s['name'],'w':s['w'],'h':s['h'],'pivot':[s['pivotX'],s['pivotY']],'sha256':sha(art/(s['name']+'.png'))})
        report={'at':now(),'revision':'art_r03','actually_viewed':['reference/WildRooster.png','reference/source_prefab_offline.png','generation/Up/raw.png','generation/Down/raw.png','offline_r01/offline_rig_proof.png','offline_r01/parts_clean.png','offline_r02/offline_rig_proof.png','local_raster_r02/body_review.png','offline_rig_proof.png','local_raster_r03/body_review.png'],'observations':'r01浮翅与重复领口否决；r02局部帽盖/尾根矩形接缝否决；r03消除接缝，尾羽仅在Up下方臀部融合，Down身前视时尾羽遮蔽。双翅内收白根与肩相连，双腿根在身体内，Up纯奶油后脑、单后趾；Down正常/愤怒/死亡头居中，头身连接。尾羽一体Body不新增Tail节点。内部离线审阅通过，尚待真实Play动态与用户美术审核。','offline_visual_pass':True,'user_approved':False,'source_protection_unchanged':True,'current_disk_baseline_files':len(before),'production_changes_before_install':[],'pieces':pieces,'transparent_tail_compatibility':True,'opaque_magenta_pixels':int(magenta.sum()),'stage_files':{p.name:sha(p) for p in art.glob(NAME+'_Directions.*')},'alpha_edges':'Actually viewed clean pieces and body details on dark background; numerical checks do not replace visual review.'}
        write(out,report)
        p=read(H/'progress.json');i=next(i for i in p['items'] if i['name']==NAME);i.update(status='staged_pending_visual_check',stage='offline_art_r03_reviewed_pending_install',final_revision='art_r03');p.update(updated_at=now());write(H/'progress.json',p)
        print(json.dumps({'offline_visual_pass':True,'revision':'art_r03','pieces':len(pieces),'protected_six_unchanged':True,'production_changes':0},ensure_ascii=False))
    elif phase=='inspect':
        out=D/'source_inspection_20261029.json'; assert not out.exists()
        t=target(); c=Client(); report={'observed_at':now(),'transport':URL,'project':c.identity()}
        for k in ['battle','source','atlas','controller']:
            p=ROOT/t[k]
            # Full reads preserve the exact current source, rather than a Git reconstruction.
            report[k]={'path':t[k],'sha256':sha(p),'bytes':len(p.read_bytes())}
        code='var paths=new[]{'+json.dumps(t['source'])+','+json.dumps(t['battle'])+'};var prefabs=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(paths,p=>new {path=p,nodes=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>(p).GetComponentsInChildren<UnityEngine.Transform>(true),n=>new {name=n.name,parent=n.parent?n.parent.name:"",position=n.localPosition,scale=n.localScale,rotation=n.localRotation,active=n.gameObject.activeSelf,components=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(n.GetComponents<UnityEngine.Component>(),v=>new {type=v.GetType().FullName,serialized=UnityEditor.EditorJsonUtility.ToJson(v)}))}))}));var ctrl=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEditor.Animations.AnimatorController>('+json.dumps(t['controller'])+');return new {prefabs=prefabs,parameters=ctrl.parameters,clips=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(System.Linq.Enumerable.Distinct(ctrl.animationClips),a=>new {name=a.name,path=UnityEditor.AssetDatabase.GetAssetPath(a),length=a.length,rate=a.frameRate,loop=UnityEditor.AnimationUtility.GetAnimationClipSettings(a).loopTime,events=UnityEditor.AnimationUtility.GetAnimationEvents(a),floats=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetCurveBindings(a),b=>new {path=b.path,type=b.type.FullName,property=b.propertyName,keys=UnityEditor.AnimationUtility.GetEditorCurve(a,b).keys})),pptrs=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetObjectReferenceCurveBindings(a),b=>new {path=b.path,type=b.type.FullName,property=b.propertyName,keys=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetObjectReferenceCurve(a,b),k=>new {time=k.time,name=k.value?k.value.name:"",asset=k.value?UnityEditor.AssetDatabase.GetAssetPath(k.value):""}))}))}))};'
        code=code.replace('position=n.localPosition,scale=n.localScale,rotation=n.localRotation', 'position=new[]{n.localPosition.x,n.localPosition.y,n.localPosition.z},scale=new[]{n.localScale.x,n.localScale.y,n.localScale.z},rotation=new[]{n.localRotation.x,n.localRotation.y,n.localRotation.z,n.localRotation.w}')
        code=code.replace('parameters=ctrl.parameters','parameters=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(ctrl.parameters,p=>new {name=p.name,type=p.type.ToString()}))')
        code=code.replace('events=UnityEditor.AnimationUtility.GetAnimationEvents(a)', 'events=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetAnimationEvents(a),e=>new {time=e.time,function=e.functionName,intParameter=e.intParameter,floatParameter=e.floatParameter,stringParameter=e.stringParameter,objectReference=e.objectReferenceParameter?UnityEditor.AssetDatabase.GetAssetPath(e.objectReferenceParameter):""}))')
        report['native_response']=c.tool('execute_code',{'action':'execute','code':code})
        write(D/'native_inspection_response_20261029.json',report)
        report['native']=result(report['native_response'])
        report['protocol_history']=c.history; write(out,report)
        print(json.dumps({'prefabs':[{'path':p['path'],'nodes':[n['name'] for n in p['nodes']]} for p in report['native']['prefabs']],'clips':[{'name':a['name'],'length':a['length'],'rate':a['rate'],'loop':a['loop'],'floats':len(a['floats']),'pptrs':len(a['pptrs']),'events':a['events']} for a in report['native']['clips']]},ensure_ascii=False))
    else:
        raise ValueError(phase)
