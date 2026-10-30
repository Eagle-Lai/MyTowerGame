"""Local-only documented RoyalBoar rear detail repair; original paid results kept."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,numpy as np
D=Path(__file__).resolve().parent;A=D/'staged_art';R=D/'raster_revision_02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
records=[]
def save(key,im):
    p=A/(key+'.png');before=R/(key+'_before.png')
    if not before.exists():Image.open(p).save(before)
    else:assert sha(p)==sha(before),'Restore via stage before retouch'
    im.save(p);im.save(R/(key+'_after.png'))
    records.append(dict(part=key,before=sha(before),after=sha(p)))
head=Image.open(A/'Up_HeadNormal.png').convert('RGBA')
a=np.array(head);w,h=head.size
# Paint the ivory lateral crescent and its inner outline as continuous gold fur.
# Keep original outer dark contour and exact silhouette; no facial feature remains.
for y in range(137,224):
    occupied=np.flatnonzero(a[y,:,3]>0)
    if len(occupied)==0:continue
    left,right=int(occupied[0]),int(occupied[-1])
    a[y,left+4:27]=a[y,28]
    a[y,w-27:right-3]=a[y,w-29]
head=Image.fromarray(a)
for role in ['HeadNormal','HeadAngry','HeadDead']:save('Up_'+role,head)
for role in ['LegFront','LegBack']:
    im=Image.open(A/('Up_'+role+'.png')).convert('RGBA');ar=np.array(im);hh,ww=ar.shape[:2]
    # Remove only the dark forward-facing toe seam within the hoof interior.
    for y in range(hh-43,hh-5):
        occ=np.flatnonzero(ar[y,:,3]>0)
        if len(occ)<10:continue
        mid=(int(occ[0])+int(occ[-1]))//2
        half=round(2+5*(y-(hh-43))/38)
        sample=ar[y,max(int(occ[0])+7,mid-half-5)].copy()
        ar[y,mid-half:mid+half+1]=sample
    save('Up_'+role,Image.fromarray(ar))
m=json.loads((A/'RoyalBoar_Directions.sprites.json').read_text())
atlas=Image.open(A/'RoyalBoar_Directions.png').convert('RGBA')
for s in m['sprites']:
    im=Image.open(A/(s['name']+'.png')).convert('RGBA')
    assert im.size==(s['w'],s['h'])
    atlas.paste(im,(s['x'],2048-s['y']-s['h']))
atlas.save(A/'RoyalBoar_Directions.png')
proof=Image.new('RGB',(1600,700),(40,48,37));draw=ImageDraw.Draw(proof)
for i,s in enumerate(m['sprites']):
    im=Image.open(A/(s['name']+'.png')).convert('RGBA');im.thumbnail((195,300))
    proof.paste(im,(i%8*200+(200-im.width)//2,i//8*350+35),im)
    draw.text((i%8*200+5,i//8*350+8),s['name'],fill='white')
proof.save(D/'parts_clean.png')
(D/'raster_retouch.json').write_text(json.dumps(dict(revision='raster_revision_02',method='Local raster color repair: lateral ivory crescents/inner lines on rear skull replaced with adjacent gold fur preserving outer outline and alpha; rear hoof front seam filled from adjacent hoof gold. No new anatomy. Raw AI sources and before/after images preserved.',parts=records),indent=2)+'\n',encoding='utf-8')
print('RoyalBoar local rear details repaired and proof rebuilt')
