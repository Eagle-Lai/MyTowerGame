"""SabretoothTiger-only staged raster cleanup; original responses remain immutable."""
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np, json, hashlib, shutil

D=Path(__file__).resolve().parent
A=D/'staged_art'
R=D/'offline_repair_r01'
R.mkdir(exist_ok=True)
for p in [D/'offline_rig_proof.png',D/'parts_clean.png',*A.glob('*')]:
    destination=R/('before_'+p.name)
    if p.is_file() and not destination.exists():shutil.copy2(p,destination)
manifest=json.loads((A/'SabretoothTiger_Directions.sprites.json').read_text())
atlas=Image.open(A/'SabretoothTiger_Directions.png').convert('RGBA')
records=[]
for key in ['Up_LegFront','Up_LegBack','Down_LegFront','Down_LegBack']:
    path=A/(key+'.png')
    im=Image.open(R/('before_'+key+'.png')).convert('RGBA')
    w,h=im.size
    if key.startswith('Down_'):
        pixels=np.asarray(im).copy()
        feather=np.clip((np.arange(h)[:,None]-h*.33)/6,0,1)
        pixels[:,:,3]=(pixels[:,:,3]*feather).astype(np.uint8)
        im=Image.fromarray(pixels)
        im.save(path)
        s=next(x for x in manifest['sprites'] if x['name']==key)
        atlas.paste(im,(s['x'],2048-s['y']-s['h']))
        records.append({'sprite':key,'operation':'Hide upper circular root under existing torso/head overlap; keep forward toes and all original lower limb colors'})
        continue
    pixels=np.asarray(im).copy()
    cut=round(h*.75)
    occupied=np.flatnonzero(pixels[cut,:,3]>127)
    left,right=int(occupied[0]),int(occupied[-1])
    pixels[cut:]=0
    im=Image.fromarray(pixels)
    scale=4
    heel=Image.new('RGBA',(w*scale,h*scale))
    draw=ImageDraw.Draw(heel)
    points=[]
    def curve(p0,p1,p2,p3):
        for t in np.linspace(0,1,41):
            x=(1-t)**3*p0[0]+3*(1-t)**2*t*p1[0]+3*(1-t)*t*t*p2[0]+t**3*p3[0]
            y=(1-t)**3*p0[1]+3*(1-t)**2*t*p1[1]+3*(1-t)*t*t*p2[1]+t**3*p3[1]
            points.append((round(x*scale),round(y*scale)))
    curve((left,cut),(left,cut+h*.06),(w*.07,h*.86),(w*.12,h*.91))
    curve((w*.12,h*.91),(w*.17,h*.99),(w*.66,h*.99),(w*.78,h*.94))
    curve((w*.78,h*.94),(w*.92,h*.91),(right,h*.85),(right,cut))
    draw.polygon(points,fill=(226,223,213,255))
    # A side-shaded rear heel, not the forward-facing toes/claws in the generated sheet.
    shade=[(round(w*.64*scale),cut*scale),(right*scale,cut*scale),*points[-48:][::-1]]
    draw.polygon(shade,fill=(184,181,171,255))
    draw.line(points,fill=(25,21,15,255),width=5*scale,joint='curve')
    crease=[(round(w*.48*scale),round(h*.88*scale)),(round(w*.49*scale),round(h*.93*scale))]
    draw.line(crease,fill=(115,109,94,255),width=2*scale)
    heel=heel.resize((w,h),Image.Resampling.LANCZOS)
    im.alpha_composite(heel)
    if key=='Up_LegFront':
        pixels=np.asarray(im).copy()
        feather=np.clip((np.arange(h)[:,None]-h*.33)/6,0,1)
        pixels[:,:,3]=(pixels[:,:,3]*feather).astype(np.uint8)
        im=Image.fromarray(pixels)
    im.save(path)
    im.save(R/(key+'_rear_heel.png'))
    s=next(x for x in manifest['sprites'] if x['name']==key)
    atlas.paste(im,(s['x'],2048-s['y']-s['h']))
    records.append({'sprite':key,'operation':'Replace front-facing lower paw/claws with a closed rear heel in the original pale fur palette; preserve complete upper limb and attachment root',
        'cut_y':cut,'size':[w,h],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
atlas.save(A/'SabretoothTiger_Directions.png')
(D/'raster_retouch.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
print('SabretoothTiger staged rear heels repaired; raw sheets unchanged')
