"""Extract actual returned parts, remove chroma background, and stage one anatomical rig."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,sys,math
HERE=Path(__file__).resolve().parent
name=sys.argv[1];directory=HERE/name
t=next(t for t in json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))['targets'] if t['name']==name)
plan=json.loads((directory/'anatomy_plan.json').read_text(encoding='utf-8'))
selection=json.loads((directory/'art_selection.json').read_text(encoding='utf-8')) if (directory/'art_selection.json').exists() else {}
transparent_parts=set(selection.get('transparent_parts',[]))
parts={};processing=[]
out=directory/'staged_art';out.mkdir(exist_ok=True)
for direction in ['Up','Down']:
    source=directory/selection.get(direction,'generation/'+direction+'/raw.png')
    raw=Image.open(source);rgb=np.asarray(raw.convert('RGB'));a=rgb.astype(np.int16)
    spectral=(a[:,:,2]<=a[:,:,1]+8)&(a[:,:,2]<=a[:,:,0]+12)&((a[:,:,0]-a[:,:,1])<=(a[:,:,1]-a[:,:,2])+26)
    warm=(a[:,:,0]>a[:,:,2]+24)&((a[:,:,0]-a[:,:,1])<170)
    mask=spectral | (warm if selection.get('preserve_warm_foreground',False) else False)
    transparency='gold/neutral foreground spectral mask; opaque interiors; alpha antialias on resampling'
    if selection.get('preserve_warm_foreground',False):
        transparency+='; warm russet foreground pixels preserved by direction-specific opt-in'
    if raw.mode=='RGBA': mask &= np.asarray(raw)[:,:,3]>=128
    rgba=np.dstack([rgb,mask.astype(np.uint8)*255]);rgba[~mask,:3]=0
    clean=Image.fromarray(rgba,'RGBA');rectangles=[]
    for row in range(plan['rows']):
        expected=min(plan['columns'],len(plan['parts'])-row*plan['columns'])
        if expected<=0:continue
        row_parts=plan['parts'][row*plan['columns']:row*plan['columns']+expected]
        explicit=[selection.get('rectangles',{}).get(direction+'_'+p) for p in row_parts]
        if all(explicit):
            for p,rect in zip(row_parts,explicit):
                if direction+'_'+p in transparent_parts:
                    parts[direction+'_'+p]=Image.new('RGBA',(1,1),(0,0,0,0))
                    rectangles.append({'part':p,'source_rect':None,'selection':'intentionally transparent for prefab contract'})
                    continue
                piece=clean.crop(rect);bounds=piece.getbbox()
                if not bounds:raise ValueError('Empty explicit part '+p)
                piece=piece.crop(bounds)
                if direction=='Up' and p in ['HeadAngry','HeadDead']:piece=parts['Up_HeadNormal'].copy()
                parts[direction+'_'+p]=piece
                rectangles.append({'part':p,'source_rect':rect,'tight_bounds':bounds,'selection':'explicit visual review'})
            continue
        y0=round(raw.height*row/plan['rows']);y1=round(raw.height*(row+1)/plan['rows'])
        occupied=mask[y0:y1].sum(axis=0)>=4
        runs=[];start=None
        for x,value in enumerate(np.r_[occupied,False]):
            if value and start is None:start=x
            if not value and start is not None:
                if x-start>=8:runs.append([start,x])
                start=None
        if len(runs)!=expected: raise ValueError(f'{direction} row{row}: expected {expected} separate parts, got {runs}; inspect and add explicit source rects')
        for j,(x0,x1) in enumerate(runs):
            p=plan['parts'][row*plan['columns']+j]
            if direction+'_'+p in transparent_parts:
                parts[direction+'_'+p]=Image.new('RGBA',(1,1),(0,0,0,0))
                rectangles.append({'part':p,'source_rect':None,'selection':'intentionally transparent for prefab contract'})
                continue
            override=selection.get('rectangles',{}).get(direction+'_'+p)
            rect=override or [max(0,x0-3),y0,min(raw.width,x1+3),y1]
            piece=clean.crop(rect);bounds=piece.getbbox()
            if not bounds:raise ValueError('Empty part '+p)
            piece=piece.crop(bounds)
            if direction=='Up' and p in ['HeadAngry','HeadDead']:piece=parts['Up_HeadNormal'].copy()
            parts[direction+'_'+p]=piece
            rectangles.append({'part':p,'source_rect':rect,'tight_bounds':bounds})
    heads=[direction+'_'+p for p in ['HeadNormal','HeadAngry','HeadDead']]
    w=max(parts[p].width for p in heads);h=max(parts[p].height for p in heads)
    for p in heads:
        im=parts[p];canvas=Image.new('RGBA',(w,h));canvas.alpha_composite(im,((w-im.width)//2,(h-im.height)//2));parts[p]=canvas
    processing.append({'direction':direction,'source':source.relative_to(directory).as_posix(),'format':raw.format,'size':list(raw.size),'mode':raw.mode,'rectangles':rectangles,'transparency':transparency,'shadow':'none'})
atlas=Image.new('RGBA',(2048,2048));sprites=[];x=y=8;row_h=0
for key,im in parts.items():
    if max(im.size)>490:im.thumbnail((490,490),Image.Resampling.LANCZOS)
    if x+im.width+8>2048:x=8;y+=row_h+8;row_h=0
    if y+im.height+8>2048:raise ValueError('Atlas full')
    role=key.split('_',1)[1]
    pivot=(.93,.9) if role.startswith('Leg') and role!='Leg' else (.5,.95) if role in ['Leg','ArmWeapon','ArmFree'] else (.93,.85) if role=='Wing' else (.93,.5) if role.startswith('Wing') else (.5,.06) if role=='Tail' else (.93,.5) if role in ['Claw','Feelers','Flap'] else (.5,.03) if role.startswith('Head') and plan['kind']=='chest' else (.5,.95) if role=='Tongue' else (.5,.5)
    if plan['kind']=='quadruped' and role in ['LegFront','LegBack']:pivot=(.5,.87)
    if plan['controller_family']=='Cow' and role=='Tail':pivot=(.5,.94)
    atlas.alpha_composite(im,(x,y));im.save(out/(key+'.png'))
    sprites.append({'name':key,'x':x,'y':2048-y-im.height,'w':im.width,'h':im.height,'pivotX':pivot[0],'pivotY':pivot[1]})
    x+=im.width+8;row_h=max(row_h,im.height)
atlas.save(out/(name+'_Directions.png'))
(out/(name+'_Directions.sprites.json')).write_text(json.dumps({'texture':name+'_Directions.png','width':2048,'height':2048,'ppu':100,'sprites':sprites},indent=2),encoding='utf-8')
reference=json.loads((directory/'reference'/('battle_structure.json' if (directory/'reference/battle_structure.json').exists() else 'source_structure.json')).read_text(encoding='utf-8'))['visible_bounds_root_local']
bottom=reference['min'][1];height=reference['max'][1]-bottom
kind=plan['kind'];views=[]
for direction in ['Up','Down']:
    up=direction=='Up';rig=[]
    def add(node,sprite,xx,yy,ww,hh,order,role,flip=False,phase=0,angle=0,alternate=''):
        rig.append(dict(name=node,sprite=direction+'_'+sprite,x=xx*height,y=bottom+yy*height,width=ww*height,height=hh*height,order=order,role=role,flipX=flip,phase=phase,angle=angle,alternate=direction+'_'+alternate if alternate else ''))
    if kind in ['hexapod','scorpion']:
        beetle=plan['controller_family']=='Scarab';queen=plan['controller_family']=='BugQueen'
        add('Body','Body',0,.52 if queen else .48,.78 if queen else .60,.82 if queen else .68,20,'body')
        add('Head','HeadNormal',0,.85 if up else .26,.36 if queen else .39,.30 if queen else .33,12 if up else 35,'head')
        for side,flip in [('L',False),('R',True)]:
            sign=-1 if side=='L' else 1
            for j,p in enumerate(['Front','Middle','Back']):
                yy=(.64-j*.19) if up else (.24+j*.19)
                add('Leg'+p+side,'Leg'+p,sign*(.23 if queen else .18),yy,.30 if queen else .36,.35 if beetle else .26,8,'leg',flip,(j+(side=='R'))%2,angle=sign*(j-1)*7)
            if kind=='scorpion':add('Claw'+side,'Claw',sign*.16,.70 if up else .23,.37,.31,12 if up else 30,'claw',flip,phase=int(flip),angle=sign*(25 if up else -25))
            if 'Feelers' in plan['parts']:add('Feeler'+side,'Feelers',sign*.12,.8 if up else .20,.36,.20,12 if up else 34,'feeler',flip)
        if kind=='scorpion':add('Tail','Tail',0,.24 if up else .43,.43,.80,25 if up else 5,'tail')
    elif kind=='quadruped':
        small=plan['controller_family'] in ['Pig','Boar','Pug'];bunny=plan['controller_family']=='Bunny';low=t['family']=='Rats'
        width=.83 if small else .66 if low else .72
        add('Body','Body',0,.52 if up else .59,width,.72 if small else .62,20,'body')
        add('Head','HeadNormal',0,.79 if up else .40,width*.96,.38 if up else .48,12 if up else 35,'head')
        for side,flip in [('L',False),('R',True)]:
            sign=-1 if side=='L' else 1
            for front in [True,False]:
                near=(not front) if up else front
                yy=.30 if near else .55
                add(('Fore' if front else 'Hind')+side,'LegFront' if front else 'LegBack',sign*width*.31,yy,width*.28,.23 if small else .32 if near else .26,8,'leg',flip,(int(front)+(side=='R'))%2)
        tail_h=.15 if small or bunny else .24 if t['family']=='Cattle' else .40
        add('Tail','Tail',0 if up else width*.28,.29 if up else .69,.22,tail_h,30 if up else 5,'tail')
    elif kind=='giant':
        add('Body','Body',0,.48,.72,.62,20,'body');add('Head','HeadNormal',0,.83,.48,.40,30,'head')
        for side in ['L','R']:
            sign=-1 if side=='L' else 1
            add('Leg'+side,'Leg',sign*.18,.25,.22,.28,12,'leg',side=='R',int(side=='R'))
        right=-1 if not up else 1
        add('ArmR','ArmWeapon',right*.31,.66,.62,.73,10 if up else 28,'arm',False,1)
        add('ArmL','ArmFree',-right*.31,.65,.25,.47,10 if up else 28,'arm',False,0)
    elif kind=='bird':
        add('Body','Body',0,.40,.60,.57,20,'body');add('Head','HeadNormal',0,.77,.56,.50,12 if up else 35,'head')
        for side,flip in [('L',False),('R',True)]:
            sign=-1 if side=='L' else 1
            add('Leg'+side,'Leg',sign*.16,.20,.18,.23,8,'leg',flip,int(flip))
            add('Wing'+side,'Wing',sign*.23,.57,.26,.36,25,'wing',flip)
        add('Tail','Tail',0,.28 if up else .52,.58 if plan['controller_family']=='Turkey' else .28,.60 if plan['controller_family']=='Turkey' else .31,32 if up else 6,'tail')
    elif kind=='crawler':
        add('Body','Body',0,.48,.68,.70,20,'body');add('Head','HeadNormal',0,.79 if up else .27,.57,.43,12 if up else 35,'head')
        add('Rear','Tip',0,.25 if up else .74,.54,.30,25 if up else 10,'segment')
        add('Segment','Segment',0,.45,.62,.35,22 if up else 18,'segment')
    elif kind=='chest':
        add('Body','Body',0,.29,.94,.54,20,'body');add('Head','HeadNormal',0,.45,.94,.54,30,'head')
        if 'Tongue' in plan['parts']:add('Tongue','Tongue',0,.48,.36,.55,35 if not up else 8,'tongue')
    elif kind=='floating':
        add('Body','Body',0,.27,.58,.47,20,'body');add('Head','HeadNormal',0,.62,.85,.77,25,'head')
        if 'Flap' in plan['parts']:
            add('FlapL','Flap',-.32,.43,.24,.14,15,'arm');add('FlapR','Flap',.32,.43,.24,.14,15,'arm',True)
    elif kind=='flying':
        eye=name in ['EvilEye','DreadEye']
        add('Body','Body',0,.34,.32,.33,15,'body');add('Head','HeadNormal',0,.56,.66 if eye else .62,.64 if eye else .56,25,'head')
        for side,flip in [('L',False),('R',True)]:
            sign=-1 if side=='L' else 1
            add('Wing'+side,'WingRaised',sign*.20,.52,.49,.64,10,'wing',flip,alternate='WingLowered')
    counts={k:sum(p['role']==r for p in rig) for k,r in [('legs','leg'),('wings','wing'),('claws','claw'),('tails','tail'),('arms','arm'),('feelers','feeler')]}
    views.append({'direction':direction,'parts':rig})
motion={'schema':1,'name':name,'controllerSource':t['controller'],'flying':kind in ['flying','floating'],'referenceBottom':bottom,'referenceHeight':height,'motionKind':kind,'anatomy':counts,'views':views}
(out/(name+'_Directions.layout.json')).write_text(json.dumps(motion,indent=2),encoding='utf-8')
(directory/'processing.json').write_text(json.dumps(processing,indent=2),encoding='utf-8')
proof=Image.new('RGB',(1600,math.ceil(len(parts)/8)*350),(40,48,37));draw=ImageDraw.Draw(proof)
for i,(key,piece) in enumerate(parts.items()):
    thumb=piece.copy();thumb.thumbnail((195,300));px=i%8*200+(200-thumb.width)//2;py=i//8*350+35
    proof.paste(thumb,(px,py),thumb);draw.text((i%8*200+5,i//8*350+8),key,fill='white')
proof.save(directory/'parts_clean.png')
print(json.dumps({'name':name,'kind':kind,'parts':len(parts),'height':height,'bottom':bottom,'anatomy':counts}))
