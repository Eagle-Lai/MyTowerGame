"""Source-preserving rear tuft/heel repair. Never changes paid raw returns."""
from session_winterwarg import *
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

owner()
source = D/'generation/Up/revision_02/raw.png'
out = D/'generation/Up/local_revision_03'
assert not out.exists()
out.mkdir()
original = Image.open(source).convert('RGB')
im = original.copy()
changes = []
for offset in [0,385,758]:
    box=(127+offset,156,235+offset,337)
    piece=original.crop(box).convert('RGBA')
    a=np.asarray(piece)
    yy,xx=np.mgrid[:piece.height,:piece.width]
    # Restrict to the observed central brown crest, not the two ochre cheek spots.
    poly=Image.new('L',piece.size)
    ImageDraw.Draw(poly).polygon([(33,0),(55,24),(88,7),(94,44),(81,62),(102,91),(105,111),(85,115),(85,140),(66,177),(49,180),(34,151),(22,121),(2,115),(8,93),(22,73),(12,52),(20,23)],fill=255)
    brown=(a[:,:,0].astype(int)-a[:,:,2].astype(int)>25)|((a[:,:,:3].max(axis=2))<105)
    mask=Image.fromarray((brown & (np.asarray(poly)>0)).astype('uint8')*255).filter(ImageFilter.MaxFilter(3))
    # Only the elongated lower crest needs removal; preserve its short original top.
    removal=np.asarray(mask).copy();removal[:55]=0
    remove=Image.fromarray(removal)
    patch=im.crop(box).copy();pa=np.asarray(patch).copy()
    for y in range(55,piece.height):
        active=np.where(removal[y]>0)[0]
        if not len(active):continue
        l=max(0,active[0]-7);r=min(piece.width-1,active[-1]+7)
        # Cream fur colors sampled just outside this crest, interpolated across it.
        left=np.median(np.asarray(original)[box[1]+y,max(0,box[0]+l-3):box[0]+l+1,:],axis=0)
        right=np.median(np.asarray(original)[box[1]+y,box[0]+r:box[0]+r+4,:],axis=0)
        for x in active:pa[y,x]=np.round(left*(1-x/(piece.width-1))+right*x/(piece.width-1))
    patch=Image.fromarray(pa)
    im.paste(patch,(box[0],box[1]),remove)
    # Retain an actual source tuft tip, shortened in height, ending near the crown.
    tip=original.crop((127+offset,211,235+offset,337)).convert('RGBA')
    tip.putalpha(mask.crop((0,55,piece.width,piece.height)))
    tip=tip.resize((108,46),Image.Resampling.LANCZOS)
    im.paste(tip,(127+offset,211),tip)
    changes.append({'part':'rear head','box':box,'method':'retain original crown; erase long lower crest with neighboring cream fur; shorten original tip'})

def curve(points,steps=18):
    result=[]
    for i in range(0,len(points)-1,3):
        p0,p1,p2,p3=points[i:i+4]
        for j in range(steps+1):
            t=j/steps;u=1-t
            result.append((u*u*u*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t*t*t*p3[0],u*u*u*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t*t*t*p3[1]))
    return result

# Both rear-view paw pads become smooth heels with no front-facing toe divisions.
for box,points in [
    ((124,843,245,918),[(19,0),(13,17),(8,31),(12,48),(14,65),(31,67),(58,68),(86,68),(106,65),(108,48),(112,30),(110,17),(105,0)]),
    ((527,843,639,918),[(22,0),(15,16),(7,30),(10,47),(11,63),(28,68),(56,68),(84,68),(101,63),(103,47),(107,29),(104,15),(99,0)])
]:
    w,h=box[2]-box[0],box[3]-box[1];s=4
    patch=Image.new('RGB',(w*s,h*s),(255,0,255));dr=ImageDraw.Draw(patch)
    outline=curve(points);path=[(x*s,y*s) for x,y in outline]
    dr.polygon(path,fill=(232,228,218))
    # A shallow warm-gray heel rim keeps the source cel-shaded material.
    shade=[(x*s,y*s) for x,y in outline if y>=43]
    if shade:dr.polygon(shade,fill=(190,181,163))
    dr.line(path,fill=(39,31,15),width=6*s,joint='curve')
    im.paste(patch.resize((w,h),Image.Resampling.LANCZOS),(box[0],box[1]))
    changes.append({'part':'rear heel','box':box,'method':'local smooth heel contour and source cream/taupe shading; no toe grooves'})

im.save(out/'raw.png')
write(out/'manifest.json',{'created_at':now(),'kind':'local pixel retouch, no API request','source':str(source.relative_to(D)),'source_sha256':sha(source),'output_sha256':sha(out/'raw.png'),'changes':changes,'paid_raw_preserved':True},True)
selection=read(D/'art_selection.json')
selection['Up']='generation/Up/local_revision_03/raw.png'
selection['rectangles'].update({
 'Down_HeadNormal':[20,110,365,480], 'Down_HeadAngry':[395,110,750,480], 'Down_HeadDead':[780,110,1130,480],
 'Down_Body':[1150,20,1525,530], 'Down_LegFront':[60,550,330,940], 'Down_LegBack':[440,550,720,940], 'Down_Tail':[790,550,1130,940]})
selection['note']='Up original paid revision02 retained; local_revision03 shortens rear crown tuft and replaces front toe marks with smooth heels. Down first HTTP200 raw retained and selected. Both use visually measured explicit crop rectangles.'
write(D/'art_selection.json',selection)
write(D/'raw_review_Down_20261029.json',{'observed_at':now(),'source':'generation/Down/raw.png','sha256':sha(D/'generation/Down/raw.png'),'format':'PNG','size':[1536,1024],'viewed':'full native raw image','findings':['Axial front face; three matching normal/angry/dead states, original long saber canines and round ears.','White/cream fur, ochre spots and original brown dorsal spines preserved.','Two anatomical leg types with front-facing clawed paws; solid shoulder and hip roots.','Torso excludes head/legs/tail; all seven parts separated; explicit body rectangle spans nominal row boundary.','Tail curves downward with root at upper-left concave edge; per-sprite pivot required.'],'raw_approved':True,'paid_generation_status':200},True)
stage('local_Up_art_repair_pending_visual_review',out/'manifest.json')
print(out/'raw.png')
