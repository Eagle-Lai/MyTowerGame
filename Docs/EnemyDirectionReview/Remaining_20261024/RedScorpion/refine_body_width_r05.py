from serial_common import *
from PIL import Image
import shutil
owner();A=D/'staged_art';R=D/'raster_revision_05';R.mkdir()
for p in A.iterdir():
    if p.is_file():shutil.copy2(p,R/p.name)
shutil.copy2(D/'offline_rig_proof.png',R/'offline_before.png')
for direction in ['Up','Down']:
    p=A/(direction+'_Body.png');im=Image.open(p);im=im.resize((round(im.width*1.35),im.height),Image.Resampling.LANCZOS);im.save(p)
m=read(A/(NAME+'_Directions.sprites.json'));atlas=Image.new('RGBA',(2048,2048));x=y=8;rh=0
for s in m['sprites']:
    im=Image.open(A/(s['name']+'.png'));w,h=im.size
    if x+w+8>2048:x=8;y+=rh+8;rh=0
    assert y+h+8<=2048
    s.update(x=x,y=2048-y-h,w=w,h=h);atlas.alpha_composite(im,(x,y));x+=w+8;rh=max(rh,h)
atlas.save(A/(NAME+'_Directions.png'));write(A/(NAME+'_Directions.sprites.json'),m)
write(R/'retouch_record.json',dict(observed_at=now(),parent='raster_revision_04',method='Proportion correction on newly generated axial torso only: width x1.35 at fixed height to match original broad plated abdomen and meet limb roots. No side-view sprite was used to fake axial art.',final_staged={p.name:sha(p) for p in A.iterdir() if p.is_file()}))
