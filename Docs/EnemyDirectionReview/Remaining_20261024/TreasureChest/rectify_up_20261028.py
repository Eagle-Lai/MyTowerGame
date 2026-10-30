from session_treasurechest import *
from PIL import Image,ImageOps
owner();out=D/'local_raster_revision_01';assert not out.exists();out.mkdir()
raw=D/'generation/Up/revision_02/raw.png';im=Image.open(raw).convert('RGB');sheet=Image.new('RGB',im.size,(255,0,255))
rects={'closed':[40,147,175,455],'open':[809,53,954,455]}
operations=[]
for cell,state in [(0,'closed'),(1,'closed'),(2,'open')]:
    box=rects[state];half=im.crop(box);part=Image.new('RGB',(half.width*2,half.height),(255,0,255));part.paste(half,(0,0));part.paste(ImageOps.mirror(half),(half.width,0))
    dest=(cell*384+(384-part.width)//2,455-part.height);sheet.paste(part,dest)
    operations.append(dict(cell=cell+1,state=state,source_half=box,destination=list(dest),method='Retain generated rear panel left half and reflect around its axial center; remove unintended visible right side depth. No source side artwork used; no recolor.'))
sheet.save(out/'Up_sheet.png')
write(out/'derivation.json',dict(observed_at=now(),parent='generation/Up/revision_02/raw.png',parent_sha256=sha(raw),output='local_raster_revision_01/Up_sheet.png',output_sha256=sha(out/'Up_sheet.png'),finding='Generated true rear fittings/no lock were correct, but unintended right side face made it slightly three-quarter. Local symmetry uses only the new rear surface.',operations=operations,original_preserved=True,paid_request_count=0))
print(json.dumps(dict(output=str(out/'Up_sheet.png'))))
