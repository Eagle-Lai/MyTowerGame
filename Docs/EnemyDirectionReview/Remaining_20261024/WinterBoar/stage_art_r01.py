"""WinterBoar local raster revision: chroma extraction and duplicate forelock repair."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib,json,os,sys,shutil
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;H=D.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
c=json.loads((H/'conversation_chain.json').read_text(encoding='utf-8'))
assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='WinterBoar'
assert c['dispatch_token']=='winterbear-to-winterboar-20261029_121124-c33ba1f5-87c8-4aee-8729-55b098f67a75'
assert not (D/'art_selection.json').exists() and not (D/'installed_manifest.json').exists()
O=D/'local_raster_r01';O.mkdir(exist_ok=False)
reports=[]
for direction in ['Up','Down']:
    p=D/'generation'/direction/'raw.png'
    raw=Image.open(p).convert('RGBA');a=np.array(raw);rgb=a[:,:,:3].astype(float)
    # Only magenta-like background is removed. Cream, gray, brown, black retained.
    excess=np.minimum(rgb[:,:,0],rgb[:,:,2])-rgb[:,:,1]
    alpha=np.clip((90-excess)/65*255,0,255).astype('uint8')
    alpha=np.minimum(alpha,a[:,:,3]);a[:,:,3]=alpha;a[alpha==0,:3]=0
    clean=Image.fromarray(a);clean.save(O/(direction+'_clean_unretouched.png'))
    repairs=[]
    if direction=='Down':
        # Replace only repeated top forelock on the three head slices with a
        # rounded cream skull. Body retains the one genuine dorsal mane.
        # Work at 3x for clean contour antialiasing; keep ears/brows/face/tusks.
        big=clean.resize((4608,3072),Image.Resampling.NEAREST)
        dr=ImageDraw.Draw(big)
        for left in [0,502,1010]:
            er=[(left+144,56),(left+406,56),(left+406,194),(left+137,194)]
            dr.polygon([(x*3,y*3) for x,y in er],fill=(0,0,0,0))
            # Crown arc has its lower edge concealed by the retained brow/face.
            curve=[(left+126,215),(left+143,183),(left+172,161),(left+207,147),(left+245,143),(left+283,148),(left+320,161),(left+354,184),(left+374,208)]
            fill=curve+[(left+365,231),(left+130,231)]
            dr.polygon([(x*3,y*3) for x,y in fill],fill=(232,229,220,255))
            dr.line([(x*3,y*3) for x,y in curve],fill=(48,42,25,255),width=18,joint='curve')
            repairs.append({'head_offset_x':left,'area':[left+126,56,left+406,231],'method':'remove duplicate forelock above brows; redraw one rounded cream skull crown with dark outline; ears and face kept'})
        clean=big.resize(raw.size,Image.Resampling.LANCZOS)
    clean.save(O/(direction+'_clean_sheet.png'))
    reports.append({'direction':direction,'source':p.relative_to(D).as_posix(),'source_sha256':sha(p),'format':'PNG','size':list(raw.size),'mode':Image.open(p).mode,'background_method':'magenta excess90..25 alpha ramp, only red-and-blue-dominant chroma; source RGB preserved except documented head crown repair','repairs':repairs,'clean_sha256':sha(O/(direction+'_clean_sheet.png'))})

parts=['HeadNormal','HeadAngry','HeadDead','Body','LegFront','LegBack']
rects={'Up':[[70,65,480,430],[565,65,975,430],[1060,65,1470,430],[0,435,580,1000],[675,585,925,925],[1100,585,1360,925]],'Down':[[25,45,490,475],[525,45,998,475],[1030,45,1515,475],[15,480,560,1000],[655,560,930,960],[1110,560,1390,960]]}
selection={v:'generation/'+v+'/raw.png' for v in rects}
selection['rectangles']={v+'_'+p:r for v,rs in rects.items() for p,r in zip(parts,rs)}
(D/'art_selection.json').write_text(json.dumps(selection,indent=2)+'\n',encoding='utf-8')
(O/'repair_manifest.json').write_text(json.dumps({'revision':'art_r01','created_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'originals_unchanged':True,'processing':reports},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Render current battle source without replacing shared reference contact.
s=(H/'render_source_reference.py').read_text(encoding='utf-8')
s=s.replace("contact.save(HERE/'source_reference_contact.png')","contact.save(HERE/'WinterBoar/reference/battle_reference_contact.png')")
sys.argv=[str(H/'render_source_reference.py'),'--battle','--name','WinterBoar']
exec(compile(s,str(H/'render_source_reference.py'),'exec'),{'__file__':str(H/'render_source_reference.py'),'__name__':'__main__'})

# Retain the established atlas/layout contract; specialize only cleanup/tail.
s=(H/'pack_character.py').read_text(encoding='utf-8')
start=s.index('    raw=Image.open(source);');end=s.index('rectangles=[]',start)+len('rectangles=[]')
s=s[:start]+"    raw=Image.open(source)\n    clean=Image.open(directory/'local_raster_r01'/(direction+'_clean_sheet.png')).convert('RGBA')\n    mask=np.asarray(clean)[:,:,3]>0\n    transparency='WinterBoar magenta-only removal and documented local crown repair; see local_raster_r01/repair_manifest.json'\n    rectangles=[]"+s[end:]
s=s.replace("        add('Tail','Tail',0 if up else width*.28,.29 if up else .69,.22,tail_h,30 if up else 5,'tail')",'        # No Tail sprite or node exists in original WinterBoar.')
sys.argv=[str(H/'pack_character.py'),'WinterBoar']
exec(compile(s,str(H/'pack_character.py'),'exec'),{'__file__':str(H/'pack_character.py'),'__name__':'__main__'})
lp=D/'staged_art/WinterBoar_Directions.layout.json';layout=json.loads(lp.read_text())
h=layout['referenceHeight'];bottom=layout['referenceBottom']
layout['motion']={'legAngle':8,'legLift':.08,'bodyBob':.003,'bodyRoll':.7,'tailSwing':0}
for v in layout['views']:
    up=v['direction']=='Up'
    for p in v['parts']:
        if p['name']=='Body':p.update(x=0,y=bottom+h*(.51 if up else .63),width=h*.84,height=h*(.78 if up else .70),order=20)
        elif p['name']=='Head':p.update(x=0,y=bottom+h*(.83 if up else .41),width=h*(.65 if up else .94),height=h*(.49 if up else .58),order=12 if up else 35)
        else:
            front=p['name'].startswith('Fore');near=(not front) if up else front;sign=-1 if p['name'].endswith('L') else 1
            p.update(x=sign*h*(.33 if near else .31),y=bottom+h*(.29 if near else .61),width=h*(.18 if near else .16),height=h*(.23 if near else .20),order=8)
lp.write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
(D/'layout_adjustments.json').write_text(json.dumps({'revision':'art_r01','reason':'WinterBoar broad short-legged boar; four legs, no tail; roots placed inside plump torso','layout':{'motion':layout['motion']},'parts':{v['direction']+'/'+p['name']:{k:p[k]/h if k in ['x','width','height'] else (p[k]-bottom)/h if k=='y' else p[k] for k in ['x','y','width','height','order']} for v in layout['views'] for p in v['parts']}},indent=2)+'\n',encoding='utf-8')
print('Staged art_r01; inspect offline proof before installation')
