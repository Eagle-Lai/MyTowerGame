"""Verify the live MyTowerGame editor via its existing 8088 MCP endpoint."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json, os, sys, time

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D.parent))
from mcp_call import Client, URL

def unwrap(v):
    return v.get('structuredContent') or json.loads(v['content'][0]['text'])

def result(v):
    r = unwrap(v)['data']['result']
    return json.loads(r) if isinstance(r, str) else r

chain = json.loads((D.parent / 'conversation_chain.json').read_text(encoding='utf-8-sig'))
assert chain['state'] == 'active' and chain['current_character'] == 'WildGoat'
assert chain['owner_thread_id'] == os.environ.get('CODEX_THREAD_ID') == '01a1841b-d4fc-7eb2-9ace-b66dc688e0c2'
output = D / 'unity_release_post_r02_20261029.json'
assert not output.exists(), 'Keep earlier final verification; inspect before retrying'
c = Client()
report = {'observed_at': datetime.now(timezone(timedelta(hours=8))).isoformat(), 'transport': URL}
try:
    report['project'] = c.identity()
    report['initial_errors'] = c.tool('read_console', {'action': 'get', 'types': ['error'], 'count': '50', 'format': 'json'})
    initial = c.resource('mcpforunity://editor/state')['data']
    assert not initial['editor']['play_mode']['is_playing'] and not initial['tests']['is_running']
    assert initial['advice']['ready_for_tools']
    report['refresh'] = c.tool('refresh_unity', {'mode': 'force', 'scope': 'all', 'compile': 'request', 'wait_for_ready': True})
    time.sleep(2)
    report['project_after_refresh'] = c.identity()
    for attempt in range(30):
        state = c.resource('mcpforunity://editor/state')['data']
        if (not state['compilation']['is_compiling'] and not state['compilation']['is_domain_reload_pending']
                and not state['assets']['is_updating'] and state['advice']['ready_for_tools']):
            break
        time.sleep(2)
    else:
        raise RuntimeError('Editor did not become idle within the bounded wait')
    report['cache_refresh'] = c.tool('execute_code', {'action': 'execute', 'code': 'var t=System.Linq.Enumerable.FirstOrDefault(System.Linq.Enumerable.Select(System.AppDomain.CurrentDomain.GetAssemblies(),a=>a.GetType("MCPForUnity.Editor.Services.EditorStateCache")),x=>x!=null);if(t==null)throw new System.Exception("Editor state cache type unavailable");var m=t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic);if(m==null)throw new System.Exception("Cache refresh method unavailable");m.Invoke(null,new object[]{"WildGoat factual final snapshot"});return true;'})
    report['state'] = c.resource('mcpforunity://editor/state')
    probe = 'return new {projectRoot=System.IO.Path.GetFullPath(System.IO.Path.Combine(UnityEngine.Application.dataPath,"..")),unityVersion=UnityEngine.Application.unityVersion,playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path,sceneCount=UnityEngine.SceneManagement.SceneManager.sceneCount,sceneDirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation};'
    report['live_probe_response'] = c.tool('execute_code', {'action': 'execute', 'code': probe})
    report['live_probe'] = result(report['live_probe_response'])
    sprite_probe = 'var path="Assets/_UIAssets/Monsters/Cattle/WildGoat/Directions/WildGoat_Directions.png";var importer=UnityEditor.AssetImporter.GetAtPath(path) as UnityEditor.TextureImporter;if(importer==null)throw new System.Exception("WildGoat atlas importer missing");var sprites=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.OfType<UnityEngine.Sprite>(UnityEditor.AssetDatabase.LoadAllAssetsAtPath(path)));return new {spriteMode=importer.spriteImportMode.ToString(),ppu=importer.spritePixelsPerUnit,alphaIsTransparency=importer.alphaIsTransparency,mipmaps=importer.mipmapEnabled,spriteCount=sprites.Length,sprites=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(System.Linq.Enumerable.OrderBy(sprites,s=>s.name),s=>new {name=s.name,ppu=s.pixelsPerUnit,x=s.rect.x,y=s.rect.y,w=s.rect.width,h=s.rect.height,pivotX=s.pivot.x,pivotY=s.pivot.y}))};'
    report['sprite_imports_response'] = c.tool('execute_code', {'action': 'execute', 'code': sprite_probe})
    report['sprite_imports'] = result(report['sprite_imports_response'])
    report['errors_response'] = c.tool('read_console', {'action': 'get', 'types': ['error'], 'count': '50', 'format': 'json'})
    report['errors'] = unwrap(report['errors_response'])
    live = report['live_probe']
    assert live['projectRoot'].replace('\\', '/').lower() == 'e:/mytowergame'
    assert live['unityVersion'] == '2022.3.62f3c1'
    assert live['scene'] == 'Assets/Scenes/Boot.unity' and live['sceneCount'] == 1
    assert not any(live[k] for k in ['playing', 'compiling', 'failed', 'updating', 'sceneDirty', 'balance', 'recording', 'review', 'manual'])
    assert report['sprite_imports']['spriteCount'] == 14
    assert report['errors']['success'] and report['errors']['data'] == []
    state = report['state']['data']
    assert state['advice']['ready_for_tools'] and not state['tests']['is_running']
    assert not state['compilation']['is_domain_reload_pending'] and not state['assets']['external_changes_dirty']
    report['success'] = True
except Exception as exc:
    report['success'] = False
    report['error'] = str(exc)
finally:
    report['protocol_history'] = c.history
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: report.get(k) for k in ['success', 'error', 'transport', 'project', 'live_probe', 'errors']}, ensure_ascii=False))
if not report['success']:
    raise SystemExit(1)
