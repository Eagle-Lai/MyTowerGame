"""ShardLizard-only derivatives. Preserve paid source files and record pixel bounds."""
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import json, hashlib

D = Path(__file__).resolve().parent
OUT = D / 'local_raster_revision_01'
OUT.mkdir(exist_ok=False)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
records = []
for direction, source in [('Up', D/'generation/Up/revision_02/raw.png'), ('Down', D/'generation/Down/raw.png')]:
    original = Image.open(source).convert('RGB')
    repaired = original.copy()
    if direction == 'Up':
        a = np.array(repaired)
        for box in [(110,560,285,840), (440,550,660,845)]:
            x0,y0,x1,y1 = box
            part = a[y0:y1,x0:x1].copy()
            fg = (part[:,:,1] > 35) & (part[:,:,2] < part[:,:,1]+8)
            interior = np.array(Image.fromarray((fg*255).astype('uint8')).filter(ImageFilter.MinFilter(13))) > 220
            yy,xx = np.indices(fg.shape)
            # Smooth lower heel interior; preserve exterior silhouette and dark border.
            region = interior & (yy+y0 >= 787) & (yy+y0 <= 825)
            blend = np.clip((yy+y0-787)/8,0,1)
            shade = np.clip(xx/max(1,x1-x0),0,1)
            for ch,(light,dark) in enumerate([(141,113),(124,97),(84,62)]):
                target = light+(dark-light)*shade
                part[:,:,ch][region] = (part[:,:,ch][region]*(1-blend[region])+target[region]*blend[region]).astype('uint8')
            a[y0:y1,x0:x1] = part
        repaired = Image.fromarray(a)
        method = 'Recolor lower rear heel interiors with olive cel shading; retain original silhouettes and outer contours.'
    else:
        draw = ImageDraw.Draw(repaired)
        for offset in [0,386]:
            poly = [(110,173),(248,171),(279,227),(265,248),(235,244),(210,264),(182,250),(157,257),(130,245),(102,245),(87,220)]
            draw.polygon([(x+offset,y) for x,y in poly], fill=(135,117,78))
            draw.polygon([(110+offset,174),(247+offset,172),(258+offset,204),(236+offset,215),(127+offset,211),(99+offset,217)], fill=(147,129,87))
            # Two small original-style angular forehead chips, no torso-sized plaque.
            for cx in [128+offset,231+offset]:
                draw.polygon([(cx-18,199),(cx-7,181),(cx+13,196),(cx+12,216),(cx-11,220)], fill=(47,43,25))
                draw.polygon([(cx-11,200),(cx-5,190),(cx+6,199),(cx+5,210),(cx-7,213)], fill=(232,177,63))
                draw.polygon([(cx-11,200),(cx-5,190),(cx+6,199),(cx-2,201)], fill=(255,220,136))
        draw.polygon([(891,174),(1028,172),(1063,217),(1042,239),(1016,234),(995,252),(968,241),(941,250),(915,238),(883,241),(870,216)], fill=(135,117,78))
        draw.polygon([(891,175),(1027,173),(1043,204),(1022,214),(899,211),(882,218)], fill=(147,129,87))
        for cx,cy in [(911,201),(1018,197)]:
            draw.polygon([(cx-18,cy),(cx-7,cy-18),(cx+13,cy-3),(cx+12,cy+17),(cx-11,cy+21)], fill=(47,43,25))
            draw.polygon([(cx-11,cy+1),(cx-5,cy-9),(cx+6,cy),(cx+5,cy+11),(cx-7,cy+14)], fill=(232,177,63))
            draw.polygon([(cx-11,cy+1),(cx-5,cy-9),(cx+6,cy),(cx-2,cy+2)], fill=(255,220,136))
        method = 'Replace invented dorsal-plaque duplicate on all three heads with olive forehead planes and two small angular gold chips; preserve face, jaw, expressions, body shard and all other pixels.'
    destination = OUT/(direction+'.png')
    repaired.save(destination)
    changed = np.any(np.array(original)!=np.array(repaired),axis=2)
    yy,xx = np.where(changed)
    records.append(dict(direction=direction,source=source.relative_to(D).as_posix(),source_sha256=sha(source),output=destination.relative_to(D).as_posix(),output_sha256=sha(destination),changed_pixels=int(changed.sum()),changed_bounds=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],method=method))
(OUT/'processing.json').write_text(json.dumps(dict(created_at=datetime.now(timezone.utc).isoformat(),records=records,visual_review='pending',user_approved=False),indent=2)+'\n',encoding='utf-8')
print(json.dumps(records))
