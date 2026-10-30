"""Offline anatomy/layout proof only. This is never Unity runtime evidence."""
from pathlib import Path
import json,sys,math
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent.parent
name=sys.argv[1]
directory=HERE/name
art=directory/'staged_art'
layout=json.loads((art/(name+'_Directions.layout.json')).read_text(encoding='utf-8'))
manifest=json.loads((art/(name+'_Directions.sprites.json')).read_text(encoding='utf-8'))
slices={s['name']:s for s in manifest['sprites']}
height=layout['referenceHeight'];bottom=layout['referenceBottom']
resolution=800;ppu=330/height

def render(view,phase=0):
    canvas=Image.new('RGBA',(resolution,resolution),(0,0,0,0))
    for part in sorted(view['parts'],key=lambda p:p['order']):
        key=part['alternate'] if part['role']=='wing' and phase%2 else part['sprite']
        source=Image.open(art/(key+'.png')).convert('RGBA');s=slices[key]
        base=Image.open(art/(part['sprite']+'.png'))
        scale=min(part['width']/base.width,part['height']/base.height)
        w=max(1,round(source.width*scale*ppu));h=max(1,round(source.height*scale*ppu))
        piece=source.resize((w,h),Image.Resampling.LANCZOS)
        pivotX=s['pivotX'];pivotY=s['pivotY']
        if part['flipX']:
            piece=piece.transpose(Image.Transpose.FLIP_LEFT_RIGHT);pivotX=1-pivotX
        anchorX=pivotX*w;anchorY=(1-pivotY)*h
        if part.get('angle'):
            # Rotate around the actual Sprite pivot on a padded local canvas.
            radius=math.ceil(math.hypot(w,h));padded=Image.new('RGBA',(radius*2,radius*2))
            padded.alpha_composite(piece,(round(radius-anchorX),round(radius-anchorY)))
            piece=padded.rotate(part['angle'],resample=Image.Resampling.BICUBIC)
            anchorX=anchorY=radius
        x=resolution/2+part['x']*ppu-anchorX
        y=700-(part['y']-bottom)*ppu-anchorY
        canvas.alpha_composite(piece,(round(x),round(y)))
    return canvas

proof=Image.new('RGB',(2400,880),(40,48,37));draw=ImageDraw.Draw(proof)
reference=Image.open(directory/'reference/battle_prefab_offline.png').convert('RGBA')
reference.thumbnail((760,720));proof.paste(reference,((800-reference.width)//2,100),reference)
draw.text((20,20),name+' ORIGINAL BATTLE PREFAB - offline reference',fill='white')
for index,view in enumerate(layout['views']):
    frame=render(view);frame.save(directory/('offline_'+view['direction']+'.png'))
    proof.paste(frame,((index+1)*800,70),frame)
    draw.text(((index+1)*800+20,20),view['direction']+' STAGED RIG - offline layout only',fill='white')
proof.save(directory/'offline_rig_proof_r02.png')
if name=='Bat':
    alternate=Image.new('RGB',(1600,1640),(40,48,37));draw=ImageDraw.Draw(alternate)
    for row in range(2):
        for column,view in enumerate(layout['views']):
            pose=render(view,row);alternate.paste(pose,(column*800,row*820+20),pose)
            draw.text((column*800+20,row*820+5),'OFFLINE '+view['direction']+' wing pose '+str(row),fill='white')
    alternate.save(directory/'offline_wing_joints.png')
print(str(directory/'offline_rig_proof_r02.png'))
