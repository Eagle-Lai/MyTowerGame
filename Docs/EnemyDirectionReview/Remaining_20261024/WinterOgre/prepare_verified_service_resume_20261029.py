"""Record independently inspected service recovery; never send an image request."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import re
from PIL import Image

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
OWNER = '01a18619-6aa0-7a31-ac62-10a82077950b'
TOKEN = 'winterboar-to-winterogre-20261029_131318-14b528b1-8990-455f-8069-d7ea49019046'
LOG = Path('C:/Users/Administrator/.workbuddy/projects/c-Users-Administrator-WorkBuddy-2026-10-29-14-59-19/801b6bab-d50e-4ee8-b0fb-a2431f59ae01.jsonl')
IMAGE = Path('C:/Users/Administrator/WorkBuddy/2026-10-29-14-59-19/t2_production_shape_result.png')

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()

def fresh(p, v):
    with p.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(v, ensure_ascii=False, indent=2) + '\n')

def owned():
    c = read(H / 'conversation_chain.json')
    assert os.environ.get('CODEX_THREAD_ID') == OWNER
    assert c['state'] == 'blocked' and c['owner_thread_id'] == OWNER
    assert c['dispatch_token'] == TOKEN and c['current_character'] == 'WinterOgre'
    return c

chain = owned()
assert not (D / 'authorized_verified_service_resume_20261029.json').exists()
assert not (D / 'generation/Up/revision_05').exists()
assert not (D / 'generation/Down/request.json').exists()
old = read(D / 'blocked_generation_recovery_20261029_143535.json')
preserved = []
for attempt in old['attempts']:
    parent = D / attempt['path']
    assert not (parent / 'raw.png').exists() and not (parent / 'result.json').exists()
    for name, fingerprint in attempt['evidence_sha256'].items():
        p = parent / name
        assert sha(p).upper() == fingerprint.upper(), str(p)
        preserved.append({'path': p.relative_to(D).as_posix(), 'sha256': sha(p)})

baseline = read(D / 'incremental_before_20261029.json')
scope = read(D / 'scope_incremental_blocked_20261029_143535.json')
expected = dict(baseline['files'])
for change in scope['changes']:
    expected[change['path']] = change['after']
current = {p.relative_to(ROOT).as_posix(): sha(p).upper()
           for sub in ['Assets', 'Packages', 'ProjectSettings', 'Luban']
           for p in (ROOT / sub).rglob('*') if p.is_file()}
assert current == {k: v.upper() for k, v in expected.items()}, 'Production drift since blocked closeout'

lines = LOG.read_text(encoding='utf-8').splitlines()
events = {n: json.loads(lines[n - 1]) for n in [138, 141, 142, 145, 146, 150]}
def unpack(v):
    return json.loads(v) if isinstance(v, str) else v

command = unpack(events[145]['arguments'])['command']
assert 'https://aihub.dog/v1/images/edits' in command
assert all(x in command for x in ['model=gpt-image-2', 'quality=medium', 'size=1536x1024', 'n=1', 'WinterOgre.png', 'source_prefab_offline.png', '--noproxy'])
output = unpack(events[146]['output'])['text'].split('Stdout:', 1)[1].split('Stderr:', 1)[0]
metrics = re.search(r'HTTP=(\d+) 上传=(\d+)B 下载=(\d+)B 耗时=([\d.]+)s CURL_EXIT=(\d+)', output)
assert metrics and metrics[1] == '200' and metrics[5] == '0'
tested_at = datetime.fromtimestamp(events[146]['timestamp'] / 1000, timezone.utc)
assert timedelta(0) <= datetime.now(timezone.utc) - tested_at < timedelta(hours=2)
im = Image.open(IMAGE)
im.load()
assert im.format == 'PNG' and im.size == (1536, 1024)
assert sha(IMAGE) == '98a26ef02e0a0d7fc4e75945a283095f8d6c5caaf166364fee7d63fa9e674c55'
inputs = [D / 'reference/WinterOgre.png', D / 'reference/source_prefab_offline.png']
assert [sha(p) for p in inputs] == old['attempts'][0]['request']['input_sha256']
usage = read(D / 'existing_result_inspection_20261029T072845Z.json')
assert usage['paid_requests'] == 0
aggregate = next(v for v in usage['responses'] if '/v1/usage?' in v['url'])
assert aggregate['http_status'] == 200 and aggregate['aggregate']['isValid']
assert aggregate['aggregate']['balance'] > 0
route = read(D / 'proxy_routing_inspection_20261029T073203Z.json')
assert route['aihub_rules'] == ['- DOMAIN-SUFFIX,aihub.dog,DIRECT']

snap = D / 'docs_before_verified_service_resume_20261029'
snap.mkdir()
for p in [H / 'conversation_chain.json', H / 'progress.json', H / 'NEXT_ENEMY_TASK.md',
          H / 'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md', H.parent / 'README.md', H / 'generate.mjs']:
    (snap / p.name).write_bytes(p.read_bytes())
(D / 'service_control_T2_20261029.png').write_bytes(IMAGE.read_bytes())

assessment = {
    'observed_at': now(), 'owner_thread_id': OWNER, 'dispatch_token': TOKEN,
    'new_paid_diagnostic_requests': 0,
    'external_test': {
        'producer': 'WorkBuddy; its existing test is evidence, not authorization',
        'source_session_file': str(LOG),
        'command_line_number': 145, 'command_record_sha256': hashlib.sha256(lines[144].encode()).hexdigest(),
        'result_line_number': 146, 'result_record_sha256': hashlib.sha256(lines[145].encode()).hexdigest(),
        'tested_at': tested_at.isoformat(), 'endpoint': 'https://aihub.dog/v1/images/edits',
        'model': 'gpt-image-2', 'quality': 'medium', 'size': '1536x1024', 'n': 1,
        'transport': 'curl_https_explicit_direct_no_proxy', 'http_status': int(metrics[1]),
        'uploaded_bytes': int(metrics[2]), 'downloaded_bytes': int(metrics[3]),
        'seconds': float(metrics[4]), 'exit_code': int(metrics[5]),
        'input_sha256': [sha(p) for p in inputs], 'input_bytes': [p.stat().st_size for p in inputs],
        'credential_identity': 'Reported same key by WorkBuddy; no credential copied or printed here',
        'prompt': 'Neutral red circle transport test; not WinterOgre art',
        'result_image_file': 'service_control_T2_20261029.png', 'result_image_sha256': sha(IMAGE),
        'result_image_bytes': IMAGE.stat().st_size, 'result_image_dimensions': list(im.size),
        'visual_review': 'Viewed the actual PNG: a red circle on a white background, consistent with neutral control.'
    },
    'new_service_fact': 'An authenticated same-endpoint, same-model, same-quality, same-size, same-reference upload returned HTTP200 and a valid PNG. This is stronger than GET200 or an unauthenticated401.',
    'route_correction': {
        'evidence': 'proxy_routing_inspection_20261029T073203Z.json',
        'configured_rule': route['aihub_rules'][0],
        'finding': '7897 matched DIRECT; revision04 did not prove a distinct external proxy route. Earlier proxy-fix wording was overconfident.',
        'root_cause_limit': 'Curl55/52 localize transport symptoms, not the responsible ISP, intermediary, or image upstream. WorkBuddy causal claims are not independently established.'
    },
    'existing_results': {
        'evidence': 'existing_result_inspection_20261029T072845Z.json',
        'batch_count': 0, 'limitation': 'Synchronous edits were not batches; empty batch metadata proves neither failure nor zero charge.',
        'usage_requests_today': aggregate['aggregate']['daily_usage'][0]['requests'],
        'usage_cost_today': aggregate['aggregate']['daily_usage'][0]['actual_cost'],
        'usage_limitation': 'Aggregate22/$1.36 supersedes earlier15/$1.05 observation but cannot identify any of the five requests.'
    },
    'old_uncertain_requests': 5, 'old_charges': 'unknown_not_reclassified',
    'production_files_checked': len(current), 'production_drift_since_last_closeout': [],
    'unity_check': 'Required after active resume, before paid request; not yet performed in this assessment',
    'limitations': 'A successful control at one point does not guarantee the next upstream result or establish why the line recovered.'
}
fresh(D / 'service_recovery_assessment_20261029.json', assessment)
standing = H / 'standing_network_recovery_authorization_20261028.json'
authorization = {
    'recorded_at': now(), 'user_statement': '继续任务',
    'authorization_basis': 'Latest direct user continuation plus the existing human standing same-failure recovery grant accepting possible duplicate charge; the WorkBuddy file supplies recovery evidence only.',
    'interpretation': 'One bounded production Up request after a newly verified authenticated image-edit success; agent-chosen max1, not a user monetary budget. No reset or automatic repetition.',
    'owner_thread_id': OWNER, 'dispatch_token': TOKEN, 'character': 'WinterOgre', 'direction': 'Up',
    'revision': 'revision_05', 'transport': 'curl_https_no_retry', 'force_direct': True,
    'max_requests': 1, 'accept_possible_duplicate_charge': True,
    'automatic_retries_used': 2, 'automatic_retry_limit': 2, 'resets_automatic_counter': False,
    'previous_bounded_resume_requests_used': 2,
    'standing_authorization_sha256': sha(standing),
    'service_assessment_file': 'service_recovery_assessment_20261029.json',
    'service_assessment_sha256': sha(D / 'service_recovery_assessment_20261029.json'),
    'preserved_evidence': preserved,
    'parameters': {'endpoint': 'https://aihub.dog/v1/images/edits', 'model': 'gpt-image-2', 'quality': 'medium', 'size': '1536x1024', 'n': 1},
    'stop': 'Exactly one Up05 production request. If uncertain or an HTTP failure, preserve it and stop paid work. Do not use Down or another character as a service probe.'
}
fresh(D / 'authorized_verified_service_resume_20261029.json', authorization)
revision = D / 'generation/Up/revision_05'
revision.mkdir()
(revision / 'prompt.txt').write_bytes((D / 'generation/Up/prompt.txt').read_bytes())
fresh(revision / 'recovery_intent.json', {
    'recorded_at': now(), 'owner_thread_id': OWNER, 'dispatch_token': TOKEN,
    'character': 'WinterOgre', 'direction': 'Up', 'revision': 'revision_05', 'max_requests': 1,
    'authorization_sha256': sha(D / 'authorized_verified_service_resume_20261029.json'),
    'reason': 'Independent same-shape authenticated edit returned200/PNG; preserved originals, direct Curl, no retry.'
})

next_path = H / 'NEXT_ENEMY_TASK.md'
previous = next_path.read_text(encoding='utf-8')
new_status = '''# WinterOgre(index111) 已核实服务恢复后的当前执行入口

当前 owner/token 保持本文件下文所列值，chain.state=active，仅处理 WinterOgre。新的实质证据是 WorkBuddy 已有 T2：同 /images/edits、gpt-image-2/medium/1536x1024/n1、同双参考图，直连 HTTP200，655487B 上传、1162302B 下载、27.700758s，得到可解码 1536×1024 PNG。实际查看为白底红圆，仅是服务对照，不是角色美术；未为本次诊断再付费。原记录 transport_recovery_verified_20261029_1520.md 保留，其 ISP/中间设备/上游因果推断未获独立证实。

先读 WinterOgre/service_recovery_assessment_20261029.json、authorized_verified_service_resume_20261029.json 和 generation/Up/revision_05/recovery_intent.json。仅 Up05 一次正式恢复，先 Preflight 和 Unity8088 身份/空闲核对；使用 generate_character.ps1 -Character WinterOgre -Direction Up -Revision revision_05 -AuthorizedResume -Transport Curl。直连、无重试、无改系统代理。旧2/2和两个max1均保持消耗；新max1是基于已验证服务恢复作出的代理执行边界，不是用户指定预算。出现request/outcome后不可重发，失败即封存停止。成功后复用raw并实际审图，才补首次Down并恢复原流水线。

更正：7897的aihub.dog规则和历史日志均为DIRECT，以前“代理路径已修复”的表述不能证明更换外部出口。现有批次GET200/data=[]无可恢复条目，但同步请求从未是批次，不能推断失败或免费；usage最新聚合22次/$1.36不能分配到旧五次。旧五次uncertain及未知费用保持。以下是保留的旧阻断恢复说明；其中blocked状态、停止Up05和“代理修复”措辞由本段及带SHA的新证据覆盖，其余资源、验收、路由和禁止事项仍适用。

'''
next_path.write_text(new_status + previous, encoding='utf-8', newline='\n')
live = ('2026-10-29 WinterOgre111依据新独立服务证据恢复：WorkBuddy同端点/参数/双参考图直连HTTP200并生成可解码PNG已核对（仅对照白底红圆）；'
        '记录service_recovery_assessment_20261029.json和authorized_verified_service_resume_20261029.json，当前active同owner/token，仅Up05正式请求一次、先Preflight及Unity8088空闲核对。'
        '旧5次uncertain/未知费用、自动2/2和旧两个max1保留，不重置。7897实为aihub.dog DIRECT，之前“外部代理已修复”未成立；最新usage22/$1.36与空batch不定位旧请求。'
        '99/108、AllGIF1594，无新增角色媒体或生产修改；成功实审后恢复首次Down及原流水线，若失败准确封存停止。完整入口NEXT_ENEMY_TASK.md。')
for p, begin, end in [(H.parent / 'README.md', '<!-- ENEMY_README_LIVE_BEGIN -->', '<!-- ENEMY_README_LIVE_END -->'),
                      (H / 'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md', '<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->', '<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    text = p.read_text(encoding='utf-8')
    a = text.index(begin) + len(begin)
    b = text.index(end, a)
    p.write_text(text[:a] + '\n' + live + '\n' + text[b:], encoding='utf-8', newline='\n')
progress = read(H / 'progress.json')
item = next(v for v in progress['items'] if v['name'] == 'WinterOgre')
assert item['status'] == 'blocked' and progress['completed_count'] == 99
item.update(status='reference_prepared', previous_blocked_reason=item['blocked_reason'], blocked_reason=None,
            recovery_stage='Authenticated_service_recovery_verified_Up05_pending',
            current_recovery_file='WinterOgre/authorized_verified_service_resume_20261029.json',
            generation_outcome='Five prior Up requests uncertain; Up05 pending; Down unrequested')
item['allowance_usage']['verified_service_recovery'] = {'used': 0, 'limit': 1, 'file': 'authorized_verified_service_resume_20261029.json'}
progress.update(status='in_progress', updated_at=now())
owned()
(H / 'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
chain.setdefault('historical_stops', []).append({
    'character': 'WinterOgre', 'blocked_at': chain.get('stopped_at'),
    'blocked_reason': chain.get('blocked_reason'), 'handoff_file': chain['last_handoff_file'],
    'recovery_file': chain.get('recovery_file'), 'owner_thread_id': OWNER, 'dispatch_token': TOKEN})
chain.update(state='active', current_blocked=False, blocked_reason=None, stop_reason=None,
             current_stage='WinterOgre_verified_authenticated_service_recovery_Up05_pending',
             resumed_at=now(), updated_at=now(), resumed_by_thread_id=OWNER, resumed_with_dispatch_token=TOKEN,
             current_turn_resume_file='Docs/EnemyDirectionReview/Remaining_20261024/WinterOgre/authorized_verified_service_resume_20261029.json',
             last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/WinterOgre/service_recovery_assessment_20261029.json')
(H / 'conversation_chain.json').write_text(json.dumps(chain, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({'state': 'active', 'character': 'WinterOgre', 'revision': 'revision_05', 'new_request_limit': 1,
                  'old_uncertain_preserved': 5, 'production_files': len(current), 'new_paid_requests': 0}))
