"""Close only the reviewed Swine r02 installation; never rebuild production assets."""
from session_swine import *
import time
from PIL import Image
import numpy as np

chain = owner()
assert URL == 'http://127.0.0.1:8088/mcp'
assert not (D/'final_validation_20261028.json').exists(), 'Inspect any prior finalization first'
progress = read(H/'progress.json')
assert progress['completed_count'] == 85
item = next(x for x in progress['items'] if x['name'] == NAME)
assert item['status'] != 'completed_pending_user_art_review' and not item.get('user_approved')

baseline = read(D/'incremental_before_20261028.json')
before = {p:s.upper() for p,s in baseline['files'].items()}
current = inventory()
assert len(before) == 5258
changes = [dict(path=p,before=before.get(p),after=current.get(p))
           for p in sorted(set(before)|set(current)) if before.get(p) != current.get(p)]
battle = 'Assets/Prefabs/Enemy/Enemy_Swine.prefab'
art = 'Assets/_UIAssets/Monsters/Pigs/Swine/Directions'
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
legacy_before = read(H/'scope_Swine_before_20261028.json')
legacy_after = read(H/'scope_Swine_r02_final_20261028.json')
old_unexpected = {x['path']:x.get('after') for x in legacy_before['unexpected']}
assert {x['path']:x.get('after') for x in legacy_after['unexpected']} == old_unexpected
old_failures = {n:s['unexpected'] for n,s in legacy_before['semantics'].items() if not s['pass']}
new_failures = {n:s['unexpected'] for n,s in legacy_after['semantics'].items() if not s['pass']}
assert old_failures == new_failures and legacy_after['semantics'][NAME]['pass']

manifest = read(D/'installed_manifest.json')
assert all(sha(R/x['path']) == x['after'].upper() for x in manifest['changes'])
verify = manifest['verification']['data']['result']
assert verify['pass'] and (D/'installed_verify.txt').read_text(encoding='utf-8') == verify['report']
preplay = read(D/'preplay_version_binding_r02_20261028.json')
assert sha(D/'installed_manifest.json') == preplay['installed_manifest_sha256']
assert all(sha(R/p) == s for p,s in preplay['installed_files'].items())
original = read(D/'original_sprite_contracts_20261028.json')
prefab = (R/battle).read_text(encoding='utf-8-sig')
assert original['retained_non_shadow_count'] == 8 and original['included_hp_sprites']
for fid,value in original['before'].items():
    block = re.search(r'^--- !u!212 &'+fid+r'\s*\n(.*?)(?=^--- !u!|\Z)', prefab, re.M|re.S)
    if value['name'] == 'Shadow':
        assert not block
    else:
        assert block and re.search(r'^  m_Sprite: (.+)$', block[1], re.M)[1] == value['sprite'], fid

offline = read(D/'offline_review_20261028.json')
staging_changes = [p for p,s in offline['staging_sha256'].items() if sha(D/'staged_art'/p) != s]
assert set(staging_changes) == {'Up_LegFront.png','Swine_Directions.png'}
assert {p.name for p in (D/'staged_art').iterdir() if p.is_file()
        and sha(p) != sha(D/'local_raster_revision_03/before_staged_art'/p.name)} == set(staging_changes)
for suffix in ['.png','.sprites.json','.layout.json']:
    assert sha(D/'staged_art'/('Swine_Directions'+suffix)) == sha(R/art/('Swine_Directions'+suffix))
selection = read(D/'art_selection.json')
assert selection['Up'] == 'local_raster_revision_03/Up_sheet.png'
assert selection['Down'] == 'local_raster_revision_02/Down_sheet.png'
assert selection == preplay['selection']
for direction,expected_bytes in [('Up',1360116),('Down',1465033)]:
    result = read(D/'generation'/direction/'result.json')
    raw = D/'generation'/direction/'raw.png'
    assert result['status'] == 200 and result['bytes'] == raw.stat().st_size == expected_bytes
for file in ['local_raster_revision_01/processing.json',
             'local_raster_revision_02/Up_processing.json',
             'local_raster_revision_02/Down_processing.json',
             'local_raster_revision_03/processing.json']:
    processing = read(D/file)
    assert sha(D/processing['parent']) == processing['parent_sha256']
    assert sha((D/file).parent/processing['output']) == processing['output_sha256']
