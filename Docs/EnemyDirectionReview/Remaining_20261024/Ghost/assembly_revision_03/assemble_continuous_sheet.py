from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
from PIL import ImageFilter
P=Path(__file__).resolve().parents[1]
manifest={'revision':'assembly_revision_03','reason':'Revision_02 failed due to tiny low-alpha stray background pixels expanding crop bounds; revision_03 selects largest opaque component and fills interior. Observed seam and flap-root gap in first offline proof. Merge upper sheet and generated hem as a continuous whole-sheet head-state sprite, matching original single visible Body renderer anatomy. Keep transparent Body compatibility slices and two independently animated short side flaps. No shared code changes.','directions':{}}
for direction in ['Up','Down']:
 source=P/'generation'/direction/('revision_01/raw.png' if direction=='Up' else 'raw.png')
 raw=Image.open(source).convert('RGB')
 def clean(rect):
  v=np.asarray(raw.crop(rect)).astype(float);a=1-np.maximum(0,np.minimum(v[:,:,0],v[:,:,2])-v[:,:,1])/255;a[a<.12]=0
  safe=np.maximum(a,.001)
  rgb=(v-(1-a[:,:,None])*np.array([255,0,255]))/safe[:,:,None]
  out=np.dstack([np.clip(rgb,0,255),a*255]).astype('uint8');out[a==0,:3]=0
  solid=a>.5;ys=np.where(solid.sum(axis=1)>=8)[0];xs=np.where(solid.sum(axis=0)>=8)[0];bounds=(int(xs[0]),int(ys[0]),int(xs[-1])+1,int(ys[-1])+1);support=np.asarray(Image.fromarray((solid*255).astype('uint8')).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(5)))>0;out[~support]=0;im=Image.fromarray(out,'RGBA');return im.crop(bounds)
 rects=[[0,0,384,510],[384,0,768,510],[768,0,1152,510],[1152,0,1536,510],[0,512,384,1024]]
 upper=[clean(x) for x in rects[:3]];hem=clean(rects[3]);flap=clean(rects[4])
 if direction=='Up':upper=[upper[0].copy() for _ in range(3)]
 hem=hem.crop((0,90 if direction=='Up' else 110,hem.width,hem.height))
 merged=[]
 for im in upper:
  cut=im.height-3 if direction=='Up' else 260
  im=im.crop((0,0,im.width,cut));a=np.array(im)[:,:,3];ys=np.where(a[-5]>150)[0];left,right=int(ys[0]),int(ys[-1])+1
  w=right-left;hh=round(hem.height*w/hem.width);piece=hem.resize((w,hh),Image.Resampling.LANCZOS)
  # Join at complete cross sections; overlap avoids any transparent seam.
  full=Image.new('RGBA',(im.width,im.height+hh-3));full.alpha_composite(im,(0,0));full.alpha_composite(piece,(left,im.height-3));merged.append(full)
 width=max(x.width for x in merged);height=max(x.height for x in merged)
 outputs=[]
 for i,name in enumerate(['HeadNormal','HeadAngry','HeadDead']):
  im=merged[i];c=Image.new('RGBA',(width,height));c.alpha_composite(im,((width-im.width)//2,(height-im.height)//2));outputs.append(c)
 outputs += [Image.new('RGBA',(1,1),(0,0,0,0)),flap]
 sheet=Image.new('RGBA',(1536,1024))
 for i,im in enumerate(outputs):
  im=im.copy();im.thumbnail((345,460),Image.Resampling.LANCZOS);sheet.alpha_composite(im,((i%4)*384+(384-im.width)//2,(i//4)*512+(512-im.height)//2))
 out=P/'assembly_revision_03'/(direction+'_assembled_parts.png');sheet.save(out)
 manifest['directions'][direction]={'source':source.relative_to(P).as_posix(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output':out.relative_to(P).as_posix(),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'upper_size':[width,height]}
(P/'assembly_revision_03/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
selection={'Up':'assembly_revision_03/Up_assembled_parts.png','Down':'assembly_revision_03/Down_assembled_parts.png','transparent_parts':['Up_Body','Down_Body'],'rectangles':{}}
for direction in ['Up','Down']:
 for i,name in enumerate(['HeadNormal','HeadAngry','HeadDead','Body','Flap']):selection['rectangles'][direction+'_'+name]=[(i%4)*384,(i//4)*512,(i%4+1)*384,(i//4+1)*512]
(P/'art_selection.json').write_text(json.dumps(selection,indent=2),encoding='utf-8')
a={'note':manifest['reason'],'layout':{'motion':{'legAngle':0,'legLift':0,'bodyBob':.018,'bodyRoll':0,'tailSwing':0}},'parts':{}}
for direction in ['Up','Down']:
 a['parts'][direction+'/Head']={'x':0,'y':.5,'width':.75,'height':1.0}
 a['parts'][direction+'/Body']={'x':0,'y':.5,'width':.01,'height':.01}
 for side,sign in [('L',-1),('R',1)]:a['parts'][direction+'/Flap'+side]={'x':sign*(.30 if direction=='Up' else .29),'y':.46,'width':.17,'height':.10,'order':15,'phase':0}
(P/'layout_adjustments.json').write_text(json.dumps(a,indent=2),encoding='utf-8')
