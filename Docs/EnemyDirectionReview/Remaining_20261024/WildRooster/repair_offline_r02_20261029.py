"""Preserve rejected offline r01; local body cleanup and joint placement, no paid calls."""
from PIL import Image, ImageDraw
import numpy as np
import shutil, subprocess, sys
from checkpoint_20261029 import D,H,NAME,read,write,sha,now,owner
owner()
assert not (D/'installed_manifest.json').exists()
old=D/'offline_r01';assert not old.exists();old.mkdir()
shutil.copytree(D/'staged_art',old/'staged_art')
for p in ['offline_Up.png','offline_Down.png','offline_rig_proof.png','parts_clean.png','layout_adjustments.json']:
    shutil.copy2(D/p,old/p)
write(old/'rejected.json',{'at':now(),'reason':'Actually viewed r01: detached wing roots, Down collar/shoulder protrusions and torso tail resembling a second comb, Up high tail overlaps nape; not installed, no runtime or approval.'})
out=D/'local_raster_r02';out.mkdir()

def bez(a,b,c,d):
    return [tuple((1-t)**3*a[k]+3*(1-t)**2*t*b[k]+3*(1-t)*t*t*c[k]+t**3*d[k] for k in range(2)) for t in np.linspace(0,1,50)]

def torso(direction,cut,apex,fill):
    src=Image.open(old/'staged_art'/(direction+'_Body.png')).convert('RGBA')
    a=np.array(src);xs=np.where(a[cut,:,3]>200)[0];l,r=int(xs.min()),int(xs.max());cx=(l+r)/2
    outline=tuple(a[cut,l,:3].tolist())+(255,)
    scale=4;cap=Image.new('RGBA',(src.width*scale,src.height*scale))
    boundary=bez((l+5,cut+5),(l,apex+35),(cx-45,apex),(cx,apex))+bez((cx,apex),(cx+45,apex),(r,apex+35),(r-5,cut+5))
    poly=boundary+[(r-5,cut+15),(l+5,cut+15)]
    draw=ImageDraw.Draw(cap);draw.polygon([(round(x*scale),round(y*scale)) for x,y in poly],fill=fill)
    draw.line([(round(x*scale),round(y*scale)) for x,y in boundary],fill=outline,width=10*scale,joint='curve')
    cap=cap.resize(src.size,Image.Resampling.LANCZOS)
    # Keep the real returned lower body texture and outline, close only the removed top.
    cap.alpha_composite(src.crop((0,cut+4,src.width,src.height)),(0,cut+4))
    if direction=='Up':
        # The original source tail is integral with Body. Move only the generated
        # three-feather tuft down to the rump, with its open gold root buried in body.
        tail=src.crop((52,0,232,123))
        cap.alpha_composite(tail,((src.width-tail.width)//2,220))
    cap=cap.crop(cap.getbbox());cap.save(out/(direction+'_Body.png'))
    return cap

bodies={'Up_Body':torso('Up',160,83,(222,144,9,255)),
        'Down_Body':torso('Down',230,83,(211,136,10,255))}
art=D/'staged_art';spec=read(art/(NAME+'_Directions.sprites.json'))
atlas=Image.new('RGBA',(2048,2048));x=y=8;row_h=0;changes=[]
for s in spec['sprites']:
    key=s['name'];im=bodies.get(key) or Image.open(old/'staged_art'/(key+'.png')).convert('RGBA')
    if x+im.width+8>2048:x=8;y+=row_h+8;row_h=0
    assert y+im.height+8<=2048
    atlas.alpha_composite(im,(x,y));im.save(art/(key+'.png'))
    changes.append({'part':key,'before':sha(old/'staged_art'/(key+'.png')),'after':sha(art/(key+'.png'))})
    s.update(x=x,y=2048-y-im.height,w=im.width,h=im.height)
    x+=im.width+8;row_h=max(row_h,im.height)
atlas.save(art/(NAME+'_Directions.png'));write(art/(NAME+'_Directions.sprites.json'),spec)
layout=read(art/(NAME+'_Directions.layout.json'));height=layout['referenceHeight'];bottom=layout['referenceBottom']
for v in layout['views']:
    for p in v['parts']:
        if p['role']=='head':p.update(y=bottom+.75*height,order=30 if v['direction']=='Up' else 35)
        if p['role']=='body':p.update(y=bottom+.43*height,width=.60*height,height=.58*height)
        if p['role']=='wing':p.update(x=(-1 if p['name'].endswith('L') else 1)*.17*height,y=bottom+.54*height)
        if p['role']=='leg':p.update(x=(-1 if p['name'].endswith('L') else 1)*.145*height,y=bottom+.205*height)
write(art/(NAME+'_Directions.layout.json'),layout)
write(out/'manifest.json',{'at':now(),'revision':'art_r02','parent':'offline_r01/staged_art','raws_unchanged':{d:sha(D/'generation'/d/'raw.png') for d in ['Up','Down']},'method':'Local RGBA body upper cap replacement using the same returned gold and dark outline. Up integral tail tuft repositioned inside lower rump; Down duplicated collar/side protrusions and upper tail fully occluded in front view. Original source unmodified. Wing roots moved inside torso, head/body overlap increased, thigh roots inset. No face/leg/wing pixel substitution.','changes':changes,'stage_files':{p.name:sha(p) for p in art.glob(NAME+'_Directions.*')}})
subprocess.run([sys.executable,str(H/'render_staged_rig.py'),NAME],check=True)
proof=Image.new('RGB',(1200,500),(40,48,37));draw=ImageDraw.Draw(proof)
for i,key in enumerate(['Up_Body','Down_Body']):
    im=bodies[key].copy();im.thumbnail((480,440));proof.paste(im,(i*600+(600-im.width)//2,45),im);draw.text((i*600+20,12),key+' local r02 - not raw',fill='white')
proof.save(out/'body_review.png')
print('Local r02 body and joints ready for actual offline review')
