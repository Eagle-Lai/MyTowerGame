from session_current import *
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import numpy as np
import shutil, subprocess

owner()
art=HERE/'staged_art'
backup=HERE/'staged_art_before_body_r04'
assert not backup.exists()
shutil.copytree(art,backup)
for name in ['offline_rig_proof.png','offline_Up.png','offline_Down.png','parts_clean.png']:
    shutil.copy2(HERE/name,HERE/(Path(name).stem+'_before_body_r04'+Path(name).suffix))
p=art/'Down_Body.png'
original=Image.open(p).convert('RGBA')
a=np.array(original); before=a.copy()
mask=Image.new('L',original.size)
draw=ImageDraw.Draw(mask)
draw.rectangle((46,97,104,146),fill=255)
draw.rectangle((216,97,273,146),fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(3))
weight=np.array(mask,dtype=float)/255
# Both rectangles are inside the cream torso; preserve its complete outer contour,
# central taupe fur, all four lower spots and existing alpha cleanup.
interior=np.array(original.getchannel('A').filter(ImageFilter.MinFilter(9)))==255
weight*=interior
a[:,:,:3]=np.rint(a[:,:,:3]*(1-weight[:,:,None])+np.array([232,228,218])*weight[:,:,None]).astype('uint8')
assert np.array_equal(a[:,:,3],before[:,:,3])
Image.fromarray(a).save(p)
manifest=read(art/(NAME+'_Directions.sprites.json'))
atlas=Image.new('RGBA',(manifest['width'],manifest['height']))
for part in manifest['sprites']:
    im=Image.open(art/(part['name']+'.png')).convert('RGBA')
    assert im.size==(part['w'],part['h'])
    atlas.alpha_composite(im,(part['x'],manifest['height']-part['y']-part['h']))
atlas.save(art/(NAME+'_Directions.png'))
proof=Image.new('RGB',(1600,700),(40,48,37));draw=ImageDraw.Draw(proof)
for i,part in enumerate(manifest['sprites']):
    im=Image.open(art/(part['name']+'.png')).convert('RGBA');im.thumbnail((195,300))
    proof.paste(im,(i%8*200+(200-im.width)//2,i//8*350+35),im)
    draw.text((i%8*200+5,i//8*350+8),part['name'],fill='white')
proof.save(HERE/'parts_clean.png')
Image.fromarray(a).resize((622,894)).save(HERE/'Down_Body_detail_r04.png')
save(HERE/'staged_body_cleanup_r04_20261029.json',{
    'observed_at':now(),'parent_stage':'staged_art_before_body_r04',
    'parent_part_sha256':sha(backup/p.name),'output_part_sha256':sha(p),
    'method':'Local raster cleanup of two broken upper ochre/ear-motif remnants using feathered source cream. Retain central taupe fur, four lower spots, all contours and alpha. No paid request, no new AI return.',
    'regions_xyxy':[[46,97,104,146],[216,97,273,146]],
    'changed_pixels':int(np.any(a!=before,axis=2).sum()),'alpha_unchanged':True,
    'unchanged_other_parts':all(sha(q)==sha(backup/q.name) for q in art.glob('*.png') if q.name not in [p.name,NAME+'_Directions.png']),
    'requires_visual_review':True})
subprocess.run([sys.executable,str(RUN/'render_staged_rig.py'),NAME],check=True)
# Full silhouettes: use fit rather than crop, including original mirrored Right.
board=Image.new('RGB',(2000,720),(40,48,37));draw=ImageDraw.Draw(board)
ref=Image.open(HERE/'reference/battle_prefab_offline.png').convert('RGBA')
images=[ref,ImageOps.mirror(ref),Image.open(HERE/'offline_Up.png'),Image.open(HERE/'offline_Down.png')]
for i,(label,im) in enumerate(zip(['Left original','Right original mirrored','Up staged rear','Down staged front'],images)):
    im=im.convert('RGBA');bbox=im.getbbox();im=im.crop(bbox);im.thumbnail((460,600))
    board.paste(im,(i*500+(500-im.width)//2,70+(600-im.height)//2),im)
    draw.text((i*500+20,20),label+' - OFFLINE ONLY',fill='white')
board.save(HERE/'offline_four_directions_r04.png')
print('Body r04 staged; previous stage and alpha preserved.')
