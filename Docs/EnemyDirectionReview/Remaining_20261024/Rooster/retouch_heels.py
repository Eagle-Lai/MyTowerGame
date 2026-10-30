"""Rooster-only rear foot repair from paid raster; preserve all original sheets."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,math
D=Path(__file__).resolve().parent;A=D/'staged_art';R=D/'raster_revision_02'
R.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
p=A/'Up_Leg.png';source=Image.open(p).convert('RGBA')
before=R/'Up_Leg_before.png'
if not before.exists():source.save(before)
else:assert sha(p)==sha(before),'Run through stage to restore source before retouch'
# The source is upside down. Preserve its gold shaft and cream cuff, flipping
# vertically; the three forward toes are then replaced by a rear heel/hallux.
im=source.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
im.paste((0,0,0,0),(0,195,im.width,im.height))
scale=4
heel=Image.new('RGBA',(im.width*scale,im.height*scale))
draw=ImageDraw.Draw(heel)
def poly(points,fill):draw.polygon([(round(x*scale),round(y*scale)) for x,y in points],fill=fill)
def ellipse(box,fill):draw.ellipse(tuple(round(x*scale) for x in box),fill=fill)
# Rear tarsus and rounded heel; the front three digits point away and are
# concealed by the heel rather than displayed as three viewer-facing talons.
poly([(58,177),(107,177),(108,230),(124,261),(118,280),(91,288),(64,282),(46,269),(51,248)],(60,43,13,255))
poly([(66,176),(100,176),(100,230),(114,259),(109,272),(88,277),(66,272),(56,263),(64,242)],(232,162,7,255))
poly([(67,184),(80,187),(78,240),(70,262),(61,264),(67,235)],(255,191,14,255))
poly([(95,184),(101,187),(101,229),(112,260),(105,270),(91,273),(95,251)],(192,127,6,255))
ellipse((65,249,105,274),(245,178,9,255))
# Single rear hallux, short and tapered, with a subtle gold claw tip.
poly([(75,263),(94,263),(101,284),(91,303),(81,307),(70,295),(69,283)],(61,44,15,255))
poly([(79,269),(90,269),(94,284),(87,298),(81,299),(77,291),(76,283)],(226,156,7,255))
poly([(81,286),(90,284),(87,295),(82,299),(79,293)],(255,199,35,255))
heel=heel.resize(im.size,Image.Resampling.LANCZOS)
im.alpha_composite(heel)
# Blend retained cuff over the tarsus root so the joint has the original outline.
cuff=source.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
cuff.paste((0,0,0,0),(0,195,im.width,im.height))
im.alpha_composite(cuff)
im.save(p);im.save(R/'Up_Leg_after.png')
manifest=json.loads((A/'Rooster_Directions.sprites.json').read_text())
s=next(s for s in manifest['sprites'] if s['name']=='Up_Leg')
atlas=Image.open(A/'Rooster_Directions.png').convert('RGBA')
atlas.paste(im,(s['x'],2048-s['y']-s['h']));atlas.save(A/'Rooster_Directions.png')
# Rebuild the part proof after retouch, not from packer's pre-retouch images.
proof=Image.new('RGB',(1600,700),(40,48,37));draw=ImageDraw.Draw(proof)
for i,s in enumerate(manifest['sprites']):
    piece=Image.open(A/(s['name']+'.png')).convert('RGBA');piece.thumbnail((195,300))
    proof.paste(piece,(i%8*200+(200-piece.width)//2,i//8*350+35),piece)
    draw.text((i%8*200+5,i//8*350+8),s['name'],fill='white')
proof.save(D/'parts_clean.png')
record=dict(revision='raster_revision_02',source='generation/Up/raw.png',source_sha256=sha(D/'generation/Up/raw.png'),before_sha256=sha(before),after_sha256=sha(p),
    method='Local raster repair only: vertically reorient retained shaft/cuff, replace front three-toe fan with gold rear heel and single rear hallux using sampled palette. Original paid sheet preserved. Atlas and part proof rebuilt.',status='pending_actual_visual_review')
(D/'raster_retouch.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
