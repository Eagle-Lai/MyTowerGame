from session_current import *

owner()
reviewdir = HERE / 'visual_review_final_20261029'
assert not (HERE / 'final_validation_20261029.json').exists()
files = snapshot()
scope = audit(files)
assert scope['pass'] and scope['prefab_semantic_scoped_pass']
assert not scope['prefab_semantic']['pass'] and scope['head_binding_repair']['pass']
save(HERE / 'scope_incremental_final_20261029.json', scope)

prepath = HERE / 'preplay_version_binding_r02_20261029.json'
pre = read(prepath)
initial = read(HERE / 'preplay_version_binding_20261029.json')
assert pre['production_fingerprints'] == bound(files)
assert pre['staged_fingerprints'] == {
    p.relative_to(HERE / 'staged_art').as_posix(): sha(p)
    for p in (HERE / 'staged_art').rglob('*') if p.is_file()
}
assert pre['manifest_sha256'] == initial['manifest_sha256'] == sha(HERE / 'installed_manifest.json')
assert initial['verify_sha256'] == sha(HERE / 'installed_verify.txt')
assert pre['verify_file'] == 'installed_verify_repair_r02.txt'
assert pre['verify_sha256'] == sha(HERE / pre['verify_file'])
assert pre['repair_manifest_sha256'] == sha(HERE / pre['repair_manifest'])
for name in ['installed_verify.txt', pre['verify_file']]:
    assert 'FAIL ' not in (HERE / name).read_text(encoding='utf-8')

immutable = {}
for path, digest in read(HERE / 'sync_start_20261029.json')['read_full_json_sha256'].items():
    path = path.replace('\\', '/')
    if path.endswith(('local_baseline.json', 'production_fingerprints_before.json', 'user_approval_20261023.json')):
        immutable[path] = {'expected': digest, 'actual': sha(ROOT / path), 'matches': digest == sha(ROOT / path)}
assert all(r['matches'] for r in immutable.values())

