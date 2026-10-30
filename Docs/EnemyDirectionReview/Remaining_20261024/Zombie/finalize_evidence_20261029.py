from session_current import *
from PIL import Image

chain=owner();reviewdir=HERE/'visual_review_final_20261029'
assert not (HERE/'final_validation_20261029.json').exists()
files=snapshot();scope=audit(files)
assert scope['pass'] and scope['prefab_semantic']['pass'] and not scope['head_binding_repair']['applies']
save(HERE/'scope_incremental_final_20261029.json',scope)
prepath=HERE/'preplay_version_binding_20261029.json';pre=read(prepath)
assert pre['production_fingerprints']==bound(files) and len(bound(files))==22
stage={p.relative_to(HERE/'staged_art').as_posix():sha(p) for p in (HERE/'staged_art').rglob('*') if p.is_file()}
assert pre['staged_fingerprints']==stage
for key,path in [('manifest_sha256','installed_manifest.json'),('verify_sha256','installed_verify.txt'),('native_attack_manifest_sha256','native_attack_timing01_manifest_20261029.json'),('native_attack_verify_sha256','native_attack_timing01_verify.txt')]:
    assert pre[key]==sha(HERE/path)
for name in ['installed_verify.txt','native_attack_timing01_verify.txt']:
    assert 'FAIL ' not in (HERE/name).read_text(encoding='utf-8')
immutable={}
for path,digest in read(HERE/'sync_start_20261029.json')['read_full_json_sha256'].items():
    path=path.replace('\\','/')
    if path.endswith(('local_baseline.json','production_fingerprints_before.json','user_approval_20261023.json')):
        immutable[path]={'expected':digest,'actual':sha(ROOT/path),'matches':digest==sha(ROOT/path)}
assert all(r['matches'] for r in immutable.values())
native={}
for p in (HERE/'reference/exact_original_animation_contract').iterdir():
    assert p.is_file()
    live=ROOT/'Assets/_UIAssets/Monsters/_Common/Animations/Giant'/p.name
    assert sha(p)==sha(live)
    native[live.relative_to(ROOT).as_posix()]=sha(live)
