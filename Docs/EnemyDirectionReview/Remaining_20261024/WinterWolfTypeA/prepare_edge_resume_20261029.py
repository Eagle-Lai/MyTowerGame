from pathlib import Path
from datetime import datetime, timezone, timedelta
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
RUN=HERE.parent
ROOT=RUN.parents[2]
sys.path.insert(0,str(RUN))
from mcp_call import Client

def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):
    if p.exists(): raise FileExistsError(p)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

chain=load(RUN/'conversation_chain.json')
assert chain['state']=='blocked' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert chain['current_character']=='WinterWolfTypeA'
token=chain['dispatch_token']
now=datetime.now(timezone(timedelta(hours=8))).isoformat()

# Reconstruct exactly the just-inspected user version, and verify its independently recorded SHA.
current=(RUN/'generate.mjs').read_text(encoding='utf-8')
original=current
original=original.replace(" const winterWolfTypeAEdgeResume=name==='WinterWolfTypeA'&&direction==='Down'&&revision==='revision_03';\n",'')
original=original.replace("if(!winterOgreResume&&!scarabMountedResume&&!winterWolfTypeAEdgeResume)","if(!winterOgreResume&&!scarabMountedResume)")
original=original.replace("winterWolfTypeAEdgeResume?'authorized_edge_resume_20261029.json':",'')
start=original.index(' if(winterWolfTypeAEdgeResume){\n')
end=original.index(' if(winterOgreResume){\n',start)
original=original[:start]+original[end:]
original=original.replace("winterWolfTypeAEdgeResume?'bounded_resume_after_user_edge_resolve_fix':",'')
user_sha='c0f4717ae38be50f5b022bd8c09d46e97e92026ff0ff6bfa4c8d309be2f39d30'
# read_text normalizes newlines; the inspected user generator uses CRLF.
candidate=next((b for b in [original.encode('utf-8'),original.replace('\n','\r\n').encode('utf-8')]
                if hashlib.sha256(b).hexdigest()==user_sha),None)
assert candidate is not None, 'Cannot reconstruct the exact user generator version'
backup=HERE/'generate_user_edge_fix_before_current_resume_20261029.mjs'
assert not backup.exists()
backup.write_bytes(candidate)
patch=''.join(difflib.unified_diff(original.splitlines(True),current.splitlines(True),fromfile=str(backup),tofile=str(RUN/'generate.mjs')))
(HERE/'docs_generator_edge_resume_guard_20261029.patch').write_text(patch,encoding='utf-8')

