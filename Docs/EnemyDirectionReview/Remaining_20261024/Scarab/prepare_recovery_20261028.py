"""Persist a single-direction explicit-failure recovery intent. Writes Docs only."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, subprocess

D = Path(__file__).resolve().parent
HERE = D.parent
ROOT = HERE.parents[2]
OWNER = '01a18093-7687-7313-aaba-7419090cc829'
TOKEN = 'sabretoothtiger-to-scarab-a14cefa3c87b4f9187c899d88ead8c0c'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write_new(p, x):
    with p.open('x', encoding='utf-8') as f: json.dump(x, f, ensure_ascii=False, indent=2); f.write('\n')

chain = read(HERE/'conversation_chain.json')
assert (chain['state'], chain['owner_thread_id'], chain['dispatch_token'], chain['current_character']) == ('active', OWNER, TOKEN, 'Scarab')
assert os.environ.get('CODEX_THREAD_ID') == OWNER
assessment_path = HERE/'SabretoothTiger/successor_recovery_assessment_20261028_113344.json'
assessment = read(assessment_path)
protected = assessment['protected_six']
assert all(sha(ROOT/p) == s.lower() for p,s in protected.items())
prior = []
for direction in ['Up','Down']:
    folder = D/'generation'/direction
    result = read(folder/'result.json')
    assert result['status'] == 503 and not (folder/'raw.png').exists()
    assert not list(folder.glob('revision_*'))
    assert not (folder/'uncertain_result.json').exists()
    prior.append(dict(direction=direction, request=str((folder/'request.json').relative_to(ROOT)).replace('\\','/'), request_sha256=sha(folder/'request.json'), result_sha256=sha(folder/'result.json'), http_status=503))
for e in assessment['same_service_success_evidence']:
    assert sha(ROOT/e['request']) == e['request_sha256'].lower()
    assert sha(ROOT/e['result']) == e['result_sha256'].lower()
    request, result = read(ROOT/e['request']), read(ROOT/e['result'])
    assert request['endpoint']=='https://aihub.dog/v1/images/edits' and request['model']=='gpt-image-2'
    assert result['status']==200 and result['bytes']>0
    assert sha((ROOT/e['request']).with_name('raw.png')) == e['raw_sha256'].lower()
stamp = datetime.now(timezone(timedelta(hours=8))).isoformat()
files = {p.relative_to(ROOT).as_posix():sha(p).upper() for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
baseline_path = D/'incremental_before_recovery_20261028.json'
write_new(baseline_path, dict(observed_at=stamp, files=files, protected_scarab=protected, owner_thread_id=OWNER, dispatch_token=TOKEN))
(D/'git_status_before_recovery_20261028.txt').write_text(subprocess.run(['git','status','--short'],cwd=ROOT,capture_output=True,text=True,check=True).stdout,encoding='utf-8')
revision = D/'generation/Up/revision_01'
revision.mkdir()
prompt = (D/'generation/Up/prompt.txt').read_text(encoding='utf-8')
prompt += '\nScarab-specific anatomy clarification from the two original references: the head has TWO long dark olive antennae with ochre highlights, not mammal ears or horns. Preserve these two antennae in all three rear head states. Rear head is a plain dark olive outer head plate: no orange eye lenses, no teeth, no front mandibles visible from behind. Torso is the actual olive/ochre oval beetle carapace with broad cream/ochre longitudinal ridge bands, no tail, saddle, wings, fur or added organs. Each detached walking leg has the original cream jointed blade-like form and ochre tapered tip, with a thick dark outline and a solid root. Three leg cells represent the front/middle/rear LEFT legs; the rig will supply the opposite side. Exactly seven separate parts, not a whole insect. Keep the flat simple original cartoon style, no glossy 3D rendering.\n'
(revision/'prompt.txt').write_text(prompt,encoding='utf-8')
intent = dict(schema_version=1,character='Scarab',direction='Up',revision='revision_01',owner_thread_id=OWNER,dispatch_token=TOKEN,max_requests=1,
    reason='Both original Scarab requests were explicit HTTP503 with no raw or uncertain output. The preserved latest same-service SabretoothTiger Up revision_01 and Down revision_02 requests both returned HTTP200. This supports one bounded recovery attempt under the existing ordinary image-generation authorization; it does not guarantee service availability. SabretoothTiger Down-only $0.07 authorization is consumed and is not used here.',
    parent_request_sha256=sha(D/'generation/Up/request.json'),parent_result_sha256=sha(D/'generation/Up/result.json'),prior_attempts=prior,
    production_baseline=baseline_path.relative_to(ROOT).as_posix(),production_baseline_sha256=sha(baseline_path),production_file_count=len(files),protected_six_unchanged=True,
    same_service_success_evidence=dict(source=assessment_path.relative_to(ROOT).as_posix(),source_sha256=sha(assessment_path),successes=assessment['same_service_success_evidence']),
    reference_review=dict(atlas='reference/Scarab.png',complete_source='reference/source_prefab_offline.png',observation='Actual atlas and assembled reference viewed. Olive ochre shell, orange lens eyes, two antennae, ivory ochre mandibles, six cream jointed legs. No tail. Rear head must not display the face.'),
    recovery_policy='Preflight, then at most one Up request. Review the actual returned image before any Down request. Stop all paid generation immediately on service failure or uncertainty. Preserve all original evidence.',created_at=stamp)
write_new(revision/'recovery_intent.json',intent)
write_new(D/'recovery_preparation_20261028.json',dict(observed_at=stamp,owner_thread_id=OWNER,dispatch_token=TOKEN,production_count=len(files),protected_drift=[],prior_attempts=prior,up_revision='generation/Up/revision_01',paid_requests_made=0,unity='Target MyTowerGame absent from 8082 listing; user will connect it manually. No computer control authorized.'))
print(json.dumps(dict(production_files=len(files),protected_drift=[],up_revision=str(revision),paid_requests_made=0),ensure_ascii=False))
