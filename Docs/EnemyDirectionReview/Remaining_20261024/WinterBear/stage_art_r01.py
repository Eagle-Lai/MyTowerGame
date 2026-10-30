"""WinterBear-only reviewed raster preparation, preserving successful AI originals."""
from pathlib import Path
import hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

D = Path(__file__).resolve().parent
H = D.parent
sys.path.insert(0, str(D))
from checkpoint_20261029 import owner, write, now, sha
owner()
assert not (D/'installed_manifest.json').exists()
assert not (D/'art_selection.json').exists(), 'Do not overwrite a staged revision'
O = D/'local_raster_r01'
O.mkdir(exist_ok=True)
sources = {v: D/'generation'/v/'revision_01/raw.png' for v in ['Up', 'Down']}
processing = []
for direction, path in sources.items():
    raw = Image.open(path).convert('RGBA')
    a = np.array(raw)
    assert raw.size == (1536,1024)
    # Down returned a semi-transparent white matte (background alpha 91..160).
    # Its solid drawing is alpha 249..253. Separate by alpha, preserving all RGB.
    lo, span = (180,65) if direction == 'Down' else (30,210)
    alpha = np.clip((a[:,:,3].astype(float)-lo)/span*255,0,255).astype('uint8')
    a[:,:,3] = alpha
    a[alpha==0,:3] = 0
    clean = Image.fromarray(a)
    clean.save(O/(direction+'_clean_unretouched.png'))
    repairs=[]
    if direction == 'Up':
        # Fill the first head's exposed ear cups and inner contours with outer fur.
        # The three rear expressions intentionally use this same pure rear head.
        polygons = [
            [(73,228),(67,210),(68,193),(77,181),(89,175),(104,176),(117,182),(128,194),(117,202),(104,214),(91,230),(84,238)],
            [(272,193),(282,181),(295,176),(308,180),(319,191),(322,207),(315,226),(305,239),(298,228),(288,215),(277,205)]
        ]
        original = np.array(clean).copy()
        for poly in polygons:
            mask=Image.new('L',raw.size)
            ImageDraw.Draw(mask).polygon(poly,fill=255)
            mask=mask.filter(ImageFilter.GaussianBlur(.7))
            m=np.asarray(mask).astype(float)/255
            yy=np.indices(a.shape[:2])[0]
            t=np.clip((yy-175)/65,0,1)
            fur=np.stack([234-25*t,231-26*t,225-28*t],axis=2)
            a[:,:,:3]=np.rint(a[:,:,:3]*(1-m[:,:,None])+fur*m[:,:,None]).astype('uint8')
            repairs.append({'global_polygon':poly,'method':'local white-gray outer-ear fur fill; no inner-ear contour; original exterior alpha retained'})
        a[a[:,:,3]==0,:3]=0
        clean=Image.fromarray(a)
        # Ensure every retouched pixel is confined to the documented ear regions.
        changed=np.any(original!=a,axis=2)
        ys,xs=np.where(changed)
        assert xs.min()>=64 and xs.max()<=325 and ys.min()>=172 and ys.max()<=242
    clean.save(O/(direction+'_clean_sheet.png'))
    processing.append({'direction':direction,'source':path.relative_to(D).as_posix(),'source_sha256':sha(path),'alpha_extrema_original':list(raw.getchannel('A').getextrema()),'alpha_remap':{'zero_below':lo,'opaque_at':lo+span,'reason':'separate background alpha from opaque artwork without RGB color deletion'},'clean_sheet_sha256':sha(O/(direction+'_clean_sheet.png')),'repairs':repairs})

selection={v:sources[v].relative_to(D).as_posix() for v in sources}
selection['rectangles']={}
parts=['HeadNormal','HeadAngry','HeadDead','Body','LegFront','LegBack','Tail']
for direction in sources:
    for j,part in enumerate(parts):
        x=(j%4)*384 if j<4 else (j-4)*384
        y0=0 if j<4 else 500 if direction=='Down' else 512
        y1=(550 if part=='Body' else 500) if direction=='Down' and j<4 else 512 if j<4 else 1024
        selection['rectangles'][direction+'_'+part]=[x,y0,x+384,y1]
write(D/'art_selection.json',selection)
write(O/'repair_manifest.json',{'at':now(),'revision':'art_r01','originals_unchanged':True,'processing':processing})

# Reuse the existing pack/layout contract, replacing only its chroma-removal block.
source=(H/'pack_character.py').read_text(encoding='utf-8')
start=source.index('    raw=Image.open(source);')
end=source.index('rectangles=[]',start)+len('rectangles=[]')
replacement="""    raw=Image.open(source)
    clean=Image.open(directory/'local_raster_r01'/(direction+'_clean_sheet.png')).convert('RGBA')
    mask=np.asarray(clean)[:,:,3]>0
    transparency='direction-specific alpha separation; original RGB retained; Up outer-ear local repair; see local_raster_r01/repair_manifest.json'
    rectangles=[]"""
source=source[:start]+replacement+source[end:]
sys.argv=[str(H/'pack_character.py'),'WinterBear']
exec(compile(source,str(H/'pack_character.py'),'exec'),{'__file__':str(H/'pack_character.py'),'__name__':'__main__'})

updates={}
for direction in ['Up','Down']:
    up=direction=='Up'
    updates[direction+'/Body']={'x':0,'y':.48 if up else .63,'width':.60 if up else .64,'height':.60 if up else .64,'order':20}
    updates[direction+'/Head']={'x':0,'y':.825 if up else .43,'width':.56 if up else .63,'height':.43 if up else .46,'order':12 if up else 35}
    for side in ['L','R']:
        sign=-1 if side=='L' else 1
        for front in [True,False]:
            near=not front if up else front
            updates[direction+'/'+('Fore' if front else 'Hind')+side]={'x':sign*(.24 if near else .235),'y':.34 if near else .65,'width':.23 if near else .21,'height':.34 if near else .28,'order':8}
    updates[direction+'/Tail']={'x':0 if up else .16,'y':.24 if up else .81,'width':.11,'height':.14,'order':30 if up else 5,'angle':0 if up else -15}
write(D/'layout_adjustments.json',{'revision':'art_r01','reason':'stocky Bear quadruped with four heavy paws and tiny pointed tail; native side behavior unchanged','layout':{'motion':{'legAngle':7,'legLift':.09,'bodyBob':.003,'bodyRoll':.65,'tailSwing':4}},'parts':updates})
print('Prepared art_r01 without production writes')