runtime=read(HERE/'runtime_summary.json');assert runtime['passes']==168 and runtime['failures']==0
assert [r['revision'] for r in runtime['runtime']]==['runtime_r01','runtime_updeath_r01']
runs=[]
for run in runtime['runtime']:
    folder=HERE/run['revision'];records=[json.loads(l) for l in (folder/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if l]
    checks=(folder/'actual_runtime_checks.txt').read_text(encoding='utf-8')
    assert run['records_sha256']==sha(folder/'actual_frames.jsonl') and len(records)==run['frames']
    assert 'FAIL ' not in checks and checks.count('PASS ')==84 and not (folder/'exception.txt').exists()
    actual={r['file']:sha(folder/r['file']) for r in records};assert len(actual)==len(records)
    assert all(b['frame']>a['frame'] and b['realtime']>=a['realtime'] for a,b in zip(records,records[1:]))
    returned=read(HERE/(run['revision']+'_returned.json'))
    assert returned['state']=={'playing':False,'review':False,'scene':'Assets/Scenes/Boot.unity','dirty':False}
    runs.append({**run,'records_sha256_verified':True,'actual_png_sha256':actual,'checks_sha256':sha(folder/'actual_runtime_checks.txt'),'media_manifest_sha256':sha(folder/'media_manifest.json'),'media':{p.name:sha(p) for p in folder.glob('*.gif')},'returned_to_Boot':returned})
assert sum(r['frames'] for r in runs)==runtime['actual_frames']==639
sources=read(reviewdir/'sources.json')['sources'];samples=read(reviewdir/'gif_samples.json')['samples']
assert all(sha(HERE/r['revision']/r['source'])==r['source_sha256'] for r in sources)
assert all(sha(HERE/r['revision']/r['gif'])==r['gif_sha256'] and sha(reviewdir/r['output'])==r['output_sha256'] for r in samples)
gifs={(r['revision'],r['gif']) for r in samples};assert len(gifs)==12 and len(samples)==60
boards=[p for p in reviewdir.glob('*.png') if 'sequence_' in p.name or 'native_walk_cycles' in p.name or p.name.endswith('_gif_samples.png')]
assert len(boards)==14
unique_png=len({(r['revision'],r['source']) for r in sources})
timing=read(HERE/'gif_quantization_fix_20261029.json');assert len(timing['changes'])==6
assert all(r['after_encoded_ms']==670 for r in timing['changes'])
assert abs(timing['quantization_error_ms']-3.3333)<.01
for run in runs:
    for filename in ['UpWalk.gif','DownWalk.gif','up_down_walk.gif']:
        with Image.open(HERE/run['revision']/filename) as im:
            total=0
            for i in range(im.n_frames):im.seek(i);total+=im.info['duration']
            assert total==670
note=(
    f'Zombie最终版本{pre["art_revision"]}：Up初图正脸后脑被否决并保留，采用一次定向AI revision_01的无脸后脑；Down采用初次成功图。'
    '保源灰褐/橄榄色缝合双足巨人、赭斑、浅米高光、顶部浅褐脑瓣、淡黄圆眼小黑瞳和三表情、深色宽护腕、米白破腰裙，以及仅解剖右手持有的单根象牙刺金褐木棒。无骷髅项链/腰扣/尾巴/靴子。'
    '14透明分件、2048atlas、PPU100；alpha01局部填354个小孔像素，原raw与修前暂存保留；最终零孔洞/零品红残留，layout02埋肩髋根、双腿错相短步，Up后跟无前趾线。'
    '仅本角色Attack_Directions的92条DirectionVisual曲线按自身Giant原生蓄力/发力时序修正，2/3秒结束蓄力、0.766666651秒原Attack事件对齐峰值；Down双臂摆向镜像，空臂幅度30%。原左右曲线、事件、时长/loop/状态和源动画未变。'
    f'实看最终离线四向、两轮真实four_directions、runtime strip和14张时序/原生循环/GIF解码板，共{len(sources)}采样位/{unique_png}张不同实际PNG，12最终GIF各5编码帧共60；另看完整未裁Up、Down愤怒攻击、Up死亡、复用、双向GIF和两轮Up/Down发力峰值实际帧。'
    '所审样本肩髋根保持连接、单木棒随右臂蓄力横扫且发力时被躯干正常遮挡，头手脚武器无裁边/重复器官/地面影；连续转向、白闪结束、死亡旋转收缩淡出及同实例复位正常。死亡按renderer淡出，重叠分件可见，不声称一体alpha。'
    f'两轮runtime_r01/runtime_updeath_r01各84PASS0FAIL，共{runtime["actual_frames"]}张真实Play PNG。自身Walk约666.6667ms，6个行走GIF仅Docs用真实相位/原帧配对重新编码为最近合法670ms，量化差约+3.3333ms，6份旧GIF和两manifest保留。'
    '原battle三表情接收器完整，无前任HeadSprites修复；generic原组件语义直接通过。逐序抽样，未实时播放GIF，也未逐张审完全部639PNG。仍待用户美术审核。'
)
extras=['runtime_r01_UpWalk_uncropped.png','runtime_r01_Attack_uncropped.png','runtime_updeath_r01_DeathAutoRecycle_uncropped.png','runtime_updeath_r01_Reuse_uncropped.png','runtime_r01_up_down_walk_encoded_004.png']
event_files=['runtime_r01/frames/Attack_00120.png','runtime_r01/frames/Attack_00145.png','runtime_updeath_r01/frames/Attack_00116.png','runtime_updeath_r01/frames/Attack_00142.png']
review={'observed_at':now(),'art_revision':pre['art_revision'],'result':'accepted_for_record_pending_user_art_review','user_approved':False,'note':note,'boards':{p.name:sha(p) for p in boards},'png_sample_positions':len(sources),'unique_png_samples':unique_png,'encoded_gif_samples':len(samples),'final_gifs_sampled':len(gifs),'gif_frames_per_file':5,'additional_uncropped_viewed':{p:sha(reviewdir/p) for p in extras},'additional_attack_event_pngs_viewed':{p:sha(HERE/p) for p in event_files},'also_viewed':{p:sha(HERE/p) for p in ['offline_four_directions_final_20261029.png','runtime_r01/four_directions.png','runtime_updeath_r01/four_directions.png','runtime_visual_strip.png']},'earlier_stage_review_sha256':sha(HERE/'staged_visual_review_final_20261029.json'),'limitations':'Chronological actual PNG and decoded GIF sampling. No real-time playback or all-639-frame visual claim. Renderer alpha permits visible overlaps.'}
save(reviewdir/'review.json',review)
(HERE/'record_note_utf8.txt').write_text(note+'\n',encoding='utf-8')
attempts=[]
for relative in ['generation/Up','generation/Up/revision_01','generation/Down']:
    folder=HERE/relative;request=read(folder/'request.json');result=read(folder/'result.json')
    assert result['status']==200 and request['model']=='gpt-image-2' and request['n']==1 and request['quality']=='medium'
    assert request['resolve_transport']['ip']=='191.101.132.254'
    with Image.open(folder/'raw.png') as im:fmt,size,mode=im.format,list(im.size),im.mode
    attempts.append({'folder':relative,'request_sha256':sha(folder/'request.json'),'result_sha256':sha(folder/'result.json'),'raw_sha256':sha(folder/'raw.png'),'raw_bytes':(folder/'raw.png').stat().st_size,'status':result['status'],'actual_format':fmt,'actual_size':size,'actual_mode':mode,'transport':request['transport'],'resolve_transport':request['resolve_transport'],'selected':relative!='generation/Up','purpose':'Necessary paid head-direction art correction' if relative.endswith('revision_01') else 'Initial directional image','charge':'Not independently verified; response usage is a local estimate.'})
assert len(list((HERE/'generation').rglob('request.json')))==3
save(HERE/'generation_final_accounting_20261029.json',{'observed_at':now(),'requests':attempts,'authenticated_image_requests':3,'http200':3,'unknown':0,'additional_network_recovery_used':0,'new_paid_art_revisions':1,'paid_diagnostics':0,'counters_reset':False,'local_alpha_and_layout_are_not_AI_returns':True,'other_character_unknowns':'PossessedWarg original Down and other preserved historical unknowns/counters unchanged. No reissue or uncharged/unsent inference.'})
release=read(HERE/'unity_release_final_20261029.json');assert release['success']
binding={'observed_at':now(),'owner_thread_id':chain['owner_thread_id'],'dispatch_token':chain['dispatch_token'],'preplay_file':prepath.name,'preplay_sha256':sha(prepath),'art_revision':pre['art_revision'],'production_fingerprints':bound(files),'staged_fingerprints':stage,'preplay_production_matches':True,'preplay_staged_matches':True,'install_manifest_matches':True,'install_verify_matches':True,'native_attack_manifest_matches':True,'native_attack_verify_matches':True,'original_install_manifest_sha256':sha(HERE/'installed_manifest.json'),'original_install_verify_sha256':sha(HERE/'installed_verify.txt'),'native_attack_manifest_sha256':sha(HERE/'native_attack_timing01_manifest_20261029.json'),'native_attack_verify_sha256':sha(HERE/'native_attack_timing01_verify.txt'),'immutable_baselines':immutable,'unchanged_native_animation_files':native,'runtime':runs,'visual_review_sha256':sha(reviewdir/'review.json'),'scope_sha256':sha(HERE/'scope_incremental_final_20261029.json'),'unity_release_sha256':sha(HERE/'unity_release_final_20261029.json'),'media_timing_sha256':sha(HERE/'gif_quantization_fix_20261029.json'),'generation_accounting_sha256':sha(HERE/'generation_final_accounting_20261029.json'),'source_animation_contract_sha256':sha(HERE/'source_animation_contract_complete_20261029.json'),'all_production_fingerprints':files}
save(HERE/'final_version_binding_20261029.json',binding)
rel=lambda p:p.relative_to(ROOT).as_posix()
save(HERE/'final_validation_20261029.json',{'observed_at':now(),'name':NAME,'status':'completed_pending_user_art_review','user_approved':False,'art_revision':pre['art_revision'],'passes':168,'failures':0,'actual_frames':runtime['actual_frames'],'runtime':runtime['runtime'],'scope_pass':scope['pass'],'scope_added':scope['added'],'scope_deleted':scope['deleted'],'scope_changes':len(scope['changes']),'scope_unexpected':scope['unexpected'],'original_semantics_pass':scope['prefab_semantic']['pass'],'original_semantics_difference':scope['prefab_semantic']['unexpected'],'head_binding_repair_applied':False,'production_fingerprints_match_preplay':True,'bound_production_paths':len(bound(files)),'no_Unity_CSharp_changed':True,'historical_global_scope':'Not reclassified or claimed PASS','visual_review':rel(reviewdir/'review.json'),'version_binding':rel(HERE/'final_version_binding_20261029.json'),'Unity_release':rel(HERE/'unity_release_final_20261029.json'),'generation_accounting':rel(HERE/'generation_final_accounting_20261029.json'),'source_collection_limit':'Installed Verify includes collectors; live import, dependencies and native clips checked. No release build/deployment.'})
print(json.dumps({'scope_pass':scope['pass'],'generic_semantics_pass':scope['prefab_semantic']['pass'],'before':scope['before_count'],'after':scope['after_count'],'changes':len(scope['changes']),'added':scope['added'],'deleted':scope['deleted'],'unexpected':len(scope['unexpected']),'bound':len(bound(files)),'positions':len(sources),'unique_pngs':unique_png,'gif_samples':len(samples),'ready_for_record':True},ensure_ascii=False))
