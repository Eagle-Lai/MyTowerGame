from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, sys
D=Path(__file__).resolve().parent
H=D.parent
ROOT=H.parents[2]
sys.path.insert(0,str(H))
from mcp_call import Client
NAME='Rooster'
TOKEN='redscorpion-to-rooster-64fbbeeea5ba4bbfaa560ffa59b0dcf4'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
now=lambda:datetime.now(timezone(timedelta(hours=8))).isoformat()
unwrap=lambda r:r.get('structuredContent') or json.loads(r['content'][0]['text'])
def owner():
    c=read(H/'conversation_chain.json')
    assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID']
    assert c['current_character']==NAME and c['dispatch_token']==TOKEN
    return c
def available(c):
    project=c.identity()
    errors=unwrap(c.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
    state=c.resource('mcpforunity://editor/state')
    code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};'
    probe=unwrap(c.tool('execute_code',dict(action='execute',code=code)))['data']['result']
    assert not any(v for k,v in probe.items() if k!='scene'),probe
    s=state['data']
    assert s['advice']['ready_for_tools'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating']
    return dict(observed_at=now(),project=project,state=state,probe=probe,errors=errors,protocol_history=c.history)
