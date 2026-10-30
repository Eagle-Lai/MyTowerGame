"""Seal Watchdog art_r04 evidence. Only Docs are written; production is read-only."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw
import ast, hashlib, json, os, re, subprocess, sys
import numpy as np

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
NAME = 'Watchdog'
OWNER = '01a18379-8413-7bb3-bbc3-e0e5b2544d59'
TOKEN = 'wasp-to-watchdog-20261029_010456-a6f96d67-324e-4b30-9ff0-555b83354188'
REVISION = 'art_r04'
RUNS = ['runtime_r01', 'runtime_updeath_r01']
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
now = lambda: datetime.now(timezone(timedelta(hours=8))).isoformat()

def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def data(value):
    return value.get('structuredContent') or json.loads(value['content'][0]['text'])

def result(value):
    value = data(value)['data']['result']
    return json.loads(value) if isinstance(value, str) else value

def ownership():
    chain = read(H / 'conversation_chain.json')
    assert chain['state'] == 'active' and chain['owner_thread_id'] == OWNER
    assert chain['dispatch_token'] == TOKEN and chain['current_character'] == NAME
    assert os.environ.get('CODEX_THREAD_ID') == OWNER
    return chain

ownership()
phase = sys.argv[1]
assert phase in ['audit', 'seal']
progress = read(H / 'progress.json')
item = next(r for r in progress['items'] if r['name'] == NAME)
assert item['status'] == 'staged_pending_visual_check' and not item.get('user_approved', False)
assert progress['completed_count'] == 93 and not (D / 'final_validation_20261029.json').exists()
baseline = read(D / 'incremental_before_20261029.json')
before = {p: v.upper() for p, v in baseline['files'].items()}
assert len(before) == 5425
current = {p.relative_to(ROOT).as_posix(): sha(p)
           for folder in ['Assets', 'Packages', 'ProjectSettings', 'Luban']
           for p in (ROOT / folder).rglob('*') if p.is_file()}
t = baseline['target']
battle, art = t['battle'], t['art_dir']
manifest_path = D / 'production_before_play_20261029.json'
manifest = read(manifest_path)
installed = manifest['final_files']
assert manifest['revision'] == REVISION and manifest['verify_pass'] and len(installed) == 22
assert manifest['manifest_sha256'] == sha(D / 'installed_manifest.json')
assert all(current.get(p) == digest for p, digest in installed.items()), 'Production drift since prePlay snapshot'
installation = read(D / 'installed_manifest.json')
verified = installation['verification']['data']['result']
assert verified['pass'] is True and len(installation['changes']) == 20
verify = (D / 'installed_verify.txt').read_text(encoding='utf-8-sig')
assert verify.strip() == verified['report'].strip()
assert all(s.startswith('PASS ') for s in verify.splitlines())
assert 'PASS YooAsset prefab and artwork collectors present' in verify
assert all(p in [battle, battle + '.meta', art + '.meta'] or p.startswith(art + '/') for p in installed)
changes = [{'path': p, 'before': before.get(p), 'after': current.get(p)}
           for p in sorted(set(before) | set(current)) if before.get(p) != current.get(p)]
side_effects = []
for row in changes:
    if row['path'] == 'Assets/StreamingAssets/build_info':
        assert current['Assets/Reporter/Editor/ReporterEditor.cs'] == before['Assets/Reporter/Editor/ReporterEditor.cs']
        assert re.fullmatch(r'Build from .+ at .+', (ROOT / row['path']).read_text(encoding='utf-8'))
        side_effects.append(dict(row, origin='Unmodified ReporterEditor automatic Play timestamp'))
allowed = set(installed) | {row['path'] for row in side_effects}
unexpected = [row for row in changes if row['path'] not in allowed]
assert not unexpected, unexpected
protected = {p: v.upper() for p, v in baseline['protected_six'].items()}
protected_drift = [p for p, v in protected.items() if p != battle and current.get(p) != v]
assert not protected_drift
assert all(sha(D / 'reference' / Path(p).name) == v for p, v in protected.items())
cs_drift = [p for p in set(before) | set(current) if p.endswith('.cs') and before.get(p) != current.get(p)]
assert not cs_drift
audit_source = H.parent / 'Batch01_10/audit_scope.py'
tree = ast.parse(audit_source.read_text(encoding='utf-8-sig'))
definitions = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)], type_ignores=[])
ns = {'re': re, 'hashlib': hashlib, 'HERE': H, 'ROOT': ROOT, 'targets': {NAME: t}}
exec(compile(definitions, str(audit_source), 'exec'), ns)
semantic = ns['semantic'](NAME)
assert semantic['pass'], semantic
r04 = read(D / 'staged_art_r04/manifest.json')
assert r04['revision'] == REVISION and r04['raw_unchanged']
assert all(sha(D / 'staged_art' / p) == v for p, v in r04['final_art'].items())
staged = {f: sha(D / 'staged_art' / f)
          for f in [NAME + '_Directions.png', NAME + '_Directions.sprites.json', NAME + '_Directions.layout.json']}
assert all(current[art + '/' + f] == v for f, v in staged.items())
sprite_spec = read(D / 'staged_art/Watchdog_Directions.sprites.json')
atlas = Image.open(D / 'staged_art/Watchdog_Directions.png').convert('RGBA')
assert atlas.size == (2048, 2048) == (sprite_spec['width'], sprite_spec['height'])
assert sprite_spec['ppu'] == 100
parts = {}
for sprite in sprite_spec['sprites']:
    path = D / 'staged_art' / (sprite['name'] + '.png')
    im = Image.open(path).convert('RGBA')
    a = np.asarray(im)
    opaque = a[:, :, 3] > 0
    pad = Image.new('L', (im.width + 2, im.height + 2), 255)
    pad.paste(Image.fromarray(np.where(opaque, 0, 255).astype('uint8')), (1, 1))
    ImageDraw.floodfill(pad, (0, 0), 127)
    holes = int((np.asarray(pad)[1:-1, 1:-1] == 255).sum())
    rgb = a[:, :, :3].astype(np.int16)
    spill = int((opaque & (rgb[:, :, 2] > rgb[:, :, 1] + 6)
                 & (rgb[:, :, 0] > rgb[:, :, 1] + 10)).sum())
    assert holes == 0 and spill == 0 and opaque.any(), sprite['name']
    assert im.size == (sprite['w'], sprite['h'])
    crop = atlas.crop((sprite['x'], atlas.height - sprite['y'] - sprite['h'],
                       sprite['x'] + sprite['w'], atlas.height - sprite['y']))
    assert np.array_equal(np.asarray(crop), a), sprite['name']
    parts[sprite['name']] = {'sha256': sha(path), 'size': list(im.size), 'enclosed_alpha_holes': holes,
                             'spill_pixels': spill, 'pivot': [sprite['pivotX'], sprite['pivotY']]}
assert len(parts) == 14
assert len({parts['Up_Head' + pose]['sha256'] for pose in ['Normal', 'Angry', 'Dead']}) == 1
for direction in ['Up', 'Down']:
    assert all(parts[direction + '_' + p]['pivot'] == [.5, .94] for p in ['LegFront', 'LegBack'])
    assert parts[direction + '_Tail']['pivot'] == [.5, .97]
layout = read(D / 'staged_art/Watchdog_Directions.layout.json')
assert layout['motionKind'] == 'quadruped' and layout['anatomy']['legs'] == 4 and layout['anatomy']['tails'] == 1
runtime = read(D / 'runtime_summary.json')
assert (runtime['passes'], runtime['failures'], runtime['actual_frames']) == (168, 0, 597)
assert [r['revision'] for r in runtime['runtime']] == RUNS
frames = {}
for run in runtime['runtime']:
    revision, folder = run['revision'], D / run['revision']
    checks = (folder / 'actual_runtime_checks.txt').read_text(encoding='utf-8-sig').splitlines()
    records = [json.loads(line) for line in (folder / 'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if line]
    assert (run['pass'], run['fail']) == (84, 0) and len(records) == run['frames']
    assert sum(s.startswith('PASS ') for s in checks) == 84 and not any(s.startswith('FAIL ') for s in checks)
    assert all(b['frame'] > a['frame'] and b['realtime'] > a['realtime'] for a, b in zip(records, records[1:]))
    assert all(not r['shadow'] for r in records)
    assert sha(folder / 'actual_frames.jsonl') == run['records_sha256']
    frames[revision] = {r['file']: sha(folder / r['file']) for r in records}
    assert all(frames[revision].values())
    assert len(frames[revision]) == len(list((folder / 'frames').glob('*.png'))) == run['frames']
    start = read(D / (revision + '_start.json'))
    assert start['project']['projectRoot'].lower() == 'e:/mytowergame' and start['revision'] == revision
    assert result(start['response']) is True
    assert read(D / (revision + '_returned.json'))['state'] == {
        'playing': False, 'review': False, 'scene': 'Assets/Scenes/Boot.unity', 'dirty': False}
    assert datetime.fromisoformat(start.get('observed_at', installation['installed_at'])) >= datetime.fromisoformat(installation['installed_at'])
assert read(D / 'runtime_updeath_r01_start.json')['death_up'] is True
samples_path = 'gif_samples_20261029_r02/samples.json'
samples = read(D / samples_path)
assert len(samples['samples']) == 60
assert len({(r['revision'], r['file']) for r in samples['samples']}) == 12
for row in samples['samples']:
    gif_path = D / row['revision'] / row['file']
    assert sha(gif_path) == row['gif_sha256']
    with Image.open(gif_path) as gif:
        assert gif.n_frames == row['frame_count']
        gif.seek(row['frame_index_zero_based'])
        image = gif.convert('RGB').crop(row['stable_crop'])
        image.thumbnail((300, 215), Image.Resampling.LANCZOS)
        assert hashlib.sha256(image.tobytes()).hexdigest().upper() == row['sample_sha256']
full_sources = read(D / 'gif_samples_20261029_full/sources.json')
assert len(full_sources) == 4
for row in full_sources:
    assert sha(D / row['source']) == row['source_sha256']
    with Image.open(D / row['source']) as gif:
        gif.seek(row['frame'])
        assert np.array_equal(np.asarray(gif.convert('RGB')), np.asarray(Image.open(D / row['output']).convert('RGB')))
board = read(D / 'visual_review_final_20261029/sources.json')
sample_positions = len(board['sources'])
unique_pngs = len({(r['revision'], r['source']) for r in board['sources']})
assert (sample_positions, unique_pngs) == (256, 229)
assert all(r['source'] in frames[r['revision']] for r in board['sources'])
reviewed = ['offline_rig_proof.png', 'parts_clean_final.png', 'runtime_visual_strip.png']
reviewed += [r + '/four_directions.png' for r in RUNS]
reviewed += ['visual_review_final_20261029/' + r + '_' + suffix + '.png'
             for r in RUNS for suffix in ['sequence_0', 'sequence_1', 'sequence_2', 'walk_cycle', 'angry_detail']]
reviewed += [directory + '/' + r + '_samples.png'
             for directory in ['gif_samples_20261029', 'gif_samples_20261029_r02'] for r in RUNS]
originals = ['runtime_r01/frames/' + p for p in ['UpWalk_00009.png', 'DownWalk_00028.png',
             'Attack_00123.png', 'Hurt_00137.png', 'DeathAutoRecycle_00146.png', 'Reuse_00156.png',
             'LeftWalk_00047.png', 'RightWalk_00066.png']]
originals += ['runtime_updeath_r01/frames/DeathAutoRecycle_00146.png']
note = ('最终art_r04实际查看离线rig/透明分件、两轮四方向图、runtime strip、10张时序/步态/愤怒细节板'
        '（256采样位、229张不同真实PNG）、9张原尺寸PNG；12个最终GIF各5个编码帧共60帧，'
        '并补看两轮Up/Down各1张未裁切GIF编码整帧。保留矮壮深橄榄棕犬、赭色圆斑、折三角耳、'
        '短宽吻、象牙色牙及单一金色尖钉项圈，四足与短楔尾相连。Up为无眼无口的纯后脑，'
        '可见后跟垫、两侧远足；Down正常/张口愤怒/闭眼死亡切换正确。原左右侧图及镜像保留。'
        '轴向体形较侧面窄；行走足部错相、尾根藏入躯干，未见断颈、悬足、重复项圈或地面阴影。'
        '攻击有前压回收，受击全身白闪后恢复，Down/Up死亡侧倾缩小淡出、自动回收及同实例复用返回正常Down。'
        '暂停冻结、恢复及1x/2x/3x有相位推进证据。原整帧及未裁切GIF帧确认耳尖完整、血条有间距；'
        '初版GIF抽样裁切顶部40%造成耳尖假性截断，修订r02降至30%后消失，原媒体未改写。'
        'GIF为编码帧抽样，非实时播放或逐GIF全帧审核；597张实际PNG均保留。用户美术验收待进行。')
visual = {'reviewed_at': now(), 'character': NAME, 'owner_thread_id': OWNER, 'dispatch_token': TOKEN,
          'final_revision': REVISION, 'runs': RUNS,
          'reviewed_images': {p: sha(D / p) for p in reviewed},
          'selected_original_pngs': {p: sha(D / p) for p in originals},
          'uncropped_encoded_gif_frames': {r['output']: sha(D / r['output']) for r in full_sources},
          'sample_positions': sample_positions, 'unique_board_source_pngs': unique_pngs,
          'gif_count': 12, 'encoded_gif_samples': 60, 'additional_uncropped_encoded_frames': 4,
          'gif_sample_manifest': samples_path, 'gif_sample_manifest_sha256': sha(D / samples_path),
          'uncropped_gif_manifest': 'gif_samples_20261029_full/sources.json',
          'observations': note, 'technical_visual_pass': True, 'user_approved': False,
          'limitations': ['Encoded-frame sampling, not real-time playback or exhaustive GIF review.',
                          'All 597 actual PNGs retained and hashed; 229 distinct board sources and 9 full originals reviewed.',
                          'Initial GIF preview crop clipped ear tips; corrected r02 crop and uncropped encoded frames confirm intact source ears. Old preview evidence is preserved.'],
          'local_revisions': {'r02': 'Exposed far paws and hid Up tail root.',
                              'r03': 'Buried Down hip caps and placed front head toward chest.',
                              'art_r04': 'Removed eight spill pixels; zero enclosed alpha holes in all 14 slices.'}}
assert all(visual['reviewed_images'].values()) and all(visual['selected_original_pngs'].values())
scope = {'observed_at': now(), 'baseline': 'incremental_before_20261029.json',
         'baseline_sha256': sha(D / 'incremental_before_20261029.json'), 'baseline_files': len(before),
         'current_files': len(current), 'comparison': 'Full path union across Assets/Packages/ProjectSettings/Luban; current disk baseline, never Git HEAD.',
         'changes': changes, 'added_count': sum(r['before'] is None for r in changes),
         'deleted_count': sum(r['after'] is None for r in changes), 'unexpected_incremental': unexpected,
         'automatic_editor_side_effects': side_effects, 'protected_six': protected,
         'protected_drift': protected_drift, 'shared_CSharp_drift': cs_drift,
         'installed_manifest_paths': installed, 'installed_manifest_drift': [],
         'staged_to_installed_hashes': staged, 'prefab_semantics': semantic, 'stage_parts': parts,
         'legacy_global_note': 'Historical global audit had 291 unexpected paths and six other-character semantic failures. This is Watchdog-only incremental audit, not global PASS or a new full historical re-audit.'}

if phase == 'audit':
    for path in ['scope_incremental_final_20261029.json', 'visual_review_final_20261029/review.json', 'record_note_utf8.txt']:
        assert not (D / path).exists(), path
    write(D / 'scope_incremental_final_20261029.json', scope)
    write(D / 'visual_review_final_20261029/review.json', visual)
    (D / 'record_note_utf8.txt').write_text(note + '\n', encoding='utf-8')
    print(json.dumps({'character': NAME, 'phase': 'audit_and_visual_sealed', 'baseline_files': len(before),
                      'current_files': len(current), 'changes': len(changes), 'added': scope['added_count'],
                      'unexpected': 0, 'semantic_pass': True, 'parts': len(parts), 'sample_positions': sample_positions,
                      'unique_board_pngs': unique_pngs, 'original_pngs': len(originals)}, ensure_ascii=False))
    raise SystemExit(0)

saved_scope = read(D / 'scope_incremental_final_20261029.json')
assert saved_scope['changes'] == changes and saved_scope['stage_parts'] == parts
saved_visual = read(D / 'visual_review_final_20261029/review.json')
for key in ['reviewed_images', 'selected_original_pngs', 'uncropped_encoded_gif_frames']:
    assert saved_visual[key] == visual[key]
probe_path = D / 'unity_release_probe_20261029_response.json'
probe = read(probe_path)
assert probe['success'] and probe['transport'] == 'http://127.0.0.1:8088/mcp'
assert probe['project']['projectRoot'].lower() == 'e:/mytowergame' and probe['project']['unityVersion'] == '2022.3.62f3c1'
state = probe['results'][1]['data']
errors = data(probe['results'][2])
live = result(probe['results'][3])
assert state['advice']['ready_for_tools'] and state['activity']['phase'] == 'idle' and not state['staleness']['is_stale']
assert not state['tests']['is_running'] and not state['compilation']['is_compiling']
assert not state['compilation']['is_domain_reload_pending'] and not state['assets']['is_updating']
assert not state['assets']['external_changes_dirty']
assert errors['data'] == [] and live['scene'] == 'Assets/Scenes/Boot.unity' and live['sceneCount'] == 1
assert all(live[k] is False for k in ['playing', 'compiling', 'failed', 'updating', 'sceneDirty', 'balance', 'recording', 'review', 'manual'])
imports = result(probe['results'][4])
assert imports['spriteMode'] == 'Multiple' and imports['ppu'] == 100
assert imports['alphaIsTransparency'] and not imports['mipmaps'] and imports['spriteCount'] == 14
for sprite in sprite_spec['sprites']:
    actual = next(s for s in imports['sprites'] if s['name'] == sprite['name'])
    assert actual['ppu'] == 100
    assert all(abs(actual[k] - sprite[k]) < 1e-4 for k in ['x', 'y', 'w', 'h'])
    assert abs(actual['pivotX'] - sprite['pivotX'] * sprite['w']) < 1e-3
    assert abs(actual['pivotY'] - sprite['pivotY'] * sprite['h']) < 1e-3
archive_path = H.parent / 'AllGIF/manifest.json'
archive_before = read(archive_path)
assert not any(r['source'].startswith('Remaining_20261024/Watchdog/') for r in archive_before['files'])
runtime.update(final_revision=REVISION, visual_reviewed=True,
               visual_review_file='visual_review_final_20261029/review.json', visual_note=note,
               user_approved=False, status='completed_pending_user_art_review')
write(D / 'runtime_summary.json', runtime)
record = subprocess.run([sys.executable, str(H / 'record_review.py'), NAME, note],
                        capture_output=True, text=True, encoding='utf-8', check=True)
progress = read(H / 'progress.json')
item = next(r for r in progress['items'] if r['name'] == NAME)
assert progress['completed_count'] == 94 and item['status'] == 'completed_pending_user_art_review'
assert not item['user_approved'] and item['actual_frames'] == 597
archive = read(archive_path)
by_source = {r['source']: r for r in archive['files']}
pairs = []
for run in RUNS:
    gifs = sorted((D / run).glob('*.gif'))
    assert len(gifs) == 6
    for path in gifs:
        source = 'Remaining_20261024/Watchdog/' + run + '/' + path.name
        row = by_source[source]
        digest = sha(path)
        assert row['sha256'] == digest == sha(H.parent / 'AllGIF' / row['file'])
        assert row['status'] == '当前审核版本'
        pairs.append({'source': source, 'archive': row['file'], 'sha256': digest, 'status': row['status']})
new_sources = set(by_source) - {r['source'] for r in archive_before['files']}
assert new_sources == {r['source'] for r in pairs}
assert archive['count'] == archive_before['count'] + len(new_sources)
archive_report = {'verified_at': now(), 'source_gif_count': len(pairs), 'matching_archive_count': len(pairs),
                  'final_review_gifs': 12, 'historical_gifs': 0, 'global_archive_count_before': archive_before['count'],
                  'global_archive_count': archive['count'], 'all_source_and_archive_sha256_match': True,
                  'files': pairs, 'manifest_sha256': sha(archive_path)}
write(D / 'gif_archive_verification_20261029.json', archive_report)
remaining = [r for r in progress['items'] if r['status'] not in ['completed_pending_user_art_review', 'user_approved']]
recoverable = [r for r in remaining if r['status'] not in ['not_started', 'blocked']]
selected = min(recoverable or [r for r in remaining if r['status'] != 'blocked'], key=lambda r: r['index'])
assert selected['name'] == 'WhiteWolf' and selected['index'] == 106
item.update(stage='recorded_pending_user_art_review', final_revision=REVISION,
            final_validation_file='Watchdog/final_validation_20261029.json',
            version_binding_file='Watchdog/version_binding_final_20261029.json',
            scope_file='Watchdog/scope_incremental_final_20261029.json',
            visual_review_file='Watchdog/visual_review_final_20261029/review.json',
            gif_archive_file='Watchdog/gif_archive_verification_20261029.json')
progress.update(current=selected['name'], updated_at=now())
write(H / 'progress.json', progress)
evidence = {p.relative_to(D).as_posix(): sha(p) for p in sorted(D.rglob('*')) if p.is_file()
            and 'frames' not in p.relative_to(D).parts
            and p.name not in ['version_binding_final_20261029.json', 'final_validation_20261029.json']}
binding = {'observed_at': now(), 'final_revision': REVISION, 'manifest': manifest_path.name,
           'manifest_sha256': sha(manifest_path), 'installed_files': installed,
           'production_scope_files': {r['path']: r['after'] for r in changes}, 'files': evidence,
           'actual_png_frames': frames, 'frame_total': 597,
           'note': 'Full 22-path prePlay snapshot unchanged; 597 actual PNGs, 12 final GIFs, logs, reviewed boards/9 originals/encoded samples are bound to art_r04 installed before both Play runs.'}
write(D / 'version_binding_final_20261029.json', binding)
final = {'observed_at': now(), 'character': NAME, 'owner_thread_id': OWNER, 'dispatch_token': TOKEN,
         'status': 'completed_pending_user_art_review', 'user_approved': False, 'final_revision': REVISION,
         'passes': 168, 'failures': 0, 'actual_png_frames': 597, 'runtime': runtime['runtime'],
         'installer_verify_pass': True, 'manifest': manifest_path.name,
         'manifest_sha256': sha(manifest_path), 'incremental_scope_file': 'scope_incremental_final_20261029.json',
         'incremental_scope_sha256': sha(D / 'scope_incremental_final_20261029.json'),
         'incremental_changes': len(changes), 'incremental_unexpected': 0, 'prefab_semantic_pass': True,
         'version_binding_file': 'version_binding_final_20261029.json',
         'version_binding_sha256': sha(D / 'version_binding_final_20261029.json'),
         'visual_review_file': 'visual_review_final_20261029/review.json',
         'visual_review_sha256': sha(D / 'visual_review_final_20261029/review.json'),
         'gif_archive_file': 'gif_archive_verification_20261029.json',
         'gif_archive_sha256': sha(D / 'gif_archive_verification_20261029.json'),
         'archived_character_gifs': 12, 'final_review_gifs': 12, 'global_archive_count': archive['count'],
         'unity': {'transport': probe['transport'], 'project': probe['project'],
                   'instance_id': state['unity']['instance_id'], 'live_probe': live,
                   'sprite_imports': imports, 'ready_for_tools': True, 'console_errors': 0,
                   'external_changes_dirty': state['assets']['external_changes_dirty'], 'evidence': probe_path.name,
                   'cache_note': 'Existing ForceUpdate refreshed factual idle snapshot; no plugin source edited.'},
         'progress': {'completed_count': 94, 'authorized_count': 108, 'next_candidate': selected['name']},
         'record_review_output': record.stdout.strip(), 'legacy_global_scope_warning': scope['legacy_global_note']}
write(D / 'final_validation_20261029.json', final)
chain = ownership()
chain.update(current_stage='recorded_pending_user_art_review',
             last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Watchdog/final_validation_20261029.json',
             updated_at=now())
write(H / 'conversation_chain.json', chain)
print(json.dumps({'character': NAME, 'status': final['status'], 'completed_count': 94,
                  'baseline_files': len(before), 'current_files': len(current), 'scope_changes': len(changes),
                  'incremental_unexpected': 0, 'semantic_pass': True, 'passes': 168, 'failures': 0,
                  'frames': 597, 'character_gifs': 12, 'archive_count': archive['count'], 'next': selected['name']}, ensure_ascii=False))
