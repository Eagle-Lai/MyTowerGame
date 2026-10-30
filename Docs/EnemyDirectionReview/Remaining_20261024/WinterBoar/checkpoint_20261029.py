"""Guarded single-character checkpoints; all generated evidence stays under WinterBoar."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,sys,time
D=Path(__file__).resolve().parent;H=D.parent;ROOT=H.parents[2]
sys.path.insert(0,str(H))
from mcp_call import Client,URL
NAME='WinterBoar';TOKEN='winterbear-to-winterboar-20261029_121124-c33ba1f5-87c8-4aee-8729-55b098f67a75'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
now=lambda:datetime.now(timezone(timedelta(hours=8))).isoformat()
def owner():
    c=read(H/'conversation_chain.json')
    assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']==NAME and c['dispatch_token']==TOKEN
    return c
def write(p,v):
    assert not p.exists(),p
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def unwrap(v):
    v=v.get('structuredContent') or json.loads(v['content'][0]['text'])
    assert v.get('success'),v
    return v
def result(v):
    v=unwrap(v)['data']['result'];return json.loads(v) if isinstance(v,str) else v
def files():
    return {p.relative_to(ROOT).as_posix():sha(p) for f in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/f).rglob('*') if p.is_file()}
def target():return next(t for t in read(H/'local_baseline.json')['targets'] if t['name']==NAME)
LIVE='return new {projectRoot=System.IO.Path.GetFullPath(System.IO.Path.Combine(UnityEngine.Application.dataPath,"..")),unityVersion=UnityEngine.Application.unityVersion,playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path,sceneCount=UnityEngine.SceneManagement.SceneManager.sceneCount,sceneDirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation};'
def idle(v):
    assert v['projectRoot'].replace('\\','/').lower()=='e:/mytowergame' and v['unityVersion']=='2022.3.62f3c1'
    assert v['scene']=='Assets/Scenes/Boot.unity' and v['sceneCount']==1
    assert not any(v[k] for k in ['playing','compiling','failed','updating','sceneDirty','balance','recording','review','manual']),v
def probe(label):
    owner();c=Client();report={'at':now(),'transport':URL,'project':c.identity()}
    report['errors']=unwrap(c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'}))
    report['state']=c.resource('mcpforunity://editor/state')
    report['live']=result(c.tool('execute_code',{'action':'execute','code':LIVE}))
    report['protocol_history']=c.history
    write(D/('unity_'+label+'_20261029.json'),report)
    idle(report['live']);assert report['errors']['data']==[],report['errors']
    state=report['state']['data']
    assert not state['tests']['is_running']
    print(json.dumps({'probe':label,'project':report['project'],'live':report['live'],'errors':0,'state_staleness':state['staleness']},ensure_ascii=False))
    return report
if __name__=='__main__':
    owner();phase=sys.argv[1]
    if phase=='probe':probe(sys.argv[2])
    elif phase=='preinstall':
        from PIL import Image
        import numpy as np
        base=read(D/'incremental_before_20261029.json');current=files()
        assert current==base['files'],'Preinstall full path union drift'
        art=D/'staged_art';spec=read(art/(NAME+'_Directions.sprites.json'));layout=read(art/(NAME+'_Directions.layout.json'))
        assert len(spec['sprites'])==12 and spec['ppu']==100 and layout['anatomy']=={'legs':4,'wings':0,'claws':0,'tails':0,'arms':0,'feelers':0}
        atlas=Image.open(art/(NAME+'_Directions.png')).convert('RGBA');a=np.array(atlas).astype(np.int16)
        assert atlas.size==(2048,2048) and np.any(a[:,:,3]==0)
        magenta=(np.minimum(a[:,:,0],a[:,:,2])-a[:,:,1]>18)&(a[:,:,3]>30)
        assert not np.any(magenta),'Visible magenta fringe'
        pieces=[]
        for s in spec['sprites']:
            p=art/(s['name']+'.png');im=Image.open(p).convert('RGBA');assert im.getbbox() is not None
            assert im.size==(s['w'],s['h']) and 0<=s['pivotX']<=1 and 0<=s['pivotY']<=1
            crop=atlas.crop((s['x'],2048-s['y']-s['h'],s['x']+s['w'],2048-s['y']))
            pa,ca=np.array(im),np.array(crop)
            assert np.array_equal(pa[:,:,3],ca[:,:,3]) and np.array_equal(pa[pa[:,:,3]>0],ca[pa[:,:,3]>0])
            pieces.append({'name':s['name'],'size':list(im.size),'pivot':[s['pivotX'],s['pivotY']],'sha256':sha(p)})
        for v in layout['views']:
            assert len(v['parts'])==6 and sum(p['role']=='leg' for p in v['parts'])==4 and all(p['role']!='tail' for p in v['parts'])
        write(D/'offline_review_art_r04_20261029.json',{'at':now(),'revision':'art_r04','actually_viewed':['reference/WinterBoar.png','reference/source_prefab_offline.png','generation/Up/raw.png','generation/Down/raw.png','down_head_original_detail.png','down_body_original_detail.png','offline_art_r01/offline_rig_proof.png','offline_art_r01/parts_clean.png','offline_art_r02/offline_Down.png','offline_art_r02/parts_clean.png','offline_Up.png','offline_Down.png','parts_clean.png','staged_art/Down_HeadNormal.png','offline_art_r03/offline_Up.png','offline_art_r03/offline_Down.png','staged_art/Up_Body.png'],'visual_note':'实际审完整源atlas和prefab，WinterBoar白灰圆胖四足、赭斑、棕背鬃、宽金鼻与双长獠牙，无独立尾。两方向raw已实看，Down重复额顶鬃毛本地去除，保留躯干唯一背鬃与原耳/眉/脸；r01额头角折裁边、r02眉部白缺口/品红边/露腿根否决保留。r03清理品红污染边、恢复原眉与远侧腿根内收；Up纯后脑无脸、耳背和光滑后跟，Down鼻口居中，颈肩髋连接、短腿，无地面阴影。远侧腿会被圆胖躯干轴向遮挡，真实动态待审。细微白色眉顶高光/局部修绘与源相比简化，不冒充AI原图；r03预检发现28个缩小后品红染边，r04在保持alpha和形状下用最近不污染描边RGB修复所有检查到的污染边缘像素，内部离线通过但用户待美术验收。','offline_visual_pass':True,'user_approved':False,'pieces':pieces,'opaque_magenta_pixels':int(magenta.sum()),'production_changes_before_install':[],'basis_files':len(current),'stage_files':{p.name:sha(p) for p in art.glob(NAME+'_Directions.*')},'raster_manifests':{p.relative_to(D).as_posix():sha(p) for p in D.glob('local_raster_r*/repair_manifest.json')}})
        p=read(H/'progress.json');i=next(i for i in p['items'] if i['name']==NAME);i.update(status='staged_pending_visual_check',stage='offline_art_r04_reviewed_pending_install',final_revision='art_r04');p['updated_at']=now();(H/'progress.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'offline_visual_pass':True,'revision':'art_r04','pieces':len(pieces),'source_protected':True,'production_changes':0}))
    elif phase=='preplay':
        manifest=read(D/'installed_manifest.json');assert manifest['verification']['data']['result']['pass']
        t=target();art=ROOT/t['art_dir'];paths=[ROOT/t['battle'],ROOT/(t['battle']+'.meta'),ROOT/(t['art_dir']+'.meta')]+[p for p in art.rglob('*') if p.is_file()]
        snapshot={p.relative_to(ROOT).as_posix():sha(p) for p in paths};assert all(snapshot.values())
        before=read(D/'incremental_before_20261029.json');current=files()
        changes=[p for p in set(before['files'])|set(current) if before['files'].get(p)!=current.get(p)]
        assert set(changes)<=set(snapshot),changes
        assert all(current[p]==v for p,v in before['protected_six'].items() if p!=t['battle'])
        assert all(current[x['path']]==x['after'] for x in manifest['changes'])
        for suffix in ['.png','.layout.json','.sprites.json']:assert sha(D/'staged_art'/(NAME+'_Directions'+suffix))==sha(art/(NAME+'_Directions'+suffix))
        write(D/'production_before_play_20261029.json',{'at':now(),'revision':'art_r04','manifest':'installed_manifest.json','manifest_sha256':sha(D/'installed_manifest.json'),'offline_review_sha256':sha(D/'offline_review_art_r04_20261029.json'),'final_files':snapshot,'preplay_changes':changes})
        print(json.dumps({'preplay_files':len(snapshot),'changes':len(changes),'verify':True,'stage_identical':True}))
    else:raise ValueError(phase)
