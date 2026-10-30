"""Audit and seal only WinterBoar's current evidence; production is read-only."""
from pathlib import Path
from PIL import Image
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import numpy as np

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
sys.path.insert(0, str(D))
from checkpoint_20261029 import owner, read, sha, now, write, files, NAME, TOKEN

owner()
OWNER = os.environ['CODEX_THREAD_ID']
phase = sys.argv[1]
assert phase in ['audit', 'seal']
REV = 'art_r04'
RUNS = ['runtime_r01', 'runtime_updeath_r01']
baseline = read(D / 'incremental_before_20261029.json')
before = baseline['files']
assert isinstance(before, dict) and len(before) == 5525
current = files()
t = next(t for t in read(H / 'local_baseline.json')['targets'] if t['name'] == NAME)
snapshot = read(D / 'production_before_play_20261029.json')
installed = snapshot['final_files']
manifest = read(D / 'installed_manifest.json')
assert snapshot['revision'] == REV and snapshot['manifest_sha256'] == sha(D / 'installed_manifest.json')
assert len(installed) == 22 and all(current.get(p) == v for p, v in installed.items())
assert manifest['verification']['data']['result']['pass'] and len(manifest['changes']) == 20
assert all(current[r['path']] == r['after'] for r in manifest['changes'])
verify = (D / 'installed_verify.txt').read_text(encoding='utf-8-sig')
assert all(s.startswith('PASS ') for s in verify.splitlines())
assert verify.strip() == manifest['verification']['data']['result']['report'].strip()

changes = [{'path': p, 'before': before.get(p), 'after': current.get(p)}
           for p in sorted(set(before) | set(current)) if before.get(p) != current.get(p)]
side_effects = []
for r in changes:
    if r['path'] == 'Assets/StreamingAssets/build_info':
        assert before['Assets/Reporter/Editor/ReporterEditor.cs'] == current['Assets/Reporter/Editor/ReporterEditor.cs']
        assert re.fullmatch(r'Build from .+ at .+', (ROOT / r['path']).read_text(encoding='utf-8'))
        side_effects.append(dict(r, origin='Unmodified ReporterEditor automatic Play timestamp'))
unexpected = [r for r in changes if r['path'] not in set(installed) | {x['path'] for x in side_effects}]
assert not unexpected, unexpected
protected = baseline['protected_six']
assert all(current[p] == v for p, v in protected.items() if p != t['battle'])
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

offline = read(D / 'offline_review_art_r04_20261029.json')
assert offline['offline_visual_pass'] and offline['revision'] == REV
assert all(sha(D / 'staged_art' / f) == v == current[t['art_dir'] + '/' + f]
           for f, v in offline['stage_files'].items())
repair = read(D / 'local_raster_r01/repair_manifest.json')
assert all(sha(D / r['source']) == r['source_sha256'] for r in repair['processing'])
generation = [p for p in (D / 'generation').rglob('result.json')]
assert len(generation) == 2 and all(read(p)['status'] == 200 for p in generation)
assert not list((D / 'generation').rglob('uncertain_result.json'))
spec = read(D / 'staged_art/WinterBoar_Directions.sprites.json')
atlas = Image.open(D / 'staged_art/WinterBoar_Directions.png').convert('RGBA')
layout = read(D / 'staged_art/WinterBoar_Directions.layout.json')
assert atlas.size == (2048, 2048) and spec['ppu'] == 100 and layout['motionKind'] == 'quadruped'
assert layout['anatomy'] == {'legs': 4, 'wings': 0, 'claws': 0, 'tails': 0, 'arms': 0, 'feelers': 0}
parts = {}
for s in spec['sprites']:
    p = D / 'staged_art' / (s['name'] + '.png')
    im = Image.open(p).convert('RGBA')
    assert im.size == (s['w'], s['h']) and im.getchannel('A').getbbox()
    a = np.array(im)
    b = np.array(atlas.crop((s['x'], 2048 - s['y'] - s['h'], s['x'] + s['w'], 2048 - s['y'])))
    assert np.array_equal(a[:, :, 3], b[:, :, 3]) and np.array_equal(a[a[:, :, 3] > 0], b[a[:, :, 3] > 0])
    parts[s['name']] = {'sha256': sha(p), 'size': list(im.size), 'pivot': [s['pivotX'], s['pivotY']]}
