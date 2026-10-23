"""Register the explicitly coordinated ten-role art handoff, without moving its baseline."""
from formal_tools import *
import datetime, shutil, sys

tag = sys.argv[1] if len(sys.argv) > 1 else 'ten-role-art-final'
assert tag and all(c.isalnum() or c in '-_' for c in tag)
owner = '01a163de-a875-7b71-8a76-0cde03d599b9'
art = ROOT / 'Docs/EnemyDirectionReview/Batch01_10'
def read(name): return json.loads((art / name).read_text(encoding='utf-8-sig'))
progress = read('progress.json')
assert progress['status'] == 'completed_pending_user_art_review'
assert len(progress['items']) == 10 and all(x['runtime_verified'] and x['visual_reviewed'] for x in progress['items'])
assert progress['approved_example_regression']['runtime_verified'] and progress['approved_example_regression']['visual_reviewed']
scope = read('scope_final.json')
assert scope['untouched_prefabs'] == 109
assert not scope['unexpected_prefab_changes'] and not scope['original_sources_or_GUID_drift'] and not scope['shared_animation_drift']
assert len(scope['prefab_semantics']) == 10 and all(x['pass'] for x in scope['prefab_semantics'].values())
assert read('handoff_boundary_audit.json')['frozen_inputs_unchanged']
baseline = read('local_baseline.json')
expected = {'Bat', 'BattlePanther', 'Bear', 'BearMounted', 'BlackBear', 'BlackBoar', 'BlackWolf', 'BlueScorpion', 'Boar', 'BoarMounted'}
assert {t['name'] for t in baseline['targets']} == expected
codes = {'Assets/Scripts/Enemy/EnemyDirectionalProfile.cs', 'Assets/Scripts/Enemy/EnemyDirectionalVisual.cs',
         'Assets/Editor/EnemyDirectionPrefabBuilder.cs', 'Assets/Editor/EnemyDirectionalRigBuilder.cs',
         'Assets/Editor/EnemyDirectionBatchReview.cs'}
prefabs = {t['battle'] for t in baseline['targets']}
directories = {t['art_dir'].rstrip('/') for t in baseline['targets']}
def allowed(path):
    return (path in codes or path.removesuffix('.meta') in codes or
            path in prefabs or path.removesuffix('.meta') in prefabs or
            any(path.startswith(d + '/') or path == d + '.meta' for d in directories))
manifest_source = art / 'implementation_manifest.json'
manifest = read(manifest_source.name)
freeze_source = art / 'final_frozen_fingerprints.json'
freeze = read(freeze_source.name)
for path, digest in freeze['files'].items():
    assert (ROOT/path).is_file() and hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest.lower(), path
protected = json.loads((REPORT/'audit/protected-files-before.json').read_text(encoding='utf-8'))
destination = REPORT/'audit/coordinated-code-snapshot'/tag
assert not destination.exists(), destination
current = REPORT/'audit/coordinated-external-changes.json'
previous = json.loads(current.read_text(encoding='utf-8'))
records = dict(previous['files'])
for e in records.values():
    e.setdefault('ownerFingerprintSource', previous['ownerFingerprintSource'])
    e.setdefault('ownerFingerprintSha256', previous['ownerFingerprintSha256'])
for entry in manifest['files']:
    path = entry['path']; assert allowed(path), path
    observed = hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    assert observed == entry['after_sha256'].lower() == freeze['files'][path].lower(), path
    records[path] = dict(originalBaselineSha256=protected.get(path),
                         frozenSha256=observed, ownerThreadId=owner,
                         handoffBeforeSha256=entry['before_sha256'],
                         beforeEvidenceStatus=entry['baseline_status'],
                         ownerFingerprintSource=manifest_source.relative_to(ROOT).as_posix(),
                         ownerFingerprintSha256=hashlib.sha256(manifest_source.read_bytes()).hexdigest(),
                         scope='Explicitly handed off ten-role direction art, three shared directional scripts and two Editor helpers; gameplay frozen')
# Validate every retained prior registration too, including the frozen BaseEnemy integration.
for path, entry in records.items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == entry['frozenSha256'], path
destination.mkdir(parents=True)
for path in records:
    target = destination/path; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ROOT/path, target)
for name in ['implementation_manifest.json','final_frozen_fingerprints.json','scope_final.json','handoff_boundary_audit.json','editor_validation.json','progress.json']:
    shutil.copy2(art/name, destination/name)
history = REPORT/f'audit/coordinated-external-changes-before-{tag}.json'
assert not history.exists(); shutil.copy2(current, history)
record = dict(capturedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              authorization='User authorized coordination; explicit narrow handoff and explicit return recorded in this chat',
              ownerFingerprintSource=manifest_source.relative_to(ROOT).as_posix(),
              ownerFingerprintSha256=hashlib.sha256(manifest_source.read_bytes()).hexdigest(),
              ownerFreezeSource=freeze_source.relative_to(ROOT).as_posix(),
              ownerFreezeSha256=hashlib.sha256(freeze_source.read_bytes()).hexdigest(),
              ownerFreezeFilesChecked=len(freeze['files']), files=records,
              previousRegistration=history.relative_to(REPORT).as_posix(),
              snapshot=destination.relative_to(REPORT).as_posix())
current.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(len(manifest['files']), 'narrow art files registered;', len(freeze['files']), 'final freeze hashes verified; original protection baseline unchanged')
