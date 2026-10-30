"""Offline affine rendering of serialized source prefab sprites. Reference only, not runtime evidence."""
from pathlib import Path
import re,json,math,sys
import numpy as np
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
targets=json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))['targets']
if '--name' in sys.argv: targets=[t for t in targets if t['name']==sys.argv[sys.argv.index('--name')+1]]

def number(text,key,default=0):
    m=re.search(r'^\s*'+re.escape(key)+r': ([-.\deE+]+)\s*$',text,re.M)
    return float(m.group(1)) if m else default

def vector(text,key,default):
    m=re.search(re.escape(key)+r': \{([^}]+)\}',text)
    return {k:float(v) for k,v in re.findall(r'(\w+): ([-.\deE+]+)',m.group(1))} if m else default

def field_id(text,key):
    m=re.search(re.escape(key)+r': \{fileID: (-?\d+)',text)
    return int(m.group(1)) if m else 0

def parse_sprite_meta(path):
    text=path.read_text(encoding='utf-8-sig')
    result={}
    for block in re.split(r'^    - serializedVersion: 2\s*$',text,flags=re.M)[1:]:
        m=re.search(r'^      name: (.+)$',block,re.M)
        fid=re.search(r'^      internalID: (-?\d+)',block,re.M)
        if not m or not fid: continue
        rect={key:number(block,key) for key in ['x','y','width','height']}
        result[int(fid.group(1))]={'name':m.group(1).strip(),'rect':rect,'pivot':vector(block,'pivot',{'x':.5,'y':.5})}
    return result,number(text,'spritePixelsToUnits',100)

contact=Image.new('RGB',(1600,math.ceil(len(targets)/5)*550),(40,48,37));draw=ImageDraw.Draw(contact)
for index,t in enumerate(targets):
    source=ROOT/t['source'];battle='--battle' in sys.argv
    text=(ROOT/t['battle'] if battle else source).read_text(encoding='utf-8-sig')
    atlas=Image.open(ROOT/t['atlas']).convert('RGBA')
    sprites,ppu=parse_sprite_meta(ROOT/(t['atlas']+'.meta'))
    gos={};transforms={};renderers=[]
    for match in re.finditer(r'^--- !u!(\d+) &(-?\d+)\s*\n(.*?)(?=^--- !u!|\Z)',text,re.M|re.S):
        kind,fid,body=int(match.group(1)),int(match.group(2)),match.group(3)
        if kind==1:
            name=re.search(r'^  m_Name: (.*)$',body,re.M).group(1)
            gos[fid]={'name':name,'active':number(body,'m_IsActive',1)!=0}
        if kind==4:
            pos=vector(body,'m_LocalPosition',{'x':0,'y':0});scale=vector(body,'m_LocalScale',{'x':1,'y':1})
            q=vector(body,'m_LocalRotation',{'z':0,'w':1});angle=2*math.atan2(q['z'],q['w'])
            c,s=math.cos(angle),math.sin(angle)
            matrix=np.array([[c*scale['x'],-s*scale['y'],pos['x']],[s*scale['x'],c*scale['y'],pos['y']],[0,0,1.]])
            transforms[fid]={'go':field_id(body,'m_GameObject'),'parent':field_id(body,'m_Father'),'matrix':matrix}
        if kind==212:renderers.append({'go':field_id(body,'m_GameObject'),'sprite':field_id(body,'m_Sprite'),
            'enabled':number(body,'m_Enabled',1)!=0,'order':number(body,'m_SortingOrder'),
            'flipx':number(body,'m_FlipX'),'flipy':number(body,'m_FlipY')})
    bygo={v['go']:k for k,v in transforms.items()}
    def world(fid):
        t=transforms[fid]
        return world(t['parent'])@t['matrix'] if t['parent'] in transforms else t['matrix']
    def active(fid):
        t=transforms[fid]
        return gos[t['go']]['active'] and (active(t['parent']) if t['parent'] in transforms else True)
    layers=[];points=[];structure=[]
    for r in sorted(renderers,key=lambda r:r['order']):
        if not r['enabled'] or not active(bygo[r['go']]) or gos[r['go']]['name'] in ['Shadow','Fill','Bg']:continue
        info=sprites[r['sprite']];rect=info['rect'];pivot=info['pivot'];w,h=int(rect['width']),int(rect['height'])
        image=atlas.crop((int(rect['x']),atlas.height-int(rect['y'])-h,int(rect['x'])+w,atlas.height-int(rect['y'])))
        m=world(bygo[r['go']])@np.array([[(-1 if r['flipx'] else 1)/ppu,0,-pivot['x']*w/ppu*( -1 if r['flipx'] else 1)],
                         [0,(1 if r['flipy'] else -1)/ppu,(1-pivot['y'])*h/ppu*(-1 if r['flipy'] else 1)],[0,0,1]])
        bbox=image.getbbox()
        if not bbox:continue
        corners=np.array([[bbox[0],bbox[1],1],[bbox[2],bbox[1],1],[bbox[2],bbox[3],1],[bbox[0],bbox[3],1]]).T
        p=m@corners;points.extend(p[:2].T.tolist());layers.append((image,m))
        structure.append({'node':gos[r['go']]['name'],'sprite':info['name'],'order':r['order'],'matrix':m.tolist()})
    coords=np.array(points);minimum=coords.min(axis=0);maximum=coords.max(axis=0);center=(minimum+maximum)/2
    root_id=next(fid for fid,tform in transforms.items() if tform['parent'] not in transforms)
    root_inverse=np.linalg.inv(world(root_id))
    local=(root_inverse@np.column_stack([coords,np.ones(len(coords))]).T)[:2].T
    ratio=840/max(maximum-minimum)
    screen=np.array([[ratio,0,512-ratio*center[0]],[0,-ratio,500+ratio*center[1]],[0,0,1]])
    output=Image.new('RGBA',(1024,1024),(0,0,0,0))
    for image,m in layers:
        inv=np.linalg.inv(screen@m)
        warped=image.transform(output.size,Image.Transform.AFFINE,tuple(inv[:2].flatten()),Image.Resampling.BICUBIC)
        output.alpha_composite(warped)
    out=HERE/t['name']/'reference';output.save(out/('battle_prefab_offline.png' if battle else 'source_prefab_offline.png'))
    (out/('battle_structure.json' if battle else 'source_structure.json')).write_text(json.dumps({'note':'Offline original prefab reference; no Unity runtime validation',
        'visible_bounds_world':{'min':minimum.tolist(),'max':maximum.tolist()},
        'visible_bounds_root_local':{'min':local.min(axis=0).tolist(),'max':local.max(axis=0).tolist()},'renderers':structure},indent=2),encoding='utf-8')
    thumb=output.copy();thumb.thumbnail((300,470));x=(index%5)*320+(320-thumb.width)//2;y=(index//5)*550+50
    contact.paste(thumb,(x,y),thumb);draw.text(((index%5)*320+12,(index//5)*550+14),t['name'],fill='white')
    print(t['name'],len(layers),'rendered parts',minimum.tolist(),maximum.tolist())
contact.save(HERE/'source_reference_contact.png')
