"""Install reviewed local patch by replacing this character's atlas only."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, shutil, sys, time
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;H=D.parent;R=H.parents[2]
sys.path.insert(0,str(H))
from mcp_call import Client,URL
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def unwrap(v):return v.get('structuredContent') or json.loads(v['content'][0]['text'])
c=read(H/'conversation_chain.json')
assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert c['current_character']=='SlugQueen' and c['dispatch_token']=='sheep-to-slugqueen-5dd11f24cb8646d0ac5a622d232ec22d'
out=D/'local_raster_revision_02';assert not (out/'installation.json').exists()
art='Assets/_UIAssets/Monsters/Insects/SlugQueen/Directions'
atlas=art+'/SlugQueen_Directions.png'
manifest=read(D/'installed_manifest.json')
assert all(sha(R/x['path'])==x['after'].upper() for x in manifest['changes'])
baseline=read(D/'incremental_before_20261028.json')
assert all(sha(R/p)==s.upper() for p,s in baseline['protected_six'].items() if p!='Assets/Prefabs/Enemy/Enemy_SlugQueen.prefab')
for f in ['SlugQueen_Directions.layout.json','SlugQueen_Directions.sprites.json']:
    assert sha(D/'staged_art'/f)==sha(R/art/f),'Slice/layout drift: '+f
selection=read(D/'art_selection.json');assert selection['Up']=='local_raster_revision_02/Up_sheet.png'
assert sha(out/'Up_sheet.png')==read(out/'processing.json')['output_sha256']
write(out/'review.json',dict(observed_at=now(),accepted_for_install=True,user_approved=False,actually_viewed=['local_raster_revision_01/repair_preview.png','offline_Up.png (r01)','local_raster_revision_02/repair_preview.png','offline_rig_proof.png (r02)'],observation='Original ochre torso patch now visible below collar. R01 pale ring rejected; r02 one-pixel inset pigment mask removes that fringe. Crowns remain unique, rear head has no face, body lobes overlap without a gap, no new limbs or ground shadow. No additional paid request.',reviewed_preview_sha256=sha(out/'repair_preview.png'),reviewed_offline_sha256=sha(D/'offline_rig_proof.png'),selected_sheet_sha256=sha(out/'Up_sheet.png')))
client=Client();project=client.identity()
errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
probe=unwrap(client.tool('execute_code',dict(action='execute',code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};')))
assert errors['data']==[] and probe['success']
assert not any(v for k,v in probe['data']['result'].items() if k!='scene')
assert probe['data']['result']['scene']=='Assets/Scenes/Boot.unity'
for f in ['installed_manifest.json','installed_verify.txt','offline_review_20261028.json']:
    shutil.copy2(D/f,out/('preinstall_'+f))
shutil.copy2(R/atlas,out/'installed_atlas_before.png')
shutil.copy2(D/'staged_art/SlugQueen_Directions.png',R/atlas)
refresh=client.tool('refresh_unity',dict(mode='force',scope='assets',compile='none',wait_for_ready=True))
client.identity()
for attempt in range(4):
    state=client.resource('mcpforunity://editor/state');s=state['data']
    if not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']:break
    if s['advice'].get('blocking_reasons')==['stale_status']:
        client.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"SlugQueen_atlas_r02_read"});return true;'))
    time.sleep(1)
else:raise RuntimeError('Editor not ready after atlas import; inspect preserved state')
verify=unwrap(client.tool('execute_code',dict(action='execute',code='FTProject.EditorTools.EnemyDirectionSpec spec;FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("SlugQueen",out spec);string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report);var clip=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>("Assets/_UIAssets/Monsters/Insects/SlugQueen/Directions/Animations/Walk_Directions.anim");return new{pass=pass,report=report,afterFloatBindings=UnityEditor.AnimationUtility.GetCurveBindings(clip).Length};')))
assert verify['success'] and verify['data']['result']['pass'] and verify['data']['result']['afterFloatBindings']==73
changed=[x for x in manifest['changes'] if sha(R/x['path'])!=x['after'].upper()]
assert len(changed)==1 and changed[0]['path']==atlas,changed
old=changed[0]['after'];changed[0]['after']=sha(R/atlas)
manifest.setdefault('repair_history',[]).append(dict(observed_at=now(),revision=out.name,path=atlas,before=old,after=sha(R/atlas),reason='Expose original Up ochre patch below collar with clean edge',original_manifest='local_raster_revision_02/preinstall_installed_manifest.json',atlas_only=True,walk_reset_retained=True))
manifest['verification']=verify;write(D/'installed_manifest.json',manifest)
(D/'installed_verify.txt').write_text(verify['data']['result']['report'],encoding='utf-8')
alpha={}
for p in (D/'staged_art').glob('*.png'):
    a=np.asarray(Image.open(p).convert('RGBA'))
    alpha[p.name]=dict(size=list(a.shape[:2][::-1]),transparent=int((a[:,:,3]==0).sum()),opaque=int((a[:,:,3]==255).sum()),magenta_foreground=int(((a[:,:,0]>200)&(a[:,:,2]>150)&(a[:,:,1]<80)&(a[:,:,3]>128)).sum()))
assert all(x['magenta_foreground']==0 for x in alpha.values())
review=read(out/'preinstall_offline_review_20261028.json')
review.update(observed_at=now(),final_local_revision='local_raster_revision_02',local_review='local_raster_revision_02/review.json',staging_files={p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()},alpha=alpha,observation=read(out/'review.json')['observation'])
write(D/'offline_review_20261028.json',review)
write(out/'installation.json',dict(observed_at=now(),transport=URL,project=project,probe=probe,errors=errors,refresh=refresh,state=state,verify=verify,changed_paths=[atlas],before=old,after=sha(R/atlas),walk_reset_sha256=sha(R/art/'Animations/Walk_Directions.anim'),protocol_history=client.history))
write(D/'preplay_version_binding_r02_20261028.json',dict(observed_at=now(),transport=URL,installed_manifest_sha256=sha(D/'installed_manifest.json'),installed_files={x['path']:sha(R/x['path']) for x in manifest['changes']},selection=selection,local_revision_sha256=sha(out/'Up_sheet.png'),repair_sha256=sha(D/'side_reuse_repair_r01/repair.json'),runtime_revisions=['runtime_r02','runtime_updeath_r02']))
c.update(current_stage='SlugQueen_local_patch_r02_installed_pending_two_Play_rounds',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/SlugQueen/local_raster_revision_02/installation.json',updated_at=now());write(H/'conversation_chain.json',c)
print(json.dumps(dict(transport=URL,atlas_only=True,verify=True,walk_reset_preserved=True)))
