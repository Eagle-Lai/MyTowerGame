from pathlib import Path
from PIL import Image,ImageDraw
import json
root=Path(__file__).resolve().parent
sources=[('OFFLINE r03 LAYOUT - not runtime','offline_rig_proof.png'),('FINAL INSTALLED REAL PLAY FOUR DIRECTIONS','runtime_r01/four_directions.png'),('REAL PLAY UP / DOWN / ATTACK / UP DEATH','runtime_visual_strip.png')]
canvas=Image.new('RGB',(2400,3040),(40,48,37));draw=ImageDraw.Draw(canvas);y=0
for label,path in sources:
 im=Image.open(root/path).convert('RGB');draw.text((12,y+8),label,fill='white');y+=30
 canvas.paste(im,((2400-im.width)//2,y));y+=im.height+10
records=[json.loads(s) for s in (root/'runtime_r01/actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
draw.text((12,y+5),'ACTUAL REUSE / PAUSE / RESUME / SPEED FRAMES',fill='white');y+=25
for i,stage in enumerate(['Reuse','Pause','Resume1x','Speed2x','Speed3x']):
 subset=[r for r in records if r['stage']==stage]
 r=subset[len(subset)//2];im=Image.open(root/'runtime_r01'/r['file']).convert('RGB').resize((280,280))
 canvas.paste(im,(i*480+100,y));draw.text((i*480+12,y+2),stage+' f'+str(r['frame']),fill='white')
canvas.crop((0,0,2400,min(3040,y+285))).save(root/'final_visual_review_board.png')
print(str(root/'final_visual_review_board.png'))
