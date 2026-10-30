from session_winterwarg import *
from PIL import Image,ImageDraw,ImageFilter
import numpy as np
owner()
out=D/'generation/Up/local_revision_05';assert not out.exists();out.mkdir()
src=D/'generation/Up/revision_02/raw.png';im=Image.open(src).convert('RGB')
m=Image.new('L',im.size);ImageDraw.Draw(m).rectangle((124,208,244,346),fill=255)
im.paste(Image.new('RGB',im.size,(234,231,222)),(0,0),m.filter(ImageFilter.GaussianBlur(1)))
s=4;layer=Image.new('RGBA',(160*s,120*s));d=ImageDraw.Draw(layer)
poly=[(34,10),(100,10),(110,29),(95,27),(95,42),(81,38),(68,60),(53,48),(39,48),(42,34),(22,35)]
d.polygon([(x*s,y*s) for x,y in poly],fill=(113,93,50))
d.line([(x*s,y*s) for x,y in poly[1:]+[poly[0]]],fill=(48,38,17),width=5*s,joint='curve')
d.polygon([(42*s,10*s),(95*s,10*s),(83*s,27*s),(69*s,45*s),(57*s,35*s)],fill=(139,116,66))
layer=layer.resize((160,120),Image.Resampling.LANCZOS);im.paste(layer,(112,193),layer)
for box in [(120,840,250,921),(520,840,650,921)]:
    rgb=np.asarray(Image.open(src).convert('RGB').crop(box)).copy();v=rgb.astype(int)
    fg=(v[:,:,2]<=v[:,:,1]+8)&(v[:,:,2]<=v[:,:,0]+12)
    for y in range(10,61):
        xs=np.where(fg[y])[0]
        if len(xs)<20:continue
        l,r=xs[0],xs[-1]
        color=np.array([234,230,220]) if y<47 else np.array([232,228,218])
        rgb[y,l+7:r-6]=color
    piece=Image.fromarray(rgb);cut=50;xs=np.where(fg[cut])[0];l,r=int(xs[0]),int(xs[-1]);w=r-l
    high=piece.resize((piece.width*4,piece.height*4),Image.Resampling.NEAREST);d=ImageDraw.Draw(high)
    d.rectangle((0,cut*4,high.width,high.height),fill=(255,0,255))
    pts=[(l,cut),(l+1,cut+8),(l+w*.1,cut+14),(l+w*.3,cut+18),(l+w*.5,cut+20),(l+w*.7,cut+18),(r-w*.1,cut+14),(r-1,cut+8),(r,cut)]
    d.polygon([(round(x*4),round(y*4)) for x,y in pts],fill=(190,181,163))
    d.line([(round(x*4),round(y*4)) for x,y in pts],fill=(39,31,15),width=6*4,joint='curve')
    im.paste(high.resize(piece.size,Image.Resampling.LANCZOS),(box[0],box[1]))
im.save(out/'raw.png')
write(out/'manifest.json',{'created_at':now(),'source':str(src.relative_to(D)),'source_sha256':sha(src),'output_sha256':sha(out/'raw.png'),'kind':'local raster repair, no API','prior_rejected':['local_revision_03: crest ghosts/ankle seams','local_revision_04: residual nape and toe antialias marks'],'repairs':['short cream-backed crown tuft without horizontal top seam','solid heel interiors, source leg outline retained'],'rear_states':'All three rear states reuse selected normal head; paid raw retained unchanged.'},True)
sel=read(D/'art_selection.json');sel['Up']='generation/Up/local_revision_05/raw.png';sel['note']='Up local_revision05 removes reviewed pixel ghosts; selected normal rear head reused across all states. Down uses first successful raw. All prior paid/retouch sources retained.';write(D/'art_selection.json',sel)
adjust={'reason':'WinterWarg measured four-leg axial layout: short round ears, small crown tuft, broad dorsal-spined body, smooth rear heels, long top-root drooping tail. Caps buried inside shoulder/hip and diagonal pairs alternate.',
 'layout':{'motion':{'legAngle':8,'legLift':.025,'bodyBob':.007,'bodyRoll':.65,'tailSwing':5.5}},
 'parts':{
  'Up/Body':{'y':.54,'width':.72,'height':.69},'Up/Head':{'y':.83,'width':.73,'height':.46,'order':30},
  'Up/ForeL':{'x':-.19,'y':.57,'width':.18,'height':.28,'angle':-30},'Up/ForeR':{'x':.19,'y':.57,'width':.18,'height':.28,'angle':30},
  'Up/HindL':{'x':-.15,'y':.36,'width':.18,'height':.30,'angle':-5},'Up/HindR':{'x':.15,'y':.36,'width':.18,'height':.30,'angle':5},
  'Up/Tail':{'x':.00,'y':.40,'width':.24,'height':.38,'order':31},
  'Down/Body':{'y':.65,'width':.72,'height':.68},'Down/Head':{'y':.44,'width':.76,'height':.54},
  'Down/ForeL':{'x':-.15,'y':.38,'width':.18,'height':.32,'angle':-8},'Down/ForeR':{'x':.15,'y':.38,'width':.18,'height':.32,'angle':8},
  'Down/HindL':{'x':-.20,'y':.66,'width':.18,'height':.29,'angle':-35},'Down/HindR':{'x':.20,'y':.66,'width':.18,'height':.29,'angle':35},
  'Down/Tail':{'x':.12,'y':.88,'width':.24,'height':.37,'angle':-20,'order':5}},
 'sprites':{**{d+'_'+p:{'pivotX':.5,'pivotY':.94} for d in ['Up','Down'] for p in ['LegFront','LegBack']},'Up_Tail':{'pivotX':.18,'pivotY':.95},'Down_Tail':{'pivotX':.08,'pivotY':.74}}}
write(D/'layout_adjustments.json',adjust,True)
print(out/'raw.png')
