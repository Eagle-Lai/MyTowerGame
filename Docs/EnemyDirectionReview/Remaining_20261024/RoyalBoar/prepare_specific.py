from pathlib import Path
import json
D=Path(__file__).resolve().parent
plan=json.loads((D/'anatomy_plan.json').read_text(encoding='utf-8'))
old=plan['identity']
identity='Very round bright golden boar with ochre oval spots, cream-and-gold swept forelock, pointed gold ears, huge ivory upward tusks and four tiny golden hoof feet. No crown. Original atlas and six serialized renderers have NO independent tail sprite or tail binding; do not invent a tail.'
plan.update(identity=identity,actual_source_observation='Actually viewed original atlas and complete battle prefab offline rendering. Four legs, round torso with integrated original forelock/ears; separate original facial slice contains eyes, muzzle, tusks. Vertical view assigns tuft and ears exclusively to the head slice, no duplicate hair on body. No independent tail in atlas or six-renderer source.',vertical_distribution='Head owns ears and cream swept forelock. Torso owns ochre spots and small original flank fur points only. Transparent compatibility Tail, no rig tail node.')
(D/'anatomy_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for direction in ['Up','Down']:
 p=D/'generation'/direction/'prompt.txt'
 assert not (p.parent/'request.json').exists()
 s=p.read_text(encoding='utf-8').replace(old,identity)
 s=s.replace('7. ONE full detached original tail, root at BOTTOM center, rising UP from rump; preserve exact tail type','7. EMPTY MAGENTA CELL. Original has no independent tail; draw nothing here.')
 s+='\nRoyalBoar-specific distribution: ALL ears and the swept cream-and-gold forehead hair belong to each head slice ONLY. The head slice includes the full outer forehead/head silhouette around the facial parts. Torso is a very broad round golden spotted boar body; NO second forelock, NO ears, NO face, NO crown, NO tail, NO painted feet. Preserve short original flank fur points; do not invent a spiky dorsal mane. Four legs are created by mirroring detached fore/hind parts; each foot is a tiny tapered golden hoof block, no human toes, no claw fan. On Up feet show plain rear heel, no front cleft aimed at viewer. On Down show hoof fronts. Keep crisp thick original outlines and broad flat cel shading; no airbrush.\n'
 p.write_text(s,encoding='utf-8')
(D/'art_selection.json').write_text(json.dumps(dict(Up='generation/Up/raw.png',Down='generation/Down/raw.png',transparent_parts=['Up_Tail','Down_Tail'],reason='No independent tail in original atlas or actual serialized renderers. Seventh compatibility slice remains transparent; tail nodes removed before install.'),indent=2)+'\n',encoding='utf-8')
print('RoyalBoar exact reference distribution saved; no request sent')
