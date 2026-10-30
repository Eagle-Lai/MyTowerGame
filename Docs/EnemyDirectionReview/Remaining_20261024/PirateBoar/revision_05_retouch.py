"""Repair the viewed rear-ear artifact and stage one character only."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib, json, shutil
HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
backup = HERE/'generation/selection_before_revision_05'
backup.mkdir(exist_ok=False)
for name in ['art_selection.json','layout_adjustments.json','processing.json','offline_Up.png','offline_Down.png','offline_rig_proof.png']:
    shutil.copy2(HERE/name, backup/name)
source = HERE/'generation/Up/revision_03/raw.png'
dest = HERE/'generation/Up/revision_05'
dest.mkdir(exist_ok=False)
im = Image.open(source).convert('RGB')
draw = ImageDraw.Draw(im)
for offset in [0,384,768]:
    def points(ps): return [(x+offset,y) for x,y in ps]
    # Remove the second earring outside the intact ear/head contour.
    draw.polygon(points([(340,275),(370,275),(370,370),(325,370),(319,347),(317,332),(324,318),(335,304)]), fill=(255,0,255))
    # Restore one closed solid outer ear behind the skull, no inner pad.
    draw.polygon(points([(287,266),(310,252),(335,247),(346,248),(347,264),(343,287),(335,307),(324,320),(313,321),(305,302)]), fill=(77,58,26))
    draw.polygon(points([(297,270),(316,260),(338,256),(337,278),(331,297),(321,309),(314,309),(311,291)]), fill=(178,126,34))
    # Image-left keeps the sole original gold ring; cover only inner pad.
    draw.polygon(points([(53,258),(62,258),(77,266),(84,279),(75,287),(66,277)]), fill=(178,126,34))
im.save(dest/'raw.png')
operation={'revision':'revision_05','method':'deterministic bounded polygon pixel retouch; no AI/API call',
           'parent':'generation/Up/revision_03/raw.png','parent_sha256':sha(source),'sha256':sha(dest/'raw.png'),
           'bounded_regions_per_head':[[287,247,370,370],[53,258,84,287]],
           'preserved':'single image-left ring, hat, skull/back contour, torso, legs and cannon unchanged',
           'reason':'revision_04 cut horizontal slots; restore closed bare right ear, remove second ring, cover rear-facing inner pads',
           'pending_visual_check':True}
(dest/'patch.json').write_text(json.dumps(operation,indent=2)+'\n',encoding='utf-8')
selection=json.loads((HERE/'art_selection.json').read_text(encoding='utf-8'))
selection.update(Up='generation/Up/revision_05/raw.png',revision='Up_revision_05_Down_revision_04',review_basis='bounded repair of viewed rear-ear artifacts; new staged review required')
(HERE/'art_selection.json').write_text(json.dumps(selection,indent=2)+'\n',encoding='utf-8')
layout=json.loads((HERE/'layout_adjustments.json').read_text(encoding='utf-8'))
layout['revision']='layout_revision_02'
layout['reason']+=' Rear head must remain visibly connected ahead of cannon, not hidden under torso. Scale broad head to original proportions.'
layout['parts']['Up/Head'].update(y=.67,width=.64,height=.43,order=25)
layout['parts']['Down/Head'].update(y=.28,width=.68,height=.46,order=35)
(HERE/'layout_adjustments.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(operation))
