from pathlib import Path
import json,math
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
REL='Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/Directions'
layout=json.loads((HERE/'staged/BlueScorpion_Directions.layout.json').read_text())
manifest=json.loads((HERE/'staged/BlueScorpion_Directions.sprites.json').read_text())
tail=next(p for p in layout['views'][0]['parts'] if p['role']=='tail');tail.update(x=.25,y=.5,angle=0,order=15)
(HERE/'staged/BlueScorpion_Directions.layout.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
atlas=Image.open(ROOT/REL/'BlueScorpion_Directions.png').convert('RGBA')
board=Image.new('RGB',(700,850),(40,48,37));draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
ppu=140;slices={s['name']:s for s in manifest['sprites']}
for p in sorted(layout['views'][0]['parts'],key=lambda p:p['order']):
 s=slices[p['sprite']];piece=atlas.crop((s['x'],2048-s['y']-s['h'],s['x']+s['w'],2048-s['y']))
 scale=min(p['width']/s['w'],p['height']/s['h'])*ppu;w,h=round(s['w']*scale),round(s['h']*scale);piece=piece.resize((w,h),Image.Resampling.LANCZOS)
 px=s['pivotX'];py=s['pivotY']
 if p['flipX']:piece=piece.transpose(Image.Transpose.FLIP_LEFT_RIGHT);px=1-px
 radius=math.ceil(math.hypot(w,h));pad=Image.new('RGBA',(radius*2,radius*2));pad.alpha_composite(piece,(round(radius-px*w),round(radius-(1-py)*h)));pad=pad.rotate(p['angle'],resample=Image.Resampling.BICUBIC)
 board.paste(pad,(round(350+p['x']*ppu-radius),round(620-p['y']*ppu-radius)),pad)
draw.text((15,15),'尾根位于腹部末端，尾弧向屏幕上方卷起',font=font,fill='white')
draw.text((15,810),'离线布局预演；下一步检查真实动作',font=font,fill='white')
board.save(HERE/'layout_refined.png')
print(tail)
