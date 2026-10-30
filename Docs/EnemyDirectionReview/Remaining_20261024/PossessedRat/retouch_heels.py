from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json
D=Path(__file__).resolve().parent; A=D/'staged_art'; R=D/'raster_revision_01'; R.mkdir(exist_ok=True)
manifest=json.loads((A/'PossessedRat_Directions.sprites.json').read_text())
atlas=Image.open(A/'PossessedRat_Directions.png').convert('RGBA'); records=[]
for key in ['Up_LegFront','Up_LegBack']:
 im=Image.open(A/(key+'.png')).convert('RGBA');im.save(R/(key+'_before.png'));pixels=np.array(im);h,w=pixels.shape[:2]
 mask=Image.new('L',im.size);draw=ImageDraw.Draw(mask);draw.rectangle((0,round(h*.77),w,h),fill=255)
 interior=np.array(im.getchannel('A').filter(ImageFilter.MinFilter(13)))>220
 region=(np.array(mask)>0)&interior
 yy,xx=np.indices((h,w));shade=np.clip((xx-w*.25)/(w*.8),0,1)
 for ch,(light,dark) in enumerate([(91,62),(76,51),(45,30)]):
  pixels[:,:,ch][region]=(light+(dark-light)*shade[region]).astype(np.uint8)
 im=Image.fromarray(pixels);im.save(A/(key+'.png'));im.save(R/(key+'_after.png'))
 s=next(x for x in manifest['sprites'] if x['name']==key);atlas.paste(im,(s['x'],2048-s['y']-s['h']))
 records.append({'sprite':key,'revision':'raster_revision_01','change':'Remove front gold toes in lower 23 percent; use plain dark back heel, preserve alpha and outline.'})
atlas.save(A/'PossessedRat_Directions.png');(D/'raster_retouch.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
