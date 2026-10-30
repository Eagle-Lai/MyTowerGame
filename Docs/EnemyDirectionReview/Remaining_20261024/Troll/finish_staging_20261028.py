from session_troll import *
from PIL import Image,ImageDraw
import numpy as np,shutil
owner();art=D/'staged_art';old=D/'staged_before_pinhole_repair';assert not old.exists();shutil.copytree(art,old)
manifest=read(art/'Troll_Directions.sprites.json');atlas=Image.open(art/'Troll_Directions.png').convert('RGBA');report={}
for s in manifest['sprites']:
    p=art/(s['name']+'.png');im=Image.open(p).convert('RGBA');a=np.array(im);pad=Image.new('L',(im.width+2,im.height+2),255);pad.paste(Image.fromarray(np.where(a[:,:,3]==0,255,0).astype('uint8')),(1,1));ImageDraw.floodfill(pad,(0,0),127);holes=np.array(pad)[1:-1,1:-1]==255
    coords=np.argwhere(holes);original=a.copy()
    for y,x in coords:
        for radius in range(1,20):
            ya,yb=max(0,y-radius),min(im.height,y+radius+1);xa,xb=max(0,x-radius),min(im.width,x+radius+1)
            yy,xx=np.where(original[ya:yb,xa:xb,3]==255)
            if len(yy):
                j=np.argmin((yy+ya-y)**2+(xx+xa-x)**2);a[y,x]=original[yy[j]+ya,xx[j]+xa];break
        else:raise ValueError('No nearby original opaque colour')
    assert np.array_equal(original[~holes],a[~holes])
    Image.fromarray(a).save(p);atlas.paste(Image.fromarray(a),(s['x'],2048-s['y']-s['h']))
    report[s['name']]=dict(filled_pixels=len(coords),before_sha256=sha(old/p.name),after_sha256=sha(p),method='Only enclosed zero-alpha microholes filled from nearest original opaque pixel. Outside silhouette and all existing opaque/antialias pixels unchanged.')
atlas.save(art/'Troll_Directions.png');write(D/'chroma_pinhole_repair_20261028.json',dict(observed_at=now(),parts=report,total=sum(x['filled_pixels'] for x in report.values()),component_evidence='pinholes_components_20261028.json',max_component_pixels=12,staged_atlas_sha256=sha(art/'Troll_Directions.png')))
layout=read(art/'Troll_Directions.layout.json');adj=read(D/'layout_adjustments.json');adj.update(final_arm_roots={v['direction']:{p['name']:[p['x'],p['y']] for p in v['parts'] if p['role']=='arm'} for v in layout['views']},final_layout_sha256=sha(art/'Troll_Directions.layout.json'),final_sprites_sha256=sha(art/'Troll_Directions.sprites.json'));write(D/'layout_adjustments.json',adj)
subprocess.run([sys.executable,str(H/'render_staged_rig.py'),NAME],check=True)
# Wider offline proof only; production layout stays identical. Original helper is not modified.
source=(H/'render_staged_rig.py').read_text(encoding='utf-8').replace('resolution=800;ppu=600/height','resolution=1000;ppu=500/height').replace('y=700-','y=780-').replace('(2400,880)','(3000,1000)').replace('(760,720)','(940,840)').replace('(800-reference.width)//2','(1000-reference.width)//2').replace('(index+1)*800','(index+1)*1000').replace("'offline_'+view['direction']","'offline_wide_'+view['direction']").replace("'offline_rig_proof.png'","'offline_wide_rig_proof.png'")
sys.argv=[str(H/'render_staged_rig.py'),NAME];exec(compile(source,str(H/'render_staged_rig.py'),'exec'),{'__file__':str(H/'render_staged_rig.py'),'__name__':'__main__'})
print(json.dumps(dict(filled_pixels=sum(x['filled_pixels'] for x in report.values()),parts=len(report))))
