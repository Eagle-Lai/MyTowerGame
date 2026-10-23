"""Remove magenta, inspect actual image size, and stage one character's transparent atlas/rig in Docs."""
from pathlib import Path
import sys,json,math
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
name=sys.argv[1]
t=next(t for t in json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))['targets'] if t['name']==name)
directory=HERE/name
out=directory/'staged_art';out.mkdir(exist_ok=True)
selection=json.loads((directory/'art_selection.json').read_text(encoding='utf-8')) if (directory/'art_selection.json').exists() else {}
bat=name=='Bat';scorpion=name=='BlueScorpion'
names=['HeadNormal','HeadAngry','HeadDead','Body']+(['WingRaised','WingLowered'] if bat else ['LegFront','LegMiddle','LegBack','Claw','Tail'] if scorpion else ['LegFront','LegBack','Tail'])
cols,rows=(3,3) if scorpion else (4,2)
parts={};processing=[]
def clean_source(source):
    raw=Image.open(source)
    rgb=raw.convert('RGB');array=np.asarray(rgb).astype(np.int16)
    foreground=(array[:,:,2]<=array[:,:,1]+2)&(array[:,:,2]<=array[:,:,0]+4)&((array[:,:,0]-array[:,:,1])<=(array[:,:,1]-array[:,:,2])+12)
    if raw.mode=='RGBA':foreground &= np.asarray(raw)[:,:,3]>=128
    rgba=np.dstack([np.asarray(rgb),foreground.astype(np.uint8)*255]).astype(np.uint8)
    rgba[~foreground,:3]=0
    return raw,Image.fromarray(rgba,'RGBA')
