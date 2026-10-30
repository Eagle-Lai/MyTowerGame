"""Punisher Up heel cleanup: remove front toe-cap arc within the original opaque silhouette."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import json,numpy as np
p=Path(__file__).resolve().parent;a=p/'staged_art';f=a/'Up_Leg.png';im=Image.open(f).convert('RGBA');pixels=np.asarray(im).copy();w,h=im.size
mask=Image.new('L',im.size);d=ImageDraw.Draw(mask);d.rectangle((int(w*.12),int(h*.71),int(w*.88),int(h*.90)),fill=255)
inside=np.asarray(im.getchannel('A').filter(ImageFilter.MinFilter(13)))>220;m=(np.asarray(mask)>0)&inside
c=pixels[:,:,:3].astype(float);c[m]=[111,96,65]
for i in range(1400):
 n=(np.roll(c,1,0)+np.roll(c,-1,0)+np.roll(c,1,1)+np.roll(c,-1,1))*.25;c[m]=n[m]
pixels[:,:,:3]=np.clip(c,0,255).astype('uint8');im=Image.fromarray(pixels);im.save(f)
s=json.loads((a/'Punisher_Directions.sprites.json').read_text());r=next(x for x in s['sprites'] if x['name']=='Up_Leg');atlas=Image.open(a/'Punisher_Directions.png').convert('RGBA');atlas.paste(im,(r['x'],2048-r['y']-r['h']));atlas.save(a/'Punisher_Directions.png')
(p/'raster_retouch.json').write_text(json.dumps({'sprite':'Up_Leg','operation':'Remove forward toe-cap arch for rear heel; preserve contour, alpha, sole and original olive palette','mask':[.12,.71,.88,.90]},indent=2),encoding='utf-8')
