"""Audit and seal WinterWarg art_r02; never install, regenerate, or replace history."""
from session_winterwarg import *
from audit_current import audit
from PIL import Image, ImageDraw, ImageOps
import numpy as np

owner()
phase = sys.argv[1]
assert phase in ['audit', 'seal']
REV = 'art_r02'
RUNS = ['runtime_art_r02', 'runtime_art_updeath_r02']
V = D/'visual_review_art_r02_full_actor_20261029'
baseline = read(D/'incremental_before_20261029.json')
before = baseline['files']; current = snapshot(); target = baseline['target']
scope = audit()
assert scope['pass'] and scope['prefab_semantic']['pass'], scope
assert (len(before), len(current), len(scope['changes']), scope['added'], scope['deleted']) == (5565, 5585, 22, 20, 0)
assert not any(p.endswith('.cs') and before.get(p) != current.get(p) for p in set(before)|set(current))
preplay = read(D/'preplay_version_binding_art_r02_20261029.json')
installed = preplay['production_fingerprints']
assert preplay['art_revision'] == REV and len(installed) == 22
assert all(current.get(p) == s for p, s in installed.items())
assert all(sha(D/p) == s for p, s in preplay['staged_fingerprints'].items())
assert preplay['manifest_sha256'] == sha(D/'installed_manifest.json')
assert preplay['repair_manifest_sha256'] == sha(D/'installed_repair_art_r02_20261029.json')
manifest = read(D/'installed_manifest.json')
repair = read(D/'installed_repair_art_r02_20261029.json')
assert repair['parent_manifest_sha256'] == sha(D/'installed_manifest.json')
assert manifest['verification']['data']['result']['pass'] and repair['verification']['pass']
assert len(manifest['changes']) == 20 and len(repair['changes']) == 7
original_hashes = {r['path']:r['after'] for r in manifest['changes']}
for r in manifest['changes']:
    assert before.get(r['path']) == r['before']
for r in repair['changes']:
    assert original_hashes.get(r['path'], read(D/'preplay_version_binding_art_r01_20261029.json')['production_fingerprints'].get(r['path'])) == r['before']
    assert current.get(r['path']) == r['after']
for p, s in original_hashes.items():
    if p not in {r['path'] for r in repair['changes']}:
        assert current[p] == s
for file, check in [('installed_verify.txt', manifest['verification']['data']['result']),
                    ('installed_verify_art_r02.txt', repair['verification'])]:
    lines = (D/file).read_text(encoding='utf-8-sig').strip()
    assert lines == check['report'].strip() and all(s.startswith('PASS ') for s in lines.splitlines())
assert 'PASS YooAsset prefab and artwork collectors present' in repair['verification']['report']
preplay_drift = [p for p in set(current)|set(preplay['all_production_fingerprints'])
                 if current.get(p) != preplay['all_production_fingerprints'].get(p)]
assert set(preplay_drift) <= {'Assets/StreamingAssets/build_info'}
assert all(sha(D/'reference'/Path(p).name) == s for p, s in baseline['protected_six'].items())

spec = read(D/'staged_art'/f'{NAME}_Directions.sprites.json')
for suffix in ['.png', '.sprites.json', '.layout.json']:
    p = D/'staged_art'/(NAME+'_Directions'+suffix)
    assert sha(p) == current[target['art_dir']+'/'+p.name]
atlas = Image.open(D/'staged_art'/f'{NAME}_Directions.png').convert('RGBA')
assert atlas.size == (2048,2048) and spec['ppu'] == 100 and len(spec['sprites']) == 14
parts = {}
for s in spec['sprites']:
    p = D/'staged_art'/(s['name']+'.png'); im = Image.open(p).convert('RGBA')
    a = np.array(im); mask = im.getchannel('A').point(lambda v:255 if v>127 else 0)
    exterior = ImageOps.expand(mask, border=1, fill=0); ImageDraw.floodfill(exterior, (0,0), 128)
    holes = int(np.count_nonzero(np.array(exterior) == 0))
    b = np.array(atlas.crop((s['x'],2048-s['y']-s['h'],s['x']+s['w'],2048-s['y'])))
    assert im.size == (s['w'], s['h']) and mask.getbbox() and holes == 0
    assert np.array_equal(a[:,:,3],b[:,:,3]) and np.array_equal(a[a[:,:,3]>0],b[a[:,:,3]>0])
    rgb = a.astype(np.int16)
    chroma = int(np.count_nonzero((np.minimum(rgb[:,:,0],rgb[:,:,2])-rgb[:,:,1]>18)&(rgb[:,:,3]>30)))
    assert chroma == 0
    parts[s['name']] = {'sha256':sha(p),'size':list(im.size),'pivot':[s['pivotX'],s['pivotY']],
                        'enclosed_transparent_pixels':holes,'opaque_magenta_pixels':chroma}
