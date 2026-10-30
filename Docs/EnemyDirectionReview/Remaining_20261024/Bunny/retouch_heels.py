"""Small raster cleanup of generated rear feet: remove front toe creases, keep outline and shading."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import json, numpy as np
D=Path(__file__).resolve().parent;A=D/'staged_art'
spec={'Up_LegFront':[(45,244,35,299),(91,244,85,302)],'Up_LegBack':[(65,287,60,342),(115,288,110,345)]}
manifest=json.loads((A/'Bunny_Directions.sprites.json').read_text())
atlas=Image.open(A/'Bunny_Directions.png').convert('RGBA')
records=[]
for key,strokes in spec.items():
    p=A/(key+'.png');im=Image.open(p).convert('RGBA');pixels=np.asarray(im).copy()
    mask=Image.new('L',im.size)
    draw=ImageDraw.Draw(mask)
    for stroke in strokes:draw.line(stroke,fill=255,width=22)
    m=np.asarray(mask)>0
    # Protect the actual outer contour and alpha; cream fill corresponds to original rabbit fur.
    interior=np.asarray(im.getchannel('A').filter(ImageFilter.MinFilter(11)))>220
    fill=m&interior
    colors=pixels[:,:,:3].astype(np.float64)
    colors[fill]=[244,224,190]
    for iteration in range(1200):
        neighbors=(np.roll(colors,1,0)+np.roll(colors,-1,0)+np.roll(colors,1,1)+np.roll(colors,-1,1))*.25
        colors[fill]=neighbors[fill]
    pixels[:,:,:3]=np.clip(colors,0,255).astype(np.uint8)
    im=Image.fromarray(pixels);im.save(p)
    s=next(x for x in manifest['sprites'] if x['name']==key)
    x,y=s['x'],2048-s['y']-s['h']
    atlas.paste(im,(x,y))
    records.append({'sprite':key,'lines':strokes,'operation':'Remove front toe crease marks for rear-facing heel; preserve opaque outline and existing alpha'})
atlas.save(A/'Bunny_Directions.png')
(D/'raster_retouch.json').write_text(json.dumps(records,indent=2)+'\n')
