"""RatKing local raster/layout revision 01; preserve paid originals and old staging."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,hashlib,shutil,subprocess,sys
D=Path(__file__).resolve().parent;A=D/'staged_art';R=D/'raster_revision_01'
assert not R.exists(),'Review existing revision; do not overwrite evidence'
R.mkdir()
for n in ['parts_clean.png','offline_Up.png','offline_Down.png','offline_rig_proof.png','processing.json']:
    shutil.copy2(D/n,R/n)
shutil.copytree(A,R/'staged_before')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
manifest=json.loads((A/'RatKing_Directions.sprites.json').read_text())
atlas=Image.open(A/'RatKing_Directions.png').convert('RGBA');records=[]
for s in manifest['sprites']:
    key=s['name'];p=A/(key+'.png');im=Image.open(p).convert('RGBA')
    before=sha(p);pixels=np.array(im);h,w=pixels.shape[:2];yy,xx=np.indices((h,w));changes=[]
    if key.startswith('Up_Head'):
        # Ear outer contours and the single hoop remain. Replace the triangular inner pad
        # with uninterrupted olive back-of-ear color, never paint a face on the rear head.
        regions=Image.new('L',(w,h));dr=ImageDraw.Draw(regions)
        def poly(points):dr.polygon([(round(x*w),round(y*h)) for x,y in points],fill=255)
        poly([(.018,.278),(.075,.260),(.190,.280),(.285,.336),(.212,.458),(.075,.491),(.032,.395)])
        poly([(.714,.335),(.812,.277),(.928,.260),(.982,.278),(.968,.395),(.920,.489),(.788,.459)])
        region=np.array(regions.filter(ImageFilter.GaussianBlur(.6)))/255
        mask=(pixels[:,:,3]>230)&(region>0)
        for ch,(left,right) in enumerate([(109,83),(94,72),(54,42)]):
            target=left+(right-left)*np.clip((xx/w-.02)/.96,0,1)
            pixels[:,:,ch][mask]=(pixels[:,:,ch][mask]*(1-region[mask])+target[mask]*region[mask]).astype(np.uint8)
        # Black inset is visible from front only; back crown remains uninterrupted gold.
        crown=(yy<h*.24)&(xx>w*.39)&(xx<w*.61)&(pixels[:,:,0]<90)&(pixels[:,:,1]<90)&(pixels[:,:,3]>220)
        # Restrict to the inset itself, leaving crown outer dark contour intact.
        diamond=(abs(xx/w-.50)/.048+abs(yy/h-.145)/.045)<1.05
        crown &= diamond
        pixels[:,:,:3][crown]=[227,161,25]
        changes+=['Repaint only rear inner-ear pads to olive outer-ear surfaces; preserve hoop and contours','Back crown inset filled gold; no frontal jewel on rear']
    if key in ['Up_LegFront','Up_LegBack']:
        interior=np.array(im.getchannel('A').filter(ImageFilter.MinFilter(7)))>220
        fill=(yy>=h*.73)&interior
        blend=np.clip((yy-h*.73)/(h*.028),0,1)
        for ch,(light,dark) in enumerate([(139,111),(112,89),(54,43)]):
            target=light+(dark-light)*np.clip(xx/w,0,1)-np.clip((yy/h-.73)/.27,0,1)*7
            pixels[:,:,ch][fill]=(pixels[:,:,ch][fill]*(1-blend[fill])+target[fill]*blend[fill]).astype(np.uint8)
        changes.append('Remove frontal toe grooves with continuous rear-heel shading, preserve outside contour and alpha')
    # Neutralize leftover chroma only at a true alpha edge, never remove opaque organs.
    alpha=Image.fromarray(pixels[:,:,3]);edge=(pixels[:,:,3]>0)&(np.array(alpha.filter(ImageFilter.MinFilter(5)))<220)
    rgb=pixels[:,:,:3].astype(np.int16);fringe=edge&(rgb[:,:,2]>rgb[:,:,1]+8)
    pixels[:,:,2][fringe]=np.minimum(rgb[:,:,2][fringe],rgb[:,:,1][fringe]+3).astype(np.uint8)
    if fringe.any():changes.append('Neutralize blue/magenta edge chroma without changing alpha')
    im=Image.fromarray(pixels);im.save(p);atlas.paste(im,(s['x'],2048-s['y']-s['h']))
    records.append(dict(sprite=key,parent_sha256=before,sha256=sha(p),changes=changes))
atlas.save(A/'RatKing_Directions.png')
parts={
 'Up/Body':dict(y=.52,width=.70,height=.62),
 'Up/Head':dict(y=.84,width=.67,height=.35,order=25),
 'Up/Tail':dict(x=0,y=.30,width=.16,height=.31,order=5,angle=180),
 'Down/Body':dict(y=.59,width=.70,height=.62),
 'Down/Head':dict(y=.40,width=.59,height=.47),
 'Down/Tail':dict(x=.02,y=.88,width=.14,height=.29,order=5,angle=0)
}
for side,sign in [('L',-1),('R',1)]:
    parts['Up/Fore'+side]=dict(x=sign*.10,y=.47,width=.14,height=.20,angle=0)
    parts['Up/Hind'+side]=dict(x=sign*.20,y=.35,width=.16,height=.24,angle=sign*8)
    parts['Down/Fore'+side]=dict(x=sign*.16,y=.40,width=.16,height=.25,angle=sign*18)
    parts['Down/Hind'+side]=dict(x=sign*.17,y=.66,width=.17,height=.27,angle=sign*45)
adjust=dict(layout={'motion':dict(legAngle=8.5,legLift=.13,bodyBob=.004,bodyRoll=.8,tailSwing=6)},parts=parts)
(D/'layout_adjustments.json').write_text(json.dumps(adjust,indent=2)+'\n',encoding='utf-8')
(R/'changes.json').write_text(json.dumps(dict(method='local deterministic raster correction; not a new provider output',records=records,raw_sources={k:sha(D/'generation'/k/'raw.png') for k in ['Up','Down']}),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(D.parent/'adjust_layout.py'),'RatKing'],check=True)
subprocess.run([sys.executable,str(D.parent/'render_staged_rig.py'),'RatKing'],check=True)
board=Image.new('RGB',(1400,740),(40,48,37));draw=ImageDraw.Draw(board)
for i,s in enumerate(manifest['sprites']):
    key=s['name'];im=Image.open(A/(key+'.png')).convert('RGBA');im.thumbnail((185,315))
    x=i%7*200+(200-im.width)//2;y=i//7*370+35
    board.paste(im,(x,y),im);draw.text((i%7*200+4,i//7*370+8),key,fill='white')
board.save(D/'parts_final_retouch.png')
print('RatKing raster/layout revision 01 complete in Docs only')
