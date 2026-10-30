from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

D = Path(__file__).resolve().parent
H = D.parent
R = H.parents[2]
NAME = 'Turkey'
TOKEN = 'troll-to-turkey-1e2dd1235ed84e41b82b178e45f86309'
sys.path.insert(0, str(H))
from mcp_call import Client, URL


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def owner():
    chain = read(H / 'conversation_chain.json')
    assert chain['state'] == 'active'
    assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
    assert chain['current_character'] == NAME
    assert chain['dispatch_token'] == TOKEN
    assert Path(chain['project_root'].replace('/', '\\')).resolve() == R.resolve()
    return chain


def inventory():
    return {
        path.relative_to(R).as_posix(): sha(path)
        for folder in ['Assets', 'Packages', 'ProjectSettings', 'Luban']
        for path in (R / folder).rglob('*')
        if path.is_file()
    }


def unwrap(value):
    value = value.get('structuredContent') or json.loads(value['content'][0]['text'])
    if 'result' in value and 'data' not in value:
        value = value['result']
    if not value.get('success'):
        raise RuntimeError(json.dumps(value, ensure_ascii=False))
    return value


def probe(client):
    code = 'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};'
    return unwrap(client.tool('execute_code', {'action': 'execute', 'code': code}))['data']['result']


def replace_once(text, before, after, label):
    count = text.count(before)
    if count != 1:
        raise ValueError(f'{label}: expected one match, found {count}')
    return text.replace(before, after, 1)


chain = owner()
assert not (D / 'incremental_before_20261028.json').exists()
assert not (D / 'reference_review_20261028.json').exists()
assert not (D / 'generation' / 'Up' / 'generation_intent.json').exists()
assert not (D / 'generation' / 'Down' / 'generation_intent.json').exists()
assert (D / 'anatomy_plan.json').is_file()

target = next(item for item in read(H / 'local_baseline.json')['targets'] if item['name'] == NAME)
production = read(H / 'production_fingerprints_before.json')
protected_paths = [
    target['battle'], target['battle'] + '.meta',
    target['source'], target['source'] + '.meta',
    target['atlas'], target['atlas'] + '.meta',
]
protected = {path: sha(R / path) for path in protected_paths}
assert all(protected[path] == production[path].upper() for path in protected_paths)
reference_names = {
    target['battle']: 'Enemy_Turkey.prefab',
    target['battle'] + '.meta': 'Enemy_Turkey.prefab.meta',
    target['source']: 'Turkey.prefab',
    target['source'] + '.meta': 'Turkey.prefab.meta',
    target['atlas']: 'Turkey.png',
    target['atlas'] + '.meta': 'Turkey.png.meta',
}
assert all(sha(D / 'reference' / reference_names[path]) == digest for path, digest in protected.items())

for direction in ['Up', 'Down']:
    out = D / 'generation' / direction
    assert (out / 'prompt.txt').is_file()
    assert not any((out / name).exists() for name in ['request.json', 'result.json', 'uncertain_result.json', 'raw.png'])

client = Client()
project = client.identity()
assert project['projectRoot'].replace('\\', '/').lower() == str(R).replace('\\', '/').lower()
project_version = next(
    line.split(':', 1)[1].strip()
    for line in (R / 'ProjectSettings' / 'ProjectVersion.txt').read_text(encoding='utf-8').splitlines()
    if line.startswith('m_EditorVersion:')
)
assert project['unityVersion'] == project_version
state = client.resource('mcpforunity://editor/state')
live = probe(client)
assert not any(value for key, value in live.items() if key != 'scene'), live
errors = unwrap(client.tool('read_console', {'action': 'get', 'types': ['error'], 'count': '50', 'format': 'json'}))

