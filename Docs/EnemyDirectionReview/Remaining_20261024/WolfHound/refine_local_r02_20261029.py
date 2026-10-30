from session_current import *
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,shutil,subprocess
owner()
shutil.copytree(HERE/'staged_art',HERE/'staged_art_before_local_r02')
for f in ['art_selection.json','layout_adjustments.json','parts_clean.png','offline_rig_proof.png','offline_Up.png','offline_Down.png']:
 shutil.copy2(HERE/f,HERE/(Path(f).stem+'_before_local_r02'+Path(f).suffix))
selection=read(HERE/'art_selection.json')
for view in ['Up','Down']:
 parent=HERE/selection[view];out=HERE/'generation'/view/'local_revision_02';out.mkdir()
 im=Image.open(parent).convert('RGBA');a=np.array(im)
 original=np.array(Image.open(HERE/'generation'/view/'raw.png').convert('RGBA'))
 operations=[]
 for role in (['Body','LegFront','LegBack'] if view=='Up' else ['Body']):
  box=selection['rectangles'][view+'_'+role];x0,y0,x1,y1=box
  fg=original[y0:y1,x0:x1,3]>=128
  yy,xx=np.where(fg);left,top,right,bottom=xx.min(),yy.min(),xx.max()+1,yy.max()+1
  w,h=right-left,bottom-top
  inner=np.asarray(Image.fromarray(fg.astype('uint8')*255).filter(ImageFilter.MinFilter(11)))>0
  paint=Image.new('RGB',(x1-x0,y1-y0),(77,64,39));d=ImageDraw.Draw(paint)
  def pts(points):return [(left+round(px*w),top+round(py*h)) for px,py in points]
  if role=='Body':
   # Continuous complete torso recolor follows actual opaque contour, with source's broad jagged fur and round ochre spots.
   d.polygon(pts([(.28,0),(.72,0),(.75,.14),(.66,.11),(.83,.27),(.71,.23),(.79,.48),(.68,.43),(.64,.64),(.55,.58),(.5,.72),(.44,.61),(.34,.65),(.31,.48),(.2,.5),(.28,.29),(.18,.32),(.26,.14)]),fill=(114,95,61))
   for cx,cy,rx,ry in [(.17,.52,.065,.065),(.82,.52,.065,.065),(.22,.78,.065,.055),(.76,.77,.065,.055)]:
    d.ellipse((left+(cx-rx)*w,top+(cy-ry)*h,left+(cx+rx)*w,top+(cy+ry)*h),fill=(143,100,20))
  elif role=='LegFront':
   d.polygon(pts([(.17,0),(.92,0),(.76,.67),(.78,1),(.18,1),(.25,.7),(.36,.4)]),fill=(114,95,61))
   d.ellipse((left+.50*w,top+.06*h,left+.78*w,top+.23*h),fill=(143,100,20))
  else:
   d.ellipse((left+.13*w,top+.07*h,left+.76*w,top+.48*h),fill=(114,95,61))
   d.polygon(pts([(.52,.44),(.80,.47),(.68,.73),(.75,1),(.13,1),(.24,.72),(.49,.65)]),fill=(114,95,61))
  crop=a[y0:y1,x0:x1,:3];crop[inner]=np.array(paint)[inner]
  operations.append({'part':role,'region':box,'pixels':int(inner.sum()),'method':'Full connected silhouette interior, 5px inset from original alpha boundary. Source palette broad jagged fur and ochre circles; original outside contour preserved. Up legs have continuous plain back heel without front toes or rectangular patch seam.'})
 Image.fromarray(a,'RGBA').convert('RGB').save(out/'raw.png')
 save(out/'processing.json',{'observed_at':now(),'parent':parent.relative_to(HERE).as_posix(),'parent_sha256':sha(parent),'output_sha256':sha(out/'raw.png'),
   'new_AI_return':False,'operations':operations,'reason':'Local01 lower paw fill had a flat horizontal boundary; replace complete connected interiors. Simplify muddy generated torso shading to original broad flat source palette.'})
 selection[view]=(out/'raw.png').relative_to(HERE).as_posix()
 selection['source_sha256'][view]=sha(out/'raw.png')
selection['note']+=' Local02 whole connected torso and Up leg interior source-palette refinement; local01 preserved and rejected for lower-paw horizontal boundary.'
(HERE/'art_selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
layout=read(HERE/'layout_adjustments.json');p=layout['parts']
p.update({'Up/Body':dict(y=.43,width=.64,height=.64),'Up/Head':dict(y=.77,width=.56,height=.45,order=30),
 'Up/Tail':dict(x=-.01,y=.235,width=.27,height=.31,order=31,angle=-8),
 'Down/Body':dict(y=.62,width=.65,height=.66),'Down/Head':dict(y=.50,width=.65,height=.60,order=35),
 'Down/Tail':dict(x=.17,y=.80,width=.28,height=.33,order=5,angle=-14)})
for side,sign in [('L',-1),('R',1)]:
 p['Up/Fore'+side]=dict(x=sign*.22,y=.57,width=.15,height=.22,angle=sign*8)
 p['Up/Hind'+side]=dict(x=sign*.19,y=.24,width=.18,height=.22,angle=sign*2)
 p['Down/Fore'+side]=dict(x=sign*.16,y=.30,width=.17,height=.25,angle=sign*2)
 p['Down/Hind'+side]=dict(x=sign*.21,y=.69,width=.16,height=.24,angle=sign*10)
layout['reason']+=' Local02 compact vertical scale and full buried leg roots; tail root in rump, far limbs mostly occluded by axial body.'
(HERE/'layout_adjustments.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(RUN/'character_step.py'),'stage',NAME],check=True)
