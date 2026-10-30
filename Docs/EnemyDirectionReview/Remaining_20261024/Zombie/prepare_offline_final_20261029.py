from session_current import *
from PIL import Image,ImageDraw,ImageOps
import numpy as np,shutil

owner()
source=RUN/'render_staged_rig.py'
text=source.read_text(encoding='utf-8').replace('resolution=800;ppu=600/height','resolution=1000;ppu=600/height')
# Keep its image rendering function with a wider canvas; the existing 800px proof
# framing clips this correctly scaled long club. This changes Docs rendering only.
scope={'__file__':str(source),'__name__':'offline_Zombie'}
old=sys.argv;sys.argv=[str(source),NAME]
exec(text[:text.index("proof=Image.new('RGB'")],scope);sys.argv=old
for view in scope['layout']['views']:
 im=scope['render'](view);im.save(HERE/('offline_'+view['direction']+'.png'))
 assert im.getbbox()[0]>0 and im.getbbox()[2]<im.width,'Offline framing cropped club'
original=Image.open(HERE/'reference/battle_prefab_offline.png').convert('RGBA');original=original.crop(original.getbbox());original=original.resize((round(original.width*600/original.height),600),Image.Resampling.LANCZOS)
board=Image.new('RGB',(4000,900),(40,48,37));draw=ImageDraw.Draw(board)
for i,(label,im) in enumerate([('Left original source',original),('Right original mirror',original.transpose(Image.Transpose.FLIP_LEFT_RIGHT)),('Up staged',Image.open(HERE/'offline_Up.png')),('Down staged',Image.open(HERE/'offline_Down.png'))]):
 if i<2:board.paste(im,(i*1000+(1000-im.width)//2,120),im)
 else:board.paste(im,(i*1000,100),im)
 draw.text((i*1000+20,20),NAME+' '+label+' | OFFLINE only, equal source height scale',fill='white')
board.save(HERE/'offline_four_directions_final_20261029.png')
art=HERE/'staged_art';records=[]
for s in read(art/'Zombie_Directions.sprites.json')['sprites']:
 p=art/(s['name']+'.png');im=Image.open(p).convert('RGBA');a=np.asarray(im);alpha=a[:,:,3]
 exterior=ImageOps.expand(Image.fromarray(np.where(alpha==0,0,255).astype('uint8')),border=1,fill=0);ImageDraw.floodfill(exterior,(0,0),128)
 holes=int((np.asarray(exterior)[1:-1,1:-1]==0).sum());assert holes==0
 chroma=(a[:,:,0].astype(int)>a[:,:,1].astype(int)+60)&(a[:,:,2].astype(int)>a[:,:,1].astype(int)+60)&(alpha>0)
 assert not chroma.any()
 assert im.size==(s['w'],s['h']) and s['x']>=0 and s['y']>=0 and s['x']+s['w']<=2048 and s['y']+s['h']<=2048
 records.append({'sprite':s['name'],'sha256':sha(p),'size':list(im.size),'holes':holes,'magenta_pixels':int(chroma.sum()),'pivot':[s['pivotX'],s['pivotY']]})
save(HERE/'stage_alpha_rect_audit_final_20261029.json',{'observed_at':now(),'source_mask':'Existing spectral extraction, then recorded small-hole boundary median fill alpha01; all source raws preserved.','parts':records,'pass':True})
print(json.dumps({'sprites':len(records),'holes':0,'magenta':0,'offline_canvas':1000,'club_uncropped':True}))