assert len(parts) == 12 and len({parts['Up_Head' + k]['sha256'] for k in ['Normal', 'Angry', 'Dead']}) == 1
pixels = np.array(atlas).astype(np.int16)
assert not np.any((np.minimum(pixels[:, :, 0], pixels[:, :, 2]) - pixels[:, :, 1] > 18) & (pixels[:, :, 3] > 30))

runtime = read(D / 'runtime_summary.json')
assert (runtime['passes'], runtime['failures'], runtime['actual_frames']) == (168, 0, 589)
assert [r['revision'] for r in runtime['runtime']] == RUNS
frames = {}
for run in runtime['runtime']:
    folder = D / run['revision']
    records = [json.loads(l) for l in (folder / 'actual_frames.jsonl').read_text().splitlines() if l]
    checks = (folder / 'actual_runtime_checks.txt').read_text(encoding='utf-8-sig').splitlines()
    assert (run['pass'], run['fail']) == (84, 0) and len(records) == run['frames']
    assert sum(s.startswith('PASS ') for s in checks) == 84 and not any(s.startswith('FAIL ') for s in checks)
    assert all(b['frame'] > a['frame'] and b['realtime'] > a['realtime'] for a, b in zip(records, records[1:]))
    assert not any(r['shadow'] for r in records) and sha(folder / 'actual_frames.jsonl') == run['records_sha256']
    frames[run['revision']] = {r['file']: sha(folder / r['file']) for r in records}
    assert all(frames[run['revision']].values())
    assert len(frames[run['revision']]) == len(list((folder / 'frames').glob('*.png')))
    assert read(D / (run['revision'] + '_start.json'))['project']['projectRoot'] == 'E:/MyTowerGame'
    assert (D / (run['revision'] + '_start.json')).stat().st_mtime > (D / 'production_before_play_20261029.json').stat().st_mtime
    assert read(D / (run['revision'] + '_returned.json'))['state'] == {'playing': False, 'review': False, 'scene': 'Assets/Scenes/Boot.unity', 'dirty': False}
assert read(D / 'runtime_updeath_r01_start.json')['death_up'] is True
board = read(D / 'visual_review_art_r04_20261029/sources.json')
positions = len(board['sources'])
unique = len({(r['revision'], r['source']) for r in board['sources']})
assert positions == 256 and all(r['source'] in frames[r['revision']] for r in board['sources'])
samples = read(D / 'gif_samples_art_r04_20261029/samples.json')['samples']
assert len(samples) == 60 and len({(r['revision'], r['file']) for r in samples}) == 12
for r in samples:
    p = D / r['revision'] / r['file']
    assert sha(p) == r['gif_sha256']
    with Image.open(p) as gif:
        assert gif.n_frames == r['frame_count']
        gif.seek(r['frame_index_zero_based'])
        im = gif.convert('RGB').crop(r['stable_crop'])
        im.thumbnail((300, 215), Image.Resampling.LANCZOS)
        assert hashlib.sha256(im.tobytes()).hexdigest().upper() == r['sample_sha256']
full = read(D / 'gif_samples_art_r04_20261029_full/sources.json')
assert len(full) == 4
for r in full:
    assert sha(D / r['source']) == r['source_sha256'] and sha(D / r['output']) == r['output_sha256']
    with Image.open(D / r['source']) as gif:
        gif.seek(r['frame'])
        assert gif.convert('RGB').tobytes() == Image.open(D / r['output']).convert('RGB').tobytes()
reviewed = ['offline_rig_proof.png', 'staged_art/Up_Body.png', 'runtime_visual_strip.png']
reviewed += [r + '/four_directions.png' for r in RUNS]
reviewed += ['visual_review_art_r04_20261029/' + r + '_' + s + '.png' for r in RUNS
             for s in ['sequence_0', 'sequence_1', 'sequence_2', 'walk_cycle', 'angry_detail']]
