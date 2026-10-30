from session_tiger import *
from PIL import Image, ImageOps

owner(); assert inventory()==read(D/'incremental_before_20261028.json')['files']
out=D/'local_raster_revision_01';assert not out.exists();out.mkdir()
up=D/'generation/Up/revision_01/raw.png';down=D/'generation/Down/raw.png'
assert read(up.with_name('result.json'))['status']==200 and read(down.with_name('result.json'))['status']==200
im=Image.open(up).convert('RGB');before=im.copy()
# The inspected lower-right side claw is inappropriate in the back view. The left half
# of this same heel is intact; mirror only that heel, preserving the hip and upper leg.
rect=(582,810,710,910)
im.paste((255,0,255),rect)
heel=ImageOps.mirror(before.crop((520,810,582,910)))
im.paste(heel,(582,810));im.save(out/'Up_sheet.png')
detail=im.crop((500,760,710,920)).resize((630,480),Image.Resampling.NEAREST);detail.save(out/'heel_detail_after.png')
write(out/'derivation.json',dict(created_at=now(),method='Local raster mirror of the intact left half of the same rear heel, with magenta outside; no new API request.',parent='generation/Up/revision_01/raw.png',parent_sha256=sha(up),output_sha256=sha(out/'Up_sheet.png'),changed_rect=list(rect),mirror_source_rect=[520,810,582,910],preserved='All pixels outside changed_rect, all head/body/tail/upper leg art and the original paid image remain intact.',review='Pending actual patched detail and final staged rig review'))
write(D/'art_selection.json',dict(Up='local_raster_revision_01/Up_sheet.png',Down='generation/Down/raw.png',selection_note='Actual Up revision_01 and initial Down HTTP200 PNGs viewed. Rear hind heel side claw removed locally; all original results preserved. Pending sliced/pivot/assembled review.'))
write(D/'generation/Down/review_20261028.json',dict(observed_at=now(),source='generation/Down/raw.png',method='Actual full returned PNG viewed',observations=['Normal stern eyes, attack open mouth with ivory canines, dead blank round eyes and ochre tongue; all centered front view.','One pair of round ears and cream ruff on each head; striped axial torso, separate fore/hind legs with front claws, thin striped tail.','No extra feet/face on body; neck ruff will be overlapped by the head in assembly.'],accepted_for_staging=True,approval='Internal staging only, not user approval or runtime completion'))
print(json.dumps(dict(Up='local_raster_revision_01',Down='initial',production_changes=0)))
