from serial_common import *
from PIL import Image,ImageDraw
import numpy as np,shutil
owner();A=D/'staged_art';R=D/'raster_revision_04';R.mkdir()
for p in A.iterdir():
    if p.is_file():shutil.copy2(p,R/p.name)
shutil.copy2(D/'offline_rig_proof.png',R/'rejected_local_body_layout.png')
raw=D/'generation/Up/revision_01/raw.png';im=Image.open(raw).convert('RGB')
rectangles={'Up_Body':[210,105,675,900],'Down_Body':[855,110,1325,900]}
for key,rect in rectangles.items():
    rgb=np.asarray(im.crop(rect));a=rgb.astype(np.int16)
    mask=(a[:,:,2]<=a[:,:,1]+8)&(a[:,:,2]<=a[:,:,0]+12)&((a[:,:,0]-a[:,:,1])<=(a[:,:,1]-a[:,:,2])+26)
    out=np.dstack([rgb,mask.astype(np.uint8)*255]);out[~mask,:3]=0
    piece=Image.fromarray(out).crop(Image.fromarray(out).getbbox());piece.thumbnail((490,490),Image.Resampling.LANCZOS);piece.save(A/(key+'.png'))
src=Image.open(D/'raster_revision_01/Up_HeadNormal.png').convert('RGBA');w,h=src.size
mask=Image.new('L',src.size);dr=ImageDraw.Draw(mask);dr.rectangle((0,0,w,88),fill=255);dr.ellipse((42,53,215,221),fill=255)
a=np.asarray(src).copy();a[:,:,3]=np.minimum(a[:,:,3],np.asarray(mask));head=Image.fromarray(a)
dr=ImageDraw.Draw(head);dr.arc((42,53,215,221),0,180,fill=(54,43,22,255),width=5)
for k in ['Up_HeadNormal','Up_HeadAngry','Up_HeadDead']:head.save(A/(k+'.png'))
m=read(A/(NAME+'_Directions.sprites.json'));atlas=Image.new('RGBA',(2048,2048));x=y=8;row_h=0
for s in m['sprites']:
    p=Image.open(A/(s['name']+'.png')).convert('RGBA');w,h=p.size
    if x+w+8>2048:x=8;y+=row_h+8;row_h=0
    assert y+h+8<=2048
    s.update(x=x,y=2048-y-h,w=w,h=h);atlas.alpha_composite(p,(x,y));x+=w+8;row_h=max(row_h,h)
atlas.save(A/(NAME+'_Directions.png'));write(A/(NAME+'_Directions.sprites.json'),m)
la=read(D/'layout_adjustments.json')
la['parts']['Up/Body'].update(y=.35,width=.46,height=.52)
la['parts']['Down/Body'].update(y=.40,width=.46,height=.52)
write(D/'layout_adjustments.json',la)
s=read(D/'art_selection.json');s['part_sources']={k:dict(source='generation/Up/revision_01/raw.png',rect=v) for k,v in rectangles.items()};s['status']='targeted_torso_revision_selected_pending_offline_and_runtime';s['do_not_rerun_stage']='Final per-part source selection and retouches are assembled by use_body_revision_r04.py; standard pack does not support these per-part overrides.';write(D/'art_selection.json',s)
write(R/'retouch_record.json',dict(observed_at=now(),parent='raster_revision_03',reason='Locally reconstructed flattened body rejected visually; replace ONLY body parts with actually reviewed targeted paid revision. Keep original heads, limbs, claws and tails. Rear head masking restored continuous horn roots.',source=str(raw.relative_to(D)),source_sha256=sha(raw),rectangles=rectangles,final_staged={p.name:sha(p) for p in A.iterdir() if p.is_file()}))
board=Image.new('RGB',(1600,1000),(40,48,37));dr=ImageDraw.Draw(board)
keys=['Up_HeadNormal','Up_Body','Up_LegFront','Up_Tail','Down_HeadNormal','Down_Body','Down_Claw','Down_Tail']
for i,key in enumerate(keys):
    p=Image.open(A/(key+'.png'));p.thumbnail((380,450));x=i%4*400+(400-p.width)//2;y=i//4*500+30;board.paste(p,(x,y),p);dr.text((i%4*400+5,i//4*500+5),key,fill='white')
board.save(D/'parts_selected_r04.png')
