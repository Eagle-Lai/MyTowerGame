from pathlib import Path
from PIL import Image,ImageDraw
import json,math
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
for name in ['BlackBear','BlackWolf','BlueScorpion']:
 family='Scorpions' if name=='BlueScorpion' else 'Dogs'
 rel=f'Assets/_UIAssets/Monsters/{family}/{name}/Directions'
 source=HERE/'before'/rel;dest=HERE/'staged'/rel;dest.mkdir(parents=True,exist_ok=True)
 layout=json.loads((source/f'{name}_Directions.layout.json').read_text())
 manifest=json.loads((source/f'{name}_Directions.sprites.json').read_text());h=layout['referenceHeight'];bottom=layout['referenceBottom']
 for view in layout['views']:
  up=view['direction']=='Up'
  for p in view['parts']:
   side=-1 if p['name'].endswith('L') else 1
   if name!='BlueScorpion':
    if p['role']=='leg':
     p['x']=side*h*(.145 if name=='BlackBear' else .150)
     # The entire shoulder/hip cap stays under the body during the swing.
     p['y']+=h*(.018 if (up and 'Hind' in p['name']) or (not up and 'Fore' in p['name']) else .01)
     far=(up and 'Fore' in p['name']) or (not up and 'Hind' in p['name'])
     p['angle']=side*(28 if far else 5)
    if p['role']=='tail':
     p['x']=0 if up else h*.025
     p['y']=bottom+h*(.44 if up else .71)
     p['angle']=0 if up else 165
     p['width']*=.85 if name=='BlackWolf' else 1
     p['height']*=.85 if name=='BlackWolf' else 1
     if name=='BlackBear':p['height']*=.85
   else:
    if p['role']=='leg':
     p['x']=side*h*(.11 if 'Front' in p['name'] else .13 if 'Middle' in p['name'] else .10)
     sweep=(110 if up else 35) if 'Front' in p['name'] else 80 if 'Middle' in p['name'] else (35 if up else 105)
     p['angle']=side*sweep
    if p['role']=='claw':p['x']=side*h*.11
 for s in manifest['sprites']:
  if s['name'].endswith('_Tail') and name!='BlueScorpion':
   s['pivotX']=.35 if name=='BlackWolf' else .30;s['pivotY']=.90
 for obj,suffix in [(layout,'layout'),(manifest,'sprites')]:
  (dest/f'{name}_Directions.{suffix}.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 atlas=Image.open(source/f'{name}_Directions.png').convert('RGBA');slices={s['name']:s for s in manifest['sprites']}
 board=Image.new('RGB',(1200,710),(40,48,37));draw=ImageDraw.Draw(board);ppu=520/h
 for col,view in enumerate(layout['views']):
  for p in sorted(view['parts'],key=lambda p:p['order']):
   s=slices[p['sprite']];piece=atlas.crop((s['x'],2048-s['y']-s['h'],s['x']+s['w'],2048-s['y']))
   scale=min(p['width']/s['w'],p['height']/s['h'])*ppu
   w,hh=round(s['w']*scale),round(s['h']*scale);piece=piece.resize((w,hh),Image.Resampling.LANCZOS)
   px=s['pivotX'];py=s['pivotY']
   if p['flipX']:piece=piece.transpose(Image.Transpose.FLIP_LEFT_RIGHT);px=1-px
   radius=math.ceil(math.hypot(w,hh));pad=Image.new('RGBA',(radius*2,radius*2));pad.alpha_composite(piece,(round(radius-px*w),round(radius-(1-py)*hh)))
   pad=pad.rotate(p['angle'],resample=Image.Resampling.BICUBIC)
   board.paste(pad,(round(col*600+300+p['x']*ppu-radius),round(630-(p['y']-bottom)*ppu-radius)),pad)
  draw.text((col*600+10,15),'OFFLINE layout proposal '+name+' '+view['direction'],fill='white')
 board.save(HERE/f'{name}_layout_proposal.png')
print('Staged three layouts and manifests in Docs; production untouched.')
