from session_swine import *
from PIL import Image, ImageDraw, ImageFilter
import numpy as np, shutil
owner(); assert not (D/'staged_art').exists()
out=D/'local_raster_revision_01';out.mkdir(exist_ok=False)
raw=D/'generation/Up/raw.png'; im=Image.open(raw).convert('RGB')
# Preserve actual returned pixels below a smooth upper head contour; remove only
# the duplicate head ears. The two ears on the original returned torso remain.
def bezier(a,b,c,d):
    return [tuple((1-t)**3*a[j]+3*(1-t)**2*t*b[j]+3*(1-t)*t*t*c[j]+t**3*d[j] for j in [0,1]) for t in np.linspace(0,1,81)]
curve=bezier((45,304),(42,225),(96,168),(201,168))+bezier((201,168),(303,168),(359,226),(362,304))
for dx in [0,371,742]:
    pts=[(x+dx,y) for x,y in curve]
    mask=Image.new('L',im.size,0); draw=ImageDraw.Draw(mask)
    draw.polygon([(25+dx,110),(380+dx,110),(380+dx,304)]+list(reversed(pts))+[(25+dx,304)],fill=255)
    im.paste((255,0,255),mask=mask)
    layer=Image.new('RGBA',(im.width*3,im.height*3));d=ImageDraw.Draw(layer)
    d.line([(round(x*3),round(y*3)) for x,y in pts],fill=(39,33,15,255),width=25,joint='curve')
    layer=layer.resize(im.size,Image.Resampling.LANCZOS)
    im=Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')
# Cover the forward toe notch only; preserve the rounded heel and outer outline.
draw=ImageDraw.Draw(im);draw.polygon([(188,835),(183,854),(197,854),(193,835)],fill=(200,158,75))
im.save(out/'Up_sheet.png')
write(out/'processing.json',dict(observed_at=now(),parent='generation/Up/raw.png',parent_sha256=sha(raw),output='Up_sheet.png',output_sha256=sha(out/'Up_sheet.png'),method='Local raster mask above recorded cubic head contours; antialiased dark outline restoration; small heel seam fill. Original paid raw unchanged.',head_contour=curve,head_offsets=[0,371,742],ear_policy='Exactly two ears retained on torso, duplicate pair removed from each rear head state',heel_fill_rect=[183,835,197,854],no_paid_retry=True))
write(D/'generation/Down/review_20261028.json',dict(observed_at=now(),viewed='Original 1536x1024 PNG',raw_sha256=sha(D/'generation/Down/raw.png'),accepted_for_staging=True,observation='Axial broad golden snout, two nostrils, two ivory tusks, round normal eyes, angular angry lids, blank dead eyes and small tongue. No ears on detached face, two small triangular ears on torso. Four leg instances can use two short tan hoof slices; one small pointed tail. No rider, mane, armor or ground shadow.'))
parts=read(D/'anatomy_plan.json')['parts'];rectangles={}
for direction,rects in [('Up',[[25,110,380,490],[396,110,751,490],[767,110,1122,490],[1140,65,1525,535],[110,560,275,900],[475,560,680,900],[890,565,1000,895]]),('Down',[[5,165,375,535],[390,165,755,535],[770,165,1130,535],[1145,60,1530,555],[210,590,435,975],[645,590,880,975],[1120,640,1255,930]])]:
    for p,rect in zip(parts,rects):rectangles[direction+'_'+p]=rect
write(D/'art_selection.json',dict(Up='local_raster_revision_01/Up_sheet.png',Down='generation/Down/raw.png',rectangles=rectangles,selection_note='Both original HTTP200 sheets actually viewed; Up duplicate head ears removed locally, source torso pair retained. Rear heel notch closed. All original requests and raw unchanged.'))
adj=dict(layout=dict(motion=dict(legAngle=8.0,legLift=.014,bodyBob=.004,bodyRoll=.7,tailSwing=3.0)),parts={},reason='Round squat boar, four short tan feet and tiny tapered tail. Solid paired roots buried under torso. Ears remain only on torso; small plain rear head overlaps neck cap. Diagonal phase pairs, small leg compression and body roll.')
for direction in ['Up','Down']:
    up=direction=='Up'
    adj['parts'][direction+'/Body']=dict(y=.52 if up else .59,width=.84,height=.72,order=20)
    adj['parts'][direction+'/Head']=dict(y=.85 if up else .405,width=.53 if up else .86,height=.34 if up else .59,order=22 if up else 35)
    for side in ['L','R']:
        sign=-1 if side=='L' else 1
        for front in [True,False]:
            near=(not front) if up else front
            adj['parts'][direction+'/'+('Fore' if front else 'Hind')+side]=dict(x=sign*(.285 if near else .35),y=.29 if near else .52,width=.16,height=.19,order=8,angle=sign*(0 if near else 8))
    adj['parts'][direction+'/Tail']=dict(x=0,y=.24 if up else .91,width=.07,height=.13,order=30 if up else 5,angle=180 if up else 0)
write(D/'layout_adjustments.json',adj)
run('character_step.py','stage',NAME)
print(json.dumps(dict(staged=NAME,revision=out.name)))
