"""Check the active Watchdog owner, source protection, staged r04 and live idle editor."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
sys.path.insert(0, str(H))
from mcp_call import Client

read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
chain = read(H/'conversation_chain.json')
assert chain['state'] == 'active' and chain['current_character'] == 'Watchdog'
assert chain['owner_thread_id'] == '01a18379-8413-7bb3-bbc3-e0e5b2544d59'
assert os.environ.get('CODEX_THREAD_ID') == chain['owner_thread_id']
assert chain['dispatch_token'] == 'wasp-to-watchdog-20261029_010456-a6f96d67-324e-4b30-9ff0-555b83354188'
assert not (D/'installed_manifest.json').exists()
assert not (D/'preinstall_verified_20261029.json').exists()
b = read(D/'incremental_before_20261029.json')
six = {p: sha(ROOT/p) for p in b['protected_six']}
assert six == b['protected_six'], 'Protected source drift'
final_art = read(D/'staged_art_r04/manifest.json')['final_art']
assert all(sha(D/'staged_art'/p) == v for p, v in final_art.items())

def data(r):
    v = r.get('structuredContent') or json.loads(r['content'][0]['text'])
    assert v.get('success'), v
    return v

c = Client()
project = c.identity()
errors = c.tool('read_console', {'action':'get','types':['error'],'count':'50','format':'json'})
state = c.resource('mcpforunity://editor/state')
response = c.tool('execute_code', {'action':'execute','code':'return Newtonsoft.Json.JsonConvert.SerializeObject(new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,scenes=System.Linq.Enumerable.Select(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>new {path=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).path,dirty=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty}).ToArray(),balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation});'})
probe = data(response)['data']['result']
if isinstance(probe, str): probe = json.loads(probe)
assert not any(probe[k] for k in ['playing','compiling','failed','updating','balance','recording','review','manual']), probe
assert probe['scenes'] == [{'path':'Assets/Scenes/Boot.unity','dirty':False}], probe
assert not data(errors)['data'], data(errors)
assert not state['data']['tests']['is_running']
report = {'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),
          'owner_thread_id':chain['owner_thread_id'],'dispatch_token':chain['dispatch_token'],
          'project':project,'six_match':True,'protected_six':six,'probe':probe,
          'state':state,'errors':errors,'protocol_history':c.history}
(D/'preinstall_verified_20261029.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
review = {'revision':'art_r04','reviewed_images':['offline_rig_proof.png','parts_clean_final.png'],
          'observations':'Actually viewed final r04 composite and all 14 cleaned slices. Dark olive-brown spotted dog retains folded ears, ivory fangs, gold collar with ivory conical spikes on the head and a tiny wedge tail. Up is a faceless rear head with rear heel pads. Four paws per direction connect behind body/head, far paws remain visible, hip caps are buried and tail root occluded. Collar covers neck. Earlier r01/r02 exposed caps and hidden feet were corrected in r03; r04 removes eight residual chroma edge pixels. No enclosed alpha holes in any slice; successful raw images are unchanged.',
          'offline_visual_pass':True,'runtime_visual_review':'pending','user_approved':False,
          'staged_files':final_art,'reviewed_image_hashes':{p:sha(D/p) for p in ['offline_rig_proof.png','parts_clean_final.png']}}
(D/'staged_visual_review_r04.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
progress = read(H/'progress.json')
item = next(i for i in progress['items'] if i['name']=='Watchdog')
assert item['status'] == 'staged_pending_visual_check'
item.update(stage='offline_art_r04_reviewed_pending_install',final_revision='art_r04',staged_visual_review='Watchdog/staged_visual_review_r04.json')
progress.update(current='Watchdog',updated_at=report['observed_at'])
(H/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'project':project,'protected_six_match':True,'staged_revision':'art_r04','probe':probe,'errors':data(errors)['data']},ensure_ascii=False))
