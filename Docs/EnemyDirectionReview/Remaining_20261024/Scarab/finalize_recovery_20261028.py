"""Close Scarab after actual r02 visual review. Docs-only writes and MCP probes."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, re, subprocess, sys, time

D = Path(__file__).resolve().parent
HERE = D.parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from mcp_call import Client

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p, data): p.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
def now(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
def unwrap(v): return v.get('structuredContent') or json.loads(v['content'][0]['text'])

chain = read(HERE/'conversation_chain.json')
assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert chain['current_character']=='Scarab' and chain['dispatch_token']=='sabretoothtiger-to-scarab-a14cefa3c87b4f9187c899d88ead8c0c'
assert not (D/'final_validation_20261028.json').exists(), 'Inspect existing closeout before retry'
intent = read(D/'generation/Down/revision_02/recovery_intent.json')
assert sha(HERE/'standing_network_recovery_authorization_20261028.json').lower()==intent['authorization_sha256'].lower()
for key, p in [('prior_request_sha256','request.json'),('prior_uncertain_sha256','uncertain_result.json'),('prior_console_sha256','console.txt')]:
    assert sha(D/'generation/Down/revision_01'/p).lower()==intent[key].lower(), p
result = read(D/'generation/Down/revision_02/result.json')
assert result['status']==200 and result['bytes']==(D/'generation/Down/revision_02/raw.png').stat().st_size
assert not (D/'generation/Down/revision_01/raw.png').exists() and not (D/'generation/Down/revision_01/result.json').exists()

baseline_path = D/'incremental_before_authorized_retry_20261028.json'
base = {p:s.upper() for p,s in read(baseline_path)['files'].items()}
current = {p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
changes = [dict(path=p,before=base.get(p),after=current.get(p)) for p in sorted(set(base)|set(current)) if base.get(p)!=current.get(p)]
battle = 'Assets/Prefabs/Enemy/Enemy_Scarab.prefab'
art = 'Assets/_UIAssets/Monsters/Insects/Scarab/Directions'
unexpected, side_effects = [], []
for x in changes:
    p=x['path']
    if p==battle or p.startswith(art+'/') or p==art+'.meta': continue
    if p=='Assets/StreamingAssets/build_info' and current['Assets/Reporter/Editor/ReporterEditor.cs']==base['Assets/Reporter/Editor/ReporterEditor.cs'] and re.fullmatch(r'Build from .+ at .+', (ROOT/p).read_text(encoding='utf-8')):
        side_effects.append(dict(x,origin='Unmodified ReporterEditor InitializeOnLoad timestamp'))
    else: unexpected.append(x)
assert not unexpected, unexpected
protected = read(D/'incremental_before_recovery_20261028.json')['protected_scarab']
protected_drift = [p for p,s in protected.items() if p!=battle and sha(ROOT/p)!=s.upper()]
assert not protected_drift, protected_drift
targets = {t['name']:t for t in read(HERE/'local_baseline.json')['targets']}
definitions = (HERE.parent/'Batch01_10/audit_scope.py').read_text(encoding='utf-8')
exec(definitions[definitions.index('def sha('):definitions.index('changed=[];unexpected=[]')])
sem = semantic('Scarab')
assert sem['pass'], sem
manifest = read(D/'installed_manifest.json')
drift = [x['path'] for x in manifest['changes'] if sha(ROOT/x['path'])!=x['after'].upper()]
assert not drift, drift
staged_drift = [n for n in ['Scarab_Directions.png','Scarab_Directions.layout.json','Scarab_Directions.sprites.json'] if sha(D/'staged_art'/n)!=sha(ROOT/art/n)]
assert not staged_drift, staged_drift
preplay = read(D/'version_binding_preplay_20261028.json')
assert all(sha(D/'staged_art'/p)==s.upper() for p,s in preplay['staging_files'].items())
verify = manifest['verification']['data']['result']
assert verify['pass'] and 'PASS YooAsset prefab and artwork collectors present' in verify['report']
assert (D/'installed_verify.txt').read_text(encoding='utf-8')==verify['report']
legacy_before = read(HERE/'scope_SabretoothTiger_20261028_final.json')
legacy_name = 'scope_Scarab_20261028_final.json'
if not (HERE/legacy_name).exists():
    with (D/'scope_final_console_20261028.txt').open('w',encoding='utf-8') as log:
        run = subprocess.run([sys.executable,str(HERE/'audit_scope.py'),legacy_name],stdout=log,stderr=subprocess.STDOUT)
    assert run.returncode==0, 'See scope_final_console_20261028.txt'
else:
    assert read(D/'scope_incremental_final_20261028.json')['changes']==changes, 'Production changed since partial closeout'
    assert all(sha(ROOT/x['path'])==x['after'] for x in read(HERE/legacy_name)['changes']), 'Legacy audit drift'
legacy = read(HERE/legacy_name)
prior_unexpected = {x['path']:x.get('after') for x in legacy_before['unexpected']}
new_unexpected = [x for x in legacy['unexpected'] if prior_unexpected.get(x['path'])!=x.get('after')]
new_semantic = {n:s['unexpected'] for n,s in legacy['semantics'].items() if not s['pass'] and s['unexpected']!=legacy_before['semantics'].get(n,{}).get('unexpected')}
assert not new_unexpected and not new_semantic, (new_unexpected,new_semantic)
scope = dict(observed_at=now(),baseline=baseline_path.name,baseline_sha256=sha(baseline_path),baseline_files=len(base),current_files=len(current),
    comparison='Union of before/current file paths, including additions and deletions',changes=changes,unexpected_incremental=unexpected,
    automatic_editor_side_effects=side_effects,protected_six=protected,protected_drift=protected_drift,prefab_semantics=sem,
    installed_asset_drift=drift,staged_production_drift=staged_drift,legacy_before='scope_SabretoothTiger_20261028_final.json',legacy_after=legacy_name,
    legacy_pass=legacy['pass'],legacy_unexpected_count=len(legacy['unexpected']),legacy_semantic_failure_count=sum(not s['pass'] for s in legacy['semantics'].values()),
    legacy_semantic_failures=[n for n,s in legacy['semantics'].items() if not s['pass']],new_unexpected_vs_preexisting_legacy=new_unexpected,new_semantic_failures=new_semantic,
    note='Existing historical differences preserved. No global PASS claim.')
write(D/'scope_incremental_final_20261028.json',scope)

runtime = read(D/'runtime_summary.json')
assert runtime['passes']==168 and runtime['failures']==0
assert [r['revision'] for r in runtime['runtime']]==['runtime_r02','runtime_updeath_r02']
frames = {}
for r in runtime['runtime']:
    folder=D/r['revision']; records=folder/'actual_frames.jsonl'
    assert sha(records)==r['records_sha256'].upper()
    rows=[json.loads(line) for line in records.read_text(encoding='utf-8').splitlines() if line.strip()]
    assert len(rows)==r['frames'] and all(a['frame']<b['frame'] for a,b in zip(rows,rows[1:]))
    assert len({x['file'] for x in rows})==len(rows)
    checks=(folder/'actual_runtime_checks.txt').read_text(encoding='utf-8').splitlines()
    assert sum(x.startswith('PASS ') for x in checks)==84 and not any(x.startswith('FAIL ') for x in checks)
    frames[r['revision']]={x['file']:sha(folder/x['file']) for x in rows}
    assert all(frames[r['revision']].values())
assert sum(len(x) for x in frames.values())==runtime['actual_frames']

note='Up复用revision_01并采用local_raster_revision_01去掉错误后脑口器；Down按用户同类网络故障继续授权补发唯一revision_02成功HTTP200，旧Down revision_01仍uncertain、未推定未收费，全部原证据保留。初轮虽168/0，实际时序审阅发现死亡后复用的侧身倒置，已否决并保留。最终side_reuse_repair_r02只在Scarab自有Walk副本新增Body三轴Euler常量0曲线，原侧图曲线/事件/时长/loop保持，未改源/共享动画或C#。最终runtime_r02和runtime_updeath_r02各84/0，共692真实帧。实际查看最终四方向、strip及10张时序/步态/愤怒细节板：橄榄赭色条带甲壳、双触角和六足，Up后脑无眼/口，Down橙色镜片眼、愤怒斜眼与死亡叉眼可辨；无尾翼。六足错相抬落、腿根收在甲壳下，头甲壳连接未见脱开，触角未碰血条；连续转向后的左右侧身均已直立且相位延续。受击/致死白闪结束，死亡全身倾斜淡出，自动回收和同实例复用后颜色/姿态恢复；暂停不变，恢复及2x/3x推进；抽样未见地面阴影。后脑下缘局部补色较简洁且大部分被胸甲覆盖，正背比侧图更接近轴向俯视，保留给用户最终美术判断。审阅方式为按时序真实PNG抽样，未播放GIF全片，也未逐张审完692帧；仅内部技术与视觉完成，user_approved=false。'
(D/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
visual_folder=D/'visual_review_final_r02_20261028'
sources=read(visual_folder/'sources.json')
sheets=sorted({x['sheet'] for x in sources['sources']})
assert len(sheets)==10 and len(sources['sources'])==256
assert {r['revision'] for r in sources['runtime_summary']}=={'runtime_r02','runtime_updeath_r02'}
unique=len({(x['revision'],x['source']) for x in sources['sources']})
write(visual_folder/'review.json',dict(observed_at=now(),status='completed_pending_user_art_review',user_approved=False,note=note,
    viewed_sheets=sheets,sample_slots=len(sources['sources']),distinct_actual_frame_samples=unique,source_manifest='sources.json',
    additional_viewed=['runtime_r02/four_directions.png','runtime_visual_strip.png'],method='Chronological actual PNG samples, walk cycles and angry details. No live GIF playback; not every frame reviewed.',
    rejected_previous='side_reuse_repair_r02/visual_rejection.json',final_install_manifest='installed_manifest.json',sources_sha256=sha(visual_folder/'sources.json'),
    viewed_sheet_sha256={p:sha(visual_folder/p) for p in sheets},final_version_binding='version_binding_final_20261028.json'))
runtime.update(status='runtime_and_internal_visual_review_complete_pending_user_art_review',visual_review_file='visual_review_final_r02_20261028/review.json')
write(D/'runtime_summary.json',runtime)

version_files = [D/p for p in ['installed_manifest.json','installed_verify.txt','art_selection.json','layout_adjustments.json','processing.json',
    'generation/Up/revision_01/raw.png','generation/Down/revision_02/raw.png','generation/Down/revision_02/result.json','generation/Down/revision_02/recovery_intent.json',
    'local_raster_revision_01/Up_sheet.png','local_raster_revision_01/processing.json','repair_up_rear_cap_20261028.py',
    'runtime_summary.json','runtime_visual_strip.png','side_reuse_repair_r02/repair.json','side_reuse_repair_r02/repair_mcp.json','repair_side_reuse_20261028.py',
    'record_note_utf8.txt','visual_review_final_r02_20261028/sources.json','visual_review_final_r02_20261028/review.json']]
for r in runtime['runtime']:
    folder=D/r['revision']
    version_files += [folder/'actual_frames.jsonl',folder/'actual_runtime_checks.txt',folder/'media_manifest.json',folder/'four_directions.png',D/(r['revision']+'_start.json'),D/(r['revision']+'_returned.json')]
    version_files += list(folder.glob('*.gif'))
version_files += [p for p in (D/'staged_art').iterdir() if p.is_file()]
version_files += list(visual_folder.glob('*.png'))
assert all(p.is_file() for p in version_files)
write(D/'version_binding_final_20261028.json',dict(observed_at=now(),final_install_manifest='installed_manifest.json',
    files={p.relative_to(D).as_posix():sha(p) for p in version_files},installed_files={x['path']:x['after'] for x in manifest['changes']},
    actual_png_frames=frames,frame_total=sum(len(x) for x in frames.values()),
    note='Final copied Walk reset repair preceded both r02 actual Play rounds; original generated sheets/source animations unchanged. Previous r01 evidence retained and visually rejected.'))

c=Client();project=c.identity()
refresh=c.tool('refresh_unity',dict(mode='force',scope='assets',compile='none',wait_for_ready=True))
c.identity()
cache_refresh=None
for attempt in range(4):
    state=c.resource('mcpforunity://editor/state');s=state['data']
    if not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']: break
    if attempt==0 and s.get('advice',{}).get('blocking_reasons')==['stale_status']:
        # Installed plugin OnUpdate deliberately skips snapshots when no state changes.
        # Rebuild the snapshot from actual Editor APIs; never alter readiness flags.
        cache_refresh=unwrap(c.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");var m=t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static);m.Invoke(null,new object[]{"Scarab_final_live_state_read"});return true;')))
        assert cache_refresh['success'] and cache_refresh['data']['result'] is True
    time.sleep(1)
else: raise RuntimeError('Editor state not ready; do not record completion')
errors=unwrap(c.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
probe=unwrap(c.tool('execute_code',dict(action='execute',code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};')))
assert probe['success']; observed=probe['data']['result']
assert not any(v for k,v in observed.items() if k!='scene') and observed['scene']=='Assets/Scenes/Boot.unity',observed
assert errors['success'] and errors['data']==[],errors
assert all(sha(ROOT/x['path'])==x['after'].upper() for x in manifest['changes'])
write(D/'final_validation_20261028.json',dict(observed_at=now(),project=project,refresh=refresh,cache_refresh=cache_refresh,state=state,errors=errors,probe=probe,
    final_install_manifest='installed_manifest.json',installed_asset_drift=[],runtime_summary_sha256=sha(D/'runtime_summary.json'),protocol_history=c.history))

before_progress=read(HERE/'progress.json')
before_count=sum(i['status'] in ['completed_pending_user_art_review','user_approved'] for i in before_progress['items'])
subprocess.run([sys.executable,str(HERE/'record_review.py'),'Scarab',note],check=True)
p=read(HERE/'progress.json'); item=next(i for i in p['items'] if i['name']=='Scarab')
historical={k:item[k] for k in ['blocked_reason','blocked_record','blocked_at'] if k in item}
item.setdefault('historical_blocked_records',[]).append(dict(historical,closed_at=now(),resolution='Authorized Down revision_02 returned; installed and repaired r02 verified and visually reviewed. Original Down revision_01 remains uncertain.'))
for k in ['blocked_reason','blocked_at','blocked_record']: item.pop(k,None)
item.update(current_blocked=False,recovery_in_progress=False,recovery_completed_at=now(),recovery_stage='recorded_pending_user_art_review',current_stage='recorded_pending_user_art_review',
    generation_revisions=dict(Up='revision_01',Down='revision_02'),final_animation_repair='Scarab/side_reuse_repair_r02/repair.json',
    final_install_manifest='Scarab/installed_manifest.json',final_visual_review='Scarab/visual_review_final_r02_20261028/review.json',
    final_validation='Scarab/final_validation_20261028.json',final_scope='Scarab/scope_incremental_final_20261028.json',
    prior_down_revision_01_outcome='uncertain_preserved',additional_network_recovery_requests=1)
assert p['completed_count']==before_count+1 and item['status']=='completed_pending_user_art_review' and not item['user_approved']
write(HERE/'progress.json',p)
gifs=read(HERE.parent/'AllGIF/manifest.json')
own=[x for x in gifs['files'] if x['source'].startswith('Remaining_20261024/Scarab/')]
current_gifs=[x for x in own if x['status']=='当前审核版本']
assert len(own)==24 and len(current_gifs)==12
assert all(sha(HERE.parent/x['source'])==x['sha256'] and sha(HERE.parent/'AllGIF'/x['file'])==x['sha256'] for x in own)
write(D/'gif_archive_verification_20261028.json',dict(observed_at=now(),total=gifs['count'],character_count=len(own),current_count=len(current_gifs),files=own,sha256_match=True))
chain.update(character_status_at_handoff=item['status'],completed_count_snapshot=p['completed_count'],current_stage='recorded_pending_user_art_review',
    resume_stage='Scarab r02 repaired, 168/0, 692 real frames, actual PNG visual review, record and GIF archive complete',
    last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Scarab/final_validation_20261028.json',updated_at=now(),current_blocked=False)
write(HERE/'conversation_chain.json',chain)
print(json.dumps(dict(completed=p['completed_count'],changes=len(changes),added=sum(x['before'] is None for x in changes),unexpected=len(unexpected),
    legacy_unexpected=len(legacy['unexpected']),new_legacy=len(new_unexpected),prefab_semantics=sem['pass'],samples=unique,probe=observed,
    gifs_total=gifs['count'],character_gifs=len(own),current_gifs=len(current_gifs)),ensure_ascii=False))
