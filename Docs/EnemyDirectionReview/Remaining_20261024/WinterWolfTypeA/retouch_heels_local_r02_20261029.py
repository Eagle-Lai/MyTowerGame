from pathlib import Path
from PIL import Image,ImageFilter
import numpy as np,json,hashlib
HERE=Path(__file__).resolve().parent;src=HERE/'generation/Up/local_revision_01/raw.png';out=HERE/'generation/Up/local_revision_02';assert not out.exists();out.mkdir()
array=np.array(Image.open(src).convert('RGB'));before=array.copy();wide=array.astype(np.int16)
fg=(wide[:,:,2]<=wide[:,:,1]+8)&(wide[:,:,2]<=wide[:,:,0]+12)&((wide[:,:,0]-wide[:,:,1])<=(wide[:,:,1]-wide[:,:,2])+26)
inside=np.asarray(Image.fromarray(fg.astype(np.uint8)*255).filter(ImageFilter.MinFilter(9)))>0
regions=[(119,811,247,880),(475,821,638,895)];total=0
for x0,y0,x1,y1 in regions:
    region=np.zeros(fg.shape,bool);region[y0:y1,x0:x1]=True
    dark=(array[:,:,0]<160)&(array[:,:,1]<150)&(array[:,:,2]<130)
    mask=(np.asarray(Image.fromarray((region&dark).astype(np.uint8)*255).filter(ImageFilter.MaxFilter(3)))>0)&region&inside
    samples=region&inside&~mask&(array[:,:,1]>160)&(wide[:,:,2]<wide[:,:,1]+20)
    coords=np.argwhere(samples)
    for yy,xx in np.argwhere(mask):
        sy,sx=coords[np.argmin(np.sum((coords-np.array([yy,xx]))**2,axis=1))];array[yy,xx]=array[sy,sx]
    total+=int(mask.sum())
im=Image.fromarray(array);im.save(out/'raw.png');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
(out/'processing.json').write_text(json.dumps({'parent':str(src.relative_to(HERE)),'parent_sha256':sha(src),'output_sha256':sha(out/'raw.png'),'method':'Local raster repair of remaining rear toe strokes only; nearest original ivory/taupe pixel samples and four-pixel protected outer border. No AI response fabricated.','regions':regions,'pixels':int(np.any(before!=array,axis=2).sum()),'previous_version':'Preserved; earlier mask left obvious toe-stroke stubs and was visually rejected.'},indent=2)+'\n',encoding='utf-8')
im.crop((100,590,690,910)).resize((1180,640)).save(HERE/'up_heels_review_local_r02.png')
print(total)
