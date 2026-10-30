from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from session_current import *
owner()
assert not (HERE/'staged_art').exists() and not (HERE/'art_selection.json').exists()
for direction,source in [('Up','generation/Up/revision_01/raw.png'),('Down','generation/Down/raw.png')]:
    src=HERE/source;out=HERE/'generation'/direction/'local_revision_01';assert not out.exists();out.mkdir()
    a=np.array(Image.open(src).convert('RGB'));original=a.copy();wide=a.astype(np.int16)
    fg=(wide[:,:,2]<=wide[:,:,1]+8)&(wide[:,:,2]<=wide[:,:,0]+12)&((wide[:,:,0]-wide[:,:,1])<=(wide[:,:,1]-wide[:,:,2])+26)
    inside=np.asarray(Image.fromarray(fg.astype('uint8')*255).filter(ImageFilter.MinFilter(9)))>0
    if direction=='Up':
        regions=[[(129,831),(246,831),(246,879),(129,879)],[(508,845),(602,845),(602,883),(508,883)]]
        color=[230,225,215]
        method='Fill only lower paw interiors in same pale ivory cel tone to remove incorrect front toe lines from rear heels; exterior four-pixel contour preserved.'
    else:
        regions=[[(1204,91),(1259,62),(1304,82),(1317,132),(1313,174),(1252,181),(1220,157)],[(1374,82),(1430,62),(1485,98),(1490,160),(1423,181),(1373,155)]]
        color=[231,227,216]
        method='Remove two internal tan ear-shaped shoulder motifs from far rump; preserve torso outline and original lower brown ventral bib, ochre spots and central taupe area.'
    masks=[]
    for points in regions:
        mask=Image.new('L',(a.shape[1],a.shape[0]));ImageDraw.Draw(mask).polygon(points,fill=255)
        m=(np.asarray(mask)>0)&inside;a[m]=color;masks.append(points)
    Image.fromarray(a).save(out/'raw.png')
    save(out/'processing.json',{'observed_at':now(),'parent':source,'parent_sha256':sha(src),'output_sha256':sha(out/'raw.png'),'method':method,
        'regions':masks,'changed_pixels':int(np.any(a!=original,axis=2).sum()),'new_AI_return':False,'requires_visual_review':True})
up={'HeadNormal':[576,178,742,400],'HeadAngry':[576,178,742,400],'HeadDead':[576,178,742,400],
    'Body':[1205,35,1485,515],'LegFront':[105,635,270,900],'LegBack':[470,635,655,900],'Tail':[795,605,1052,910]}
down={'HeadNormal':[20,58,363,485],'HeadAngry':[402,58,747,485],'HeadDead':[787,58,1134,485],
    'Body':[1178,35,1508,505],'LegFront':[100,580,283,930],'LegBack':[475,580,680,930],'Tail':[813,555,1075,953]}
selection={'Up':'generation/Up/local_revision_01/raw.png','Down':'generation/Down/local_revision_01/raw.png',
    'rectangles':{**{'Up_'+k:v for k,v in up.items()},**{'Down_'+k:v for k,v in down.items()}},
    'source_sha256':{v:sha(HERE/'generation'/v/'local_revision_01/raw.png') for v in ['Up','Down']},
    'note':'Full actual raw images reviewed. Up selects only real plain rear head, excludes all front heads, and reuses same rear silhouette for three expressions. Local edits have preserved parent raw and processing SHA. No paid art revisions.'}
save(HERE/'art_selection.json',selection)
parts={'Up/Body':dict(y=.56,width=.65,height=.70),'Up/Head':dict(y=.86,width=.43,height=.50,order=30),
       'Up/Tail':dict(x=-.01,y=.43,width=.28,height=.38,order=31,angle=0),
       'Down/Body':dict(y=.61,width=.67,height=.78),'Down/Head':dict(y=.54,width=.66,height=.62,order=35),
       'Down/Tail':dict(x=.18,y=.89,width=.25,height=.37,order=5,angle=-18)}
for direction in ['Up','Down']:
    for side,sign in [('L',-1),('R',1)]:
        parts[f'{direction}/Fore{side}']=dict(x=sign*(.16 if direction=='Up' else .15),y=.65 if direction=='Up' else .31,width=.18,height=.29,angle=sign*(23 if direction=='Up' else 5))
        parts[f'{direction}/Hind{side}']=dict(x=sign*(.16 if direction=='Up' else .19),y=.35 if direction=='Up' else .72,width=.18,height=.30,angle=sign*(5 if direction=='Up' else 25))
layout={'reason':'Own white/taupe/ochre wolf reference and actual parts measured. Long axial torso, one rear head, four short canine legs, downward full tail. The tail pivot uses the actual upper-left attachment. Far roots remain buried; diagonal limb phases and small body/head/tail offsets.',
    'layout':{'motion':{'legAngle':7,'legLift':.025,'bodyBob':.005,'bodyRoll':.6,'tailSwing':4.5}},'parts':parts,
    'sprites':{f'{v}_{role}':{'pivotX':.5,'pivotY':.94} for v in ['Up','Down'] for role in ['LegFront','LegBack']}}
layout['sprites'].update({'Up_Tail':{'pivotX':.07,'pivotY':.85},'Down_Tail':{'pivotX':.07,'pivotY':.90}})
save(HERE/'layout_adjustments.json',layout)
save(HERE/'down_raw_review_20261029.json',{'observed_at':now(),'source':'generation/Down/raw.png','sha256':sha(HERE/'generation/Down/raw.png'),'full_raw_reviewed':True,
    'actual_format':'PNG RGB','actual_size':[1536,1024],'findings':'True front expressions, front toe paws, white/taupe/ochre coat and brown chest. Two internal ear-like rump shapes locally removed; grid lines excluded by actual rectangles and transparency.','stage_pending':True})
print('Documented local raster revisions and own measured layout prepared.')
