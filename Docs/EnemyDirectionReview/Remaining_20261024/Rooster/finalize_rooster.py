from pathlib import Path
from datetime import datetime
import hashlib, json, re, subprocess, sys
from serial_common import *

owner()
note = (D / 'record_note_utf8.txt').read_text(encoding='utf-8-sig').strip()
if not note:
    raise ValueError('Actual visual observations required')
output = D / 'final_validation_20261026.json'
if output.exists():
    raise ValueError('Final evidence exists; inspect before retrying')

digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
baseline = read(D / 'incremental_before_20261026.json')
base = baseline['files']
current = {p.relative_to(ROOT).as_posix(): p
           for folder in ['Assets', 'Packages', 'ProjectSettings', 'Luban']
           for p in (ROOT / folder).rglob('*') if p.is_file()}
changes = [{'path': p, 'before': s, 'after': digest(ROOT / p)}
           for p, s in base.items() if digest(ROOT / p) != s]
allowed_prefix = 'Assets/_UIAssets/Monsters/Birds/Rooster/Directions/'
unexpected = []
reporter_side_effects = []
for change in changes:
    path = change['path']
    if path == 'Assets/Prefabs/Enemy/Enemy_Rooster.prefab':
        continue
    if path == 'Assets/StreamingAssets/build_info' and digest(ROOT / 'Assets/Reporter/Editor/ReporterEditor.cs') == base.get('Assets/Reporter/Editor/ReporterEditor.cs') and re.fullmatch(r'Build from .+ at .+', (ROOT / path).read_text(encoding='utf-8')):
        reporter_side_effects.append(dict(change, origin='Unmodified ReporterEditor writes build timestamp on entering Play'))
    else:
        unexpected.append(change)
if unexpected:
    raise ValueError('Unexpected incremental changes: ' + str(unexpected))

added = [{'path': p, 'sha256': digest(current[p])} for p in sorted(set(current) - set(base))]
unexpected_added = [x for x in added if not (x['path'].startswith(allowed_prefix) or x['path'] == 'Assets/_UIAssets/Monsters/Birds/Rooster/Directions.meta')]
if unexpected_added:
    raise ValueError('Unexpected added production files: ' + str(unexpected_added))
protected = baseline['protected_rooster']
for path, expected in protected.items():
    if path != 'Assets/Prefabs/Enemy/Enemy_Rooster.prefab' and digest(ROOT / path) != expected:
        raise ValueError('Protected file drift: ' + path)

manifest = read(D / 'installed_manifest.json')
drift = [x['path'] for x in manifest['changes'] if digest(ROOT / x['path']) != x['after']]
if drift:
    raise ValueError('Final installed assets changed: ' + str(drift))
runtime = read(D / 'runtime_summary.json')
if runtime['passes'] != 168 or runtime['failures'] != 0 or runtime['actual_frames'] != 681:
    raise ValueError('Unexpected runtime summary: ' + str(runtime))
sources = read(D / 'visual_review_serial_full_20261026' / 'sources.json')['sources']
sampling = {'sheets': 10, 'sample_slots': len(sources), 'unique_actual_frames': len({(x['revision'], x['source']) for x in sources}), 'method': 'Chronological full-body actual PNG samples; GIFs not played; not all frames individually viewed'}
if sampling['sample_slots'] != 256 or sampling['unique_actual_frames'] != 231:
    raise ValueError('Unexpected review sampling: ' + str(sampling))
frames = {}
for item in runtime['runtime']:
    rev = item['revision']
    records = D / rev / 'actual_frames.jsonl'
    if digest(records) != item['records_sha256']:
        raise ValueError('Runtime records hash mismatch: ' + rev)
    rows = [json.loads(line) for line in records.read_text(encoding='utf-8').splitlines() if line]
    if len(rows) != item['frames']:
        raise ValueError('Runtime frame count mismatch: ' + rev)
    frames[rev] = {row['file']: digest(D / rev / row['file']) for row in rows}
binding = dict(observed_at=now(), final_manifest='installed_manifest.json', manifest_sha256=digest(D / 'installed_manifest.json'), runtime_summary_sha256=digest(D / 'runtime_summary.json'), raw_sources={str(p.relative_to(D)): digest(p) for p in (D / 'generation').rglob('*') if p.is_file()}, staged={p.name: digest(p) for p in (D / 'staged_art').iterdir() if p.is_file()}, actual_png_sha256=frames, review_sampling=sampling, added_files=added, unexpected_added=unexpected_added)
write(D / 'version_binding_final_20261026.json', binding)
subprocess.run([sys.executable, str(H / 'finalize_serial_character.py'), 'Rooster', 'installed_manifest.json', 'visual_review_serial_full_20261026'], check=True)
scope = read(D / 'scope_incremental_20261026.json')
scope.update(added_files=added, unexpected_added=unexpected_added)
write(D / 'scope_incremental_20261026.json', scope)
validation = read(D / 'final_validation_20261026.json')
errors = unwrap(validation['errors'])
if not errors.get('success') or errors.get('data') != []:
    raise ValueError('Unity console errors: ' + str(errors))
progress = read(H / 'progress.json')
item = next(x for x in progress['items'] if x['name'] == 'Rooster')
if item['status'] != 'completed_pending_user_art_review' or item['user_approved'] is not False:
    raise ValueError('Progress state mismatch')
if note != item['visual_note']:
    raise ValueError('Progress visual note mismatch')
print(json.dumps({'completed_count': progress['completed_count'], 'new_files': len(added), 'sampling': sampling, 'frames': runtime['actual_frames'], 'console_errors': 0}, ensure_ascii=False))
