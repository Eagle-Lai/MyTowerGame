from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from session_current import owner,save,sha,now
owner()
assert not (HERE/'staged_art').exists() and not (HERE/'art_selection.json').exists()
rects={
 'Up':{'HeadNormal':[50,125,335,440],'HeadAngry':[400,125,700,440],'HeadDead':[750,125,1050,440],
       'Body':[1110,75,1445,510],'LegFront':[110,590,285,880],'LegBack':[455,585,640,880],'Tail':[770,575,1050,905]},
 'Down':{'HeadNormal':[25,120,355,500],'HeadAngry':[395,120,725,505],'HeadDead':[775,120,1105,505],
         'Body':[1140,70,1505,530],'LegFront':[100,600,275,900],'LegBack':[425,595,645,900],'Tail':[775,570,1075,905]}}
def bezier(p0,p1,p2,p3,n=100):
 return [((1-t)**3*p0[0]+3*(1-t)**2*t*p1[0]+3*(1-t)*t*t*p2[0]+t**3*p3[0],(1-t)**3*p0[1]+3*(1-t)**2*t*p1[1]+3*(1-t)*t*t*p2[1]+t**3*p3[1]) for t in np.linspace(0,1,n)]
for direction in ['Up','Down']:
 src=HERE/'generation'/direction/'raw.png';out=src.parent/'local_revision_01';assert not out.exists();out.mkdir()
 raw=Image.open(src).convert('RGBA');a=np.array(raw);fg=a[:,:,3]>=128
 a[~fg]=[255,0,255,255];a[fg,3]=255
 operations=[]
 if direction=='Up':
  # Repaint the complete connected leg interiors, not a rectangular paw patch.
  for role in ['LegFront','LegBack']:
   x0,y0,x1,y1=rects['Up'][role];sil=np.zeros(fg.shape,dtype=np.uint8);sil[y0:y1,x0:x1]=fg[y0:y1,x0:x1]*255
   inner=np.asarray(Image.fromarray(sil).filter(ImageFilter.MinFilter(13)))>0
   painted=Image.new('RGB',raw.size,(109,101,81));d=ImageDraw.Draw(painted)
   if role=='LegFront':
    d.polygon([(204,625),(229,646),(239,705),(223,751),(229,792),(214,831),(188,844),(171,839),(189,812),(195,773),(194,738),(210,706)],fill=(130,124,107))
    d.ellipse((163,676,217,738),fill=(141,103,31))
   else:
    d.polygon([(536,608),(571,623),(589,651),(596,683),(583,717),(570,743),(568,785),(549,827),(512,843),(493,836),(519,810),(531,768),(533,726),(554,693)],fill=(131,125,107))
    d.ellipse((514,678,568,740),fill=(141,103,31))
   a[inner,:3]=np.asarray(painted)[inner]
   operations.append({'part':role,'region':[x0,y0,x1,y1],'pixels':int(inner.sum()),'method':'Repaint entire eroded connected leg interior with broad source gray-khaki plane, jagged highlight and one ochre spot; retain original complete dark outer silhouette. Smooth rear heel, no front toe strokes.'})
 else:
  # The model incorrectly attached two paws to the torso. Keep the original torso/saddle,
  # reshape only its lower silhouette into a rounded solid chest/neck attachment.
  curve=bezier((1159,380),(1176,433),(1245,449),(1319,452))+bezier((1319,452),(1390,449),(1468,433),(1483,380))[1:]
  keep=Image.new('L',raw.size,255);cut=Image.new('L',raw.size,0);d=ImageDraw.Draw(cut)
  d.polygon([(1140,0),(1505,0),(1505,380)]+list(reversed(curve))+[(1140,380)],fill=255)
  keep_a=np.asarray(cut)>0;roi=np.zeros(fg.shape,dtype=bool);roi[70:530,1140:1505]=True
  removed=roi&~keep_a&fg;a[removed]=[255,0,255,255]
  line=Image.new('RGBA',raw.size,(0,0,0,0));ld=ImageDraw.Draw(line);ld.line(curve,fill=(48,39,21,255),width=8,joint='curve')
  la=np.asarray(line);line_mask=(la[:,:,3]>0)&roi&keep_a
  a[line_mask]=la[line_mask]
  operations.append({'region':[1140,375,1505,530],'removed_pixels':int(removed.sum()),'new_contour':curve,'method':'Remove both erroneous attached front paws below smooth curved chest contour; retain upper torso, all saddle features and small throat tuft. Draw only continuous curved dark lower outline, no rectangular color fill.'})
 Image.fromarray(a,'RGBA').convert('RGB').save(out/'raw.png')
 save(out/'processing.json',{'observed_at':now(),'parent':src.relative_to(HERE).as_posix(),'parent_sha256':sha(src),'output_sha256':sha(out/'raw.png'),
  'method':'Local raster derivation, not an AI return. Threshold returned alpha at128; replace exterior only with exact magenta; targeted recorded anatomy corrections. Raw returned file remains unchanged.',
  'operations':operations,'new_AI_return':False})
