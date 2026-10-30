"""Repair tiny chroma-key interior holes and edge spill in staged WhiteWolf only."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib,json,os,shutil
import numpy as np
D=Path(__file__).resolve().parent; H=D.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
c=read(H/'conversation_chain.json')
assert c['state']=='active' and c['current_character']=='WhiteWolf' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert not (D/'installed_manifest.json').exists()
shutil.copytree(D/'staged_art',D/'staged_art_r03')
shutil.copy2(D/'offline_rig_proof.png',D/'r03_offline_rig_proof.png')
art=D/'staged_art'; spec=read(art/'WhiteWolf_Directions.sprites.json')
atlas=Image.new('RGBA',(2048,2048));stats={}
for s in spec['sprites']:
    p=art/(s['name']+'.png'); im=Image.open(p).convert('RGBA');a=np.array(im);opaque=a[:,:,3]>0
    pad=Image.new('L',(im.width+2,im.height+2),255)
    pad.paste(Image.fromarray(np.where(opaque,0,255).astype('uint8')),(1,1));ImageDraw.floodfill(pad,(0,0),127)
    holes=np.asarray(pad)[1:-1,1:-1]==255
    for y,x in zip(*np.where(holes)):
        for radius in range(1,max(im.size)):
            y0=max(0,y-radius);y1=min(im.height,y+radius+1);x0=max(0,x-radius);x1=min(im.width,x+radius+1)
            yy,xx=np.where(opaque[y0:y1,x0:x1])
            if len(xx):
                n=np.argmin((yy+y0-y)**2+(xx+x0-x)**2)
                a[y,x]=a[yy[n]+y0,xx[n]+x0];break
    rgb=a[:,:,:3].astype(np.int16)
    spill=(a[:,:,3]>0)&(rgb[:,:,2]>rgb[:,:,1]+6)&(rgb[:,:,0]>rgb[:,:,1]+10)
    a[:,:,2][spill]=a[:,:,1][spill]
    im=Image.fromarray(a);im.save(p);atlas.paste(im,(s['x'],2048-s['y']-s['h']))
    stats[s['name']]={'interior_pixels_repaired':int(holes.sum()),'edge_pixels_despilled':int(spill.sum())}
atlas.save(art/'WhiteWolf_Directions.png')
proof=Image.new('RGB',(1600,700),(40,48,37));draw=ImageDraw.Draw(proof)
for i,s in enumerate(spec['sprites']):
    im=Image.open(art/(s['name']+'.png'));im.thumbnail((195,300),Image.Resampling.LANCZOS)
    proof.paste(im,(i%8*200+(200-im.width)//2,i//8*350+35),im);draw.text((i%8*200+5,i//8*350+8),s['name'],fill='white')
proof.save(D/'parts_clean_final.png')
shutil.copytree(art,D/'staged_art_r04')
raw=read(D/'staged_art_r01/manifest.json')['raw'];assert all(sha(D/p)==v for p,v in raw.items())
manifest={'revision':'art_r04','raw_unchanged':True,'raw':raw,'repairs':stats,'final_art':{p.name:sha(p) for p in art.iterdir() if p.is_file()}}
(D/'staged_art_r04/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'interior_pixels_repaired':sum(s['interior_pixels_repaired'] for s in stats.values()),'edge_pixels_despilled':sum(s['edge_pixels_despilled'] for s in stats.values()),'revision':'art_r04'}))
