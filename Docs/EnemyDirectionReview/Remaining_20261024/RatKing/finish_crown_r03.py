"""Final rear crown fill respects the existing outline; preserves all preceding evidence."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,shutil,hashlib,subprocess,sys
D=Path(__file__).resolve().parent;A=D/'staged_art';R=D/'raster_revision_03';assert not R.exists();R.mkdir()
shutil.copytree(A,R/'staged_before');shutil.copy2(D/'offline_rig_proof.png',R/'offline_rig_proof.png')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper();records=[]
for name in ['Up_HeadNormal','Up_HeadAngry','Up_HeadDead']:
    p=A/(name+'.png');before=sha(p);im=Image.open(p).convert('RGBA');original=Image.open(D/'raster_revision_01/staged_before'/(name+'.png')).convert('RGBA')
    im.paste(original.crop((0,0,original.width,76)),(0,0));a=np.array(im)
    dark=(a[:,:,0]<85)&(a[:,:,1]<80)&(a[:,:,2]<65)&(a[:,:,3]>200)
    mask=np.zeros(dark.shape,dtype=bool);stack=[(50,123)];seen=set()
    while stack:
        y,x=stack.pop()
        if (y,x) in seen or not (25<=y<82 and 110<=x<170) or not dark[y,x]:continue
        seen.add((y,x));mask[y,x]=True
        stack.extend([(y+1,x),(y-1,x),(y,x+1),(y,x-1)])
    assert 500<mask.sum()<700,mask.sum()
    a[:,:,:3][mask]=[243,174,24];im=Image.fromarray(a);im.save(p)
    records.append(dict(sprite=name,parent_sha256=before,sha256=sha(p),changed_pixels=int(mask.sum()),method='Restore original crown outline then fill only disconnected front jewel dark component with gold for its back surface'))
manifest=json.loads((A/'RatKing_Directions.sprites.json').read_text());atlas=Image.open(A/'RatKing_Directions.png').convert('RGBA')
for s in manifest['sprites']:atlas.paste(Image.open(A/(s['name']+'.png')),(s['x'],2048-s['y']-s['h']))
atlas.save(A/'RatKing_Directions.png');(R/'changes.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(D.parent/'render_staged_rig.py'),'RatKing'],check=True)
board=Image.new('RGB',(1400,740),(40,48,37));draw=ImageDraw.Draw(board)
for i,s in enumerate(manifest['sprites']):
    key=s['name'];im=Image.open(A/(key+'.png')).convert('RGBA');im.thumbnail((185,315));x=i%7*200+(200-im.width)//2;y=i//7*370+35
    board.paste(im,(x,y),im);draw.text((i%7*200+4,i//7*370+8),key,fill='white')
board.save(D/'parts_final_retouch.png')
print('Final crown revision 03 complete')
