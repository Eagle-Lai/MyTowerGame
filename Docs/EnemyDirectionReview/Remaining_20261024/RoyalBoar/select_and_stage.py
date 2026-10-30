from pathlib import Path
from PIL import Image
import hashlib,json
D=Path(__file__).resolve().parent
R=D/'raster_revision_01';R.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
up=D/'generation/Up/revision_01/raw.png';down=D/'generation/Down/raw.png'
src=Image.open(down).convert('RGB');rear=Image.open(up).convert('RGB')
assert src.size==rear.size==(1536,1024)
# The torso has no direction-specific face, tuft, appendage, or equipment.
# Reuse only that detached gold spotted torso; keep actual Down expression heads.
src.paste(rear.crop((1040,0,1536,550)),(1040,0))
src.save(R/'Down_derived_sheet.png')
parts=['HeadNormal','HeadAngry','HeadDead','Body','LegFront','LegBack','Tail']
rects=[[0,0,370,550],[375,0,740,550],[745,0,1080,550],[1080,0,1536,550],[0,550,370,1024],[375,550,740,1024],[745,550,1080,1024]]
# Up first three are identical; all use the exact first reviewed rear head crop.
selection=dict(Up='generation/Up/revision_01/raw.png',Down='raster_revision_01/Down_derived_sheet.png',transparent_parts=['Up_Tail','Down_Tail'],rectangles={direction+'_'+part:rect for direction in ['Up','Down'] for part,rect in zip(parts,rects)},reason='Derived Down replaces only rejected duplicate-face torso with the plain Up revision torso; no view-specific detail in torso. Original Down heads/legs retained. No original independent tail: transparent compatibility slice and rig nodes removed.')
(D/'art_selection.json').write_text(json.dumps(selection,indent=2)+'\n',encoding='utf-8')
record=dict(revision='raster_revision_01',method='Local raster assembly; not an AI response. Down expressions and limbs from original paid Down, detached plain torso from successful Up revision_01. Two Down revision requests explicitly failed HTTP503 No available compatible accounts, preserved unchanged.',sources={str(p.relative_to(D)):sha(p) for p in [up,down,D/'generation/Down/revision_01/result.json',D/'generation/Down/revision_02/result.json']},derived_sha256=sha(R/'Down_derived_sheet.png'))
(R/'assembly.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print('Reviewed source selection and local assembly saved')
