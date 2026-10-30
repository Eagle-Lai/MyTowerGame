"""One-shot final binding and record for the actually reviewed RoyalBoar install."""
import re
import subprocess
from serial_common import *

owner()
assert not (D / 'final_validation_20261026.json').exists(), 'Inspect existing finalization before retry'
note = (D / 'record_note_utf8.txt').read_text(encoding='utf-8-sig').strip()
assert note
digest = lambda p: sha(p) if p.is_file() else None
baseline = read(D / 'incremental_before_20261026.json')
base = baseline['files']
assert len(base) == 5118 and len(baseline['protected_royalboar']) == 6
current = {p.relative_to(ROOT).as_posix(): p
           for folder in ['Assets', 'Packages', 'ProjectSettings', 'Luban']
           for p in (ROOT / folder).rglob('*') if p.is_file()}
changes = [{'path': p, 'before': s, 'after': digest(ROOT / p)}
           for p, s in base.items() if digest(ROOT / p) != s]
allowed_prefix = 'Assets/_UIAssets/Monsters/Pigs/RoyalBoar/Directions/'
unexpected = []
reporter_side_effects = []
for change in changes:
    path = change['path']
    if path == 'Assets/Prefabs/Enemy/Enemy_RoyalBoar.prefab':
        continue
    if (path == 'Assets/StreamingAssets/build_info'
        and digest(ROOT / 'Assets/Reporter/Editor/ReporterEditor.cs') == base.get('Assets/Reporter/Editor/ReporterEditor.cs')
        and re.fullmatch(r'Build from .+ at .+', (ROOT / path).read_text(encoding='utf-8'))):
        reporter_side_effects.append(dict(change, origin='Unmodified ReporterEditor writes build timestamp on entering Play'))
    else:
        unexpected.append(change)
assert not unexpected, unexpected
added = [{'path': p, 'sha256': digest(current[p])} for p in sorted(set(current) - set(base))]
unexpected_added = [x for x in added if not (
    x['path'].startswith(allowed_prefix) or x['path'] == 'Assets/_UIAssets/Monsters/Pigs/RoyalBoar/Directions.meta')]
assert not unexpected_added, unexpected_added
for path, expected in baseline['protected_royalboar'].items():
    if path != 'Assets/Prefabs/Enemy/Enemy_RoyalBoar.prefab':
        assert digest(ROOT / path) == expected, path

manifest = read(D / 'installed_manifest.json')
drift = [x['path'] for x in manifest['changes'] if digest(ROOT / x['path']) != x['after']]
assert not drift, drift
runtime = read(D / 'runtime_summary.json')
assert (runtime['passes'], runtime['failures'], runtime['actual_frames']) == (168, 0, 681)
sources = read(D / 'visual_review_serial_full_20261026' / 'sources.json')['sources']
sampling = dict(sheets=len({x['sheet'] for x in sources}), sample_slots=len(sources),
                unique_actual_frames=len({(x['revision'], x['source']) for x in sources}),
                method='Chronological full-body actual PNG samples; GIFs not played; not all frames individually viewed',
                extra_original_size_views=['runtime_r01/frames/UpWalk_00006.png', 'runtime_r01/frames/DownWalk_00029.png'])
assert (sampling['sheets'], sampling['sample_slots'], sampling['unique_actual_frames']) == (10, 256, 237), sampling
frames = {}
record_rows = {}
for item in runtime['runtime']:
    rev = item['revision']
    records = D / rev / 'actual_frames.jsonl'
    assert digest(records) == item['records_sha256'], rev
    rows = [json.loads(line) for line in records.read_text(encoding='utf-8').splitlines() if line]
    assert len(rows) == item['frames']
    assert len({row['file'] for row in rows}) == len(rows)
    frames[rev] = {row['file']: digest(D / rev / row['file']) for row in rows}
    assert all(frames[rev].values())
    record_rows[rev] = {row['file']: row for row in rows}
for sample in sources:
    assert record_rows[sample['revision']][sample['source']]['frame'] == sample['frame'], sample
report = available(Client())
assert report['errors']['success'] and report['errors']['data'] == [], report['errors']
assert report['probe']['scene'] == 'Assets/Scenes/Boot.unity'
write(D / 'finalize_preflight_20261026.json', report)
binding = dict(observed_at=now(), final_manifest='installed_manifest.json',
               manifest_sha256=digest(D / 'installed_manifest.json'),
               runtime_summary_sha256=digest(D / 'runtime_summary.json'),
               raw_sources={str(p.relative_to(D)): digest(p) for p in (D / 'generation').rglob('*') if p.is_file()},
               art_selection_sha256=digest(D / 'art_selection.json'),
               layout_adjustments_sha256=digest(D / 'layout_adjustments.json'),
               raster_retouch_sha256=digest(D / 'raster_retouch.json'),
               selected_sources={direction: {'path': path, 'sha256': digest(D / path)}
                                 for direction, path in read(D / 'art_selection.json').items() if direction in ['Up', 'Down']},
               staged={p.name: digest(p) for p in (D / 'staged_art').iterdir() if p.is_file()},
               actual_png_sha256=frames, review_sampling=sampling,
               added_files=added, unexpected_added=unexpected_added)
write(D / 'version_binding_final_20261026.json', binding)
subprocess.run([sys.executable, str(H / 'finalize_serial_character.py'), NAME,
                'installed_manifest.json', 'visual_review_serial_full_20261026'], check=True)
scope = read(D / 'scope_incremental_20261026.json')
scope.update(added_files=added, unexpected_added=unexpected_added)
write(D / 'scope_incremental_20261026.json', scope)
validation = read(D / 'final_validation_20261026.json')
errors = unwrap(validation['errors'])
assert errors['success'] and errors['data'] == [], errors
progress = read(H / 'progress.json')
item = next(x for x in progress['items'] if x['name'] == NAME)
assert item['status'] == 'completed_pending_user_art_review' and item['user_approved'] is False
assert note == item['visual_note'] and progress['completed_count'] == 79
print(json.dumps(dict(completed_count=progress['completed_count'], added_files=len(added),
                      sampling=sampling, frames=runtime['actual_frames'], console_errors=0), ensure_ascii=False))
