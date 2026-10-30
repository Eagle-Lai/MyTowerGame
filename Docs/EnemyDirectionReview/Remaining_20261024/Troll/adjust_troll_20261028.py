from session_troll import *
import shutil,numpy as np
from PIL import Image,ImageDraw
owner();art=D/'staged_art';out=D/'offline_initial_default';assert not out.exists();out.mkdir()
for p in ['offline_rig_proof.png','offline_Up.png','offline_Down.png','parts_clean.png']:shutil.copy2(D/p,out/p)
for p in art.iterdir():shutil.copy2(p,out/p.name)
manifest=read(art/'Troll_Directions.sprites.json');layout=read(art/'Troll_Directions.layout.json');h=layout['referenceHeight'];bottom=layout['referenceBottom']
pivots={'Up_ArmWeapon':(.307,.955),'Down_ArmWeapon':(.855,.955),'Up_ArmFree':(.31,.95),'Down_ArmFree':(.46,.95)}
for s in manifest['sprites']:
    if s['name'] in pivots:s['pivotX'],s['pivotY']=pivots[s['name']]
for view in layout['views']:
    for p in view['parts']:
        if p['role']=='arm':
            p['y']=bottom+.73*h
            if p['name']=='ArmR':p['width']=.61*h;p['height']=.65*h
        if p['role']=='leg':p['height']=.24*h;p['y']=bottom+.228*h
write(art/'Troll_Directions.sprites.json',manifest);write(art/'Troll_Directions.layout.json',layout)
write(D/'layout_adjustments.json',dict(observed_at=now(),reason='Combined weapon-arm shoulder is off-centre in its actual image. Measure actual shoulder roots, not overall image centre. Align anatomical right weapon to viewer-right Up and viewer-left Down. Shorten two legs toward source stout proportions.',pivots=pivots,arm_root_y_fraction=.73,weapon_arm_max_width_fraction=.61,weapon_arm_max_height_fraction=.65,leg_height_fraction=.24,leg_root_y_fraction=.228,original='offline_initial_default',final_layout_sha256=sha(art/'Troll_Directions.layout.json'),final_sprites_sha256=sha(art/'Troll_Directions.sprites.json')))
alpha={}
for p in sorted(art.glob('Up_*.png'))+sorted(art.glob('Down_*.png')):
    im=Image.open(p).convert('RGBA');a=np.array(im)[:,:,3];pad=Image.new('L',(im.width+2,im.height+2),255);pad.paste(Image.fromarray(np.where(a==0,255,0).astype('uint8')),(1,1));ImageDraw.floodfill(pad,(0,0),127)
    holes=int((np.array(pad)==255).sum());alpha[p.name]=dict(size=list(im.size),internal_transparent_holes=holes,opaque=int((a==255).sum()),transparent=int((a==0).sum()),sha256=sha(p))
write(D/'alpha_quality_20261028.json',dict(observed_at=now(),parts=alpha,processing_sha256=sha(D/'processing.json')))
print(json.dumps(dict(alpha_parts=len(alpha),holes={n:v['internal_transparent_holes'] for n,v in alpha.items() if v['internal_transparent_holes']})))
subprocess.run([sys.executable,str(H/'render_staged_rig.py'),NAME],check=True)
