from session_current import *
from collections import Counter

owner()
resolve = '--resolve-historical-installs' in sys.argv
out = HERE/('queue_completion_audit_resolved_20261030.json' if resolve else 'queue_completion_audit_20261030.json')
assert not out.exists()
progress = read(RUN/'progress.json')
manifest = read(RUN.parent/'AllGIF/manifest.json')
by_source = {r['source']: r for r in manifest['files']}
rows, issues = [], []
install_shapes = Counter()
previous = read(HERE/'queue_completion_audit_20261030.json') if resolve else None
if previous:
    assert previous['progress_sha256'] == sha(RUN/'progress.json')
    assert previous['allgif_manifest_sha256'] == sha(RUN.parent/'AllGIF/manifest.json')
    assert snapshot() == read(HERE/'final_version_binding_20261030.json')['all_production_fingerprints']
effective_installs = {'DreadEye': 'repair_01', 'Horse': 'repair_controller_r01', 'Pony': 'repair_controller_r01', 'PirateBoar': 'repair_shot_r01'} if resolve else {}

def installed_result(value):
    if 'structuredContent' in value:
        value = value['structuredContent']
    elif 'content' in value:
        value = json.loads(value['content'][0]['text'])
    if 'data' in value:
        value = value['data'].get('result', value['data'])
    return json.loads(value) if isinstance(value, str) else value

