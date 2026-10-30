from pathlib import Path
from PIL import Image,ImageDraw
import json
HERE=Path(__file__).resolve().parent
targets=json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))['targets']
for start in range(0,len(targets),18):
    canvas=Image.new('RGB',(1800,1050),(40,48,37));draw=ImageDraw.Draw(canvas)
    for i,t in enumerate(targets[start:start+18]):
        im=Image.open(HERE/t['name']/'reference/source_prefab_offline.png').convert('RGBA');im=im.crop(im.getbbox());im.thumbnail((286,300))
        x=i%6*300;y=i//6*350
        canvas.paste(im,(x+(300-im.width)//2,y+36+(300-im.height)//2),im)
        draw.text((x+8,y+8),str(t['index'])+' '+t['name'],fill='white')
    canvas.save(HERE/('references_%02d.png'%(start//18+1)))
