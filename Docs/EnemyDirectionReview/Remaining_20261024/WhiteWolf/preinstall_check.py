"""Check the active WhiteWolf owner, source protection, staged r04 and live idle editor."""
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
assert chain['state'] == 'active' and chain['current_character'] == 'WhiteWolf'
assert chain['owner_thread_id'] == '01a183d9-2ad7-73d2-b736-3057ef92f215'
assert os.environ.get('CODEX_THREAD_ID') == chain['owner_thread_id']
assert chain['dispatch_token'] == 'watchdog-to-whitewolf-20261029_024758-616f3dd3-f8a9-4ec4-b44b-f70f383f1fbf'
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
fresh = c.tool('execute_code', {'action':'execute','code':'var t=System.Linq.Enumerable.FirstOrDefault(System.Linq.Enumerable.Select(System.AppDomain.CurrentDomain.GetAssemblies(),a=>a.GetType("MCPForUnity.Editor.Services.EditorStateCache")),x=>x!=null); if(t==null)throw new System.Exception("Editor state cache type unavailable"); var m=t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic); if(m==null)throw new System.Exception("Cache refresh method unavailable"); m.Invoke(null,new object[]{"WhiteWolf factual preinstall snapshot"}); return true;'})
assert data(fresh)['data']['result'] is True
state = c.resource('mcpforunity://editor/state')
assert state['data']['advice']['ready_for_tools']
assert not state['data']['compilation']['is_compiling']
assert not state['data']['compilation']['is_domain_reload_pending']
assert not state['data']['assets']['is_updating']
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
          'observations':'Actually viewed final r04 composite and all 14 cleaned slices. Shaggy ivory and gray wolf retains broad ochre spots, upright pointed ears, golden eyes, long muzzle, ivory fangs and curved bushy tail; no collar or equipment. Up uses one faceless rear head for all three expressions, with heel pads facing viewer. Down has stern normal, open-jaw angry and pale-eyed slack tongue-out death heads. Four paws in each direction remain visible and attached, shoulder/hip caps and tail roots buried behind body/head. Earlier local layout revisions preserved; r04 fills 361 tiny enclosed chroma-key pixels and removes 164 residual spill pixels across the 14 slices. Successful raw images remain unchanged.',
          'offline_visual_pass':True,'runtime_visual_review':'pending','user_approved':False,
          'staged_files':final_art,'reviewed_image_hashes':{p:sha(D/p) for p in ['offline_rig_proof.png','parts_clean_final.png']}}
(D/'staged_visual_review_r04.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
progress = read(H/'progress.json')
item = next(i for i in progress['items'] if i['name']=='WhiteWolf')
assert item['status'] == 'staged_pending_visual_check'
item.update(stage='offline_art_r04_reviewed_pending_install',final_revision='art_r04',staged_visual_review='WhiteWolf/staged_visual_review_r04.json')
progress.update(current='WhiteWolf',updated_at=report['observed_at'])
(H/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'project':project,'protected_six_match':True,'staged_revision':'art_r04','probe':probe,'errors':data(errors)['data']},ensure_ascii=False))
