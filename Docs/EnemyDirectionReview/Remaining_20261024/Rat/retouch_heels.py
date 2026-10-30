"""Rat-only rear heels and concealed upper attachment caps. No generated source is edited."""
from pathlib import Path
from PIL import Image,ImageFilter
import numpy as np,json,hashlib
D=Path(__file__).resolve().parent; A=D/'staged_art'; R=D/'raster_revision_04';R.mkdir(exist_ok=True)
manifest=json.loads((A/'Rat_Directions.sprites.json').read_text())
atlas=Image.open(A/'Rat_Directions.png').convert('RGBA');records=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for key in [entry['name'] for entry in manifest['sprites']]:
    p=A/(key+'.png');im=Image.open(p).convert('RGBA')
    before=R/(key+'_before.png')
    if not before.exists():im.save(before)
    pixels=np.array(im);h,w=pixels.shape[:2];yy,xx=np.indices((h,w))
    changes=[]
    if key in ['Up_LegFront','Up_LegBack']:
        inside=np.array(im.getchannel('A').filter(ImageFilter.MinFilter(7)))>220
        fill=(yy>=h*.75)&inside
        blend=np.clip((yy-h*.75)/(h*.035),0,1)
        horizontal=np.clip((xx-w*.22)/(w*.65),0,1)
        vertical=np.clip((yy-h*.75)/(h*.25),0,1)
        for ch,(light,dark) in enumerate([(116,96),(101,81),(61,45)]):
            target=light+(dark-light)*horizontal-vertical*4
            pixels[:,:,ch][fill]=(pixels[:,:,ch][fill]*(1-blend[fill])+target[fill]*blend[fill]).astype(np.uint8)
        changes.append('Replace lower quarter interior with continuous olive rear heel shading; retain alpha and 3px outer contour')
    if key in ['Up_LegFront','Down_LegFront','Down_LegBack']:
        feather=np.clip((yy-h*.34)/6,0,1)
        pixels[:,:,3]=(pixels[:,:,3]*feather).astype(np.uint8)
        changes.append('Conceal top 34 percent circular attachment cap inside body/head overlap')
    alpha=Image.fromarray(pixels[:,:,3]);edge=(pixels[:,:,3]>0)&(np.array(alpha.filter(ImageFilter.MinFilter(5)))<220)
    rgb=pixels[:,:,:3].astype(np.int16);fringe=edge&(rgb[:,:,2]>rgb[:,:,1]+8)
    pixels[:,:,2][fringe]=np.minimum(rgb[:,:,2][fringe],rgb[:,:,1][fringe]+3).astype(np.uint8)
    im=Image.fromarray(pixels);im.save(p);im.save(R/(key+'_after.png'))
    s=next(x for x in manifest['sprites'] if x['name']==key)
    atlas.paste(im,(s['x'],2048-s['y']-s['h']))
    if fringe.any():changes.append('Reduce blue-magenta chroma on antialiased alpha edge')
    records.append(dict(sprite=key,changes=changes,before_sha256=sha(before),after_sha256=sha(p)))
atlas.save(A/'Rat_Directions.png')
(D/'raster_retouch.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
