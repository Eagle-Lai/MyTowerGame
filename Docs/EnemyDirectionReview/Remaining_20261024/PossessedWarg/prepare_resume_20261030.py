from pathlib import Path
import difflib, json, sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from session_current import *

c = owner()
decision_file = RUN / 'resume_20261030_092519_PossessedWarg/bounded_resume_decision.json'
decision = read(decision_file)
originals = read(ROOT / decision['preserved_evidence_file'])
assert len(originals) == 21
for f, s in originals.items():
    assert sha(HERE / f) == s, f
identity = ('Deep dark olive-brown shaggy warg with muted warm ochre patches and scar-like cross marks, '
            'two pointed triangular ears, a short sequence of small pointed golden spikes on the forehead and longer golden spikes along its back. '
            'Broad dark brown canine nose and muzzle, amber-yellow eyes with small black pupils, heavy dark brows, '
            'large ivory fangs and teeth, ochre mouth accents. Four sturdy canine legs with rounded paws and subtle toe divisions, '
            'one long broad curved dark brown shaggy tail. No saddle, collar, armor, rider, wings or invented organs.')
save(HERE / 'source_visual_review_20261030.json', {
    'observed_at': now(), 'reviewed': ['reference/PossessedWarg.png', 'reference/source_prefab_offline.png', 'generation/Up/raw.png'],
    'identity': identity, 'original_plan_unchanged': True,
    'up_finding': 'Rear head is faceless, but front-facing gold ear pads and forward toe divisions remain visible. Preserve raw; locally revise ear interiors to outer-ear fur and paws to plain rear heels before stage. Head crown spikes and dorsal spikes are present in its own original atlas and remain.',
    'source_anatomy': {'heads': 1, 'head_expressions': 3, 'legs': 4, 'tails': 1, 'ground_shadow_requested': False},
    'old_down_outcome': 'unknown', 'old_down_possible_charge': 'unknown',
    'source_hashes': {p: originals[p] for p in originals if p.startswith('reference/')},
})
save(HERE / 'reviewed_anatomy_plan_20261030.json', dict(read(HERE / 'anatomy_plan.json'), identity=identity,
    actual_review='source_visual_review_20261030.json', preserve_original_plan_bytes=True))
