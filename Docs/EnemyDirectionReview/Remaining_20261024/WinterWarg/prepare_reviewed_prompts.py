from session_winterwarg import *

owner()
plan = read(D/'anatomy_plan.json')
old_identity = plan['identity']
identity = ('White/ivory shaggy stocky warg with warm gray-taupe underside shadows and scattered ochre oval spots. '
            'A row of large angular dark ochre-brown dorsal fur spines runs from the shoulders along the back, '
            'decreasing toward the rump. Broad cream eyes with black pupils under brown brows, broad dark brown nose, '
            'two very long ivory upper saber canines, smaller teeth, small brown chin tuft, and two small ROUND outer ears '
            'with cream rims. Four short white clawed canine paws, rounded strong hind haunches, and one long bushy '
            'white curved drooping tail with an ochre spot. No collar, saddle, weapon or armor.')
plan.update(identity=identity,source_observation={'reviewed':['original atlas 2048x1024','complete serialized source prefab offline reference','all source/battle YAML object blocks','8088 live hierarchy/renderers/clip float and PPtr keys/events'],
    'ears':'small rounded ears, not generic pointed wolf ears',
    'gait':'four anatomical legs; opposite diagonal pairs alternate; rounded shoulder/hip roots stay covered; axial depth determines far/near overlap',
    'Up':'plain back of head/outer ears; no eyes, mouth, inner ears or canines; dorsal spines remain; near hind paws show rear heels without toe grooves',
    'Down':'normal/angry/dead frontal face with long original canines; near forepaws show toes; torso has no duplicate head/ears',
    'tail':'top-center solid root; white bushy tail drops downward, joined to rump; adjust pivot to match root',
    'source_contract':'source_contract_20261029.json; Wolf Walk 0.5s, Ready 0.5s; Attack 0.5s, Death 0.416666657s'})
write(D/'anatomy_plan.json',plan)
for direction in ['Up','Down']:
    p=D/'generation'/direction/'prompt.txt'
    assert not (p.parent/'request.json').exists()
    s=p.read_text(encoding='utf-8').replace(old_identity,identity)
    s=s.replace('ONE full detached original tail, root at BOTTOM center, rising UP from rump; preserve exact tail type',
        'ONE full detached bushy white tail; SOLID ROOT at TOP CENTER, tail curves and hangs DOWN, matching original broad white tail with ochre spot; no second tail')
    s += ('\nWinterWarg-specific source observations: keep ROUND cream-rimmed ear silhouettes and the original white/taupe/ochre palette. '
          'The body is an elongated canine torso, not a ball or a humanoid. It contains the original large dark brown dorsal spines but NO duplicated head, ears, eyes or chin tuft. '
          'Spines taper from high shoulders to rump in axial perspective. Four leg instances will be assembled from these two detached front/hind leg source slices. '
          'One tail is assembled from its separate slice. All connection roots must be filled opaque fur.\n')
    if direction=='Up':
        s += ('All THREE head cells must be identical plain rear heads with two small ROUND OUTER ear backs, white fur and an ochre spot; never depict a snout, eye or fang. '
              'Paws must show smooth rounded rear-facing heels/back fur, with NO visible toes, front nail lines or sole pads. '
              'Tail root stays at the top of its cell; long tail droops down.\n')
    else:
        s += ('The face looks directly at viewer with symmetric small rounded ears, two cream eyes, a wide dark brown nose and the original two long saber canines. '
              'Angry face opens mouth; dead face closes eyes with tongue visible as in original. Paws are frontal, claw tips and toes at bottom.\n')
    p.write_text(s,encoding='utf-8')
write(D/'reference_review_20261029.json',{'observed_at':now(),'revision':'reference_r01','source_contract_sha256':sha(D/'source_contract_20261029.json'),'protected_six':read(D/'incremental_before_20261029.json')['protected_six'],
    'observations':plan['source_observation'],'identity':identity,'user_approved':False,'production_modified':False},True)
stage('reference_and_prompts_reviewed',D/'reference_review_20261029.json')
print('WinterWarg reference/own anatomy and two prompts reviewed; first requests not yet sent.')
