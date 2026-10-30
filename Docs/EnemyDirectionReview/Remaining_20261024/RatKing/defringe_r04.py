"""Remove final chroma spill at translucent cutout edges, without changing geometry."""
from pathlib import Path
from PIL import Image,ImageFilter,ImageDraw
import numpy as np,json,hashlib,shutil,subprocess,sys
D=Path(__file__).resolve().parent;A=D/'staged_art';R=D/'raster_revision_04';assert not R.exists();R.mkdir();shutil.copytree(A,R/'staged_before')
shutil.copy2(D/'offline_rig_proof.png',R/'offline_rig_proof.png')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper();records=[]
manifest=json.loads((A/'RatKing_Directions.sprites.json').read_text());atlas=Image.open(A/'RatKing_Directions.png').convert('RGBA')
for s in manifest['sprites']:
    p=A/(s['name']+'.png');before=sha(p);im=Image.open(p).convert('RGBA');a=np.array(im);b=a[:,:,:3].astype(np.int16)
    edge=(a[:,:,3]>0)&(np.array(im.getchannel('A').filter(ImageFilter.MinFilter(5)))<220)
    spill=edge&(b[:,:,0]>b[:,:,1]+85)&(b[:,:,1]<130)
    a[:,:,0][spill]=(b[:,:,1][spill]+25).astype(np.uint8)
    a[:,:,2][spill]=np.minimum(b[:,:,2][spill],np.maximum(0,b[:,:,1][spill]-10)).astype(np.uint8)
    im=Image.fromarray(a);im.save(p);atlas.paste(im,(s['x'],2048-s['y']-s['h']))
    records.append(dict(sprite=s['name'],parent_sha256=before,sha256=sha(p),pixels=int(spill.sum()),method='Edge-only high red chroma spill corrected to neutral warm outline; no alpha or opaque interior removed'))
atlas.save(A/'RatKing_Directions.png');(R/'changes.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(D.parent/'render_staged_rig.py'),'RatKing'],check=True)
board=Image.new('RGB',(1400,740),(40,48,37));draw=ImageDraw.Draw(board)
for i,s in enumerate(manifest['sprites']):
    key=s['name'];im=Image.open(A/(key+'.png')).convert('RGBA');im.thumbnail((185,315));x=i%7*200+(200-im.width)//2;y=i//7*370+35
    board.paste(im,(x,y),im);draw.text((i%7*200+4,i//7*370+8),key,fill='white')
board.save(D/'parts_final_retouch.png')
print('Final edge-only revision 04 complete')
