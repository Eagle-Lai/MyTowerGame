"""Character-local extraction and symmetric empty-fist layout; Docs outputs only."""
from pathlib import Path
import sys
import json
sys.path.insert(0, str(Path(__file__).resolve().parent))
from session_winterogre import D, H, owner, read, write, sha, now, stage, run

owner()
down = D / 'generation/Down'
assert read(down / 'result.json')['status'] == 200
write(D / 'raw_review_Down_20261029.json', {
    'observed_at': now(), 'source': 'generation/Down/raw.png',
    'raw_sha256': sha(down / 'raw.png'), 'actual_view': True,
    'status': 'accepted_for_character_local_staging',
    'findings': [
        'Normal stern amber eyes, flat nose and ivory zigzag teeth match the source.',
        'Angry open mouth and pale blank dead eyes with tongue are distinct aligned head states.',
        'Front body has the cream square buckle with gold diamond, spotted belly and white fur skirt.',
        'Both full arms have solid rounded shoulder roots, huge matching cuffs and empty fists; no crook.',
        'Bare golden foot has front toe divisions; no boots, extra equipment or ground shadow.'
    ],
    'limitations': 'Actual raw review only; connected rig and runtime pending.'
}, fresh=True)
selection = read(D / 'art_selection.json')
selection.update(review='Both actual generated originals reviewed. Preserve full roots and source-specific features.', rectangles={
    'Up_HeadNormal': [25, 120, 340, 400],
    'Up_HeadAngry': [365, 120, 680, 400],
    'Up_HeadDead': [700, 120, 1015, 400],
    'Up_Body': [1040, 20, 1520, 490],
    'Up_ArmWeapon': [25, 490, 295, 950],
    'Up_ArmFree': [415, 490, 685, 950],
    'Up_Leg': [760, 530, 970, 920],
    'Down_HeadNormal': [30, 120, 360, 450],
    'Down_HeadAngry': [385, 120, 715, 450],
    'Down_HeadDead': [730, 120, 1055, 460],
    'Down_Body': [1070, 80, 1510, 455],
    'Down_ArmWeapon': [45, 510, 310, 940],
    'Down_ArmFree': [465, 510, 735, 940],
    'Down_Leg': [835, 550, 1045, 890]
})
write(D / 'art_selection.json', selection)
adjustments = {
    'note': 'Two equal empty-fist arms replace the generic armed-Giant size asymmetry. Shoulder pivots use actual opaque upper roots, positioned inside body stubs. Preserve original ArmR/FistR/Weapon hierarchy in production.',
    'layout': {'motion': {'legAngle': 7.5, 'legLift': 0.09, 'bodyBob': 0.005,
                           'bodyRoll': 0.6, 'tailSwing': 0}},
    'sprites': {
        'Up_ArmWeapon': {'pivotX': 0.57, 'pivotY': 0.955},
        'Up_ArmFree': {'pivotX': 0.42, 'pivotY': 0.955},
        'Down_ArmWeapon': {'pivotX': 0.59, 'pivotY': 0.955},
        'Down_ArmFree': {'pivotX': 0.41, 'pivotY': 0.955}
    }, 'parts': {}
}
for direction in ['Up', 'Down']:
    parts = adjustments['parts']
    parts[direction + '/Body'] = {'y': 0.49, 'width': 0.74, 'height': 0.62}
    parts[direction + '/Head'] = {'y': 0.84, 'width': 0.50, 'height': 0.40, 'order': 30}
    right = 1 if direction == 'Up' else -1
    for name, sign in [('ArmR', right), ('ArmL', -right)]:
        parts[direction + '/' + name] = {'x': sign * 0.245, 'y': 0.74,
                                         'width': 0.33, 'height': 0.50,
                                         'order': 12 if direction == 'Up' else 28}
    for name, sign in [('LegL', -1), ('LegR', 1)]:
        parts[direction + '/' + name] = {'x': sign * 0.15, 'y': 0.255,
                                         'width': 0.21, 'height': 0.26, 'order': 12}
write(D / 'layout_adjustments.json', adjustments, fresh=True)
run('character_step.py', 'stage', 'WinterOgre')
stage('WinterOgre_both_raws_reviewed_character_local_staging_pending_visual_check', D / 'offline_rig_proof.png')
print(json.dumps({'raws': 2, 'stage': 'offline_pending_actual_visual_review', 'new_requests': 0}))
