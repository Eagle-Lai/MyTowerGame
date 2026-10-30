"""Refine the r01 pixel repair after actual image review; no paid requests."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np, json, hashlib
D=Path(__file__).resolve().parent
O=D/'local_raster_revision_02';O.mkdir(exist_ok=False)
records=[]
for direction,relative in [('Up','generation/Up/revision_02/raw.png'),('Down','generation/Down/raw.png')]:
    p=D/relative;im=Image.open(p).convert('RGB');a=np.array(im);before=a.copy()
    if direction=='Up':
        for x0,y0,x1,y1 in [(110,560,285,840),(440,550,660,845)]:
            b=a[y0:y1,x0:x1];v=b.astype('int16')
            fg=(v[:,:,2]<=v[:,:,1]+8)&(v[:,:,2]<=v[:,:,0]+12)&((v[:,:,0]-v[:,:,1])<=(v[:,:,1]-v[:,:,2])+26)
            inside=np.array(Image.fromarray((fg*255).astype('uint8')).filter(ImageFilter.MinFilter(9)))>220
            yy,xx=np.indices(fg.shape);region=inside&(yy+y0>=785)
            mix=np.clip((yy+y0-785)/5,0,1)
            for c,(left,right) in enumerate([(142,116),(125,99),(84,64)]):
                target=left+(right-left)*np.clip(xx/(x1-x0),0,1)
                b[:,:,c][region]=(b[:,:,c][region]*(1-mix[region])+target[region]*mix[region]).astype('uint8')
        note='r01 review still showed toe lines: use complete foreground silhouette for erosion, including dark interior lines; retain 4px outer contour.'
    else:
        for off,dead in [(0,False),(386,False),(775,True)]:
            mask=Image.new('L',im.size);draw=ImageDraw.Draw(mask)
            # Follow the inner head outline, cover the entire invented plaque edge.
            poly=[(109,173),(248,171),(281,225),(270,249),(235,253),(211,266),(178,256),(152,263),(123,249),(98,249),(86,220)]
            if dead: poly=[(116,174),(253,172),(288,217),(271,246),(241,242),(220,258),(189,247),(164,256),(136,244),(108,246),(95,216)]
            draw.polygon([(x+off,y) for x,y in poly],fill=255)
            m=np.array(mask.filter(ImageFilter.GaussianBlur(2.2)))/255
            yy,xx=np.indices(m.shape)
            blend=np.clip((yy-175)/95,0,1)
            for c,(top,bottom) in enumerate([(146,137),(128,119),(86,79)]):
                target=top+(bottom-top)*blend
                a[:,:,c]=(a[:,:,c]*(1-m)+target*m).astype('uint8')
        repaired=Image.fromarray(a);draw=ImageDraw.Draw(repaired)
        for off,cy in [(0,198),(386,198),(775,196)]:
            for cx in [128+off,231+off]:
                draw.polygon([(cx-18,cy+14),(cx-8,cy-18),(cx+17,cy+9),(cx+9,cy+20)], fill=(46,41,25))
                draw.polygon([(cx-10,cy+10),(cx-5,cy-6),(cx+8,cy+9),(cx+5,cy+13)], fill=(232,177,63))
                draw.polygon([(cx-10,cy+10),(cx-5,cy-6),(cx+2,cy+2)], fill=(255,220,136))
        a=np.array(repaired)
        note='r01 review showed a hard patch boundary: blend coherent olive forehead cel planes and use small triangular gold chips. Preserve all facial expressions.'
    result=Image.fromarray(a);dest=O/(direction+'.png');result.save(dest)
    yy,xx=np.where(np.any(before!=a,axis=2))
    records.append(dict(direction=direction,parent=relative,parent_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),output=dest.relative_to(D).as_posix(),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),changed_pixels=len(xx),bounds=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],method=note))
(O/'processing.json').write_text(json.dumps(dict(records=records,review='pending',supersedes='local_raster_revision_01; preserved'),indent=2)+'\n',encoding='utf-8')