runtime = read(HERE / 'runtime_summary.json')
assert runtime['passes'] == 168 and runtime['failures'] == 0
assert [r['revision'] for r in runtime['runtime']] == ['runtime_r02', 'runtime_updeath_r02']
runs = []
for run in runtime['runtime']:
    folder = HERE / run['revision']
    records = [json.loads(line) for line in (folder / 'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if line]
    checks = (folder / 'actual_runtime_checks.txt').read_text(encoding='utf-8')
    assert run['records_sha256'] == sha(folder / 'actual_frames.jsonl') and len(records) == run['frames']
    assert 'FAIL ' not in checks and sum(line.startswith('PASS ') for line in checks.splitlines()) == 84
    actual = {r['file']: sha(folder / r['file']) for r in records}
    assert len(actual) == len(records)
    assert all(b['frame'] > a['frame'] and b['realtime'] >= a['realtime'] for a, b in zip(records, records[1:]))
    returned = read(HERE / (run['revision'] + '_returned.json'))
    assert returned['state'] == {'playing': False, 'review': False, 'scene': 'Assets/Scenes/Boot.unity', 'dirty': False}
    runs.append({**run, 'records_sha256_verified': True, 'actual_png_sha256': actual,
                 'checks_sha256': sha(folder / 'actual_runtime_checks.txt'),
                 'media_manifest_sha256': sha(folder / 'media_manifest.json'),
                 'media': {p.name: sha(p) for p in folder.glob('*.gif')}, 'returned_to_Boot': returned})
assert sum(r['frames'] for r in runs) == runtime['actual_frames'] == 600

sources = read(reviewdir / 'sources.json')['sources']
samples = read(reviewdir / 'gif_samples.json')['samples']
assert all(sha(HERE / r['revision'] / r['source']) == r['source_sha256'] for r in sources)
assert all(sha(HERE / r['revision'] / r['gif']) == r['gif_sha256'] and sha(reviewdir / r['output']) == r['output_sha256'] for r in samples)
gifs = {(r['revision'], r['gif']) for r in samples}
assert len(gifs) == 12 and len(samples) == 60
boards = [p for p in reviewdir.glob('*.png') if 'sequence_' in p.name or 'native_walk_cycles' in p.name or p.name.endswith('_gif_samples.png')]
assert len(boards) == 14
unique_png = len({(r['revision'], r['source']) for r in sources})
timing = read(HERE / 'gif_quantization_fix_20261029.json')
timing_count = len(timing['changes'])
assert all(r['before_encoded_ms'] == 470 and r['after_encoded_ms'] == 500 for r in timing['changes'])

note = (
    f'WolfMounfed最终美术{pre["art_revision"]}，生产版本{pre["asset_revision"]}：Up/Down各一次AIHub成功图的本地01像素衍生，原始返回保留。'
    'Up第2/3头误为正脸，采用第1个无脸后脑用于三表情；整条腿内部按源灰褐色面与赭圆斑重画平滑后跟，保外轮廓。'
    'Down躯干误带的两只前爪沿记录的弧形胸下轮廓移除，保独立四腿；layout02埋足尾根、遮远侧腿，尾根在臀部下且尾下垂。'
    '保自身灰褐/橄榄底色、赭斑、尖耳、小黑瞳象牙眼与犬齿，单个分段金鞍及后缘三颗象牙刺、解剖左侧单个银灰X圆扣均属于躯干，无骑手/项圈。'
    f'实看原atlas/source、离线四方向与14透明分件、两轮真实four_directions、runtime strip及14张时序/原生循环/GIF解码板，共{len(sources)}个PNG采样位、{unique_png}张不同真实PNG与12个最终GIF各5编码帧。'
    '另看未裁Up、Down愤怒攻击、Up死亡、复用及双向GIF整帧。所审样本足尾根保持连接，四足短步与尾摆错相，原左右步态、连续转向、暂停恢复/1x2x3x、攻击蓄力发力与头事件、白闪结束、死亡旋转收缩淡出、同实例复用复位正常。'
    'Up无五官/前向耳垫/后趾线，Down有前趾及愤怒/死亡头，无地面影、重复器官、矩形补色接缝或裁耳脚尾。死亡按renderer淡出，重叠分件可见，不声称一体alpha。'
    '初轮runtime_r01因battle原有HeadSprites空数组在静态检查失败，原两异常和零帧失败轮保留；仅将该接收器填为自身原atlas的Normal/Angry/Dead三sprite。'
    '通用语义报告对此原组件变化仍为false且原文保留，另以仅三项绑定及其余组件字段不变的严格定点门通过；未改共享审计或C#。'
    f'最终runtime_r02/runtime_updeath_r02各84PASS0FAIL，共{runtime["actual_frames"]}张真实PNG。自身Walk合同500ms，{timing_count}个Up/Down GIF原470ms仅Docs按真实相位累计10ms边界修至500ms，修前GIF及两manifest保留；两个原500ms双向GIF未重写。'
    f'采用逐序抽样，未实时播放GIF，也未逐张审完全部{runtime["actual_frames"]}帧。用户美术尚未批准。'
)
extras = ['runtime_r02_UpWalk_uncropped.png', 'runtime_r02_Attack_uncropped.png',
          'runtime_updeath_r02_DeathAutoRecycle_uncropped.png', 'runtime_updeath_r02_Reuse_uncropped.png',
          'runtime_r02_up_down_walk_encoded_004.png']
review = {'observed_at': now(), 'art_revision': pre['art_revision'], 'asset_revision': pre['asset_revision'],
          'result': 'accepted_for_record_pending_user_art_review', 'user_approved': False, 'note': note,
          'boards': {p.name: sha(p) for p in boards}, 'png_sample_positions': len(sources),
          'unique_png_samples': unique_png, 'encoded_gif_samples': len(samples), 'final_gifs_sampled': len(gifs),
          'gif_frames_per_file': 5, 'additional_uncropped_viewed': {p: sha(reviewdir / p) for p in extras},
          'also_viewed': {p: sha(HERE / p) for p in ['runtime_r02/four_directions.png', 'runtime_updeath_r02/four_directions.png', 'runtime_visual_strip.png']},
          'earlier_stage_review_sha256': sha(HERE / 'staged_visual_review_final_20261029.json'),
          'limitations': f'Chronological actual PNG and decoded GIF frame sampling. No real-time playback or all-{runtime["actual_frames"]}-frame visual claim.'}
save(reviewdir / 'review.json', review)
(HERE / 'record_note_utf8.txt').write_text(note + '\n', encoding='utf-8')
release = read(HERE / 'unity_release_final_20261029.json')
assert release['success']
history_names = ['runtime_r01/exception.txt', 'runtime_r01_detailed_errors_20261029.json',
                 'runtime_r01_failure_scene_20261029.json', 'head_binding_repair_r02_20261029.json',
                 'before_head_binding_repair_r02/Enemy_WolfMounfed.prefab']
binding = {'observed_at': now(), 'preplay_file': prepath.name, 'preplay_sha256': sha(prepath),
           'art_revision': pre['art_revision'], 'asset_revision': pre['asset_revision'],
           'production_fingerprints': bound(files), 'preplay_production_matches': True, 'preplay_staged_matches': True,
           'install_manifest_matches': True, 'install_verify_matches': True,
           'original_install_manifest_sha256': sha(HERE / 'installed_manifest.json'),
           'original_install_verify_sha256': sha(HERE / 'installed_verify.txt'),
           'repair_manifest': pre['repair_manifest'], 'repair_manifest_sha256': pre['repair_manifest_sha256'],
           'repair_verify_file': pre['verify_file'], 'repair_verify_sha256': pre['verify_sha256'],
           'historical_failure_and_repair_evidence': {p: sha(HERE / p) for p in history_names},
           'immutable_baselines': immutable, 'runtime': runs, 'visual_review_sha256': sha(reviewdir / 'review.json'),
           'scope_sha256': sha(HERE / 'scope_incremental_final_20261029.json'),
           'unity_release_sha256': sha(HERE / 'unity_release_final_20261029.json'),
           'media_timing_sha256': sha(HERE / 'gif_quantization_fix_20261029.json'), 'all_production_fingerprints': files}
save(HERE / 'final_version_binding_20261029.json', binding)
save(HERE / 'final_validation_20261029.json', {
    'observed_at': now(), 'name': NAME, 'status': 'completed_pending_user_art_review', 'user_approved': False,
    'art_revision': pre['art_revision'], 'asset_revision': pre['asset_revision'], 'passes': 168, 'failures': 0,
    'actual_frames': runtime['actual_frames'], 'runtime': runtime['runtime'], 'scope_pass': scope['pass'],
    'scope_added': scope['added'], 'scope_deleted': scope['deleted'], 'scope_changes': len(scope['changes']),
    'scope_unexpected': scope['unexpected'], 'original_semantics_pass': scope['prefab_semantic']['pass'],
    'original_semantics_difference': scope['prefab_semantic']['unexpected'],
    'precise_head_binding_repair_pass': scope['head_binding_repair']['pass'],
    'prefab_semantic_scoped_pass': scope['prefab_semantic_scoped_pass'],
    'production_fingerprints_match_preplay': True, 'bound_production_paths': len(bound(files)),
    'no_Unity_CSharp_changed': True, 'historical_global_scope': 'Not reclassified or claimed PASS',
    'visual_review': (reviewdir / 'review.json').relative_to(ROOT).as_posix(),
    'version_binding': (HERE / 'final_version_binding_20261029.json').relative_to(ROOT).as_posix(),
    'Unity_release': (HERE / 'unity_release_final_20261029.json').relative_to(ROOT).as_posix(),
    'source_collection_limit': 'Installed Verify includes collectors; live import, dependencies and native clips checked. No release build/deployment.'})
print(json.dumps({'scope_pass': scope['pass'], 'generic_semantics_pass': scope['prefab_semantic']['pass'],
                  'precise_binding_repair_pass': scope['head_binding_repair']['pass'],
                  'before': scope['before_count'], 'after': scope['after_count'], 'changes': len(scope['changes']),
                  'added': scope['added'], 'deleted': scope['deleted'], 'unexpected': len(scope['unexpected']),
                  'bound': len(bound(files)), 'positions': len(sources), 'unique_pngs': unique_png,
                  'gif_samples': len(samples), 'ready_for_record': True}, ensure_ascii=False))