reviewed += ['gif_samples_art_r04_20261029/' + r + '_samples.png' for r in RUNS]
originals = read(D / 'original_png_selection_20261029.json')
assert len(originals) == 8 and all(p.split('/', 1)[1] in frames[p.split('/', 1)[0]] for p in originals)
note = f'最终art_r04实际查看最终离线组合及Up Body局部、两轮四方向图和runtime strip、10张时序/步态/攻击表情板（{positions}采样位、{unique}张不同真实PNG）、8张768像素完整原PNG、12个最终GIF各5个编码帧共60帧、另4张未裁切GIF整帧。白灰圆胖长毛、赭斑、棕背鬃、宽金鼻与双象牙色獠牙身份保留；四足且原始无独立尾，不新增尾。Up纯后脑无脸、外耳背面、后足光滑后跟；Down三表情鼻口居中，原耳眉与脸保留。轴向正背面比原侧面窄，圆身遮挡大部分远侧腿；没有据此新增肢体。r01角折额顶/裁耳眉、r02白色眉缺口/品红边/露远腿根否决保留；r03恢复原眉与内收腿根，预检发现28个缩小后品红染边像素；r04保持alpha/形状，用最近不污染描边RGB修复所有检测到的997个边缘染色像素（含低alpha），不冒充未经修绘的AI原图。2次付费请求均HTTP200，Up/Down成功raw原件保留，没有重试或结果不明请求，usage估算非账单。两轮各84PASS/0FAIL、合计589真实PNG；行走错相短腿、连续转向、攻击头切换、受击白闪恢复、Down/Up全身死亡旋转缩小淡出、自动回收及同实例Down正常复用、暂停冻结/恢复与1x/2x/3x推进，在运行记录及抽样中正常。原左右侧面保留，无地面阴影，头身和肩髋腿根连接。淡出时既有逐renderer alpha可见重叠分件透叠。GIF为编码帧抽样，非实时播放或逐帧全审；原PNG与完整媒体留盘。内部技术视觉通过，仍待用户美术验收。'
visual = {'reviewed_at': now(), 'character': NAME, 'owner_thread_id': OWNER, 'dispatch_token': TOKEN,
          'final_revision': REV, 'runs': RUNS, 'reviewed_images': {p: sha(D / p) for p in reviewed},
          'selected_original_pngs': {p: sha(D / p) for p in originals},
          'uncropped_encoded_gif_frames': {r['output']: sha(D / r['output']) for r in full},
          'sample_positions': positions, 'unique_board_source_pngs': unique, 'encoded_gif_samples': 60,
          'gif_count': 12, 'additional_uncropped_encoded_frames': 4, 'observations': note,
          'technical_visual_pass': True, 'user_approved': False,
          'limitations': ['Chronological PNG and encoded GIF sampling, no realtime playback or exhaustive every-frame visual review.',
                         'Existing per-renderer death alpha makes overlapping parts translucent during fade.',
                         'Axial Up/Down views are narrower than original side views; body occludes far legs.'],
          'rejected_revisions': ['art_r01', 'art_r02', 'art_r03_preinstall'],
          'offline_review_file': 'offline_review_art_r04_20261029.json'}
assert all(visual['reviewed_images'].values()) and all(visual['selected_original_pngs'].values())
scope = {'observed_at': now(), 'baseline': 'incremental_before_20261029.json',
         'baseline_sha256': sha(D / 'incremental_before_20261029.json'),
         'comparison': 'Full path union Assets/Packages/ProjectSettings/Luban vs initial current disk, never Git HEAD.',
         'baseline_files': len(before), 'current_files': len(current), 'changes': changes,
         'added_count': sum(r['before'] is None for r in changes), 'deleted_count': sum(r['after'] is None for r in changes),
         'unexpected_incremental': unexpected, 'automatic_editor_side_effects': side_effects,
         'protected_six': protected, 'protected_drift': [], 'shared_CSharp_drift': cs_drift,
         'installed_files': installed, 'prePlay_production_drift': [], 'prefab_semantics': semantic,
         'stage_parts': parts,
         'legacy_global_note': 'Historical global audit 291 unexpected paths and six other-character semantic failures preserved, not re-audited. Only WinterBoar incremental PASS.'}
