"""Record the current user's one-request override; preserve all earlier outcomes."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, shutil

directory = Path(__file__).resolve().parent
base = directory.parent
root = base.parents[2]
now = datetime.now(timezone(timedelta(hours=8))).isoformat()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(path, value):
    with path.open('x', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

chain = json.loads((base/'conversation_chain.json').read_text(encoding='utf-8'))
assert chain['state'] == 'blocked'
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['current_character'] == 'SabretoothTiger'
revision = directory/'generation/Down/revision_02'
assert not revision.exists()
prior = []
for rel in ['generation/Down/request.json', 'generation/Down/result.json',
            'generation/Down/revision_01/request.json', 'generation/Down/revision_01/uncertain_result.json',
            'generation/Down/revision_01/recovery_intent.json',
            'generation/Down/revision_01/transport_failure_evidence.json',
            'generation/Up/revision_01/raw.png']:
    prior.append({'path': rel, 'sha256': sha(directory/rel)})
provider = {
    'observed_at': now, 'source': 'Authenticated existing AIHub browser tab, visible usage UI only',
    'url': 'https://aihub.dog/usage', 'filters': {'time_range': '近24小时', 'model': 'gpt-image-2', 'request_category': '全部请求'},
    'visible_total': 3, 'visible_cost_usd': 0.21, 'all_pages_visible': True,
    'rows': [
        {'finished_china': '2026-10-28 09:59:29', 'cost_usd': 0.07, 'matches': 'SabretoothTiger/generation/Up/revision_01/result.json'},
        {'finished_china': '2026-10-28 09:01:53', 'cost_usd': 0.07, 'matches': 'ShardLizard/generation/Down/result.json'},
        {'finished_china': '2026-10-28 08:59:04', 'cost_usd': 0.07, 'matches': 'ShardLizard/generation/Up/revision_02/result.json'}],
    'endpoint': '/v1/images/edits', 'group': 'Image2原生 1.00x', 'key_label': 'ImageAPI',
    'per_row_quantity': '1张 (2K)', 'fault_transfer_tab': '暂无数据',
    'down_entry_found': False, 'down_local_output_found': False, 'active_generator_found': False,
    'conclusion': 'No visible Down usage entry. This is not conclusive server-outcome or no-billing evidence; old uncertainty remains.',
    'price_basis': 'All three matching recent same-key model/size usages cost USD 0.07 each. Provider hallway model-price popover was unavailable; no claim of a guaranteed server-side spending-limit API.',
    'sensitive_fields_omitted': ['account identifier', 'account balance', 'IP', 'other model usage']}
save(directory/'provider_usage_check_20261028.json', provider)
authorization = {
    'recorded_at': now, 'character': 'SabretoothTiger', 'direction': 'Down', 'revision': 'revision_02',
    'owner_thread_id': chain['owner_thread_id'], 'dispatch_token': chain['dispatch_token'],
    'source': 'Direct user answer in current chat to request_user_input_async',
    'question_item_id': '["request_user_input_async","call_GDs9TFQSRSYTGQpDUFqrBl9n",0]',
    'user_answer': '授权补发一次 Down，上限 $0.07',
    'accept_possible_duplicate_charge': True, 'max_requests': 1, 'max_cost_usd': 0.07,
    'model': 'gpt-image-2', 'quality': 'medium', 'n': 1, 'size': '1536x1024',
    'provider_evidence': 'provider_usage_check_20261028.json', 'prior_evidence': prior,
    'old_result': 'revision_01 stays uncertain; authorization does not prove no charge or server failure',
    'on_failure': 'Stop. No automatic retry, revision_03 or other-character paid probe under this authorization.'}
authfile=directory/'authorized_down_retry_20261028.json'
save(authfile, authorization)
revision.mkdir()
shutil.copy2(directory/'generation/Down/revision_01/prompt.txt', revision/'prompt.txt')
save(revision/'recovery_intent.json', {
    'created_at': now, 'character':'SabretoothTiger', 'direction':'Down', 'revision':'revision_02',
    'max_requests': 1, 'authorization_sha256': sha(authfile),
    'reason': 'Current user explicitly accepts possible duplicate charge and authorizes one Down-only attempt at the unchanged recent USD0.07 tier. Preserve earlier request uncertainty.'})
chain.update(state='active', current_blocked=False, resumed_at=now,
             current_stage='down_single_retry_explicitly_authorized',
             resume_authorization=authfile.relative_to(root).as_posix(),
             previous_blocked_reason=chain.get('blocked_reason'), updated_at=now)
chain['stage_history'].append({'character':'SabretoothTiger','status':'active','stage':chain['current_stage'],
    'opened_at':now,'authorization':authfile.relative_to(root).as_posix(),
    'owner_thread_id':chain['owner_thread_id'],'dispatch_token':chain['dispatch_token']})
(base/'conversation_chain.json').write_text(json.dumps(chain,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
progress=json.loads((base/'progress.json').read_text(encoding='utf-8'))
item=next(x for x in progress['items'] if x['name']=='SabretoothTiger')
item.update(status='generation_recovery_in_progress',current_blocked=False,recovery_in_progress=True,
            current_stage=chain['current_stage'],authorized_retry=authfile.relative_to(root).as_posix())
progress.update(status='active',current='SabretoothTiger',updated_at=now)
(base/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'active_owner':chain['owner_thread_id'],'authorization':str(authfile),'revision':str(revision),'max_requests':1,'max_cost_usd':0.07}))
