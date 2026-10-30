from pathlib import Path
import hashlib,json
from PIL import Image,ImageFilter
import numpy as np
D=Path(__file__).resolve().parent;out=D/'local_raster_revision_01';assert not out.exists()
raw=D/'generation/Up/raw.png';im=Image.open(raw).convert('RGB');a=np.asarray(im).copy();before=a.copy()
# Close only the hollow neck's interior; retain the outer dark silhouette.
fg=(a[:,:,1]>30)&(a[:,:,2]<a[:,:,1]+30)
interior=np.asarray(Image.fromarray(fg.astype('uint8')*255).filter(ImageFilter.MinFilter(15)))>0
region=np.zeros(interior.shape,dtype=bool);region[96:171,1273:1378]=True
mask=interior&region
cream=a[185,1320].copy();a[mask]=cream
# Same-sheet rear hind hoof replaces the forward-cleft fore hoof only.
heel=Image.fromarray(before).crop((524,798,624,858)).resize((105,60),Image.Resampling.LANCZOS)
patched=Image.fromarray(a);patched.paste(heel,(132,798))
out.mkdir();patched.save(out/'Up_sheet.png')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
changed=np.any(np.asarray(patched)!=before,axis=2);ys,xs=np.where(changed)
(out/'processing.json').write_text(json.dumps(dict(parent='generation/Up/raw.png',parent_sha256=sha(raw),output='Up_sheet.png',output_sha256=sha(out/'Up_sheet.png'),method='Local same-sheet raster derivation, not an AI return. Fill neck-ring interior with wool cream sampled at (1320,185) retaining existing silhouette; copy intact rear heel to fore hoof.',neck_region=[1273,96,1378,171],neck_pixels=int(mask.sum()),heel_source=[524,798,624,858],heel_destination=[132,798,237,858],changed_pixels=int(changed.sum()),changed_bounds=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],raw_unchanged=True),indent=2)+'\n',encoding='utf-8')
review=Image.new('RGB',(900,650),(40,48,37));review.paste(patched.crop((1140,80,1510,525)).resize((444,534)),(5,5));review.paste(patched.crop((95,605,275,875)).resize((270,405)),(535,100));review.save(out/'repair_preview.png')
print(json.dumps(dict(parent_sha256=sha(raw),output_sha256=sha(out/'Up_sheet.png'),changed=int(changed.sum()))))
