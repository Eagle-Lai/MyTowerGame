"""Full extent RatKing proof; fixed generic 800-square crop excludes enlarged crown/tail."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,math
D=Path(__file__).resolve().parent;A=D/'staged_art';layout=json.loads((A/'RatKing_Directions.layout.json').read_text());sprites={s['name']:s for s in json.loads((A/'RatKing_Directions.sprites.json').read_text())['sprites']}
ppu=450/layout['referenceHeight'];bottom=layout['referenceBottom']
proof=Image.new('RGB',(2400,1000),(40,48,37));dr=ImageDraw.Draw(proof)
reference=Image.open(D/'reference/battle_prefab_offline.png').convert('RGBA');reference.thumbnail((760,780));proof.paste(reference,((800-reference.width)//2,100),reference);dr.text((20,20),'RatKing ORIGINAL - offline serialized reference',fill='white')
for i,view in enumerate(layout['views']):
    canvas=Image.new('RGBA',(800,960))
    for p in sorted(view['parts'],key=lambda p:p['order']):
        s=sprites[p['sprite']];im=Image.open(A/(p['sprite']+'.png')).convert('RGBA')
        scale=min(p['width']/im.width,p['height']/im.height);w=max(1,round(im.width*scale*ppu));h=max(1,round(im.height*scale*ppu));im=im.resize((w,h),Image.Resampling.LANCZOS)
        px=s['pivotX'];py=s['pivotY']
        if p['flipX']:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);px=1-px
        ax=px*w;ay=(1-py)*h
        if p.get('angle'):
            radius=math.ceil(math.hypot(w,h));pad=Image.new('RGBA',(radius*2,radius*2));pad.alpha_composite(im,(round(radius-ax),round(radius-ay)));im=pad.rotate(p['angle'],resample=Image.Resampling.BICUBIC);ax=ay=radius
        canvas.alpha_composite(im,(round(400+p['x']*ppu-ax),round(780-(p['y']-bottom)*ppu-ay)))
    box=canvas.getbbox();assert box and box[0]>0 and box[1]>0 and box[2]<800 and box[3]<960,box
    canvas.save(D/('offline_'+view['direction']+'.png'));proof.paste(canvas,((i+1)*800,30),canvas);dr.text(((i+1)*800+20,20),view['direction']+' FULL EXTENT - offline only',fill='white')
proof.save(D/'offline_rig_proof.png')
print('Full-extent offline crown/tail proof saved; no clipping')
