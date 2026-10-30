from pathlib import Path
import hashlib,json
from PIL import Image,ImageFilter
import numpy as np
D=Path(__file__).resolve().parent;out=D/'local_raster_revision_02';assert not out.exists()
raw=D/'generation/Up/raw.png';im=Image.open(raw).convert('RGB');a=np.asarray(im).copy();before=a.copy()
v=a.astype('int16');fg=(v[:,:,2]<=v[:,:,1]+8)&(v[:,:,2]<=v[:,:,0]+12)&((v[:,:,0]-v[:,:,1])<=(v[:,:,1]-v[:,:,2])+26)
interior=np.asarray(Image.fromarray(fg.astype('uint8')*255).filter(ImageFilter.MinFilter(15)))>0
region=np.zeros(fg.shape,dtype=bool);region[96:175,1273:1378]=True
mask=interior&region;a[mask]=a[185,1320]
patched=Image.fromarray(a)
# Reuse the complete same-sheet rear-facing leg so there is no ankle splice.
hind=im.crop((492,609,657,865));patched.paste((255,0,255),(97,609,276,875));patched.paste(hind,(106,609))
out.mkdir();patched.save(out/'Up_sheet.png')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
changed=np.any(np.asarray(patched)!=before,axis=2)
(out/'processing.json').write_text(json.dumps(dict(parent='generation/Up/raw.png',parent_sha256=sha(raw),output='Up_sheet.png',output_sha256=sha(out/'Up_sheet.png'),method='Local raster derivation, not AI return: fill hollow neck interior with same-sheet wool cream retaining original closed outer outline; use intact same-sheet rear-facing hind leg for foreleg to preserve one continuous ankle.',neck_region=[1273,96,1378,175],neck_pixels=int(mask.sum()),leg_source=[492,609,657,865],leg_destination=[106,609,271,865],changed_pixels=int(changed.sum()),raw_unchanged=True,rejects='local_raster_revision_01 has a block edge and partial ring remaining; retained and not selected'),indent=2)+'\n',encoding='utf-8')
(D/'local_raster_revision_01/rejected.json').write_text(json.dumps(dict(reason='Actual preview still showed a ring opening/block fill and an ankle splice edge. Do not select.',replaced_by='local_raster_revision_02'),indent=2)+'\n',encoding='utf-8')
review=Image.new('RGB',(900,650),(40,48,37));review.paste(patched.crop((1140,80,1510,525)).resize((444,534)),(5,5));review.paste(patched.crop((95,605,275,875)).resize((270,405)),(535,100));review.save(out/'repair_preview.png')
print(json.dumps(dict(parent_sha256=sha(raw),output_sha256=sha(out/'Up_sheet.png'),changed=int(changed.sum()))))
