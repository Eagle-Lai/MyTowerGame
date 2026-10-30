from pathlib import Path
from PIL import Image,ImageFilter
import numpy as np,json,hashlib
HERE=Path(__file__).resolve().parent;src=HERE/'generation/Up/local_revision_02/raw.png';out=HERE/'generation/Up/local_revision_03';assert not out.exists();out.mkdir()
a=np.array(Image.open(src).convert('RGB'));before=a.copy();wide=a.astype(np.int16)
fg=(wide[:,:,2]<=wide[:,:,1]+8)&(wide[:,:,2]<=wide[:,:,0]+12)&((wide[:,:,0]-wide[:,:,1])<=(wide[:,:,1]-wide[:,:,2])+26)
inside=np.asarray(Image.fromarray(fg.astype(np.uint8)*255).filter(ImageFilter.MinFilter(9)))>0
for x0,y0,x1,y1 in [(119,813,247,880),(475,824,638,895)]:
    region=np.zeros(fg.shape,bool);region[y0:y1,x0:x1]=True
    mask=region&inside
    # Original broad cream cel shading is used; nearest-neighbor reconstruction in r02
    # left a mottled heel, so replace that lower heel fill with one source ivory color.
    a[mask]=[235,229,216]
im=Image.fromarray(a);im.save(out/'raw.png');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
(out/'processing.json').write_text(json.dumps({'parent':str(src.relative_to(HERE)),'parent_sha256':sha(src),'output_sha256':sha(out/'raw.png'),'method':'Only smooth lower rear heel interiors to one original-style ivory cel shade; four-pixel exterior boundary protected. All previous raw and failed local versions retained.','changed_pixels':int(np.any(a!=before,axis=2).sum()),'reason':'r02 removed toe lines but left mottled fill.','requires_visual_review':True},indent=2)+'\n',encoding='utf-8')
im.crop((100,590,690,910)).resize((1180,640)).save(HERE/'up_heels_review_local_r03.png')
