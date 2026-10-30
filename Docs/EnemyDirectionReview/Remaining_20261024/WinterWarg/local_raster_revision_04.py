"""Repair the observed r03 patch artifacts, keeping every prior image."""
from session_winterwarg import *
from PIL import Image,ImageDraw,ImageFilter
import numpy as np
owner()
src=D/'generation/Up/revision_02/raw.png';out=D/'generation/Up/local_revision_04'
assert not out.exists();out.mkdir()
im=Image.open(src).convert('RGB');a=np.asarray(im).copy()
# Work only on the selected normal rear head; staged rear expressions reuse it exactly.
mask=Image.new('L',im.size);dr=ImageDraw.Draw(mask)
dr.polygon([(146,204),(213,204),(220,230),(236,264),(216,273),(217,297),(198,338),(179,345),(158,317),(147,285),(147,276),(126,275),(129,249),(143,229)],fill=255)
patch=Image.new('RGB',im.size,(234,231,222))
im.paste(patch,(0,0),mask.filter(ImageFilter.GaussianBlur(.6)))
# Short crown tip continues the original upper tuft and ends above the nape.
s=4;layer=Image.new('RGBA',(160*s,120*s));d=ImageDraw.Draw(layer)
poly=[(34,10),(100,10),(110,29),(95,27),(95,42),(81,38),(68,60),(53,48),(39,48),(42,34),(22,35)]
d.polygon([(x*s,y*s) for x,y in poly],fill=(113,93,50),outline=(48,38,17),width=5*s)
d.polygon([(42*s,13*s),(95*s,13*s),(83*s,27*s),(69*s,45*s),(57*s,35*s)],fill=(139,116,66))
layer=layer.resize((160,120),Image.Resampling.LANCZOS)
im.paste(layer,(112,193),layer)

for box in [(120,840,250,921),(520,840,650,921)]:
    rgb=np.asarray(Image.open(src).convert('RGB').crop(box)).copy();v=rgb.astype(int)
    fg=(v[:,:,2]<=v[:,:,1]+8)&(v[:,:,2]<=v[:,:,0]+12)
    for y in range(12,62):
        xs=np.where(fg[y])[0]
        if len(xs)<20:continue
        l,r=xs[0],xs[-1];row=rgb[y]
        bright=row[(row[:,0]>190)&(np.arange(len(row))>l+8)&(np.arange(len(row))<r-8)]
        color=np.median(bright,axis=0) if len(bright) else [233,229,219]
        for x in range(l+8,r-7):
            if max(rgb[y,x])<130:rgb[y,x]=color
    # Replace only the last heel rim, with endpoints read from the original silhouette.
    piece=Image.fromarray(rgb);cut=50
    xs=np.where(fg[cut])[0];l,r=int(xs[0]),int(xs[-1]);w=r-l
    high=piece.resize((piece.width*4,piece.height*4),Image.Resampling.NEAREST);d=ImageDraw.Draw(high)
    d.rectangle((0,cut*4,high.width,high.height),fill=(255,0,255))
    pts=[(l,cut),(l+1,cut+8),(l+w*.1,cut+14),(l+w*.3,cut+18),(l+w*.5,cut+20),(l+w*.7,cut+18),(r-w*.1,cut+14),(r-1,cut+8),(r,cut)]
    d.polygon([(round(x*4),round(y*4)) for x,y in pts],fill=(190,181,163))
    d.line([(round(x*4),round(y*4)) for x,y in pts],fill=(39,31,15),width=6*4,joint='curve')
    im.paste(high.resize(piece.size,Image.Resampling.LANCZOS),(box[0],box[1]))
im.save(out/'raw.png')
write(out/'manifest.json',{'created_at':now(),'kind':'local pixel retouch; no API','source':str(src.relative_to(D)),'source_sha256':sha(src),'output_sha256':sha(out/'raw.png'),'prior':'local_revision_03 retained, rejected: crest ghosts and ankle seams','repairs':['Solid cream nape, short source-style crown tuft on normal rear head; same rear image for all states.','Original leg outlines retained; internal toe lines removed and heel base smoothed from measured row boundaries.'],'status':'pending actual visual inspection'},True)
sel=read(D/'art_selection.json');sel['Up']='generation/Up/local_revision_04/raw.png';sel['note']='Local revision04 fixes observed revision03 patch artifacts. Up states reuse the normal rear head during extraction; all API raw outputs and prior retouch are retained.';write(D/'art_selection.json',sel)
print(out/'raw.png')
