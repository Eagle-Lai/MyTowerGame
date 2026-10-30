from session_current import *
import subprocess, shutil

owner()
assert not (HERE/'gif_archive_verification_20261030.json').exists()
final = read(HERE/'final_validation_20261030.json')
assert final['passes'] == 168 and final['failures'] == 0 and final['scope_pass'] and final['original_semantics_pass']
binding = read(HERE/'final_version_binding_20261030.json')
assert snapshot() == binding['all_production_fingerprints']
progress = read(RUN/'progress.json')
assert progress['completed_count'] == 107
item = next(r for r in progress['items'] if r['name'] == NAME)
assert not item.get('user_approved')
backup = HERE/'docs_before_final_record_20261030'
backup.mkdir(exist_ok=False)
shutil.copy2(RUN/'progress.json', backup/'progress.json')
shutil.copy2(HERE/'runtime_summary.json', backup/'runtime_summary.json')
for n in ['manifest.json', 'README.md', 'index.html']:
    shutil.copy2(RUN.parent/'AllGIF'/n, backup/n)
assert sha(backup/'manifest.json') == sha(HERE/'allgif_manifest_before_20261030.json')
note = (HERE/'record_note_utf8.txt').read_text(encoding='utf-8').strip()
assert 'PossessedWarg79' in note and '681' in note and '458' in note and '用户美术' in note and '?' not in note
assert read(HERE/'visual_review_final_20261030/review.json')['note'] == note
subprocess.run([sys.executable, str(RUN/'character_step.py'), 'record', NAME, note], check=True)
owner()
manifest = read(RUN.parent/'AllGIF/manifest.json')
old = read(backup/'manifest.json')
assert {(r['source'], r['sha256']) for r in old['files']} <= {(r['source'], r['sha256']) for r in manifest['files']}
for r in old['files']:
    assert sha(RUN.parent/r['source']) == sha(RUN.parent/'AllGIF'/r['file']) == r['sha256']
sources = {p.relative_to(RUN.parent).as_posix(): p for p in HERE.rglob('*.gif')}
entries = [r for r in manifest['files'] if r['source'].startswith('Remaining_20261024/'+NAME+'/')]
assert len(sources) == len(entries) == 16 and set(sources) == {r['source'] for r in entries}
assert old['count'] == 1744 and manifest['count'] == old['count']+len(entries) == 1760
verified = []
for r in entries:
    assert sha(sources[r['source']]) == sha(RUN.parent/'AllGIF'/r['file']) == r['sha256']
    verified.append({**r, 'source_copy_sha256_match': True})
final_gifs = sum(r['status'] == '当前审核版本' for r in entries)
historical_gifs = len(entries)-final_gifs
assert final_gifs == 12 and historical_gifs == len(list((HERE/'media_before_gif_quantization_fix_20261030').rglob('*.gif'))) == 4
save(HERE/'gif_archive_verification_20261030.json', {'observed_at': now(), 'before': old['count'], 'after': manifest['count'],
    'current_character_sources': len(sources), 'final': final_gifs, 'historical_timing_originals': historical_gifs,
    'all_old_source_hashes_retained': True, 'old_sources_and_copies_verified': len(old['files']),
    'all_current_source_copy_matches': True, 'entries': verified, 'user_approved': False})
progress = read(RUN/'progress.json')
item = next(r for r in progress['items'] if r['name'] == NAME)
assert progress['completed_count'] == 108 and item['status'] == 'completed_pending_user_art_review' and item['visual_note'] == note
rel = lambda p: p.relative_to(ROOT).as_posix()
item.update(current_stage='recorded_pending_user_art_review', completed_at=now(), production_modified=True,
    staging=final['art_revision'], install_verify='PASS', record='completed', new_gifs=len(entries), final_gifs=final_gifs, historical_gifs=historical_gifs,
    scope_record=rel(HERE/'scope_incremental_final_20261030.json'), unity_release=rel(HERE/'unity_release_final_20261030.json'),
    final_validation=rel(HERE/'final_validation_20261030.json'), version_binding=rel(HERE/'final_version_binding_20261030.json'),
    visual_review=rel(HERE/'visual_review_final_20261030/review.json'), gif_archive=rel(HERE/'gif_archive_verification_20261030.json'),
    resume_status='bounded_Down_revision_01_succeeded_recorded', user_approved=False,
    historical_block_resolution={'resolved_at': now(), 'old_block_fields_are_historical': True,
        'method': 'Current owner executed exactly one authorized new Down revision_01 request; HTTP200 raw preserved, local art repaired and verified, two actual Play rounds and visual review completed.',
        'old_down_outcome': 'unknown', 'old_down_possible_charge': 'unknown', 'new_down_billing_independently_verified': False,
        'accounting_file': rel(HERE/'generation_final_accounting_20261030.json')})
assert all(r['status'] == 'completed_pending_user_art_review' and r.get('user_approved') is False for r in progress['items'])
progress.update(current=None, remaining_count=0, updated_at=now(), last_completed_character=NAME,
                status='completed_pending_user_art_review')
(RUN/'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
runtime = read(HERE/'runtime_summary.json')
runtime.update(status='runtime_complete_visual_reviewed_pending_user_art_review', visual_review=rel(HERE/'visual_review_final_20261030/review.json'), user_approved=False)
(HERE/'runtime_summary.json').write_text(json.dumps(runtime, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
final.update(status='completed_pending_user_art_review', record_completed=True, completed_count=108, authorized_count=108,
    gif_archive_count=manifest['count'], character_gifs=len(entries), final_gifs=final_gifs, historical_gifs=historical_gifs,
    gif_archive_verification_sha256=sha(HERE/'gif_archive_verification_20261030.json'), progress_sha256_after_record=sha(RUN/'progress.json'),
    runtime_summary_sha256_after_record=sha(HERE/'runtime_summary.json'))
(HERE/'final_validation_20261030.json').write_text(json.dumps(final, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'completed': 108, 'authorized': 108, 'remaining': 0, 'allGIF_before': old['count'], 'allGIF_after': manifest['count'],
    'character_gifs': len(entries), 'final': final_gifs, 'history': historical_gifs, 'old_sources_and_copies_verified': len(old['files']),
    'all_sha_match': True, 'user_approved': False, 'next': None}, ensure_ascii=False))
