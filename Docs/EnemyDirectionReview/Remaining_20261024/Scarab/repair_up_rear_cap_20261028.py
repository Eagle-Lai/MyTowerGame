"""Local raster cleanup of the generated rear head. No paid call, no production write."""
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np, hashlib, json
from datetime import datetime, timezone, timedelta
D=Path(__file__).resolve().parent
source=D/'generation/Up/revision_01/raw.png'
out=D/'local_raster_revision_01'
out.mkdir(exist_ok=False)
raw=Image.open(source).convert('RGB')
assert raw.size==(1536,1024)
image=raw.copy()
# The returned rear head has no lens eyes but incorrectly retains front mouth parts.
# Keep its antennae and upper cap pixels. Replace only the bottom cap/mandible region.
head=raw.crop((0,0,384,512))
edited=head.copy()
draw=ImageDraw.Draw(edited)
draw.rectangle((65,366,330,470), fill=(255,0,255))
outer=Image.new('L',head.size,0); od=ImageDraw.Draw(outer)
od.ellipse((87,227,301,407),fill=255)
inner=Image.new('L',head.size,0); idr=ImageDraw.Draw(inner)
idr.ellipse((95,235,293,399),fill=255)
a=np.asarray(edited).copy(); original=np.asarray(head)
o=np.asarray(outer)>0; i=np.asarray(inner)>0
yy,xx=np.indices(o.shape)
bottom=(yy>=366)&o
a[bottom]=[49,43,22]
inside=(yy>=366)&i
# Continue the original olive cap tones from a nearby intact band, not a new organ.
sample=np.asarray(head)[350:362,125:267].mean(axis=(0,1)).round().astype(np.uint8)
a[inside]=sample
edited=Image.fromarray(a,'RGB')
for x in [0,384,768]: image.paste(edited,(x,0))
image.save(out/'Up_sheet.png')
preview=Image.new('RGB',(768,512),(40,48,37))
preview.paste(head,(0,0)); preview.paste(edited,(384,0))
preview.save(out/'rear_cap_before_after.png')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),parent='generation/Up/revision_01/raw.png',parent_sha256=sha(source),output='local_raster_revision_01/Up_sheet.png',output_sha256=sha(out/'Up_sheet.png'),method='Local raster removal of incorrect rear mandibles; close lower cap with sampled original olive color and dark rim. Reuse the same repaired rear head for all expression states.',edited_region='First head cell x65..330 y366..470; copy repaired first cell to the other two head cells',invariants=['Original AI raw preserved','Original antennae, upper head, carapace and leg pixels preserved','No front eyes or mouth on rear head','No invented tail or extra limbs','No production resources written'],ai_generated_original=False,source_is_ai_return=True,status='pending_actual_visual_review')
(out/'processing.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(output=str(out/'Up_sheet.png'),review=str(out/'rear_cap_before_after.png'))))
