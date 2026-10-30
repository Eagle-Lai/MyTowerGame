from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from session_current import *
owner()
assert not (HERE/'staged_art').exists() and not (HERE/'art_selection.json').exists()
for direction in ['Up','Down']:
    src=HERE/'generation'/direction/'raw.png'
    out=src.parent/'local_revision_01';assert not out.exists();out.mkdir()
    raw=np.array(Image.open(src).convert('RGBA'));a=raw[:,:,:3].copy();original=a.copy()
    fg=raw[:,:,3]>=128
    inside=np.asarray(Image.fromarray(fg.astype('uint8')*255).filter(ImageFilter.MinFilter(13)))>0
    operations=[]
    if direction=='Up':
        for box in [(137,785,220,831),(548,828,665,880)]:
            x0,y0,x1,y1=box
            region=np.zeros(fg.shape,dtype=bool);region[y0:y1,x0:x1]=True
            dark=np.max(a,axis=2)<96
            m=np.asarray(Image.fromarray((region&dark).astype('uint8')*255).filter(ImageFilter.MaxFilter(7)))>0
            m &= region & inside
            ys,xs=np.where(m)
            if len(xs):
                # Source-colored harmonic fill removes only internal toe strokes, preserving outer heel and gray/brown color boundary.
                crop=a[y0:y1,x0:x1].astype(float);mm=m[y0:y1,x0:x1]
                for k in range(500):
                    pad=np.pad(crop,((1,1),(1,1),(0,0)),mode='edge')
                    avg=(pad[:-2,1:-1]+pad[2:,1:-1]+pad[1:-1,:-2]+pad[1:-1,2:])/4
                    crop[mm]=avg[mm]
                a[y0:y1,x0:x1][mm]=np.rint(crop[mm]).astype('uint8')
            operations.append({'region':box,'method':'Local harmonic fill of internal dark front-toe strokes, original exterior contour retained','masked_pixels':int(m.sum())})
    a[~fg]=[255,0,255]
    Image.fromarray(a).save(out/'raw.png')
    save(out/'processing.json',{'observed_at':now(),'parent':src.relative_to(HERE).as_posix(),'parent_sha256':sha(src),'output_sha256':sha(out/'raw.png'),
        'method':'Locally derived raster, not an AI return. Returned RGBA threshold at128 to solid foreground and flat magenta exterior, preserving raw file. Exact measured rectangles exclude generated grid. Up paw-only corrections detailed below.',
        'operations':operations,'changed_foreground_pixels':int((np.any(a!=original,axis=2)&fg).sum()),'new_AI_return':False})
up={'HeadNormal':[26,90,353,427],'HeadAngry':[410,90,738,427],'HeadDead':[794,90,1122,427],
    'Body':[1184,63,1502,479],'LegFront':[117,600,287,850],'LegBack':[477,598,698,897],'Tail':[797,575,1111,915]}
down={'HeadNormal':[25,87,353,462],'HeadAngry':[408,87,737,483],'HeadDead':[792,87,1120,478],
    'Body':[1181,91,1497,502],'LegFront':[97,609,288,895],'LegBack':[477,589,685,901],'Tail':[798,563,1100,913]}
save(HERE/'art_selection.json',{'Up':'generation/Up/local_revision_01/raw.png','Down':'generation/Down/local_revision_01/raw.png',
    'rectangles':{**{'Up_'+k:v for k,v in up.items()},**{'Down_'+k:v for k,v in down.items()}},
    'source_sha256':{v:sha(HERE/'generation'/v/'local_revision_01/raw.png') for v in ['Up','Down']},
    'note':'Both complete actual raw returns reviewed. True rear head selected and reused for all three Up states; rear toe strokes locally removed. Exact rectangles, no grid assumptions; original raw/result/request retained.'})
parts={'Up/Body':dict(y=.56,width=.65,height=.73),'Up/Head':dict(y=.88,width=.53,height=.50,order=30),
       'Up/Tail':dict(x=-.015,y=.39,width=.29,height=.39,order=31,angle=0),
       'Down/Body':dict(y=.63,width=.66,height=.76),'Down/Head':dict(y=.55,width=.65,height=.61,order=35),
       'Down/Tail':dict(x=.19,y=.91,width=.27,height=.38,order=5,angle=-14)}
for direction in ['Up','Down']:
    for side,sign in [('L',-1),('R',1)]:
        parts[f'{direction}/Fore{side}']=dict(x=sign*(.18 if direction=='Up' else .15),y=.65 if direction=='Up' else .35,width=.18,height=.29,angle=sign*(23 if direction=='Up' else 5))
        parts[f'{direction}/Hind{side}']=dict(x=sign*.18,y=.35 if direction=='Up' else .73,width=.19,height=.30,angle=sign*(5 if direction=='Up' else 23))
changes={'reason':'Own gray/brown Wolf source, actual returned anatomy and measured upper-left tail roots. Four diagonal-phase short legs; one rear head and one front head; compact low wolf with root overlap.',
    'layout':{'motion':{'legAngle':7,'legLift':.025,'bodyBob':.005,'bodyRoll':.6,'tailSwing':4.5}},'parts':parts,
    'sprites':{f'{v}_{role}':{'pivotX':.5,'pivotY':.94} for v in ['Up','Down'] for role in ['LegFront','LegBack']}}
changes['sprites'].update({'Up_Tail':{'pivotX':.075,'pivotY':.90},'Down_Tail':{'pivotX':.04,'pivotY':.90}})
save(HERE/'layout_adjustments.json',changes)
save(HERE/'raw_visual_review_20261029.json',{'observed_at':now(),'reviewed':[{'path':f'generation/{v}/raw.png','sha256':sha(HERE/'generation'/v/'raw.png'),'actual_format':'PNG RGBA','actual_size':[1536,1024]} for v in ['Up','Down']],
    'findings':'Up has plain rear head with outer ear backs, no face; front toe strokes require the documented local correction. Down has centered front head with ivory eyes, dark nose, fangs, angry jaw and dead tongue; four canine limbs through mirroring. Gray/olive brown coat and ochre marks, no equipment or ground shadow. Actual alpha return with low-alpha exterior and generated cell lines excluded by explicit crop.',
    'requests':2,'http200':2,'unknown':0,'paid_art_revisions':0,'stage_pending':True})
print('Wolf measured selection and local raster01 prepared')