plan_path = D / 'anatomy_plan.json'
plan = read(plan_path)
plan.update(
    identity='Golden tan spotted turkey with a long cream neck, attached gold wattle, rounded tan body, two folded feather wings, two clawed feet, and a broad cream-and-ochre fan tail.',
    source_observations={
        'viewed': [
            'reference/Turkey.png',
            'reference/source_prefab_offline.png',
            'reference/Turkey.prefab',
            'reference/Enemy_Turkey.prefab',
            'reference/source_structure.json',
            'Assets/_UIAssets/Monsters/_Common/Animations/Turkey/Controller.controller',
        ],
        'silhouette': 'The original has a rounded golden-tan spotted body, long cream neck and gold wattle, folded wings, two clawed legs, and a broad cream-and-ochre fan tail.',
        'head': 'HeadNormal, HeadAngry and HeadDead are separate source expressions. Up uses one consistent featureless rear head/neck silhouette; Down uses the corresponding source expressions.',
        'body': 'Keep the spotted torso and rump as one central cutout. Do not paint the separately-authored tail fan or wings onto the body.',
        'limbs': 'The source prefab has separate Wing, LegL and LegR renderers. Each sheet cell is one complete source-side limb cutout; the installed rig must preserve the original paired limb count.',
        'tail': 'Tail is its own broad fan-feather renderer, not a narrow tuft. Preserve its centerline attachment and validate pivot/overlap against the source prefab before installation.',
        'prefab_contract': 'Preserve the original root scale, SortingGroup, Animator, Collider, BaseEnemy, HpBar, Shadow and animation-event receiver. No shared C# changes are planned.',
        'animation_contract': 'Retain the Turkey controller parameters and Idle/Ready/Walk/Run/Attack/Death behavior, including Attack SetHead expression events and Death HeadDead event.',
    },
    orientation_contract={
        'Up': 'Axial rear view travelling screen-up. No eyes, beak or front facial features; head includes the full neck and keeps the wattle in its source location, naturally hidden from directly behind.',
        'Down': 'Axial front view travelling screen-down. Beak below the eyes; cream neck and gold wattle remain attached to the head/neck cutout.',
        'pairing': 'The sheet uses one folded wing cell and one leg cell; final assembly must retain two wings and two legs.',
        'tail': 'Use a broad symmetrical cream-and-ochre fan attached at the rump centerline; never replace it with a narrow rooster tail or duplicate it on the body.',
    },
)
plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

up_replacements = [
    ('Requested view: REAR/BACK view, travelling AWAY toward screen UP. NO visible eyes, nostrils, teeth, inner-ear pads or face on the back of the head. Only plain outer backs of ears, actual original rear head hair/hat, rump and tail are visible. Same elevated orthographic game perspective as source, never rotate/flip/stretch its side sprite to fake a new view.',
     'Requested view: axial REAR/BACK view travelling AWAY toward screen UP. Show the outer back of the head, full rear neck, body and tail. No eyes, beak or front-face features. Keep the long cream neck and gold wattle attached to the original head/neck cutout; from directly behind the front-facing wattle is naturally occluded. Same elevated orthographic game perspective as the source, never rotate, flip or stretch its side sprite to fake a new view.'),
    ('1. detached normal head only, including its original ears/horns/crest/hat, NO torso (rear view: expressions use the SAME plain rear head silhouette, no face)',
     '1. rear-facing head plus full long cream neck as one source-aligned cutout; keep the gold wattle attached in its original position, naturally hidden from directly behind; NO body or face'),
    ('2. same head and alignment, angry attack expression (rear view: expressions use the SAME plain rear head silhouette, no face)',
     '2. same blank rear head-and-neck silhouette and alignment; no face or visible expression'),
    ('3. same head and alignment, dead expression (rear view: expressions use the SAME plain rear head silhouette, no face)',
     '3. same blank rear head-and-neck silhouette and alignment; no face or visible expression'),
    ('4. detached complete torso/back and rump ONLY, preserving original dorsal details/saddle/armor, NO head, legs, tail or wings',
     '4. detached spotted torso and rump ONLY, with its exact original rear markings; NO head/neck, legs, fan tail or wings'),
    ('6. ONE left leg/foot, root at TOP center, toes down towards the ground',
     '6. ONE complete left-side golden leg and clawed foot, root at TOP center, toes at the ground; no second leg in this cell'),
    ('7. ONE full detached original tail, root at BOTTOM center, rising UP from rump; preserve exact tail type',
     '7. ONE broad detached cream-and-ochre fan tail, narrow root at BOTTOM center, feathers radiating symmetrically UP and outward; preserve the original wide fan, not a narrow tuft'),
    ('Torso includes all distinctive back adornment visible from this view (mushrooms, crystals, mane, saddle, armor, cannon or fan feathers where present), but excludes anything assigned its own cell.',
     'Body contains only the original spotted torso and rump. The broad fan tail belongs only in its own cell and must not be painted onto the body.'),
    ('muzzle centered below eyes', 'beak centered below eyes on the front-facing Down sheet; the Up sheet has no visible face'),
]

