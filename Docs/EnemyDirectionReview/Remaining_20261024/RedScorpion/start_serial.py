from serial_common import *
owner()
t=next(t for t in read(H/'local_baseline.json')['targets'] if t['name']==NAME)
baseline=read(H/'production_fingerprints_before.json')
protected={p:sha(ROOT/p) for q in ['battle','source','atlas'] for p in [t[q],t[q]+'.meta']}
assert all(s==baseline[p] for p,s in protected.items())
for q in ['source','atlas','battle']:
    for suffix in ['', '.meta']:
        assert sha(D/'reference'/(Path(t[q]).name+suffix))==protected[t[q]+suffix]
assert not (D/'installed_manifest.json').exists()
assert not any((D/'generation').rglob('request.json'))
report=available(Client())
report.update(protected=protected,rule_path_discrepancy='AGENTS FreedomTower_1/D: is historical; explicit target E:/MyTowerGame')
write(D/'start_preflight_20261026.json',report)
plan=read(D/'anatomy_plan.json')
plan['observed_reference_notes_zh']='已实际查看原始图集和完整源prefab：金黄甲壳带赭色斑点、深棕描边，头前有两条象牙色弯曲眉角与口钳，身体分节背甲带象牙色锥刺；六条细长分节步足、两只宽金黄钳、高拱分节尾和末端金黄钩状膨大尾刺，尾刺上也有象牙色锥刺。尾根在后腹，Up不画脸，身体不能重复画足、钳、头或第二条尾。名称不要求红色。'
write(D/'anatomy_plan.json',plan)
for direction in ['Up','Down']:
    p=D/'generation'/direction/'prompt.txt'
    text=p.read_text(encoding='utf-8')
    text+='\nREFERENCE-SPECIFIC: This is a stylized game scorpion, with exactly SIX walking legs and TWO broad pincers, not a biological diagram. The head has two swept ivory brow horns and small ivory mouth pincers on its FRONT, not ears. Back torso has gold segmented plates, ochre patches and the ORIGINAL ivory conical dorsal spikes; no duplicate legs/pincers/head/tail painted on body. Walking legs are slim gold articulated tapered plates, not mammal paws. Tail cell includes the WHOLE gold segmented high arch and its bulbous gold downward-hooking sting bearing large ivory conical spikes; do NOT replace it with a thin ivory needle or a low spiral. All part roots solid and filled. Keep tail and claws wholly within their own cells. '
    if direction=='Up':
        text+='All three head cells show the SAME plain closed golden rear head with no eyes, mouth, teeth, nostrils, or front-facing ivory brow mask. Only appropriate rear silhouettes of the original horns may show. Rear walking-leg tips point along travel away from viewer; no front toes. The rear tail base sits at bottom, curves up then over with intact downward hook.'
    else:
        text+='The centered front head preserves original amber stern eyes, two prominent swept ivory brow horns and small mouth pincers. Angry and dead states match this head. Pincer arm has both upper broad jaw and lower slim curved jaw, joined at the right root. No invented hair or red shell.'
    p.write_text(text+'\n',encoding='utf-8')
print(json.dumps(dict(project=report['project'],probe=report['probe'],protected_count=len(protected),prompts='two unrequested prompts prepared'),ensure_ascii=False))
