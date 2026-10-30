"""Resume the existing serial owner under the user's new standing authorization."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,os
D=Path(__file__).resolve().parent; HERE=D.parent; ROOT=HERE.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
chain=read(HERE/'conversation_chain.json'); owner=os.environ['CODEX_THREAD_ID']
assert chain['owner_thread_id']==owner=='01a18093-7687-7313-aaba-7419090cc829'
assert chain['dispatch_token']=='sabretoothtiger-to-scarab-a14cefa3c87b4f9187c899d88ead8c0c' and chain['current_character']=='Scarab'
assert chain['state']=='blocked'
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
policy_path=HERE/'standing_network_recovery_authorization_20261028.json'
assert not policy_path.exists()
policy=dict(schema_version=1,chain_id=chain['chain_id'],recorded_at=stamp,user_statement='继续任务。后续同样的情况，不再需要我确认，可以继续静默执行',source='Direct user reply to the prior closeout requiring a decision accepting possible duplicate charge for a bounded Down retry',accept_possible_duplicate_charge=True,scope='This serial enemy-direction task: same transient fetch failed / ECONNRESET before secure TLS, preserving uncertain originals. A fresh revision, active owner and per-attempt intent are mandatory.',max_additional_network_retries_per_direction=2,limit_origin='Conservative execution limit, not a user-specified monetary budget',parameters=dict(endpoint='https://aihub.dog/v1/images/edits',model='gpt-image-2',quality='medium',size='1536x1024',n=1),do_not_reclassify_prior_outcomes=True,stop_conditions=['Existing successful image must be reused','In-flight request or missing outcome must be inspected','Authentication/balance failures require actual resolution, not endless retries','Two additional attempts per direction exhausted','No endpoint or quality/candidate escalation'],computer_control_policy='New standing authorization is applied to the image-service retry described immediately before the user reply. Preserve the separate rule requiring a dialog before desktop control; use target Unity MCP by default.',not_related_to='SabretoothTiger Down-only $0.07 special authorization remains consumed and unchanged')
write(policy_path,policy)
base={p.relative_to(ROOT).as_posix():sha(p).upper() for f in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/f).rglob('*') if p.is_file()}
protected=read(D/'incremental_before_recovery_20261028.json')['protected_scarab']
assert all(sha(ROOT/p)==s.lower() for p,s in protected.items())
baseline_path=D/'incremental_before_authorized_retry_20261028.json'; assert not baseline_path.exists()
write(baseline_path,dict(observed_at=stamp,files=base,protected_scarab=protected,authorization_sha256=sha(policy_path)))
old=D/'generation/Down/revision_01'; dest=D/'generation/Down/revision_02'; dest.mkdir()
assert not (old/'raw.png').exists() and not (old/'result.json').exists()
(dest/'prompt.txt').write_text((old/'prompt.txt').read_text(encoding='utf-8'),encoding='utf-8')
intent=dict(schema_version=1,character='Scarab',direction='Down',revision='revision_02',prior_revision='revision_01',owner_thread_id=owner,dispatch_token=chain['dispatch_token'],max_requests=1,authorization_sha256=sha(policy_path),prior_request_sha256=sha(old/'request.json'),prior_uncertain_sha256=sha(old/'uncertain_result.json'),prior_console_sha256=sha(old/'console.txt'),reason='The user directly authorized silent continuation in the same network-failure situation after being told about possible duplicate charge. Reuse successful Up. Preserve Down revision_01 as uncertain; one new formal request after preflight.',created_at=stamp)
write(dest/'recovery_intent.json',intent)
chain['historical_stop_before_standing_network_recovery']={k:chain.get(k) for k in ['state','stopped_at','stop_reason','blocked_reason','recovery_file']}
chain.update(state='active',current_blocked=False,blocked_reason=None,stopped_at=None,stop_reason=None,current_stage='Scarab_Down_revision_02_standing_authorized_network_recovery',resume_authorization=policy_path.relative_to(ROOT).as_posix(),updated_at=stamp,resumed_at=stamp,resumed_by_thread_id=owner)
chain.setdefault('stage_history',[]).append(dict(character='Scarab',status='active',stage=chain['current_stage'],opened_at=stamp,authorization=chain['resume_authorization'],owner_thread_id=owner,dispatch_token=chain['dispatch_token']))
write(HERE/'conversation_chain.json',chain)
progress=read(HERE/'progress.json'); i=next(i for i in progress['items'] if i['name']=='Scarab'); i.update(status='reference_prepared',recovery_stage='authorized_Down_revision_02_preflight_pending',standing_recovery_authorization=chain['resume_authorization']); progress.update(current='Scarab',updated_at=stamp); write(HERE/'progress.json',progress)
note='\n\n## 2026-10-28 用户最新恢复授权\n\n用户明确回复“继续任务。后续同样的情况，不再需要我确认，可以继续静默执行”。此新指令覆盖上文对同类图像服务网络失败逐次确认的要求；旧Down结果仍uncertain。授权文件standing_network_recovery_authorization_20261028.json；现恢复Scarab Down revision_02，单次预检/正式请求，后续同类自动恢复采用每方向最多2次新增请求的执行限额，原请求全保留，不沿用SabretoothTiger的$0.07专用授权。优先通过目标Unity MCP，不把此授权扩大成桌面控制许可。chain实时active和owner/token为准。\n'
with (HERE/'NEXT_ENEMY_TASK.md').open('a',encoding='utf-8') as f:f.write(note)
print(json.dumps(dict(state='active',authorization=str(policy_path),revision=str(dest),baseline_files=len(base),protected_drift=[])))
