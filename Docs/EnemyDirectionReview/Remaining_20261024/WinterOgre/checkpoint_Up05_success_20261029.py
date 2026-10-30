"""Write only WinterOgre review/ownership documents after the actual Up05 success."""
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parent))
from session_winterogre import D, H, NAME, OWNER, TOKEN, owner, read, write, sha, now, stage

owner()
up = D / 'generation/Up/revision_05'
assert read(up / 'result.json')['status'] == 200
assert not (D / 'generation/Down/request.json').exists()
write(D / 'raw_review_Up05_20261029.json', {
    'observed_at': now(), 'source': 'generation/Up/revision_05/raw.png',
    'raw_sha256': sha(up / 'raw.png'), 'actual_view': True, 'format': 'PNG',
    'dimensions': [1536, 1024], 'status': 'accepted_for_character_local_staging',
    'findings': [
        'Three matching bald spotted rear heads with outer pointed ears; no eyes, nose, mouth or tongue.',
        'Rear belt has studs and no front square buckle; white fur loincloth retained.',
        'Two complete shoulder-to-empty-fist arms with matching brown studded white-rimmed cuffs; no weapon.',
        'The bare leg has a smooth heel and no front toe divisions; connection roots are solid opaque.',
        'Magenta background and no ground shadow. Torso includes rounded shoulder stubs; inspect connected layering for duplicated silhouettes.',
        'Arm roots start above the nominal lower half; explicit extraction rectangles must preserve the roots.'
    ],
    'limitations': 'Raw parts review only; connected offline rig and runtime are pending.'
}, fresh=True)
write(D / 'art_selection.json', {
    'Up': 'generation/Up/revision_05/raw.png', 'Down': 'generation/Down/raw.png',
    'preserve_warm_foreground': True,
    'review': 'Up05 actually viewed; Down pending. Service-control art is excluded.'
}, fresh=True)
write(D / 'generation/Down/generation_intent.json', {
    'recorded_at': now(), 'owner_thread_id': OWNER, 'dispatch_token': TOKEN,
    'character': NAME, 'direction': 'Down', 'max_requests': 1,
    'kind': 'first_production_direction_not_network_probe',
    'reason': 'Actual Up05 succeeded and was visually reviewed. Fill missing front art under the original task authorization.',
    'up_result_sha256': sha(up / 'result.json'), 'up_raw_sha256': sha(up / 'raw.png'),
    'parameters': {'endpoint': 'https://aihub.dog/v1/images/edits', 'model': 'gpt-image-2',
                   'quality': 'medium', 'size': '1536x1024', 'n': 1},
    'stop': 'No automatic retry. Preserve any missing or HTTP outcome.'
}, fresh=True)
p = read(H / 'progress.json')
i = next(x for x in p['items'] if x['name'] == NAME)
i['allowance_usage']['verified_service_recovery']['used'] = 1
i.update(generation_outcome='Up05HTTP200/raw actually viewed; prior five Up uncertain preserved; firstDown pending',
         recovery_stage='Up05_actual_raw_review_done_Down_initial_pending')
p['updated_at'] = now()
write(H / 'progress.json', p)
stage('WinterOgre_Up05_HTTP200_actual_raw_review_done_Down_initial_pending', D / 'raw_review_Up05_20261029.json')
print(json.dumps({'up_status': 200, 'old_uncertain': 5, 'down': 'first_request_pending'}))