repair = read(D/'side_reuse_repair_r01/repair.json')
preserve = repair['preservation_checks']
assert preserve['originalCurvesEventsTimingPreserved']
assert preserve['originalFloatBindings'] == 136 and preserve['afterFloatBindings'] == 139
assert sha(R/repair['path']) == repair['after'] == '3507551C0A1814E4BD53E7443632113982D59929D2A3CBAC4F13289E86DA096F'
heel = read(D/'local_raster_revision_03/installation.json')
assert heel['atlas_only'] and heel['walk_before'] == heel['walk_after'] == repair['after']

alpha = {}
for path in (D/'staged_art').glob('*.png'):
    im = Image.open(path)
    assert im.mode == 'RGBA'
    a = np.asarray(im)
    opaque = a[:,:,3] > 0
    magenta = opaque & (a[:,:,0] > 150) & (a[:,:,2] > 150) & (a[:,:,1] < 100)
    assert not magenta.any(), path
    alpha[path.name] = dict(size=list(im.size),transparent=int((a[:,:,3] == 0).sum()),
                            opaque=int((a[:,:,3] == 255).sum()),magenta_foreground=int(magenta.sum()))
write(D/'scope_incremental_final_20261028.json',dict(
    observed_at=now(),baseline='incremental_before_20261028.json',
    baseline_sha256=sha(D/'incremental_before_20261028.json'),baseline_files=len(before),current_files=len(current),
    comparison='Union of before/current paths including additions and deletions',changes=changes,
    unexpected_incremental=unexpected,automatic_editor_side_effects=side_effects,
    protected_six=baseline['protected_six'],protected_drift=protected_drift,
    original_sprite_contracts='original_sprite_contracts_20261028.json',retained_non_shadow_sprite_count=8,
    prefab_semantics=legacy_after['semantics'][NAME],installed_asset_drift=[],staged_production_drift=[],
    staged_changes_since_initial_offline_review=staging_changes,final_staging_alpha=alpha,
    legacy_before='scope_Swine_before_20261028.json',legacy_after='scope_Swine_r02_final_20261028.json',
    legacy_pass=legacy_after['pass'],legacy_unexpected_count=len(old_unexpected),
    legacy_semantic_failures=list(new_failures),new_unexpected_vs_preexisting_legacy=[],new_semantic_failures={},
    note='Historical global differences remain; no global PASS claim. Only expected heel/atlas staging changes since initial offline review.'))

