"""Close the reviewed single-character recovery; no paid calls or production writes."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, re, subprocess, sys

D = Path(__file__).resolve().parent
HERE = D.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from mcp_call import Client

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
def now(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
def unwrap(r): return r.get('structuredContent') or json.loads(r['content'][0]['text'])

chain = read(HERE/'conversation_chain.json')
assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert chain['current_character']=='SabretoothTiger'
assert chain['dispatch_token']=='shardlizard-to-sabretoothtiger-cffa9cb0c6fe47429c981a1e421b9a8e'
assert not (D/'final_validation_20261028.json').exists(), 'Inspect saved closeout before any retry'
auth = read(D/'authorized_down_retry_20261028.json')
assert auth['user_answer']=='授权补发一次 Down，上限 $0.07' and auth['max_requests']==1
result = read(D/'generation/Down/revision_02/result.json')
assert result['status']==200 and result['bytes']==1579303
for evidence in auth['prior_evidence']:
    assert sha(D/evidence['path']).lower()==evidence['sha256'].lower(), evidence['path']
billing = dict(observed_at=now(),source='Existing authenticated AIHub usage UI, agent research tab; no API request made for this check',
    filters=dict(period='last24h',model='gpt-image-2',request_category='all'),visible_rows=4,
    matched_request=dict(provider_local_time='2026/10/28 10:54:16',endpoint='/v1/images/edits',model='gpt-image-2',
        group='Image2原生 1.00x',quantity='1张 (2K)',charge_usd=0.07,result_finished_utc=result['finished'],
        result='generation/Down/revision_02/result.json',result_sha256=sha(D/'generation/Down/revision_02/result.json')),
    approved_limit_usd=0.07,within_approved_limit=True,authorization_consumed=True,new_requests_in_authorized_retry=1,
    prior_uncertain_request='generation/Down/revision_01/request.json',prior_uncertain_outcome='Still uncertain; absent visible usage row is not proof of no processing or charge',
    excluded_private_fields='Account identifier, balance, IP, credentials and unrelated model logs were not persisted')
write(D/'authorized_retry_billing_20261028.json',billing)

baseline_path = D/'incremental_before_authorized_retry_20261028.json'
base = {p:s.upper() for p,s in read(baseline_path)['files'].items()}
current = {p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
changes = [dict(path=p,before=base.get(p),after=current.get(p)) for p in sorted(set(base)|set(current)) if base.get(p)!=current.get(p)]
battle = 'Assets/Prefabs/Enemy/Enemy_SabretoothTiger.prefab'
art = 'Assets/_UIAssets/Monsters/Felines/SabretoothTiger/Directions'
unexpected, side_effects = [], []
for x in changes:
    p=x['path']
    if p==battle or p.startswith(art+'/') or p==art+'.meta': continue
    if p=='Assets/StreamingAssets/build_info' and current['Assets/Reporter/Editor/ReporterEditor.cs']==base['Assets/Reporter/Editor/ReporterEditor.cs'] and re.fullmatch(r'Build from .+ at .+', (ROOT/p).read_text(encoding='utf-8')):
        side_effects.append(dict(x,origin='Unmodified ReporterEditor InitializeOnLoad build timestamp; not an art change'))
    else: unexpected.append(x)
assert not unexpected, unexpected
protected = read(D/'incremental_before_recovery_20261028_095734.json')['protected_sabretoothtiger']
protected_drift = [p for p,s in protected.items() if p!=battle and sha(ROOT/p)!=s.upper()]
assert not protected_drift, protected_drift
targets = {t['name']:t for t in read(HERE/'local_baseline.json')['targets']}
definitions = (HERE.parent/'Batch01_10/audit_scope.py').read_text(encoding='utf-8')
exec(definitions[definitions.index('def sha('):definitions.index('changed=[];unexpected=[]')])
sem = semantic('SabretoothTiger')
assert sem['pass'], sem
manifest = read(D/'installed_manifest.json')
drift = [x['path'] for x in manifest['changes'] if sha(ROOT/x['path'])!=x['after'].upper()]
assert not drift, drift
staged_drift = [n for n in ['SabretoothTiger_Directions.png','SabretoothTiger_Directions.layout.json','SabretoothTiger_Directions.sprites.json'] if sha(D/'staged_art'/n)!=sha(ROOT/art/n)]
assert not staged_drift, staged_drift
verify = manifest['verification']['data']['result']
assert verify['pass'] and 'PASS YooAsset prefab and artwork collectors present' in verify['report']
assert (D/'installed_verify.txt').read_text(encoding='utf-8')==verify['report']
legacy_before = read(HERE/'scope_ShardLizard_20261028_final.json')
legacy_name = 'scope_SabretoothTiger_20261028_final.json'
assert not (HERE/legacy_name).exists()
run = subprocess.run([sys.executable,str(HERE/'audit_scope.py'),legacy_name],capture_output=True,text=True,encoding='utf-8')
assert run.returncode==0, run.stderr
legacy = read(HERE/legacy_name)
prior_unexpected = {x['path']:x.get('after') for x in legacy_before['unexpected']}
new_unexpected = [x for x in legacy['unexpected'] if prior_unexpected.get(x['path'])!=x.get('after')]
new_semantic = {n:s['unexpected'] for n,s in legacy['semantics'].items() if not s['pass'] and s['unexpected']!=legacy_before['semantics'].get(n,{}).get('unexpected')}
assert not new_unexpected and not new_semantic, (new_unexpected,new_semantic)
scope = dict(observed_at=now(),baseline=baseline_path.name,baseline_sha256=sha(baseline_path),baseline_files=len(base),current_files=len(current),
    comparison='Union of before/current file paths, including additions and deletions',changes=changes,unexpected_incremental=unexpected,
    automatic_editor_side_effects=side_effects,protected_six=protected,protected_drift=protected_drift,prefab_semantics=sem,
    installed_asset_drift=drift,staged_production_drift=staged_drift,legacy_before='scope_ShardLizard_20261028_final.json',legacy_after=legacy_name,
    legacy_pass=legacy['pass'],legacy_unexpected_count=len(legacy['unexpected']),legacy_semantic_failure_count=sum(not s['pass'] for s in legacy['semantics'].values()),
    new_unexpected_vs_preexisting_legacy=new_unexpected,new_semantic_failures=new_semantic,
    note='Historical 291 unexpected entries and six other-character semantic failures preserved. No global PASS claim.')
write(D/'scope_incremental_authorized_recovery_20261028.json',scope)

runtime = read(D/'runtime_summary.json')
assert runtime['passes']==168 and runtime['failures']==0 and runtime['actual_frames']==681
assert [r['revision'] for r in runtime['runtime']]==['runtime_r01','runtime_updeath_r01']
version_files = [D/p for p in ['installed_manifest.json','art_selection.json','layout_adjustments.json','raster_retouch.json','retouch_heels.py',
    'generation/Up/revision_01/raw.png','generation/Down/revision_02/raw.png','runtime_summary.json','authorized_retry_billing_20261028.json']]
frames = {}
for r in runtime['runtime']:
    folder = D/r['revision']
    records = folder/'actual_frames.jsonl'
    assert sha(records)==r['records_sha256'].upper()
    rows = [json.loads(line) for line in records.read_text(encoding='utf-8').splitlines() if line.strip()]
    assert len(rows)==r['frames'] and all(a['frame']<b['frame'] for a,b in zip(rows,rows[1:]))
    assert len({x['file'] for x in rows})==len(rows)
    checks=(folder/'actual_runtime_checks.txt').read_text(encoding='utf-8').splitlines()
    assert sum(x.startswith('PASS ') for x in checks)==84 and not any(x.startswith('FAIL ') for x in checks)
    frames[r['revision']]={x['file']:sha(folder/x['file']) for x in rows}
    assert all(frames[r['revision']].values())
    version_files += [records,folder/'actual_runtime_checks.txt',folder/'media_manifest.json',D/(r['revision']+'_start.json'),D/(r['revision']+'_returned.json')]
    version_files += list(folder.glob('*.gif'))
version_files += [p for p in (D/'staged_art').iterdir() if p.is_file()]
write(D/'version_binding_final_20261028.json',dict(observed_at=now(),final_install_manifest='installed_manifest.json',
    files={p.relative_to(D).as_posix():sha(p) for p in version_files},installed_files={x['path']:x['after'] for x in manifest['changes']},
    actual_png_frames=frames,frame_total=sum(len(x) for x in frames.values()),
    note='Final staged local heel/joint/tail repairs preceded installation and both real Play rounds. Original generated sheets unchanged.'))

c=Client()
project=c.identity()
errors=unwrap(c.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
state=c.resource('mcpforunity://editor/state')
code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};'
probe=unwrap(c.tool('execute_code',dict(action='execute',code=code)))
assert probe['success'],probe
observed=probe['data']['result']
assert not any(v for k,v in observed.items() if k!='scene') and observed['scene']=='Assets/Scenes/Boot.unity',observed
s=state['data']
assert not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']
assert errors['success'] and errors['data']==[],errors
write(D/'final_validation_20261028.json',dict(observed_at=now(),project=project,state=state,errors=errors,probe=probe,
    final_install_manifest='installed_manifest.json',installed_asset_drift=drift,runtime_summary_sha256=sha(D/'runtime_summary.json'),protocol_history=c.history))

note='Up复用revision_01；Down经用户明确授权单次补发revision_02，HTTP200，用量页10:54:16实际$0.07，授权已消耗，旧Down revision_01仍结果不明并保留。最终采用显式切片与local heel/joint/tail修正，原生成图不改。两轮真实Play各84/0，共681帧。实际查看四方向、runtime_visual_strip及10张时序/步态/愤怒细节板；Up后脑无五官和剑齿，白灰虎身棕纹与尾根连接，后足为闭合后跟而非前爪；Down正脸剑齿与攻击张口可辨。运动中近侧足与躯干相连，远侧足部分被轴向身体遮挡；后跟局部绘制较简洁，留待用户美术判断。连续转向有步态延续，尾根固定、尾尖完整；白闪结束、死亡整身倾倒淡出、同实例复用恢复不透明状态均有实际帧和检查支持；暂停不变、恢复和倍速推进，抽样未见地面阴影。审阅为按时序真实PNG抽样，未播放GIF全片、未逐张审完681帧。仅内部技术与视觉检查完成，user_approved=false。'
(D/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
visual_folder=D/'visual_review_final_20261028'
sources=read(visual_folder/'sources.json')
sheets=sorted({x['sheet'] for x in sources['sources']})
assert len(sheets)==10 and len(sources['sources'])==256
unique=len({(x['revision'],x['source']) for x in sources['sources']})
write(visual_folder/'review.json',dict(observed_at=now(),status='completed_pending_user_art_review',user_approved=False,note=note,
    viewed_sheets=sheets,sample_slots=len(sources['sources']),distinct_actual_frame_samples=unique,source_manifest='sources.json',
    additional_viewed=['runtime_r01/four_directions.png','runtime_visual_strip.png'],method='Chronological actual PNG samples, walk cycles and angry details. No live GIF playback; not every frame reviewed.',
    final_install_manifest='installed_manifest.json',sources_sha256=sha(visual_folder/'sources.json'),viewed_sheet_sha256={p:sha(visual_folder/p) for p in sheets},final_version_binding='version_binding_final_20261028.json'))
subprocess.run([sys.executable,str(HERE/'record_review.py'),'SabretoothTiger',note],check=True)
p=read(HERE/'progress.json')
i=next(x for x in p['items'] if x['name']=='SabretoothTiger')
i.update(recovery_in_progress=False,recovery_completed_at=now(),current_blocked=False,historical_blocked_records_preserved=True,
    current_stage='recorded_pending_user_art_review',generation_revisions=dict(Up='revision_01',Down='revision_02'),
    final_install_manifest='SabretoothTiger/installed_manifest.json',final_visual_review='SabretoothTiger/visual_review_final_20261028/review.json',
    final_validation='SabretoothTiger/final_validation_20261028.json',final_scope='SabretoothTiger/scope_incremental_authorized_recovery_20261028.json',
    billing='SabretoothTiger/authorized_retry_billing_20261028.json',authorized_down_retry_consumed=True)
assert p['completed_count']==81 and i['status']=='completed_pending_user_art_review' and not i['user_approved']
write(HERE/'progress.json',p)
chain.update(character_status_at_handoff=i['status'],completed_count_snapshot=81,current_stage='recorded_pending_user_art_review',
    resume_stage='SabretoothTiger installed, 168/0, 681 frames, actual visual review, record and GIF archive complete',
    last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/SabretoothTiger/final_validation_20261028.json',updated_at=now(),current_blocked=False)
write(HERE/'conversation_chain.json',chain)
gifs=read(HERE.parent/'AllGIF/manifest.json')
own=[x for x in gifs['files'] if x['source'].startswith('Remaining_20261024/SabretoothTiger/')]
assert len(own)==12 and all(x['status']=='当前审核版本' for x in own)
assert all(sha(HERE.parent/x['source'])==x['sha256'] and sha(HERE.parent/'AllGIF'/x['file'])==x['sha256'] for x in own)
write(D/'gif_archive_verification_20261028.json',dict(observed_at=now(),total=gifs['count'],character_count=len(own),current_count=len(own),files=own,sha256_match=True))
print(json.dumps(dict(completed=p['completed_count'],changes=len(changes),added=sum(x['before'] is None for x in changes),unexpected=len(unexpected),legacy_unexpected=len(legacy['unexpected']),new_legacy=len(new_unexpected),prefab_semantics=sem['pass'],samples=unique,probe=observed,gifs_total=gifs['count'],character_gifs=len(own),retry_cost_usd=0.07),ensure_ascii=False))
