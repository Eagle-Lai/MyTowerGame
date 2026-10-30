from serial_common import *
from PIL import Image,ImageDraw
import shutil
owner();A=D/'staged_art';R=D/'raster_revision_06';R.mkdir()
for p in A.iterdir():
    if p.is_file():shutil.copy2(p,R/p.name)
p=A/'Down_Tail.png';im=Image.open(p).convert('RGBA');ImageDraw.Draw(im).rectangle((110,98,130,125),fill=(0,0,0,0));im.save(p)
m=read(A/(NAME+'_Directions.sprites.json'));atlas=Image.new('RGBA',(2048,2048))
for s in m['sprites']:atlas.alpha_composite(Image.open(A/(s['name']+'.png')),(s['x'],2048-s['y']-s['h']))
atlas.save(A/(NAME+'_Directions.png'))
write(R/'retouch_record.json',dict(observed_at=now(),parent='raster_revision_05',method='Actual tail closeup showed one small attached brown chroma remnant inside Down tail arch; remove only x110..130/y98..125. Tail geometry unchanged.',final_staged={p.name:sha(p) for p in A.iterdir() if p.is_file()}))
