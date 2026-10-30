from serial_common import *
from PIL import Image, ImageDraw, ImageFilter
import numpy as np, shutil, math
owner()
R=D/'raster_revision_01';R.mkdir()
A=D/'staged_art'
for p in A.iterdir():
    if p.is_file():shutil.copy2(p,R/p.name)
for p in ['offline_rig_proof.png','offline_Up.png','offline_Down.png','parts_clean.png']:
    shutil.copy2(D/p,R/p)
changes=[]
# Remove only the two invented lateral rear-head spikes; preserve rear brow-horn silhouettes.
im=Image.open(A/'Up_HeadNormal.png').convert('RGBA')
w,h=im.size
mask=Image.new('L',im.size,0); dr=ImageDraw.Draw(mask)
dr.polygon([(0,0),(w,0),(w,78),(211,78),(216,112),(213,160),(201,198),(177,214),(127,222),(79,214),(57,195),(46,160),(42,113),(48,78),(0,78)],fill=255)
arr=np.asarray(im).copy();arr[:,:,3]=np.minimum(arr[:,:,3],np.asarray(mask))
im=Image.fromarray(arr)
dr=ImageDraw.Draw(im)
dr.line([(48,78),(43,111),(46,157),(57,190)],fill=(54,43,22,255),width=6)
dr.line([(211,78),(215,111),(212,157),(201,190)],fill=(54,43,22,255),width=6)
for name in ['Up_HeadNormal','Up_HeadAngry','Up_HeadDead']:
    im.save(A/(name+'.png'));changes.append(name)
# Keep the largest opaque component in each slice: small chroma-edge flecks are not anatomy.
for p in A.glob('*.png'):
    if p.name.startswith('RedScorpion_'):continue
    piece=Image.open(p).convert('RGBA');a=np.asarray(piece).copy();opaque=a[:,:,3]>0
    seen=np.zeros(opaque.shape,bool);components=[]
    for yy,xx in zip(*np.where(opaque)):
        if seen[yy,xx]:continue
        todo=[(int(yy),int(xx))];seen[yy,xx]=True;comp=[]
        while todo:
            y,x=todo.pop();comp.append((y,x))
            for dy,dx in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                ny,nx=y+dy,x+dx
                if 0<=ny<a.shape[0] and 0<=nx<a.shape[1] and opaque[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;todo.append((ny,nx))
        components.append(comp)
    removed=[]
    for comp in components:
        if len(comp)<70:
            for y,x in comp:a[y,x]=0
            removed.append(len(comp))
    if removed:Image.fromarray(a).save(p);changes.append(dict(piece=p.name,removed_isolated_pixel_groups=removed))
# Repack unchanged slice rectangles; original paid PNGs and prior staged atlas remain in R.
m=read(A/(NAME+'_Directions.sprites.json'));atlas=Image.new('RGBA',(2048,2048))
for s in m['sprites']:atlas.alpha_composite(Image.open(A/(s['name']+'.png')),(s['x'],2048-s['y']-s['h']))
atlas.save(A/(NAME+'_Directions.png'))
write(R/'retouch_record.json',dict(observed_at=now(),parent='original staged art',method='Local removal of invented rear-head side spikes and disconnected chroma-edge flecks; whole returned images unchanged',changes=changes,raw_sha256={k:sha(D/'generation'/k/'raw.png') for k in ['Up','Down']},final_staged={p.name:sha(p) for p in A.iterdir() if p.is_file()}))
parts={
'Up/Body':dict(y=.34,width=.50,height=.46),
'Up/Head':dict(y=.57,width=.29,height=.25,order=22),
'Up/Tail':dict(x=.02,y=.17,width=.58,height=.82,order=25),
'Down/Body':dict(y=.39,width=.49,height=.49),
'Down/Head':dict(y=.20,width=.34,height=.28),
'Down/Tail':dict(x=0,y=.59,width=.30,height=.48,order=5)}
for direction in ['Up','Down']:
    for side in ['L','R']:
        sign=-1 if side=='L' else 1
        parts[direction+'/Claw'+side]=dict(x=sign*.15,y=.53 if direction=='Up' else .20,width=.33,height=.28,angle=sign*(18 if direction=='Up' else -18))
        for j,leg in enumerate(['Front','Middle','Back']):
            parts[direction+'/Leg'+leg+side]=dict(x=sign*.15,y=([.49,.34,.21] if direction=='Up' else [.22,.36,.50])[j],width=.28,height=.25)
changes=dict(reason='Original is a low six-leg scorpion under a high arch; generic layout had oversized torso, low Up tail and too high Down tail. Correct scale and attachment before installation.',parts=parts,sprites={'Up_Tail':dict(pivotX=.62,pivotY=.06),'Down_Tail':dict(pivotX=.20,pivotY=.06)},layout=dict(motion=dict(legAngle=7,legLift=.085,bodyBob=.002,bodyRoll=.7,tailSwing=3)))
for direction in ['Up','Down']:
    for leg in ['Front','Middle','Back']:changes['sprites'][direction+'_Leg'+leg]=dict(pivotX=.80,pivotY=.88)
write(D/'layout_adjustments.json',changes)
print('Retouch and character-specific layout r01 preserved and prepared')
