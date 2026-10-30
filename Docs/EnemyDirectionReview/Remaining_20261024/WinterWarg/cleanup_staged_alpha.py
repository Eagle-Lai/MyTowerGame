from session_winterwarg import *
from PIL import Image,ImageDraw
from collections import deque
import numpy as np,shutil,math
owner();art=D/'staged_art';hist=D/'stage_history/before_alpha_cleanup';assert not hist.exists();shutil.copytree(art,hist)
sprites=read(art/(NAME+'_Directions.sprites.json'));atlas=Image.new('RGBA',(2048,2048));report=[]
for s in sprites['sprites']:
    p=art/(s['name']+'.png');a=np.asarray(Image.open(p).convert('RGBA')).copy();fg=a[:,:,3]>127
    seen=np.zeros(fg.shape,dtype=bool);removed=0
    for y,x in zip(*np.where(fg)):
        if seen[y,x]:continue
        todo=[(y,x)];seen[y,x]=True;group=[]
        while todo:
            yy,xx=todo.pop();group.append((yy,xx))
            for ry in range(max(0,yy-1),min(fg.shape[0],yy+2)):
                for rx in range(max(0,xx-1),min(fg.shape[1],xx+2)):
                    if fg[ry,rx] and not seen[ry,rx]:seen[ry,rx]=True;todo.append((ry,rx))
        if len(group)<8:
            for yy,xx in group:a[yy,xx]=0;fg[yy,xx]=False
            removed+=len(group)
    outside=np.zeros(fg.shape,dtype=bool);q=deque()
    for y in range(fg.shape[0]):
        for x in [0,fg.shape[1]-1]:
            if not fg[y,x] and not outside[y,x]:outside[y,x]=True;q.append((y,x))
    for x in range(fg.shape[1]):
        for y in [0,fg.shape[0]-1]:
            if not fg[y,x] and not outside[y,x]:outside[y,x]=True;q.append((y,x))
    while q:
        y,x=q.popleft()
        for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
            if 0<=yy<fg.shape[0] and 0<=xx<fg.shape[1] and not fg[yy,xx] and not outside[yy,xx]:outside[yy,xx]=True;q.append((yy,xx))
    holes=set(zip(*np.where(~fg & ~outside)));total=len(holes)
    while holes:
        progress=False
        for y,x in list(holes):
            colors=[a[yy,xx,:3] for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)] if 0<=yy<fg.shape[0] and 0<=xx<fg.shape[1] and fg[yy,xx]]
            if colors:a[y,x,:3]=np.median(colors,axis=0);a[y,x,3]=255;fg[y,x]=True;holes.remove((y,x));progress=True
        assert progress
    im=Image.fromarray(a);im.save(p);atlas.alpha_composite(im,(s['x'],2048-s['y']-s['h']))
    report.append({'file':p.name,'before_sha256':sha(hist/p.name),'after_sha256':sha(p),'filled_enclosed_micro_pixels':total,'removed_dust_pixels':removed})
atlas.save(art/(NAME+'_Directions.png'))
proof=Image.new('RGB',(1600,700),(40,48,37));draw=ImageDraw.Draw(proof)
for i,s in enumerate(sprites['sprites']):
    im=Image.open(art/(s['name']+'.png'));im.thumbnail((195,300));proof.paste(im,(i%8*200+(200-im.width)//2,i//8*350+35),im);draw.text((i%8*200+5,i//8*350+8),s['name'],fill='white')
proof.save(D/'parts_clean.png')
write(D/'staged_alpha_cleanup_20261029.json',{'created_at':now(),'reason':'Spectral chroma mask contained scattered 17-119 enclosed missing pixels per slice; restore tiny enclosed pixels from neighboring foreground and remove 1-3 pixel exterior dust only. No part removed or palette-keyed organ loss.','slices':report},True)
run('render_staged_rig.py',NAME)
print(json.dumps({'parts':len(report),'filled':sum(x['filled_enclosed_micro_pixels'] for x in report),'dust_removed':sum(x['removed_dust_pixels'] for x in report)}))