for direction in ['Up','Down']:
    source=directory/selection.get(direction,'generation/'+direction+'/raw.png')
    raw,clean=clean_source(source);actual={'format':raw.format,'size':list(raw.size),'mode':raw.mode}
    for i,part_name in enumerate(names):
        x0=round(i%cols*raw.width/cols);x1=round((i%cols+1)*raw.width/cols)
        y0=round(i//cols*raw.height/rows);y1=round((i//cols+1)*raw.height/rows)
        piece=clean.crop((x0,y0,x1,y1))
        override=selection.get('part_overrides',{}).get(direction+'_'+part_name)
        if override:
            _,replacement=clean_source(directory/override['source'])
            piece=replacement.crop(override['rect'])
        bounds=piece.getbbox()
        if not bounds or bounds[2]-bounds[0]<15 or bounds[3]-bounds[1]<15:raise ValueError('Empty/small part '+direction+' '+part_name)
        piece=piece.crop(bounds)
        if part_name.startswith('Head') and direction=='Up' and i>0:
            # The same back-of-head silhouette correctly serves hidden facial expressions.
            piece=parts[direction+'_HeadNormal'].copy()
        parts[direction+'_'+part_name]=piece
    head_keys=[direction+'_'+n for n in names[:3]]
    maxw=max(parts[key].width for key in head_keys);maxh=max(parts[key].height for key in head_keys)
    for key in head_keys:
        p=parts[key];canvas=Image.new('RGBA',(maxw,maxh));canvas.alpha_composite(p,((maxw-p.width)//2,(maxh-p.height)//2));parts[key]=canvas
    processing.append({'direction':direction,'source':str(source.relative_to(HERE)),'actual':actual,'part_overrides':selection.get('part_overrides',{}),'key_method':'Original alpha >=128 plus magenta spectral separation; opaque interiors, antialias at final resampling','ground_shadow':'none permitted'})

# Full-rect slices retain transparent padding. Head expression canvases are identical in size.
atlas=Image.new('RGBA',(2048,2048));sprites=[];x=y=8;row_height=0
for key,piece in parts.items():
    if max(piece.size)>500:piece.thumbnail((500,500),Image.Resampling.LANCZOS)
    piece.save(out/(key+'.png'))
    if x+piece.width+8>2048:x=8;y+=row_height+8;row_height=0
    if y+piece.height+8>2048:raise ValueError('Atlas does not fit')
    atlas.alpha_composite(piece,(x,y))
    role=key.split('_',1)[1]
    pivot=(1,.5) if role.startswith('Wing') else ((1,.95) if scorpion else (.5,.95)) if role.startswith('Leg') else (1,.5) if role=='Claw' else (.5,.05) if role=='Tail' else (.5,.5)
    if bat and role.startswith('Wing'):
        # Shoulder-circle centers differ between the two actual poses. A shared edge-center
        # pivot would make the wing root jump when the Animator swaps its sprite.
        pivot={'Up_WingRaised':(.897,.556),'Up_WingLowered':(.911,.856),
               'Down_WingRaised':(.936,.457),'Down_WingLowered':(.940,.739)}[key]
    sprites.append({'name':key,'x':x,'y':2048-y-piece.height,'w':piece.width,'h':piece.height,'pivotX':pivot[0],'pivotY':pivot[1]})
    x+=piece.width+8;row_height=max(row_height,piece.height)
atlas.save(out/(name+'_Directions.png'))
(out/(name+'_Directions.sprites.json')).write_text(json.dumps({'texture':name+'_Directions.png','width':2048,'height':2048,'ppu':100,'sprites':sprites},indent=2),encoding='utf-8')

reference=json.loads((directory/'reference/battle_structure.json').read_text(encoding='utf-8'))['visible_bounds_root_local']
bottom=reference['min'][1];height=reference['max'][1]-bottom
views=[]
for direction in ['Up','Down']:
    up=direction=='Up';rig=[]
    def add(node,sprite,xx,yy,ww,hh,order,role,flip=False,phase=0,angle=0):
        rig.append({'name':node,'sprite':direction+'_'+sprite,'x':xx*height,'y':bottom+yy*height,'width':ww*height,'height':hh*height,
                    'order':order,'role':role,'flipX':flip,'phase':phase,'angle':angle,'alternate':direction+'_WingLowered' if role=='wing' else ''})
    if bat:
        add('Body','Body',0,.22,.34,.40,15,'body')
        add('Head','HeadNormal',0,.65,.85,.72,25,'head')
        add('WingL','WingRaised',-.12,.34,.58,.66,10,'wing',phase=0)
        add('WingR','WingRaised',.12,.34,.58,.66,10,'wing',flip=True,phase=0)
    elif scorpion:
        add('Body','Body',0,.28,.40,.35,20,'body')
        add('Head','HeadNormal',0,.47 if up else .20,.27,.25,15 if up else 35,'head')
        add('Tail','Tail',0,.25 if up else .30,.40,.65,15 if up else 5,'tail')
        for side,flip in [('L',False),('R',True)]:
            sign=-1 if side=='L' else 1
            for j,part in enumerate(['Front','Middle','Back']):
                yy=(.37-j*.12) if up else (.12+j*.12)
                add('Leg'+part+side,'Leg'+part,sign*.15,yy,.29,.18,8,'leg',flip,phase=(j+(side=='R'))%2)
            add('Claw'+side,'Claw',sign*.13,.48 if up else .23,.34,.27,12 if up else 30,'claw',flip,phase=0 if side=='L' else 1,angle=sign*30 if up else -sign*30)
    else:
        boar='Boar' in name
        wolf=name=='BlackWolf';panther=name=='BattlePanther'
        # Elevated quadruped view: the back is behind the head, not an upright humanoid chest.
        width=.83 if boar else .70 if wolf or panther else .80
        headheight=(.36 if up else .55) if boar else (.36 if up else .45) if wolf or panther else .42
        add('Body','Body',0,(.50 if up else .58) if boar else (.57 if up else .63),width,.80 if boar else .62,20,'body')
        add('Head','HeadNormal',0,.83 if up else .37,width*(.94 if boar else .90),headheight,12 if up else 35,'head')
        for side,flip in [('L',False),('R',True)]:
            sign=-1 if side=='L' else 1
            for front in [True,False]:
                near=not front if up else front
                yy=(.23 if near else .55) if boar else (.36 if near else .58)
                hh=(.20 if near else .17) if boar else (.36 if near else .25)
                xx=width*(.33 if near else .40)
                add(('Fore' if front else 'Hind')+side,'LegFront' if front else 'LegBack',sign*xx,yy,width*.27,hh,8,'leg',flip,phase=(int(front)+(side=='R'))%2)
        tailheight=(.48 if up else .30) if wolf or panther else .13 if boar else .20
        add('Tail','Tail',0 if up else width*.31,.30 if up else .68,.28 if wolf or panther else .13,tailheight,30 if up else 5,'tail')
    views.append({'direction':direction,'parts':rig})
layout={'schema':1,'name':name,'controllerSource':t['controller'],'flying':bat,'referenceBottom':bottom,'referenceHeight':height,'views':views}
(out/(name+'_Directions.layout.json')).write_text(json.dumps(layout,indent=2),encoding='utf-8')
(directory/'processing.json').write_text(json.dumps(processing,indent=2),encoding='utf-8')
proof=Image.new('RGB',(1600,math.ceil(len(parts)/8)*400),(40,48,37));draw=ImageDraw.Draw(proof)
for i,(key,piece) in enumerate(parts.items()):
    thumb=piece.copy();thumb.thumbnail((195,320));px=i%8*200+(200-thumb.width)//2;py=i//8*400+40
    proof.paste(thumb,(px,py),thumb);draw.text((i%8*200+5,i//8*400+15),key,fill='white')
proof.save(directory/'parts_clean.png')
print(json.dumps({'name':name,'parts':len(parts),'actual':processing,'referenceHeight':height,'referenceBottom':bottom},indent=2))
