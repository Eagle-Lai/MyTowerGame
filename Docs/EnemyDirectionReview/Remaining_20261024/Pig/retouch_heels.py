"""Pig rear-heel cleanup, preserve source revision and outline/alpha."""
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np,json
D=Path(__file__).resolve().parent;A=D/'staged_art'
manifest=json.loads((A/'Pig_Directions.sprites.json').read_text())
atlas=Image.open(A/'Pig_Directions.png').convert('RGBA');records=[]
for key in ['Up_LegFront','Up_LegBack']:
 p=A/(key+'.png');im=Image.open(p).convert('RGBA');v=np.asarray(im).copy();h,w=v.shape[:2];yy,xx=np.mgrid[:h,:w]
 interior=np.asarray(im.getchannel('A').filter(ImageFilter.MinFilter(11)))>220
 fill=(xx>w*.32)&(xx<w*.65)&(yy>h*.79)&(yy<h*.97)&interior
 colors=v[:,:,:3].astype(float)
 for i in range(1400):
  neighbor=(np.roll(colors,1,0)+np.roll(colors,-1,0)+np.roll(colors,1,1)+np.roll(colors,-1,1))*.25
  colors[fill]=neighbor[fill]
 v[:,:,:3]=np.clip(colors,0,255).astype(np.uint8);out=Image.fromarray(v);out.save(p)
 s=next(x for x in manifest['sprites'] if x['name']==key);atlas.paste(out,(s['x'],2048-s['y']-s['h']))
 records.append({'sprite':key,'pixels':int(fill.sum()),'operation':'Blend central front toe crease to rear heel; preserve alpha and outer outline'})
atlas.save(A/'Pig_Directions.png')
(D/'raster_retouch.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
