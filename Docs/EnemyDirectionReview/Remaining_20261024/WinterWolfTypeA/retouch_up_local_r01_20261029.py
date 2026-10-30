from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,hashlib
HERE=Path(__file__).resolve().parent
src=HERE/'generation/Up/raw.png';out=HERE/'generation/Up/local_revision_01';assert not out.exists();out.mkdir()
image=Image.open(src).convert('RGB');before=np.array(image)
draw=ImageDraw.Draw(image)
draw.rectangle((1243,65,1418,126),fill=(255,0,255))
crest=[(1243,133),(1254,125),(1273,116),(1293,108),(1314,101),(1334,99),(1353,102),(1374,109),(1397,120),(1418,133)]
draw.polygon(crest+[(1418,143),(1243,143)],fill=(232,226,212))
draw.line(crest,fill=(46,34,15),width=8,joint='curve')
array=np.array(image)
wide=array.astype(np.int16)
foreground=(wide[:,:,1]>wide[:,:,2]-20)&(wide[:,:,2]<wide[:,:,0]+30)&(wide[:,:,1]>35)
inside=np.asarray(Image.fromarray(foreground.astype(np.uint8)*255).filter(ImageFilter.MinFilter(17)))>0
regions=[(134,821,165,872),(171,823,197,877),(484,833,514,887),(516,837,552,892)]
total=0
for x0,y0,x1,y1 in regions:
    local=np.zeros(array.shape[:2],bool);local[y0:y1,x0:x1]=True
    dark=(array[:,:,0]<155)&(array[:,:,1]<145)&(array[:,:,2]<125)
    mask=(np.asarray(Image.fromarray((local&dark).astype(np.uint8)*255).filter(ImageFilter.MaxFilter(5)))>0)&local&inside
    if not mask.any():continue
    sample=np.zeros(array.shape[:2],bool);sample[max(0,y0-20):y1+20,max(0,x0-20):x1+20]=True
    valid=sample&~mask&(array[:,:,1]>150)&(wide[:,:,2]<=wide[:,:,1]+20)&inside
    coordinates=np.argwhere(valid)
    for yy,xx in np.argwhere(mask):
        sy,sx=coordinates[np.argmin(np.sum((coordinates-np.array([yy,xx]))**2,axis=1))]
        array[yy,xx]=array[sy,sx]
    total+=int(mask.sum())
image=Image.fromarray(array);image.save(out/'raw.png')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
report={'parent':'generation/Up/raw.png','parent_sha256':sha(src),'output':'generation/Up/local_revision_01/raw.png','output_sha256':sha(out/'raw.png'),'type':'local raster correction, not an AI response','regions':[{'box':[1243,65,1419,144],'reason':'Remove two duplicate ear-like brown protrusions from BODY only; close collar with plain ivory convex shoulder edge and dark original-style outline.'},{'boxes':regions,'reason':'Remove interior toe-division strokes from rear heel pieces using nearest surrounding original ivory/taupe pixels; protect exterior dark boundary by eight pixels.','pixels':total}],'changed_pixels':int(np.any(array!=before,axis=2).sum()),'original_raw_preserved':True,'requires_visual_review':True}
(out/'processing.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
image.crop((100,590,690,910)).resize((1180,640)).save(HERE/'up_heels_review_local_r01.png')
image.crop((1170,65,1495,510)).resize((520,712)).save(HERE/'up_body_review_local_r01.png')
print(json.dumps(report,ensure_ascii=False))