save(HERE/'art_selection.json',{'Up':'generation/Up/local_revision_01/raw.png','Down':'generation/Down/local_revision_01/raw.png',
 'rectangles':{v+'_'+p:r for v,parts in rects.items() for p,r in parts.items()},
 'source_sha256':{v:sha(HERE/'generation'/v/'local_revision_01/raw.png') for v in ['Up','Down']},
 'note':'Both complete raw returns actually viewed. Own faceless rear head reused for all Up expressions; Up smooth heel interior and Down torso removes two erroneously attached paws. Explicit measured rectangles.'})
parts={'Up/Body':dict(y=.52,width=.66,height=.64),'Up/Head':dict(y=.87,width=.56,height=.42,order=25),
 'Up/Tail':dict(x=0,y=.40,width=.31,height=.36,order=30,angle=-5),
 'Down/Body':dict(y=.64,width=.66,height=.72),'Down/Head':dict(y=.42,width=.61,height=.52,order=35),
 'Down/Tail':dict(x=.19,y=.82,width=.31,height=.35,order=5,angle=20)}
for direction in ['Up','Down']:
 for side,sign in [('L',-1),('R',1)]:
  parts[f'{direction}/Fore{side}']=dict(x=sign*.16,y=.60 if direction=='Up' else .27,width=.18,height=.24,angle=sign*(15 if direction=='Up' else 2))
  parts[f'{direction}/Hind{side}']=dict(x=sign*.175,y=.29 if direction=='Up' else .70,width=.18,height=.24,angle=sign*(2 if direction=='Up' else 15))
changes={'reason':'Own mounted-wolf anatomy: one saddle and three ivory rear-rim spikes with single silver buckle, no rider/collar. Measured drooping tail uses actual upper-left root; short diagonal-pair steps and buried four limb roots.',
 'layout':{'motion':{'legAngle':6.8,'legLift':.026,'bodyBob':.0045,'bodyRoll':.65,'tailSwing':4.5}},'parts':parts,
 'sprites':{f'{v}_{r}':{'pivotX':.5,'pivotY':.94} for v in ['Up','Down'] for r in ['LegFront','LegBack']}}
changes['sprites'].update({'Up_Tail':{'pivotX':.055,'pivotY':.94},'Down_Tail':{'pivotX':.055,'pivotY':.94}})
save(HERE/'layout_adjustments.json',changes)
save(HERE/'raw_visual_review_20261029.json',{'observed_at':now(),'reviewed':[{'path':f'generation/{v}/raw.png','sha256':sha(HERE/'generation'/v/'raw.png'),'format':'PNG RGBA','size':[1536,1024]} for v in ['Up','Down']],
 'findings':'Own muted spotted gray-taupe wolf, unique saddle/three spikes/single silver X buckle, pointed ears, ivory eyes/small pupils and fangs, long broad drooping tail. Up heads truly faceless with plain ear backs; rear paws incorrectly had toe lines, locally corrected. Down frontal head expressions usable; torso incorrectly included two front paws, locally removed before four-leg assembly. Low-alpha exterior glows removed using returned alpha. No ground shadow.',
 'requests':2,'http200':2,'unknown':0,'paid_art_revisions':0,'stage_pending':True})
print('WolfMounfed measured local raster01 and layout01 prepared')
