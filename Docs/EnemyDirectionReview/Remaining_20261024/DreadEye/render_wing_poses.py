from pathlib import Path
import runpy,sys
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[1]
sys.argv=[str(root/'render_staged_rig.py'),'DreadEye']
ns=runpy.run_path(str(root/'render_staged_rig.py'))
out=Image.new('RGB',(1600,1640),(40,48,37));draw=ImageDraw.Draw(out)
for row in range(2):
    for col,view in enumerate(ns['layout']['views']):
        p=ns['render'](view,row);out.paste(p,(col*800,row*820+20),p)
        draw.text((col*800+20,row*820+5),view['direction']+' OFFLINE wing pose '+str(row),fill='white')
out.save(root/'DreadEye/offline_wing_poses.png')
