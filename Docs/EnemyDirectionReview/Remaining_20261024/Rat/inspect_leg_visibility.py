from pathlib import Path
from PIL import Image
import json
D=Path(__file__).resolve().parent
layout=json.loads((D/'staged_art/Rat_Directions.layout.json').read_text(encoding='utf-8'))
sprites={s['name']:s for s in json.loads((D/'staged_art/Rat_Directions.sprites.json').read_text(encoding='utf-8'))['sprites']}
for view in layout['views']:
    layers=[]
    for part in sorted(view['parts'],key=lambda p:p['order']):
        im=Image.open(D/'staged_art'/(part['sprite']+'.png')).convert('RGBA');s=sprites[part['sprite']]
        scale=min(part['width']/im.width,part['height']/im.height)*160
        im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))))
        pivot=s['pivotX']
        if part['flipX']:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);pivot=1-pivot
        x=round(500+part['x']*160-im.width*pivot)
        y=round(800-part['y']*160-im.height*(1-s['pivotY']))
        mask=Image.new('L',(1000,1000));mask.paste(im.getchannel('A'),(x,y))
        layers.append((part,mask))
    for i,(part,mask) in enumerate(layers):
        if part['role']!='leg':continue
        visible=mask.copy()
        for _,higher in layers[i+1:]:visible.paste(0,mask=higher)
        total=sum(v>128 for v in mask.getdata());shown=sum(v>128 for v in visible.getdata())
        print(view['direction'],part['name'],shown,'/',total,round(shown/max(total,1),3))