for item in sorted(progress['items'], key=lambda r: r['index']):
    if previous:
        old = next(r for r in previous['items'] if r['name'] == item['name'])
        if not old['issues']:
            rows.append({**old, 'audit_source': 'Unchanged valid item from queue_completion_audit_20261030.json; progress and archive identity rechecked.'})
            continue
    folder = RUN/item['name']
    row = {'index': item['index'], 'name': item['name'], 'status': item['status'], 'user_approved': item.get('user_approved'), 'issues': [], 'runtime': []}
    try:
        assert item['status'] == 'completed_pending_user_art_review' and item['user_approved'] is False
        assert item['visual_reviewed'] and item['visual_note'].strip() and '\ufffd' not in item['visual_note']
        row['visual_note_sha256'] = hashlib.sha256(item['visual_note'].encode('utf-8')).hexdigest().upper()
        initial = read(folder/'installed_manifest.json')
        revision = effective_installs.get(item['name'])
        install_path = folder/revision/'manifest.json' if revision else folder/'installed_manifest.json'
        verify_path = folder/revision/'verify.txt' if revision else folder/'installed_verify.txt'
        installed = read(install_path)
        install_shapes[str(sorted(installed))] += 1
        verification = installed_result(installed['verification'])
        assert verification['pass'] and 'FAIL ' not in verification['report']
        row['installed_manifest_sha256'] = sha(install_path)
        row['installed_verify_sha256'] = sha(verify_path)
        row['effective_install_manifest'] = install_path.relative_to(RUN).as_posix()
        assert 'FAIL ' not in verify_path.read_text(encoding='utf-8')
        if revision:
            row['historical_failure_preserved'] = {'original_manifest_sha256': sha(folder/'installed_manifest.json'),
                'original_verify_sha256': sha(folder/'installed_verify.txt'), 'original_verification_pass': installed_result(initial['verification'])['pass'],
                'resolved_by': revision, 'repair_reason': installed.get('reason', 'See existing repair manifest and actual selected runtime evidence.'),
                'interpretation': 'Initial failed install remains immutable history. Existing later successful repair and selected actual runs form the effective completion evidence. No production or historical item rewritten by this audit.'}
            assert not row['historical_failure_preserved']['original_verification_pass']
        summary = read(folder/'runtime_summary.json')
        assert summary['passes'] == 168 and summary['failures'] == 0
        assert summary['name'] == item['name'] and len(item['runtime']) == 2
        for r in item['runtime']:
            revision = folder/r['revision']
            records = [json.loads(line) for line in (revision/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if line]
            checks = (revision/'actual_runtime_checks.txt').read_text(encoding='utf-8')
            assert r['pass'] == 84 and r['fail'] == 0
            assert sha(revision/'actual_frames.jsonl') == r['records_sha256'] and len(records) == r['frames']
            assert 'FAIL ' not in checks and sum(line.startswith('PASS ') for line in checks.splitlines()) == 84
            assert any(s['revision'] == r['revision'] and s['records_sha256'] == r['records_sha256'] and s['frames'] == r['frames'] for s in summary['runtime'])
            assert len({v['file'] for v in records}) == len(records)
            assert all(b['frame'] > a['frame'] and b['realtime'] >= a['realtime'] for a, b in zip(records, records[1:]))
            pngs = {}
            for frame in records:
                p = revision/frame['file']
                assert p.is_file() and p.stat().st_size > 8, p
                with p.open('rb') as f:
                    assert f.read(8) == b'\x89PNG\r\n\x1a\n', p
                pngs[frame['file']] = sha(p)
            media = []
            for gif in sorted(revision.glob('*.gif')):
                source = gif.relative_to(RUN.parent).as_posix()
                entry = by_source[source]
                assert entry['status'] == '当前审核版本' and sha(gif) == entry['sha256']
                assert sha(RUN.parent/'AllGIF'/entry['file']) == entry['sha256']
                media.append(entry)
            assert len(media) == 6
            assert (revision/'four_directions.png').is_file() and (folder/'runtime_visual_strip.png').is_file()
            row['runtime'].append({**r, 'records_sha256_verified': True, 'checks_sha256': sha(revision/'actual_runtime_checks.txt'),
                'actual_png_sha256': pngs, 'final_gifs': media, 'media_manifest_sha256': sha(revision/'media_manifest.json')})
        assert sum(r['frames'] for r in row['runtime']) == item['actual_frames'] == summary['actual_frames']
        row['actual_frames'] = item['actual_frames']
        row['runtime_summary_sha256'] = sha(folder/'runtime_summary.json')
    except Exception as error:
        import traceback
        row['issues'].append(traceback.format_exc())
    if row['issues']:
        issues.append({'name': item['name'], 'issues': row['issues']})
    rows.append(row)

assert len(rows) == 108 and len({r['name'] for r in rows}) == 108
report = {'observed_at': now(), 'progress_sha256': sha(RUN/'progress.json'), 'allgif_manifest_sha256': sha(RUN.parent/'AllGIF/manifest.json'),
    'authorized_count': progress['authorized_count'], 'completed_count': progress['completed_count'], 'current': progress['current'],
    'remaining_count': sum(r['status'] != 'completed_pending_user_art_review' for r in rows), 'user_approved_in_continuation_queue': sum(bool(r['user_approved']) for r in rows),
    'historical_completed_runs_checked': sum(len(r['runtime']) for r in rows), 'selected_actual_png_files_hashed': sum(len(a['actual_png_sha256']) for r in rows for a in r['runtime']),
    'selected_final_gifs_verified': sum(len(a['final_gifs']) for r in rows for a in r['runtime']), 'install_manifest_shapes': dict(install_shapes),
    'issues': issues, 'pass': not issues and progress['completed_count'] == 108 and progress['current'] is None,
    'prior_audit_sha256': sha(HERE/'queue_completion_audit_20261030.json') if previous else None,
    'resolved_historical_install_references': effective_installs,
    'interpretation': 'Read and hash-verified each of 108 effective recorded completion items: installation Verify, two selected actual runtime logs and records, every selected raw PNG file, visual note and 12 final source/archive GIFs. This is an evidence audit, not a new runtime or visual re-review of the other 107 characters. Earlier global scope failures, rejected revisions and user approval boundaries remain unchanged.',
    'items': rows}
save(out, report)
print(json.dumps({k: v for k, v in report.items() if k not in ['items', 'install_manifest_shapes']}, ensure_ascii=False))
assert report['pass'], issues
