from pathlib import Path
import json
d=Path(__file__).resolve().parent
(d/'art_review_rejected.json').write_text(json.dumps({'Up':{'revision':'initial','issues':['Invented paired ear-like appendages behind head','Rear foot shows front claws aimed at viewer','Wing has four rather than original three feather tips','Body has raised neck collar rim']},'Down':{'revision':'initial','issues':['Torso includes duplicate leg stubs','Wing connection is on left rather than requested top right and size/shape varies']}},ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
for direction in ['Up','Down']:
    p=d/'generation'/direction/'revision_01';p.mkdir(exist_ok=False)
    prompt=(p.parent/'prompt.txt').read_text(encoding='utf-8')+chr(10)+'Image 3 is the REJECTED initial sheet, shown only to identify the corrections. Preserve identity and exact 4 by 2 part arrangement, but correct the following mistakes. Cell 4 torso MUST be a plain round original gold-brown body, with smooth convex top and bottom. NO neck stump/collar/rim, NO legs, NO wings, NO tail painted into body. Cell 5 ONE small original three-tipped folded wing. Round solid root at TOP RIGHT, three tips extend down LEFT. Wing has only THREE feather tips; same source gold palette, no invented taupe wing-tip stripes. Cell 7 remains the original FIVE round-tipped fan feathers, source color bands.'
    if direction=='Up':
        prompt+=chr(10)+'CRITICAL rear head fix: the original turkey has absolutely NO EARS or side appendages. Cells 1/2/3 are the smooth plain rear of a long pale gold head and neck with pointed neck ruff only. Entire rear head/neck silhouette has smooth sides: NO little lobes, wings, wattles, beak, eyes or round ear ornaments on either side. All three back heads IDENTICAL plain gold, no different scars. Cell 6 rear leg ends in a PLAIN ROUNDED GOLDEN HEEL with NO claws or toenails facing viewer. The three front toes extend AWAY behind the ankle and are hidden/foreshortened; do NOT draw a three-lobed front foot or claw tips on the rear surface.'
    else:
        prompt+=chr(10)+'Preserve existing three correct centered front head/neck expressions and exactly ONE long side gold wattle; no X eyes. Front foot remains three gold toes and small ivory claws. Fix only torso lower duplicate leg shapes and wing root/anatomy.'
    (p/'prompt.txt').write_text(prompt,encoding='utf-8')
