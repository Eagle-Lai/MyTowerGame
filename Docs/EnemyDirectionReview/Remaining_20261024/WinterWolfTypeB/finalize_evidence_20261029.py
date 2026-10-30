from session_current import *

owner();reviewdir=HERE/'visual_review_final_20261029'
assert not (HERE/'final_validation_20261029.json').exists()
files=snapshot();scope=audit(files)
save(HERE/'scope_incremental_final_20261029.json',scope)
assert scope['pass'],scope
pre=read(HERE/'preplay_version_binding_20261029.json')
assert pre['production_fingerprints']==bound(files)
assert pre['staged_fingerprints']=={p.relative_to(HERE/'staged_art').as_posix():sha(p) for p in (HERE/'staged_art').rglob('*') if p.is_file()}
assert pre['manifest_sha256']==sha(HERE/'installed_manifest.json')
assert pre['verify_sha256']==sha(HERE/'installed_verify.txt')
assert 'FAIL ' not in (HERE/'installed_verify.txt').read_text(encoding='utf-8')
immutable={}
for path,digest in read(HERE/'sync_start_20261029.json')['read_full_json_sha256'].items():
    path=path.replace('\\','/')
    if path.endswith(('local_baseline.json','production_fingerprints_before.json','user_approval_20261023.json')):
        immutable[path]={'expected':digest,'actual':sha(ROOT/path),'matches':digest==sha(ROOT/path)}
