"""Record this revision without rewriting any earlier review identities."""
from pathlib import Path
import json, hashlib, datetime

HERE = Path(__file__).resolve().parent
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

audit = json.loads((HERE/'scope_audit.json').read_text())
assert audit['pass'] and len(audit['changed_files']) == 9
assert audit['unchanged_other_battle_prefabs'] == 118
batch = HERE.parent/'Batch01_10'
original_batch_identity = {
    'implementation_manifest.json': '58A40662C0C8ABCB97ABF02D4B76439B91C43DB5833838A09DDA4852B99CB3C0',
    'final_frozen_fingerprints.json': 'AB1C018D90C15BFBAF8E060364D5B5B08D06EF31F8B4D0B215718B4A7EFC37D8',
}
assert all(sha(batch/p) == h for p, h in original_batch_identity.items())
semantics = json.loads((batch/'scope_tailfix_r01.json').read_text())
assert all(v['pass'] for v in semantics['prefab_semantics'].values())
assert not semantics['unexpected_prefab_changes']

artifacts = ['baseline.json', 'source_snapshot.json', 'implementation_manifest.json',
             'final_fingerprints.json', 'scope_audit.json', 'editor_validation.json',
             'focused_media_manifest.json', 'installed.txt', 'tail_before_after.gif',
             'tail_before_after.png', 'up_walk_fixed.gif', 'up_attack_fixed.gif',
             'up_death_fixed.gif', 'up_walk_fixed_phases.png',
             'up_attack_fixed_phases.png', 'up_death_fixed_phases.png', 'README.md']
progress = {
    'recorded_at': datetime.datetime.now().astimezone().isoformat(),
    'character': 'BlueScorpion', 'scope': 'Up Tail attachment only',
    'status': 'installed_waiting_for_user_art_review',
    'next_action': 'Wait for user review of BlueScorpion tail; do not start more enemies.',
    'changed_production_files': len(audit['changed_files']),
    'unchanged_other_battle_prefabs': 118,
    'runtime': audit['runtime'],
    'runtime_pass_count': sum(r['pass'] for r in audit['runtime']),
    'runtime_fail_count': sum(r['fail'] for r in audit['runtime']),
    'actual_frames': sum(r['frames'] for r in audit['runtime']),
    'semantic_audit': '../Batch01_10/scope_tailfix_r01.json',
    'original_batch_identity_unchanged': original_batch_identity,
    'prior_polish_identity_unchanged': audit['prior_polish_identity'],
    'artifacts_sha256': {p: sha(HERE/p) for p in artifacts},
    'unity_released': True,
    'unperformed': ['APK/device', 'release bundle build/readback', 'long battle', 'complete balance regression'],
}
(HERE/'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'status': progress['status'], 'pass': progress['runtime_pass_count'],
                  'fail': progress['runtime_fail_count'], 'frames': progress['actual_frames'],
                  'changed_files': progress['changed_production_files'],
                  'earlier_batch_identity_unchanged': True}))
