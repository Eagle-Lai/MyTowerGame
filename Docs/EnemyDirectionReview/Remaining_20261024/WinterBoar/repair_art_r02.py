"""Replace rejected r01 crown repair with a curved skull and preserved original brows/ears."""
from pathlib import Path
import hashlib,json,os,shutil,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
D=Path(__file__).resolve().parent;H=D.parent
c=json.loads((H/'conversation_chain.json').read_text(encoding='utf-8'))
assert c['state']=='active' and c['current_character']=='WinterBoar' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert not (D/'installed_manifest.json').exists()
O=D/'local_raster_r02';O.mkdir(exist_ok=False)
old=D/'offline_art_r01';old.mkdir(exist_ok=False)
for f in ['offline_rig_proof.png','offline_Up.png','offline_Down.png','parts_clean.png']:
    shutil.copy2(D/f,old/f)
shutil.copytree(D/'staged_art',old/'staged_art')
(old/'REJECTED.json').write_text(json.dumps({'revision':'art_r01','finding':'Down crown repair was angular, overlaid upper brows and clipped ear. Not installed; replace using original successful raw.'},indent=2)+'\n',encoding='utf-8')
source=Image.open(D/'local_raster_r01/Down_clean_unretouched.png').convert('RGBA')
result=source.copy()
audit=[]
for offset in [0,502,1010]:
    original=source.crop((offset,0,offset+500,480))
    # Restore each ear and each brow from the original after the skull redraw.
    ears=[[(93,128),(132,129),(163,154),(167,207),(139,230),(95,202)],[(365,149),(414,125),(433,131),(430,193),(406,223),(373,213)]]
    brows=[[(134,204),(157,200),(194,207),(226,229),(245,261),(236,278),(211,274),(180,253),(138,244)],[(272,235),(295,212),(326,200),(380,193),(387,239),(349,249),(307,268),(278,279),(269,260)]]
    patch=original.resize((1500,1440),Image.Resampling.NEAREST)
    dr=ImageDraw.Draw(patch)
    dr.rectangle((150*3,50*3,384*3,235*3),fill=(0,0,0,0))
    # Smooth crown: no bottom outline or horizontal band. Lower fill is hidden
    # beneath the restored brow cells and blends into original cream forehead.
    pts=[]
    control=[(145,211),(170,151),(318,137),(380,205)]
    for t in np.linspace(0,1,160):
        q=sum(((1-t)**3,3*(1-t)**2*t,3*(1-t)*t*t,t**3)[i]*np.array(control[i]) for i in range(4))
        pts.append(tuple(q))
    dr.polygon([(round(x*3),round(y*3)) for x,y in pts+[(372,252),(150,252)]],fill=(233,230,220,255))
    dr.line([(round(x*3),round(y*3)) for x,y in pts],fill=(47,42,26,255),width=18,joint='curve')
    patch=patch.resize((500,480),Image.Resampling.LANCZOS)
    # Keep every original pixel outside the documented repair polygon except
    # the upper removed forelock; restore ears and brows in their exact pose.
    for poly in ears+brows:
        m=Image.new('L',original.size);ImageDraw.Draw(m).polygon(poly,fill=255)
        patch.paste(original,(0,0),m)
    result.paste(patch,(offset,0))
    audit.append({'offset_x':offset,'removed_forelock_area':[150,50,384,235],'crown_bezier':control,'original_ears_and_brows_preserved':ears+brows})
result.save(O/'Down_clean_sheet.png')
shutil.copy2(D/'local_raster_r01/Up_clean_sheet.png',O/'Up_clean_sheet.png')
(O/'repair_manifest.json').write_text(json.dumps({'revision':'art_r02','parents':['generation/Down/raw.png','local_raster_r01/Down_clean_unretouched.png'],'originals_unchanged':True,'local_repairs':audit,'rejected':'offline_art_r01/REJECTED.json'},indent=2)+'\n',encoding='utf-8')
s=(H/'pack_character.py').read_text(encoding='utf-8')
start=s.index('    raw=Image.open(source);');end=s.index('rectangles=[]',start)+len('rectangles=[]')
s=s[:start]+"    raw=Image.open(source)\n    clean=Image.open(directory/'local_raster_r02'/(direction+'_clean_sheet.png')).convert('RGBA')\n    mask=np.asarray(clean)[:,:,3]>0\n    transparency='WinterBoar magenta-only alpha and curved crown repair; see local_raster_r02/repair_manifest.json'\n    rectangles=[]"+s[end:]
s=s.replace("        add('Tail','Tail',0 if up else width*.28,.29 if up else .69,.22,tail_h,30 if up else 5,'tail')",'        # No tail in source WinterBoar.')
sys.argv=[str(H/'pack_character.py'),'WinterBoar']
exec(compile(s,str(H/'pack_character.py'),'exec'),{'__file__':str(H/'pack_character.py'),'__name__':'__main__'})
layout=json.loads((old/'staged_art/WinterBoar_Directions.layout.json').read_text())
for v in layout['views']:
    if v['direction']=='Down':
        for p in v['parts']:
            if p['name']=='Body':p['y']=layout['referenceBottom']+layout['referenceHeight']*.60;p['height']=layout['referenceHeight']*.67
            if p['name']=='Head':p['y']=layout['referenceBottom']+layout['referenceHeight']*.405;p['height']=layout['referenceHeight']*.60
(D/'staged_art/WinterBoar_Directions.layout.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
shutil.copy2(D/'layout_adjustments.json',old/'layout_adjustments.json')
adjust=json.loads((D/'layout_adjustments.json').read_text());adjust.update(revision='art_r02',reason='Curved forehead with exact original ears/brows; slightly shorter torso overlap')
adjust['parts']['Down/Body'].update(y=.60,height=.67)
adjust['parts']['Down/Head'].update(y=.405,height=.60)
(D/'layout_adjustments.json').write_text(json.dumps(adjust,indent=2)+'\n',encoding='utf-8')
print('Prepared art_r02, not installed')
