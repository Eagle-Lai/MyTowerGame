from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from session_current import owner,save,sha,now
owner()
assert not (HERE/'staged_art').exists() and not (HERE/'art_selection.json').exists()
rects={
 'Up':{'HeadNormal':[15,100,375,480],'HeadAngry':[400,100,755,485],'HeadDead':[790,100,1138,485],
       'Body':[1160,90,1515,518],'LegFront':[95,620,292,917],'LegBack':[450,610,705,920],'Tail':[790,560,1110,930]},
 'Down':{'HeadNormal':[15,110,375,490],'HeadAngry':[400,110,755,490],'HeadDead':[790,110,1138,500],
         'Body':[1160,110,1515,520],'LegFront':[95,590,295,910],'LegBack':[465,590,705,910],'Tail':[790,565,1110,920]}}
for direction in ['Up','Down']:
 src=HERE/'generation'/direction/'raw.png'
 out=src.parent/'local_revision_01';assert not out.exists();out.mkdir()
 raw=Image.open(src).convert('RGBA');a=np.array(raw);fg=a[:,:,3]>=128
 a[~fg]=[255,0,255,255];a[fg,3]=255
 operations=[]
 if direction=='Up':
  # The rear head in cell one is valid. pack_character explicitly reuses it for all Up expressions.
  # Erase only the interior toe strokes, retaining the complete connected opaque heel silhouette.
  inside=np.asarray(Image.fromarray(fg.astype('uint8')*255).filter(ImageFilter.MinFilter(13)))>0
  for box in [(108,823,267,885),(474,821,665,888)]:
   x0,y0,x1,y1=box
   region=np.zeros(fg.shape,dtype=bool);region[y0:y1,x0:x1]=True
   m=inside&region
   # Full lower heel interior, not a rectangular pasted patch; every boundary follows the silhouette.
   a[m,:3]=[114,95,61]
   operations.append({'region':box,'method':'Fill eroded connected lower paw interior in original khaki fur; retain outer dark rounded heel outline. Remove front toe divisions for back-facing feet.','pixels':int(m.sum())})
 # All pixels outside actual alpha are replaced by exact magenta; the raw returned alpha remains in parent.
 Image.fromarray(a,'RGBA').convert('RGB').save(out/'raw.png')
 save(out/'processing.json',{'observed_at':now(),'parent':src.relative_to(HERE).as_posix(),'parent_sha256':sha(src),'output_sha256':sha(out/'raw.png'),
   'method':'Local raster derivation, not a new AI return. Threshold returned alpha at128 and replace exterior only with flat magenta. Own alpha edges determine silhouette; measured boxes contain complete parts.',
   'operations':operations,'new_AI_return':False})
save(HERE/'art_selection.json',{'Up':'generation/Up/local_revision_01/raw.png','Down':'generation/Down/local_revision_01/raw.png',
 'rectangles':{v+'_'+p:rect for v,parts in rects.items() for p,rect in parts.items()},
 'source_sha256':{v:sha(HERE/'generation'/v/'local_revision_01/raw.png') for v in ['Up','Down']},
 'note':'Full raw returns viewed. Reuse the first faceless rear head in all Up expressions; reject erroneous front faces in raw Up cells2/3. Rear feet locally remove front toe strokes. Explicit measured rectangles, preserved originals.'})
parts={'Up/Body':dict(y=.55,width=.66,height=.76),'Up/Head':dict(y=.89,width=.58,height=.54,order=30),
 'Up/Tail':dict(x=-.01,y=.34,width=.30,height=.36,order=31,angle=-8),
 'Down/Body':dict(y=.63,width=.67,height=.74),'Down/Head':dict(y=.53,width=.67,height=.62,order=35),
 'Down/Tail':dict(x=.16,y=.85,width=.28,height=.35,order=5,angle=-14)}
for direction in ['Up','Down']:
 for side,sign in [('L',-1),('R',1)]:
  parts[f'{direction}/Fore{side}']=dict(x=sign*(.19 if direction=='Up' else .16),y=.64 if direction=='Up' else .33,width=.18,height=.28,angle=sign*(20 if direction=='Up' else 3))
  parts[f'{direction}/Hind{side}']=dict(x=sign*.19,y=.34 if direction=='Up' else .72,width=.19,height=.29,angle=sign*(3 if direction=='Up' else 20))
changes={'reason':'Own WolfHound source and measured returned shapes: short stocky four-legged dog, one collar entirely on head, upswept tail rooted at lower-left of its actual slice; short diagonal-phase gait with buried roots.',
 'layout':{'motion':{'legAngle':6.5,'legLift':.025,'bodyBob':.0045,'bodyRoll':.6,'tailSwing':4}},'parts':parts,
 'sprites':{f'{v}_{role}':{'pivotX':.5,'pivotY':.94} for v in ['Up','Down'] for role in ['LegFront','LegBack']}}
changes['sprites'].update({'Up_Tail':{'pivotX':.12,'pivotY':.12},'Down_Tail':{'pivotX':.12,'pivotY':.12}})
save(HERE/'layout_adjustments.json',changes)
save(HERE/'raw_visual_review_20261029.json',{'observed_at':now(),'reviewed':[{'path':f'generation/{v}/raw.png','sha256':sha(HERE/'generation'/v/'raw.png'),'actual_format':'PNG RGBA','actual_size':[1536,1024]} for v in ['Up','Down']],
 'findings':'Own khaki/olive-brown coat, ochre spots, sole gold/ivory-spiked collar and short upswept shaggy tail retained. Up cell1 faceless rear head usable, cells2/3 wrongly frontal and rejected in favor of cell1; rear paw toe strokes need local removal. Down is frontal with small pupils, fangs, angry jaw and pale dead eyes/tongue. Low-alpha exterior glows are removed from actual alpha. No floor/ground shadow. Stage remains to be checked.',
 'requests':2,'http200':2,'unknown':0,'paid_art_revisions':0,'stage_pending':True})
print('WolfHound measured selection and local raster01 prepared')