assert all(r['matches'] for r in immutable.values())
runtime=read(HERE/'runtime_summary.json')
assert runtime['passes']==168 and runtime['failures']==0
runs=[]
for run in runtime['runtime']:
    folder=HERE/run['revision']
    records=[json.loads(line) for line in (folder/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if line]
    checks=(folder/'actual_runtime_checks.txt').read_text(encoding='utf-8')
    assert run['records_sha256']==sha(folder/'actual_frames.jsonl') and len(records)==run['frames']
    assert 'FAIL ' not in checks and sum(line.startswith('PASS ') for line in checks.splitlines())==84
    actual={r['file']:sha(folder/r['file']) for r in records};assert len(actual)==len(records)
    assert all(b['frame']>a['frame'] and b['realtime']>=a['realtime'] for a,b in zip(records,records[1:]))
    returned=read(HERE/(run['revision']+'_returned.json'))
    assert returned['state']=={'playing':False,'review':False,'scene':'Assets/Scenes/Boot.unity','dirty':False}
    runs.append({**run,'records_sha256_verified':True,'actual_png_sha256':actual,
                 'checks_sha256':sha(folder/'actual_runtime_checks.txt'),
                 'media_manifest_sha256':sha(folder/'media_manifest.json'),
                 'media':{p.name:sha(p) for p in folder.glob('*.gif')},'returned_to_Boot':returned})
assert sum(r['frames'] for r in runs)==runtime['actual_frames']
sources=read(reviewdir/'sources.json')['sources'];samples=read(reviewdir/'gif_samples.json')['samples']
assert all(sha(HERE/r['revision']/r['source'])==r['source_sha256'] for r in sources)
assert all(sha(HERE/r['revision']/r['gif'])==r['gif_sha256'] and sha(reviewdir/r['output'])==r['output_sha256'] for r in samples)
gifs={(r['revision'],r['gif']) for r in samples}
assert len(gifs)==12 and len(samples)==60
boards=[p for p in reviewdir.glob('*.png') if 'sequence_' in p.name or 'native_walk_cycles' in p.name or p.name.endswith('_gif_samples.png')]
assert len(boards)==14
unique_png=len({(r['revision'],r['source']) for r in sources})
note=f'WinterWolfTypeB最终Up本地03/Down本地03、alpha01、Down躯干局部04与布局04：已实看两轮four_directions、runtime strip、14张完整时序/原生循环/GIF编码抽帧板，{len(sources)}个PNG采样位、{unique_png}张不同真实帧及12个最终GIF各5编码帧。另看未裁Up、Down愤怒攻击、Up死亡、回收复用及双向GIF整帧。Up为无脸后脑/尖耳、平滑后跟与完整斑点长尾；Down保留象牙眼/小黑瞳、赭鼻斑点、尖牙、棕色下巴/胸毛和前趾。清除躯干两处破碎耳状残痕，四足和尾根连接，原左右步态、转向、白闪结束、死亡旋转收缩淡出与同实例复用复位在所审样本中正常，无地面阴影。两轮各84PASS0FAIL共{runtime["actual_frames"]}张真实PNG。原生Walk合同500ms，Up/Down GIF原460–470ms截短已仅在Docs按真实相位累计边界量化修正为500ms，保留6份修前GIF及manifest；没有实时播放或逐帧审完全部{runtime["actual_frames"]}帧，用户美术尚未批准。'
extras=['runtime_r01_UpWalk_uncropped.png','runtime_r01_Attack_uncropped.png',
        'runtime_updeath_r01_DeathAutoRecycle_uncropped.png','runtime_updeath_r01_Reuse_uncropped.png',
        'runtime_r01_up_down_walk_encoded_004.png']
review={'observed_at':now(),'art_revision':pre['art_revision'],'result':'accepted_for_record_pending_user_art_review',
        'user_approved':False,'note':note,'boards':{p.name:sha(p) for p in boards},
        'png_sample_positions':len(sources),'unique_png_samples':unique_png,'encoded_gif_samples':len(samples),
        'final_gifs_sampled':len(gifs),'gif_frames_per_file':5,
        'additional_uncropped_viewed':{p:sha(reviewdir/p) for p in extras},
        'also_viewed':{p:sha(HERE/p) for p in ['runtime_r01/four_directions.png','runtime_updeath_r01/four_directions.png','runtime_visual_strip.png']},
        'limitations':f'Chronological actual PNG and decoded GIF frame sampling. No real-time playback or all-{runtime["actual_frames"]}-frame visual claim.'}
save(reviewdir/'review.json',review)
(HERE/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
release=read(HERE/'unity_release_final_20261029.json');assert release['success']
binding={'observed_at':now(),'preplay_file':'preplay_version_binding_20261029.json',
         'preplay_sha256':sha(HERE/'preplay_version_binding_20261029.json'),'art_revision':pre['art_revision'],
         'production_fingerprints':bound(files),'preplay_production_matches':True,'preplay_staged_matches':True,
         'install_manifest_matches':True,'install_verify_matches':True,'immutable_baselines':immutable,'runtime':runs,
         'visual_review_sha256':sha(reviewdir/'review.json'),'scope_sha256':sha(HERE/'scope_incremental_final_20261029.json'),
         'unity_release_sha256':sha(HERE/'unity_release_final_20261029.json'),
         'media_timing_sha256':sha(HERE/'gif_quantization_fix_20261029.json'),'all_production_fingerprints':files}
save(HERE/'final_version_binding_20261029.json',binding)
save(HERE/'final_validation_20261029.json',{'observed_at':now(),'name':NAME,
     'status':'completed_pending_user_art_review','user_approved':False,'art_revision':pre['art_revision'],
     'passes':168,'failures':0,'actual_frames':runtime['actual_frames'],'runtime':runtime['runtime'],
     'scope_pass':scope['pass'],'scope_added':scope['added'],'scope_deleted':scope['deleted'],
     'scope_changes':len(scope['changes']),'scope_unexpected':scope['unexpected'],
     'original_semantics_pass':scope['prefab_semantic']['pass'],'production_fingerprints_match_preplay':True,
     'bound_production_paths':len(bound(files)),'no_Unity_CSharp_changed':True,
     'historical_global_scope':'Not reclassified or claimed PASS',
     'visual_review':str(reviewdir.relative_to(ROOT)/'review.json'),
     'version_binding':str((HERE/'final_version_binding_20261029.json').relative_to(ROOT)),
     'Unity_release':str((HERE/'unity_release_final_20261029.json').relative_to(ROOT)),
     'source_collection_limit':'Installed Verify includes collectors; live import, dependencies and native clips checked. No release build/deployment.'})
print(json.dumps({'scope_pass':scope['pass'],'before':scope['before_count'],'after':scope['after_count'],
    'changes':len(scope['changes']),'added':scope['added'],'deleted':scope['deleted'],
    'attributions':[{k:r[k] for k in ['path','attribution']} for r in scope['changes']],
    'bound':len(bound(files)),'positions':len(sources),'unique_pngs':unique_png,'gif_samples':len(samples),'ready_for_record':True},ensure_ascii=False))
