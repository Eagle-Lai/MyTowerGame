from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
here=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
ops=[]
for direction in ['Up','Down']:
 source=here/'generation'/direction/'revision_03/raw.png'
 dest=source.parent.parent/'revision_04';dest.mkdir(exist_ok=True)
 assert not (dest/'raw.png').exists()
 im=Image.open(source).convert('RGB');a=np.array(im)
 if direction=='Up':
  # Remove only the disconnected extra ring under the bare right ear.
  # Keep the first complete dark outer contour of each rear head.
  for column in range(3):
   offset=column*384
   for y in range(277,365):
    line=a[y,offset+296:offset+366];dark=(line<130).all(axis=1)
    indices=np.where(dark)[0]
    if not len(indices):continue
    end=int(indices[0])
    while end+1<len(dark) and dark[end+1]:end+=1
    a[y,offset+296+end+1:offset+366]=[255,0,255]
  operation={'type':'erase extra ring outside existing rear cranium contour','cells':[1,2,3],'local_roi':[296,277,366,365],'preserved':'one original image-left earring, head/hat contour, all other parts'}
 else:
  # Copy adjacent unadorned torso paint onto the spurious gold ring only.
  # The chain and cannon carriage remain outside this bounded ellipse.
  patch=im.crop((1310,280,1360,340));mask=Image.new('L',(50,60),0)
  ImageDraw.Draw(mask).ellipse((2,1,47,57),fill=255);mask=mask.filter(ImageFilter.GaussianBlur(1.5))
  im.paste(patch,(1380,278),mask);a=np.array(im)
  operation={'type':'clone adjacent plain torso skin over extra ring','source_rect':[1310,280,1360,340],'target_rect':[1380,278,1430,338],'mask':'bounded feathered ellipse; excludes chain and carriage'}
 Image.fromarray(a).save(dest/'raw.png')
 meta={'revision':'revision_04','method':'deterministic bounded pixel retouch, no paid request','parent':'revision_03/raw.png','parent_sha256':sha(source),'sha256':sha(dest/'raw.png'),'operation':operation,'pending_visual_check':True}
 (dest/'patch.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8');ops.append(meta)
backup=here/'generation'/'selection_before_revision_04';backup.mkdir(exist_ok=True)
for filename in ['art_selection.json','layout_adjustments.json','anatomy_plan.json']:
 p=here/filename;shutil.copy2(p,backup/filename)
 d=json.loads(p.read_text(encoding='utf-8-sig'))
 if filename=='art_selection.json':
  d.update(Up='generation/Up/revision_04/raw.png',Down='generation/Down/revision_04/raw.png',revision='revision_04',review_basis='revision_03 viewed; bounded ear-ring retouch awaiting staged visual check')
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(here/'revision_04_processing.json').write_text(json.dumps(ops,indent=2)+'\n',encoding='utf-8')
print('Revision 04 pixel corrections preserved as new sources; selection updated')
