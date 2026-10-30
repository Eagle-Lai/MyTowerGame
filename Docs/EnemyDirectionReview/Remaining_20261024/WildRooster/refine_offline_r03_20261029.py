"""Refine visible local cap seams and fuse tail root; retain r02 evidence."""
from PIL import Image, ImageDraw
import numpy as np
import shutil, subprocess, sys
from checkpoint_20261029 import D,H,NAME,owner,read,write,sha,now
owner();assert not (D/'installed_manifest.json').exists()
old=D/'offline_r02';old.mkdir();shutil.copytree(D/'staged_art',old/'staged_art')
for p in ['offline_Up.png','offline_Down.png','offline_rig_proof.png']:shutil.copy2(D/p,old/p)
write(old/'rejected.json',{'at':now(),'reason':'Actually viewed r02: local cap has a horizontal paint transition, and cropped Up tail root/left edge are visibly rectangular. Not installed.'})
out=D/'local_raster_r03';out.mkdir();art=D/'staged_art'
def bez(a,b,c,d):
    return [tuple((1-t)**3*a[k]+3*(1-t)**2*t*b[k]+3*(1-t)*t*t*c[k]+t**3*d[k] for k in range(2)) for t in np.linspace(0,1,50)]
bodies={}
for direction,cut,fill in [('Up',160,(222,144,9,255)),('Down',230,(211,136,10,255))]:
    src=Image.open(D/'offline_r01/staged_art'/(direction+'_Body.png')).convert('RGBA');a=np.array(src)
    xs=np.where(a[cut,:,3]>200)[0];l,r=int(xs.min()),int(xs.max());cx=(l+r)/2
    outline=tuple(a[cut,l,:3].tolist())+(255,)
    cap=Image.new('RGBA',(src.width*4,src.height*4));draw=ImageDraw.Draw(cap)
    boundary=bez((l+5,cut+5),(l,118),(cx-45,83),(cx,83))+bez((cx,83),(cx+45,83),(r,118),(r-5,cut+5))
    draw.polygon([(round(x*4),round(y*4)) for x,y in boundary+[(r-5,cut+35),(l+5,cut+35)]],fill=fill)
    draw.line([(round(x*4),round(y*4)) for x,y in boundary],fill=outline,width=40,joint='curve')
    cap=cap.resize(src.size,Image.Resampling.LANCZOS)
    lower=np.array(src.crop((0,cut+4,src.width,src.height)))
    for y in range(min(30,lower.shape[0])):
        w=y/29
        inside=(lower[y,:,3]>0)&(lower[y,:,:3].max(axis=1)>80)
        lower[y,inside,:3]=np.round((1-w)*np.array(fill[:3])+w*lower[y,inside,:3]).astype(np.uint8)
    cap.alpha_composite(Image.fromarray(lower),(0,cut+4))
    if direction=='Up':
        tail=src.crop((0,0,src.width,132));ta=np.array(tail)
        for y in range(105,132):ta[y,:,3]=(ta[y,:,3].astype(float)*(131-y)/26).astype(np.uint8)
        tail=Image.fromarray(ta);tail=tail.crop(tail.getbbox());tail.thumbnail((188,145),Image.Resampling.LANCZOS)
        cap.alpha_composite(tail,((src.width-tail.width)//2,219))
    body=cap.crop(cap.getbbox());body.save(out/(direction+'_Body.png'));body.save(art/(direction+'_Body.png'));bodies[direction]=body
spec=read(art/(NAME+'_Directions.sprites.json'));atlas=Image.new('RGBA',(2048,2048));x=y=8;row_h=0
for s in spec['sprites']:
    im=Image.open(art/(s['name']+'.png')).convert('RGBA')
    if x+im.width+8>2048:x=8;y+=row_h+8;row_h=0
    atlas.alpha_composite(im,(x,y));s.update(x=x,y=2048-y-im.height,w=im.width,h=im.height);x+=im.width+8;row_h=max(row_h,im.height)
atlas.save(art/(NAME+'_Directions.png'));write(art/(NAME+'_Directions.sprites.json'),spec)
write(out/'manifest.json',{'at':now(),'revision':'art_r03','parent':'local_raster_r02/manifest.json','method':'Retain original returned lower torso, blend cap paint over thirty interior rows; copy the entire three-feather tuft silhouette before alpha-fusing only its last 27 root rows into the rump. No side-view transformation; generated Up/Down raw unchanged.','files':{p.name:sha(p) for p in art.glob(NAME+'_Directions.*')},'raws':{d:sha(D/'generation'/d/'raw.png') for d in ['Up','Down']}})
subprocess.run([sys.executable,str(H/'render_staged_rig.py'),NAME],check=True)
proof=Image.new('RGB',(1200,500),(40,48,37));draw=ImageDraw.Draw(proof)
for i,d in enumerate(['Up','Down']):
    im=bodies[d];proof.paste(im,(i*600+(600-im.width)//2,45),im);draw.text((i*600+20,12),d+' Body local r03 - not raw',fill='white')
proof.save(out/'body_review.png')
print('r03 preserves rejected r01/r02 and awaits actual visual review')
