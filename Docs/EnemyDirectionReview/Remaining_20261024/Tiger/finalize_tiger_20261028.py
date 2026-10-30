"""Bind the reviewed Tiger installation and record it without rebuilding assets."""
from session_tiger import *
import time

chain = owner()
assert URL == 'http://127.0.0.1:8088/mcp'
assert not (D/'final_validation_20261028.json').exists(), 'Inspect existing finalization before resuming'
progress = read(H/'progress.json')
assert progress['completed_count'] == 86
item = next(x for x in progress['items'] if x['name'] == NAME)
assert item['status'] != 'completed_pending_user_art_review' and not item.get('user_approved')

baseline = read(D/'incremental_before_20261028.json')
before = {p:s.upper() for p,s in baseline['files'].items()}
current = inventory()
assert len(before) == 5278
battle = 'Assets/Prefabs/Enemy/Enemy_Tiger.prefab'
art = 'Assets/_UIAssets/Monsters/Felines/Tiger/Directions'
changes = [dict(path=p,before=before.get(p),after=current.get(p))
           for p in sorted(set(before)|set(current)) if before.get(p) != current.get(p)]
unexpected, side_effects = [], []
for change in changes:
    path = change['path']
    if path == battle or path == art+'.meta' or path.startswith(art+'/'):
        continue
    if (path == 'Assets/StreamingAssets/build_info'
            and current['Assets/Reporter/Editor/ReporterEditor.cs'] == before['Assets/Reporter/Editor/ReporterEditor.cs']
            and re.fullmatch(r'Build from .+ at .+', (R/path).read_text(encoding='utf-8'))):
        side_effects.append(dict(change,origin='Unmodified ReporterEditor InitializeOnLoad Play timestamp'))
    else:
        unexpected.append(change)
assert not unexpected, unexpected
protected_drift = [p for p,s in baseline['protected_six'].items() if p != battle and sha(R/p) != s.upper()]
assert not protected_drift, protected_drift
assert all(sha(D/'reference'/Path(p).name) == s.upper() for p,s in baseline['protected_six'].items())
legacy_before = read(H/'scope_Tiger_before_20261028.json')
legacy_after = read(H/'scope_Tiger_final_20261028.json')
old_unexpected = {x['path']:x.get('after') for x in legacy_before['unexpected']}
assert {x['path']:x.get('after') for x in legacy_after['unexpected']} == old_unexpected
old_failures = {n:s['unexpected'] for n,s in legacy_before['semantics'].items() if not s['pass']}
new_failures = {n:s['unexpected'] for n,s in legacy_after['semantics'].items() if not s['pass']}
assert old_failures == new_failures and legacy_after['semantics'][NAME]['pass']

manifest = read(D/'installed_manifest.json')
assert all(sha(R/x['path']) == x['after'].upper() for x in manifest['changes'])
verify = manifest['verification']['data']['result']
assert verify['pass'] and (D/'installed_verify.txt').read_text(encoding='utf-8') == verify['report']
assert all(x['path'] == battle or x['path'].startswith(art+'/') for x in manifest['changes'])

def sprite_contract(path):
    text = path.read_text(encoding='utf-8-sig')
    blocks = list(re.finditer(r'^--- !u!(\d+) &(-?\d+)\s*\n(.*?)(?=^--- !u!|\Z)',text,re.M|re.S))
    objects = {m[2]:re.search(r'^  m_Name: (.+)$',m[3],re.M)[1] for m in blocks if m[1] == '1'}
    result = {}
    for m in blocks:
        if m[1] != '212': continue
        go = re.search(r'^  m_GameObject: \{fileID: (-?\d+)\}',m[3],re.M)[1]
        result[m[2]] = dict(name=objects[go],game_object=go,sprite=re.search(r'^  m_Sprite: (.+)$',m[3],re.M)[1])
    return result

original = sprite_contract(D/'before'/battle)
installed_sprites = sprite_contract(R/battle)
assert len(original) == 10 and sum(x['name'] != 'Shadow' for x in original.values()) == 9
assert {'Bg','Fill'}.issubset({x['name'] for x in original.values()})
for fid,value in original.items():
    if value['name'] == 'Shadow': assert fid not in installed_sprites
    else: assert installed_sprites[fid] == value, fid