probe = read(D / 'unity_release_final_r04_20261029.json')
assert probe['success'] and probe['transport'] == 'http://127.0.0.1:8088/mcp' and probe['errors']['data'] == []
imports = probe['sprite_imports']
assert imports['spriteMode'] == 'Multiple' and imports['ppu'] == 100 and imports['spriteCount'] == 12
assert imports['alphaIsTransparency'] and not imports['mipmaps']
for s in spec['sprites']:
    actual = next(a for a in imports['sprites'] if a['name'] == s['name'])
    assert all(abs(actual[k] - s[k]) < 1e-4 for k in ['x', 'y', 'w', 'h'])
    assert abs(actual['pivotX'] - s['pivotX'] * s['w']) < 1e-3 and abs(actual['pivotY'] - s['pivotY'] * s['h']) < 1e-3
assert (len(current), len(changes), scope['added_count'], scope['deleted_count']) == (5545, 22, 20, 0)
archive_path = H.parent / 'AllGIF/manifest.json'

if phase == 'audit':
    paths = ['scope_incremental_final_20261029.json', 'visual_review_art_r04_20261029/review.json',
             'record_note_utf8.txt', 'archive_before_record_20261029.json']
    assert all(not (D / p).exists() for p in paths)
    write(D / paths[0], scope)
    write(D / paths[1], visual)
    (D / paths[2]).write_text(note + '\n', encoding='utf-8')
    archive = read(archive_path)
    assert not any(r['source'].startswith('Remaining_20261024/WinterBoar/') for r in archive['files'])
    write(D / paths[3], {'count': archive['count'], 'sources': [r['source'] for r in archive['files']],
                        'manifest_sha256': sha(archive_path)})
    print(json.dumps({'phase': 'audit', 'changes': len(changes), 'unexpected': 0,
                      'semantic_pass': True, 'positions': positions, 'unique_pngs': unique, 'frames': 589}))
    raise SystemExit(0)

assert read(D / 'scope_incremental_final_20261029.json')['changes'] == changes
assert read(D / 'visual_review_art_r04_20261029/review.json')['observations'] == note
assert not (D / 'final_validation_20261029.json').exists()
progress = read(H / 'progress.json')
item = next(i for i in progress['items'] if i['name'] == NAME)
assert progress['completed_count'] == 98 and item['status'] != 'completed_pending_user_art_review'
runtime.update(final_revision=REV, visual_reviewed=True, visual_review_file='visual_review_art_r04_20261029/review.json',
               visual_note=note, user_approved=False, status='completed_pending_user_art_review')
