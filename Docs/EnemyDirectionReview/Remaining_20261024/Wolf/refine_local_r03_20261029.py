from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,sys,json,shutil
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from session_current import *
owner()
backup=HERE/'staged_art_before_local_r03';assert not backup.exists();shutil.copytree(HERE/'staged_art',backup)
for n in ['offline_Up.png','offline_Down.png','offline_rig_proof.png','parts_clean.png','art_selection.json','layout_adjustments.json']:
    shutil.copy2(HERE/n,HERE/(Path(n).stem+'_before_local_r03'+Path(n).suffix))
base=(106,88,57);gray=(115,106,90);spot=(143,100,20);outline=(46,38,24)
for direction in ['Up','Down']:
    parent=HERE/'generation'/direction/'local_revision_02/raw.png';original=HERE/'generation'/direction/'local_revision_01/raw.png'
    out=parent.parent.parent/'local_revision_03';assert not out.exists();out.mkdir()
    a=np.array(Image.open(parent).convert('RGB'));before=a.copy();raw=np.array(Image.open(original).convert('RGB'))
    fg=(raw[:,:,0]!=255)|(raw[:,:,1]!=0)|(raw[:,:,2]!=255)
    interior=np.asarray(Image.fromarray(fg.astype('uint8')*255).filter(ImageFilter.MinFilter(9)))>0
    rect=[1184,63,1502,479] if direction=='Up' else [1181,91,1497,502]
    region=np.zeros(fg.shape,dtype=bool);x0,y0,x1,y1=rect;region[y0:y1,x0:x1]=True;m=region&interior
    paint=Image.new('RGB',(1536,1024),base);d=ImageDraw.Draw(paint)
    if direction=='Up':
        poly=[(1322,64),(1370,64),(1429,177),(1406,175),(1434,225),(1398,211),(1417,267),(1383,248),(1383,292),(1356,271),(1341,314),(1323,279),(1295,293),(1301,254),(1268,270),(1286,226),(1259,241),(1288,183),(1268,181)]
        dots=[(1250,350,22),(1432,343,22),(1290,189,14),(1400,175,11)]
    else:
        poly=[(1267,99),(1314,115),(1340,100),(1370,115),(1414,99),(1447,183),(1425,175),(1441,230),(1418,214),(1426,274),(1400,254),(1410,317),(1384,294),(1372,344),(1352,319),(1322,345),(1315,310),(1287,322),(1294,283),(1267,293),(1280,248),(1257,263),(1274,217),(1246,232),(1269,180)]
        dots=[(1279,199,20),(1394,185,17),(1259,323,19),(1420,324,19)]
    d.polygon(poly,fill=gray)
    for x,y,r in dots:d.ellipse((x-r,y-r,x+r,y+r),fill=spot)
    if direction=='Down':
        chest=[(1340,367),(1354,394),(1365,385),(1373,410),(1383,403),(1394,434),(1383,456),(1366,476),(1340,489),(1317,477),(1300,457),(1290,433),(1301,405),(1315,415),(1324,391),(1334,405)]
        d.polygon(chest,fill=(145,135,116),outline=outline,width=6)
        d.polygon([(1341,389),(1349,419),(1361,409),(1366,438),(1378,430),(1374,454),(1340,475),(1310,445),(1319,432),(1331,443)],fill=(179,169,147))
    a[m]=np.array(paint)[m]
    operations=[{'region':rect,'method':'Whole connected torso interior, exact Wolf source swatches; replaces rectangular-mask seams from local02. Original silhouette and border retained. Existing jagged coat, spots and Down chest tuft rasterized without fragmented marks.','fur_polygon':poly,'spot_centers':dots}]
    if direction=='Up':
        defs=[([117,600,287,850],[(159,685),(180,695),(187,680),(208,697),(228,689),(226,732),(221,779),(219,840),(143,840),(141,803),(171,787),(176,743)],None),
              ([477,598,698,897],[(548,631),(578,628),(605,636),(634,660),(647,720),(644,778),(655,837),(680,870),(678,890),(574,888),(555,851),(552,822),(561,789),(551,750),(537,709),(532,682)],(550,766,18))]
        for box,poly,dot in defs:
            x0,y0,x1,y1=box;region=np.zeros(fg.shape,dtype=bool);region[y0:y1,x0:x1]=True;m=region&interior
            paint=Image.new('RGB',(1536,1024),base);d=ImageDraw.Draw(paint);d.polygon(poly,fill=gray)
            if dot:
                x,y,r=dot;d.ellipse((x-r,y-r,x+r,y+r),fill=spot)
            a[m]=np.array(paint)[m]
            operations.append({'region':box,'method':'Whole connected rear-leg interior retains contour and brown shoulder/hip, one jagged gray fur field and existing hindleg patch; smooth heel has no front toe strokes or rectangular fill seam','fur_polygon':poly})
    Image.fromarray(a).save(out/'raw.png')
    save(out/'processing.json',{'observed_at':now(),'parent':parent.relative_to(HERE).as_posix(),'parent_sha256':sha(parent),'silhouette_parent':original.relative_to(HERE).as_posix(),'silhouette_parent_sha256':sha(original),
        'output_sha256':sha(out/'raw.png'),'new_AI_return':False,'operations':operations,'changed_pixels':int(np.any(a!=before,axis=2).sum()),'reason':'Offline local02 rejected for rectangular heel and torso interior seams; full connected local fills remove those boundaries.'})
selection=read(HERE/'art_selection.json')
for v in ['Up','Down']:selection[v]=f'generation/{v}/local_revision_03/raw.png';selection['source_sha256'][v]=sha(HERE/selection[v])
selection['note']+=' Local03 supersedes rectangular local02 fills with connected whole-interior source-colored regions; no additional AI call.'
(HERE/'art_selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Connected local03 raster prepared; all prior stages retained')