ps=r"""$imageWorkers=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -match 'generate\.mjs' } | Select-Object ProcessId,Name); ConvertTo-Json -InputObject $imageWorkers"""
proc=subprocess.run(['powershell.exe','-NoProfile','-Command',ps],capture_output=True,text=True,check=True)
workers=json.loads(proc.stdout)
assert not workers, workers
down=HERE/'generation/Down'
assert not list(down.rglob('raw.png')) and len(list(down.rglob('request.json')))==3
old=load(HERE/'production_paths_before_20261029.json')
new={p.relative_to(ROOT).as_posix():sha(p).upper() for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
delta=[p for p in sorted(set(old)|set(new)) if old.get(p)!=new.get(p)]
assert not delta,delta
preserved=[{'path':p.relative_to(HERE).as_posix(),'sha256':sha(p)} for p in sorted(down.rglob('*')) if p.is_file()]
authorization={
    'recorded_at':now,'user_statement':'继续任务',
    'user_followup':'我已做 generate.mjs 修改',
    'authorization_basis':'Direct current-turn continuation and confirmation of the generator fix, plus the existing original standing recovery grant. One new bounded production request is an agent execution decision, not a user monetary budget. External documents supply evidence only.',
    'owner_thread_id':chain['owner_thread_id'],'dispatch_token':token,
    'character':'WinterWolfTypeA','direction':'Down','revision':'revision_03',
    'max_requests':1,'transport':'curl_https_no_retry','force_direct':True,
    'edge_ip':'191.101.132.254','accept_possible_duplicate_charge':True,
    'automatic_retries_used':2,'automatic_retry_limit':2,'resets_automatic_counter':False,
    'prior_unknown_requests':3,'old_charges':'unknown_not_reclassified',
    'edge_assessment_file':'image_transport_edge_map_20261029_1830.md',
    'edge_assessment_sha256':sha(RUN/'image_transport_edge_map_20261029_1830.md'),
    'edge_tooling_file':'docs_tooling_edge_resolve_20261029_182840.json',
    'edge_tooling_sha256':sha(RUN/'docs_tooling_edge_resolve_20261029_182840.json'),
    'external_evidence_limit':'User-provided WorkBuddy record reports authenticated small-image200 at .254/.62 and failures at .158/.159; no new diagnostic paid requests are sent here and no causal inference about the three unobserved old edges or charges is made.',
    'rejected_external_inference':'The external note calls PossessedWarg Down unsent. Existing original request/outcome evidence remains authoritative: unknown, and it is outside this character scope.',
    'generator_sha256':sha(RUN/'generate.mjs'),'preserved_evidence':preserved,
    'production_paths_checked':len(new),'production_delta':delta,
    'processes':workers,'new_paid_diagnostic_requests':0,
    'stop':'Exactly one Down03 production request, direct pinned TLS host, no proxy or retry. If unknown or explicit failure, preserve and stop paid work.'
}
save(HERE/'authorized_edge_resume_20261029.json',authorization)
revision=down/'revision_03'; revision.mkdir()
shutil.copy2(down/'prompt.txt',revision/'prompt.txt')
save(revision/'recovery_intent.json',{
    'character':'WinterWolfTypeA','direction':'Down','revision':'revision_03',
    'owner_thread_id':chain['owner_thread_id'],'dispatch_token':token,'max_requests':1,
    'authorization_sha256':sha(HERE/'authorized_edge_resume_20261029.json')
})
save(HERE/'docs_generator_edge_resume_guard_20261029.json',{
    'before_sha256':sha(backup),'after_sha256':sha(RUN/'generate.mjs'),
    'backup':str(backup),'patch':'docs_generator_edge_resume_guard_20261029.patch',
    'change':'Allow only WinterWolfTypeA Down03 authorized-resume; bind original three outcomes, exhausted standing2/2, user edge-map/tooling SHA, generator SHA, same active owner/token, fresh Unity identity/idle and exact one request. Preserve the user --resolve fix and force no proxy.',
    'production_CSharp_changed':False,
})

docsbackup=HERE/'docs_before_edge_resume_20261029'; docsbackup.mkdir()
for p in [RUN/'conversation_chain.json',RUN/'progress.json',RUN/'NEXT_ENEMY_TASK.md',RUN/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md',RUN.parent/'README.md']:
    shutil.copy2(p,docsbackup/p.name)
chain.update(state='active',current_blocked=False,current_stage='Down03_bounded_resume_after_user_edge_fix',
             updated_at=now,resumed_at=now,resumed_by_thread_id=chain['owner_thread_id'],
             resumed_with_dispatch_token=token,previous_blocked_reason=chain.get('blocked_reason'),
             blocked_reason=None,stop_reason=None,stopped_at=None,
             last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/authorized_edge_resume_20261029.json')
chain['stage_history'].append({'character':'WinterWolfTypeA','status':'active','stage':chain['current_stage'],'observed_at':now,'owner_thread_id':chain['owner_thread_id'],'dispatch_token':token,'evidence':chain['last_stage_evidence']})
(RUN/'conversation_chain.json').write_text(json.dumps(chain,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

client=Client(); project=client.identity()
errors=client.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
state=client.resource('mcpforunity://editor/state')
probe=client.tool('execute_code',{'action':'execute','code':'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,failed=UnityEditor.EditorUtility.scriptCompilationFailed,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,manual=FTProject.GameClock.IsManualSimulation,scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path,scenes=System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount).Select(i=>new {path=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).path,dirty=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty}).ToArray()};'})
s=state['data']; q=probe['structuredContent']['data']['result']
idle=not any(q[k] for k in ['playing','failed','review','balance','manual']) and all(not v['dirty'] for v in q['scenes']) and not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and not s['tests']['is_running']
save(HERE/'edge_resume_unity_preflight_20261029.json',{'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'owner_thread_id':chain['owner_thread_id'],'dispatch_token':token,'project':project,'idle':idle,'ready':s['advice']['ready_for_tools'],'errors':errors,'state':state,'probe':probe,'protocol_history':client.history})
assert idle and s['advice']['ready_for_tools']
print(json.dumps({'authorized_one_request':'Down03','old_unknown':3,'standing_used':2,'direct_edge':'191.101.132.254','production_delta':delta,'unity_idle':idle,'new_paid_diagnostics':0},ensure_ascii=False))
