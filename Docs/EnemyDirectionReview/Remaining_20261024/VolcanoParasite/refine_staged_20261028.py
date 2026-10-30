from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,shutil,os
import numpy as np
D=Path(__file__).resolve().parent;H=D.parent;A=D/'staged_art';name='VolcanoParasite'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
c=read(H/'conversation_chain.json');assert c['state']=='active' and c['current_character']==name and c['owner_thread_id']==os.environ['CODEX_THREAD_ID']
backup=D/'local_raster_revision_01';backup.mkdir(exist_ok=False);shutil.copytree(A,backup/'before')
for p in [D/'parts_clean.png',D/'offline_rig_proof.png',D/'offline_Up.png',D/'offline_Down.png']:shutil.copy2(p,backup/p.name)
pieces={p.stem:Image.open(p).convert('RGBA') for p in A.glob('*.png') if p.name!=name+'_Directions.png'}
assert len(pieces)==12
mapping={'Up_Body':'Up_Segment','Down_Body':'Up_Segment','Down_Segment':'Down_Tip','Down_Tip':'Up_Tip'}
original={k:v.copy() for k,v in pieces.items()}
for dest,source in mapping.items():pieces[dest]=original[source].copy()
holes_report={}
for key,im in pieces.items():
    a=np.asarray(im).copy();pad=Image.new('L',(im.width+2,im.height+2),255);pad.paste(Image.fromarray(np.where(a[:,:,3]==0,255,0).astype('uint8')),(1,1));ImageDraw.floodfill(pad,(0,0),127)
    holes=np.asarray(pad)[1:-1,1:-1]==255;count=int(holes.sum());before=a.copy()
    for y,x in np.argwhere(holes):
        radius=1
        while True:
            y0,y1=max(0,y-radius),min(im.height,y+radius+1);x0,x1=max(0,x-radius),min(im.width,x+radius+1)
            candidates=np.argwhere(before[y0:y1,x0:x1,3]==255)
            if len(candidates):
                candidates+=np.array([y0,x0]);ds=((candidates-np.array([y,x]))**2).sum(axis=1);yy,xx=candidates[ds.argmin()];a[y,x]=before[yy,xx];break
            radius+=1
            assert radius<max(im.size)
    assert np.array_equal(before[~holes],a[~holes]);holes_report[key]={'filled_internal_alpha_pixels':count,'other_pixels_preserved':True}
    pieces[key]=Image.fromarray(a,'RGBA')
atlas=Image.new('RGBA',(2048,2048));slices=[];x=y=8;rh=0
for key,im in pieces.items():
    if x+im.width+8>2048:x=8;y+=rh+8;rh=0
    assert y+im.height+8<=2048
    atlas.alpha_composite(im,(x,y));im.save(A/(key+'.png'));slices.append({'name':key,'x':x,'y':2048-y-im.height,'w':im.width,'h':im.height,'pivotX':.5,'pivotY':.5});x+=im.width+8;rh=max(rh,im.height)
atlas.save(A/(name+'_Directions.png'))
(A/(name+'_Directions.sprites.json')).write_text(json.dumps({'texture':name+'_Directions.png','width':2048,'height':2048,'ppu':100,'sprites':slices},indent=2)+'\n',encoding='utf-8')
layout=read(A/(name+'_Directions.layout.json'));h=layout['referenceHeight'];bottom=layout['referenceBottom']
positions={'Up':{'Head':(.75,.64,.44,12),'Body':(.56,.60,.43,20),'Segment':(.38,.47,.34,22),'Rear':(.22,.29,.21,25)},'Down':{'Head':(.31,.66,.46,35),'Body':(.49,.60,.43,20),'Segment':(.66,.47,.34,18),'Rear':(.80,.29,.21,10)}}
for v in layout['views']:
    for part in v['parts']:
        yy,ww,hh,order=positions[v['direction']][part['name']];part.update(x=0,y=bottom+yy*h,width=ww*h,height=hh*h,order=order,phase={'Body':0,'Segment':.33,'Rear':.66,'Head':0}[part['name']])
layout['motion']={'legAngle':0,'legLift':0,'bodyBob':.003,'bodyRoll':.65,'tailSwing':0}
(A/(name+'_Directions.layout.json')).write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
proof=Image.new('RGB',(1600,700),(40,48,37));draw=ImageDraw.Draw(proof)
for i,(key,im) in enumerate(pieces.items()):
    p=im.copy();p.thumbnail((190,300));proof.paste(p,(i%8*200+(200-p.width)//2,i//8*350+35),p);draw.text((i%8*200+4,i//8*350+8),key,fill='white')
proof.save(D/'parts_clean.png')
report={'revision':'local_raster_revision_01','reason':'Default composition repeated a multi-segment generated Body under independent sections. Use actual single-segment successful cutouts for four attached shrinking crawler sections. No new organs, AI request or source pixel redraw.','piece_mapping':mapping,'provenance':'Destination images derive from the named original staged cutout in local_raster_revision_01/before; original raw/request/results unchanged. Down Body uses a nonfacial gold dorsal section from Up; Down front heads remain Down revision_01.','alpha':holes_report,'filled_pixels':sum(v['filled_internal_alpha_pixels'] for v in holes_report.values()),'staged_hashes':{p.name:sha(p) for p in A.iterdir() if p.is_file()},'layout_normalized':positions,'user_approved':False}
(D/'local_raster_revision_01.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'parts':len(pieces),'filled_pixels':report['filled_pixels'],'phase_offsets':[0,.33,.66]}))
