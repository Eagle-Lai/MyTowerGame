from session_treasurechest import *
from PIL import Image,ImageDraw
import numpy as np
owner();assert inventory()==read(D/'incremental_before_20261028.json')['files']
alpha={};fixes=[];out=D/'staged_art';manifest=read(out/'TreasureChest_Directions.sprites.json');atlas=Image.open(out/'TreasureChest_Directions.png').convert('RGBA')
for p in sorted(out.glob('Up_*.png'))+sorted(out.glob('Down_*.png')):
    im=Image.open(p).convert('RGBA');a=np.array(im)[:,:,3]
    if p.stem.endswith('_Body'):
        assert im.size==(1,1) and not a.any();alpha[p.name]=dict(intentional_transparent_carrier=True,size=[1,1],sha256=sha(p));continue
    # Lanczos produces isolated 1-23 alpha ringing outside the cutout. Remove only
    # that nearly transparent fringe; keep all >=24 antialias and opaque pixels.
    native_before=sha(p);pixels=np.array(im);ring=(a>0)&(a<24);ring_count=int(ring.sum());pixels[ring]=0
    im=Image.fromarray(pixels,'RGBA');a=pixels[:,:,3]
    mask=Image.fromarray(np.where(a==0,255,0).astype('uint8'));pad=Image.new('L',(im.width+2,im.height+2),255);pad.paste(mask,(1,1));ImageDraw.floodfill(pad,(0,0),127);holes=np.argwhere(np.array(pad)[1:-1,1:-1]==255)
    assert len(holes)<=100,(p.name,len(holes))
    if len(holes):
        before=sha(p);pixels=np.array(im);original=pixels.copy()
        for y,x in holes:
            candidates=[(dy*dy+dx*dx,dy,dx) for dy in range(-3,4) for dx in range(-3,4) if 0<=y+dy<im.height and 0<=x+dx<im.width and original[y+dy,x+dx,3]==255]
            assert candidates,(p.name,int(x),int(y));_,dy,dx=min(candidates);pixels[y,x]=original[y+dy,x+dx]
        Image.fromarray(pixels,'RGBA').save(p);im=Image.open(p).convert('RGBA');s=next(s for s in manifest['sprites'] if s['name']==p.stem);atlas.paste(im,(s['x'],2048-s['y']-s['h']))
        fixes.append(dict(part=p.name,before_sha256=before,after_sha256=sha(p),pixels=[[int(x),int(y)] for y,x in holes],method='nearest original opaque pixel within3px, interior enclosed pinholes only'))
    assert len(holes)==0,'Inspect unexpected actual interior holes before mutation'
    if ring_count:
        im.save(p);s=next(s for s in manifest['sprites'] if s['name']==p.stem);atlas.paste(im,(s['x'],2048-s['y']-s['h']))
        fixes.append(dict(part=p.name,before_sha256=native_before,after_sha256=sha(p),outer_low_alpha_pixels_removed=ring_count,method='remove Lanczos fringe alpha1..23 only; no opaque content fill/recolor'))
    alpha[p.name]=dict(size=list(im.size),transparent=int((a==0).sum()),interior_holes_before=int(len(holes)),interior_holes_after=0,sha256=sha(p))
if fixes:atlas.save(out/'TreasureChest_Directions.png')
write(D/'chroma_quality_20261028.json',dict(observed_at=now(),parts=alpha,fixes=fixes,total_fringe_pixels_removed=sum(x.get('outer_low_alpha_pixels_removed',0) for x in fixes),actual_interior_pixels_filled=0,atlas_sha256=sha(out/'TreasureChest_Directions.png'),paid_raw_modified=False))
# Exact bottom-aligned complete-state board at native state size.
board=Image.new('RGB',(1600,550),(40,48,37));draw=ImageDraw.Draw(board)
for i,key in enumerate(['Up_HeadNormal','Up_HeadDead','Down_HeadNormal','Down_HeadDead']):
    im=Image.open(out/(key+'.png'));board.paste(im,(i*400+8,40),im);draw.text((i*400+8,10),key+' whole state',fill='white')
board.save(D/'state_alignment_proof.png')
print(json.dumps(dict(parts=len(alpha),actual_interior_pixels_filled=0,fringe_pixels_removed=sum(x.get('outer_low_alpha_pixels_removed',0) for x in fixes),board=str(D/'state_alignment_proof.png'))))