down_replacements = [
    ('Requested view: FRONT view travelling TOWARD viewer, screen DOWN. Show the matching face and forward-pointing feet, with correct forehead/neck and chest connections. Same elevated orthographic game perspective as source, never rotate/flip/stretch its side sprite to fake a new view.',
     'Requested view: axial FRONT view travelling TOWARD viewer, screen DOWN. Show the source-matched eyes and beak, long cream neck, attached gold wattle and forward-facing clawed feet. Same elevated orthographic game perspective as the source, never rotate, flip or stretch its side sprite to fake a new view.'),
    ('1. detached normal head only, including its original ears/horns/crest/hat, NO torso',
     '1. detached normal head plus full long cream neck and attached gold wattle as one source-aligned cutout; NO torso'),
    ('2. same head and alignment, angry attack expression',
     '2. same head-and-neck size and alignment, using the original angry expression and keeping the wattle attached'),
    ('3. same head and alignment, dead expression',
     '3. same head-and-neck size and alignment, using the original dead expression and keeping the wattle attached'),
    ('4. detached complete torso/back and rump ONLY, preserving original dorsal details/saddle/armor, NO head, legs, tail or wings',
     '4. detached spotted torso and rump ONLY, with exact original markings; NO head/neck, legs, fan tail or wings'),
    ('6. ONE left leg/foot, root at TOP center, toes down towards the ground',
     '6. ONE complete left-side golden leg and clawed foot, root at TOP center, toes at the ground; no second leg in this cell'),
    ('7. ONE full detached original tail, root at BOTTOM center, rising UP from rump; preserve exact tail type',
     '7. ONE broad detached cream-and-ochre fan tail, narrow root at BOTTOM center, feathers radiating symmetrically UP and outward; preserve the original wide fan, not a narrow tuft'),
    ('Torso includes all distinctive back adornment visible from this view (mushrooms, crystals, mane, saddle, armor, cannon or fan feathers where present), but excludes anything assigned its own cell.',
     'Body contains only the original spotted torso and rump. The broad fan tail belongs only in its own cell and must not be painted onto the body.'),
    ('muzzle centered below eyes', 'beak centered below eyes, with the original cream neck and gold wattle attached to the head/neck cutout'),
]

for direction, replacements, appendix in [
    ('Up', up_replacements, 'REAR-SPECIFIC: all three head cells are the same featureless rear head-and-neck silhouette. Do not show the eyes, beak, front of the wattle or any facial expression. Keep one wing and one leg per cell; final assembly retains a pair of each. The tail is a broad, rounded fan with the original cream and ochre feather pattern, centered behind the rump. Do not invent a rooster comb, spurs, horns, rider or equipment.\n'),
    ('Down', down_replacements, 'FRONT-SPECIFIC: keep each original face expression distinct and aligned; the gold wattle stays attached beneath the long cream neck and is not painted on the body. Keep one wing and one leg per cell; final assembly retains a pair of each. The original broad cream-and-ochre tail fan remains a separate centerline part behind the spotted rump. Do not invent a rooster comb, spurs, horns, rider or equipment.\n'),
]:
    prompt_path = D / 'generation' / direction / 'prompt.txt'
    prompt = prompt_path.read_text(encoding='utf-8')
    for before, after in replacements:
        prompt = replace_once(prompt, before, after, direction)
    prompt += '\n' + appendix
    prompt_path.write_text(prompt, encoding='utf-8')

