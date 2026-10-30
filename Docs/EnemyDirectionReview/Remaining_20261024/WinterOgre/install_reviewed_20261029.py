"""Install only the actually viewed final WinterOgre stage and bind pre-Play evidence."""
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from session_winterogre import D, H, ROOT, NAME, owner, read, write, sha, now, stage, run, snapshot, Client, probe, idle

owner()
assert not (D / 'installed_manifest.json').exists()
resume_import = sys.argv[1:] == ['--resume-after-import-adapter']
assert not sys.argv[1:] or resume_import
baseline = read(D / 'incremental_before_20261029.json')
expected = dict(baseline['files'])
for x in read(D / 'scope_incremental_blocked_20261029_143535.json')['changes']:
    expected[x['path']] = x['after']
assert snapshot() == expected, 'Production drift since preflight'
art = D / 'staged_art'
spec = read(art / (NAME + '_Directions.sprites.json'))
layout = read(art / (NAME + '_Directions.layout.json'))
assert len(spec['sprites']) == 14
assert layout['anatomy'] == {'legs': 2, 'wings': 0, 'claws': 0, 'tails': 0, 'arms': 2, 'feelers': 0}
assert read(D / 'edge_cleanup_manifest_20261029.json')['total_part_pixels'] == 224
offline_review = {
    'reviewed_at': now(), 'revision': 'art_r01', 'offline_visual_pass': True,
    'viewed': {p: sha(D / p) for p in ['parts_clean.png', 'offline_rig_proof.png', 'offline_Up.png', 'offline_Down.png']},
    'raw_up': 'generation/Up/revision_05/raw.png', 'raw_down': 'generation/Down/raw.png',
    'stage_files': {p.name: sha(p) for p in art.iterdir() if p.is_file()},
    'observations': 'Actual final standalone800px Up/Down inspected: solid neck/shoulder/hip connections, bald face-free rear, smooth heels; front amber eyes/teeth/square buckle and toe divisions. Both empty fists have matching large fur-rimmed cuffs. Lowered shoulder pivots eliminate extra nubs; short legs match stocky source. No ground shadow.224 residual magenta edge RGB pixels replaced without alpha or shape changes; originals and pre-clean stage retained.',
    'initial_layout': 'offline_initial_layout_20261029 retained with observed excessive shoulder protrusion and long legs.',
    'limitations': 'Offline proof only; motion, hit/death and reuse require actual Play checks.'
}
if resume_import:
    previous = read(D / 'offline_review_final_20261029.json')
    assert previous['stage_files'] == offline_review['stage_files']
    assert previous['viewed'] == offline_review['viewed']
else:
    write(D / 'offline_review_final_20261029.json', offline_review, fresh=True)
c = Client()
project = c.identity()
errors = c.tool('read_console', {'action': 'get', 'types': ['error'], 'count': '50', 'format': 'json'})
live = probe(c)
idle(live)
write(D / ('preinstall_idle_after_import_adapter_20261029.json' if resume_import else 'preinstall_idle_20261029.json'), {'observed_at': now(), 'project': project, 'errors': errors,
      'live': live, 'protocol_history': c.history, 'cleared_console': False}, fresh=True)
run('install_character.py', NAME)
manifest = read(D / 'installed_manifest.json')
assert manifest['verification']['data']['result']['pass']
target = next(x for x in read(H / 'local_baseline.json')['targets'] if x['name'] == NAME)
current = snapshot()
final_paths = [target['battle'], target['battle'] + '.meta']
final_paths += [p.relative_to(ROOT).as_posix() for p in (ROOT / target['art_dir']).rglob('*') if p.is_file()]
assert all(current[p] == fingerprint for p, fingerprint in baseline['protected_six'].items() if p != target['battle'])
assert all(sha(art / (NAME + '_Directions' + suffix)) == current[target['art_dir'] + '/' + NAME + '_Directions' + suffix]
           for suffix in ['.png', '.sprites.json', '.layout.json'])
for change in manifest['changes']:
    assert current[change['path']] == change['after']
write(D / 'production_before_play_20261029.json', {
    'observed_at': now(), 'revision': 'art_r01', 'manifest_sha256': sha(D / 'installed_manifest.json'),
    'final_files': {p: current[p] for p in final_paths},
    'source_and_meta_protection': True, 'stage_files_match': True,
    'no_shared_CSharp_changes': not any(p.endswith('.cs') and baseline['files'].get(p) != v for p, v in current.items())
}, fresh=True)
stage('WinterOgre_final_art_r01_installed_Verify_pass_runtime_pending', D / 'production_before_play_20261029.json')
print(json.dumps({'installed': True, 'verify': True, 'production_files_bound': len(final_paths), 'changes': len(manifest['changes'])}))
