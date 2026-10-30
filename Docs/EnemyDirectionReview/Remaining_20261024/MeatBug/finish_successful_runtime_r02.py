from pathlib import Path
import json,sys,hashlib
base=Path('Docs/EnemyDirectionReview/Remaining_20261024').resolve();d=base/'MeatBug';sys.path.insert(0,str(base));from mcp_call import Client
c=Client();c.identity()
r=c.tool('execute_code',{'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,recorder=FTProject.EditorTools.BalanceVideoRecorder.Running,compiling=UnityEditor.EditorApplication.isCompiling,updating=UnityEditor.EditorApplication.isUpdating,compilationFailed=UnityEditor.EditorUtility.scriptCompilationFailed,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty};'})
v=r.get('structuredContent') or json.loads(r['content'][0]['text']);assert v.get('success') and not any(v['data']['result'].values()),v
(d/'runtime_updeath_r01_returned.json').write_text(json.dumps({'state':v,'protocol_history':c.history},ensure_ascii=False,indent=2),encoding='utf-8')
for rev in ['runtime_r02','runtime_updeath_r01']:
 p=d/rev;assert not (p/'exception.txt').exists();checks=(p/'actual_runtime_checks.txt').read_text(encoding='utf-8');assert checks.count('PASS ')==84 and checks.count('FAIL ')==0
script=base/'finish_runtime.py';source=script.read_text(encoding='utf-8').replace("'runtime_r01'","'runtime_r02'").replace('runtime_r01/actual_frames.jsonl','runtime_r02/actual_frames.jsonl')
(d/'finish_runtime_r02_source.py').write_text(source,encoding='utf-8')
sys.argv=[str(script),'MeatBug'];exec(compile(source,str(script),'exec'),{'__name__':'__main__','__file__':str(script)})
p=base/'progress.json';progress=json.loads(p.read_text(encoding='utf-8'));assert progress['current']=='MeatBug';item=next(i for i in progress['items'] if i['name']=='MeatBug');item.update(status='runtime_complete_pending_visual_check',runtime_repair='runtime_r01 failed with original null side head reference; repair_02; successful replacement runtime_r02 retained separately');p.write_text(json.dumps(progress,ensure_ascii=False,indent=2),encoding='utf-8')