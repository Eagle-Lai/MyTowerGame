from serial_common import *
from PIL import Image,ImageDraw
import numpy as np,shutil
owner()
A=D/'staged_art';R=D/'raster_revision_02';R.mkdir()
for p in A.iterdir():
    if p.is_file():shutil.copy2(p,R/p.name)
shutil.copy2(D/'offline_rig_proof.png',R/'offline_rig_proof.png')
for direction in ['Up','Down']:
    p=A/(direction+'_Body.png');im=Image.open(p).convert('RGBA');w,h=im.size
    if direction=='Up':
        cone=im.crop((137,0,214,94));regions=[(24,54,120,156),(231,54,328,157),(129,0,220,101)]
        oval=(0,48,w-1,h-1);locations=[(178,112,.62),(178,200,.82),(178,295,1)]
    else:
        cone=im.crop((103,0,177,87));regions=[(99,0,180,91),(90,86,186,170),(0,93,58,170),(226,93,281,172),(33,36,93,93),(199,35,246,94)]
        oval=(13,40,w-14,h-1);locations=[(140,104,.70),(140,184,.90),(140,267,1)]
    cm=Image.new('L',cone.size,0);cd=ImageDraw.Draw(cm)
    cw,ch=cone.size
    cd.polygon([(cw*.5,0),(cw*.76,ch*.13),(cw-1,ch*.83),(cw*.92,ch*.96),(cw*.67,ch-1),(cw*.25,ch-1),(0,ch*.87),(cw*.10,ch*.48),(cw*.31,ch*.10)],fill=255)
    ca=np.asarray(cone).copy();ca[:,:,3]=np.minimum(ca[:,:,3],np.asarray(cm));cone=Image.fromarray(ca)
    mask=Image.new('L',im.size,0);md=ImageDraw.Draw(mask)
    for box in regions:md.rectangle(box,fill=255)
    inside=Image.new('L',im.size,0);ImageDraw.Draw(inside).ellipse(oval,fill=255)
    valid=np.asarray(inside)>0;a=np.asarray(im).copy();holes=(np.asarray(mask)>0)|((a[:,:,3]==0)&valid)
    holes &= valid
    rgb=a[:,:,:3].astype(np.float32);rgb[holes]=(211,151,37)
    # Local harmonic color fill from neighboring generated shell colors; no new image API request.
    weight=np.zeros((h,w),np.float32)
    for dy,dx in [(1,0),(-1,0),(0,1),(0,-1)]:weight+=np.roll(valid,(dy,dx),(0,1))
    for iteration in range(900):
        total=np.zeros_like(rgb)
        for dy,dx in [(1,0),(-1,0),(0,1),(0,-1)]:total+=np.roll(rgb*valid[:,:,None],(dy,dx),(0,1))
        rgb[holes]=(total/np.maximum(weight[:,:,None],1))[holes]
    a[:,:,:3]=np.clip(rgb,0,255).astype(np.uint8);a[:,:,3]=np.asarray(inside)
    result=Image.fromarray(a);ImageDraw.Draw(result).ellipse(oval,outline=(54,43,22,255),width=6)
    for cx,base,ratio in locations:
        piece=cone.resize((round(cone.width*ratio),round(cone.height*ratio)),Image.Resampling.LANCZOS)
        result.alpha_composite(piece,(round(cx-piece.width/2),round(base-piece.height)))
    result.save(p)
m=read(A/(NAME+'_Directions.sprites.json'));atlas=Image.new('RGBA',(2048,2048))
for s in m['sprites']:atlas.alpha_composite(Image.open(A/(s['name']+'.png')),(s['x'],2048-s['y']-s['h']))
atlas.save(A/(NAME+'_Directions.png'))
la=read(D/'layout_adjustments.json');la['parts']['Down/Tail'].update(y=.40,width=.45,height=.63)
write(D/'layout_adjustments.json',la)
write(R/'retouch_record.json',dict(observed_at=now(),parent='raster_revision_01',method='Local generated-shell inpainting removes lateral surplus body spines and repositions three existing ivory spine cutouts along the axial segmented back, matching source three-spine torso. Original paid sheets unchanged.',final_staged={p.name:sha(p) for p in A.iterdir() if p.is_file()}))