sprite_evidence = dict(observed_at=now(),before=original,original_count=10,retained_non_shadow_count=9,
    included_hp_sprites=True,only_removed_original_sprite='Shadow',all_retained_pptr_unchanged=True,
    baseline_prefab_sha256=sha(D/'before'/battle),current_prefab_sha256=sha(R/battle))

source_contracts = read(D/'source_animation_contracts_20261028.json')['contracts']['data']['result']['clips']
clips = {x['name']:x for x in source_contracts}
euler = {n:[b for b in clips[n]['bindings'] if b['path']=='Body' and 'localEulerAnglesRaw.' in b['property']]
         for n in ['Walk','Death']}
assert all(len(v)==3 for v in euler.values())
assert all(k['value']==0 for b in euler['Death'] for k in b['keys'])
assert {n:len(c['bindings']) for n,c in clips.items()} == {'Ready':21,'Attack':36,'Walk':24,'Death':39}
reuse_evidence = dict(observed_at=now(),source_contract='source_animation_contracts_20261028.json',
    body_euler_bindings=euler,repair_required=False,own_animation_patch=False,
    reason='Source Feline Walk already animates Body Euler x/y/z and Death Body Euler is zero. Original horizontal curves/events/timing/loop passed installed Verify. No Swine-style reset patch was added.',
    limitation='No separate live pre/post-reuse Euler measurement or separately captured preplay-version binding; final manifest predates both runtime rounds and final hashes match.')

preinstall = read(D/'preinstall_review_20261028.json')
assert {p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()} == preinstall['staged']
assert len(preinstall['alpha']) == 14 and all(x['internal_transparent_holes']==0 for x in preinstall['alpha'].values())
for suffix in ['.png','.sprites.json','.layout.json']:
    assert sha(D/'staged_art'/('Tiger_Directions'+suffix)) == sha(R/art/('Tiger_Directions'+suffix))
selection = read(D/'art_selection.json')
assert selection['Up'] == 'local_raster_revision_01/Up_sheet.png' and selection['Down'] == 'generation/Down/raw.png'
for path,expected_bytes in [('generation/Up/revision_01',1421271),('generation/Down',1553528)]:
    result = read(D/path/'result.json')
    assert result['status'] == 200 and result['bytes'] == (D/path/'raw.png').stat().st_size == expected_bytes
application = read(D/'standing_recovery_application_20261028.json')
assert application['owner_thread_id'] == chain['owner_thread_id'] and application['dispatch_token'] == TOKEN
assert sha(H/'standing_network_recovery_authorization_20261028.json') == application['authorization_sha256'].upper()
assert all(sha(D/x['path']) == x['sha256'].upper() for x in application['preserved_evidence'])
recovery = read(D/'generation/Up/revision_01/recovery_intent.json')
assert recovery['additional_attempt'] == 1 and recovery['application_sha256'].upper() == sha(D/'standing_recovery_application_20261028.json')
assert len(list((D/'generation/Up').glob('revision_*/request.json'))) == 1
assert not (D/'generation/Up/raw.png').exists() and not (D/'generation/Up/result.json').exists()
assert 'curl transport failed 55' in read(D/'generation/Up/uncertain_result.json')['message']
derivation = read(D/'local_raster_revision_01/derivation.json')
assert sha(D/derivation['parent']) == derivation['parent_sha256']
assert sha(D/'local_raster_revision_01/Up_sheet.png') == derivation['output_sha256']
repair = read(D/'chroma_pinhole_repair_20261028.json')
assert repair['total'] == 27 and sha(D/'staged_art/Tiger_Directions.png') == repair['atlas_sha256']
assert all(sha(D/'staged_art'/p['part']) == p['after_file_sha256'] for p in repair['parts'])

