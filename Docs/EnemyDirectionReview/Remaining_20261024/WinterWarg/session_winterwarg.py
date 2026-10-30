from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, subprocess, sys

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
NAME = 'WinterWarg'
OWNER = '01a186cb-e01e-72b2-ad8b-f5a5b86bfd1f'
TOKEN = 'winterogre-to-winterwarg-20261029_163224-4c489e91-3117-4716-a1e2-87af74077d40'
sys.path.insert(0, str(H))
from mcp_call import Client

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def now(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest().upper()
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
