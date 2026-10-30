"""WinterBoar final offline cleanup from successful images, without new requests."""
from pathlib import Path
import json,os,shutil,sys
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;H=D.parent
c=json.loads((H/'conversation_chain.json').read_text(encoding='utf-8'))
assert c['state']=='active' and c['current_character']=='WinterBoar' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert not (D/'installed_manifest.json').exists()
O=D/'local_raster_r03';O.mkdir(exist_ok=False)
old=D/'offline_art_r02';old.mkdir(exist_ok=False)
for f in ['offline_rig_proof.png','offline_Up.png','offline_Down.png','parts_clean.png','layout_adjustments.json']:
    shutil.copy2(D/f,old/f)
shutil.copytree(D/'staged_art',old/'staged_art')
(old/'REJECTED.json').write_text(json.dumps({'revision':'art_r02','finding':'Tiny white nick on left brow, magenta fringe and exposed rounded roots on far legs. Not installed.'},indent=2)+'\n',encoding='utf-8')
repairs=[]
for direction in ['Up','Down']:
    im=Image.open(D/'local_raster_r02'/(direction+'_clean_sheet.png')).convert('RGBA')
    if direction=='Down':
        orig=Image.open(D/'local_raster_r01/Down_clean_unretouched.png')
        for left in [0,502]:
            poly=[(left+131,202),(left+155,198),(left+181,201),(left+213,217),(left+238,242),(left+251,265),(left+241,284),(left+207,280),(left+169,261),(left+135,248)]
            mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(poly,fill=255)
            im.paste(orig,(0,0),mask)
            repairs.append({'part':'Down left brow','polygon':poly,'method':'restore whole original brow pixels'})
    a=np.array(im);v=a[:,:,:3].astype(np.int16);excess=np.minimum(v[:,:,0],v[:,:,2])-v[:,:,1]
    fringe=(excess>15)&(a[:,:,3]>0)
    removed=int(fringe.sum());a[fringe]=0
    im=Image.fromarray(a);im.save(O/(direction+'_clean_sheet.png'))
    repairs.append({'direction':direction,'magenta_fringe_pixels_removed':removed,'criterion':'min(R,B)-G>15; only magenta-contaminated edge pixels, no source-colored interiors deleted'})
s=(H/'pack_character.py').read_text(encoding='utf-8')
start=s.index('    raw=Image.open(source);');end=s.index('rectangles=[]',start)+len('rectangles=[]')
s=s[:start]+"    raw=Image.open(source)\n    clean=Image.open(directory/'local_raster_r03'/(direction+'_clean_sheet.png')).convert('RGBA')\n    mask=np.asarray(clean)[:,:,3]>0\n    transparency='WinterBoar magenta-only removal, curved crown and preserved brows; local_raster_r03'\n    rectangles=[]"+s[end:]
s=s.replace("        add('Tail','Tail',0 if up else width*.28,.29 if up else .69,.22,tail_h,30 if up else 5,'tail')",'        # No tail exists in actual source.')
sys.argv=[str(H/'pack_character.py'),'WinterBoar']
exec(compile(s,str(H/'pack_character.py'),'exec'),{'__file__':str(H/'pack_character.py'),'__name__':'__main__'})
layout=json.loads((old/'staged_art/WinterBoar_Directions.layout.json').read_text());h=layout['referenceHeight'];bottom=layout['referenceBottom']
for v in layout['views']:
    for p in v['parts']:
        if p['role']=='leg':
            front=p['name'].startswith('Fore');near=(not front) if v['direction']=='Up' else front
            sign=-1 if p['name'].endswith('L') else 1
            p['x']=h*sign*(.31 if near else .255)
            if not near:p['y']=bottom+h*.57
layout['motion']={'legAngle':8,'legLift':.08,'bodyBob':.003,'bodyRoll':.7,'tailSwing':0}
(D/'staged_art/WinterBoar_Directions.layout.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
(O/'repair_manifest.json').write_text(json.dumps({'revision':'art_r03','parent':'local_raster_r02/repair_manifest.json','originals_unchanged':True,'repairs':repairs,'layout':'Far hip/shoulder roots inset to0.255h and0.57h; near feet0.31h. Four short legs, no tail.'},indent=2)+'\n',encoding='utf-8')
adjust=json.loads((D/'layout_adjustments.json').read_text());adjust.update(revision='art_r03',reason='Whole brow restored, magenta fringe removed, four roots inset into body')
adjust['parts']={v['direction']+'/'+p['name']:{k:p[k]/h if k in ['x','width','height'] else (p[k]-bottom)/h if k=='y' else p[k] for k in ['x','y','width','height','order']} for v in layout['views'] for p in v['parts']}
(D/'layout_adjustments.json').write_text(json.dumps(adjust,indent=2)+'\n',encoding='utf-8')
print('Prepared art_r03; no production writes')
