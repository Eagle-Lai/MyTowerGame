"""Document one current-turn resume after factual non-billable service checks.

The previous automatic allowance remains exhausted. The latest direct request
and the existing standing human grant are the authorization basis. The bound of
one is an execution choice, not a newly invented user monetary limit.
"""
from pathlib import Path
import sys
import json
import hashlib
import os
from datetime import datetime, timezone, timedelta

D=Path(__file__).resolve().parent
H=D.parent
ROOT=H.parents[2]
OWNER='01a18619-6aa0-7a31-ac62-10a82077950b'
TOKEN='winterboar-to-winterogre-20261029_131318-14b528b1-8990-455f-8069-d7ea49019046'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().lower()
now=lambda:datetime.now(timezone(timedelta(hours=8))).isoformat()

def check():
    c=read(H/'conversation_chain.json')
    assert c['state']=='blocked' and c['owner_thread_id']==OWNER and c['dispatch_token']==TOKEN and c['current_character']=='WinterOgre'
    assert os.environ.get('CODEX_THREAD_ID')==OWNER
    return c

def fresh(p,v):
    check()
    assert not p.exists(),str(p)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))

chain=check()
network_file=D/'read_only_service_recheck_20261029T061254Z.json'
network=read(network_file)
assert network['paid_requests']==0
models,usage=network['responses']
assert models['http_status']==200 and 'gpt-image-2' in models['image_models']
assert usage['http_status']==200 and usage['body']['isValid'] and usage['body']['balance']>0
assert datetime.now(timezone.utc)-datetime.fromisoformat(network['completed_at'].replace('Z','+00:00'))<timedelta(minutes=20)
standing=H/'standing_network_recovery_authorization_20261028.json'
assert read(standing)['accept_possible_duplicate_charge'] and read(standing)['max_additional_network_retries_per_direction']==2
old_block=D/'blocked_generation_recovery_20261029_134607.json'
assert read(old_block)['additional_network_attempts_used']=={'Up':2,'Down':0}
preserved=[]
for sub in ['generation/Up','generation/Up/revision_01','generation/Up/revision_02']:
    f=D/sub
    assert not (f/'raw.png').exists() and not (f/'result.json').exists()
    for p in sorted(f.iterdir()):
        if p.is_file():preserved.append(dict(path=p.relative_to(D).as_posix(),sha256=sha(p)))
assert not (D/'generation/Down/request.json').exists()
baseline=read(D/'incremental_before_20261029.json')
scope=read(D/'scope_incremental_blocked_20261029_134607.json')
current={p.relative_to(ROOT).as_posix():sha(p).upper() for sub in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/sub).rglob('*') if p.is_file()}
expected=dict(baseline['files'])
expected['Assets/StreamingAssets/build_info']=scope['changes'][0]['after']
assert current==expected,'Production drift since blocked closeout'
fresh(D/'authorized_resume_20261029.json',dict(
    recorded_at=now(),user_statement='继续任务',source='Latest direct human message in this owner chat, after the explicit blocked closeout.',
    authorization_basis='Existing direct standing grant to continue the same transient network failures silently, accepting possible duplicate charge; latest direct continuation follows factual current transport/authentication/positive-balance checks.',
    interpretation='One additional current-turn request is an explicit execution decision under the standing grant. The number one is chosen by the agent, not represented as a user-specified monetary budget. No reset of the exhausted automatic-retry allowance.',
    owner_thread_id=OWNER,dispatch_token=TOKEN,character='WinterOgre',direction='Up',revision='revision_03',
    transport='curl_https_no_retry',max_requests=1,accept_possible_duplicate_charge=True,
    automatic_retries_used=2,automatic_retry_limit=2,resets_automatic_counter=False,
    standing_authorization_file=standing.relative_to(ROOT).as_posix(),standing_authorization_sha256=sha(standing),
    network_assessment_file=network_file.name,network_assessment_sha256=sha(network_file),
    prior_blocked_file=old_block.name,prior_blocked_sha256=sha(old_block),preserved_evidence=preserved,
    parameters=dict(endpoint='https://aihub.dog/v1/images/edits',model='gpt-image-2',quality='medium',size='1536x1024',n=1),
    cost='Prior three charges and outcomes remain unknown; current public key usage is aggregate only.',
    stop='No automatic repeat of this request. If uncertain, authentication, balance or upstream failure occurs, preserve evidence and stop paid work.'))
revision=D/'generation/Up/revision_03'
assert not revision.exists()
revision.mkdir()
(revision/'prompt.txt').write_bytes((D/'generation/Up/prompt.txt').read_bytes())
fresh(revision/'recovery_intent.json',dict(recorded_at=now(),owner_thread_id=OWNER,dispatch_token=TOKEN,
    character='WinterOgre',direction='Up',revision='revision_03',max_requests=1,
    authorization_sha256=sha(D/'authorized_resume_20261029.json'),
    reason='Latest user continuation plus standing silent recovery permission; current auth/models/usage succeeded. Preserve original uncertain requests, use original references, no automatic retry.'))
fresh(D/'resume_before_20261029.json',dict(recorded_at=now(),chain=chain,progress=read(H/'progress.json'),
    next_task_sha256=sha(H/'NEXT_ENEMY_TASK.md'),generator_sha256=sha(H/'generate.mjs'),
    baseline_files=len(current),protected_six_unchanged=True,automatic_retry_count_retained=2))
