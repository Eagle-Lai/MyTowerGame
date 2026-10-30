from pathlib import Path
from datetime import datetime, timezone
import sys, json, hashlib, shutil

D = Path(__file__).resolve().parent
HERE = D.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from mcp_call import Client

out = D / 'repair_controller_r01'
if out.exists():
    raise ValueError('Preserve existing repair evidence; do not repeat')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
previous = json.loads((D / 'installed_manifest.json').read_text(encoding='utf-8'))
for c in previous['changes']:
    if sha(ROOT / c['path']) != c['after']:
        raise ValueError('Installed asset drift: ' + c['path'])
c = Client()
identity = c.identity()
def unwrap(result):
    v = result.get('structuredContent') or json.loads(result['content'][0]['text'])
    if not v.get('success'): raise ValueError(str(v))
    return v
state = unwrap(c.tool('execute_code', {'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,updating=UnityEditor.EditorApplication.isUpdating,failed=UnityEditor.EditorUtility.scriptCompilationFailed,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty};'}))['data']['result']
if any(state.values()): raise ValueError('Editor occupied: ' + str(state))
art = ROOT / 'Assets/_UIAssets/Monsters/Horses/Pony/Directions'
paths = [ROOT/'Assets/Prefabs/Enemy/Enemy_Pony.prefab', ROOT/'Assets/Prefabs/Enemy/Enemy_Pony.prefab.meta'] + [p for p in art.rglob('*') if p.is_file()]
before = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
out.mkdir()
for p in paths:
    dest = out/'before'/p.relative_to(ROOT)
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(p,dest)
shutil.copy2(D/'installed_manifest.json',out/'previous_manifest.json')
code = (HERE/'Horse/repair_controller_r01/repair_code.txt').read_text(encoding='utf-8').replace('Horses/Horse/', 'Horses/Pony/').replace('Horse_Directions', 'Pony_Directions').replace('TryGetSpec("Horse"', 'TryGetSpec("Pony"')
(out/'repair_code.txt').write_text(code,encoding='utf-8')
result = unwrap(c.tool('execute_code',{'action':'execute','code':code}))
after = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
manifest = {'name':'Pony','revision':'repair_controller_r01','at':datetime.now(timezone.utc).isoformat(),'project':identity,'reason':'Builder mapped distinct source Run to Walk. Pony-only Run state now references its copied Run with vertical gait, preserving source curves/events/duration. No shared C# changed.','changes':[{'path':p,'before':before.get(p),'after':h} for p,h in after.items()],'verification':result,'protocol_history':c.history}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'verify.txt').write_text(result['data']['result']['report'],encoding='utf-8')
if not result['data']['result']['pass']:raise ValueError('Repair Verify failed')
print(json.dumps({'name':'Pony','revision':'repair_controller_r01','verify':True,'modified':[p for p in after if after[p]!=before[p]]}))