folder = HERE / 'generation/Down/revision_01'
folder.mkdir(exist_ok=False)
prompt = f'''Use case: identity-preserve. Asset type: production 2D cutout game sprite parts sheet.
Image 1 is PossessedWarg's actual original atlas. Image 2 is the full original serialized source prefab, reference only. Preserve this precise character's color blocks, outline, proportions and anatomy. Do not infer a new design from the name.
Character: {identity}
Requested view: TRUE FRONT, travelling TOWARD viewer toward screen DOWN, elevated orthographic axial quadruped view. No side profile, three-quarter, rotation or mirror shortcut. Muzzle centered beneath the two amber-yellow eyes, broad near face, far rump behind.
ONE sheet exactly 4 equal columns by 2 equal rows, seven detached parts in reading order, eighth cell EMPTY:
1. ONE normal head only: exactly two pointed ears with original ochre inner pads, original golden forehead spikes, amber eyes, broad dark nose, closed snarl and visible ivory fangs. No torso.
2. Same skull/ear/spike silhouette and alignment, angry attack head with open jaws and original ivory fangs/teeth. No torso.
3. Same skull/ear/spike silhouette and alignment, dead head with rolled amber eyes and hanging ochre tongue, matching original expression. No torso.
4. ONE complete elevated axial canine torso ONLY: broad rounded far rump at TOP, narrow near neck/chest at BOTTOM CENTER. Preserve dark olive-brown ragged fur, sparse warm ochre markings and its actual golden dorsal spikes on the far back, no duplicated forehead spikes or face. Compact horizontal quadruped viewed from front above, NOT an upright human torso. No attached head, ears, legs, paws or tail; solid opaque neck root.
5. ONE detached left foreleg with rounded opaque shoulder root at TOP CENTER and single forward-facing rounded paw at BOTTOM, dark brown fur and subtle toe divisions. No extra limb.
6. ONE detached left hindleg with rounded opaque hip root at TOP CENTER and single forward-facing rounded paw at BOTTOM, matching fur and toe divisions. No extra limb.
7. ONE full long bushy curved dark brown tail matching original, solid rounded root at BOTTOM CENTER rising upward to a tapered shaggy tip. No new organ or detached spikes.
8. EMPTY magenta background.
Each part stays entirely in its own equal cell, centered with 12 percent empty padding. All three head cells have the same scale and alignment. No assembled creature, duplicate heads or ears on torso, labels, grid lines or crossing cell borders. Solid opaque roots and complete continuous dark outlines; no open tubes or internal magenta holes.
Exact original simple flat cartoon cel shading and thick smooth dark brown outline, deep olive-brown fur with restrained ochre details and golden pointed spikes, amber eyes and ivory fangs. No photorealistic fur, new mane, equipment or identity changes.
Background flat RGB #FF00FF immediately outside every outline. No floor, ground shadow, cast shadow, glow, halo, checkerboard, text or watermark. Crisp clean edges suitable for true transparency extraction.
'''
(folder / 'prompt.txt').write_text(prompt, encoding='utf-8')
before = (HERE / 'generate_before_20261030.mjs').read_text(encoding='utf-8')
after = (RUN / 'generate.mjs').read_text(encoding='utf-8')
assert sha(HERE / 'generate_before_20261030.mjs') == decision['generator_before_sha256']
(HERE / 'generator_resume_patch_20261030.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='generate.mjs.before', tofile='generate.mjs')), encoding='utf-8')
save(HERE / 'generator_resume_scope_20261030.json', {
    'observed_at': now(), 'before_sha256': sha(HERE / 'generate_before_20261030.mjs'), 'after_sha256': sha(RUN / 'generate.mjs'),
    'before_backup': 'generate_before_20261030.mjs', 'patch': 'generator_resume_patch_20261030.patch',
    'scope': 'Dedicated PossessedWarg authorized-resume Down/revision_01 branch only, no original Down/raw requirement; original protections in all other branches retained. This branch checks original 21 evidence files, six protected files, actual owner/token, fresh8088 Unity evidence, no live generation/no successful Down, fixed one request and direct Curl. Transport result and provider response saved only for this branch.',
    'ps1_unchanged': sha(RUN / 'generate_character.ps1') == sha(HERE / 'generate_character_before_20261030.ps1'),
    'no_paid_tests': True,
})
auth = {
    'observed_at': now(), 'owner_thread_id': c['owner_thread_id'], 'dispatch_token': c['dispatch_token'],
    'character': NAME, 'direction': 'Down', 'revision': 'revision_01', 'user_statement': '继续任务',
    'parent_decision_file': decision_file.relative_to(ROOT).as_posix(), 'parent_decision_sha256': sha(decision_file),
    'standing_original_messages_file': decision['standing_original_messages_file'], 'standing_original_messages_sha256': decision['standing_original_messages_sha256'],
    'standing_source_thread_id': decision['standing_source_thread_id'], 'standing_source_user_message_id': decision['standing_source_user_message_id'],
    'interpretation': decision['authorization_interpretation'], 'max_requests': 1, 'accept_possible_duplicate_charge': True,
    'original_outcome': 'unknown', 'original_possible_charge': 'unknown', 'original_request_sha256': decision['original_request_sha256'],
    'prior_unknown_requests': 1, 'resets_automatic_counter': False, 'transport': 'curl_https_no_retry',
    'force_direct': True, 'edge_ip': '191.101.132.254', 'parameters': decision['parameters'],
    'generator_sha256': sha(RUN / 'generate.mjs'), 'preserved_evidence': originals, 'protected_six': decision['protected_six'],
    'no_borrowed_allowance': True, 'old_failure_not_invented': True, 'paid_diagnostic_requests': 0,
}
auth_file = HERE / 'authorized_resume_20261030.json'
save(auth_file, auth)
save(folder / 'recovery_intent.json', {
    'observed_at': now(), 'owner_thread_id': c['owner_thread_id'], 'dispatch_token': c['dispatch_token'],
    'character': NAME, 'direction': 'Down', 'revision': 'revision_01', 'max_requests': 1,
    'authorization_file': auth_file.relative_to(ROOT).as_posix(), 'authorization_sha256': sha(auth_file),
    'parent_decision_file': auth['parent_decision_file'], 'parent_decision_sha256': auth['parent_decision_sha256'],
    'standing_original_messages_file': auth['standing_original_messages_file'], 'standing_original_messages_sha256': auth['standing_original_messages_sha256'],
    'original_outcome': 'unknown', 'original_possible_charge': 'unknown', 'original_request_sha256': decision['original_request_sha256'],
    'preserved_evidence': originals, 'protected_six': decision['protected_six'], 'generator_sha256': auth['generator_sha256'],
    'parameters': decision['parameters'], 'transport': 'curl_https_no_retry', 'force_direct': True, 'edge_ip': '191.101.132.254',
    'input_sha256': [sha(HERE / 'reference/PossessedWarg.png'), sha(HERE / 'reference/source_prefab_offline.png')],
    'prompt_sha256': sha(folder / 'prompt.txt'), 'reason': 'One documented new bounded production request; original unknown evidence retained; never an automatic network retry.',
})
print('PossessedWarg exact Down01 authorization, intent, prompt and generator patch saved; no request sent.')