next_file=H/'NEXT_ENEMY_TASK.md'
saved_next=D/'next_task_blocked_before_resume_20261029.md'
assert not saved_next.exists()
saved_next.write_bytes(next_file.read_bytes())
next_text=next_file.read_text(encoding='utf-8')
next_text=next_text.replace('# WinterOgre(index111) 阻断恢复：完整执行入口','# WinterOgre(index111) 当前单次有界恢复：完整执行入口',1)
next_text=next_text.replace('当前真实状态是共同图片网络阻断，不能把本文件当成新增付费请求、重置上限或创建下一聊天的指令。先按以下完整说明读取并恢复既有阶段。',
    '最新用户在已知阻断后再次直接要求“继续任务”。只读检查确认Curl/Node连接可用、鉴权models/usage均HTTP200、密钥有效及余额充足；这些不保证图片上游。结合既有“同类故障可静默继续并接受可能重复收费”授权，已单独记录本轮唯一Up revision_03/Curl请求决定。自动恢复2/2仍耗尽，没有重置；本轮最大1次是代理执行上限，不冒充用户指定预算。先读WinterOgre/authorized_resume_20261029.json、read_only_service_recheck_20261029T061254Z.json和revision_03/recovery_intent.json，按真实已有阶段恢复，禁止重复发已存在request。',1)
next_text=next_text.replace('- chain.state=blocked；','- chain.state=active；',1)
next_text=next_text.replace('- 进度99/108：99项completed_pending_user_art_review，2项blocked（PossessedWarg79、WinterOgre111），7项not_started',
    '- 进度99/108：99项completed_pending_user_art_review；PossessedWarg79仍blocked，WinterOgre111恢复到reference_prepared、本轮Up单次请求待执行；7项not_started',1)
next_text=next_text.replace('每方向最多2次额外网络恢复已用于Up，不能发第三次额外Up请求，不能清空或重置计数，不能借Down未用次数或新角色作付费探针。',
    '原自动网络恢复上限2/2已用尽，原授权文件不改。本轮独立current-turn有界恢复仅允许WinterOgre Up revision_03、Curl、max_requests=1；必须使用既有generate_character.ps1 -AuthorizedResume -Revision revision_03，先Preflight和正确Unity身份/空闲核对，再至多一次正式请求。输出/request/不明结果一旦存在就停止，不换revision重复本轮请求，不借Down或其他角色作探针。',1)
next_text=next_text.replace('只有真实故障解决证据和新允许执行的有界范围才能扩大已耗尽的尝试；“继续任务”、新聊天或elapsed time本身不构成自动扩额。',
    '原封存条件保留：不能仅靠新聊天或时间流逝自动扩额。本轮具体决定已由当前直接继续指令、既有静默恢复授权及新的鉴权/余额/连接事实共同落盘，旧三次结果不明与2/2自动计数不变。若本轮失败，准确封存并停止；若成功则复用该raw、实际审图后恢复原逐阶段流水线。',1)
next_file.write_bytes(next_text.encode('utf-8'))
live=('2026-10-29 WinterOgre111按最新直接“继续任务”和既有同类网络故障静默恢复授权，结合新只读连接/鉴权models与usage HTTP200、密钥有效且余额充足事实，登记本轮独立Up revision_03/Curl/max_requests=1。'
    '原自动恢复2/2保持耗尽，原三次uncertain/未知费用不变，不冒充用户新增预算，不自动重试。当前active owner/token保留、reference_prepared，99/108、AllGIF1594，无角色生产改动。'
    '授权WinterOgre/authorized_resume_20261029.json，证据read_only_service_recheck_20261029T061254Z.json，完整入口NEXT_ENEMY_TASK.md。原blocked交接及2条MCP错误历史保留；正式请求前重核正确Unity8088身份/空闲，失败即保留并停止。')
for file,begin,end in [(H.parent/'README.md','<!-- ENEMY_README_LIVE_BEGIN -->','<!-- ENEMY_README_LIVE_END -->'),
                       (H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->','<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    raw=file.read_bytes();a=raw.index(begin.encode())+len(begin);b=raw.index(end.encode(),a)
    file.write_bytes(raw[:a]+b'\n'+live.encode('utf-8')+b'\n'+raw[b:])
progress=read(H/'progress.json')
item=next(i for i in progress['items'] if i['name']=='WinterOgre')
assert item['status']=='blocked' and progress['completed_count']==99
item.update(status='reference_prepared',previous_blocked_reason=item['blocked_reason'],blocked_reason=None,
    current_recovery_file='WinterOgre/authorized_resume_20261029.json')
progress.update(status='in_progress',updated_at=now())
(H/'progress.json').write_bytes((json.dumps(progress,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
chain.setdefault('historical_stops',[]).append(dict(character='WinterOgre',owner_thread_id=OWNER,
    dispatch_token=TOKEN,blocked_at=chain['stopped_at'],blocked_reason=chain['blocked_reason'],
    handoff_file=chain['last_handoff_file'],recovery_file=chain['recovery_file']))
chain.update(state='active',current_blocked=False,blocked_reason=None,stop_reason=None,
    current_stage='WinterOgre_current_turn_Up_revision_03_single_resume_authorized',
    resumed_at=now(),updated_at=now(),resumed_by_thread_id=OWNER,resumed_with_dispatch_token=TOKEN,
    current_turn_resume_file='Docs/EnemyDirectionReview/Remaining_20261024/WinterOgre/authorized_resume_20261029.json',
    last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/WinterOgre/generation/Up/revision_03/recovery_intent.json')
check()
(H/'conversation_chain.json').write_bytes((json.dumps(chain,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(dict(state='active',character='WinterOgre',revision='revision_03',current_turn_max_requests=1,
    prior_automatic_used=2,prior_automatic_limit=2,original_uncertain=3,production_files=len(current))))