files = inventory()
assert not (R / target['art_dir']).exists()
assert not (R / (target['art_dir'] + '.meta')).exists()
diff = subprocess.run(
    ['git', 'diff', '--', target['battle'], str(Path(target['source']).parent)],
    cwd=R, capture_output=True, text=True, check=True,
)
assert not diff.stdout.strip(), 'Turkey source or battle assets have pre-existing diff'
status = subprocess.run(['git', 'status', '--short', '--untracked-files=all'], cwd=R, capture_output=True, text=True, check=True)
(D / 'git_status_before_20261028.txt').write_text(status.stdout, encoding='utf-8')
(D / 'git_target_diff_before_20261028.txt').write_text(diff.stdout, encoding='utf-8')

baseline_path = D / 'incremental_before_20261028.json'
write(baseline_path, {
    'observed_at': now(),
    'files': files,
    'protected_six': protected,
    'owner_thread_id': chain['owner_thread_id'],
    'dispatch_token': TOKEN,
    'scope': ['Assets', 'Packages', 'ProjectSettings', 'Luban'],
    'comparison': 'Path union of this pre-install snapshot and the post-install project inventory.',
})

review_path = D / 'reference_review_20261028.json'
write(review_path, {
    'observed_at': now(),
    'owner_thread_id': chain['owner_thread_id'],
    'dispatch_token': TOKEN,
    'transport': URL,
    'project': project,
    'editor_state': state,
    'live_probe': live,
    'existing_errors': errors,
    'protected_six': protected,
    'reference_sha256': {path.name: sha(path) for path in (D / 'reference').iterdir() if path.is_file()},
    'anatomy_plan_sha256': sha(plan_path),
    'prompt_sha256': {direction: sha(D / 'generation' / direction / 'prompt.txt') for direction in ['Up', 'Down']},
    'observations': plan['source_observations'],
    'art_review_status': 'internal_reference_review_complete; generated art not yet reviewed',
    'user_approved': False,
})

up_dir = D / 'generation' / 'Up'
write(up_dir / 'generation_intent.json', {
    'created_at': now(),
    'owner_thread_id': chain['owner_thread_id'],
    'dispatch_token': TOKEN,
    'character': NAME,
    'direction': 'Up',
    'max_requests': 1,
    'model': 'gpt-image-2',
    'quality': 'medium',
    'size': '1536x1024',
    'n': 1,
    'transport': 'node_fetch',
    'prompt_sha256': sha(up_dir / 'prompt.txt'),
    'inputs': {
        'atlas_sha256': sha(D / 'reference' / 'Turkey.png'),
        'source_render_sha256': sha(D / 'reference' / 'source_prefab_offline.png'),
    },
    'protected_six': protected,
})

progress = read(H / 'progress.json')
item = next(value for value in progress['items'] if value['name'] == NAME)
assert item['status'] == 'not_started'
item.update(status='reference_prepared', user_approved=False, reference_review_file='Turkey/reference_review_20261028.json')
progress.update(current=NAME, updated_at=now())
(H / 'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

chain = owner()
chain.update(
    current_stage='reference_prepared_pending_Up_generation',
    last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Turkey/reference_review_20261028.json',
    updated_at=now(),
)
(H / 'conversation_chain.json').write_text(json.dumps(chain, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print(json.dumps({
    'character': NAME,
    'status': item['status'],
    'user_approved': item['user_approved'],
    'baseline_files': len(files),
    'protected_files': len(protected),
    'live': live,
    'up_intent_max_requests': 1,
}, ensure_ascii=False))
