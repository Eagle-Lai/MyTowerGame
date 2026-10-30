from pathlib import Path
from PIL import Image,ImageDraw
from datetime import datetime,timezone,timedelta
import hashlib,json,os,sys,re
import numpy as np
D=Path(__file__).resolve().parent;H=D.parent;R=H.parents[2];A=D/'staged_art';name='VolcanoParasite'
sys.path.insert(0,str(H));from mcp_call import Client
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
def unwrap(v):
    v=v.get('structuredContent') or json.loads(v['content'][0]['text']);assert v.get('success'),v;return v
c=read(H/'conversation_chain.json');assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']==name
baseline=read(D/'incremental_before_20261028.json');current={p.relative_to(R).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (R/folder).rglob('*') if p.is_file()}
diff=[{'path':p,'before':baseline['files'].get(p),'after':current.get(p)} for p in sorted(set(baseline['files'])|set(current)) if baseline['files'].get(p)!=current.get(p)]
assert not diff,diff
parts={}
for p in list(A.glob('Up_*.png'))+list(A.glob('Down_*.png')):
    im=Image.open(p);a=np.asarray(im).astype(np.int16);assert im.mode=='RGBA' and (a[:,:,3]==0).any() and (a[:,:,3]>0).any()
    pad=Image.new('L',(im.width+2,im.height+2),255);pad.paste(Image.fromarray(np.where(a[:,:,3]==0,255,0).astype('uint8')),(1,1));ImageDraw.floodfill(pad,(0,0),127);holes=int((np.asarray(pad)[1:-1,1:-1]==255).sum());assert holes==0,(p,holes)
    magenta=int(((a[:,:,0]>a[:,:,1]+45)&(a[:,:,2]>a[:,:,1]+45)&(a[:,:,3]>128)).sum());assert magenta==0,(p,magenta)
    parts[p.name]={'sha256':sha(p),'mode':im.mode,'size':list(im.size),'enclosed_alpha_holes':holes,'opaque_magenta_pixels':magenta}
assert len(parts)==12
manifest=read(A/(name+'_Directions.sprites.json'));assert len(manifest['sprites'])==12 and manifest['ppu']==100
layout=read(A/(name+'_Directions.layout.json'));assert layout['motionKind']=='crawler' and all(v==0 for v in layout['anatomy'].values())
client=Client();project=client.identity();errors=unwrap(client.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'}));state=client.resource('mcpforunity://editor/state')
probe=unwrap(client.tool('execute_code',{'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};'}))['data']['result']
assert errors['data']==[] and not any(v for k,v in probe.items() if k!='scene'),probe
assert state['data']['advice']['ready_for_tools'] and not state['data']['compilation']['is_domain_reload_pending']
assert not (D/'installed_manifest.json').exists()
report={'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'project':project,'live_probe':probe,'state':state,'errors':errors,'project_changes_before_install':diff,'staged_art':{p.name:sha(p) for p in A.iterdir() if p.is_file()},'parts':parts,'visual_review':{'viewed':['offline_rig_proof.png','parts_clean.png','staged_art/Down_HeadAngry.png'],'finding':'Four attached progressively smaller sections, dark curved spikes, plain Up rear cranium, tooth rows in Down face. Initial multi-section Body composition rejected and retained. Nonfacial single dorsal cutouts deliberately shared as recorded, no invented limbs.','raw_selection':read(D/'art_selection.json'),'alpha_filled_pixels':11,'user_approved':False},'source_contract':{'Ready':{'duration':.6666667,'loop':True,'float_bindings':15},'Walk':{'duration':.5,'loop':True,'float_bindings':18},'Attack':{'duration':.5,'loop':False,'float_bindings':33,'event':'Event(Attack) at 0.366666675'},'Death':{'duration':.5,'loop':False,'float_bindings':27,'event':'SetHead(1) at 0; preserve original actual event rather than assume generic 2'},'all_pptr_curves':0,'parameters':['Attack:Trigger','Action:Bool','State:Int','Speed:Float']},'protocol_history':client.history}
out=D/'preinstall_review_20261028.json';assert not out.exists();out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
c.update(current_stage='staged_reviewed_pending_single_character_install',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/VolcanoParasite/preinstall_review_20261028.json');(H/'conversation_chain.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'preinstall_pass':True,'parts':len(parts),'project_changes':len(diff),'live':probe}))
