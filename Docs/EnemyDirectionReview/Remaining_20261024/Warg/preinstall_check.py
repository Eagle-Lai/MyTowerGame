from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib,json,sys
D=Path(__file__).resolve().parent;BASE=D.parent;ROOT=BASE.parents[2]
sys.path.insert(0,str(BASE))
from mcp_call import Client
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
chain=json.loads((BASE/'conversation_chain.json').read_text(encoding='utf-8'))
assert chain['state']=='active' and chain['owner_thread_id']=='01a1830c-598a-7473-8ee1-01bccdd1f9be' and chain['current_character']=='Warg'
assert not (D/'installed_manifest.json').exists()
b=json.loads((D/'incremental_before_20261028.json').read_text(encoding='utf-8'))
six={p:sha(ROOT/p) for p in b['protected_six']}
assert six==b['protected_six'],'Source drift'
c=Client();project=c.identity()
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
state=c.resource('mcpforunity://editor/state')
probe=c.tool('execute_code',{'action':'execute','code':'return new { playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode, compiling=UnityEditor.EditorApplication.isCompiling, failed=UnityEditor.EditorUtility.scriptCompilationFailed, updating=UnityEditor.EditorApplication.isUpdating, scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path, sceneCount=UnityEngine.SceneManagement.SceneManager.sceneCount, dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty, balance=FTProject.EditorTools.BalancePlayModeVerifier.Running, recording=FTProject.EditorTools.BalanceVideoRecorder.Running, review=FTProject.EditorTools.EnemyDirectionBatchReview.Running, manual=FTProject.GameClock.IsManualSimulation };'})
v=probe.get('structuredContent') or json.loads(probe['content'][0]['text']);p=v['data']['result']
assert not any(p[k] for k in ['playing','compiling','failed','updating','dirty','balance','recording','review','manual']),p
assert p['scene']=='Assets/Scenes/Boot.unity' and p['sceneCount']==1,p
e=errors.get('structuredContent') or json.loads(errors['content'][0]['text'])
assert not e.get('data'),e
record={'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'project':project,'six_match':True,'protected_six':six,'probe':p,'state':state,'errors':errors,'protocol_history':c.history}
(D/'preinstall_verified_20261028.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'project':project,'six_match':True,'probe':p,'errors':e},ensure_ascii=False))
