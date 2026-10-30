from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
out=D/'generation/Down/revision_01'
out.mkdir(exist_ok=False)
prompt='''Use case: precise-object-edit. RoyalBoar production cutout sheet.
Image 1 is original atlas, image 2 complete source prefab, image 3 rejected Down sheet. Keep its first THREE facial head sprites: normal round eyes, angry eyes, X dead eyes, original gold ears/cream swept forelock/huge ivory tusks/gold muzzle. They own ALL facial features and ALL cream hair. Correct the fourth cell torso which wrongly contains cream hair and a second snout. Correct leg scale to match tiny source hoof blocks.
Output ONE exact 4-column x 2-row sheet, isolated sprites, 12 percent margins, flat pure #FF00FF background, no grid/text.
Cells 1,2,3: matching front-view normal/angry/dead heads with same dimensions and alignment as the edit target. Preserve original palette, style and boar identity.
Cell 4: ONE broad round golden spotted TORSO ONLY. Closed plain rounded top; darker ochre underside; a few short original flank fur points. NO cream or white hair anywhere on torso. NO nose, snout, mouth, eyes, nostrils, head, ears, tusks, neck bulb, tail, legs or feet. Only a round gold spotted torso silhouette. Do not put small faces or protruding bulbs on it.
Cell 5: one SHORT detached front leg with solid rounded attachment root above and TINY golden cloven hoof block below. Squat compact boar proportions, not long human leg.
Cell 6: one SHORT detached hind leg with solid rounded attachment root above and TINY golden cloven hoof block below. Squat compact boar proportions.
Cells 7 and 8: EMPTY pure magenta, no tail.
Orthographic slightly elevated FRONT view moving screen DOWN. Thick crisp dark outline, bright warm golden and ochre spots, broad clean flat cel shading, original adorable fat boar. No crown or additional equipment, no ground shadow, no gradients or noise in background, no watermark, no side-view cheat. All sprite interiors solid opaque, magenta ONLY outside sprite boundaries.
'''
(out/'prompt.txt').write_text(prompt,encoding='utf-8')
record=dict(status='rejected_pending_targeted_revision',source='generation/Down/raw.png',sha256=hashlib.sha256((D/'generation/Down/raw.png').read_bytes()).hexdigest().upper(),actual_observations='Actually viewed full returned sheet. First three expression heads coherent. Torso duplicates cream forelock and protruding gold snout/nostril shapes, so rejected before staging. Legs too elongated relative to original tiny source feet. Targeted revision preserves heads and isolates plain torso.',revision='generation/Down/revision_01')
(D/'raw_review_down_initial.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Down revision_01 prepared; initial image preserved')
