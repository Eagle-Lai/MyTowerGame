"""Fill only isolated chroma-removal pinholes in derived native parts and the atlas."""
from session_tiger import *
from PIL import Image, ImageDraw
import numpy as np

owner()
art=D/'staged_art';atlas_path=art/'Tiger_Directions.png';atlas=Image.open(atlas_path).convert('RGBA')
manifest=read(art/'Tiger_Directions.sprites.json');records=[]
for s in manifest['sprites']:
    p=art/(s['name']+'.png');im=Image.open(p).convert('RGBA');a=np.array(im)
    mask=Image.fromarray(np.where(a[:,:,3]==0,255,0).astype('uint8'));pad=Image.new('L',(im.width+2,im.height+2),255);pad.paste(mask,(1,1));ImageDraw.floodfill(pad,(0,0),127)
    ys,xs=np.where(np.array(pad)[1:-1,1:-1]==255)
    assert len(xs)<=16, (p.name,len(xs))
    original=a.copy()
    for x,y in zip(xs,ys):
        candidates=[]
        for yy in range(max(0,y-3),min(im.height,y+4)):
            for xx in range(max(0,x-3),min(im.width,x+4)):
                if original[yy,xx,3]==255:candidates.append(((xx-x)**2+(yy-y)**2,yy,xx))
        assert candidates
        _,yy,xx=min(candidates);a[y,x]=original[yy,xx]
    if len(xs):
        fixed=Image.fromarray(a,'RGBA');fixed.save(p)
        atlas.paste(fixed,(s['x'],2048-s['y']-s['h']))
    records.append(dict(part=p.name,filled=len(xs),coordinates=[[int(x),int(y)] for x,y in zip(xs,ys)],before_sha256=hashlib.sha256(original.tobytes()).hexdigest(),after_file_sha256=sha(p)))
atlas.save(atlas_path)
write(D/'chroma_pinhole_repair_20261028.json',dict(observed_at=now(),method='Fill only transparent pixels unreachable from the exterior, using the nearest original opaque neighbor within 3 pixels. Native part and atlas copies updated together; raw paid images and all outside pixels preserved.',total=sum(r['filled'] for r in records),parts=records,atlas_sha256=sha(atlas_path)))
print(json.dumps(dict(total_filled=sum(r['filled'] for r in records),production_changes=0)))
