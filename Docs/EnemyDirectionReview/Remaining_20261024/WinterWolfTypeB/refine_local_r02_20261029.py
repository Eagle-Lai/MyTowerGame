from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,shutil,sys,json
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from session_current import *
owner();backup=HERE/'staged_art_rejected_local_r01'
if not backup.exists():
    shutil.copytree(HERE/'staged_art',backup)
    for n in ['offline_rig_proof.png','offline_Up.png','offline_Down.png','parts_clean.png','processing.json','art_selection.json','layout_adjustments.json']:
        shutil.copy2(HERE/n,HERE/(Path(n).stem+'_before_local_r02'+Path(n).suffix))
else:
    assert not (HERE/'generation/Up/local_revision_02').exists()
    assert all(sha(p)==sha(HERE/'staged_art'/p.name) for p in backup.iterdir() if p.is_file())
for direction,source in [('Up','generation/Up/revision_01/raw.png'),('Down','generation/Down/raw.png')]:
    src=HERE/source;im=Image.open(src).convert('RGB');a=np.array(im);old=a.copy();wide=a.astype(np.int16)
    fg=(wide[:,:,2]<=wide[:,:,1]+8)&(wide[:,:,2]<=wide[:,:,0]+12)&((wide[:,:,0]-wide[:,:,1])<=(wide[:,:,1]-wide[:,:,2])+26)
    inside=np.asarray(Image.fromarray(fg.astype('uint8')*255).filter(ImageFilter.MinFilter(9)))>0
    if direction=='Up':
        lower=np.zeros(fg.shape,dtype=bool);lower[837:875,152:225]=True;lower[848:879,522:555]=True
        dark=(wide[:,:,0]<145)&(wide[:,:,1]<135)&(wide[:,:,2]<125)
        mask=np.asarray(Image.fromarray((dark&lower).astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
        mask &= inside&lower
        for y,x in zip(*np.where(mask)):
            y0,y1=max(0,y-30),min(a.shape[0],y+31);x0,x1=max(0,x-30),min(a.shape[1],x+31)
            area=old[y0:y1,x0:x1];valid=fg[y0:y1,x0:x1]&~mask[y0:y1,x0:x1]&(area[:,:,0]>175)&(area[:,:,1]>170)
            assert valid.any();a[y,x]=np.median(area[valid],axis=0).astype('uint8')
        method='Replace only actual internal dark toe strokes and their one-pixel antialias fringe with nearby original pale paw pixels; retain existing shading, smooth exterior heel outline and four-pixel contour. Replaces rejected broad flat fill.'
    else:
        region=np.zeros(fg.shape,dtype='uint8');region[50:190,1190:1500]=255
        mask_im=Image.fromarray(region).filter(ImageFilter.GaussianBlur(7))
        blend=np.asarray(mask_im).astype(float)/255;blend*=inside
        yy,xx=np.mgrid[:a.shape[0],:a.shape[1]]
        # Preserve the actual central taupe dorsal region and the two original ochre spots.
        central=((xx>=1293)&(xx<=1398)&(yy>=135))
        for cx,cy,rx,ry in [(1263,179,19,15),(1447,179,18,15)]:
            central|=((xx-cx)/rx)**2+((yy-cy)/ry)**2<=1
        blend[central]=0
        a=np.rint(a*(1-blend[:,:,None])+np.array([232,228,218])*blend[:,:,None]).astype('uint8')
        mask=np.any(a!=old,axis=2)
        method='Remove only upper rump ear-like motifs, use original-style pale torso fill feathered at local borders, preserve the actual central taupe dorsal region and both original ochre spots plus the exterior outline. Replaces rejected hard patch seams.'
    out=HERE/'generation'/direction/'local_revision_02';assert not out.exists();out.mkdir();Image.fromarray(a).save(out/'raw.png')
    save(out/'processing.json',{'observed_at':now(),'parent':source,'parent_sha256':sha(src),'replaces_rejected_local':'local_revision_01','output_sha256':sha(out/'raw.png'),'method':method,'changed_pixels':int(np.any(a!=old,axis=2).sum()),'new_AI_return':False,'requires_visual_review':True})
selection=read(HERE/'art_selection.json')
for v in ['Up','Down']:selection[v]=f'generation/{v}/local_revision_02/raw.png';selection['source_sha256'][v]=sha(HERE/selection[v])
(HERE/'art_selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
layout=read(HERE/'layout_adjustments.json')
for side,sign in [('L',-1),('R',1)]:
    layout['parts']['Up/Fore'+side].update(x=sign*.13,y=.59,angle=sign*20)
    layout['parts']['Down/Fore'+side].update(y=.36)
    layout['parts']['Down/Hind'+side].update(x=sign*.16,angle=sign*22)
(HERE/'layout_adjustments.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
save(HERE/'offline_rejected_local_r01_review_20261029.json',{'observed_at':now(),'rejected':'staged_art_rejected_local_r01','findings':'Flat paw recolor produced a hard rectangle seam; broad torso motif recolor created pale polygon boundaries and clipped ochre spots. Preserve and replace before install. Far forelegs also appeared too much like side arms; roots moved lower/inward behind torso.','production_changed':False})
print('Local r02 ready; r01 rejected evidence preserved.')