runtime = read(D/'runtime_summary.json')
assert runtime['passes'] == 168 and runtime['failures'] == 0 and runtime['actual_frames'] == 677
assert [x['revision'] for x in runtime['runtime']] == ['runtime_r02','runtime_updeath_r02']
frames = {}
for item_runtime in runtime['runtime']:
    folder = D/item_runtime['revision']
    assert sha(folder/'actual_frames.jsonl') == item_runtime['records_sha256']
    rows = [json.loads(line) for line in (folder/'actual_frames.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    checks = (folder/'actual_runtime_checks.txt').read_text(encoding='utf-8').splitlines()
    assert sum(x.startswith('PASS ') for x in checks) == 84 and not any(x.startswith('FAIL ') for x in checks)
    assert len(rows) == item_runtime['frames'] and all(a['frame'] < b['frame'] for a,b in zip(rows,rows[1:]))
    frames[item_runtime['revision']] = {x['file']:sha(folder/x['file']) for x in rows}
    assert len(frames[item_runtime['revision']]) == len(rows) and all(frames[item_runtime['revision']].values())
assert sum(map(len,frames.values())) == 677
visual = D/'visual_review_final_r02_20261028'
sources = read(visual/'sources.json')
sheets = sorted({x['sheet'] for x in sources['sources']})
unique = len({(x['revision'],x['source']) for x in sources['sources']})
assert len(sheets) == 10 and len(sources['sources']) == 256 and unique == 238
for sample in sources['sources']:
    assert sample['source'] in frames[sample['revision']]
additional = ['runtime_r02/four_directions.png','runtime_visual_strip.png',
              'runtime_r02/frames/DeathAutoRecycle_00162.png',
              'runtime_r02/frames/ContinuousTurns_00323.png',
              'runtime_updeath_r02/frames/DeathAutoRecycle_00162.png',
              'staged_art/Up_LegFront.png']
note = ('Up/Down正式生成各一次HTTP200，未付费重试。Up最终选local_raster_revision_03/Up_sheet.png，Down选local_raster_revision_02/Down_sheet.png；原raw保留。本地r01去除Up头部重复耳，r02仅压扁生成躯干恢复圆胖比例；两版被否决布局保留，最终后脑盖住颈帽、四短足根嵌入身体、尾巴细小。旧两轮673帧因后脚残留淡三角痕降为历史，r03完整同行插值清除后跟内痕、保持外轮廓，仅替换当前角色图集后重跑。保留原tan/ochre斑点野猪、象牙色獠牙、躯干上唯一一对耳、四短足和细尖尾；Up后脑无脸无獠牙，Down正常圆眼、攻击斜眉、死亡空白圆眼及短吐舌可辨。原含HP的8个非Shadow Sprite PPtr及非美术语义保持，只移除授权战斗Shadow。源Boar Death旋转Body而Walk无复位，只在Swine自有Walk补Body Euler三轴常量0，136原float绑定/PPtr/事件/时长/loop保持，改后139；图集返修后动画SHA不变，不改共享资源或C#。现场反射采样多数错过复用阶段，仅有旧轮行走Body0观察，不能声称量测复用前后Euler0；复用恢复由实际断言及PNG证明。最终runtime_r02为84/0、338帧，runtime_updeath_r02为84/0、339帧，共677真实PNG。实际看最终四方向与strip、全部10张时序/步态/愤怒板(256采样位/238张不同实际帧)、双向死亡和复用后Left三张原尺寸PNG及后脚原尺寸切片。抽样可见短足小幅对角摆动、头身轻摇、连续四向转向；攻击表情切换、受击/致死白闪结束、双向倾斜淡出/回收、复用正常朝向、暂停静止及1x/2x/3x推进。未见断开的根部、重复耳、紫底残留或地面阴影。淡出半透明阶段可透见头身重叠轮廓；正背相对原侧图更窄、材质更平滑，最终美术判断交用户。方法为真实PNG时序抽样，未实时播放GIF全片、未逐张审完677帧。实现与内部审阅完成，user_approved=false。')
(D/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
write(visual/'review.json',dict(observed_at=now(),status='completed_pending_user_art_review',user_approved=False,
    note=note,viewed_sheets=sheets,sample_slots=256,distinct_actual_frame_samples=unique,
    source_manifest='sources.json',sources_sha256=sha(visual/'sources.json'),
    viewed_sheet_sha256={p:sha(visual/p) for p in sheets},additional_viewed=additional,
    additional_viewed_sha256={p:sha(D/p) for p in additional},
    method='Chronological actual PNG samples, gait-cycle and angry sheets, three full runtime PNGs and native heel; no live GIF playback or exhaustive all-frame review',
    rejected_previous='local_raster_revision_03/rejected_previous.json',
    live_euler_limitation='Live reflection mostly missed reuse stage; no measured pre/post-reuse Euler-zero claim',
    final_version_binding='version_binding_final_20261028.json'))
runtime.update(status='runtime_and_internal_visual_review_complete_pending_user_art_review',
               visual_review_file='visual_review_final_r02_20261028/review.json')
write(D/'runtime_summary.json',runtime)

files = [D/p for p in ['installed_manifest.json','installed_verify.txt','art_selection.json','anatomy_plan.json',
    'layout_adjustments.json','processing.json','offline_review_20261028.json','reference_review_20261028.json',
    'original_sprite_contracts_20261028.json','preplay_version_binding_20261028.json',
    'preplay_version_binding_r02_20261028.json','source_animation_contracts_20261028.json',
    'source_death_reuse_contract_20261028.json','source_death_reuse_probe_20261028.json',
    'reuse_live_inspection_20261028.json','reuse_live_inspection_r02_20261028.json',
    'runtime_summary.json','runtime_visual_strip.png','record_note_utf8.txt',
    'visual_review_final_r02_20261028/sources.json','visual_review_final_r02_20261028/review.json',
    'scope_incremental_final_20261028.json']]
for folder in ['local_raster_revision_01','local_raster_revision_02','local_raster_revision_03','side_reuse_repair_r01']:
    files += [p for p in (D/folder).rglob('*') if p.is_file()]
for direction in ['Up','Down']:
    files += [D/'generation'/direction/p for p in ['raw.png','result.json','generation_intent.json','request.json','prompt.txt','review_20261028.json']]
for item_runtime in runtime['runtime']:
    revision = item_runtime['revision'];folder = D/revision
    files += [folder/p for p in ['actual_frames.jsonl','actual_runtime_checks.txt','media_manifest.json','four_directions.png']]
    files += list(folder.glob('*.gif')) + [D/(revision+p) for p in ['_start.json','_returned.json']]
files += [p for p in (D/'staged_art').iterdir() if p.is_file()] + list(visual.glob('*.png'))
assert all(p.is_file() for p in files), [str(p) for p in files if not p.is_file()]
write(D/'version_binding_final_20261028.json',dict(observed_at=now(),final_install_manifest='installed_manifest.json',
    files={p.relative_to(D).as_posix():sha(p) for p in sorted(set(files))},
    installed_files={x['path']:x['after'].upper() for x in manifest['changes']},
    production_scope_files={x['path']:x['after'] for x in changes if x['path'] not in {s['path'] for s in side_effects}},
    actual_png_frames=frames,frame_total=677,
    note='Original requests and raw, local derivations, selected images, staging, final installation, own Walk reset, final Play rounds, actually viewed sheets and all 677 final actual PNG SHA256. Initial r01 rounds remain historical.'))

client = Client();project = client.identity();cache_refresh = None
errors = unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
assert errors['data'] == []
for attempt in range(4):
    state = client.resource('mcpforunity://editor/state');s = state['data']
    if (not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending']
            and not s['assets']['is_updating'] and s['advice']['ready_for_tools']):
        break
    if attempt == 0 and s['advice'].get('blocking_reasons') == ['stale_status']:
        cache_refresh = unwrap(client.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"Swine_final_live_state_read"});return true;')))
    time.sleep(1)
else:
    raise RuntimeError('Unity not ready; do not record')
live = probe(client)
assert live['scene'] == 'Assets/Scenes/Boot.unity' and not any(v for k,v in live.items() if k != 'scene'), live
assert all(sha(R/x['path']) == x['after'].upper() for x in manifest['changes'])
write(D/'final_validation_20261028.json',dict(observed_at=now(),transport=URL,project=project,state=state,
    cache_refresh=cache_refresh,errors=errors,live=live,installed_asset_drift=[],
    final_install_manifest='installed_manifest.json',runtime_summary_sha256=sha(D/'runtime_summary.json'),
    version_binding_sha256=sha(D/'version_binding_final_20261028.json'),
    scope_sha256=sha(D/'scope_incremental_final_20261028.json'),protocol_history=client.history))

owner()
run('character_step.py','record',NAME,note)
progress = read(H/'progress.json');item = next(x for x in progress['items'] if x['name'] == NAME)
assert progress['completed_count'] == 86 and item['status'] == 'completed_pending_user_art_review' and item['user_approved'] is False
item.update(current_stage='recorded_pending_user_art_review',
    final_install_manifest='Swine/installed_manifest.json',final_animation_repair='Swine/side_reuse_repair_r01/repair.json',
    final_visual_review='Swine/visual_review_final_r02_20261028/review.json',
    final_validation='Swine/final_validation_20261028.json',final_scope='Swine/scope_incremental_final_20261028.json',
    final_version_binding='Swine/version_binding_final_20261028.json')
write(H/'progress.json',progress)
gifs = read(H.parent/'AllGIF/manifest.json')
own = [x for x in gifs['files'] if x['source'].startswith('Remaining_20261024/Swine/')]
active = [x for x in own if x['status'] == '当前审核版本']
assert {x['source'] for x in own} == {p.relative_to(H.parent).as_posix() for p in D.rglob('*.gif')}
assert len(active) == 12 and {x['source'].split('/')[2] for x in active} == {'runtime_r02','runtime_updeath_r02'}
assert all(sha(H.parent/x['source']) == x['sha256'] and sha(H.parent/'AllGIF'/x['file']) == x['sha256'] for x in own)
write(D/'gif_archive_verification_20261028.json',dict(observed_at=now(),total=gifs['count'],character_count=len(own),
    current_count=len(active),files=own,sha256_match=True,all_available_character_gifs_archived=True))
chain = owner()
chain.update(character_status_at_handoff=item['status'],completed_count_snapshot=86,
    current_stage='recorded_pending_user_art_review',
    last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Swine/final_validation_20261028.json',updated_at=now())
write(H/'conversation_chain.json',chain)
print(json.dumps(dict(completed=86,production_changes=len(changes),production_additions=sum(x['before'] is None for x in changes),
    unexpected_incremental=len(unexpected),legacy_unexpected=len(old_unexpected),legacy_semantic_failures=list(new_failures),
    sample_slots=256,distinct_actual_samples=unique,frames=677,live=live,gifs_total=gifs['count'],swine_gifs=len(own),current_gifs=len(active)),ensure_ascii=False))
