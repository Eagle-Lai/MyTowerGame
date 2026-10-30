"""Bind reviewed Sheep r02 evidence, release Unity, record and archive this character only."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, re, subprocess, sys, time

D = Path(__file__).resolve().parent
H = D.parent
R = H.parents[2]
sys.path.insert(0, str(H))
from mcp_call import Client

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None

def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()

def unwrap(value):
    return value.get('structuredContent') or json.loads(value['content'][0]['text'])

chain = read(H / 'conversation_chain.json')
assert chain['state'] == 'active' and chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['current_character'] == 'Sheep'
assert chain['dispatch_token'] == 'scarabmounted-to-sheep-fd7d7a5afb264ca7a1691363ab276f5f'
assert not (D / 'final_validation_20261028.json').exists(), 'Inspect prior finalization before retry'
progress_before = read(H / 'progress.json')
assert progress_before['completed_count'] == 83
assert next(x for x in progress_before['items'] if x['name'] == 'Sheep')['status'] != 'completed_pending_user_art_review'

baseline = read(D / 'incremental_before_20261028.json')
before = {p: s.upper() for p, s in baseline['files'].items()}
current = {p.relative_to(R).as_posix(): sha(p) for folder in ['Assets', 'Packages', 'ProjectSettings', 'Luban'] for p in (R / folder).rglob('*') if p.is_file()}
changes = [dict(path=p, before=before.get(p), after=current.get(p)) for p in sorted(set(before) | set(current)) if before.get(p) != current.get(p)]
battle = 'Assets/Prefabs/Enemy/Enemy_Sheep.prefab'
art = 'Assets/_UIAssets/Monsters/Cattle/Sheep/Directions'
unexpected, side_effects = [], []
for change in changes:
    path = change['path']
    if path == battle or path.startswith(art + '/') or path == art + '.meta':
        continue
    if path == 'Assets/StreamingAssets/build_info' and current['Assets/Reporter/Editor/ReporterEditor.cs'] == before['Assets/Reporter/Editor/ReporterEditor.cs'] and re.fullmatch(r'Build from .+ at .+', (R / path).read_text(encoding='utf-8')):
        side_effects.append(dict(change, origin='Unmodified ReporterEditor InitializeOnLoad Play timestamp'))
    else:
        unexpected.append(change)
assert not unexpected, unexpected
protected = baseline['protected_six']
protected_drift = [p for p, s in protected.items() if p != battle and sha(R / p) != s.upper()]
assert not protected_drift, protected_drift

legacy_before = read(H / 'scope_Sheep_before_20261028.json')
legacy_after = read(H / 'scope_Sheep_final_20261028.json')
old_unexpected = {x['path']: x.get('after') for x in legacy_before['unexpected']}
assert {x['path']: x.get('after') for x in legacy_after['unexpected']} == old_unexpected
old_failures = {n: s['unexpected'] for n, s in legacy_before['semantics'].items() if not s['pass']}
new_failures = {n: s['unexpected'] for n, s in legacy_after['semantics'].items() if not s['pass']}
assert new_failures == old_failures
assert legacy_after['semantics']['Sheep']['pass']

manifest = read(D / 'installed_manifest.json')
assert all(sha(R / x['path']) == x['after'].upper() for x in manifest['changes'])
verify = manifest['verification']['data']['result']
assert verify['pass'] and (D / 'installed_verify.txt').read_text(encoding='utf-8') == verify['report']
preplay = read(D / 'preplay_version_binding_r02_20261028.json')
assert sha(D / 'installed_manifest.json') == preplay['installed_manifest_sha256']
assert all(sha(R / p) == s for p, s in preplay['installed_files'].items())
original_sprites = read(D / 'preplay_version_binding_20261028.json')['original_sprites']
prefab = (R / battle).read_text(encoding='utf-8-sig')
for fid, value in original_sprites.items():
    block = re.search(r'^--- !u!212 &' + fid + r'\s*\n(.*?)(?=^--- !u!|\Z)', prefab, re.M | re.S)
    assert block and re.search(r'^  m_Sprite: .+$', block[1], re.M)[0] == value, fid
offline = read(D / 'offline_review_20261028.json')
assert all(sha(D / 'staged_art' / p) == s for p, s in offline['staging_files'].items())
assert all(sha(D / 'staged_art' / p) == sha(R / art / p) for p in ['Sheep_Directions.png', 'Sheep_Directions.layout.json', 'Sheep_Directions.sprites.json'])
for direction in ['Up', 'Down']:
    result = read(D / 'generation' / direction / 'result.json')
    assert result['status'] == 200 and result['bytes'] == (D / 'generation' / direction / 'raw.png').stat().st_size
    assert sha(D / 'generation' / direction / 'raw.png') == offline['raw_sha256'][direction]
repair = read(D / 'head_reuse_repair_r01/repair.json')
assert repair['preservation_checks']['originalCurvesEventsTimingPreserved']
assert repair['preservation_checks']['originalFloatBindings'] == 125 and repair['preservation_checks']['afterFloatBindings'] == 128
old_pose = read(D / 'reuse_live_inspection_runtime_head_probe_r03_20261028.json')
pose = read(D / 'reuse_live_inspection_runtime_r02_20261028.json')
assert old_pose['initial_horizontal_head_y'] == [0.7] and old_pose['after_reuse_horizontal_head_y'] == [0.4]
assert pose['initial_horizontal_head_y'] == [0.7] and pose['after_reuse_horizontal_head_y'] == [0.7]

scope = dict(observed_at=now(), baseline='incremental_before_20261028.json', baseline_sha256=sha(D / 'incremental_before_20261028.json'), baseline_files=len(before), current_files=len(current), comparison='Union of before/current paths including additions and deletions', changes=changes, unexpected_incremental=unexpected, automatic_editor_side_effects=side_effects, protected_six=protected, protected_drift=protected_drift, original_sprite_contracts=original_sprites, prefab_semantics=legacy_after['semantics']['Sheep'], installed_asset_drift=[], staged_production_drift=[], legacy_before='scope_Sheep_before_20261028.json', legacy_after='scope_Sheep_final_20261028.json', legacy_pass=legacy_after['pass'], legacy_unexpected_count=len(old_unexpected), legacy_semantic_failures=list(new_failures), new_unexpected_vs_preexisting_legacy=[], new_semantic_failures={}, note='Historical global differences remain; no global PASS claim')
write(D / 'scope_incremental_final_20261028.json', scope)

runtime = read(D / 'runtime_summary.json')
assert runtime['passes'] == 168 and runtime['failures'] == 0
assert [x['revision'] for x in runtime['runtime']] == ['runtime_r02', 'runtime_updeath_r02']
frames = {}
for item in runtime['runtime']:
    folder = D / item['revision']
    assert sha(folder / 'actual_frames.jsonl') == item['records_sha256']
    rows = [json.loads(line) for line in (folder / 'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    checks = (folder / 'actual_runtime_checks.txt').read_text(encoding='utf-8').splitlines()
    assert sum(x.startswith('PASS ') for x in checks) == 84 and not any(x.startswith('FAIL ') for x in checks)
    assert len(rows) == item['frames'] and all(a['frame'] < b['frame'] for a, b in zip(rows, rows[1:]))
    frames[item['revision']] = {x['file']: sha(folder / x['file']) for x in rows}
    assert len(frames[item['revision']]) == len(rows) and all(frames[item['revision']].values())
assert sum(len(x) for x in frames.values()) == runtime['actual_frames'] == 676
visual = D / 'visual_review_final_r02_20261028'
sources = read(visual / 'sources.json')
sheets = sorted({x['sheet'] for x in sources['sources']})
assert len(sheets) == 10 and len(sources['sources']) == 256
assert {x['revision'] for x in sources['runtime_summary']} == {'runtime_r02', 'runtime_updeath_r02'}
unique = len({(x['revision'], x['source']) for x in sources['sources']})
additional = ['runtime_r02/four_directions.png', 'runtime_visual_strip.png', 'runtime_r02/frames/DeathAutoRecycle_00155.png', 'runtime_r02/frames/ContinuousTurns_00320.png']
note = ('Up/Down初次生成各一次HTTP200，未重试；Up选local_raster_revision_02，局部闭合空心颈环并用同图完整后蹄替换前向蹄片，Down用原始生成。原图、本地首版与两次被否决布局均保留。最终布局revision03让四短蹄根藏入奶油云状羊毛，保留赭斑、淡金脸、下垂耳，无角无新增尾；Tail仅透明兼容切片且rig节点移除。原侧身八个Sprite PPtr与非美术语义保留。真实Play额外读数发现共享Goat Death把侧头y从0.7降到0.4、复用未复位；只在Sheep自有Walk副本新增Head局部位置三轴常量[-1,0.7,0]，125条原float绑定、PPtr/事件/时长/loop保留，未改共享源动画或C#。修复后现场同实例复用读数y=0.7，旧r01和探针证据保留，其中head_probe_r02无有效姿态样本不作修复证据。最终runtime_r02/runtime_updeath_r02各84 PASS/0 FAIL，共676张真实Unity帧。实际查看四方向、strip、10张时序/步态/愤怒细节板（256采样位/' + str(unique) + '张不同实际帧），另看Down死亡与复用后Left原尺寸PNG。Up后脑无眼口，Down正常圆眼、攻击斜眼与死亡空白眼/吐舌可辨；四蹄错相并有轻微摇摆，抽样未见断开的腿根、颈环空洞、底色污染或阴影。受击白闪结束，双向死亡倾斜淡出，自动回收/复用恢复正常；暂停姿态和动画时间保持，恢复及2x/3x推进。正背轴向俯视与原侧图的体型比例、羊毛遮住远侧腿的程度留给用户最终美术判断。审阅为真实PNG时序抽样，未实时播放GIF全片、未逐张审完676帧；仅内部技术与视觉完成，user_approved=false。')
(D / 'record_note_utf8.txt').write_text(note + '\n', encoding='utf-8')
write(visual / 'review.json', dict(observed_at=now(), status='completed_pending_user_art_review', user_approved=False, note=note, viewed_sheets=sheets, sample_slots=len(sources['sources']), distinct_actual_frame_samples=unique, source_manifest='sources.json', additional_viewed=additional, additional_viewed_sha256={p: sha(D / p) for p in additional}, method='Actual chronological PNG samples, gait cycles, angry details and two full frames; no live GIF playback or exhaustive all-frame visual inspection', rejected_previous='head_reuse_repair_r01/rejected_previous.json', final_install_manifest='installed_manifest.json', sources_sha256=sha(visual / 'sources.json'), viewed_sheet_sha256={p: sha(visual / p) for p in sheets}, final_version_binding='version_binding_final_20261028.json'))
runtime.update(status='runtime_and_internal_visual_review_complete_pending_user_art_review', visual_review_file='visual_review_final_r02_20261028/review.json')
write(D / 'runtime_summary.json', runtime)

files = [D / p for p in ['installed_manifest.json', 'installed_verify.txt', 'art_selection.json', 'anatomy_plan.json', 'layout_adjustments.json', 'processing.json', 'offline_review_20261028.json', 'reference_review_20261028.json', 'local_raster_revision_02/Up_sheet.png', 'local_raster_revision_02/processing.json', 'local_raster_revision_02/review.json', 'head_reuse_repair_r01/repair.json', 'head_reuse_repair_r01/repair_mcp.json', 'head_reuse_repair_r01/rejected_previous.json', 'repair_head_position_20261028.py', 'preplay_version_binding_20261028.json', 'preplay_version_binding_r02_20261028.json', 'source_animation_contracts_20261028.json', 'source_animation_contracts_detail_20261028.json', 'source_death_reuse_probe_20261028.json', 'reuse_live_inspection_runtime_head_probe_r03_20261028.json', 'reuse_live_inspection_runtime_r02_20261028.json', 'runtime_summary.json', 'runtime_visual_strip.png', 'record_note_utf8.txt', 'visual_review_final_r02_20261028/sources.json', 'visual_review_final_r02_20261028/review.json', 'scope_incremental_final_20261028.json']]
for direction in ['Up', 'Down']:
    files += [D / 'generation' / direction / p for p in ['raw.png', 'result.json', 'generation_intent.json', 'request.json', 'prompt.txt', 'review_20261028.json']]
for item in runtime['runtime']:
    folder = D / item['revision']
    files += [folder / p for p in ['actual_frames.jsonl', 'actual_runtime_checks.txt', 'media_manifest.json', 'four_directions.png']]
    files += list(folder.glob('*.gif'))
    files += [D / (item['revision'] + p) for p in ['_start.json', '_returned.json']]
files += [p for p in (D / 'staged_art').iterdir() if p.is_file()] + list(visual.glob('*.png'))
assert all(p.is_file() for p in files), [str(p) for p in files if not p.is_file()]
write(D / 'version_binding_final_20261028.json', dict(observed_at=now(), final_install_manifest='installed_manifest.json', files={p.relative_to(D).as_posix(): sha(p) for p in files}, installed_files={x['path']: x['after'] for x in manifest['changes']}, actual_png_frames=frames, frame_total=runtime['actual_frames'], note='Selected images, local derivation, layout, original contracts, own Walk repair and live before/after pose, install and all final actual PNG frames bound by SHA256. Final r02 preplay production hashes still match. Previous revisions remain historical.'))

client = Client()
project = client.identity()
refresh = client.tool('refresh_unity', dict(mode='force', scope='assets', compile='none', wait_for_ready=True))
client.identity()
cache_refresh = None
for attempt in range(4):
    state = client.resource('mcpforunity://editor/state')
    observed = state['data']
    if not observed['compilation']['is_compiling'] and not observed['compilation']['is_domain_reload_pending'] and not observed['assets']['is_updating'] and observed['advice']['ready_for_tools']:
        break
    if attempt == 0 and observed.get('advice', {}).get('blocking_reasons') == ['stale_status']:
        cache_refresh = unwrap(client.tool('execute_code', dict(action='execute', code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"Sheep_final_live_state_read"});return true;')))
        assert cache_refresh['success'] and cache_refresh['data']['result'] is True
    time.sleep(1)
else:
    raise RuntimeError('Unity not ready; do not record')
errors = unwrap(client.tool('read_console', dict(action='get', types=['error'], count='50', format='json')))
probe = unwrap(client.tool('execute_code', dict(action='execute', code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};')))
assert probe['success']
released = probe['data']['result']
assert not any(v for k, v in released.items() if k != 'scene') and released['scene'] == 'Assets/Scenes/Boot.unity'
assert errors['success'] and errors['data'] == []
assert all(sha(R / x['path']) == x['after'].upper() for x in manifest['changes'])
write(D / 'final_validation_20261028.json', dict(observed_at=now(), project=project, refresh=refresh, cache_refresh=cache_refresh, state=state, errors=errors, probe=probe, final_install_manifest='installed_manifest.json', installed_asset_drift=[], runtime_summary_sha256=sha(D / 'runtime_summary.json'), version_binding_sha256=sha(D / 'version_binding_final_20261028.json'), scope_sha256=sha(D / 'scope_incremental_final_20261028.json'), protocol_history=client.history))

subprocess.run([sys.executable, str(H / 'character_step.py'), 'record', 'Sheep', note], check=True)
progress = read(H / 'progress.json')
item = next(x for x in progress['items'] if x['name'] == 'Sheep')
assert progress['completed_count'] == 84 and item['status'] == 'completed_pending_user_art_review' and item['user_approved'] is False
item.update(current_stage='recorded_pending_user_art_review', final_install_manifest='Sheep/installed_manifest.json', final_animation_repair='Sheep/head_reuse_repair_r01/repair.json', final_visual_review='Sheep/visual_review_final_r02_20261028/review.json', final_validation='Sheep/final_validation_20261028.json', final_scope='Sheep/scope_incremental_final_20261028.json', final_version_binding='Sheep/version_binding_final_20261028.json')
write(H / 'progress.json', progress)
gifs = read(H.parent / 'AllGIF/manifest.json')
own = [x for x in gifs['files'] if x['source'].startswith('Remaining_20261024/Sheep/')]
active = [x for x in own if x['status'] == '当前审核版本']
sources_on_disk = {p.relative_to(H.parent).as_posix() for p in D.rglob('*.gif')}
assert {x['source'] for x in own} == sources_on_disk
assert len(active) == 12 and {x['source'].split('/')[2] for x in active} == {'runtime_r02', 'runtime_updeath_r02'}
assert all(sha(H.parent / x['source']) == x['sha256'] and sha(H.parent / 'AllGIF' / x['file']) == x['sha256'] for x in own)
write(D / 'gif_archive_verification_20261028.json', dict(observed_at=now(), total=gifs['count'], character_count=len(own), current_count=len(active), files=own, sha256_match=True, all_available_character_gifs_archived=True))
chain.update(character_status_at_handoff=item['status'], completed_count_snapshot=progress['completed_count'], current_stage='recorded_pending_user_art_review', last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Sheep/final_validation_20261028.json', updated_at=now())
write(H / 'conversation_chain.json', chain)
print(json.dumps(dict(completed=progress['completed_count'], production_changes=len(changes), production_additions=sum(x['before'] is None for x in changes), unexpected_incremental=len(unexpected), legacy_unexpected=len(old_unexpected), legacy_semantic_failures=list(new_failures), sample_slots=256, distinct_actual_samples=unique, frames=runtime['actual_frames'], probe=released, gifs_total=gifs['count'], sheep_gifs=len(own), current_gifs=len(active)), ensure_ascii=False))
