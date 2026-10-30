from pathlib import Path
from PIL import Image,ImageDraw
import json
root=Path(__file__).resolve().parent
layout=json.loads((root/'staged_art/Ram_Directions.layout.json').read_text(encoding='utf-8'))
sprites={s['name']:s for s in json.loads((root/'staged_art/Ram_Directions.sprites.json').read_text(encoding='utf-8'))['sprites']}
for v in layout['views']:
 layers=[]
 for p in sorted(v['parts'],key=lambda p:p['order']):
  im=Image.open(root/'staged_art'/(p['sprite']+'.png')).convert('RGBA');s=sprites[p['sprite']]
  scale=min(p['width']/im.width,p['height']/im.height)*160
  im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))))
  px=s['pivotX']
  if p['flipX']:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);px=1-px
  x=round(500+p['x']*160-im.width*px);y=round(800-p['y']*160-im.height*(1-s['pivotY']))
  m=Image.new('L',(1000,1000));m.paste(im.getchannel('A'),(x,y));layers.append((p,m))
 for i,(p,m) in enumerate(layers):
  if p['role']!='leg':continue
  n=sum(x>128 for x in m.getdata());vis=m.copy()
  for _,other in layers[i+1:]:vis.paste(0,mask=other)
  k=sum(x>128 for x in vis.getdata())
  print(v['direction'],p['name'],'visible',k,'/',n,'fraction',round(k/max(n,1),3))
