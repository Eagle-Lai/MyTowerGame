from pathlib import Path
from PIL import Image,ImageFilter
import numpy as np,shutil,sys,json
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from session_current import *
owner();backup=HERE/'staged_art_rejected_local_r02';assert not backup.exists();shutil.copytree(HERE/'staged_art',backup)
for n in ['offline_rig_proof.png','offline_Up.png','offline_Down.png','parts_clean.png','processing.json','art_selection.json','layout_adjustments.json']:
    shutil.copy2(HERE/n,HERE/(Path(n).stem+'_before_local_r03'+Path(n).suffix))
for direction in ['Up','Down']:
    src=HERE/f'generation/{direction}/local_revision_02/raw.png';a=np.array(Image.open(src).convert('RGB'));old=a.copy();w=a.astype('int16')
    fg=(w[:,:,2]<=w[:,:,1]+8)&(w[:,:,2]<=w[:,:,0]+12)&((w[:,:,0]-w[:,:,1])<=(w[:,:,1]-w[:,:,2])+26)
    inner=np.asarray(Image.fromarray(fg.astype('uint8')*255).filter(ImageFilter.MinFilter(15)))>0
    yy,xx=np.mgrid[:a.shape[0],:a.shape[1]]
    if direction=='Up':
        blend=np.zeros(fg.shape,float)
        for x0,x1,y0,y1 in [(125,249,822,881),(503,609,839,886)]:
            region=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1)&inner
            blend[region]=np.minimum(1,(yy[region]-y0)/18)
        a=np.rint(a*(1-blend[:,:,None])+np.array([231,226,215])*blend[:,:,None]).astype('uint8')
        method='Smooth only lower rear heel interiors using source ivory with a vertical feathered boundary; retain full exterior outline and remove remaining toe-shaped shade. No new AI request.'
    else:
        # Only tiny remnants of the two removed motifs near the upper-center root remain.
        region=(xx>=1245)&(xx<=1457)&(yy>=130)&(yy<=184)&inner
        dark=(w[:,:,0]<120)&(w[:,:,1]<115)&(w[:,:,2]<105)
        mask=np.asarray(Image.fromarray((region&dark).astype('uint8')*255).filter(ImageFilter.MaxFilter(7)))>0
        mask &= region;a[mask]=[232,228,218]
        method='Erase only isolated internal dark leftovers of removed ear-like motifs; preserve original ochre circles and torso contour. No new AI request.'
    out=HERE/f'generation/{direction}/local_revision_03';assert not out.exists();out.mkdir();Image.fromarray(a).save(out/'raw.png')
    save(out/'processing.json',{'parent':src.relative_to(HERE).as_posix(),'parent_sha256':sha(src),'output_sha256':sha(out/'raw.png'),'method':method,'changed_pixels':int(np.any(a!=old,axis=2).sum()),'new_AI_return':False})
selection=read(HERE/'art_selection.json')
for v in ['Up','Down']:selection[v]=f'generation/{v}/local_revision_03/raw.png';selection['source_sha256'][v]=sha(HERE/selection[v])
(HERE/'art_selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
layout=read(HERE/'layout_adjustments.json');layout['parts']['Down/Body'].update(y=.60,height=.63,width=.64)
layout['parts']['Down/Head'].update(y=.48,height=.66,width=.65)
for side,sign in [('L',-1),('R',1)]:
    layout['parts']['Up/Fore'+side].update(x=sign*.105,y=.59,width=.16,height=.25,angle=sign*18)
    layout['parts']['Up/Hind'+side].update(x=sign*.145,y=.34,width=.175,height=.28)
    layout['parts']['Down/Fore'+side].update(y=.33,width=.175,height=.28)
    layout['parts']['Down/Hind'+side].update(x=sign*.14,y=.67,width=.16,height=.25,angle=sign*21)
layout['parts']['Down/Tail'].update(y=.83)
(HERE/'layout_adjustments.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
print('Local r03 prepared; r02 retained.')
