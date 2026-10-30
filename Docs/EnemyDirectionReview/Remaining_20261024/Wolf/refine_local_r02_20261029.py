from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,sys,json,shutil
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from session_current import *
owner()
backup=HERE/'staged_art_before_local_r02'
if not backup.exists():
    shutil.copytree(HERE/'staged_art',backup)
    for n in ['offline_Up.png','offline_Down.png','offline_rig_proof.png','parts_clean.png','art_selection.json','layout_adjustments.json']:
        shutil.copy2(HERE/n,HERE/(Path(n).stem+'_before_local_r02'+Path(n).suffix))
else:
    assert '--resume-after-dtype-error' in sys.argv
    assert read(HERE/'art_selection.json')==read(HERE/'art_selection_before_local_r02.json')
    assert not (HERE/'generation/Up/local_revision_02/raw.png').exists()
base=[106,88,57];gray=[115,106,90];spot=[143,100,20]
for direction in ['Up','Down']:
    parent=HERE/'generation'/direction/'local_revision_01/raw.png';out=parent.parent.parent/'local_revision_02'
    if out.exists():assert not any(out.iterdir()) and '--resume-after-dtype-error' in sys.argv
    else:out.mkdir()
    a=np.array(Image.open(parent).convert('RGB'));before=a.copy()
    fg=(a[:,:,0]!=255)|(a[:,:,1]!=0)|(a[:,:,2]!=255)
    interior=np.asarray(Image.fromarray(fg.astype('uint8')*255).filter(ImageFilter.MinFilter(11)))>0
    # Flatten the existing torso's interior into source coat swatches. Keep its full outline and the original Down chest tuft.
    torso=np.zeros(fg.shape,dtype=bool);torso[110:443 if direction=='Up' else 365,1201:1486]=True
    m=torso & interior
    a[m]=base
    paint=Image.new('RGB',(1536,1024),tuple(base));draw=ImageDraw.Draw(paint)
    if direction=='Up':
        poly=[(1322,106),(1370,106),(1429,177),(1406,175),(1434,225),(1398,211),(1417,267),(1383,248),(1383,292),(1356,271),(1341,314),(1323,279),(1295,293),(1301,254),(1268,270),(1286,226),(1259,241),(1288,183),(1268,181)]
        dots=[(1250,350,22),(1432,349,22),(1292,197,15),(1400,197,15)]
    else:
        poly=[(1267,127),(1314,133),(1340,122),(1370,134),(1414,128),(1447,183),(1425,175),(1441,230),(1418,214),(1426,274),(1400,254),(1410,317),(1384,294),(1372,344),(1352,319),(1322,345),(1315,310),(1287,322),(1294,283),(1267,293),(1280,248),(1257,263),(1274,217),(1246,232),(1269,180)]
        dots=[(1279,199,20),(1394,200,20),(1259,323,19),(1420,324,19)]
    draw.polygon(poly,fill=tuple(gray))
    for x,y,r in dots:draw.ellipse((x-r,y-r,x+r,y+r),fill=tuple(spot))
    painted=np.array(paint);a[m]=painted[m]
    operations=[{'region':'original torso interior, original outline retained; Down chest below365 retained','method':'Local flat-color derivation using actual Wolf swatches base106/88/57, gray115/106/90, ochre143/100/20; existing jagged coat and round spot locations simplified, no added anatomy','fur_polygon':poly,'existing_spots':dots,'pixels':int(m.sum())}]
    if direction=='Up':
        # Replace the rejected soft heel fill with column colors sampled immediately above the old toe strokes.
        raw=np.array(Image.open(HERE/'generation/Up/raw.png').convert('RGB'))
        for box,sample_y in [((137,779,224,833),774),((548,820,668,882),814)]:
            x0,y0,x1,y1=box
            for x in range(x0,x1):
                color=np.median(raw[sample_y-2:sample_y+3,x],axis=0)
                if color.max()<85:color=gray
                valid=interior[y0:y1,x]
                a[y0:y1,x][valid]=np.asarray(color,dtype='uint8')
            operations.append({'region':box,'method':'Flat column continuation from above toe stroke; solid smooth heel and original exterior preserved','sample_y':sample_y})
    Image.fromarray(a).save(out/'raw.png')
    save(out/'processing.json',{'observed_at':now(),'parent':parent.relative_to(HERE).as_posix(),'parent_sha256':sha(parent),'output_sha256':sha(out/'raw.png'),
        'new_AI_return':False,'operations':operations,'changed_pixels':int(np.any(a!=before,axis=2).sum()),'reason':'Prior offline version rejected for blurred rear heels and fragmented torso markings; local source-colored cleanup.'})
selection=read(HERE/'art_selection.json')
for v in ['Up','Down']:selection[v]=f'generation/{v}/local_revision_02/raw.png';selection['source_sha256'][v]=sha(HERE/selection[v])
selection['note']+=' Local02 simplifies torso interior into original flat coat swatches, keeps contour/Down chest; rear heel blur removed. All previous stages and raw parents preserved.'
(HERE/'art_selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
changes=read(HERE/'layout_adjustments.json')
for side,sign in [('L',-1),('R',1)]:
    changes['parts']['Up/Fore'+side].update(x=sign*.13,y=.64,angle=sign*15)
    changes['parts']['Down/Fore'+side].update(y=.41)
(HERE/'layout_adjustments.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Local02 and root layout prepared; stage may now be rebuilt from retained parents')
