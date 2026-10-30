from session_current import *
from PIL import Image

owner()
assert not (HERE/'final_validation_20261030.json').exists()
save_new = save
def save(p, obj):
    if Path(p).exists():
        previous = read(p)
        assert {k:v for k,v in previous.items() if k != 'observed_at'} == {k:v for k,v in obj.items() if k != 'observed_at'}, p
    else:
        save_new(p, obj)
reviewdir = HERE/'visual_review_final_20261030'
files = snapshot()
scope = audit(files)
save(HERE/'scope_incremental_final_20261030.json', scope)
assert scope['pass'], scope
pre = read(HERE/'preplay_version_binding_20261030.json')
assert pre['production_fingerprints'] == bound(files)
assert pre['staged_fingerprints'] == {p.relative_to(HERE/'staged_art').as_posix(): sha(p) for p in (HERE/'staged_art').rglob('*') if p.is_file()}
for key, file in [('manifest_sha256', 'installed_manifest.json'), ('verify_sha256', 'installed_verify.txt'), ('nativeattack_verify_sha256', 'installed_verify_nativeattack01_20261030.json')]:
    assert pre[key] == sha(HERE/file), file
assert read(HERE/'installed_verify_nativeattack01_20261030.json')['pass']
sync = read(HERE/'sync_start_20261030.json')
old_evidence = {p: {'expected': s, 'actual': sha(HERE/p), 'matches': sha(HERE/p) == s} for p, s in sync['old_evidence'].items()}
assert len(old_evidence) == 21 and all(r['matches'] for r in old_evidence.values())
runtime = read(HERE/'runtime_summary.json')
assert runtime['passes'] == 168 and runtime['failures'] == 0
runs = []
for run in runtime['runtime']:
    folder = HERE/run['revision']
    records = [json.loads(line) for line in (folder/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if line]
    checks = (folder/'actual_runtime_checks.txt').read_text(encoding='utf-8')
    assert run['records_sha256'] == sha(folder/'actual_frames.jsonl') and len(records) == run['frames']
    assert 'FAIL ' not in checks and sum(line.startswith('PASS ') for line in checks.splitlines()) == 84
    actual = {r['file']: sha(folder/r['file']) for r in records}
    assert len(actual) == len(records)
    assert all(b['frame'] > a['frame'] and b['realtime'] >= a['realtime'] for a, b in zip(records, records[1:]))
    returned = read(HERE/(run['revision']+'_returned.json'))
    assert returned['state'] == {'playing': False, 'review': False, 'scene': 'Assets/Scenes/Boot.unity', 'dirty': False}
    runs.append({**run, 'records_sha256_verified': True, 'actual_png_sha256': actual,
                 'checks_sha256': sha(folder/'actual_runtime_checks.txt'), 'media_manifest_sha256': sha(folder/'media_manifest.json'),
                 'media': {p.name: sha(p) for p in folder.glob('*.gif')}, 'returned_to_Boot': returned})
assert sum(r['frames'] for r in runs) == runtime['actual_frames'] == 681
sources = read(reviewdir/'sources.json')['sources']
samples = read(reviewdir/'gif_samples.json')['samples']
assert all(sha(HERE/r['revision']/r['source']) == r['source_sha256'] for r in sources)
assert all(sha(HERE/r['revision']/r['gif']) == r['gif_sha256'] and sha(reviewdir/r['output']) == r['output_sha256'] for r in samples)
continuous = read(reviewdir/'continuous_gifs/manifest.json')['files']
assert len(continuous) == 12 and sum(r['encoded_frames'] for r in continuous) == 458
for r in continuous:
    assert r['gif_sha256'] == sha(HERE/r['revision']/r['gif'])
    assert all(p['sha256'] == sha(reviewdir/'continuous_gifs'/p['file']) for p in r['pages'])
boards = [p for p in reviewdir.glob('*.png') if 'sequence_' in p.name or 'native_walk_cycles' in p.name or p.name.endswith('_gif_samples.png')]
assert len(boards) == 14
unique_png = len({(r['revision'], r['source']) for r in sources})
assert len(sources) == 312 and unique_png == 301
note = f'''PossessedWarg79最终版本{pre['art_revision']}：复用旧Up HTTP200原图，并使用本次唯一有界Down revision_01 HTTP200原图，分别经本地02像素修补、alpha01和layout03制作；原始返回图及所有修前材料保留，本地修图不冒充AI返回。实际查看自身atlas/source、最终离线四向与14分件、两轮真实four_directions与runtime strip、14张时序/原生循环/GIF抽帧板（312采样位、301张不同真实PNG）、5张未裁原始PNG；再按顺序审阅12个最终GIF的全部458编码帧、22张连续板，未实时播放，也未逐张审完全部681张Unity原始PNG。保留深橄榄棕蓬毛、赭色斑、实际金色冠刺/背刺、琥珀眼、象牙獠牙、双耳、四犬腿及一条长尾。Up后脑无脸或前向耳垫，后跟无前趾线；Down正面三表情，原图躯干重复口吻已局部清除，远侧后足在轴向大多被遮挡。已审样本足尾根连接，步态/尾摆错相、原左右侧面、转向、攻击蓄力/发力与头事件、白闪消退、上下死亡旋转收缩淡出、同实例回收复用、暂停恢复与1x/2x/3x正常，未见地面影、矩形补色缝、品红或可见孔洞。死亡为逐renderer淡出，重叠部件仍可见，不声称一体alpha。自身Walk与Attack均0.5s，愤怒事件0.166666672s、发力0.333333343s，Death0.416666657s；上下攻击新增曲线按原生时序定点适配，源与原侧float/PPtr/事件/时长loop完整保留。Directions沿用现有六状态Speed/Attack/兼容Action生成策略，原controller未变，不声称派生controller与原过渡/状态速度完全相同。两轮真实Play各84PASS/0FAIL，共168PASS/0FAIL、681PNG。4个上下步行GIF按真实相位累计边界从480或490ms修为实测500ms，边界取整误差不超过5ms；修前4GIF和2manifest保留，双向GIF原500ms未重写。旧Down请求结果及可能费用永久unknown，本次Down成功费用未独立核账。用户美术尚未批准。'''
extras = ['runtime_r01_UpWalk_uncropped.png', 'runtime_r01_Attack_uncropped.png', 'runtime_r01_DeathAutoRecycle_uncropped.png', 'runtime_updeath_r01_DeathAutoRecycle_uncropped.png', 'runtime_updeath_r01_Reuse_uncropped.png']
review = {'observed_at': now(), 'art_revision': pre['art_revision'], 'result': 'accepted_for_record_pending_user_art_review', 'user_approved': False, 'note': note,
    'boards': {p.name: sha(p) for p in boards}, 'png_sample_positions': len(sources), 'unique_png_samples': unique_png,
    'distributed_gif_samples': len(samples), 'continuous_gif_frames_reviewed': 458, 'final_gifs_reviewed_in_encoding_order': 12,
    'continuous_boards_viewed': {p['file']: p['sha256'] for r in continuous for p in r['pages']},
    'continuous_manifest_sha256': sha(reviewdir/'continuous_gifs/manifest.json'),
    'additional_uncropped_viewed': {p: sha(reviewdir/p) for p in extras},
    'also_viewed': {p: sha(HERE/p) for p in ['offline_four_directions_final_20261030.png', 'parts_clean.png', 'staged_art/PossessedWarg_Directions.png', 'runtime_r01/four_directions.png', 'runtime_updeath_r01/four_directions.png', 'runtime_visual_strip.png']},
    'limitations': 'All final GIF encoded frames reviewed in static encoding order. No real-time playback. Chronological Unity PNG sampling, not all 681 PNGs individually inspected. Per-renderer overlapping fade, not a unified silhouette alpha. User art approval pending.'}
save(reviewdir/'review.json', review)
(HERE/'record_note_utf8.txt').write_text(note+'\n', encoding='utf-8')
release = read(HERE/'unity_release_final_20261030.json')
assert release['success']
ledger = []
for folder in [HERE/'generation/Up', HERE/'generation/Down', HERE/'generation/Down/revision_01']:
    row = {'folder': folder.relative_to(HERE).as_posix(), 'files': {p.name: sha(p) for p in folder.iterdir() if p.is_file()}}
    if (folder/'result.json').exists():
        result = read(folder/'result.json')
        row.update(http_status=result['status'], raw_bytes=(folder/'raw.png').stat().st_size, raw_sha256=sha(folder/'raw.png'))
        with Image.open(folder/'raw.png') as im:
            row.update(actual_format=im.format, actual_size=list(im.size), actual_mode=im.mode)
    else:
        row.update(outcome='unknown', possible_charge='unknown', request_sha256=sha(folder/'request.json'))
        assert not any((folder/n).exists() for n in ['raw.png', 'result.json', 'uncertain_result.json', 'provider_response.json'])
    ledger.append(row)
assert len(list((HERE/'generation/Down').rglob('request.json'))) == 2
assert len(list((HERE/'generation/Up').rglob('request.json'))) == 1
save(HERE/'generation_final_accounting_20261030.json', {'observed_at': now(), 'original_21_evidence': old_evidence,
    'requests': ledger, 'new_paid_production_requests_this_owner': 1, 'new_down_successful_requests': 1,
    'additional_up_requests': 0, 'network_recovery_branch_used': False, 'paid_diagnostics': 0,
    'billing_independently_verified': False, 'usage_notice': 'Down revision_01 result usage is a low-confidence local estimate, not a provider billing receipt.',
    'old_Down_outcome_and_possible_charge': 'unknown permanently; no invented ECONNRESET/unsent/uncharged claim',
    'authorization_sha256': sha(HERE/'authorized_resume_20261030.json'), 'generator_patch_sha256': sha(HERE/'generator_resume_patch_20261030.patch')})
immutable = {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in [RUN/'local_baseline.json', RUN/'production_fingerprints_before.json', RUN.parent/'Batch01_10/user_approval_20261023.json', RUN.parent/'PREFAB_CHANGES_SUMMARY_20261026.md']}
source_paths = {p: s for p, s in files.items() if p in sync['protected_six'] or p.startswith('Assets/_UIAssets/Monsters/_Common/Animations/Wolf/')}
binding = {'observed_at': now(), 'preplay_file': 'preplay_version_binding_20261030.json', 'preplay_sha256': sha(HERE/'preplay_version_binding_20261030.json'),
    'art_revision': pre['art_revision'], 'production_fingerprints': bound(files), 'preplay_production_matches': True, 'preplay_staged_matches': True,
    'staged_fingerprints': pre['staged_fingerprints'], 'source_and_animation_fingerprints': source_paths,
    'install_manifest_matches': True, 'install_verify_matches': True, 'immutable_documents': immutable, 'runtime': runs,
    'visual_review_sha256': sha(reviewdir/'review.json'), 'scope_sha256': sha(HERE/'scope_incremental_final_20261030.json'),
    'unity_release_sha256': sha(HERE/'unity_release_final_20261030.json'), 'media_timing_sha256': sha(HERE/'gif_quantization_fix_20261030.json'),
    'generation_accounting_sha256': sha(HERE/'generation_final_accounting_20261030.json'), 'all_production_fingerprints': files,
    'preexisting_drift': sync['prior_Zombie_drift']}
save(HERE/'final_version_binding_20261030.json', binding)
save(HERE/'final_validation_20261030.json', {'observed_at': now(), 'name': NAME, 'status': 'validated_ready_for_record_pending_user_art_review', 'user_approved': False,
    'art_revision': pre['art_revision'], 'passes': 168, 'failures': 0, 'actual_frames': 681, 'runtime': runtime['runtime'],
    'scope_pass': scope['pass'], 'scope_added': scope['added'], 'scope_deleted': scope['deleted'], 'scope_changes': len(scope['changes']), 'scope_unexpected': scope['unexpected'],
    'original_semantics_pass': scope['prefab_semantic']['pass'], 'production_fingerprints_match_preplay': True, 'bound_production_paths': len(bound(files)),
    'no_Unity_CSharp_changed': True, 'old_evidence_files_unchanged': 21, 'historical_global_scope': 'Not reclassified or claimed PASS; parent preexisting build_info drift separately retained.',
    'visual_review': (reviewdir/'review.json').relative_to(ROOT).as_posix(), 'version_binding': (HERE/'final_version_binding_20261030.json').relative_to(ROOT).as_posix(),
    'Unity_release': (HERE/'unity_release_final_20261030.json').relative_to(ROOT).as_posix(),
    'source_collection_limit': 'Own Verify includes collectors; actual import/dependencies/pivots/PPU/full source animation contracts checked. No build/deployment/device/long battle acceptance.'})
print(json.dumps({'scope_pass': scope['pass'], 'before': scope['before_count'], 'after': scope['after_count'], 'changes': len(scope['changes']), 'added': scope['added'], 'deleted': scope['deleted'], 'bound': len(bound(files)), 'actual_png': 681, 'gif_encoded_frames_reviewed': 458, 'ready_for_record': True}, ensure_ascii=False))
