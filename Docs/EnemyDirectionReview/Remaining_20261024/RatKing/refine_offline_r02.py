"""Remove painted duplicate limbs; finish rear crown surface. Docs-only revision 02."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,shutil,hashlib,subprocess,sys
D=Path(__file__).resolve().parent;A=D/'staged_art';R=D/'raster_revision_02'
assert not R.exists();R.mkdir();shutil.copytree(A,R/'staged_before')
for n in ['layout_adjustments.json','offline_Up.png','offline_Down.png','offline_rig_proof.png','parts_final_retouch.png']:shutil.copy2(D/n,R/n)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
records=[]
for name in ['Up_HeadNormal','Up_HeadAngry','Up_HeadDead']:
    p=A/(name+'.png');before=sha(p);im=Image.open(p).convert('RGBA');dr=ImageDraw.Draw(im)
    dr.polygon([(140,31),(164,56),(140,81),(115,56)],fill=(244,177,28,255))
    im.save(p);records.append(dict(sprite=name,parent_sha256=before,sha256=sha(p),change='Fill complete front-facing jewel inset on back of crown with gold'))
p=A/'Up_Body.png';before=sha(p);im=Image.open(p).convert('RGBA');w,h=im.size
left=[(31,185),(33,215),(34,247),(39,278),(49,306),(63,331),(82,352),(108,370),(136,382),(165,386)]
mask=Image.new('L',(w,h));dr=ImageDraw.Draw(mask)
poly=[(0,0),(w,0),(w,184)]+[(w-1-x,y) for x,y in left]+list(reversed(left))+[(0,184)]
dr.polygon(poly,fill=255)
alpha=im.getchannel('A');import PIL.ImageChops
im.putalpha(PIL.ImageChops.multiply(alpha,mask))
dr=ImageDraw.Draw(im);dr.line(left,fill=(48,42,25,255),width=5,joint='curve');dr.line([(w-1-x,y) for x,y in left],fill=(48,42,25,255),width=5,joint='curve')
im.save(p);records.append(dict(sprite='Up_Body',parent_sha256=before,sha256=sha(p),change='Clip two generated painted hind-leg lobes outside torso; retain original back fur and add matching outline only at clipped boundary. Four articulated rig legs remain sole legs.'))
adj=json.loads((D/'layout_adjustments.json').read_text())
for side,sign in [('L',-1),('R',1)]:
    adj['parts']['Down/Hind'+side].update(x=sign*.16,y=.62,width=.15,height=.21,angle=sign*30)
(D/'layout_adjustments.json').write_text(json.dumps(adj,indent=2)+'\n',encoding='utf-8')
manifest=json.loads((A/'RatKing_Directions.sprites.json').read_text());atlas=Image.open(A/'RatKing_Directions.png').convert('RGBA')
for s in manifest['sprites']:
    im=Image.open(A/(s['name']+'.png')).convert('RGBA');atlas.paste(im,(s['x'],2048-s['y']-s['h']))
atlas.save(A/'RatKing_Directions.png')
(R/'changes.json').write_text(json.dumps(dict(records=records,method='local deterministic correction, no new paid output'),indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(D.parent/'adjust_layout.py'),'RatKing'],check=True)
subprocess.run([sys.executable,str(D.parent/'render_staged_rig.py'),'RatKing'],check=True)
board=Image.new('RGB',(1400,740),(40,48,37));draw=ImageDraw.Draw(board)
for i,s in enumerate(manifest['sprites']):
    key=s['name'];im=Image.open(A/(key+'.png')).convert('RGBA');im.thumbnail((185,315));x=i%7*200+(200-im.width)//2;y=i//7*370+35
    board.paste(im,(x,y),im);draw.text((i%7*200+4,i//7*370+8),key,fill='white')
board.save(D/'parts_final_retouch.png')
print('RatKing offline revision 02 complete; no production mutation')