assert len({parts['Up_Head'+s]['sha256'] for s in ['Normal','Angry','Dead']}) == 1
cleanup = read(D/'staged_alpha_cleanup_20261029.json')['slices']
assert sum(s['filled_enclosed_micro_pixels'] for s in cleanup) == 793
assert sum(s['removed_dust_pixels'] for s in cleanup) == 4
assert all(parts[Path(s['file']).stem]['sha256'] == s['after_sha256'] for s in cleanup)

runtime = read(D/'runtime_summary.json')
assert (runtime['passes'], runtime['failures'], runtime['actual_frames']) == (168,0,679)
assert [r['revision'] for r in runtime['runtime']] == RUNS
frames = {}
expected_records = ['CBB27FC436FD64E523709C48048A702EF408ABEC4A4675D77DB5CFE9748D384D',
                    '65F471EF31292669C2F29760AE49B0F86ABFB92F921BC202EEBF7C53D6E8D703']
for index, run in enumerate(runtime['runtime']):
    folder = D/run['revision']
    rows = [json.loads(l) for l in (folder/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if l]
    checks = (folder/'actual_runtime_checks.txt').read_text(encoding='utf-8-sig').splitlines()
    assert (run['pass'], run['fail'], len(rows)) == (84,0,run['frames'])
    assert len(rows) == [340,339][index]
    assert sum(l.startswith('PASS ') for l in checks) == 84 and not any(l.startswith('FAIL ') for l in checks)
    assert sha(folder/'actual_frames.jsonl') == run['records_sha256'] == expected_records[index]
    assert all(b['frame']>a['frame'] and b['realtime']>a['realtime'] for a,b in zip(rows,rows[1:]))
    assert not any(r['shadow'] for r in rows)
    frames[run['revision']] = {r['file']:sha(folder/r['file']) for r in rows}
    assert len(frames[run['revision']]) == len(list((folder/'frames').glob('*.png')))
    start = D/(run['revision']+'_start.json')
    assert read(start)['project']['projectRoot'] == 'E:/MyTowerGame'
    assert read(start)['death_up'] is bool(index)
    assert start.stat().st_mtime > (D/'preplay_version_binding_art_r02_20261029.json').stat().st_mtime
    assert read(D/(run['revision']+'_returned.json'))['state'] == {'playing':False,'review':False,'scene':'Assets/Scenes/Boot.unity','dirty':False}
boards = read(V/'sources.json')['sources']
positions = len(boards); unique = len({(r['revision'],r['source']) for r in boards})
assert (positions,unique) == (268,254)
assert all(frames[r['revision']][r['source']] == r['source_sha256'] for r in boards)
samples = read(V/'gif_samples.json')['samples']
assert len(samples) == 60 and len({(r['revision'],r['file']) for r in samples}) == 12
for r in samples:
    p = D/r['revision']/r['file']; assert sha(p) == r['gif_sha256']
    with Image.open(p) as gif:
        assert gif.n_frames == r['frame_count']; gif.seek(r['frame_index_zero_based'])
        im = gif.convert('RGB').crop(r['crop']); im.thumbnail((290,210),Image.Resampling.LANCZOS)
        assert hashlib.sha256(im.tobytes()).hexdigest().upper() == r['sample_sha256']
full = read(V/'uncropped_gif_sources.json'); assert len(full) == 4
for r in full:
    assert sha(D/r['source']) == r['source_sha256'] and sha(D/r['output']) == r['output_sha256']
    with Image.open(D/r['source']) as gif:
        gif.seek(r['frame']); assert gif.convert('RGB').tobytes() == Image.open(D/r['output']).convert('RGB').tobytes()
originals = read(V/'original_png_selection.json'); assert len(originals) == 8
assert all(p.split('/',1)[1] in frames[p.split('/',1)[0]] for p in originals)
for r in read(V/'native_walk_timing.json'):
    assert r['native_seconds'] == .5 and r['encoded_ms'] == sum(r['durations_ms']) == 500
fix = read(D/'gif_quantization_fix_art_r02_20261029.json'); assert len(fix['changes']) == 6 and not fix['production_changed']
for r in fix['changes']:
    assert sha(D/r['revision']/r['file']) == r['after_sha256'] and r['after_encoded_ms'] == 500
    assert sha(D/'media_before_gif_quantization_fix_art_r02'/r['revision']/r['file']) == r['before_sha256']
uncertain = sorted((D/'generation').rglob('uncertain_result.json'))
successful = sorted((D/'generation').rglob('result.json'))
assert len(uncertain) == len(successful) == 2 and all(read(p)['status'] == 200 for p in successful)
recovery = read(D/'standing_recovery_application_20261029_Up_r02.json')
assert recovery['additional_attempt'] == recovery['max_additional_network_retries_per_direction'] == 2 and not recovery['resets_counter']

unity = read(D/'unity_release_final_20261029.json')
assert unity['success'] and unity['transport'] == 'http://127.0.0.1:8088/mcp'
assert unity['errors']['data'] == unity['compile_errors']['data'] == []
idle(unity['final_probe']); actual = unity['installed_data']
assert actual['spriteMode'] == 'Multiple' and actual['spriteCount'] == 14 and actual['ppu'] == 100
assert actual['alphaIsTransparency'] and not actual['mipmaps']
for s in spec['sprites']:
    live = next(x for x in actual['sprites'] if x['name'] == s['name'])
    assert live['ppu'] == 100 and all(abs(live[k]-s[k]) < 1e-4 for k in ['x','y','w','h'])
    assert abs(live['pivotX']-s['pivotX']*s['w']) < 1e-3 and abs(live['pivotY']-s['pivotY']*s['h']) < 1e-3
contract = read(D/'source_contract_20261029.json')['contract']
for live in actual['clips']:
    old = next(s for s in contract['clips'] if s['name'] == live['name'])
    assert (live['length'],live['rate'],live['loop']) == (old['length'],old['rate'],old['loop'])
    assert live['floatBindings'] == len(old['floatCurves']) and live['objectBindings'] == len(old['pptrCurves'])
    assert live['events'] == [{k:e[k] for k in ['time','functionName','intParameter','stringParameter']} for e in old['events']]
assert all(target['art_dir']+'/'+NAME+'_Directions'+suffix in actual['dependencies'] for suffix in ['.png','.asset'])

note = ('最终art_r02实际审过两轮four_directions和最终runtime strip、12张时序/步态板（268采样位、254张不同真实PNG）、'
        '8张768像素完整原PNG、12个最终GIF各5个编码帧共60帧，另4张未裁切GIF整帧；原raw及离线审图记录保留。'
        '原角色白/象牙色蓬毛、金赭斑点、棕色背刺、圆耳、长剑齿、四条短犬腿和白赭下垂长尾保留。'
        'Up无脸、短后冠毛和光滑后跟，三种头状态复用纯后脑；Down正常/愤怒/死亡头与爪趾正确。'
        'art_r01在真实运行实审发现轴向头偏小后保留并否决，art_r02只放大并调整Up/Down头部布局，最终两轮均来自该生产版本。'
        '四足肩髋与尾根连接，前后交错短步、尾巴小幅摆动、原侧面与连续转向在抽样中正常；四向和攻击/受击/死亡/复用无地面阴影。'
        'Down张口攻击、受击/致死白闪后恢复、Down及Up全身旋转缩小淡出、自动回收及同实例Down正常复用、暂停冻结和恢复/1x/2x/3x相位推进均有实际帧及检查日志。'
        '死亡的既有逐renderer alpha会显出重叠分件，这是观察到的淡出限制。'
        '14分件本地填补793个微小封闭透明像素、去4个外部尘点，最终无封闭透明洞和不透明品红，清理前暂存保留。'
        '六个最终行走GIF因逐帧非整十毫秒截断导致480/490ms，已按累计相位量化修为原Walk500ms，保留六旧GIF；未改动作或生产资源。'
        '审阅为时序PNG和编码GIF抽样，未实时播放或逐帧全审；早先裁图会截Up耳，最终改用full_actor证据并查看完整原图。'
        '原Up与revision01请求结果/费用仍不明，2/2恢复次数已消耗且未重置；revision02 Up与首次Down均HTTP200，实际选用本地Up05/首次Down。'
        '两轮各84PASS/0FAIL，共679张真实PNG。内部技术及本范围视觉通过，待用户美术验收，user_approved=false。')
reviewed = ['runtime_visual_strip.png','offline_rig_proof.png','parts_clean.png'] + [r+'/four_directions.png' for r in RUNS]
reviewed += [p.relative_to(D).as_posix() for p in V.glob('*.png')]
visual = {'reviewed_at':now(),'character':NAME,'owner_thread_id':OWNER,'dispatch_token':TOKEN,'final_revision':REV,
          'reviewed_images':{p:sha(D/p) for p in reviewed},'selected_original_pngs':{p:sha(D/p) for p in originals},
          'sample_positions':positions,'unique_board_source_pngs':unique,'encoded_gif_samples':60,'gif_count':12,
          'additional_uncropped_encoded_frames':4,'observations':note,'technical_visual_pass':True,'user_approved':False,
          'limitations':['Chronological real PNG and encoded GIF sampling; no realtime playback or exhaustive every-frame review.',
                         'Existing per-renderer alpha exposes overlapping parts during death fade.',
                         'Earlier clipped-ear preview boards retained as superseded evidence; full_actor boards and native frames inspected.'],
          'superseded_runtime':['runtime_r01','runtime_updeath_r01'],'superseded_runtime_reason':'Axial head proportions rejected after actual Play visual inspection.',
          'historical_offline_review':'offline_art_review_20261029.json','gif_timing_fix':'gif_quantization_fix_art_r02_20261029.json'}
scope.update(baseline='incremental_before_20261029.json',baseline_sha256=sha(D/'incremental_before_20261029.json'),
             installed_files=installed,prePlay_production_drift=[],prePlay_global_delta=preplay_drift,shared_CSharp_drift=[],stage_parts=parts)
archive_path = H.parent/'AllGIF/manifest.json'
if phase == 'audit':
    write(D/'scope_incremental_final_20261029.json',scope,True)
    write(V/'review.json',visual,True)
    assert not (D/'record_note_utf8.txt').exists()
    (D/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
    archive = read(archive_path)
    assert not any(r['source'].startswith('Remaining_20261024/WinterWarg/') for r in archive['files'])
    write(D/'archive_before_record_20261029.json',{'count':archive['count'],'manifest_sha256':sha(archive_path),
           'sources':[r['source'] for r in archive['files']],
           'uncertain_files':{p.relative_to(D).as_posix():sha(p) for p in uncertain}},True)
    print(json.dumps({'phase':phase,'scope_pass':True,'changes':len(scope['changes']),'positions':positions,'unique_pngs':unique,'frames':679}))
    raise SystemExit(0)

assert read(D/'scope_incremental_final_20261029.json')['changes'] == scope['changes']
assert read(V/'review.json')['observations'] == note and (D/'record_note_utf8.txt').read_text(encoding='utf-8').strip() == note
assert not (D/'final_validation_20261029.json').exists()
progress = read(H/'progress.json'); item = next(i for i in progress['items'] if i['name'] == NAME)
assert progress['completed_count'] == 100 and item['status'] != 'completed_pending_user_art_review'
runtime.update(final_revision=REV,status='completed_pending_user_art_review',visual_reviewed=True,
               visual_review_file=V.relative_to(D).as_posix()+'/review.json',visual_note=note,user_approved=False)
write(D/'runtime_summary.json',runtime)
record = subprocess.run([sys.executable,str(H/'record_review.py'),NAME,note],capture_output=True,text=True,encoding='utf-8',check=True)
archive = read(archive_path)
rows = [r for r in archive['files'] if r['source'].startswith('Remaining_20261024/WinterWarg/')]
sources = {p.relative_to(H.parent).as_posix() for p in D.rglob('*.gif')}
assert len(rows) == len(sources) and {r['source'] for r in rows} == sources
for r in rows:
    assert sha(H.parent/r['source']) == r['sha256'] == sha(H.parent/'AllGIF'/r['file'])
final_rows = [r for r in rows if r['status'] == '当前审核版本']
assert len(final_rows) == 12 and all(r['source'].split('/')[2] in RUNS for r in final_rows)
old = read(D/'archive_before_record_20261029.json')
assert archive['count'] == old['count'] + len(rows)
assert set(r['source'] for r in archive['files']) - set(old['sources']) == sources
assert all(sha(D/p) == s for p,s in old['uncertain_files'].items())
archive_report = {'verified_at':now(),'source_gif_count':len(rows),'final_review_gifs':len(final_rows),
                  'historical_gifs':len(rows)-len(final_rows),'global_archive_count_before':old['count'],
                  'global_archive_count':archive['count'],'all_source_and_archive_sha256_match':True,
                  'files':rows,'manifest_sha256':sha(archive_path),
                  'historical_note':'Includes rejected art_r01 and pre-quantization art_r02 GIFs; historical classification is not art approval.'}
write(D/'gif_archive_verification_20261029.json',archive_report,True)
progress = read(H/'progress.json'); item = next(i for i in progress['items'] if i['name'] == NAME)
assert progress['completed_count'] == 101 and item['status'] == 'completed_pending_user_art_review' and item['user_approved'] is False
remaining = [i for i in progress['items'] if i['status'] not in ['completed_pending_user_art_review','user_approved']]
recoverable = [i for i in remaining if i['status'] not in ['not_started','blocked']]
selected = min(recoverable or [i for i in remaining if i['status'] != 'blocked'],key=lambda i:i['index'])
assert selected['name'] == 'WinterWolfTypeA' and selected['index'] == 113
item.update(stage='recorded_pending_user_art_review',final_revision=REV,
            generation_outcome='Up revision02 and first Down HTTP200; selected local Up05; two earlier Up outcomes and charges remain unknown; recovery2/2 retained',
            unity_release_file='WinterWarg/unity_release_final_20261029.json',
            final_validation_file='WinterWarg/final_validation_20261029.json',version_binding_file='WinterWarg/version_binding_final_20261029.json',
            scope_file='WinterWarg/scope_incremental_final_20261029.json',visual_review_file='WinterWarg/'+V.name+'/review.json',
            gif_archive_file='WinterWarg/gif_archive_verification_20261029.json')
progress.update(current=selected['name'],updated_at=now()); write(H/'progress.json',progress)
evidence = {p.relative_to(D).as_posix():sha(p) for p in sorted(D.rglob('*')) if p.is_file()
            and 'frames' not in p.relative_to(D).parts and p.name not in ['version_binding_final_20261029.json','final_validation_20261029.json']}
binding = {'observed_at':now(),'final_revision':REV,'installed_files':installed,
           'manifest_sha256':sha(D/'installed_manifest.json'),'repair_manifest_sha256':sha(D/'installed_repair_art_r02_20261029.json'),
           'prePlay_snapshot_sha256':sha(D/'preplay_version_binding_art_r02_20261029.json'),
           'production_scope_files':{r['path']:r['after'] for r in scope['changes']},'files':evidence,
           'actual_png_frames':frames,'frame_total':679,'note':'All22 production fingerprints including Directions root meta unchanged since before both final Play rounds.'}
write(D/'version_binding_final_20261029.json',binding,True)
final = {'observed_at':now(),'character':NAME,'owner_thread_id':OWNER,'dispatch_token':TOKEN,'status':item['status'],'user_approved':False,
         'final_revision':REV,'passes':168,'failures':0,'actual_png_frames':679,'runtime':runtime['runtime'],'installer_verify_pass':True,
         'manifest_sha256':sha(D/'installed_manifest.json'),'repair_manifest_sha256':sha(D/'installed_repair_art_r02_20261029.json'),
         'incremental_scope_file':'scope_incremental_final_20261029.json','incremental_scope_sha256':sha(D/'scope_incremental_final_20261029.json'),
         'incremental_changes':len(scope['changes']),'incremental_unexpected':0,'prefab_semantic_pass':True,
         'version_binding_file':'version_binding_final_20261029.json','version_binding_sha256':sha(D/'version_binding_final_20261029.json'),
         'visual_review_file':V.name+'/review.json','visual_review_sha256':sha(V/'review.json'),
         'gif_archive_file':'gif_archive_verification_20261029.json','gif_archive_sha256':sha(D/'gif_archive_verification_20261029.json'),
         'archived_character_gifs':len(rows),'final_review_gifs':12,'historical_gifs':len(rows)-12,'global_archive_count':archive['count'],
         'unity':{'transport':unity['transport'],'project':unity['project'],'live_probe':unity['final_probe'],'ready_for_tools':True,
                  'current_console_errors':0,'current_error_CS':0,'evidence':'unity_release_final_20261029.json','earlier_errors_retained_in_evidence':True},
         'progress':{'completed_count':101,'authorized_count':108,'next_candidate':selected['name']},
         'generation':{'successful_http200':2,'old_uncertain_requests':2,'old_unknown_charges_retained':True,'recovery_used':2,'recovery_limit':2,
                       'uncertain_evidence':{p.relative_to(D).as_posix():sha(p) for p in uncertain},
                       'successful_evidence':{p.relative_to(D).as_posix():sha(p) for p in successful}},
         'record_review_output':record.stdout.strip(),'legacy_global_scope_warning':scope['legacy_global_audit']}
write(D/'final_validation_20261029.json',final,True)
stage('recorded_pending_user_art_review',D/'final_validation_20261029.json')
print(json.dumps({'phase':'sealed','completed_count':101,'passes':168,'failures':0,'frames':679,'archived_gifs':len(rows),
                  'archive_count':archive['count'],'next':selected['name']},ensure_ascii=False))
