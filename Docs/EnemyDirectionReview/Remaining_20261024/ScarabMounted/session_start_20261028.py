"""ScarabMounted serial recovery: preserve current baseline and perform read-only preflight."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, subprocess, sys

D=Path(__file__).resolve().parent
HERE=D.parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
from mcp_call import Client
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
def now(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
def unwrap(v): return v.get('structuredContent') or json.loads(v['content'][0]['text'])
def owner():
    c=read(HERE/'conversation_chain.json')
    assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID']
    assert c['current_character']=='ScarabMounted' and c['dispatch_token']=='scarab-to-scarabmounted-dd3da45145854f44998a5b6bdc48d12e'
    return c
chain=owner()
assert not (D/'installed_manifest.json').exists()
assessment=read(HERE/'Scarab/successor_recovery_assessment_20261028_122652.json')
protected=assessment['protected_six']
assert all(sha(ROOT/p)==s for p,s in protected.items()), 'Protected source or battle drift'
assert all(sha(D/p)==s for p,s in assessment['preserved_evidence'].items()), 'Prepared evidence drift'
assert read(D/'generation/Up/result.json')['status']==402 and not (D/'generation/Up/raw.png').exists()
assert not (D/'generation/Down/request.json').exists()
processes=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',"@(Get-CimInstance Win32_Process | Where-Object { $_.Name -in @('Unity.exe','node.exe','python.exe') } | Select-Object ProcessId,Name,@{n='generation';e={$_.CommandLine -match 'generate\\.mjs'}},@{n='runtime';e={$_.CommandLine -match '(runtime_runner|start_runtime|finish_runtime)'}},@{n='balance';e={$_.CommandLine -match 'balance_pipeline'}}) | ConvertTo-Json -Depth 3"],encoding='utf-8-sig'))
assert not any(x['generation'] or x['runtime'] or x['balance'] for x in processes)
base=D/'incremental_before_recovery_20261028.json'
assert not base.exists(), 'Inspect existing baseline before retry'
files={p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
status=subprocess.check_output(['git','status','--short'],cwd=ROOT,encoding='utf-8')
(D/'git_status_before_recovery_20261028.txt').write_text(status,encoding='utf-8')
write(base,dict(observed_at=now(),owner_thread_id=chain['owner_thread_id'],dispatch_token=chain['dispatch_token'],file_count=len(files),files=files,protected_six=protected,processes=processes,rule_path_discrepancy='Root AGENTS has old FreedomTower_1/D path; explicit task and live identity E:/MyTowerGame authoritative',legacy_audit='scope_Scarab_20261028_final.json'))
c=Client();project=c.identity()
errors=unwrap(c.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
state=c.resource('mcpforunity://editor/state')
probe=unwrap(c.tool('execute_code',dict(action='execute',code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,updating=UnityEditor.EditorApplication.isUpdating,failed=UnityEditor.EditorUtility.scriptCompilationFailed,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,scenes=System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount).Select(i=>new {path=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).path,dirty=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty}).ToArray()};')))
assert probe['success']; live=probe['data']['result']
assert not any(v for k,v in live.items() if k!='scenes') and all(not x['dirty'] for x in live['scenes']),live
assert errors['success'] and errors['data']==[],errors
write(D/'preflight_recovery_20261028.json',dict(observed_at=now(),project=project,state=state,errors=errors,probe=probe,protocol_history=c.history))
revision=D/'generation/Up/revision_01';revision.mkdir()
(revision/'prompt.txt').write_bytes((D/'generation/Up/prompt.txt').read_bytes())
write(revision/'recovery_intent.json',dict(observed_at=now(),character='ScarabMounted',direction='Up',revision='revision_01',owner_thread_id=chain['owner_thread_id'],dispatch_token=chain['dispatch_token'],max_requests=1,parent_request_sha256=sha(D/'generation/Up/request.json').lower(),parent_result_sha256=sha(D/'generation/Up/result.json').lower(),reason='Original Up explicit HTTP402 with no raw; same-service Scarab Up revision_01 and Down revision_02 subsequently HTTP200. One bounded formal recovery using original references; no guarantee of current balance.',recent_success=assessment['recent_same_service_success'],assessment_sha256=sha(HERE/'Scarab/successor_recovery_assessment_20261028_122652.json')))
p=read(HERE/'progress.json');item=next(x for x in p['items'] if x['name']=='ScarabMounted')
item.update(recovery_in_progress=True,recovery_stage='preflight_complete_up_fresh_revision_intent_prepared',recovery_started_at=now(),recovery_baseline='ScarabMounted/'+base.name)
p['current']='ScarabMounted';p['updated_at']=now();write(HERE/'progress.json',p)
chain.update(current_stage='ScarabMounted_recovery_preflight_complete',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/ScarabMounted/preflight_recovery_20261028.json',updated_at=now());write(HERE/'conversation_chain.json',chain)
print(json.dumps(dict(baseline_files=len(files),protected_drift=[],project=project,live=live,revision='Up/revision_01',paid_requests=0),ensure_ascii=False))