(D / 'runtime_summary.json').write_text(json.dumps(runtime, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
record = subprocess.run([sys.executable, str(H / 'record_review.py'), NAME, note], capture_output=True,
                        text=True, encoding='utf-8', check=True)
archive = read(archive_path)
rows = [r for r in archive['files'] if r['source'].startswith('Remaining_20261024/WinterBoar/')]
assert len(rows) == 12
for r in rows:
    assert sha(H.parent / r['source']) == r['sha256'] == sha(H.parent / 'AllGIF' / r['file'])
    assert r['status'] == '当前审核版本'
old = read(D / 'archive_before_record_20261029.json')
assert archive['count'] == old['count'] + 12
assert set(r['source'] for r in archive['files']) - set(old['sources']) == {r['source'] for r in rows}
archive_report = {'verified_at': now(), 'source_gif_count': 12, 'final_review_gifs': 12, 'historical_gifs': 0,
                  'global_archive_count_before': old['count'], 'global_archive_count': archive['count'],
                  'all_source_and_archive_sha256_match': True, 'files': rows, 'manifest_sha256': sha(archive_path)}
write(D / 'gif_archive_verification_20261029.json', archive_report)
progress = read(H / 'progress.json')
item = next(i for i in progress['items'] if i['name'] == NAME)
assert progress['completed_count'] == 99 and item['status'] == 'completed_pending_user_art_review' and not item['user_approved']
remaining = [i for i in progress['items'] if i['status'] not in ['completed_pending_user_art_review', 'user_approved']]
recoverable = [i for i in remaining if i['status'] not in ['not_started', 'blocked']]
selected = min(recoverable or [i for i in remaining if i['status'] != 'blocked'], key=lambda i: i['index'])
assert selected['name'] == 'WinterOgre' and selected['index'] == 111
item.update(stage='recorded_pending_user_art_review', final_revision=REV,
            final_validation_file='WinterBoar/final_validation_20261029.json',
            version_binding_file='WinterBoar/version_binding_final_20261029.json',
            scope_file='WinterBoar/scope_incremental_final_20261029.json',
            visual_review_file='WinterBoar/visual_review_art_r04_20261029/review.json',
            gif_archive_file='WinterBoar/gif_archive_verification_20261029.json')
progress.update(current=selected['name'], updated_at=now())
(H / 'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
evidence = {p.relative_to(D).as_posix(): sha(p) for p in sorted(D.rglob('*')) if p.is_file()
            and 'frames' not in p.relative_to(D).parts
            and p.name not in ['version_binding_final_20261029.json', 'final_validation_20261029.json']}
binding = {'observed_at': now(), 'final_revision': REV, 'manifest': 'installed_manifest.json',
           'manifest_sha256': sha(D / 'installed_manifest.json'),
           'prePlay_snapshot_sha256': sha(D / 'production_before_play_20261029.json'),
           'installed_files': installed, 'production_scope_files': {r['path']: r['after'] for r in changes},
           'files': evidence, 'actual_png_frames': frames, 'frame_total': 589,
           'note': '22 prePlay production paths unchanged; art_r04 installed once before both real Play runs; original and rejected revisions preserved.'}
write(D / 'version_binding_final_20261029.json', binding)
final = {'observed_at': now(), 'character': NAME, 'owner_thread_id': OWNER, 'dispatch_token': TOKEN,
         'status': item['status'], 'user_approved': False, 'final_revision': REV,
         'passes': 168, 'failures': 0, 'actual_png_frames': 589, 'runtime': runtime['runtime'],
         'installer_verify_pass': True, 'manifest': 'installed_manifest.json',
         'manifest_sha256': sha(D / 'installed_manifest.json'),
         'incremental_scope_file': 'scope_incremental_final_20261029.json',
         'incremental_scope_sha256': sha(D / 'scope_incremental_final_20261029.json'),
         'incremental_changes': len(changes), 'incremental_unexpected': 0, 'prefab_semantic_pass': True,
         'version_binding_file': 'version_binding_final_20261029.json',
         'version_binding_sha256': sha(D / 'version_binding_final_20261029.json'),
         'visual_review_file': 'visual_review_art_r04_20261029/review.json',
         'visual_review_sha256': sha(D / 'visual_review_art_r04_20261029/review.json'),
         'gif_archive_file': 'gif_archive_verification_20261029.json',
         'gif_archive_sha256': sha(D / 'gif_archive_verification_20261029.json'),
         'archived_character_gifs': 12, 'final_review_gifs': 12, 'global_archive_count': archive['count'],
         'unity': {'transport': probe['transport'], 'project': probe['project'], 'live_probe': probe['live_probe'],
                   'ready_for_tools': True, 'console_errors': 0, 'external_changes_dirty': False,
                   'evidence': 'unity_release_final_r04_20261029.json'},
         'progress': {'completed_count': 99, 'authorized_count': 108, 'next_candidate': selected['name']},
         'generation': {'paid_requests': 2, 'successful_http200': 2, 'retries': 0, 'unknown_outcomes': 0,
                        'raw_originals_preserved': True, 'usage_is_not_bill': True},
         'record_review_output': record.stdout.strip(), 'legacy_global_scope_warning': scope['legacy_global_note']}
write(D / 'final_validation_20261029.json', final)
chain = owner()
chain.update(current_stage='recorded_pending_user_art_review',
             last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/WinterBoar/final_validation_20261029.json',
             updated_at=now())
(H / 'conversation_chain.json').write_text(json.dumps(chain, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'phase': 'sealed', 'character': NAME, 'completed_count': 99, 'scope_changes': len(changes),
                  'unexpected': 0, 'passes': 168, 'failures': 0, 'frames': 589, 'archived_gifs': 12,
                  'archive_count': archive['count'], 'next': selected['name']}, ensure_ascii=False))