runtime = read(D/'runtime_summary.json')
assert runtime['passes'] == 168 and runtime['failures'] == 0 and runtime['actual_frames'] == 676
assert [x['revision'] for x in runtime['runtime']] == ['runtime_r01','runtime_updeath_r01']
assert datetime.fromisoformat(manifest['installed_at']) < datetime.now(timezone(timedelta(hours=8)))
frames, rows_by_revision = {}, {}
for item_runtime in runtime['runtime']:
    revision = item_runtime['revision']; folder = D/revision
    assert sha(folder/'actual_frames.jsonl') == item_runtime['records_sha256']
    rows = [json.loads(line) for line in (folder/'actual_frames.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    checks = (folder/'actual_runtime_checks.txt').read_text(encoding='utf-8').splitlines()
    assert sum(x.startswith('PASS ') for x in checks) == 84 and not any(x.startswith('FAIL ') for x in checks)
    assert len(rows) == item_runtime['frames'] == 338
    assert all(a['frame'] < b['frame'] and a['realtime'] < b['realtime'] for a,b in zip(rows,rows[1:]))
    frames[revision] = {x['file']:sha(folder/x['file']) for x in rows}
    rows_by_revision[revision] = {x['file']:x for x in rows}
    assert len(frames[revision]) == len(rows) and all(frames[revision].values())
    assert len(list(folder.glob('*.gif'))) == 6
assert sum(map(len,frames.values())) == 676
visual = D/'visual_review_final_20261028'; sources = read(visual/'sources.json')
sheets = sorted({x['sheet'] for x in sources['sources']})
unique = len({(x['revision'],x['source']) for x in sources['sources']})
assert len(sheets) == 10 and len(sources['sources']) == 256 and unique == 228
for sample in sources['sources']:
    assert sample['source'] in frames[sample['revision']]
    assert sample['frame'] == rows_by_revision[sample['revision']][sample['source']]['frame']
additional = ['runtime_r01/four_directions.png','runtime_visual_strip.png',
    'runtime_r01/frames/DeathAutoRecycle_00164.png',
    'runtime_updeath_r01/frames/DeathAutoRecycle_00164.png',
    'runtime_r01/frames/ContinuousTurns_00303.png']
assert all((D/p).is_file() for p in additional)

client = Client();project = client.identity();cache_refresh = None
errors = unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
assert errors['data'] == []
for attempt in range(4):
    state = client.resource('mcpforunity://editor/state');s = state['data']
    if (not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending']
            and not s['assets']['is_updating'] and s['advice']['ready_for_tools']):
        break
    if attempt == 0 and s['advice'].get('blocking_reasons') == ['stale_status']:
        cache_refresh = unwrap(client.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"Tiger_final_live_state_read"});return true;')))
    time.sleep(1)
else:
    raise RuntimeError('Unity not ready; do not record')
live = probe(client)
assert live['scene'] == 'Assets/Scenes/Boot.unity' and not any(v for k,v in live.items() if k != 'scene'), live
assert all(sha(R/x['path']) == x['after'].upper() for x in manifest['changes'])

write(D/'original_sprite_contracts_20261028.json',sprite_evidence)
write(D/'source_death_reuse_contract_20261028.json',reuse_evidence)
write(D/'scope_incremental_final_20261028.json',dict(
    observed_at=now(),baseline='incremental_before_20261028.json',baseline_sha256=sha(D/'incremental_before_20261028.json'),
    baseline_files=len(before),current_files=len(current),comparison='Union of before/current paths including additions and deletions',
    changes=changes,unexpected_incremental=unexpected,automatic_editor_side_effects=side_effects,
    protected_six=baseline['protected_six'],protected_drift=protected_drift,
    original_sprite_contracts='original_sprite_contracts_20261028.json',retained_non_shadow_sprite_count=9,
    prefab_semantics=legacy_after['semantics'][NAME],installed_asset_drift=[],staged_production_drift=[],
    staged_changes_since_preinstall_review=[],final_staging_alpha=preinstall['alpha'],
    legacy_before='scope_Tiger_before_20261028.json',legacy_after='scope_Tiger_final_20261028.json',
    legacy_pass=legacy_after['pass'],legacy_unexpected_count=len(old_unexpected),legacy_semantic_failures=list(new_failures),
    new_unexpected_vs_preexisting_legacy=[],new_semantic_failures={},
    note='Historical global differences remain; no global PASS claim. Only Tiger battle/Directions plus documented automatic Reporter timestamp.'))
note = ('Up初次Curl55发送中断、无HTTP/raw/result，原结果与可能计费仍不明，证据保留。已回读原始人类常设授权，同类不明网络失败可静默有界恢复；仅将现有门禁扩展至Tiger Up该确切证据、保留参数与两次额外上限。Up revision_01第1次额外请求HTTP200成功，未用第2次；Down初次请求HTTP200。原raw完整保留。Up选local_raster_revision_01/Up_sheet.png，仅以同后跟完好半侧镜像去除后足侧爪痕；Down选原raw。实际源图为金橙虎、赭条斑、奶油色嘴与颊毛、头上一对圆耳、四宽爪足和一条细长条纹尾；无额卷、鬃毛、鞍具或剑齿。明确切片矩形保留Down越过半页的颈部、裁去两方向尾根大圆垫，按实际实心尾干量pivot；四足根藏于身内、后脑盖颈帽，Up后脑无脸无内耳，Down正常/攻击张嘴/死亡空白眼短舌可辨。27个封闭1至4像素透明针孔仅以近邻原色修复，14原尺寸切片内部透明孔0。原10 SpriteRenderer中9个非Shadow含HP PPtr保持，仅移除战斗Shadow。源Feline Walk已含Body Euler三轴、Death旋转为0，无需Swine式复位；原水平曲线/事件/时长/loop Verify通过，不改共享动画或C#。最终安装后未改生产文件；没有单独预运行版本绑定或现场复用Euler量测，不伪称已测。runtime_r01与runtime_updeath_r01各84 PASS/0 FAIL、338帧，合计168/0、676真实PNG，均安全回Boot。实际看最终四方向/strip、全部10张时序/步态/愤怒板（256采样位、228张不同实际帧），另看Down死亡、Up死亡和复用后Left三张原尺寸PNG。采样可见足摆/头身尾摇、原侧跳步、连续四向、攻击嘴切换、受击白闪、双向倾斜淡出回收、复用正常侧向、暂停静止及1x/2x/3x推进。未见部件断开、重复耳、紫底残留或地面阴影；死亡半透明阶段可透见分层重叠轮廓。正背视图比原侧图更窄、质感更平滑，最终美术判断交用户。方法仅真实PNG时序抽样，未实时全播GIF、未逐张审完676帧。实现与内部审阅完成，user_approved=false。')
(D/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
write(visual/'review.json',dict(observed_at=now(),status='completed_pending_user_art_review',user_approved=False,
    note=note,viewed_sheets=sheets,sample_slots=256,distinct_actual_frame_samples=unique,
    source_manifest='sources.json',sources_sha256=sha(visual/'sources.json'),
    viewed_sheet_sha256={p:sha(visual/p) for p in sheets},additional_viewed=additional,
    additional_viewed_sha256={p:sha(D/p) for p in additional},
    method='Chronological actual PNG sampling, gait-cycle and angry sheets, three full runtime PNGs; no live GIF playback or exhaustive all-frame review',
    limitations=['No separately captured preplay-version binding','No live pre/post-reuse Euler measurement','Art remains for user review'],
    final_version_binding='version_binding_final_20261028.json'))
runtime.update(status='runtime_and_internal_visual_review_complete_pending_user_art_review',
    visual_review_file='visual_review_final_20261028/review.json')
write(D/'runtime_summary.json',runtime)

files = [D/p for p in ['installed_manifest.json','installed_verify.txt','art_selection.json','anatomy_plan.json',
    'layout_adjustments.json','processing.json','preinstall_review_20261028.json','reference_review_20261028.json',
    'original_sprite_contracts_20261028.json','source_animation_contracts_20261028.json','source_death_reuse_contract_20261028.json',
    'chroma_pinhole_repair_20261028.json','standing_recovery_application_20261028.json',
    'runtime_summary.json','runtime_visual_strip.png','record_note_utf8.txt',
    'visual_review_final_20261028/sources.json','visual_review_final_20261028/review.json',
    'scope_incremental_final_20261028.json']]
files += [p for f in ['generation','local_raster_revision_01','staged_art'] for p in (D/f).rglob('*') if p.is_file()]
for item_runtime in runtime['runtime']:
    revision = item_runtime['revision'];folder = D/revision
    files += [folder/p for p in ['actual_frames.jsonl','actual_runtime_checks.txt','media_manifest.json','four_directions.png']]
    files += list(folder.glob('*.gif')) + [D/(revision+p) for p in ['_start.json','_returned.json']]
files += list(visual.glob('*.png'))
assert all(p.is_file() for p in files), [str(p) for p in files if not p.is_file()]
write(D/'version_binding_final_20261028.json',dict(observed_at=now(),final_install_manifest='installed_manifest.json',
    files={p.relative_to(D).as_posix():sha(p) for p in sorted(set(files))},
    installed_files={x['path']:x['after'].upper() for x in manifest['changes']},
    production_scope_files={x['path']:x['after'] for x in changes if x['path'] not in {s['path'] for s in side_effects}},
    external_evidence={'Docs/EnemyDirectionReview/Remaining_20261024/standing_network_recovery_authorization_20261028.json':sha(H/'standing_network_recovery_authorization_20261028.json')},
    actual_png_frames=frames,frame_total=676,
    note='Original uncertain/successful requests and raw, authorized recovery application, local derivation, final staging/installation, actual viewed sheets and all 676 actual PNG SHA256. No invented preplay binding.'))
write(D/'final_validation_20261028.json',dict(observed_at=now(),transport=URL,project=project,state=state,
    cache_refresh=cache_refresh,errors=errors,live=live,installed_asset_drift=[],
    final_install_manifest='installed_manifest.json',runtime_summary_sha256=sha(D/'runtime_summary.json'),
    version_binding_sha256=sha(D/'version_binding_final_20261028.json'),
    scope_sha256=sha(D/'scope_incremental_final_20261028.json'),protocol_history=client.history))

owner()
run('character_step.py','record',NAME,note)
progress = read(H/'progress.json');item = next(x for x in progress['items'] if x['name'] == NAME)
assert progress['completed_count'] == 87 and item['status'] == 'completed_pending_user_art_review' and item['user_approved'] is False
item.update(current_stage='recorded_pending_user_art_review',final_install_manifest='Tiger/installed_manifest.json',
    final_visual_review='Tiger/visual_review_final_20261028/review.json',final_validation='Tiger/final_validation_20261028.json',
    final_scope='Tiger/scope_incremental_final_20261028.json',final_version_binding='Tiger/version_binding_final_20261028.json',
    initial_up_outcome='uncertain_preserved',up_extra_network_requests=1)
write(H/'progress.json',progress)
gifs = read(H.parent/'AllGIF/manifest.json')
own = [x for x in gifs['files'] if x['source'].startswith('Remaining_20261024/Tiger/')]
active = [x for x in own if x['status'] == '当前审核版本']
assert {x['source'] for x in own} == {p.relative_to(H.parent).as_posix() for p in D.rglob('*.gif')}
assert len(own) == len(active) == 12 and {x['source'].split('/')[2] for x in active} == {'runtime_r01','runtime_updeath_r01'}
assert gifs['count'] == 1390
assert all(sha(H.parent/x['source']) == x['sha256'] and sha(H.parent/'AllGIF'/x['file']) == x['sha256'] for x in own)
write(D/'gif_archive_verification_20261028.json',dict(observed_at=now(),total=gifs['count'],character_count=len(own),
    current_count=len(active),files=own,sha256_match=True,all_available_character_gifs_archived=True))
chain = owner()
chain.update(character_status_at_handoff=item['status'],completed_count_snapshot=87,current_stage='recorded_pending_user_art_review',
    last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Tiger/final_validation_20261028.json',updated_at=now())
write(H/'conversation_chain.json',chain)
print(json.dumps(dict(completed=87,production_changes=len(changes),production_additions=sum(x['before'] is None for x in changes),
    unexpected_incremental=len(unexpected),legacy_unexpected=len(old_unexpected),legacy_semantic_failures=list(new_failures),
    sample_slots=256,distinct_actual_samples=unique,frames=676,live=live,gifs_total=gifs['count'],tiger_gifs=len(own)),ensure_ascii=False))
