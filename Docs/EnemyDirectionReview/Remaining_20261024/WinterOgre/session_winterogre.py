from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, subprocess, sys, time

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
NAME = 'WinterOgre'
OWNER = '01a18619-6aa0-7a31-ac62-10a82077950b'
TOKEN = 'winterboar-to-winterogre-20261029_131318-14b528b1-8990-455f-8069-d7ea49019046'
sys.path.insert(0, str(H))
from mcp_call import Client

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def now(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def owner():
    c = read(H/'conversation_chain.json')
    assert c['state']=='active' and c['owner_thread_id']==OWNER and c['current_character']==NAME and c['dispatch_token']==TOKEN
    assert os.environ.get('CODEX_THREAD_ID') == OWNER
    return c
def write(p, value, fresh=False):
    owner()
    p = Path(p)
    if fresh: assert not p.exists(), str(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def stage(status, evidence):
    c = owner()
    c.update(current_stage=status,last_stage_evidence=str(evidence),updated_at=now())
    write(H/'conversation_chain.json',c)
def result(v):
    v = v.get('structuredContent') or json.loads(v['content'][0]['text'])
    assert v.get('success'),v
    data = v.get('data',{}).get('result',v.get('data'))
    return json.loads(data) if isinstance(data,str) else data
def run(script,*args):
    owner()
    subprocess.run([sys.executable,str(H/script),*args],check=True,cwd=ROOT)
def snapshot():
    return {p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
def probe(c):
    return result(c.tool('execute_code',{'action':'execute','code':'return Newtonsoft.Json.JsonConvert.SerializeObject(new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,scenes=System.Linq.Enumerable.Select(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>new {path=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).path,dirty=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty}).ToArray(),balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation});'}))
def idle(p):
    assert not any(p[k] for k in ['playing','compiling','failed','updating','balance','recording','review','manual']),p
    assert p['scenes']==[{'path':'Assets/Scenes/Boot.unity','dirty':False}],p
