"""Reuse this generated sheet's intact round middle-leg joint to repair its contaminated front root."""
from pathlib import Path
from PIL import Image,ImageDraw
from datetime import datetime,timezone,timedelta
import numpy as np,json,hashlib,shutil
D=Path(__file__).resolve().parent
out=D/'local_raster_revision_01';out.mkdir(exist_ok=False)
before=D/'offline_staging_r01';before.mkdir()
for n in ['parts_clean.png','offline_rig_proof.png','offline_Up.png','offline_Down.png','processing.json','art_selection.json','layout_adjustments.json']:shutil.copy2(D/n,before/n)
raw=Image.open(D/'generation/Down/revision_03/raw.png').convert('RGB');image=raw.copy()
source=(812,592,881,661);destination=(332,558)
joint=raw.crop(source);mask=Image.new('L',joint.size,0);ImageDraw.Draw(mask).ellipse((0,0,68,68),fill=255)
image.paste(joint,destination,mask)
# Discard only the red/magenta contaminated right/top edge of the old round cap.
a=np.asarray(image).copy();old=np.asarray(raw);yy,xx=np.indices(a.shape[:2])
cap=(xx>=332)&(xx<=403)&(yy>=555)&(yy<=627)
ellipse=((xx-366)/34)**2+((yy-592)/34)**2<=1
red=(old[:,:,0].astype(int)>old[:,:,1].astype(int)+40)&(old[:,:,2].astype(int)>old[:,:,1].astype(int)-5)
a[cap&~ellipse&red]=[255,0,255]
image=Image.fromarray(a,'RGB');image.save(out/'Down_sheet.png')
proof=Image.new('RGB',(640,320),(40,48,37))
for col,im in enumerate([raw,image]):proof.paste(im.crop((315,540,420,645)).resize((315,315),Image.Resampling.NEAREST),(col*320,0))
proof.save(out/'root_before_after.png')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
record=dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),parent='generation/Down/revision_03/raw.png',parent_sha256=sha(D/'generation/Down/revision_03/raw.png'),output='local_raster_revision_01/Down_sheet.png',output_sha256=sha(out/'Down_sheet.png'),method='Copy only the intact circular root cap of this same sheet middle leg into front root cap; remove only contaminated red/magenta residual at outer rim. No whole leg/body rotation, stretch or synthetic view.',source_rect=source,destination=destination,mask='69px round joint ellipse',affected_region=[332,555,404,628],unchanged=['All head states and antennae','Single saddle and body','Other legs and all feet tips','Generated original raw and request outcomes'],status='pending_actual_visual_review',ai_generated_original=False)
(out/'processing.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
s=json.loads((D/'art_selection.json').read_text(encoding='utf-8'));s['Down']='local_raster_revision_01/Down_sheet.png';s['reason']+=' Down front-root-only local copy repair from intact own middle root; original raw preserved.';(D/'art_selection.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False))
