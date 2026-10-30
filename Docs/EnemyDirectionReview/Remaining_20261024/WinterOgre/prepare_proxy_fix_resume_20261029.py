from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from session_winterogre import *

owner()
prior=D/'generation/Up/revision_03'
assert not (prior/'raw.png').exists() and not (prior/'result.json').exists()
assert 'curl transport failed 55' in read(prior/'uncertain_result.json')['message']
assert read(D/'authorized_resume_20261029.json')['max_requests']==1
proof=D/'unauthenticated_upload_diagnosis_20261029_142408.json'
direct=D/'unauthenticated_upload_diagnosis_20261029_142135.json'
network=D/'read_only_service_recheck_20261029T062117Z.json'
proof_value=read(proof);direct_value=read(direct)
assert proof_value['process_exit']==0 and proof_value['credential_present'] is False
metrics=json.loads(proof_value['stdout'].split('UNAUTH_METRICS=')[1])
assert metrics['http_status']==401 and metrics['uploaded']==660604 and metrics['tls_verify']==0
assert direct_value['process_exit']==55
preserved=[]
for sub in ['generation/Up','generation/Up/revision_01','generation/Up/revision_02','generation/Up/revision_03']:
    f=D/sub
    assert not (f/'raw.png').exists() and not (f/'result.json').exists()
    preserved += [dict(path=p.relative_to(D).as_posix(),sha256=sha(p).lower()) for p in sorted(f.iterdir()) if p.is_file()]
standing=H/'standing_network_recovery_authorization_20261028.json'
write(D/'transport_fix_20261029.json',dict(recorded_at=now(),character=NAME,
    direct=dict(evidence=direct.name,sha256=sha(direct),result='Curl55; 71446 bytes uploaded, no HTTP outcome, 18.98s'),
    control=dict(evidence=proof.name,sha256=sha(proof),result='Existing local system proxy; all 660604 bytes uploaded, HTTP401, TLS verify0, 0.38s'),
    finding='Direct multipart upload fails while small direct requests work. Explicit use of the already configured local system proxy completed the same unauthenticated upload. This resolves the reproduced upload transport defect, not a claim of upstream image-generation success.',
    change='Docs CLI opt-in -UseSystemLocalProxy -> Curl --proxy http://127.0.0.1:7897 --noproxy empty; unchanged HTTPS AIHub endpoint, certificate validation on, no redirects/retries. No global proxy, registry, DNS, environment or Unity C# changes.',
    credential_policy='Bearer header supplied only via curl stdin, removed from child environment, never output or saved; HTTPS CONNECT still authenticates aihub.dog.',
    authorization_basis='The existing direct standing grant to silently continue this same network issue and latest explicit task continuation persist. The prior current-turn request is consumed; the additional one below is a separately documented agent decision after a concrete new transport repair, not a reset or a user-specified monetary budget.'),fresh=True)
write(D/'authorized_proxy_resume_20261029.json',dict(recorded_at=now(),user_statement='继续任务',
    source='Current direct continuation plus prior direct standing grant for silent network recovery accepting possible duplicate charge; substantive new complete-upload proxy control evidence.',
    owner_thread_id=OWNER,dispatch_token=TOKEN,character=NAME,direction='Up',revision='revision_04',transport='curl_https_no_retry',
    max_requests=1,accept_possible_duplicate_charge=True,use_system_local_proxy=True,
    automatic_retries_used=2,automatic_retry_limit=2,resets_automatic_counter=False,previous_current_turn_request_used=1,
    standing_authorization_sha256=sha(standing).lower(),network_assessment_file=network.name,network_assessment_sha256=sha(network).lower(),
    proxy_control_file=proof.name,proxy_control_sha256=sha(proof).lower(),preserved_evidence=preserved,
    numeric_bound_origin='Agent execution bound after concrete transport repair, not an assertion of a new user numerical budget.',
    stop='Exactly one post-fix request; no further network request if it fails. Preserve all four prior unknown results and charges.'),fresh=True)
out=D/'generation/Up/revision_04'
assert not out.exists()
out.mkdir();(out/'prompt.txt').write_bytes((D/'generation/Up/prompt.txt').read_bytes())
write(out/'recovery_intent.json',dict(recorded_at=now(),character=NAME,direction='Up',revision='revision_04',
    owner_thread_id=OWNER,dispatch_token=TOKEN,max_requests=1,authorization_sha256=sha(D/'authorized_proxy_resume_20261029.json').lower(),
    reason='Repaired reproduced direct-upload defect with independently verified full unauthenticated multipart upload through the existing local proxy; no reset or reclassification of prior requests.'),fresh=True)
stage('WinterOgre_Up_revision_04_single_post_transport_fix_request',str((out/'recovery_intent.json').relative_to(ROOT)).replace('\\','/'))
p=read(H/'progress.json');i=next(i for i in p['items'] if i['name']==NAME);i['current_recovery_file']='WinterOgre/authorized_proxy_resume_20261029.json';p['updated_at']=now();write(H/'progress.json',p)
next_file=H/'NEXT_ENEMY_TASK.md';text=next_file.read_text(encoding='utf-8')
write(D/'next_before_proxy_resume_20261029.json',dict(recorded_at=now(),content=text,sha256=sha(next_file)),fresh=True)
prefix=('# 当前覆盖块：已修复上传传输路径，唯一后续请求\n\n'
    '原Up revision_03本轮一次请求已消耗，Curl55、仍uncertain。新的不带密钥对照证明直连上传71446字节后断开，而系统现有代理127.0.0.1:7897完整上传660604字节、HTTP401、证书校验0。'
    '在同类故障静默恢复的既有用户授权和当前继续任务范围内，已单独记录修复后唯一Up revision_04请求决定。自动2/2和revision_03单次均保持已消耗，旧四次unknown/费用未知不改。'
    '当前唯一可执行生成命令是generate_character.ps1 -Character WinterOgre -Direction Up -Revision revision_04 -AuthorizedResume -Transport Curl -UseSystemLocalProxy，先Preflight；有request/raw/result/uncertain时禁止重发。'
    '授权WinterOgre/authorized_proxy_resume_20261029.json，修复证据WinterOgre/transport_fix_20261029.json。修复后仍失败则保留并停止，不能新开revision继续网络重试。'
    '以下revision_03授权过程为保留的前一阶段，不得重跑。成功后按下文原始审图/分件/安装/两轮真实运行流水线推进。\n\n')
next_file.write_text(prefix+text,encoding='utf-8')
print(json.dumps(dict(prepared=NAME,revision='revision_04',proxy='http://127.0.0.1:7897',post_fix_max_requests=1,previous_uncertain=4,automatic_used=2)))
