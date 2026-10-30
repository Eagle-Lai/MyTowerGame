from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,shutil,subprocess,sys
import numpy as np
D=Path(__file__).resolve().parent;A=D/'staged_art';R=D/'staged_art_r04'
assert not R.exists() and not (D/'installed_manifest.json').exists()
R.mkdir();shutil.copytree(A,R/'before_art')
for f in ['offline_rig_proof.png','offline_Up.png','offline_Down.png','parts_clean.png']:
    shutil.copy2(D/f,R/f)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
rows=[]
for p in sorted(A.glob('*.png')):
    if p.name=='Watchdog_Directions.png':continue
    a=np.array(Image.open(p).convert('RGBA'));rgb=a[:,:,:3].astype(np.int16)
    spill=(a[:,:,3]>0)&(rgb[:,:,2]>rgb[:,:,1]+6)&(rgb[:,:,0]>rgb[:,:,1]+10)
    before=sha(p);a[spill]=0;Image.fromarray(a).save(p)
    opaque=a[:,:,3]>0
    pad=Image.new('L',(a.shape[1]+2,a.shape[0]+2),255)
    pad.paste(Image.fromarray(np.where(opaque,0,255).astype('uint8')),(1,1));ImageDraw.floodfill(pad,(0,0),127)
    holes=int((np.array(pad)[1:-1,1:-1]==255).sum());assert holes==0
    rows.append({'part':p.name,'removed_spill_pixels':int(spill.sum()),'holes':holes,'before':before,'after':sha(p)})
spec=json.loads((A/'Watchdog_Directions.sprites.json').read_text(encoding='utf-8'))
atlas=Image.new('RGBA',(2048,2048))
proof=Image.new('RGB',(1600,700),(40,48,37));draw=ImageDraw.Draw(proof)
for i,s in enumerate(spec['sprites']):
    im=Image.open(A/(s['name']+'.png')).convert('RGBA');atlas.alpha_composite(im,(s['x'],2048-s['y']-s['h']))
    thumb=im.copy();thumb.thumbnail((195,300));proof.paste(thumb,(i%8*200+(200-thumb.width)//2,i//8*350+35),thumb)
    draw.text((i%8*200+5,i//8*350+8),s['name'],fill='white')
atlas.save(A/'Watchdog_Directions.png');proof.save(D/'parts_clean_final.png')
(R/'manifest.json').write_text(json.dumps({'revision':'art_r04','raw_unchanged':True,'parts':rows,'final_art':{p.name:sha(p) for p in A.iterdir() if p.is_file()}},indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(D.parent/'render_staged_rig.py'),'Watchdog'],check=True)
print(json.dumps({'parts':len(rows),'removed_spill_pixels':sum(r['removed_spill_pixels'] for r in rows),'holes':0}))
