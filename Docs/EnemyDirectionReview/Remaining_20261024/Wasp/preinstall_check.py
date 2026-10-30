from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys
D=Path(__file__).resolve().parent;H=D.parent;ROOT=H.parents[2]
sys.path.insert(0,str(H))
from mcp_call import Client
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
chain=json.loads((H/'conversation_chain.json').read_text(encoding='utf-8'))
assert chain['state']=='active' and chain['owner_thread_id']=='01a1833c-f96c-74a1-b7f2-2281f6ab321d' and chain['current_character']=='Wasp'
assert chain['dispatch_token']=='warg-to-wasp-20261028_235853-1e651dcf-1586-4ebc-9926-3b8be7348e7d' and os.environ.get('CODEX_THREAD_ID')==chain['owner_thread_id']
assert not (D/'installed_manifest.json').exists()
b=json.loads((D/'incremental_before_20261029.json').read_text(encoding='utf-8'))
six={p:sha(ROOT/p) for p in b['protected_six']}
assert six==b['protected_six'], 'Source drift'
c=Client();project=c.identity()
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
state=c.resource('mcpforunity://editor/state')
probe=c.tool('execute_code',{'action':'execute','code':'return new { playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode, compiling=UnityEditor.EditorApplication.isCompiling, failed=UnityEditor.EditorUtility.scriptCompilationFailed, updating=UnityEditor.EditorApplication.isUpdating, scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path, sceneCount=UnityEngine.SceneManagement.SceneManager.sceneCount, dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty, balance=FTProject.EditorTools.BalancePlayModeVerifier.Running, recording=FTProject.EditorTools.BalanceVideoRecorder.Running, review=FTProject.EditorTools.EnemyDirectionBatchReview.Running, manual=FTProject.GameClock.IsManualSimulation };'})
data=lambda r:r.get('structuredContent') or json.loads(r['content'][0]['text'])
p=data(probe)['data']['result']
assert not any(p[k] for k in ['playing','compiling','failed','updating','dirty','balance','recording','review','manual']),p
assert p['scene']=='Assets/Scenes/Boot.unity' and p['sceneCount']==1,p
assert not data(errors).get('data'),data(errors)
report={'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'project':project,'six_match':True,'protected_six':six,'probe':p,'state':state,'errors':errors,'protocol_history':c.history}
(D/'preinstall_verified_20261029.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
review={'revision':'staged_refinement_r02','reviewed_images':['reference/Wasp.png','reference/source_prefab_offline.png','staged_refinement_r02/offline_rig_proof.png','staged_refinement_r02/parts_clean.png','offline_wing_joints_r02.png','parts_clean_registered_r02.png'],
 'observations':'Both Up and Down raised/lowered poses actually inspected. Golden amber head, long paired antennae, dark abdomen stripes and cream veined wings preserve source identity. Up is a plain back head with no eyes or mouth. Wing poses share the same root and canvas; both tips stay attached and partly occluded by torso/head. r01 magenta edge remnants and exposed Up collar were rejected; r02 removes only magenta spill and moves the back head in front of collar. Source pixels and successful paid raw remain unchanged. No ground shadow or detached feet. Two wing renderers represent two wings, not four.',
 'offline_visual_pass':True,'runtime_visual_review':'pending','user_approved':False,
 'staged_files':{p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()}}
(D/'staged_visual_review_r02.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
progress=json.loads((H/'progress.json').read_text(encoding='utf-8'))
item=next(i for i in progress['items'] if i['name']=='Wasp')
assert item['status']=='reference_prepared'
item.update(status='staged_pending_visual_check',stage='offline_r02_reviewed_pending_install',staged_visual_review='Wasp/staged_visual_review_r02.json')
progress.update(current='Wasp',updated_at=report['observed_at'])
(H/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'project':project,'six_match':True,'probe':p,'errors':data(errors)},ensure_ascii=False))
