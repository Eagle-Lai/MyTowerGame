from session_current import *

owner();reviewdir=HERE/'visual_review_final_20261029'
assert not (HERE/'final_validation_20261029.json').exists()
files=snapshot();scope=audit(files);save(HERE/'scope_incremental_final_20261029.json',scope)
assert scope['pass'],scope['unexpected']
pre=read(HERE/'preplay_version_binding_20261029.json')
assert pre['production_fingerprints']==bound(files)
assert pre['staged_fingerprints']=={p.relative_to(HERE/'staged_art').as_posix():sha(p) for p in (HERE/'staged_art').rglob('*') if p.is_file()}
assert pre['manifest_sha256']==sha(HERE/'installed_manifest.json') and pre['verify_sha256']==sha(HERE/'installed_verify.txt')
checks=(HERE/'installed_verify.txt').read_text(encoding='utf-8');assert 'FAIL ' not in checks
immutable={}
for p,h in read(HERE/'sync_start_20261029.json')['read_full_json_sha256'].items():
    p=p.replace('\\','/')
    if p.endswith(('local_baseline.json','production_fingerprints_before.json','user_approval_20261023.json')):
        immutable[p]={'expected':h,'actual':sha(ROOT/p),'matches':h==sha(ROOT/p)}
assert all(r['matches'] for r in immutable.values())
runtime=read(HERE/'runtime_summary.json');assert runtime['passes']==168 and runtime['failures']==0
runs=[]
for run in runtime['runtime']:
    folder=HERE/run['revision'];records=[json.loads(l) for l in (folder/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if l]
    assert run['records_sha256']==sha(folder/'actual_frames.jsonl') and len(records)==run['frames']
    assert 'FAIL ' not in (folder/'actual_runtime_checks.txt').read_text(encoding='utf-8')
    assert sum(line.startswith('PASS ') for line in (folder/'actual_runtime_checks.txt').read_text(encoding='utf-8').splitlines())==84
    actual={r['file']:sha(folder/r['file']) for r in records}
    assert len(actual)==len(records)
    runs.append({**run,'records_sha256_verified':True,'actual_png_sha256':actual,'checks_sha256':sha(folder/'actual_runtime_checks.txt'),'media_manifest_sha256':sha(folder/'media_manifest.json'),'media':{p.name:sha(p) for p in folder.glob('*.gif')},'returned_to_Boot':read(HERE/(run['revision']+'_returned.json'))})
sources=read(reviewdir/'sources.json')['sources'];samples=read(reviewdir/'gif_samples.json')['samples']
assert len(sources)==313 and len(samples)==60
assert all(sha(HERE/r['revision']/r['source'])==r['source_sha256'] for r in sources)
assert all(sha(HERE/r['revision']/r['gif'])==r['gif_sha256'] and sha(reviewdir/r['output'])==r['output_sha256'] for r in samples)
boards=[p for p in reviewdir.glob('*.png') if 'sequence_' in p.name or 'native_walk_cycles' in p.name or p.name.endswith('_gif_samples.png')]
assert len(boards)==14
note='WinterWolfTypeA最终Up本地03/Down03，alpha_r01与尾宽0.30布局：已实看两轮four_directions、runtime strip、14张整身时序/原生循环/GIF抽帧板，313个PNG采样位、301张不同真实帧及12个最终GIF各5编码帧。另看未裁原生Up、Down攻击张嘴、Up死亡连接、复用及最终双向GIF整帧。背面纯后脑、尖耳、圆斑、整条象牙尾及平后跟保留，Down白眉/白口鼻、张嘴攻击和前趾清晰；四足交替/尾摆连接、原侧向步态、四向连续切换、白闪结束、死亡旋转淡出和同实例复用复位在所审样本中正常，无地面阴影。两轮84PASS0FAIL共668真实PNG。Up/Down GIF原470/480ms已仅在Docs按真实相位累计10ms量化为原生500ms，修前媒体保留；未实时播放或逐帧审完全部668帧，用户美术尚未批准。'
review={'observed_at':now(),'art_revision':pre['art_revision'],'result':'accepted_for_record_pending_user_art_review','user_approved':False,'note':note,'boards':{p.name:sha(p) for p in boards},'png_sample_positions':len(sources),'unique_png_samples':len({(r['revision'],r['source']) for r in sources}),'encoded_gif_samples':len(samples),'final_gifs_sampled':12,'gif_frames_per_file':5,'additional_uncropped_viewed':['runtime_r01/frames/UpWalk_00000.png','visual_review_final_20261029/runtime_r01_Attack_uncropped.png','visual_review_final_20261029/runtime_updeath_r01_DeathAutoRecycle_uncropped.png','visual_review_final_20261029/runtime_updeath_r01_Reuse_uncropped.png','visual_review_final_20261029/runtime_r01_up_down_walk_encoded_004.png'],'also_viewed':['runtime_r01/four_directions.png','runtime_updeath_r01/four_directions.png','runtime_visual_strip.png'],'limitations':'Chronological actual PNG and decoded GIF frame sampling; no real-time playback and no all-668-frame visual claim.'}
save(reviewdir/'review.json',review)
(HERE/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
binding={'observed_at':now(),'preplay_file':'preplay_version_binding_20261029.json','preplay_sha256':sha(HERE/'preplay_version_binding_20261029.json'),'art_revision':pre['art_revision'],'production_fingerprints':bound(files),'preplay_production_matches':True,'preplay_staged_matches':True,'install_manifest_matches':True,'install_verify_matches':True,'immutable_baselines':immutable,'runtime':runs,'visual_review_sha256':sha(reviewdir/'review.json'),'scope_sha256':sha(HERE/'scope_incremental_final_20261029.json'),'unity_release_sha256':sha(HERE/'unity_release_final_20261029.json'),'media_timing_sha256':sha(HERE/'gif_quantization_fix_20261029.json'),'all_production_fingerprints':files}
save(HERE/'final_version_binding_20261029.json',binding)
save(HERE/'final_validation_20261029.json',{'observed_at':now(),'name':NAME,'status':'completed_pending_user_art_review','user_approved':False,'art_revision':pre['art_revision'],'passes':168,'failures':0,'actual_frames':668,'runtime':runtime['runtime'],'scope_pass':scope['pass'],'scope_added':scope['added'],'scope_deleted':scope['deleted'],'scope_changes':len(scope['changes']),'scope_unexpected':scope['unexpected'],'original_semantics_pass':scope['prefab_semantic']['pass'],'production_fingerprints_match_preplay':True,'bound_production_paths':len(bound(files)),'no_Unity_CSharp_changed':True,'historical_global_scope':'Not reclassified or claimed PASS','visual_review':str(reviewdir.relative_to(ROOT)/'review.json'),'version_binding':str((HERE/'final_version_binding_20261029.json').relative_to(ROOT)),'Unity_release':str((HERE/'unity_release_final_20261029.json').relative_to(ROOT)),'source_collection_limit':'Actual installer Verify and live dependencies; no release build/deployment.'})
print(json.dumps({'scope_pass':scope['pass'],'scope_before':scope['before_count'],'scope_after':scope['after_count'],'changes':len(scope['changes']),'added':scope['added'],'deleted':scope['deleted'],'attributions':[{k:r[k] for k in ['path','attribution']} for r in scope['changes']],'bound':len(bound(files)),'review_positions':len(sources),'unique_pngs':301,'gif_samples':60,'ready_for_record':True},ensure_ascii=False))
