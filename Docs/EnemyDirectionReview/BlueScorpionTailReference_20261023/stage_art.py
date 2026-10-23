from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,math,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
REL='Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/Directions'
before=HERE/'before'/REL;stage=HERE/'staged';stage.mkdir(exist_ok=True)
raw=Image.open(HERE/'generation/raw.png');rgb=np.asarray(raw.convert('RGB')).astype(np.int16)
# The returned image is inspected, not assumed to match the requested size/format.
mask=(rgb.min(axis=2)<205)&((rgb[:,:,0]-rgb[:,:,2])>8)
if raw.mode=='RGBA':mask &= np.asarray(raw)[:,:,3]>=128
rgba=np.dstack([rgb.astype(np.uint8),mask.astype(np.uint8)*255]);rgba[~mask,:3]=0
clean=Image.fromarray(rgba,'RGBA');bounds=clean.getbbox()
if not bounds:raise ValueError('No tail extracted')
piece=clean.crop(bounds);piece.save(HERE/'generation/tail_transparent_full.png')
manifest=json.loads((before/'BlueScorpion_Directions.sprites.json').read_text(encoding='utf-8'))
layout=json.loads((before/'BlueScorpion_Directions.layout.json').read_text(encoding='utf-8'))
s=next(s for s in manifest['sprites'] if s['name']=='Up_Tail')
piece.thumbnail((s['w'],s['h']),Image.Resampling.LANCZOS)
cell=Image.new('RGBA',(s['w'],s['h']));offset=((s['w']-piece.width)//2,(s['h']-piece.height)//2);cell.alpha_composite(piece,offset)
cell.save(HERE/'generation/Up_Tail_final.png')
atlas=Image.open(before/'BlueScorpion_Directions.png').convert('RGBA')
box=(s['x'],atlas.height-s['y']-s['h'],s['x']+s['w'],atlas.height-s['y'])
atlas.paste(cell,box[:2]);atlas.save(stage/'BlueScorpion_Directions.png')
s.update(pivotX=.46,pivotY=.07)
tail=next(p for p in layout['views'][0]['parts'] if p['role']=='tail')
tail.update(x=0.0,y=.65,width=3.65,height=5.55,angle=12,order=25,flipX=False)
for obj,ext in [(layout,'layout'),(manifest,'sprites')]:
 (stage/f'BlueScorpion_Directions.{ext}.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Pixel-level scope check: every other atlas slice must remain exactly unchanged.
a=np.asarray(Image.open(before/'BlueScorpion_Directions.png').convert('RGBA'));b=np.asarray(atlas)
changed=np.any(a!=b,axis=2);outside=changed.copy();outside[box[1]:box[3],box[0]:box[2]]=False
assert not outside.any(),'Pixels changed outside Up_Tail'
report={'actual_return':{'format':raw.format,'size':list(raw.size),'mode':raw.mode},'white_removal':'Gold/brown spectral mask with minimum channel below 205, then native-alpha intersection and final Lanczos antialiasing; transparent RGB zeroed before resizing','source_bounds':bounds,'fit_size':list(piece.size),'cell_size':list(cell.size),'cell_offset':offset,'atlas_cell':box,'changed_pixels':int(changed.sum()),'changed_pixels_outside_Up_Tail':int(outside.sum()),'tail_layout':tail,'tail_pivot':[s['pivotX'],s['pivotY']]}
(HERE/'processing.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
old_layout=json.loads((before/'BlueScorpion_Directions.layout.json').read_text());old_manifest=json.loads((before/'BlueScorpion_Directions.sprites.json').read_text())
board=Image.new('RGB',(1400,860),(40,48,37));draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
for col,(v,m,a,label) in enumerate([(old_layout['views'][0],old_manifest,Image.open(before/'BlueScorpion_Directions.png'),'已否决：低弧尾巴扣向头部'),(layout['views'][0],manifest,atlas,'参考修订：后端竖起、高拱、毒针下垂')]):
 slices={s['name']:s for s in m['sprites']};ppu=105
 for p in sorted(v['parts'],key=lambda p:p['order']):
  sl=slices[p['sprite']];im=a.crop((sl['x'],2048-sl['y']-sl['h'],sl['x']+sl['w'],2048-sl['y']))
  scale=min(p['width']/sl['w'],p['height']/sl['h'])*ppu;w,h=round(sl['w']*scale),round(sl['h']*scale);im=im.resize((w,h),Image.Resampling.LANCZOS)
  px=sl['pivotX'];py=sl['pivotY']
  if p['flipX']:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);px=1-px
  radius=math.ceil(math.hypot(w,h));pad=Image.new('RGBA',(radius*2,radius*2));pad.alpha_composite(im,(round(radius-px*w),round(radius-(1-py)*h)));pad=pad.rotate(p['angle'],resample=Image.Resampling.BICUBIC)
  board.paste(pad,(round(col*700+350+p['x']*ppu-radius),round(745-p['y']*ppu-radius)),pad)
 draw.text((col*700+15,15),label,font=font,fill='white')
draw.text((15,825),'离线方案预演；最终以 Unity 实际行走、攻击、死亡画面为准',font=font,fill='white')
board.save(HERE/'layout_proposal.png')
print(json.dumps(report))
