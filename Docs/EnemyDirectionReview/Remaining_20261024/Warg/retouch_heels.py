"""Warg-only local raster repair, after packing. Never edits AI raw or source art."""
from pathlib import Path
from PIL import Image, ImageDraw
from collections import deque
import hashlib, json, math
import numpy as np

D = Path(__file__).resolve().parent
art = D/'staged_art'
manifest = json.loads((art/'Warg_Directions.sprites.json').read_text(encoding='utf-8'))
atlas = Image.open(art/'Warg_Directions.png').convert('RGBA')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
report = {'parent_raw': {d: sha(D/'generation'/d/'raw.png') for d in ['Up','Down']}, 'method': 'Local heel repaint preserves proximal fur, opaque silhouette and dark outline. Closed transparency holes are filled only inside the existing silhouette.', 'parts': []}

for s in manifest['sprites']:
    path = art/(s['name']+'.png')
    im = Image.open(path).convert('RGBA')
    parent_hash = sha(path)
    a = np.array(im)
    h,w = a.shape[:2]
    if s['name'] in ['Up_LegFront', 'Up_LegBack']:
        # Only the distal paw, below the fur-covered ankle, is repainted.
        # Preserve the original outer contour while replacing front toe grooves.
        y0 = 244
        mask = Image.fromarray(a[:,:,3])
        boundary = np.asarray(mask.filter(__import__('PIL.ImageFilter',fromlist=['MinFilter']).MinFilter(11))) > 0
        for y in range(y0,h):
            xs = np.where(boundary[y])[0]
            if not len(xs): continue
            for x in xs:
                vertical = (y-y0)/max(1,h-y0)
                lateral = abs(x-(xs[0]+xs[-1])/2)/max(1,(xs[-1]-xs[0])/2)
                # Muted olive heel with restrained side and lower-edge shading.
                shade = 1 - .11*vertical - .09*lateral
                color = np.array([108,89,49])*shade
                blend = min(1,(y-y0)/7)
                a[y,x,:3] = np.round((1-blend)*a[y,x,:3]+blend*color).astype(np.uint8)
        report['parts'].append({'name':s['name'],'repair':'Rear heel, no front toe divisions','region':[0,y0,w,h], 'parent_packed_sha256':parent_hash})
    # Flood only the transparent exterior. Any remaining transparent pixels are
    # enclosed spectral-mask pinholes; fill from the nearest opaque boundary.
    opaque = a[:,:,3] > 0
    exterior = np.zeros((h,w),dtype=bool)
    queue = deque()
    for x,y in [(x,y) for x in range(w) for y in [0,h-1]]+[(x,y) for y in range(h) for x in [0,w-1]]:
        if not opaque[y,x] and not exterior[y,x]: exterior[y,x]=True;queue.append((x,y))
    while queue:
        x,y=queue.popleft()
        for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
            if 0<=nx<w and 0<=ny<h and not opaque[ny,nx] and not exterior[ny,nx]:
                exterior[ny,nx]=True;queue.append((nx,ny))
    holes = np.argwhere(~opaque & ~exterior)
    for y,x in holes:
        for r in range(1,30):
            points = [(xx,yy) for yy in range(max(0,y-r),min(h,y+r+1)) for xx in range(max(0,x-r),min(w,x+r+1)) if opaque[yy,xx]]
            if points:
                xx,yy=min(points,key=lambda p:(p[0]-x)**2+(p[1]-y)**2)
                a[y,x]=a[yy,xx]; break
        else: raise ValueError('Unresolved interior hole '+s['name'])
    im=Image.fromarray(a,'RGBA');im.save(path)
    atlas.paste(im,(s['x'],2048-s['y']-s['h']))
    report.setdefault('alpha_holes_filled',{})[s['name']]=len(holes)
    report.setdefault('final_parts',{})[s['name']]=sha(path)
atlas.save(art/'Warg_Directions.png')
proof=Image.new('RGB',(1600,700),(40,48,37));draw=ImageDraw.Draw(proof)
for i,s in enumerate(manifest['sprites']):
    piece=Image.open(art/(s['name']+'.png'));piece.thumbnail((195,300))
    proof.paste(piece,(i%8*200+(200-piece.width)//2,i//8*350+35),piece)
    draw.text((i%8*200+5,i//8*350+8),s['name'],fill='white')
proof.save(D/'parts_clean.png')
(D/'local_raster_repair_r01.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'heel_parts':2,'holes_filled':sum(report['alpha_holes_filled'].values()),'raw_unchanged':True}))
