from pathlib import Path
import runpy,sys
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[1]
sys.argv=[str(root/'render_staged_rig.py'),'EvilEye']
ns=runpy.run_path(str(root/'render_staged_rig.py'))
ns['render'].__globals__['resolution']=1100
ns['render'].__globals__['ppu']=450/ns['layout']['referenceHeight']
out=Image.new('RGB',(2200,2240),(40,48,37));draw=ImageDraw.Draw(out)
for row in range(2):
    for col,view in enumerate(ns['layout']['views']):
        p=ns['render'](view,row);out.paste(p,(col*1100,row*1120+20),p)
        draw.text((col*1100+20,row*1120+5),view['direction']+' OFFLINE wing pose '+str(row),fill='white')
out.save(root/'EvilEye/offline_wing_poses.png')
