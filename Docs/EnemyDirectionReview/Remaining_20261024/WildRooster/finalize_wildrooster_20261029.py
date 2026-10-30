"""Seal WildRooster art_r03 evidence; production files are read only."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from PIL import Image
import ast, hashlib, json, os, re, subprocess, sys

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
NAME = 'WildRooster'
OWNER = '01a18560-5f4b-7b42-a2cf-f926c68a77ae'
TOKEN = 'wildgoat-to-wildrooster-20261029_095556-9aeda72a-08aa-4bfe-aca0-1b03c0381c5e'
RUNS = ['runtime_r01', 'runtime_updeath_r01']
REVISION = 'art_r03'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
now = lambda: datetime.now(timezone(timedelta(hours=8))).isoformat()

def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def ownership():
    chain = read(H / 'conversation_chain.json')
    assert chain['state'] == 'active' and chain['owner_thread_id'] == OWNER == os.environ.get('CODEX_THREAD_ID')
    assert chain['dispatch_token'] == TOKEN and chain['current_character'] == NAME
    return chain

ownership()
phase = sys.argv[1]
assert phase in ['audit', 'seal']
baseline = read(D / 'incremental_before_20261029.json')
before = {r['path']: r['sha256'].upper() for r in baseline['files']}
assert len(before) == 5485
current = {p.relative_to(ROOT).as_posix(): sha(p)
           for f in ['Assets', 'Packages', 'ProjectSettings', 'Luban']
           for p in (ROOT / f).rglob('*') if p.is_file()}
t = next(t for t in read(H / 'local_baseline.json')['targets'] if t['name'] == NAME)
battle, art = t['battle'], t['art_dir']
snapshot = read(D / 'production_before_play_20261029.json')
installed = snapshot['final_files']
manifest_path = D / 'installed_manifest.json'
installation = read(manifest_path)
assert snapshot['revision'] == REVISION and snapshot['verify_pass'] and len(installed) == 22
assert snapshot['manifest_sha256'] == sha(manifest_path)
assert all(current.get(p) == digest for p, digest in installed.items()), 'Production changed after prePlay snapshot'
verified = installation['verification']['data']['result']
assert verified['pass'] and len(installation['changes']) == 20
assert all(current[r['path']] == r['after'] for r in installation['changes'])
verify = (D / 'installed_verify.txt').read_text(encoding='utf-8-sig')
assert verify.strip() == verified['report'].strip() and all(l.startswith('PASS ') for l in verify.splitlines())
changes = [{'path': p, 'before': before.get(p), 'after': current.get(p)}
           for p in sorted(set(before) | set(current)) if before.get(p) != current.get(p)]
side_effects = []
for row in changes:
    if row['path'] == 'Assets/StreamingAssets/build_info':
        assert current['Assets/Reporter/Editor/ReporterEditor.cs'] == before['Assets/Reporter/Editor/ReporterEditor.cs']
        assert re.fullmatch(r'Build from .+ at .+', (ROOT / row['path']).read_text(encoding='utf-8'))
        side_effects.append(dict(row, origin='Unmodified ReporterEditor automatic Play timestamp'))
unexpected = [r for r in changes if r['path'] not in set(installed) | {r['path'] for r in side_effects}]
assert not unexpected, unexpected
protected = baseline['protected_six']
assert all(current[p] == v for p, v in protected.items() if p != battle)
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
repair = read(D / 'local_raster_r03/manifest.json')
assert repair['revision'] == REVISION
assert all(sha(D / 'generation' / direction / 'raw.png') == v for direction, v in repair['raws'].items())
assert all(sha(D / 'staged_art' / f) == v == current[art + '/' + f] for f, v in repair['files'].items())
spec = read(D / 'staged_art/WildRooster_Directions.sprites.json')
atlas = Image.open(D / 'staged_art/WildRooster_Directions.png').convert('RGBA')
assert atlas.size == (spec['width'], spec['height']) and spec['ppu'] == 100
parts = {}
for s in spec['sprites']:
    p = D / 'staged_art' / (s['name'] + '.png')
    im = Image.open(p).convert('RGBA')
    assert im.size == (s['w'], s['h'])
    if s['name'].endswith('_Tail'):
        assert im.size == (1,1) and im.getchannel('A').getbbox() is None
    else:
        assert im.getchannel('A').getbbox()
    crop = atlas.crop((s['x'], atlas.height-s['y']-s['h'], s['x']+s['w'], atlas.height-s['y']))
    assert crop.tobytes() == im.tobytes()
    parts[s['name']] = {'sha256': sha(p), 'size': list(im.size), 'pivot': [s['pivotX'], s['pivotY']]}
assert len(parts) == 14 and len({parts['Up_Head'+p]['sha256'] for p in ['Normal','Angry','Dead']}) == 1
runtime = read(D / 'runtime_summary.json')
assert (runtime['passes'],runtime['failures'],runtime['actual_frames']) == (168,0,600)
assert [r['revision'] for r in runtime['runtime']] == RUNS
frames = {}
for run in runtime['runtime']:
    folder = D / run['revision']
    checks = (folder/'actual_runtime_checks.txt').read_text(encoding='utf-8-sig').splitlines()
    records = [json.loads(l) for l in (folder/'actual_frames.jsonl').read_text().splitlines() if l]
    assert (run['pass'],run['fail']) == (84,0) and len(records) == run['frames']
    assert sum(l.startswith('PASS ') for l in checks) == 84 and not any(l.startswith('FAIL ') for l in checks)
    assert all(b['frame'] > a['frame'] and b['realtime'] > a['realtime'] for a,b in zip(records,records[1:]))
    assert all(not r['shadow'] for r in records)
    assert sha(folder/'actual_frames.jsonl') == run['records_sha256']
    frames[run['revision']] = {r['file']:sha(folder/r['file']) for r in records}
    assert all(frames[run['revision']].values())
    assert len(frames[run['revision']]) == len(list((folder/'frames').glob('*.png')))
    start = read(D/(run['revision']+'_start.json'))
    assert start['project']['projectRoot'].lower() == 'e:/mytowergame'
    assert (D/(run['revision']+'_start.json')).stat().st_mtime >= datetime.fromisoformat(snapshot['at']).timestamp()
    assert read(D/(run['revision']+'_returned.json'))['state'] == {'playing':False,'review':False,'scene':'Assets/Scenes/Boot.unity','dirty':False}
assert read(D/'runtime_updeath_r01_start.json')['death_up'] is True
board = read(D/'visual_review_art_r03_20261029/sources.json')
positions = len(board['sources'])
unique = len({(r['revision'],r['source']) for r in board['sources']})
assert all(r['source'] in frames[r['revision']] for r in board['sources'])
samples = read(D/'gif_samples_art_r03_20261029/samples.json')['samples']
assert len(samples) == 60 and len({(r['revision'],r['file']) for r in samples}) == 12
for r in samples:
    p = D/r['revision']/r['file']
    assert sha(p) == r['gif_sha256']
    with Image.open(p) as gif:
        assert gif.n_frames == r['frame_count']
        gif.seek(r['frame_index_zero_based'])
        im=gif.convert('RGB').crop(r['stable_crop']); im.thumbnail((300,215),Image.Resampling.LANCZOS)
        assert hashlib.sha256(im.tobytes()).hexdigest().upper() == r['sample_sha256']
full = read(D/'gif_samples_art_r03_20261029_full/sources.json')
for r in full:
    assert sha(D/r['source']) == r['source_sha256'] and sha(D/r['output']) == r['output_sha256']
    with Image.open(D/r['source']) as gif:
        gif.seek(r['frame'])
        assert gif.convert('RGB').tobytes() == Image.open(D/r['output']).convert('RGB').tobytes()
reviewed = ['offline_rig_proof.png','local_raster_r03/body_review.png','runtime_visual_strip.png']
reviewed += [r+'/four_directions.png' for r in RUNS]
reviewed += ['visual_review_art_r03_20261029/'+r+'_'+s+'.png' for r in RUNS for s in ['sequence_0','sequence_1','sequence_2','walk_cycle','angry_detail']]
reviewed += ['gif_samples_art_r03_20261029/'+r+'_samples.png' for r in RUNS]
originals = ['runtime_r01/frames/UpWalk_00004.png','runtime_r01/frames/DownWalk_00023.png','runtime_r01/frames/Attack_00122.png','runtime_updeath_r01/frames/DeathAutoRecycle_00144.png','runtime_updeath_r01/frames/Reuse_00154.png','runtime_updeath_r01/frames/LeftWalk_00039.png']
note = f'最终art_r03实际查看最终离线rig/局部Body、两轮四向图和runtime strip、10张时序/步态/愤怒细节板（{positions}采样位、{unique}张不同真实PNG）、6张768像素完整原PNG、12个最终GIF各5个编码帧共60帧，另看两轮Up/Down各1张未裁切GIF编码整帧。原金赭公鸡的高金冠、奶油长脸/后颈、钩形金喙与双瓣垂肉、白根金羽双翅、双金爪及Body一体尾羽身份保留。离线r01因浮翅/重复领口/高位尾簇否决，r02因帽盖接缝和矩形尾根否决，历史保留；r03局部RGBA清理和混色，Up三羽尾簇融合到下臀，Down正面尾羽被躯干遮蔽、移除重复领口/突起，双翼内收、头身重叠和腿根内收。原Up/Down成功raw未改，两方向各一次HTTP200，无重试/新增付费请求；usage估算不是实际账单。Up纯后脑无脸，三表情同图；Down正常/愤怒/死亡头保留。原左右侧面保留，头颈/肩/腿根相连，实际每方向双翅双腿且无Tail节点，透明1x1 Tail仅兼容切片，无地面阴影。步态错相、攻击头切换、受击白闪及恢复、Down/Up死亡旋转缩小淡出、自动回收、同实例正常Down复用、暂停冻结/恢复和1x/2x/3x推进均有运行记录与时序抽样。部分通用板裁切了冠尖，原始整帧和未裁切GIF帧确认完整、血条有间距。GIF为编码帧抽样，非实时播放或逐GIF全帧审阅；600张原PNG均保留并哈希绑定。内部技术视觉通过，用户美术验收待进行。'
visual = {'reviewed_at':now(),'character':NAME,'owner_thread_id':OWNER,'dispatch_token':TOKEN,'final_revision':REVISION,
          'runs':RUNS,'reviewed_images':{p:sha(D/p) for p in reviewed},'selected_original_pngs':{p:sha(D/p) for p in originals},
          'uncropped_encoded_gif_frames':{r['output']:sha(D/r['output']) for r in full},
          'sample_positions':positions,'unique_board_source_pngs':unique,'encoded_gif_samples':60,'gif_count':12,
          'additional_uncropped_encoded_frames':len(full),'observations':note,'technical_visual_pass':True,'user_approved':False,
          'limitations':['Chronological PNG and encoded GIF sampling; no realtime playback or exhaustive every-frame visual review.'],
          'local_repair_manifest':'local_raster_r03/manifest.json','rejected_revisions':['offline_r01','offline_r02'],'offline_review_file':'offline_review_art_r03_20261029.json'}
assert all(visual['reviewed_images'].values()) and all(visual['selected_original_pngs'].values())
scope = {'observed_at':now(),'baseline':'incremental_before_20261029.json','baseline_sha256':sha(D/'incremental_before_20261029.json'),
         'comparison':'Full path union Assets/Packages/ProjectSettings/Luban against original current-disk baseline, never Git HEAD.',
         'baseline_files':len(before),'current_files':len(current),'changes':changes,'added_count':sum(r['before'] is None for r in changes),
         'deleted_count':sum(r['after'] is None for r in changes),'unexpected_incremental':unexpected,'automatic_editor_side_effects':side_effects,
         'protected_six':protected,'protected_drift':[],'shared_CSharp_drift':cs_drift,'installed_files':installed,
         'prePlay_production_drift':[],'prefab_semantics':semantic,'stage_parts':parts,
         'legacy_global_note':'Historical global audit: 291 unexpected paths and six other-character semantic failures. Preserved and not re-audited; this is only WildRooster incremental PASS.'}
probe = read(D/'unity_release_final_r03_20261029.json')
assert probe['success'] and probe['transport'] == 'http://127.0.0.1:8088/mcp'
assert probe['observed_at'] > read(D/'runtime_updeath_r01_returned.json').get('observed_at',installation['installed_at'])
assert probe['errors']['data'] == []
imports = probe['sprite_imports']
assert imports['spriteMode']=='Multiple' and imports['ppu']==100 and imports['spriteCount']==14
assert imports['alphaIsTransparency'] and not imports['mipmaps']
for s in spec['sprites']:
    actual = next(a for a in imports['sprites'] if a['name']==s['name'])
    assert all(abs(actual[k]-s[k]) < 1e-4 for k in ['x','y','w','h'])
    assert abs(actual['pivotX']-s['pivotX']*s['w']) < 1e-3 and abs(actual['pivotY']-s['pivotY']*s['h']) < 1e-3
archive_path=H.parent/'AllGIF/manifest.json'
if phase=='audit':
    for p in ['scope_incremental_final_20261029.json','visual_review_art_r03_20261029/review.json','record_note_utf8.txt','archive_before_record_20261029.json']:
        assert not (D/p).exists(),p
    assert (len(before),len(current),len(changes),sum(r['before'] is None for r in changes))==(5485,5505,22,20)
    write(D/'scope_incremental_final_20261029.json',scope)
    write(D/'visual_review_art_r03_20261029/review.json',visual)
    (D/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
    archive=read(archive_path)
    write(D/'archive_before_record_20261029.json',{'count':archive['count'],'sources':[r['source'] for r in archive['files']],'manifest_sha256':sha(archive_path)})
    print(json.dumps({'phase':'audit','changes':len(changes),'unexpected':len(unexpected),'baseline_files':len(before),'current_files':len(current),'samples':positions,'unique_pngs':unique,'frames':600},ensure_ascii=False))
    raise SystemExit(0)
assert read(D/'scope_incremental_final_20261029.json')['changes']==changes
saved_visual=read(D/'visual_review_art_r03_20261029/review.json')
for k in ['reviewed_images','selected_original_pngs','uncropped_encoded_gif_frames']:
    assert saved_visual[k]==visual[k]
assert not (D/'final_validation_20261029.json').exists()
runtime.update(final_revision=REVISION,visual_reviewed=True,visual_review_file='visual_review_art_r03_20261029/review.json',visual_note=note,user_approved=False,status='completed_pending_user_art_review')
write(D/'runtime_summary.json',runtime)
record=subprocess.run([sys.executable,str(H/'record_review.py'),NAME,note],capture_output=True,text=True,encoding='utf-8',check=True)
archive=read(archive_path)
rows=[r for r in archive['files'] if r['source'].startswith('Remaining_20261024/WildRooster/')]
assert len(rows)==12
pairs=[]
for r in rows:
    digest=sha(H.parent/r['source'])
    assert digest==r['sha256']==sha(H.parent/'AllGIF'/r['file'])
    final=r['source'].split('/')[2] in RUNS
    assert r['status']==('当前审核版本' if final else '历史或准备材料')
    pairs.append(dict(r,final_review_version=final))
assert sum(r['final_review_version'] for r in pairs)==12
old_archive=read(D/'archive_before_record_20261029.json')
new_sources=set(r['source'] for r in archive['files'])-set(old_archive['sources'])
assert new_sources=={r['source'] for r in pairs if r['final_review_version']}
assert archive['count']==old_archive['count']+12
archive_report={'verified_at':now(),'source_gif_count':len(rows),'final_review_gifs':12,'historical_gifs':0,
                'global_archive_count_before':old_archive['count'],'global_archive_count':archive['count'],
                'all_source_and_archive_sha256_match':True,'files':pairs,'manifest_sha256':sha(archive_path)}
write(D/'gif_archive_verification_20261029.json',archive_report)
progress=read(H/'progress.json');item=next(r for r in progress['items'] if r['name']==NAME)
assert progress['completed_count']==97 and item['status']=='completed_pending_user_art_review' and not item['user_approved']
remaining=[r for r in progress['items'] if r['status'] not in ['completed_pending_user_art_review','user_approved']]
recoverable=[r for r in remaining if r['status'] not in ['not_started','blocked']]
selected=min(recoverable or [r for r in remaining if r['status']!='blocked'],key=lambda r:r['index'])
assert selected['name']=='WinterBear' and selected['index']==109
item.update(stage='recorded_pending_user_art_review',final_revision=REVISION,
            final_validation_file='WildRooster/final_validation_20261029.json',version_binding_file='WildRooster/version_binding_final_20261029.json',
            scope_file='WildRooster/scope_incremental_final_20261029.json',visual_review_file='WildRooster/visual_review_art_r03_20261029/review.json',
            gif_archive_file='WildRooster/gif_archive_verification_20261029.json')
progress.update(current=selected['name'],updated_at=now());write(H/'progress.json',progress)
evidence={p.relative_to(D).as_posix():sha(p) for p in sorted(D.rglob('*')) if p.is_file() and 'frames' not in p.relative_to(D).parts and p.name not in ['version_binding_final_20261029.json','final_validation_20261029.json']}
binding={'observed_at':now(),'final_revision':REVISION,'manifest':'installed_manifest.json','manifest_sha256':sha(manifest_path),
         'prePlay_snapshot_sha256':sha(D/'production_before_play_20261029.json'),'installed_files':installed,'production_scope_files':{r['path']:r['after'] for r in changes},
         'files':evidence,'actual_png_frames':frames,'frame_total':600,'note':'All 22 prePlay production paths unchanged; final art_r03 installed once before both runtime_r01 runs; rejected offline r01/r02 preserved.'}
write(D/'version_binding_final_20261029.json',binding)
final={'observed_at':now(),'character':NAME,'owner_thread_id':OWNER,'dispatch_token':TOKEN,'status':item['status'],'user_approved':False,
       'final_revision':REVISION,'passes':168,'failures':0,'actual_png_frames':600,'runtime':runtime['runtime'],
       'installer_verify_pass':True,'manifest':'installed_manifest.json','manifest_sha256':sha(manifest_path),
       'incremental_scope_file':'scope_incremental_final_20261029.json','incremental_scope_sha256':sha(D/'scope_incremental_final_20261029.json'),
       'incremental_changes':len(changes),'incremental_unexpected':0,'prefab_semantic_pass':True,
       'version_binding_file':'version_binding_final_20261029.json','version_binding_sha256':sha(D/'version_binding_final_20261029.json'),
       'visual_review_file':'visual_review_art_r03_20261029/review.json','visual_review_sha256':sha(D/'visual_review_art_r03_20261029/review.json'),
       'gif_archive_file':'gif_archive_verification_20261029.json','gif_archive_sha256':sha(D/'gif_archive_verification_20261029.json'),
       'archived_character_gifs':12,'final_review_gifs':12,'global_archive_count':archive['count'],
       'unity':{'transport':probe['transport'],'project':probe['project'],'live_probe':probe['live_probe'],'ready_for_tools':True,'console_errors':0,
                'external_changes_dirty':False,'evidence':'unity_release_final_r03_20261029.json'},
       'progress':{'completed_count':97,'authorized_count':108,'next_candidate':selected['name']},
       'record_review_output':record.stdout.strip(),'legacy_global_scope_warning':scope['legacy_global_note']}
write(D/'final_validation_20261029.json',final)
chain=ownership();chain.update(current_stage='recorded_pending_user_art_review',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/WildRooster/final_validation_20261029.json',updated_at=now())
write(H/'conversation_chain.json',chain)
print(json.dumps({'phase':'sealed','character':NAME,'completed_count':97,'scope_changes':len(changes),'unexpected':0,'passes':168,'failures':0,'frames':600,'archived_gifs':12,'archive_count':archive['count'],'next':selected['name']},ensure_ascii=False))
