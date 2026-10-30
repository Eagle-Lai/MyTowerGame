from pathlib import Path
from PIL import Image,ImageDraw
import json
p=Path('Docs/EnemyDirectionReview/Remaining_20261024/MeatBug')
board=Image.new('RGB',(2048,1940),(40,48,37));draw=ImageDraw.Draw(board)
for f,y in [('offline_rig_proof.png',0),('runtime_r02/four_directions.png',760),('runtime_visual_strip.png',1260)]:
 im=Image.open(p/f).convert('RGB');maxh=720 if y==0 else 480 if y==760 else 650;im.thumbnail((2048,maxh));board.paste(im,((2048-im.width)//2,y+20));draw.text((12,y+3),f,fill='white')
board.save(p/'final_visual_review_contact_r02.png')